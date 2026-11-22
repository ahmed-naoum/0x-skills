---
name: postgres-database
description: Models, queries, migrates, tunes, backs up and scales a relational database with PostgreSQL as the default. Use when designing a schema or choosing keys and an ORM, fixing a slow query or pegged database CPU, writing a migration that must not lock tables, debugging a race or running out of connections, setting up or restoring backups, recovering deleted data, or deciding on replicas and partitioning.
---

# PostgreSQL and relational data

## Stance

The schema and its data outlive every version of the code, and database mistakes are the ones a
redeploy cannot undo. Work like the engineer who has been paged for each of them: constraints
before code, measurement before tuning, no statement that waits on a lock without a timeout, and
no backup trusted until it has been restored.

- **The schema enforces the invariants.** A rule that lives only in application code is broken by
  the second code path, a script or a race. NOT NULL, CHECK, UNIQUE, foreign keys and exclusion
  constraints cannot be bypassed.
- **One Postgres until measurement says otherwise.** Queue, search, JSON documents and scheduled
  work fit in it at Prototype and Launch; every extra store is another system to operate.
- **Measure, then change.** Rank statements by total time in `pg_stat_statements` and read
  `EXPLAIN (ANALYZE, BUFFERS)` on production-sized data. A plan from a seed database proves nothing.
- **Every schema change overlaps two application versions.** Migrations expand first and contract
  later, set `lock_timeout`, and never rewrite or scan a large table under an exclusive lock,
  because a waiting `ALTER` queues every other query on that table behind it.
- **Make critical writes safe by construction.** Atomic statements, constraints and explicit row
  locks at the default isolation level. Keep transactions short with no network call inside: an
  open transaction holds a connection, its locks and vacuum.
- **Connections are a small fixed budget.** Size pools against `max_connections` and give every
  role statement, lock and idle-in-transaction timeouts, so one bad query costs a few requests
  instead of the whole pool.
- **A backup exists once a restore from it has been performed and timed.** Replicas copy a mistake
  within milliseconds and are not backups.
- **Production data changes are reviewed, counted, transactional and reversible.** Never run a
  writing statement against production until the user has seen the exact statement and the
  affected row count and has said yes: after commit the only undo is a before-image or a restore.
- **Scale in order.** Query, index, pooler, bigger instance, cache, replica, partition, shard.
  Each later step costs more to operate than all the earlier ones together.

## Route

| If the task is | Read |
|---|---|
| Designing or reviewing tables, keys, constraints or column types; UUID or integer ids; ORM or raw SQL; storing money, JSON, soft deletes, history, trees or polymorphic relations | `references/schema-modeling.md` |
| Writing or reviewing a query, upsert, bulk write or pagination; removing N+1 queries; checking what the ORM generates; running SQL by hand against production; a one-off data fix | `references/sql-queries.md` |
| Two requests raced, a counter or balance went wrong, writes must be all-or-nothing, queries block each other, deadlocks appear in logs, or a queue or run-once job is being built | `references/transactions-concurrency.md` |
| A query or endpoint is slow, database CPU or I/O is high, a plan got worse, or deciding which index to add or drop | `references/indexes-query-plans.md` |
| Any schema change on a database with live traffic: columns, indexes, constraints, renames, retypes, backfills, or a migration that failed halfway | `references/migrations.md` |
| Choosing a provider, "too many connections", pooler or serverless setup, database roles, what to monitor, killing a query, preview branches, vacuum and bloat, tuning, a major-version upgrade | `references/postgres-operations.md` |
| Setting up backups, proving a restore works, a snapshot before a risky change, deleted or corrupted production data, restoring one customer's rows | `references/backup-recovery.md` |
| One node is not enough: standby and failover, read replicas and lag, reports slowing the app, partitioning a huge table, sharding, moving providers with little downtime | `references/replication-scaling.md` |

## Defaults at a glance

Read what the project already uses first (ORM, migration tool, key scheme, provider) and stay
consistent with it. These apply to greenfield choices and when the user asks what to pick.

