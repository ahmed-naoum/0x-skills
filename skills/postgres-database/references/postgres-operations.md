# Running Postgres in production

Read this when: choosing a Postgres provider, running out of connections, setting up a pooler or
database roles, deciding what to monitor, stopping a runaway query, using database branches, or
planning vacuum maintenance, tuning or a version upgrade.

## Choosing a managed provider

Run managed Postgres. Self-hosting means owning backups, failover, patching and upgrades; take
that on only at Scale, with someone who has done it before.

| Check | What to verify on the plan being bought |
|---|---|
| Backups | Point-in-time recovery included or a paid add-on; retention window; whether a logical dump can be taken out |
| Limits | `max_connections`, storage and compute ceilings, the extension list, and whether logical replication is allowed (it is the exit path) |
| Availability | Standby in a second zone with automatic failover; whether lower tiers pause when idle or cold-start |
| Location | Same region as the application; a private network path. Each query pays the round trip, so a cross-region database multiplies latency by the number of queries per request |
| Pooling | A built-in pooler, and separate pooled and direct connection strings |
| Support | Who answers during an outage on this plan, and how fast |
| Exit | Standard Postgres reachable with `pg_dump` and logical replication. Provider-only APIs (bundled auth, storage, realtime) raise the cost of leaving |

Families: the cloud's own service (Amazon RDS and Aurora, Google Cloud SQL, Azure Database for
PostgreSQL) when the application already runs there or compliance demands it; serverless with
branching (Neon) for preview-heavy workflows; a backend platform (Supabase) when its auth and storage
are wanted too; the application platform's own add-on; a Postgres specialist (Aiven, Crunchy Bridge)
for support depth. These vendors are acquired and repackaged often: confirm the product is still
sold, and on what terms, before recommending one by name.

Default: Prototype uses whatever the application's platform offers in one click. From Launch, a
paid tier in the application's region with point-in-time recovery, no idle pausing and a pooler;
free tiers commonly pause, cap storage and keep minimal backups. Verify on the current plan page.

## Connection budget

Each connection is a server process holding memory, and throughput falls when far more queries
run at once than there are cores. `max_connections` is fixed by the instance size; raising it is
rarely the fix.

Budget: (web instances x pool max) + (workers x pool max) + 10 for migrations, admin and
monitoring must stay at or below 80 percent of `max_connections`. Count the maximum instance
number during a rolling deploy, when old and new run together. A pool of 5 to 10 per Node.js
process is usually plenty; a bigger pool does not make queries faster, it only moves the queue
into the database.

```ts
import { Pool } from "pg";

const g = globalThis as unknown as { pgPool?: Pool };
export const pool = (g.pgPool ??= new Pool({
  connectionString: process.env.DATABASE_URL, // the pooled URL at runtime
  max: 10,                        // per process; must fit the connection budget
  connectionTimeoutMillis: 3_000, // fail fast instead of queueing forever
  idleTimeoutMillis: 30_000,
  maxLifetimeSeconds: 1_800,      // recycle so connections rebalance after a failover
  application_name: "web",
}));
```

Create the pool once per process. In Next.js development, hot reload re-evaluates modules and
leaks a pool each time unless it is cached on `globalThis` as above. Set `application_name` per
service so sessions can be attributed.

| Error or symptom | Cause | Fix |
|---|---|---|
| `53300 too many clients already` | Budget exceeded | Count by user and application (monitoring query below); shrink pools or add a pooler |
| Many sessions `idle` | Pools too large, or one pool per request | One shared pool; lower `max` |
| Many `idle in transaction` | Code opens a transaction and awaits something else | Fix the code path; set the idle-in-transaction timeout |
| Many `active` for seconds | Slow queries or lock waits, not a connection problem | `indexes-query-plans.md`, `transactions-concurrency.md` |
| Pool acquire timeouts while the database is calm | Pool smaller than in-process concurrency, or connections leaked without release | Always release in `finally`; check for a client held across awaits |

## PgBouncer and serverless

Add a pooler when the number of client processes is unbounded or large: serverless functions (each
instance opens its own connections, and instances scale without limit), many small containers, or
more than a few hundred clients. Use the provider's pooler when it has one.

