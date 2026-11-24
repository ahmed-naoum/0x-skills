# Zero-downtime schema migrations

Read this when: writing any schema change that will run against a database with live traffic or
large tables, backfilling a new column, renaming or retyping a column, or cleaning up after a
migration that failed halfway.

## Two facts that cause most migration outages

**The lock queue.** Most `ALTER TABLE` forms need an ACCESS EXCLUSIVE lock. If any transaction,
even a long `SELECT`, is using the table, the `ALTER` waits, and every new query on that table
queues behind the waiting `ALTER`. A statement that takes one millisecond to run stops the
application for as long as it waits. So every migration that runs in a transaction starts with:

```sql
SET LOCAL lock_timeout = '3s';         -- give up instead of queueing the whole application
SET LOCAL statement_timeout = '15min'; -- the app role's short limit would kill index builds
```

SQLx runs each such file in its own transaction, so `SET LOCAL` ends with it; give the migrator
role no role-level `lock_timeout`, so no-transaction files run without one. The pipeline retries a
`55P03` (lock timeout) failure a few times with a pause: the failed file rolled back entirely.

**Old and new code overlap.** During a rolling deploy, and after any rollback, application code
of version N runs against the schema of version N+1 or the reverse. Every migration must be
compatible with the previous and the next application version.

At Prototype, with no real users and small tables, write, read and apply: only the versioned
files matter yet. From Launch every rule below applies, because a blocked table is a visible outage.

## Migrations as code

- One ordered `migrations/` directory of SQL files in the repository, each created with
  `sqlx migrate add <name>` (timestamp-prefixed) and written by hand; SQLx generates nothing from
  Rust types. Under SeaORM or Diesel, their generator writes a draft to read and edit: it does not
  know about locks and will emit a blocking `CREATE INDEX` and a drop-and-add for a rename.
- A merged or applied migration is immutable; fix forward with a new file. SQLx stores each file's
  checksum and refuses to run once an applied file changed by one byte, line endings included.
  A file with an older version merged later (a long-lived branch) is applied anyway, so environments
  can run files in different orders: recreate such a file with `sqlx migrate add` before merging.
- Applied from the deploy pipeline before the new version serves: `sqlx migrate run` from a pinned
  sqlx-cli, or the release binary's `migrate` subcommand (below). Never from a laptop, and never at
  web-process startup: instances queue on the migrator's lock, a slow migration fails health
  checks, and an older binary started for a rollback refuses to run (`VersionMissing`: applied
  versions it does not know) unless it ignores them (`set_ignore_missing(true)` on the `Migrator`,
  `--ignore-missing` on `sqlx migrate run`). Pipeline wiring is in `0x:ci-cd-release`.
- `sqlx::migrate!()` embeds the files at compile time. Commit the `build.rs` that `sqlx migrate
  build-script` writes, or cargo may skip the rebuild when only a migration file changed.
- Run as a dedicated owner role over a direct connection, not the application role and not a
  transaction pooler (`postgres-operations.md`).
- One logical change per file; destructive steps get their own file in a later release. Never
  combine DDL with a large backfill in one migration: the deploy would hold locks throughout.
- Make statements rerunnable where the syntax allows: `IF NOT EXISTS`, `IF EXISTS`.
- Lint migrations in CI for unsafe statements (Squawk is a linter for exactly this); `cargo sqlx
  prepare --check` against the migrated schema fails a migration that breaks a checked query.

```rust
use sqlx::{migrate::Migrator, postgres::PgPoolOptions};

static MIGRATOR: Migrator = sqlx::migrate!(); // embeds ./migrations at compile time

/// `app migrate`: run by the deploy pipeline with the migrator role's direct URL.
pub async fn migrate(direct_url: &str) -> anyhow::Result<()> {
    let pool = PgPoolOptions::new().max_connections(1).connect(direct_url).await?;
    MIGRATOR.run(&pool).await?; // takes an advisory lock, applies pending files in order
    Ok(())
}
```

## Which operations are safe

