# Choosing a datastore

Read this when: someone proposes adding a database, cache, queue, event log, search system or
vector store, or asks which store fits a workload. Also when reviewing an architecture that
already has more stores than people.

## The bar for a second store

Postgres is the default for every kind of data until a measured workload fails on it. The cost of
an additional store is not its monthly price. It is one more thing to back up, upgrade, monitor,
secure, run locally and in CI, include in every user-deletion path, and keep consistent with the
database through a sync mechanism that will have bugs.

Before adding anything, write down five answers. If one is missing, the store is not justified yet.

1. **The failing workload, with a number.** "Search p95 is 1.8 s at 4 M rows", not "search will
   need to scale".
2. **What was tried in Postgres.** An index, a rewritten query, a materialized view, a partition,
   a read replica, a bigger instance. Scaling the instance up one size is usually cheaper than a
   new system for a year.
3. **Which store holds the truth for each fact.** One store per fact. The new store is either the
   source of truth for something new (files in object storage) or derived from Postgres (cache,
   index, warehouse).
4. **How it is rebuilt from nothing, and how long that takes.**
5. **What the product does when the new store is down.** Degrade (search unavailable, cache
   bypassed) or fail. Decide; do not discover it during the outage.

Stage guidance: at Prototype, Postgres plus object storage, nothing else. At Launch, add Redis only
if a concrete need below is met. A search engine, a warehouse or an event log normally appears at
Scale, and each one arrives managed, not self-hosted.

## What Postgres already covers

| Need | In Postgres | Sign the ceiling is reached |
|---|---|---|
| Job queue | Table with `FOR UPDATE SKIP LOCKED` (pg-boss, Graphile Worker) | Sustained thousands of jobs per second (rule of thumb; measure); queue-table bloat hurting the primary |
| Cache of an expensive read | Materialized view, summary table, or the query fixed with an index | Read is already indexed, still hot, and tolerates staleness |
| Text search | `tsvector` + GIN, `pg_trgm` | Typo tolerance, facets with counts, or relevance tuning become product requirements |
| Vector similarity | `pgvector` with HNSW | The index no longer fits in memory beside the main workload (rule of thumb: somewhere in the tens of millions of vectors, sooner with large dimensions) |
| Document data | `jsonb` + GIN, expression indexes | Almost never the reason to leave |
| Pub/sub between app instances | `LISTEN`/`NOTIFY` | Needs durability or fan-out to many subscribers |
| Locks, leader election | Advisory locks | Lock traffic at a rate that matters to the primary |
| Time-partitioned events | Declarative partitioning + BRIN | Aggregations over hundreds of millions of rows on the request path |
| Geospatial | PostGIS | Rarely |
| Analytics | Read replica, rollup tables | Scans slow the replica, or data from other systems must be joined |

Traps in the Postgres-only route, so they are known rather than discovered: `NOTIFY` messages are
not stored and a disconnected listener misses them, so treat a notification as a wake-up hint and
re-read state from a table. The payload must stay under 8000 bytes. Transactions that call
`NOTIFY` are serialized on a global lock at commit, so keep it off hot write paths. `LISTEN`
needs its own direct connection: it does not work through a transaction-mode connection pooler.
A queue table with high churn needs aggressive autovacuum settings on that table. Session-level
advisory locks also break under transaction-mode pooling; use the transaction-scoped variant
(`pg_advisory_xact_lock`).

## When each common addition is justified

| Store | Add when | Not a reason |
|---|---|---|
| **Object storage** | The first user file, export, or generated asset. This is the one addition that is correct from day one: files in database rows bloat backups and replication, and files on a local disk vanish on a PaaS redeploy. | — |
| **Redis / Valkey** | Rate limiting across several app instances; a hot read that is already indexed and tolerates staleness; a job system whose features need it (see below); short-lived shared state such as presence. | "Databases are slow." Sessions (a Postgres table is fine until Scale). A query that lacks an index. |
| **Search engine** | Typo tolerance, facets with counts, instant search-as-you-type, or per-field ranking are requirements, and Postgres search has been built and measured as insufficient. | A `LIKE '%term%'` query is slow (add a trigram index). |
| **Dedicated vector store** | Vector count or query volume makes pgvector's index size or recall/latency trade unworkable on an instance the product can afford, or filtering needs outgrow it. | Building a first retrieval feature. Start in pgvector, next to the rows the vectors describe, so permissions and deletion are joins. |
| **Warehouse** | Questions need data from several systems joined, or analytical scans hurt the replica. See `streams-pipelines.md`. | One dashboard. |

Run added stores as managed services. A solo developer self-hosting Redis, a search cluster and
a broker has three unpaid on-call rotations.

## Job queue, broker or event log

These solve different problems and are routinely confused.