- **Transaction mode** is the point: a server connection is lent for one transaction, so thousands
  of clients share tens of connections. Session mode multiplexes nothing.
- Transaction mode breaks session state: session-level `SET` (use `SET LOCAL`), session advisory
  locks, `LISTEN`, temporary tables kept across transactions, SQL-level `PREPARE`. Protocol-level
  prepared statements work on PgBouncer 1.21 and later with `max_prepared_statements` set above zero
  (its default changed between releases); on older or other poolers, disable them in the driver.
- Keep two URLs. Pooled for application traffic. Direct for migrations, `pg_dump`, logical
  replication, `LISTEN/NOTIFY` and long maintenance sessions. Some providers' direct hosts are
  IPv6-only; a CI runner without IPv6 then needs the session-mode pooler for migrations.
- In a function, set the client pool to 1 to 3 connections against the pooled URL, and cap function
  concurrency (`0x:cloud-infrastructure`). Edge runtimes without TCP need the provider's HTTP or
  WebSocket driver.

```ini
[pgbouncer]
pool_mode = transaction
max_client_conn = 2000
default_pool_size = 20
query_wait_timeout = 15
max_prepared_statements = 200
```

`default_pool_size` is server connections per database/user pair, the real concurrency on
Postgres: its sum over every pair goes into the budget above, not `max_client_conn`.
`query_wait_timeout` is the seconds a client may wait for a server connection before failing.

## Roles

| Role | May | Used by |
|---|---|---|
| `app_migrator` | Owns the schema; DDL | The migration step only |
| `app_rw` | SELECT, INSERT, UPDATE, DELETE | The application; one such role per service at Scale |
| `app_ro` | SELECT; read-only by default | Dashboards, support tooling, people |

```sql
REVOKE ALL ON DATABASE app FROM PUBLIC;
GRANT CONNECT ON DATABASE app TO app_migrator, app_rw, app_ro;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO app_migrator;   -- or make it the schema's owner
GRANT USAGE ON SCHEMA public TO app_rw, app_ro;

ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
  GRANT SELECT ON TABLES TO app_ro;

ALTER ROLE app_rw CONNECTION LIMIT 40;
ALTER ROLE app_ro SET default_transaction_read_only = on;
ALTER ROLE app_ro SET statement_timeout = '60s';
```

- The application never connects as the owner or the provider's admin user. An owner can drop
  tables, and owners and superusers bypass row-level security (tenant isolation with RLS is in
  `0x:backend-architecture`).
- Default privileges apply only to objects created later by the role named in `FOR ROLE`; existing
  tables need a one-time `GRANT ... ON ALL TABLES IN SCHEMA public`. A table created by any other
  role is invisible to the application: the usual cause of "permission denied" after manual DDL.
- `TRUNCATE` is a separate privilege and is not in the list. Append-only tables additionally get
  `REVOKE UPDATE, DELETE` (`backup-recovery.md`).
- `default_transaction_read_only` is a guard rail, not a boundary: a session can switch it off.
  The grants are the boundary.
- Separate roles give separate timeouts, connection limits, credentials and attribution in
  `pg_stat_activity`; people get individual read-only logins. Require `sslmode=verify-full` where
  the provider publishes a CA. Credential storage and rotation are in `0x:web-security`.

## Monitoring

| Signal | Source | Alert at |
|---|---|---|
| Connections used | `count(*)` from `pg_stat_activity` against `max_connections` | 80 percent |
| Oldest transaction; idle in transaction | `xact_start`, `state` in `pg_stat_activity` | 5 minutes; 1 minute |
| Sessions waiting on locks | `wait_event_type = 'Lock'` | Any for more than 30 seconds |
| Disk free | Provider metric | Warn at 20 percent, page at 10. A full disk stops the database |
| CPU, I/O credits, IOPS saturation | Provider metrics | Sustained above 80 percent |
| Cache hit ratio | `blks_hit / (blks_hit + blks_read)` in `pg_stat_database` | A falling trend; healthy transactional workloads sit near 99 percent |
| Replication lag; WAL retained by slots | `replication-scaling.md` | Seconds of lag; any inactive slot |
| Transaction-ID age | `age(datfrozenxid)` in `pg_database` | 500 million |
| Dead rows; last autovacuum | `pg_stat_user_tables` | Dead rows far above live rows; no autovacuum for days on a busy table |

