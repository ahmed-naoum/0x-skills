# Backup, restore and data recovery

Read this when: setting up or reviewing database backups, running a restore drill, about to make a
risky change, or recovering deleted or corrupted data, for the whole database or for one customer.

## What protects against what

| Failure | Protection | Not protected by |
|---|---|---|
| Disk, host or zone dies | Standby with automatic failover (`replication-scaling.md`) | Backups alone: restoring takes far longer than failing over |
| A bug, a bad migration or a person deletes or corrupts data | Point-in-time recovery (PITR) | Replicas: they copy the mistake within milliseconds |
| The provider account is compromised, suspended or deleted; region lost | An independent copy in another account and region | Anything stored in the same account, including the provider's own backups |
| A customer deletes their own data and wants it back | A trash window in the product; otherwise the single-tenant restore below | |

A copy counts as a backup only if it survives the thing that destroys the original, and only if a
restore from it has been performed. Judge each one: does it survive deleting the instance,
deleting the account, or leaking the production credentials?

## Setup by stage

| Stage | Minimum |
|---|---|
| Prototype | The provider's automatic daily backups switched on. Nothing else |
| Launch | PITR with at least 7 days of retention (14 to 35 is better: bad data is often found days later); a scheduled logical dump stored outside the provider; one completed restore drill |
| Scale | Immutable copies in a separate account and region; automated restore tests; a measured restore time in the runbook |

PITR is a base backup plus the continuous archive of the write-ahead log, so the database can be
rebuilt as of any moment in the retention window. Check on the provider:

- It is actually on. On some providers and plans it is a paid add-on or needs a minimum tier.
- The retention window, and the earliest and latest restorable times shown right now.
- The recovery point: log shipping usually lags by up to a few minutes, so the last minutes before
  a total loss can be gone.
- Whether backups outlive the instance. On several providers deleting the database deletes its
  automated backups unless a final snapshot or backup retention is requested.

Self-hosted: use a physical-backup tool (pgBackRest, Barman or WAL-G) writing to object storage,
after confirming the project is currently maintained: these tools depend on a few sponsors and
their status has changed before. Alert on `failed_count` in `pg_stat_archiver`. A failing archive
silently breaks PITR and fills the disk with WAL.

A logical dump is the portable second copy. It restores into any provider and any newer version,
and a single table can be pulled from it. It is not PITR, and it is slow beyond roughly 100 GB.

```bash
DUMP="app-$(date -u +%Y%m%dT%H%MZ).dump"
pg_dump --format=custom --no-owner --no-privileges --file="$DUMP" "$DIRECT_DATABASE_URL"
pg_restore --list "$DUMP" | grep -c "TABLE DATA"    # readable, and has the expected tables
```

Use the direct connection, not a transaction pooler. The `pg_dump` client must be the server's
major version or newer. Roles and grants are not in the dump (`pg_dumpall --globals-only` where
the provider allows it; otherwise keep role setup as a script in the repository). A dump holds
one long transaction open, so at Scale run it against a replica.

## Restore drills

An untested backup fails in ordinary ways: the dump job has been erroring for months, the file is
truncated, an extension is missing on the target, the restore takes nine hours when everyone
assumed one.

Schedule: once before Launch, then quarterly, and after any change to backup configuration or a
major version upgrade. At Scale, automate it weekly.

1. Pick a target time and restore to a new instance. Never restore over the original.
2. Time it from the first click to "the application could use it": provisioning, restore, log
   replay, creating roles, switching the connection string. That number is the real recovery
   time. Write it down.
3. Verify content, not just completion: row counts of the main tables against production,
   `max(created_at)` close to the target time, extensions and roles present, the application's
   smoke test passing when pointed at it.
4. Record date, backup used, duration and every surprise in the runbook. Fix the surprises.
5. Delete the restored instance. It costs money and is a full copy of customer data.

```bash
createdb restore_check
pg_restore --no-owner --jobs=4 --dbname=restore_check app.dump
psql -d restore_check -Atc "SELECT count(*), max(created_at) FROM orders"
```

Automated form: a scheduled CI job restores the newest dump into a scratch Postgres, asserts that
key tables are non-empty and the newest row is under 48 hours old, and alerts on failure. Also
alert when the newest backup object is older than 26 hours or far smaller than the previous one.

Restore time grows with data size. Re-measure as the database grows; when it exceeds what the
business tolerates, that is a reason for a standby, not for hope.

## Before a risky change

Risky: a migration that drops or rewrites, a bulk update or delete, a major version upgrade, a
provider-side change, any script nobody else has read.

