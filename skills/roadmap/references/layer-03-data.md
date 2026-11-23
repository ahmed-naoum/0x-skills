# Layer 3: Data

Read this when: the user asks what there is to know about data, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

Where does the truth live, and how do I keep it correct, fast and recoverable?

Competencies: 115 (34 ● / 57 ◐ / 24 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## postgres-database

Model, query, migrate, tune, back up and scale a relational database, with PostgreSQL as the default: schemas, SQL, transactions, indexes, zero-downtime migrations, operations and recovery.

**Relational modeling** (`references/schema-modeling.md`)

- ● Model a domain in normalized tables with keys and foreign keys
- ● Make invalid states impossible with NOT NULL, CHECK, UNIQUE and exclusion constraints
- ● Choose column types: timestamptz, text, numeric, enums and JSONB
- ● Store money as integer minor units with an explicit currency
- ● Choose between a typed ORM (Drizzle, Prisma) and raw SQL
- ● Choose primary keys: UUIDv7, identity columns or natural keys
- ◐ Use JSONB for variable attributes without losing integrity or indexability
- ◐ Model soft deletes, audit history and temporal data deliberately
- ◐ Model hierarchies, many-to-many and polymorphic relations idiomatically
- ◐ Decide when to denormalize and how to keep the copies consistent

**Writing application SQL** (`references/sql-queries.md`)

- ● Write joins, aggregates, window functions and CTEs by hand
- ● Eliminate N+1 queries in the ORM
- ● Wrap manual production SQL in a transaction and review it first
- ● Write upserts and bulk writes with ON CONFLICT and batching
- ● Read the SQL an ORM generates and override it when it is wrong
- ◐ Write keyset pagination queries that stay fast on deep pages
- ◐ Use RETURNING, lateral joins and recursive CTEs to simplify application code
- ◐ Write, dry-run and execute a backfill to correct bad records

**Transactions, isolation and locking** (`references/transactions-concurrency.md`)

- ● Use transactions to keep multi-step writes atomic
- ● Prevent lost updates with atomic SQL updates or optimistic version checks
- ● Keep external API calls outside database transactions
- ◐ Choose an isolation level and retry serialization failures
- ◐ Lock rows with SELECT FOR UPDATE and avoid deadlocks
- ◐ Set statement, lock and idle-in-transaction timeouts to protect the pool
- ○ Use SKIP LOCKED and advisory locks for queues and single-run work
- ○ Diagnose blocked queries and deadlocks from pg_locks and logs

**Indexes and query plans** (`references/indexes-query-plans.md`)

- ● Read an EXPLAIN ANALYZE plan and fix a sequential scan
- ● Add an index that matches a slow query's filter and sort order
- ◐ Design composite and partial indexes from real query patterns
- ◐ Find the costliest queries with pg_stat_statements and fix them
- ◐ Choose index types: B-tree, GIN, GiST, BRIN or hash
- ◐ Remove unused and duplicate indexes that slow writes
- ○ Use covering indexes and index-only scans for hot reads
- ○ Fix bad plans caused by stale statistics or row misestimates

**Zero-downtime schema migrations** (`references/migrations.md`)

- ● Run schema migrations as versioned, reviewed code
- ● Write backward-compatible migrations using expand-then-contract
- ◐ Add indexes and constraints without long table locks
- ◐ Rename or retype a column across several deploys without downtime
- ◐ Backfill large tables in throttled, resumable batches
- ◐ Rehearse migrations on a production-sized copy with lock timeouts set
- ◐ Decide whether a migration needs a down script or a forward fix
- ○ Recover from a half-applied migration without losing data

**Running Postgres in production** (`references/postgres-operations.md`)

- ● Choose a managed database provider by backups, limits, support and exit path
- ● Pool connections and size the pool against database limits
- ◐ Configure pooling for serverless and high-concurrency workloads with PgBouncer
- ◐ Grant least-privilege database roles per service
- ◐ Monitor connections, locks, cache hit rate, disk and long transactions
- ◐ Kill a runaway query safely
- ◐ Use serverless Postgres with branching for previews and tests
- ○ Control vacuum, bloat and transaction-ID wraparound
- ○ Tune memory and planner settings for the instance and workload
- ○ Upgrade a major database version with minimal downtime

**Backup, restore and data recovery** (`references/backup-recovery.md`)

- ● Configure automated backups with point-in-time recovery
- ● Restore from backup on a schedule and time it
- ● Take a verified snapshot before a risky change
- ◐ Store immutable backups in a separate account and region
- ◐ Restore a database to a chosen timestamp and reconcile lost writes
- ◐ Guard critical tables with deletion protection and restricted destructive grants
- ○ Recover one tenant's deleted rows from backup without a full rollback

**Replication and scaling** (`references/replication-scaling.md`)

- ◐ Scale vertically first and recognize when that is exhausted
- ◐ Set up a standby replica and rehearse failover
- ◐ Monitor replication lag and alert before reads go stale
- ◐ Offload reporting queries so they cannot starve transactional traffic
- ○ Route reads to replicas while handling replication lag
- ○ Promote a replica and rebuild the failed primary
- ○ Partition large tables by time or tenant
- ○ Decide when to add read replicas, partition tables or shard
- ○ Migrate between database providers with minimal downtime via logical replication

## data-stores

Decide when a product needs more than Postgres and run what it adds: Redis caching, search, object storage, event streams, an analytics warehouse and pipelines, and the data lifecycle across all of them.

**Choosing a datastore** (`references/choosing-datastores.md`)

- ● Default to Postgres and justify every additional datastore
- ● Decide when to add Redis, a search engine, object storage or a vector index
- ◐ Decide when a job queue must yield to a broker or Kafka-style event log
- ◐ Use SQLite, libSQL or D1 where a single writer fits
- ◐ Keep every derived store rebuildable from the source of truth
- ○ Choose a document, key-value or wide-column store only for a proven access pattern
- ○ Run analytics on a columnar engine such as ClickHouse or DuckDB
- ○ Choose a time-series or event store for metrics-shaped data at volume

**Application caching with Redis** (`references/caching-redis.md`)

- ● Decide what must never be cached: balances, entitlements, payment state
- ◐ Cache hot reads in Redis or Valkey with TTLs and explicit invalidation
- ◐ Choose cache-aside, read-through or write-through for a use case
- ◐ Design cache keys and versions so deploys never read stale shapes
- ◐ Size memory, set an eviction policy and decide whether persistence matters
- ◐ Use Redis for counters, locks and rate limits without treating it as truth
- ◐ Measure hit rate and prove a cache earns its complexity
- ○ Prevent cache stampedes with locking or stale serving

**Search** (`references/search.md`)

- ● Use Postgres full-text and trigram search before adding a search engine
- ● Enforce tenant and permission filters inside every search query
- ◐ Choose a search engine by data size, features and operating burden
- ◐ Keep a search index in sync with the database and rebuild it without downtime
- ◐ Build autocomplete, facets and filters that stay fast
- ◐ Store and query embeddings with pgvector and HNSW indexes
- ◐ Measure search quality with zero-result and click-through rates
- ○ Tune relevance with analyzers, typo tolerance, synonyms and ranking rules

**Object storage and files** (`references/object-storage.md`)

- ● Store files in object storage with private buckets by default
- ● Issue short-lived signed URLs for private downloads
- ● Tie every object to a database row with keys, metadata and ownership
- ● Choose S3, R2 or another compatible store by egress cost and features
- ◐ Set lifecycle rules, storage classes and versioning for cost and recovery
- ◐ Serve public assets through a CDN with immutable object keys
- ◐ Clean up orphaned objects and enforce per-tenant storage quotas

**Warehouse, pipelines and event streams** (`references/streams-pipelines.md`)

- ● Decide when a warehouse is needed versus querying a read replica
- ◐ Load product, billing and marketing data into one warehouse
- ◐ Choose managed connectors or custom scripts for each data source
- ◐ Build tested, versioned SQL transformations into trusted metric tables
- ◐ Monitor pipelines with freshness and data-quality alerts
- ○ Sync warehouse segments back into CRM, email and ad tools
- ○ Stream database changes to search, cache and warehouse with change data capture
- ○ Design event streams with schemas, partition keys, ordering and replay

**Data lifecycle, retention and deletion** (`references/data-lifecycle.md`)

- ● Classify data by sensitivity and record where each class lives
- ◐ Build per-user data export and deletion that reaches every store
- ◐ Purge expired data automatically on a retention schedule
- ◐ Apply retention, deletion and pseudonymization rules to analytics data
- ◐ Delete a tenant completely at contract end and prove it
- ◐ Test that you can export your data from every datastore and SaaS vendor
- ○ Archive cold data to cheap storage while keeping it queryable
- ○ Encrypt sensitive fields at application level with managed keys
