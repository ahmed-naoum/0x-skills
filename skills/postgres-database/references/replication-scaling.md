# Replication and scaling

Read this when: one database node is no longer enough or soon will not be, adding a standby or a
read replica, replicas are lagging, reports are slowing the application, a table has grown too
large to maintain, or moving to another provider or major version by replication.

## Which move, and in what order

Name the exhausted resource before choosing a mechanism; each mechanism fixes one thing.

| Evidence | Move | Will not help |
|---|---|---|
| A few statements dominate `pg_stat_statements` | Fix queries and indexes (`indexes-query-plans.md`). Always first | Hardware |
| Connection errors while CPU is calm | Pool sizing or a pooler (`postgres-operations.md`) | Replicas, a bigger instance |
| CPU or I/O saturated across many already-tuned statements; cache hit ratio falling | A bigger instance | |
| Reads still saturate the largest instance worth paying for | Cache (`0x:data-stores`), then read replicas | Partitioning |
| Reports, exports or BI tools slow the application | Reporting replica, later a warehouse | A bigger instance, for long |
| One append-mostly table dominates size; retention deletes and vacuum on it hurt | Partition by time and drop old partitions | Replicas |
| An hour of downtime after a node or zone failure is unacceptable | Standby with automatic failover | Read replicas, backups |
| Write volume or total size beyond the largest instance, after archiving | Split a domain out, then shard by tenant | Replicas: each one applies every write |

Replicas scale reads and availability, never writes. Partitioning buys cheap retention and smaller
vacuums and indexes, not general query speed: a B-tree lookup in a billion rows reads one or two
more pages than in ten million. Prototype and Launch run one node with point-in-time recovery; add
a standby when an hour of downtime costs more than a month of the standby. Replicas and
partitioning are Scale work, done on evidence.

Sharding, different tenants in different databases, is the only move that scales writes, and it
costs more than all the others together: no cross-shard joins, transactions or unique constraints,
and every migration, backup and upgrade multiplied by the shard count. Before it, archive cold
data and move a self-contained high-volume domain (events, logs) to its own database or a store
built for it (`0x:data-stores`). Then shard by tenant, with a directory mapping tenant to database
or a distributed extension such as Citus. The cheap insurance from the first schema is `tenant_id`
on every tenant-owned table, leading its indexes (`0x:backend-architecture` covers tenancy models).

## Vertical scaling and where it ends

A bigger instance takes minutes and no code; every horizontal move is permanent complexity. As a
rule of thumb, one well-indexed node on current hardware carries thousands of transactions per
second and hundreds of gigabytes to a few terabytes. Before each doubling, spend an hour on the
top of `pg_stat_statements`; one index often returns more than the next size.

- Size memory so hot tables and indexes stay cached, and CPU so the daily peak stays under about
  70 percent: vacuum, index builds and catch-up after a failover need the rest.
- Storage speed is often bought separately from size. A volume at its IOPS or throughput cap looks
  like a slow database with idle CPU and sessions waiting on I/O (`wait_event_type = 'IO'`).
- Avoid burstable instance classes in production: when CPU credits run out the instance is
  throttled, which appears as a sudden slowdown with no change in load.
- A resize restarts the instance or fails over to a resized standby: a brief reconnect with a
  standby, minutes of downtime without. Storage usually grows online and cannot shrink.

Vertical scaling is exhausted when, after tuning, the next size does not exist or costs more than
the engineering to avoid it; or writes are the limit (WAL outruns what a replica can replay, or
autovacuum cannot keep up on the largest tables); or size is the limit (restore, upgrade or
index-build time exceeds what the business tolerates). For size, first delete or archive rows
nobody reads (`0x:data-stores` covers retention), then partition.

## Standby and failover rehearsal

On a managed service the standby is the high-availability option: a copy in another zone, fed by
physical replication and promoted automatically. It is not a backup: it replays a bad `DELETE`
within milliseconds (`backup-recovery.md`). Check on the plan in use:

- Synchronous or asynchronous. Asynchronous can lose commits acknowledged in the last moments
  before the failure. Synchronous loses none, and every commit waits for the standby.
- Whether the standby serves reads. Often it does not, so it is no substitute for a read replica.
- Whether the hostname survives a failover, and what happens to read replicas and logical
  replication slots when the primary changes.

The provider's side usually works. The application's side is what a rehearsal exposes:

