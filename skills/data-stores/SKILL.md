---
name: data-stores
description: Decides when a product needs more than Postgres and runs what it adds, covering Redis caching, search and pgvector, S3 or R2 object storage, warehouses, pipelines, event streams, and retention and deletion. Use when asked whether to add Redis, Elasticsearch, a vector database or Kafka, to cache a slow read, add search, store user files, sync an index, load a warehouse, or delete a user's data everywhere.
---

# Data stores beyond the primary database

## Stance

Every store beyond Postgres is a second copy of some data, a sync mechanism that will have bugs,
and one more system to back up, secure, upgrade and include in every deletion. The expert move
is usually to not add it yet, and when it is added, to be exact about which store holds the
truth and how every other store is rebuilt from it.

- **Postgres until a measured workload fails on it.** Queue, cache, search, vectors, documents
  and time-partitioned events all have a serviceable Postgres form. A proposal for a new store
  needs a number, not a forecast.
- **One source of truth per fact; everything else is derived and disposable.** A cache, index or
  warehouse that cannot be dropped and rebuilt with a command in the repository has become a
  second database without backups.
- **Never dual-write from request code.** "Write the database, then call the other store"
  loses or reorders updates when the second call fails. Changes reach derived stores through a
  job or outbox row written in the same transaction, or through change data capture.
- **Cache what is displayed, not what is decided.** Balances, entitlements, payment state and
  permissions are read from the database at decision time. Stale display is a cosmetic bug;
  a stale decision is a financial or security one.
- **Tenant scope is part of every key and every query.** Cache keys, object keys, index
  documents and warehouse rows carry the tenant ID. It prevents cross-tenant leaks and is what
  makes tenant deletion, export and cost attribution possible later.
- **Search and signed URLs are second read paths.** They bypass the authorization in the main
  query layer unless the filter or check is built into them on the server.
- **Decide how data dies when deciding how it is stored.** Every key gets a TTL, every bucket
  a lifecycle rule, every table a retention answer, every new store a deletion handler.
  Retrofitting deletion across six stores is a project; adding it per store is a line.
- **Buy operations.** Added stores run as managed services. One person cannot be on call for a
  search cluster, a broker and a cache.
- **Prove it earned its place.** Record the baseline before adding a store, measure after, and
  remove what did not move the number.

## Route

| If the task is… | Read |
|---|---|
| "Do we need Redis, Elasticsearch, Mongo, DynamoDB, Kafka, ClickHouse, SQLite?"; picking a store for a workload; queue versus broker versus event log; reviewing an architecture with too many stores | `references/choosing-datastores.md` |
| Making a slow read fast with a cache; stale data after an edit; cache keys and invalidation; stampedes; Redis memory and eviction; rate limits, counters or locks in Redis | `references/caching-redis.md` |
| Adding a search box, autocomplete, filters and facets, typo tolerance; choosing Meilisearch, Typesense, Algolia or Elasticsearch; index out of sync; embeddings and similarity search in pgvector; poor results | `references/search.md` |
| Storing uploads, exports or assets in S3 or R2; private downloads and signed URLs; bucket settings; serving images through a CDN; a growing storage bill; orphaned files; storage quotas | `references/object-storage.md` |
| Getting product, billing and marketing data into one place; warehouse or replica; connectors, dbt models, pipeline alerts; reverse ETL; change data capture; designing event streams | `references/streams-pipelines.md` |
| Account deletion or data export; retention periods and purge jobs; deleting a tenant at contract end; what personal data lives where; vendor lock-in checks; archiving old rows; encrypting sensitive columns | `references/data-lifecycle.md` |

## Defaults at a glance