| Scope of the change | Safety copy | Restore path |
|---|---|---|
| Rows in one or two tables | Before-image table in the same transaction: `CREATE TABLE ops.orders_20261122 AS SELECT * FROM orders WHERE ...` | `UPDATE ... FROM` or re-insert; seconds |
| A whole table | `pg_dump --table=orders` or `CREATE TABLE ... AS TABLE orders` | `pg_restore` of that table into a side schema |
| The whole database | Manual provider snapshot or a branch, plus the timestamp noted for PITR | New instance from the snapshot |

Verified means all of:

- The snapshot or dump reports complete (status available, non-trivial size), and for a
  before-image the row count equals the count of rows about to change.
- The exact time is recorded just before the change (`SELECT now();`), so PITR can target the
  moment before it.
- The restore command or console path is written in the pull request or runbook before starting.
- For irreversible, high-value changes, the copy has actually been restored once to a scratch
  database.

A manual snapshot persists beyond the PITR window; set a reminder to delete it.

## Immutable copies in another account and region

Skip until Launch (the off-provider dump covers the worst case). Mandatory at Scale, or earlier
when a contract demands it.

- A second cloud account, or a different provider, with its own owner credentials and MFA. Nothing
  in production can log in to it.
- A bucket with object lock or a retention policy, so objects cannot be deleted or overwritten
  before they expire, even by an administrator; versioning on.
- The backup job gets a write-only credential: it can add objects, not list, read or delete them.
  A compromised application or CI token then cannot destroy history.
- A different region from the primary database.
- Encrypted before upload or with a managed key, and the key stored outside the production
  account. A backup whose key was lost with the account is not a backup.
- Expiry by lifecycle rule. Default: dailies for 30 days. Weeklies and monthlies (for example
  12 weeks and a year) only when a contract, a regulation or a documented risk of
  late-discovered corruption justifies them; the longest copy is then the backup retention the
  privacy documentation states. Bounded retention is also what makes deletion requests
  answerable (`0x:privacy-compliance`).
- Restore drills must include this copy, using only the second account's credentials.

Where the provider offers cross-account or cross-region copies of its own snapshots with a lock,
use that as well. Bucket mechanics are in `0x:data-stores`; backing up secrets, configuration and
uploaded files, and rebuilding the whole stack, are in `0x:site-reliability`.

## Restoring to a point in time and reconciling

For "a deploy at 14:07 UTC corrupted orders":

1. Stop the damage: disable the code path, flag or job. If writes are still corrupting data, put
   the application in maintenance mode. Work in UTC throughout.
2. If the incident is near the edge of the retention window, start a restore or take a manual
   snapshot immediately; the window keeps moving while people discuss.
3. Find the last good moment from deploy logs, application logs or an audit table. Restore to a
   new instance at a time just before it. Start early: large restores take hours, and a second
   restore to a slightly different time is cheap compared with waiting.
4. Choose the repair:

| Damage | Repair |
|---|---|
| Confined to identifiable rows or tables | Surgical: copy the good rows from the restored instance into production (method in the last section). Keeps every legitimate write made since |
| Widespread or unknowable | Cut over to the restored instance. Everything written after the target time is gone unless reconciled |

5. Reconciling after a cutover. The damaged database still holds the later writes, so keep it,
   stopped or read-only, until this is done:
   - Per table, export rows with `created_at` or `updated_at` after the target time from the old
     database, discard the corrupt ones, and re-insert the rest. This only works if tables carry
     those timestamps.
   - Replay from outside sources of truth: payment-provider events, inbound webhooks that can be
     re-sent, uploaded files, email logs. Money first (`0x:payments-billing`).
   - Before reopening writes, move every sequence past the highest value the old database issued,
     or new rows will collide with re-inserted ones. Read each `last_value` from `pg_sequences` on
     the old database and apply it on the restored one:
     `SELECT setval(pg_get_serial_sequence('orders', 'id'), <last_value on the old database>);`
   - A restore also brings back rows deleted after the target time. Re-apply the deletions that
     users requested or the law required, from the request log (`0x:privacy-compliance`).
   - List what cannot be recovered and tell the affected customers.
6. The restored instance is a new database: new endpoint, no backup history yet, default
   parameters. Re-enable PITR, deletion protection, monitoring, the pooler, replicas, role
   settings and extensions, then switch the application's connection secret.
7. Keep the old instance until reconciliation is signed off. Then write the postmortem
   (`0x:site-reliability`).

## Guarding critical tables

Layers, cheapest first:

- **Provider**: deletion protection on the instance or project; a final snapshot on delete;
  automated backups retained after deletion. In infrastructure code add a destroy guard, for
  example with Terraform on AWS: `deletion_protection = true`, `skip_final_snapshot = false` with a
  `final_snapshot_identifier`, and `lifecycle { prevent_destroy = true }` (`0x:cloud-infrastructure`).