| | Job queue | Message broker | Event log |
|---|---|---|---|
| Examples | pg-boss, Graphile Worker, BullMQ | SQS/SNS, RabbitMQ, Google Pub/Sub | Kafka, Redpanda, Kinesis |
| Unit | A task to perform once | A message routed to subscribers | An immutable fact, retained |
| Consumers | One worker pool | Several services, each with its own queue | Many independent groups, each with its own offset |
| After consumption | Deleted or archived | Deleted | Stays until retention expires; can be re-read |
| Ordering | Not guaranteed | Not guaranteed by default (FIFO variants at lower throughput) | Guaranteed within a partition |

Stay on a Postgres-backed job queue while there is one application and one worker pool. Enqueueing
in the same transaction as the business write removes a whole class of lost-job and phantom-job
bugs, which a queue in another system can only approximate with an outbox. Move the job system to Redis (BullMQ) when volume or
features such as rate-limited queues, flows and fine-grained priorities demand it; that Redis
instance then holds data that must not be evicted (see `caching-redis.md`).

A queue must yield to a broker or log when one of these is true:

- **Several independent consumers need the same event.** Search indexing, the warehouse, a
  notification service and a webhook dispatcher each need every order event at their own pace.
  A job queue forces the producer to know every consumer.
- **Consumers must replay history**, to rebuild a store or fix a bug in a consumer.
- **Strict per-entity ordering** matters at volume.
- **Throughput** is beyond what the primary database should absorb as queue churn.

Intermediate steps that avoid Kafka for a long time: a transactional outbox table with one cursor
per consumer; a managed broker with fan-out (SNS to SQS, Pub/Sub); Redis Streams with consumer
groups if Redis is already present and its durability is acceptable. Choose a Kafka-style log
only managed, and only at Scale with someone who owns it: partition counts, consumer lag,
schema evolution and rebalancing are a standing job. Job-queue design itself belongs to
`0x:backend-architecture`; stream design is in `streams-pipelines.md`.

## SQLite, libSQL and D1

SQLite allows one writer at a time for the whole database. Where that fits, it removes the
network hop, the connection pool and the database server.

Fits: a single-server application with read-heavy traffic; one database per tenant or per user;
internal tools; read-mostly data replicated to edge locations; desktop, CLI and mobile storage.

Does not fit: several application instances that must write to one database file (never put the
file on a network filesystem: locking is unreliable and corruption follows); write-heavy
concurrent workloads; a PaaS with an ephemeral filesystem unless a persistent volume is attached;
needs for row-level security, rich extensions or logical replication.

Settings that separate a working deployment from `database is locked` errors:

```sql
PRAGMA journal_mode = WAL;        -- readers do not block the writer; stored in the database file
PRAGMA busy_timeout = 5000;       -- wait for the write lock instead of failing at once
PRAGMA synchronous = NORMAL;      -- with WAL: a power loss may drop the last commits, not corrupt
PRAGMA foreign_keys = ON;         -- off by default
```

Only `journal_mode` is stored in the file. The other three are per connection and revert to
their defaults on every new one, so set them in the code that opens connections, not once by
hand. Keep `synchronous = FULL` where losing the last committed transactions in a power loss is
unacceptable (money).

Open write transactions with `BEGIN IMMEDIATE`. A deferred transaction that reads and then tries
to write after another connection has committed fails with `SQLITE_BUSY` at once, whatever the
busy timeout. Declare tables `STRICT`,
otherwise a column accepts values of any type. Schema changes are limited: many alterations
mean creating a new table and copying.

Backups: a plain file copy of a live database can be corrupt. Use `VACUUM INTO`, the backup API,
or continuous replication of the WAL to object storage (Litestream), and test a restore.

libSQL (the SQLite fork behind Turso Cloud) adds a server mode and embedded replicas: a local
file for reads that syncs from a remote primary, with writes sent to that primary. Its vendor is
also building a separate Rust rewrite of SQLite with its own sync mechanism and steers new
projects toward it, so check which engine and sync path the current SDK recommends before
designing around either. Cloudflare D1 is SQLite reached from Workers through a binding, with a
per-database size cap (10 GB on the paid plan when this was written; check the current limits)
and a design aimed at many small databases, such as one per tenant, rather than one large one.
In both, writes go to a single primary, so a write from a far region pays the round trip.

Flip to Postgres when a second writer process on another machine is needed, or when write
contention shows up as busy timeouts under normal load.

## Derived stores must be rebuildable

A cache, a search index, a vector index, a warehouse table and a denormalized counter are all
derived data. The rule: losing any of them costs time, never information.

- No fact originates in a derived store. A view counter that lives only in Redis, or a field
  edited directly in the search index, makes that store a second source of truth with no backups.
- A rebuild command exists in the repository for each derived store, and its duration at current
  data size is known. An index that takes nine hours to rebuild is an outage plan, not a rebuild.
- Rebuilds are exercised: at minimum in staging, and whenever the schema of the derived store
  changes (which is done by building a new copy and switching, see `search.md`).
- Writes reach derived stores through one mechanism (outbox, change data capture, or an enqueue
  inside the transaction), never through "write to the database, then call the other store" in
  request code. The second call fails or arrives out of order, and the stores drift silently.