```sql
SELECT usename, application_name, state, count(*)
FROM pg_stat_activity WHERE backend_type = 'client backend'
GROUP BY 1, 2, 3 ORDER BY count(*) DESC;

SELECT pid, usename, application_name, state, wait_event_type, wait_event,
       now() - xact_start AS xact_age, now() - query_start AS query_age, left(query, 80) AS query
FROM pg_stat_activity
WHERE backend_type = 'client backend' AND state <> 'idle' AND pid <> pg_backend_pid()
ORDER BY xact_start NULLS LAST;
```

Prototype: the provider's dashboard is enough. From Launch: alerts on the first five rows, and
`log_min_duration_statement` (500 ms), `log_lock_waits` and `pg_stat_statements` turned on. The
other rows at Scale or once replicas exist. Routing alerts and dashboards: `0x:site-reliability`.

## Killing a runaway query

1. Identify it with the second query above: pid, role, application, age, statement.
2. Decide what it is. If it is the root blocker of others, it is the target
   (`transactions-concurrency.md`). Leave alone an autovacuum marked "(to prevent wraparound)" and
   replication senders. A backup or migration needs a decision, not a reflex.
3. `SELECT pg_cancel_backend(<pid>);` cancels the running statement and keeps the session.
4. If the session is `idle in transaction` (nothing to cancel) or the cancel has no effect within
   seconds: `SELECT pg_terminate_backend(<pid>);` closes the connection and rolls back.
5. Never `kill -9` a backend process: Postgres treats it as a crash and restarts, dropping every
   connection.
6. Stop the source, or it returns: a job that retries, a user who clicks again, a cron entry. Then
   give that role a `statement_timeout`.

Rollback is immediate in Postgres; the dead rows left behind are cleaned by vacuum. On managed
services the admin user can signal other roles' sessions through membership in `pg_signal_backend`. Bulk form:
`SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND now() - state_change > interval '10 minutes';`

## Serverless Postgres and branching

A branch is a copy-on-write clone of the database at a point in time, created in seconds whatever
the size and billed for what diverges. Uses: a database per pull-request preview, created on open
and deleted on close (wiring in `0x:ci-cd-release`); migration rehearsal on production-sized data;
a branch from a past timestamp to see data as it was during an incident; a branch reset from its
parent before each end-to-end test run.

- A branch of production contains production personal data. Previews and tests should branch from
  a masked or seeded parent; reserve production branches for rehearsal by people entitled to see
  that data. Seeding and anonymization are in `0x:code-quality` and `0x:ci-cd-release`.
- Scale-to-zero means the first connection after idle pays a cold start. Turn it off for the
  production database; keep it on for branches.
- Give branches a time to live. Forgotten branches accumulate storage cost and copies of data.
- Unit and integration tests are faster and work offline against a local Postgres in a container.
  Branching is a provider feature, not a Postgres one: keep the workflow replaceable.

## Vacuum, bloat and wraparound

Updates and deletes leave dead row versions; autovacuum reclaims them and also freezes old
transaction ids. Never disable it. Two things go wrong.

**It runs too rarely on big tables.** The default trigger is 20 percent dead rows, which on a
100-million-row table is 20 million. Lower it per table, and do the same for queue-like tables (on a
partitioned table set it on each partition: the parent accepts no storage parameters):

```sql
ALTER TABLE events SET (autovacuum_vacuum_scale_factor = 0.01, autovacuum_analyze_scale_factor = 0.01);
```

**It runs but cannot remove anything**, because something still needs the old rows:

```sql
SELECT pid, state, age(backend_xmin) AS xmin_age, now() - xact_start AS xact_age, left(query, 60) AS query
FROM pg_stat_activity WHERE backend_xmin IS NOT NULL ORDER BY age(backend_xmin) DESC LIMIT 5;

SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;
```

Long transactions, abandoned replication slots, forgotten prepared transactions (`pg_prepared_xacts`)
and replicas with `hot_standby_feedback` running long queries all hold cleanup back for the whole
database. Remove the holder; vacuum then catches up by itself.