| Operation | Behavior | Safe form |
|---|---|---|
| `ADD COLUMN` nullable, or with a constant or `now()` default | Instant metadata change | As is |
| `ADD COLUMN` with a volatile default (`gen_random_uuid()`, `clock_timestamp()`) or a stored generated column | Rewrites the table under ACCESS EXCLUSIVE | Add nullable, backfill in batches, then set the default |
| `SET NOT NULL` | Scans the table under ACCESS EXCLUSIVE | Check-constraint recipe below |
| `ADD CONSTRAINT ... CHECK` or `FOREIGN KEY` | Scans while blocking writes (`CHECK` blocks reads too) | `NOT VALID`, then `VALIDATE CONSTRAINT` |
| `ADD CONSTRAINT ... UNIQUE` or `PRIMARY KEY` | Builds an index under ACCESS EXCLUSIVE | Unique index `CONCURRENTLY`, then attach it |
| `CREATE INDEX` | Blocks writes for the whole build | `CREATE INDEX CONCURRENTLY` |
| `DROP INDEX` | ACCESS EXCLUSIVE on the table | `DROP INDEX CONCURRENTLY` |
| `ALTER COLUMN TYPE` | Rewrites table and indexes, except widening `varchar(n)` or converting it to `text` | New column, dual write, backfill, swap (below) |
| `RENAME COLUMN` / `RENAME TABLE` | Instant, and breaks all running code | Expand and contract, or do not rename |
| `DROP COLUMN` / `DROP TABLE` | Instant; data unrecoverable without a backup | Only after no deployed code references it |
| `ALTER TYPE ... ADD VALUE` | Fast; the value is unusable until the transaction commits | Own migration, before the code that writes it |
| `VACUUM FULL`, `CLUSTER` | Rewrite under ACCESS EXCLUSIVE | Never on a live table (`postgres-operations.md`) |

Instant operations still need the lock and so still need `lock_timeout`.

```sql
-- NOT NULL on an existing column
ALTER TABLE orders ADD CONSTRAINT orders_region_not_null CHECK (region IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_region_not_null;   -- scans, does not block writes
ALTER TABLE orders ALTER COLUMN region SET NOT NULL;             -- uses the validated check, no scan
ALTER TABLE orders DROP CONSTRAINT orders_region_not_null;

-- Foreign key
ALTER TABLE orders ADD CONSTRAINT orders_customer_id_fkey
  FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_id_fkey;

-- Unique constraint
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS orders_external_ref_key ON orders (external_ref);
ALTER TABLE orders ADD CONSTRAINT orders_external_ref_key UNIQUE USING INDEX orders_external_ref_key;
```

A `NOT VALID` constraint is enforced for new and updated rows immediately; only the check of
existing rows is deferred. Put each step in its own transaction so the brief exclusive lock of
`ADD CONSTRAINT` is released before the long validation starts.

`CREATE INDEX CONCURRENTLY` rules:

- It cannot run inside a transaction block, and SQLx wraps each file in one unless its first line
  is `-- no-transaction`. Put the statement alone in such a file.
- It waits for open transactions that have written to the table, and for any transaction in the
  database holding an older snapshot (a long query, a REPEATABLE READ transaction, `pg_dump`), so
  one such session left open stalls it. Under a `lock_timeout` that wait aborts the build and
  leaves an invalid index, so run
  it with none (the migrator role has none, or set `PGOPTIONS='-c lock_timeout=0'`, which SQLx
  reads): the build blocks no reads or writes, only other schema changes and vacuum on that table.
  The same applies to `DROP INDEX CONCURRENTLY` and `REINDEX ... CONCURRENTLY`. Do not add a `SET`
  to the file: SQLx sends it as one multi-statement string, an implicit transaction block, and the
  build is refused.
- If it fails or is cancelled it leaves an INVALID index that costs writes and serves no reads.
  SQLx records a no-transaction file only after it succeeds, so the next run executes it again,
  and `IF NOT EXISTS` then skips the invalid index and records success. Find it, drop it, rerun:

```sql
SELECT c.relname AS index_name, i.indrelid::regclass AS table_name
FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
WHERE NOT i.indisvalid;

DROP INDEX CONCURRENTLY IF EXISTS orders_external_ref_key;
```

## Expand, migrate, contract