- **Grants**: the application role owns nothing, so it cannot `DROP`, `ALTER` or `TRUNCATE`
  (`postgres-operations.md`). Append-only tables lose more:
  `REVOKE UPDATE, DELETE ON ledger_entries, audit_log FROM app_rw;`
- **Foreign keys**: `ON DELETE RESTRICT` from money and history tables to their parents, so
  deleting an account with invoices fails instead of cascading.
- **A trigger** on tables where an accidental delete is catastrophic. The override is explicit,
  visible in review, and limited to one transaction:

```sql
CREATE FUNCTION forbid_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF current_setting('app.allow_delete', true) = 'on' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'deletes on % are blocked; SET LOCAL app.allow_delete = ''on'' to override',
    TG_TABLE_NAME;
END $$;

CREATE TRIGGER invoices_no_delete BEFORE DELETE ON invoices
  FOR EACH ROW EXECUTE FUNCTION forbid_delete();
CREATE TRIGGER invoices_no_truncate BEFORE TRUNCATE ON invoices
  FOR EACH STATEMENT EXECUTE FUNCTION forbid_delete();
```

- **A trash window** for customer-initiated deletion of top-level objects: mark deleted, purge
  after a fixed period. It turns the most common recovery request into one `UPDATE`.
- **People**: read-only credentials for daily use, a separate role for writes, and the manual-SQL
  routine in `sql-queries.md`.

## Recovering one tenant's deleted rows

A full rollback would discard every other customer's work since the deletion. Instead, extract
the tenant's rows from a restored copy and merge them into live production.

1. Scope: tenant id, time of deletion, and the list of tables holding that tenant's data, parents
   before children. This is quick only when every tenant-owned table carries the tenant id.
2. Restore to a new instance (or a branch) at a moment just before the deletion.
3. Export per table from the restored copy, load into a staging schema in production:

```sql
-- connected to the restored copy
\copy (SELECT * FROM projects WHERE tenant_id = 42) TO 'projects.csv' WITH (FORMAT csv, HEADER)

-- connected to production
CREATE SCHEMA restore_20261122;
CREATE TABLE restore_20261122.projects (LIKE public.projects);
\copy restore_20261122.projects FROM 'projects.csv' WITH (FORMAT csv, HEADER)
```

4. Compare before writing: how many staged rows are missing from live, and how many exist in both
   (the customer may have recreated some).
5. Merge in one transaction, parents first, inserting only what is missing:

```sql
BEGIN;
INSERT INTO public.projects OVERRIDING SYSTEM VALUE
SELECT * FROM restore_20261122.projects
ON CONFLICT (id) DO NOTHING;
-- then each child table, in dependency order
COMMIT;
```

6. Verify with the customer (counts per table, a look through the UI), then drop the staging
   schema, delete the CSV files and delete the restored instance.

Traps:

- `SELECT *` assumes the schema has not changed since the backup. If migrations ran in between,
  list columns explicitly and map the differences.
- Identity columns declared `GENERATED ALWAYS` reject explicit ids without `OVERRIDING SYSTEM
  VALUE`; stored generated columns must be left out of the column list.
- Other unique constraints can collide (the customer reused a name or slug). Decide per case; the
  default is that live data wins and the restored row is renamed.
- Rows that exist in both but differ: keep live unless the customer asks otherwise.
- Data outside Postgres: uploaded files (restore from bucket versioning), search indexes, caches
  and denormalized counters need a rebuild for that tenant.
- Inserts fire triggers and may enqueue jobs or notifications. Check what will fire before merging.
- If the deletion was a deliberate erasure request, restoring it may be the wrong thing to do.

## Ask the user

- **How much recent data could the business lose, and how long could it be down?** These set PITR,
  standby and drill frequency. Default at Launch: minutes of data, a few hours of downtime.
  Company-wide targets are in `0x:site-reliability`.
- **How far back must recovery reach?** Bad data is often noticed late. Default: 14 days of PITR
  plus off-provider daily dumps kept 30 days; longer archives only with a stated reason, and the
  privacy documentation then quotes the longest period.
- **Is restoring a single customer's deleted data a service you offer, and at what price?** It
  takes hours of careful work. Default: a 30-day trash in the product; backup restores as a paid
  or best-effort exception.
- **Is there a second cloud account or provider for off-site copies, and who holds its
  credentials?** Default: create one owned by the founder, with MFA, used for nothing else.
- **Do contracts or regulations fix a backup retention or deletion period?** Default: none; follow
  the retention scheme above.