- A reconciliation job compares counts or checksums between source and derived store on a
  schedule and reports drift. Without it, drift is found by a customer.

Check: in staging, flush Redis and drop the search index. The product must degrade, then recover
with documented commands and no manual data repair.

## Document, key-value and wide-column stores

Choose one only for an access pattern that is proven, stable and written down. These stores are
fast because they answer a fixed set of key-based queries; every query not designed in advance is
a scan, a new secondary index or a backfill.

| Store type | The pattern that justifies it | Main trap |
|---|---|---|
| Key-value / document at scale (DynamoDB) | Known key lookups and range queries at very high volume, predictable latency, zero operations, serverless connection model | Schema is designed from the query list. A new query after launch means a new index or a migration. Hot partition keys throttle. Items have a size limit. |
| Document database (MongoDB) | The team and codebase already use it | "Flexible schema" moves the schema into application code where nothing enforces it. `jsonb` gives the same shape with transactions and joins. |
| Realtime document sync (Firestore-style) | Client-side offline sync and live updates are the core of the product | Query model and per-read pricing shape the whole data model; security rules become the authorization layer. |
| Wide-column (Cassandra, ScyllaDB) | Sustained write volume beyond a single primary, multi-region writes | Needs a team. Not a solo-founder system. |

Decision rule: list every read and write the product performs against the data. If the list is
short, key-based and has not changed in months, a key-value store can work. If the product is
still finding its shape, the queries will change, and relational wins.

## Columnar engines for analytics

Row stores read whole rows; an aggregate over three columns of a 60-column table at 500 M rows
reads everything. Columnar engines read only the needed columns, compressed, and are commonly one
to two orders of magnitude faster on such scans (rule of thumb; measure).

Order of escalation: rollup tables maintained by a job → a read replica for analytical queries →
a columnar engine.

| Engine | Use for | Know before choosing |
|---|---|---|
| **DuckDB** | In-process analytics: batch reports, ad hoc analysis, querying Parquet or CSV files in object storage, embedded in a job or script | A library, not a server. One process writes at a time. No operations at all, which is why it is the first columnar step. |
| **ClickHouse** | Customer-facing analytics and event data at volume with sub-second aggregates under concurrency | Insert in batches (or enable asynchronous inserts), never row by row. The table's `ORDER BY` key decides query speed and is expensive to change. Design tables as append-only: classic `ALTER TABLE ... UPDATE/DELETE` mutations rewrite whole data parts in the background, and the lightweight deletes and updates of newer releases are cheaper but still not meant for request-rate row changes (check their status in the version in use). Deduplication by `ReplacingMergeTree` happens at merge time, so queries must tolerate or collapse duplicates. |
| **Cloud warehouse** (BigQuery, Snowflake) | Internal business analytics joining many sources | Latency and pricing models suit analysts, not the request path. See `streams-pipelines.md`. |

Customer-facing dashboards ("usage over the last 90 days") are a product feature with product
latency needs; internal business questions are a warehouse concern. Do not serve the former from
the latter.

## Time-series and event stores

Data is metrics-shaped when it is append-only, timestamped, queried by time range and aggregate,
rarely updated, and old data loses value. That shape allows partition pruning, compression, cheap
retention by dropping whole partitions, and downsampling.

- Start with a Postgres table partitioned by time (daily or monthly by volume), a BRIN index on
  the timestamp, and retention by `DROP`/detach of old partitions instead of `DELETE`. Keep
  rollup tables (per hour, per day) for dashboards. This carries far more than most products
  ever write.
- Next step inside Postgres: the TimescaleDB extension (automatic partitioning, compression,
  continuously maintained aggregates). Its vendor (now named TigerData) keeps compression and
  continuous aggregates under its own source-available license, so other clouds that offer the
  extension typically ship the Apache-licensed edition without them, and some managed Postgres
  providers do not offer it at all. Check what the provider ships before designing around it.
- At volume (rule of thumb: billions of rows, or aggregation latency on the request path that
  rollups cannot meet), move the data to ClickHouse or a managed time-series service.
- Cardinality is the trap in every time-series system: a tag or label holding user IDs or
  request IDs multiplies the number of series and destroys both cost and speed. Put
  high-cardinality identifiers in columns of a columnar store, not in series labels.

Infrastructure metrics and traces go to the observability backend, not a product datastore; that
is `0x:site-reliability`.

## Ask the user

- **What is the measured problem?** Which query or workload, how slow, at what data size. Without
  a number, assume Postgres is sufficient and fix it there.
- **What should happen when the new store is unavailable?** Degraded feature or a failed request.
  Default: the feature degrades and the rest of the product works.
- **How stale may the derived data be?** Seconds, minutes or a day. This decides sync mechanism
  and cost. Default: seconds for search of the user's own edits, minutes for everything else.
- **Who operates it, and what is the budget?** Default: managed service, smallest tier, with a
  spending alert.
- **Is there an expected volume that changes the answer?** A known import of 100 M rows or a
  contractual latency target justifies choosing ahead of the default.