| Symptom after failover | Cause | Fix |
|---|---|---|
| Errors continue after the database is healthy again | The pool keeps dead connections, or an address is cached | Evict connections on error, cap their lifetime, connect by hostname |
| `25006`, cannot execute INSERT in a read-only transaction | A connection is still attached to the demoted node | Destroy that connection and reconnect; do not retry on it |
| A record the user saw saved is gone | Asynchronous replication lost the tail | Reconcile money paths against the payment provider; synchronous mode if that loss is unacceptable |
| Change-data or logical subscribers stop | The logical slot did not follow the failover | Slot synchronization (PostgreSQL 17+) or the provider's equivalent; otherwise re-seed |

Rehearse in staging first, then in production in a quiet, announced hour:

1. Start a probe that inserts one timestamped row per second and logs every error.
2. Trigger the provider's failover action.
3. Measure the seconds until the probe writes again and the errors each service saw. Requests and
   jobs in flight are rolled back, so retries and job handlers must be idempotent.
4. Confirm web, workers, schedulers, the pooler and reporting tools recovered without a restart,
   the new standby is in sync, replicas follow the new primary, backups continue, alerts fired.
5. Record the numbers in the runbook. Repeat yearly and after changing driver, pooler or provider.

Self-hosted high availability needs a cluster manager (Patroni is the usual choice) and fencing of
the old primary; hand-written promotion scripts end in split brain. Leave it to a provider.

## Replication lag

```sql
-- Primary: one row per connected replica
SELECT application_name, state, sync_state, replay_lag,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS behind
FROM pg_stat_replication;
-- Replica: seconds behind, without the false alarm when the primary is idle
SELECT CASE WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 0
            ELSE extract(epoch FROM now() - pg_last_xact_replay_timestamp()) END AS lag_seconds;
```

| Signal | Alert at (starting points) | Because |
|---|---|---|
| Lag on a replica serving application reads | Warn at 5 s for 5 minutes; page at the staleness the routing code assumes | Users read stale data |
| Lag on the standby | 30 s sustained | With asynchronous replication this is the data lost at failover |
| Fewer rows in `pg_stat_replication` than replicas expected | 5 minutes | A disconnected replica can report zero lag from its own side |
| A replication slot inactive, or its retained WAL growing (slot query in `postgres-operations.md`) | 15 minutes; a few gigabytes | An abandoned slot keeps WAL until the primary's disk is full. `max_slot_wal_keep_size` caps that by sacrificing the slot; the default is unlimited |

| Cause of lag | Sign | Fix |
|---|---|---|
| Write burst: backfill, bulk load, large index build | Lag rises with the job | Throttle batches on lag (`migrations.md`) |
| Long query on the replica blocks replay | Lag climbs to `max_standby_streaming_delay` (30 s by default), then the query dies with "canceling statement due to conflict with recovery" | Keep replica queries short; long ones go to a reporting replica |
| Replica smaller or on slower storage than the primary | Lag at every peak | Same class as the primary |
| Sustained writes above what replay can apply | Lag never recovers | Fewer writes (drop unused indexes, batch); beyond that this is the vertical limit |

## Reporting off the primary

A report that scans for minutes on the primary evicts hot pages from the cache, saturates I/O and,
while its transaction is open, stops vacuum from cleaning any table. In order of cost:

1. Launch: a read-only role with `statement_timeout`, a connection limit and its own `work_mem`;
   heavy reports at quiet hours; dashboards read summary tables or materialized views.
2. Scale: a dedicated reporting replica for BI tools, exports, analyst sessions and `pg_dump`. Not
   the standby, and not the replica that serves application reads.
3. When queries scan years of history or join other sources: a warehouse fed by a pipeline
   (`0x:data-stores`). The analysis itself belongs to the `data` skill.

On a reporting replica, long queries conflict with replay. Raise `max_standby_streaming_delay`
there to the longest report: replay waits, and the replica falls behind while a report runs, which
is acceptable for reporting. The alternative, `hot_standby_feedback = on`, makes the primary keep
the rows those queries need and bloats it; leave it off so reporting can never hurt the primary.
A physical replica is an exact copy: no extra indexes, no extra tables, no temporary tables.
Indexes for reports go on the primary and tax its writes, which is one signal for a warehouse.

## Routing reads to replicas

Default: everything reads from the primary. Move reads one call site at a time by explicitly
choosing a second client (`dbRead`), and only reads that are heavy and tolerate staleness: search
and list pages, dashboards, exports, public pages. Helpers that send every `SELECT` to a replica
(Drizzle's `withReplicas`, Prisma's read-replicas extension) invert that default; where the
project uses one, force the primary for these, which always stay there:

- Reads inside a transaction that writes, and anything that takes locks or claims queue rows.
- Reads that decide a write: balance and stock checks, uniqueness and idempotency lookups,
  permission and session checks.