| Step | Kind | What ships |
|---|---|---|
| 1 Expand | Migration | Add the new column, table or index. Old code is unaffected |
| 2 Dual write | Code deploy | Write old and new; still read old |
| 3 Backfill | Script or job | Copy existing rows into the new shape, in batches |
| 4 Switch reads | Code deploy | Read new; keep writing both so rollback stays possible |
| 5 Stop old writes | Code deploy | Only the new shape is written |
| 6 Contract | Migration | Drop the old column or table, after a full release cycle with no reader |

Compatible with old code: adding a table, a nullable or defaulted column, an index, a `NOT VALID`
constraint that existing writes already satisfy. Not compatible: dropping or renaming anything the
old code names, adding a required column without a default, tightening a constraint the old code
violates, removing an enum value.

Before step 6, prove nothing reads the old shape: search the code, and check `pg_stat_statements`
for statements that mention the column. Old binaries carry SQL checked against the schema of their
build, and a `FromRow` struct fails on any field it cannot find: a dropped column breaks old
instances immediately, and `cargo sqlx prepare --check` cannot see them.

## Renaming and retyping

**Rename.** Usually the right move is not to rename in the database: rename in Rust only, with
`old_name AS new_name` in the query or `#[sqlx(rename = "old_name")]` on a `FromRow` field. A true
rename is the six steps above with a new column, five deploys of work for a cosmetic gain. Table
renames: the same, or a view under the old name for the transition.

**Retype** (for example `integer` to `bigint`, `text` to `jsonb`):

1. Add `col_new` with the target type.
2. Dual write, in the application or with a trigger that copies `col` into `col_new` on insert
   and update. A trigger covers every writer, including scripts.
3. Backfill in batches (next section), then verify zero rows where the two differ.
4. Build required indexes on `col_new` concurrently; add `NOT NULL` with the check recipe.
5. Swap in one short transaction with `lock_timeout`: rename `col` to `col_old` and `col_new` to
   `col`, and drop the trigger. The release before already reads `col::bigint` into an `i64`: an
   `i32` read fails after the swap, at once under `query_scalar!`, `FromRow` and `try_get`, and at
   the first value above `i32::MAX` under `query!` and `query_as!`. Cached statements re-prepare
   themselves, except inside a transaction, where the first use fails once with `0A000`.
6. Drop `col_old` in a later release.

Retyping a primary key also means every referencing foreign key; start with `bigint` or `uuid` keys.

## Backfilling in batches

One `UPDATE` over a large table is a single long transaction: it locks every row it touches until
commit, doubles the table's size in dead rows, floods replicas with WAL and cannot resume if
interrupted. Instead:

- Walk the primary key in ranges; 1,000 to 10,000 rows per batch; commit after each.
- Make it resumable and idempotent: the predicate skips rows already done.
- Throttle: aim for batches under about a second, pause between them, and back off when
  replication lag or lock waits rise.
- Run it as a script or job outside the deploy, after the expand migration has shipped.

```sql
CREATE PROCEDURE backfill_orders_total_cents(batch_size int DEFAULT 5000, pause_s float DEFAULT 0.1)
LANGUAGE plpgsql AS $$
DECLARE last_id bigint := 0; max_id bigint;
BEGIN
  LOOP
    SELECT max(id) INTO max_id
    FROM (SELECT id FROM orders WHERE id > last_id ORDER BY id LIMIT batch_size) batch;
    EXIT WHEN max_id IS NULL;
    UPDATE orders SET total_cents = total_minor
    WHERE id > last_id AND id <= max_id AND total_cents IS NULL;
    last_id := max_id;
    COMMIT;
    PERFORM pg_sleep(pause_s);
  END LOOP;
END $$;

CALL backfill_orders_total_cents();   -- from psql in autocommit mode, not inside a transaction
```

The same loop as a Rust job can log progress and check replication lag between batches. UUIDv7
keys work the same way, since they compare in creation order:

```rust
use std::time::Duration;
use sqlx::PgPool;

// `last_id`: 0, or the last id logged by an interrupted run.
pub async fn backfill_total_cents(pool: &PgPool, mut last_id: i64, batch: i64) -> Result<(), sqlx::Error> {
    loop {
        let max_id = sqlx::query_scalar!(
            "WITH batch AS (SELECT id FROM orders WHERE id > $1 ORDER BY id LIMIT $2),
                  upd AS (UPDATE orders o SET total_cents = o.total_minor
                          FROM batch b WHERE o.id = b.id AND o.total_cents IS NULL)
             SELECT max(id) FROM batch",
            last_id, batch
        )
        .fetch_one(pool) // one statement per batch: it commits by itself
        .await?;
        let Some(max_id) = max_id else { return Ok(()) };
        last_id = max_id;
        tracing::info!(last_id, "backfill batch committed");
        tokio::time::sleep(Duration::from_millis(100)).await; // never std::thread::sleep here
    }
}
```