| Decision | Default | Changes when |
|---|---|---|
| Database | Managed PostgreSQL in the application's region, on a supported major version past its first minor releases | Self-host only at Scale, with someone who has run it before |
| Provider tier | Prototype: the platform's one-click database. Launch: a paid tier with point-in-time recovery, no idle pausing and a pooler | Compliance or data residency narrows the list first |
| Data access | Typed SQL-first layer (Drizzle); raw parameterized SQL for window functions, recursion, bulk writes and locking clauses | The project already has an ORM: keep it |
| Primary keys | UUIDv7 for anything exposed; `bigint` identity for internal high-volume tables | The project already has one scheme |
| Column types | `timestamptz`, `text` plus `CHECK`, `bigint` minor units with a currency code, `jsonb` only for variable attributes | |
| Deletes | Hard delete, with `ON DELETE RESTRICT` from money and history tables | A trash window for customer-created top-level objects |
| Concurrency | READ COMMITTED with atomic or guarded updates; a version column for records users edit | SERIALIZABLE with retries for one transaction type whose invariant cannot be locked |
| Timeouts, web role | `statement_timeout` 10 s, `lock_timeout` 3 s, idle-in-transaction 30 s, pool acquire 3 s | Longer on worker and reporting roles; migrations set their own |
| Pool | 5 to 10 connections per Node.js process; all pools together at most 80 percent of `max_connections` | Transaction-mode pooler for serverless or hundreds of clients |
| Roles | A migrator role owns the schema; the application role has DML only; a read-only role for people | One application role per service at Scale |
| Pagination | Keyset with a unique tiebreaker | `OFFSET` only for small, bounded admin lists |
| Migrations | Generated SQL read by hand, applied by the pipeline, forward-only, indexes built `CONCURRENTLY` | A short announced window can replace a multi-deploy change |
| Backups | Prototype: provider dailies. Launch: point-in-time recovery of 7 days or more, an off-provider dump, one restore drill. Scale: immutable copies in a second account and region, automated restore tests | A contract or regulation fixes retention |
| Availability | One node at Prototype and Launch | A standby once an hour of downtime costs more than a month of the standby |
| Scaling | A bigger instance before replicas; partition only large append-mostly tables; sharding last | Evidence, as laid out in `references/replication-scaling.md` |

## Before you call it done

1. Every invariant of the feature is a named constraint, and each foreign key has a deliberate
   `ON DELETE` and an index on the referencing column.
2. Moments are `timestamptz`, money is `bigint` minor units with a currency, ids follow the
   project's one scheme, and application code names its columns instead of `SELECT *`.
3. Each new or changed query was run with `EXPLAIN (ANALYZE, BUFFERS)` on production-sized data
   using a large tenant's parameters: no unexpected sequential scan, estimates within 10x of actual.
4. List endpoints run a fixed number of queries whatever the row count, and paginate by keyset.
5. Multi-step writes run in one transaction through the transaction handle with no external call
   inside; read-modify-write paths use an atomic or guarded update, a version check or a row lock.
6. The migration SQL was read line by line: `lock_timeout` set, indexes built `CONCURRENTLY`,
   constraints added `NOT VALID` then validated, nothing renamed or dropped that deployed code names.
7. The migration works with the previous application version and with the next one.
8. Backfills run in keyed batches that commit, skip finished rows and can resume, then `ANALYZE`.
9. After migrating, no invalid index and no unvalidated constraint remains (queries in
   `references/migrations.md`).
10. The application connects as a non-owner role that carries statement, lock and
    idle-in-transaction timeouts, and the pools at maximum instance count fit the connection budget.
11. Any manual production write was shown to the user with its row count, approved, run inside a
    transaction and has a before-image.
12. From Launch: point-in-time recovery is on, its restorable window was read off the provider, and
    a timed restore drill is on record.
13. Before a destructive or irreversible change: a verified snapshot, the timestamp noted, the
    restore path written down.
14. Where a replica exists: reads sent to it tolerate lag and never decide a write, and alerts on
    lag and on replication slots exist.
15. From Launch: `pg_stat_statements` and slow-statement logging are on; alerts cover connections,
    disk and long transactions.

## Not this skill

- Redis, search engines, object storage, warehouses and other non-relational stores: `0x:data-stores`
- Analytics queries, reporting SQL and statistics on business data: the `data` skill
- Choosing a multi-tenancy model and row-level tenant isolation: `0x:backend-architecture`
- SQL injection and other vulnerability classes: `0x:web-security`
- Running the migration step inside the deploy pipeline: `0x:ci-cd-release`
- Company-wide disaster recovery plans, RPO and RTO: `0x:site-reliability`