- What a user sees right after their own write.

| Technique | How | Use |
|---|---|---|
| Sticky primary | After a write, keep "read from the primary until now + N" in the session, with N well above normal lag (5 s is a common start) | Default |
| Position token | After the write, read `pg_current_wal_lsn()` on the primary and keep it in the session; before a replica read, check `SELECT pg_last_wal_replay_lsn() >= $1::pg_lsn` on the same connection and fall back to the primary when false | When "sees own write" must be exact |
| Lag breaker | A health check removes a replica from rotation when its lag passes the threshold or it is unreachable | Always, with either of the above |

Once replicas carry load they are production capacity: size for one more than the load needs, and
when one is lost shed replica-only traffic (exports, dashboards) rather than dumping it all on the
primary. Each replica has its own connection budget.

## Promoting a replica and rebuilding the old primary

Managed failover does this by itself. Promoting a managed read replica by hand (region loss,
provider exit) makes it a standalone database with its own endpoint, and other replicas usually
do not re-attach to it. The self-managed sequence, which is also what to verify a provider did:

1. Fence the old primary: stop it or cut it off from every client. If it can still accept writes
   after the promotion, two databases diverge and nothing merges them.
2. Choose the replica that received the most WAL (highest `pg_last_wal_receive_lsn()`).
3. Promote it with `SELECT pg_promote();`. It starts a new timeline and accepts writes.
4. Point the pooler or connection secret at it and verify a write.
5. Account for the loss. With asynchronous replication, commits that never left the old primary
   are missing. If its disk survives, start it isolated and extract rows newer than the promotion
   for reconciliation (method in `backup-recovery.md`).
6. Rebuild the old primary as a replica. It cannot simply reconnect if it holds WAL the new
   primary never received. Default: wipe it and take a fresh copy with
   `pg_basebackup --write-recovery-conf`. When a full copy would take hours, use `pg_rewind`,
   which needs `wal_log_hints = on` or data checksums to have been enabled beforehand.
7. Until the rebuilt node has caught up there is no redundancy: postpone risky changes. Then
   re-check what hung off the old primary: WAL archiving, logical slots, other replicas, monitoring.

## Partitioning by time or tenant

Partition when a table is past roughly 100 GB or a few hundred million rows and one of these
holds: rows are deleted by age (dropping a partition is instant, `DELETE` leaves bloat and WAL),
vacuum or index maintenance on it takes hours, or only recent data is hot and its indexes should
fit in memory. Below that, a batched retention job is simpler.

| Key | Fits | Notes |
|---|---|---|
| Time range on `created_at` | Events, logs, audit rows, notifications, metrics | The default. Monthly; daily only at very high volume. Keep the count in the low hundreds |
| Tenant by `LIST` | A handful of very large tenants kept apart from the rest | Not one partition per tenant for thousands of tenants: planning time grows with the partition count |
| Tenant by `HASH` | Spreading one huge table evenly, as a step toward sharding | The modulus is fixed at creation; changing it rewrites the data |

```sql
CREATE TABLE events (
  id          uuid NOT NULL,
  tenant_id   uuid NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  payload     jsonb NOT NULL,
  PRIMARY KEY (id, created_at)   -- every unique constraint must contain the partition key
) PARTITION BY RANGE (created_at);
CREATE TABLE events_2026_12 PARTITION OF events
  FOR VALUES FROM ('2026-12-01 00:00+00') TO ('2027-01-01 00:00+00');
-- Retention (PostgreSQL 14+, outside a transaction block): detach without blocking, then drop
ALTER TABLE events DETACH PARTITION events_2025_11 CONCURRENTLY;
DROP TABLE events_2025_11;
```

- `id` alone is not unique across partitions (use UUIDs), and a table that needs a global unique
  constraint, such as users by email, should not be partitioned.
- Queries must filter on the partition key or they visit every partition. Confirm in `EXPLAIN`
  that only the expected partitions appear.
- Create partitions ahead with a scheduled job or `pg_partman`, and alert when fewer than two
  future ones exist: an insert with no matching partition fails.
- A `DEFAULT` partition hides that failure and causes a worse one: creating the missing partition
  later scans the default under a lock and fails if matching rows are in it, and
  `DETACH ... CONCURRENTLY` is refused while a default exists. Prefer no default plus the alert.
- Write bounds with an explicit UTC offset; a bare date takes the creating session's time zone.
- `CREATE TABLE ... PARTITION OF` locks the parent ACCESS EXCLUSIVE: set `lock_timeout`. To avoid
  it, create the table standalone, add a `CHECK` matching the bounds, then `ATTACH PARTITION`.