While it runs, watch replication lag, disk (WAL) and the table's dead rows; finish with `ANALYZE` on it.

## Rehearsal

Lock duration, rewrite time and validation time depend on table size and concurrent traffic, and
neither exists in development. Before a migration touches a table that is large (over roughly a
million rows or a gigabyte) or hot:

1. Create a production-sized copy: a provider branch or clone, or a restore of last night's backup
   (`backup-recovery.md`).
2. Run the exact migration files with the same `lock_timeout` and `\timing` on; record each duration.
3. While it runs, hold a transaction open in a second session to confirm the migration fails fast
   on the lock timeout instead of hanging, and that the retry succeeds once it is released.
4. Check the outcome: expected schema, no invalid index or unvalidated constraint, acceptable disk growth.
5. Any statement that holds an exclusive lock for more than a second or two needs a safer form.

## Down script or forward fix

| Migration type | If it goes wrong |
|---|---|
| Expand (add table, column, index) | Leave it; an unused column harms nothing. A down script is optional convenience |
| Constraint or validation | Drop the constraint in a new migration |
| Data transformation, backfill | A down script cannot recover overwritten values. Keep the old column until verified, or take a before-image |
| Contract (drop, truncate) | No down exists. The undo is a backup: take a verified snapshot first (`backup-recovery.md`) |

Default for a small team: forward-only in production. Because every migration is compatible with
the previous application version, rolling back a release means redeploying old code against the
new schema, and no schema rollback is needed (`0x:ci-cd-release` covers release rollback). Down
files (`sqlx migrate add -r`, run by `sqlx migrate revert`) suit development, not an incident.

## Recovering from a half-applied migration

A migration inside a transaction that fails rolls back completely: nothing was applied. Fix the
cause (usually data the statement did not expect, or a lock timeout) and rerun, editing the file
only if it has run in no other environment. Trouble comes from migrations that could not be
transactional (`CONCURRENTLY`), runners that apply several files and stop midway, backfills that
died, and pipelines that timed out and killed the client while the server kept going.

1. Stop. Do not rerun the pipeline, and do not edit the runner's history table yet.
2. Check for leftovers still running or blocked: `pg_stat_activity` for the migration role.
3. Establish the real state: `\d table` for columns and constraints; invalid indexes (query above);
   unvalidated constraints (`SELECT conrelid::regclass, conname FROM pg_constraint WHERE NOT
   convalidated;`); `_sqlx_migrations` (or `sqlx migrate info`) for what SQLx believes is applied.
4. Ask whether the application is healthy on the current state; after a partial expand it usually is.
5. Prefer rolling forward: apply the remaining statements by hand in idempotent form, dropping and
   rebuilding any invalid index. Roll back (drop what was added) only if the forward path is blocked.
6. Make the record match reality last. SQLx writes a file's row only after the file succeeded, so
   once the remaining statements are in place, rerun the migration: idempotent statements find the
   work done and the row gets the right checksum. Never edit `_sqlx_migrations` by hand, and do not
   use `sqlx migrate override skip`: it marks every pending file applied without running it.
7. Add a new idempotent migration so every other environment converges to the same state.
8. If a destructive statement ran before the failure, do not improvise: restore the affected table
   to a side database and copy the data back (`backup-recovery.md`).

## Ask the user

- **Is a short maintenance window acceptable for this change?** A five-minute announced window can
  replace a five-deploy dance. Default: no window at Launch and later; at Prototype just run it.
- **Is the rename worth it?** It buys naming consistency for days of careful work. Default: rename
  in the Rust code only.
- **How long must dropped data stay recoverable?** Sets how long old columns or before-images are
  kept. Default: one release cycle for columns, and a verified snapshot before any drop.
- **When is traffic lowest?** Backfills and validations run there. Default: outside the main
  customer time zone's business hours.