| Decision | Prototype | Launch | Scale |
|---|---|---|---|
| Stores | Postgres + object storage | Add Redis only for a concrete need | Search engine, warehouse, event log as measured needs appear, all managed |
| Cache | None; fix the query | HTTP/CDN first, then cache-aside in Redis with TTL + delete-on-write | Stale-while-revalidate on hot keys; per-key-family metrics |
| Redis instances | — | Separate instance for queue (`noeviction`) and cache (`allkeys-lru`) | Same, sized from measured memory |
| Rate limits | In-process or none | Redis sliding window via a maintained library | Fail-open or fail-closed decided per limit |
| Search | `ILIKE` with a trigram index | Postgres full-text + trigram | Hosted engine when typo tolerance, facets or ranking are measured needs |
| Vectors | pgvector, exact scan | pgvector with HNSW, tenant filter in SQL | Dedicated store only when pgvector's memory or recall fails |
| Index sync | — | Job enqueued in the write transaction + reconciliation sweep | Change data capture through a managed service |
| Files | Private bucket, row per object | Signed URLs at click time, lifecycle rules, versioning on user data | Reconciliation, quotas, second copy of critical data |
| Storage provider | The host's cloud, or R2 | Same; CDN in front of public assets | Revisit by egress bill |
| Analytics data | Product analytics tool | Read replica; rollup tables | Serverless warehouse, managed connectors, dbt, freshness alerts |
| Events between systems | Function calls | Postgres job queue, outbox | Managed broker or log when several consumers need replay |
| Retention | Do not collect what is not needed | Retention config + purge jobs; user deletion across all stores | Tenant deletion with proof; exit tests yearly |
| Field encryption | Third-party credentials only | Plus sensitive personal fields | Per-tenant keys where contracts require |

Constant at every stage: buckets private, a TTL on every cache key, tenant ID in every key and
index document, no personal data in cache keys or event payloads that outlive the user.

## Before you call it done

1. A new store has a written justification: the measured failing workload, what was tried in
   Postgres, its source of truth, and behavior when it is down.
2. Each derived store has a rebuild command in the repository, and it has been run at least in
   staging; the application degrades instead of failing with Redis stopped or the index dropped.
3. No request path writes to the database and then to another store directly; the change
   travels by a transactional job, outbox or CDC, and a reconciliation job reports drift.
4. Nothing in the never-cache list (balances, entitlements, payment state, authorization) is
   read from a cache at decision time.
5. Every cache key contains environment, schema version and tenant or user scope, has a TTL,
   and cached values are validated on read.
6. Redis has an explicit `maxmemory` policy that matches its use, and queue data does not share
   an evicting instance.
7. A test with two tenants proves that search, autocomplete, facets and vector queries return
   nothing across the boundary; no unscoped search key reaches the browser.
8. Buckets block public access; every object has a database row with tenant, key, size and
   status; object keys contain no user-supplied filename.
9. Private downloads go through an authorization check and a signed URL of minutes, generated
   at click time; no signed URL is stored or emailed.
10. Lifecycle rules exist: abort incomplete multipart uploads, expire temporary prefixes, expire
    noncurrent versions.
11. Pipelines are idempotent, tested on keys, reconciled against the source for money metrics,
    and alert on freshness; any replication slot is monitored for retained WAL.
12. The data map lists the new store or vendor with data class, retention and deletion
    mechanism, and a deletion handler exists for it.
13. The deletion test passes: after deleting a test user or tenant, no store returns their ID
    or email, and the deletion log would replay after a backup restore.
14. Purge jobs report the age of the oldest remaining row and alert when it exceeds retention.
15. Hit rate, latency or cost was measured before and after, and the result is stated.

## Not this skill

- Schema design, SQL, indexes, migrations and backups in Postgres → `0x:postgres-database`
- HTTP and CDN caching headers and purging → `0x:web-networking`
- Job queues, retries, scheduled jobs and workflows → `0x:backend-architecture`
- The upload flow: validation, scanning and processing of user files → `0x:backend-architecture`
- Analyzing data, writing analytics SQL and building dashboards → `data`
- Legal duties behind retention and deletion requests → `0x:privacy-compliance`