Bloat is space vacuum freed inside a table but did not return to the disk; plain `VACUUM` gives
back only empty pages at the end of the file. Shrink a table online with the `pg_repack` extension
(most providers offer it) or, from PostgreSQL 19, the built-in `REPACK (CONCURRENTLY)`; it is new,
so read its documented restrictions and rehearse on a copy. Shrink an index with `REINDEX INDEX
CONCURRENTLY`. `VACUUM FULL` locks the table exclusively for its whole rewrite.

Wraparound: transaction ids are 32-bit, so every table must be frozen before its oldest id is
about two billion transactions old. Autovacuum forces a freeze at 200 million. If blockers stop it
for long enough, Postgres finally refuses writes to protect data. Watch `age(datfrozenxid)`; when
it climbs past 500 million, clear the blockers above and run
`VACUUM (FREEZE, INDEX_CLEANUP OFF) <table>;` on the oldest tables, found with
`SELECT oid::regclass, age(relfrozenxid) FROM pg_class WHERE relkind = 'r' ORDER BY 2 DESC LIMIT 10;`

## Tuning

Managed providers preset memory, and a missing index outweighs every setting here: skip this until
Scale or a measured problem. Then change one setting at a time, measured with `pg_stat_statements`:

| Setting | Guidance |
|---|---|
| `shared_buffers` | About 25 percent of memory; usually preset |
| `effective_cache_size` | 50 to 75 percent of memory. A planner hint, allocates nothing |
| `work_mem` | Per sort or hash node, per query, so many can be in use at once. Keep the global value small (4 to 16 MB) and raise it per role or with `SET LOCAL` for reporting |
| `maintenance_work_mem` | 5 to 10 percent of memory, up to 1 to 2 GB. Speeds index builds and vacuum |
| `random_page_cost` | 1.1 on SSD or network block storage. The default of 4 assumes spinning disks and biases against index scans |
| `max_wal_size` | Raise (4 GB or more) on write-heavy systems when the log reports checkpoints occurring too frequently |
| `jit` | `off` for transactional workloads |
| `track_io_timing`, `log_autovacuum_min_duration` | On, and a low threshold, so plans and logs show where time goes |

## Major version upgrades

Minor releases are bug and security fixes with no behavior change: apply them promptly in the
provider's maintenance window. Each major version is supported for five years; plan a major
upgrade every year or two rather than at the deadline, and let a new major version reach its
first or second minor release before adopting it.

| Method | Downtime | Use when |
|---|---|---|
| Provider in-place upgrade (`pg_upgrade` underneath) | Minutes; depends on the number of objects more than on data size | The default |
| Dump and restore into a new instance | Grows with data size | Small databases, up to a few tens of gigabytes |
| Logical replication to a new instance, then cut over | Seconds to a minute | Downtime must be minimal; same steps as a provider move in `replication-scaling.md`. Some providers package it as blue/green deployment |

1. Read the release notes' migration section for every version crossed. Check that each extension
   in use exists for the target.
2. Run the application's test suite against the new version.
3. Rehearse on a restored copy or clone: time the upgrade and run the slowest known queries.
4. Take a snapshot and verify it (`backup-recovery.md`). After writes land on the new version, the
   only way back is that snapshot, with data loss, which is why the rehearsal matters.
5. Upgrade in the quietest hour. Afterwards run `ANALYZE` (before PostgreSQL 18 the upgrade drops
   planner statistics and queries crawl until it finishes), update extensions with `ALTER EXTENSION
   ... UPDATE`, reindex if the release notes say so, and recreate replicas the provider left behind.
6. Watch `pg_stat_statements` for plan regressions for a day.

## Ask the user

- **Where does the application run, and which cloud accounts already exist?** The database belongs
  in the same region and ideally the same network. Default: the application platform's own
  Postgres or a provider in the same region.
- **What monthly spend on the database is acceptable?** High availability roughly doubles it.
  Default: single node with point-in-time recovery at Launch; standby when an hour of downtime
  costs more than a month of the standby.
- **Who may read production data, and who may change it?** Sets the human roles. Default: founder
  only, read-only login for daily use, a separate write role.
- **Is there a compliance or data-residency requirement (region, HIPAA, SOC 2)?** It narrows the
  provider list before anything else. Default: none; region nearest to most customers.