- `CREATE INDEX CONCURRENTLY` is refused on the parent. Create the index `ON ONLY` the parent,
  build each partition's index concurrently, then `ALTER INDEX ... ATTACH PARTITION` each.
- An existing table cannot be partitioned in place. Attach it as the first, large partition of a
  new parent, after building the parent's indexes on it concurrently and adding a `CHECK` for its
  bounds; or build the partitioned table beside it and swap (`migrations.md`).

## Moving providers with logical replication

If a maintenance window as long as a dump and restore is acceptable, do that instead
(`backup-recovery.md`); it has a tenth of the steps. Use logical replication when the write outage
must be about a minute. The same procedure performs a major-version upgrade, since it works from
an older version to a newer one.

- The source must permit logical replication (`wal_level = logical`, usually a provider setting
  that needs a restart) and have a role with the `REPLICATION` attribute. The target needs the
  same extensions and a direct connection to the source, not a transaction pooler.
- Every table needs a primary key (check `pg_index.indisprimary`); without one, updates and
  deletes on a published table fail on the source.
- Not carried over by the stream: schema changes, sequence positions, roles and grants,
  materialized view contents. Freeze migrations until cutover: a schema change on the source stops
  the subscriber at the first row that does not fit, and its slot then retains WAL.

1. Target: create roles and extensions, then load the schema, primary keys included:
   `pg_dump --schema-only --no-owner --no-privileges "$SOURCE_URL" | psql "$TARGET_URL"`.
2. Source: `CREATE PUBLICATION move_pub FOR ALL TABLES;` (name the tables instead where the
   provider's admin role may not publish all).
3. Target: create the subscription. It makes a slot on the source, copies every table, then
   streams changes. The source keeps WAL until the copy has caught up, so watch its disk.

```sql
CREATE SUBSCRIPTION move_sub
  CONNECTION 'host=SOURCE_HOST dbname=app user=repl password=... sslmode=require'
  PUBLICATION move_pub;
-- Target: tables whose initial copy is not finished; empty means done
SELECT srrelid::regclass, srsubstate FROM pg_subscription_rel WHERE srsubstate <> 'r';
-- Source: how far the subscriber is behind
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) AS behind
FROM pg_replication_slots WHERE slot_type = 'logical';
-- Source, at cutover: emits one setval per sequence, to execute on the target
SELECT format('SELECT setval(%L, %s, true);', format('%I.%I', schemaname, sequencename), last_value)
FROM pg_sequences WHERE last_value IS NOT NULL;
```

4. Make the target production-ready: `ANALYZE`, point-in-time recovery, pooler, role settings and
   timeouts, monitoring. Run the smoke test and the slowest queries against it, and rehearse the
   cutover on a staging pair, timing each step.
5. Cut over. Stop web, workers and schedulers, then make the source refuse stragglers
   (`ALTER ROLE app_rw NOLOGIN;` and terminate its sessions). Wait until `behind` settles near
   zero, compare `count(*)` and `max(updated_at)` of the busiest tables on both sides, then copy
   the sequence positions with the last query above.
6. Point every connection secret at the target (web, workers, schedulers, functions, reporting
   tools), start the application and verify a write.
7. `DROP SUBSCRIPTION move_sub;` on the target, which also removes the slot on the source; a slot
   left behind retains WAL until that disk is full. Keep the source, refusing writes, for a few
   days, then take a final snapshot and delete it.

Until step 6 the source is unchanged, so backing out means re-enabling the role and restarting.
After the first write on the target, going back loses data unless reverse replication was
prepared (a publication on the target, a subscription on the old source with `copy_data = false`).
Default: no reverse path; step 6 is the point of no return, so smoke-test before opening traffic.

## Ask the user

- **What does an hour of database downtime cost, and may a failover lose the last seconds of
  writes?** Decides standby and synchronous mode. Default: asynchronous standby once it pays.
- **Where may users see data a few seconds old?** Decides which reads may leave the primary.
  Default: never right after their own write; lists, search and dashboards otherwise.
- **How long must event-like data (logs, events, notifications) stay queryable?** Sets partition
  retention. Default: delete nothing without an answer; propose 13 months.
- **Is a maintenance window acceptable for a provider move or major upgrade, and how long?**
  Default: if a dump and restore fits the window, use it instead of logical replication.
- **Who runs reports against the database, and how fresh must they be?** Decides role versus
  replica. Default: a read-only role with a timeout until reports show in the primary's load.
