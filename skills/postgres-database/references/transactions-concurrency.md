# Transactions, isolation and locking

Read this when: several writes must succeed or fail together, concurrent requests can race on the
same rows, queries are blocking each other, deadlocks appear in logs, or a queue or single-run job
is being built on Postgres.

## Atomic multi-step writes

Any change that touches more than one row or table and must not be seen half-done goes in one
transaction: order plus items, transfer between balances, state change plus its audit row, row
plus the job that processes it.

- After `let mut tx = pool.begin().await?`, every statement runs on `&mut *tx`, never on the pool
  in application state. A statement on the pool runs on another connection, outside the
  transaction: it does not roll back, does not see uncommitted rows, and with a pool of one (or an
  exhausted one) it waits on itself until the acquire timeout. Functions that run several
  statements take `&mut PgConnection`: an `impl PgExecutor` argument is used up by its first query.
- A `Transaction` dropped without `commit()` rolls back, so returning early with `?` is safe;
  nothing is committed unless `commit().await` returned `Ok`.
- After any error inside a transaction, Postgres rejects every further statement ("current
  transaction is aborted") until rollback. Do not handle a constraint error and keep using the
  same `tx`. Avoid the error (`ON CONFLICT`), or wrap the risky statement in a `SAVEPOINT`.
- Let constraints arbitrate. "SELECT to check, then INSERT" races however it is wrapped; a unique
  or exclusion constraint plus handling of the violation does not.
- Keep transactions short: no user think time, no network calls, no slow computation between
  `BEGIN` and `COMMIT`; no `.await` between `begin()` and `commit()` except statements on `tx`,
  and CPU-heavy work goes to `spawn_blocking` before the transaction opens. A transaction holds a
  pooled connection and its row locks for its entire duration, and an open one stops vacuum from
  cleaning rows anywhere in the database.

## Races and their fixes

At the default isolation level each statement sees the latest committed data, so two requests that
read a value, compute in application code and write back will overwrite each other.

| Situation | Fix |
|---|---|
| Increment, decrement, append | One atomic statement: `SET n = n + 1`. Never read, add in code, write |
| Spend from a limited quantity (stock, credits, seats) | Atomic statement with a guard, then check the affected row count |
| User edits a record they loaded earlier | Optimistic version column; zero rows updated means someone else saved first |
| Create if absent | Unique constraint plus `ON CONFLICT` |
| Rule across several rows (allocations within a budget, at most N children) | Lock the parent row first, then read and write; or an exclusion constraint; or SERIALIZABLE |
| Only one worker may run a job or a batch | Advisory lock or `SKIP LOCKED` claim (below) |

```sql
-- Guarded atomic update: 0 rows affected means insufficient stock, not an error
UPDATE stock SET qty = qty - $2 WHERE sku = $1 AND qty >= $2;

-- Optimistic check: 0 rows affected means a concurrent edit; return a conflict to the client
UPDATE documents
SET title = $3, version = version + 1, updated_at = now()
WHERE id = $1 AND version = $2;
```

The guarded update is safe at the default level because an `UPDATE` that waits for a row lock
re-checks its `WHERE` against the newly committed row before applying. Keep a `CHECK (qty >= 0)`
as the backstop, and read the count from `rows_affected()` on the `execute` result. The HTTP side
of the optimistic check (ETag, `If-Match`, 409 or 412) is in `0x:api-design`.

## External calls stay outside transactions

A payment, email or third-party API call inside a transaction holds a connection and row locks for
the length of a network round trip, exhausts the pool when the provider slows down, and cannot be
rolled back: if the transaction fails after the call succeeded, the customer was charged and the
database has no record. Nothing in Rust stops a `reqwest` call between `begin()` and `commit()`;
look for one in review.

1. Transaction one: insert the intent with status `pending` and an idempotency key. Commit.
2. Call the provider with that key, with a timeout.
3. Transaction two: record the outcome.
4. A periodic job resolves rows stuck in `pending` by asking the provider.

Work that must happen "if and only if the transaction commits" (send email, enqueue a job, publish
an event) is written as a row in the same transaction and performed by a worker afterwards. That
is the reason a Postgres-backed queue is the default. The outbox pattern and dual-write hazards are
covered in `0x:backend-architecture`.

## Isolation levels

| Level | Sees | Still possible | Use |
|---|---|---|---|
| READ COMMITTED (default) | A fresh snapshot per statement | Lost updates in read-modify-write, write skew, two statements disagreeing | Almost everything, with the explicit fixes above |
| REPEATABLE READ | One snapshot for the whole transaction | Write skew. A write to a row changed since the snapshot fails with `40001` | Multi-query reports and exports that must be self-consistent |
| SERIALIZABLE | Behaves as if transactions ran one at a time | Nothing, but any transaction can fail with `40001` | Invariants over rows that cannot be enumerated and locked up front |

Default rule: stay at READ COMMITTED and make each critical write safe by construction (atomic
statement, constraint, explicit lock). Choose SERIALIZABLE for a specific transaction type when
the invariant is hard to lock; every transaction that touches that data must then also be
serializable, and all of them need the retry wrapper. Keep serializable transactions short; long
ones multiply false conflicts.

Retry the whole transaction on `40001` (serialization failure) and `40P01` (deadlock). Each attempt
opens, uses and commits its own transaction, so the helper takes a closure that starts a fresh
attempt rather than lending a transaction to a callback; the attempt must be safe to run again, one
more reason it contains no external calls. Since SQLx 0.9 `begin_with`, like `query`, takes a
`&'static str` unless it is wrapped in `AssertSqlSafe`: keep the isolation level a literal.

```rust
use std::time::Duration;
use sqlx::{PgConnection, PgPool};

/// Reruns `attempt` on 40001 or 40P01 with jittered backoff; each call runs its own transaction.
pub async fn with_retry<T, F, Fut>(max_attempts: u32, mut attempt: F) -> Result<T, sqlx::Error>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, sqlx::Error>>,
{
    let mut n = 1;
    loop {
        let result = attempt().await;
        let code = result.as_ref().err().and_then(|e| e.as_database_error()).and_then(|e| e.code());
        if n >= max_attempts || !code.is_some_and(|c| c == "40001" || c == "40P01") {
            return result;
        }
        let backoff = Duration::from_millis(25 << n).mul_f64(rand::random_range(0.5..1.5));
        tokio::time::sleep(backoff).await;
        n += 1;
    }
}

/// Returns false when the allocation would exceed the project's budget.
pub async fn allocate(pool: &PgPool, project: i64, amount: i64) -> Result<bool, sqlx::Error> {
    with_retry(4, || async {
        let mut tx = pool.begin_with("BEGIN ISOLATION LEVEL SERIALIZABLE").await?;
        if !try_allocate(&mut tx, project, amount).await? {
            return Ok(false); // dropping tx rolls back
        }
        tx.commit().await?; // a serializable COMMIT can itself fail with 40001
        Ok(true)
    })
    .await
}

// Takes `&mut PgConnection` so the caller decides the transaction: pass `&mut tx`.
async fn try_allocate(conn: &mut PgConnection, project: i64, amount: i64) -> Result<bool, sqlx::Error> {
    let used = sqlx::query_scalar!(
        r#"SELECT coalesce(sum(amount_minor), 0)::bigint AS "used!"
           FROM allocations WHERE project_id = $1"#,
        project
    )
    .fetch_one(&mut *conn) // reborrow: passing `conn` itself would move it
    .await?;
    let inserted = sqlx::query!(
        "INSERT INTO allocations (project_id, amount_minor)
         SELECT id, $2 FROM projects WHERE id = $1 AND budget_minor >= $3",
        project, amount, used + amount
    )
    .execute(&mut *conn)
    .await?;
    Ok(inserted.rows_affected() == 1)
}
```

## Row locks and deadlocks

Plain `SELECT` never blocks and is never blocked by writers. To hold a row steady between a read
and a later write in the same transaction, lock it in the read:
`SELECT id, budget_minor FROM projects WHERE id = $1 FOR NO KEY UPDATE`.

| Clause | Effect |
|---|---|
| `FOR NO KEY UPDATE` | Blocks other writers and lockers of the row, except foreign-key checks. The lock a normal `UPDATE` takes. Default choice |
| `FOR UPDATE` | The same, and also blocks inserts of child rows that reference this row, because their foreign-key check needs a key-share lock. Use only when deleting the row or changing its key |
| `FOR SHARE` / `FOR KEY SHARE` | `FOR SHARE` blocks writers and lets other sharers in; `FOR KEY SHARE` blocks only deletes and key changes. Rarely needed by hand |
| `NOWAIT` | Fail immediately if the row is locked |
| `SKIP LOCKED` | Silently skip locked rows. For queues only |
| `OF table` | In a join, lock rows of that table only |

A deadlock is two transactions each holding a lock the other wants. Postgres detects it after
`deadlock_timeout` (1 s) and aborts one with `40P01`. Prevent rather than retry:

- Lock rows in one global order. For several rows: `SELECT ... WHERE id = ANY($1) ORDER BY id FOR NO
  KEY UPDATE` before updating. For two tables: always the same table first, parent before child.
- A multi-row `UPDATE` or upsert locks rows in whatever order the plan visits them. Sort batches by
  key, or take the ordered lock first.
- Keep transactions short. Deadlock probability grows with how long locks are held.

## Timeouts that protect the pool

One slow or blocked statement repeated by concurrent requests occupies every connection, and then
every other request queues. Timeouts turn that outage into a handful of failed requests.

| Setting | Web role | Notes |
|---|---|---|
| `statement_timeout` | 5 to 15 s, below the app's request timeout | Cancels with `57014`. Workers and reporting roles get longer values; migrations set their own |
| `lock_timeout` | 2 to 5 s | Bounds waiting for a lock; fails with `55P03` |
| `idle_in_transaction_session_timeout` | 30 to 60 s | Kills sessions that opened a transaction and stopped; these hold locks and block vacuum |
| `transaction_timeout` | 30 to 60 s | PostgreSQL 17+. Caps the whole transaction |
| Pool acquire timeout (client side) | 2 to 5 s | A request fails fast instead of waiting on an exhausted pool |

```sql
ALTER ROLE app_rw SET statement_timeout = '10s';
ALTER ROLE app_rw SET lock_timeout = '3s';
ALTER ROLE app_rw SET idle_in_transaction_session_timeout = '30s';
```

Set them per role: they apply to every new session of that role, including through a pooler. A
session-level `SET` sent through a transaction-mode pooler lands on whichever server connection
served that statement and leaks to other clients; use `SET LOCAL` inside a transaction for
one-off overrides (`SET LOCAL statement_timeout = '5min'` in a report). The numbers are starting
points: set them above the slowest legitimate statement of that role and tighten over time. Set
them in the migration that creates the roles, at the latest before Launch.

A request timeout (tower-http `TimeoutLayer`) or a client disconnect drops the handler's future
mid-query. SQLx sends no cancel request: the statement runs on in Postgres until it ends or
`statement_timeout` stops it, which is why that timeout sits below the request timeout.

## Queues with SKIP LOCKED, single-run work with advisory locks

Prefer a maintained Postgres-backed queue crate (apalis with its Postgres backend is one; check for
recent releases before adding it) or a jobs table you own; retries, backoff and dead-letter policy
are in `0x:backend-architecture`. Underneath, they all claim work like this:

```sql
UPDATE jobs SET status = 'running', locked_at = now(), attempts = attempts + 1
WHERE id IN (
  SELECT id FROM jobs WHERE status = 'queued' AND run_at <= now()
  ORDER BY priority, run_at LIMIT 10 FOR UPDATE SKIP LOCKED
)
RETURNING id, kind, payload, attempts;
```

- Claim and commit, then do the work outside the transaction. Holding the row lock for the job's
  duration keeps a transaction open for minutes and does not work through a transaction pooler.
- Because the claim is committed, a crashed worker leaves the row `running`. A reaper requeues rows
  whose `locked_at` is older than the visibility timeout, so handlers must be idempotent.
- Index only the claimable rows: `CREATE INDEX ... ON jobs (priority, run_at) WHERE status = 'queued'`.
- Queue tables churn. Delete or partition finished jobs and give the table aggressive autovacuum
  settings (`postgres-operations.md`), or the claim query slows as dead rows pile up.
- Bound the worker: claim at most as many rows as free slots (a `tokio::sync::Semaphore` or a
  capped `JoinSet`), never one unbounded `tokio::spawn` per row. A panic in a job task ends that
  task only, silently unless its result is collected: log each `JoinError`; the reaper requeues.

Advisory locks are application-defined locks keyed by a 64-bit number, with no table behind them.

```sql
-- Skip this run if another instance already holds the lock
SELECT pg_try_advisory_xact_lock(hashtextextended('nightly-invoice-run', 0)) AS acquired;

-- Serialize per tenant: wait for the lock, released automatically at commit or rollback
SELECT pg_advisory_xact_lock(hashtextextended('invoice-number:' || $1, 0));
```

Use the transaction-scoped `_xact_` functions, and run them on `&mut *tx`: sent to the pool, the
statement is its own transaction and the lock is gone when it returns. Session-scoped locks
(`pg_advisory_lock`, and SQLx's `PgAdvisoryLock`) survive
commit, must be released explicitly, and break under transaction pooling, where the unlock can
reach a different server connection. The key space is shared by the whole database, so derive keys
from a namespaced string. They coordinate clients of one database only; locks spanning systems
need fencing tokens (`0x:backend-architecture`).

## Diagnosing blocked queries and deadlocks

```sql
SELECT blocked.pid AS blocked_pid, blocked.application_name AS blocked_app,
       now() - blocked.query_start AS waiting_for, left(blocked.query, 80) AS blocked_query,
       blocker.pid AS blocker_pid, blocker.state AS blocker_state,
       now() - blocker.xact_start AS blocker_xact_age, left(blocker.query, 80) AS blocker_last_query
FROM pg_stat_activity AS blocked
JOIN LATERAL unnest(pg_blocking_pids(blocked.pid)) AS b(pid) ON true
JOIN pg_stat_activity AS blocker ON blocker.pid = b.pid
ORDER BY waiting_for DESC;
```

Follow the chain to the session that is blocking but not itself blocked.

| Root blocker looks like | Meaning | Action |
|---|---|---|
| `idle in transaction`, old `xact_start` | Application opened a transaction and stopped (awaited a network call while holding `tx`, kept a `Transaction` alive in a long-lived struct, crashed mid-flow) | Terminate it (`postgres-operations.md`), then fix the code path and set the idle timeout |
| `active` long-running statement | A slow report, backfill or missing index | Cancel if safe; move or batch the work |
| A waiting `ALTER TABLE` with many sessions behind it | Lock queue: the DDL waits for one old transaction, and every new query on that table waits behind the DDL | Cancel the DDL now; rerun it with `lock_timeout` (`migrations.md`) |
| `active` autovacuum "(to prevent wraparound)" | Mandatory freeze holding a weak lock that conflicts with DDL | Do not kill it; reschedule the DDL |

In `pg_locks`, rows with `granted = false` are the waiters. A waiter with `locktype = transactionid`
is waiting for a row lock held by that transaction (row locks live on the row, not in `pg_locks`);
`locktype = relation` is a table-level lock, almost always DDL.

Set `log_lock_waits = on`: any wait longer than `deadlock_timeout` is logged with the blocker's
process id. A deadlock log entry names both sides:

```text
ERROR:  deadlock detected
DETAIL:  Process 4821 waits for ShareLock on transaction 9012; blocked by process 4830.
         Process 4830 waits for ShareLock on transaction 9011; blocked by process 4821.
CONTEXT:  while updating tuple (0,5) in relation "accounts"
```

The server log adds each process's statement. Find the two rows or tables that the two code paths
lock in opposite order, and make both paths take them in the same order.

## Ask the user

- **When two people edit the same record, who wins?** Last write silently, or the second saver sees
  a conflict? Default: version check with a conflict message on anything users edit in forms.
- **Can this operation oversell or overspend, and what does one mistake cost?** It decides how
  much locking is justified. Default: guarded atomic updates for stock, credits and balances.
- **If a job runs twice, what breaks?** Decides whether single-run locking is needed in addition to
  idempotent handlers. Default: idempotent handlers always; advisory lock for scheduled batch runs.
- **What is the longest a normal request may take?** Sets `statement_timeout`. Default: 10 s for
  web, longer per worker type.
