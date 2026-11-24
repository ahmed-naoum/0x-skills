# Background, scheduled and durable jobs

Read this when: work should happen outside the request (slow calls, email, imports, fan-out),
something must run on a schedule, a process spans many steps or days, or jobs are running twice,
getting stuck, failing forever or piling up.

## What leaves the request path

| Work | Place |
|---|---|
| Needed to render the response and under about a second | Inline |
| A third-party call the response does not depend on (email, CRM, analytics, webhook out) | Job |
| Anything that must be retried until it succeeds | Job |
| Slower than a second or two, or of unbounded size (import, export, report, media) | Job, with status the client can poll or subscribe to |
| Fan-out: one action touching N recipients or rows | One job that enqueues N small jobs |

Respond with `202 Accepted` and a job or resource ID, expose its status (`queued`, `running`,
`succeeded`, `failed` with an error code), and let the client poll or stream (`realtime.md`).

Not queues, although they look like one: a detached `tokio::spawn(send_email(...))`, whose work dies
with the next deploy and whose error or panic goes nowhere (`runtime-language.md`); an in-memory
`mpsc` channel drained by a spawned loop; work spawned after the response on serverless functions,
which can be frozen once the response is sent, with no retry (telemetry only).

Jobs need a long-running worker process: the same binary, started with the `worker` subcommand. On a
host without one, use a hosted queue that calls back into HTTP endpoints (QStash and Google Cloud
Tasks are examples; any language), and treat those endpoints as public: verify signatures.

## Idempotent handlers

Delivery is at-least-once in every real queue. A handler runs twice when the worker crashes after
the effect but before the acknowledgment, when a lock or visibility timeout expires under a slow
job, when a timed-out attempt had in fact succeeded, and when the same job was enqueued twice
(double click, redelivered webhook). Write every handler so a second run changes nothing.

| Effect | Make it idempotent with |
|---|---|
| Database change | Guarded state transition, upsert, or a unique constraint on the business key |
| Third-party API call | The provider's idempotency key, taken from the persisted intent or attempt row (`charge:{payment_attempt_id}`) and reused on every retry of that attempt; a new attempt after a definitive failure gets a new row and a new key (`0x:payments-billing`) |
| Email, SMS, push | A sent-log row with a unique key (`receipt:{order_id}`) claimed before sending and marked sent after, plus the provider's idempotency key where it has one. Without that key, a crash between the two steps forces the lost-or-repeated choice below |
| Duplicate enqueue | A deterministic job key so the queue collapses duplicates |
| Several effects in one job | Split into one job per effect, or checkpoint after each step |

- The key never contains the attempt number, a timestamp or a random value generated inside the
  handler, or every retry is a new operation. "Check whether it was done, then do it" without a
  constraint is a race between two workers.
- For an effect that cannot be made idempotent, choose deliberately: record before acting gives
  at-most-once (may be lost), record after gives at-least-once (may repeat). Receipts tolerate a
  repeat; payouts do not.

## Postgres-backed queue first

Reasons it is the default: a job enqueued in the same transaction as the business write exists if
and only if that write committed (no dual write, no outbox to build); there is no extra system to
run; and the queue can be inspected and repaired with SQL. The mechanism is `SELECT ... FOR UPDATE
SKIP LOCKED`. In Rust, apalis with its Postgres storage is a maintained crate; graphile_worker and
underway are others (check recent releases before adopting). A hand-written table is small enough to
own, and then every rule in this file is yours to keep:

```sql
CREATE TABLE jobs (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  queue        text        NOT NULL,   kind text NOT NULL,   -- kind: 'send_invoice.v1'
  args         jsonb       NOT NULL,
  dedupe_key   text        UNIQUE,            -- 'daily-digest:2026-11-24'
  status       text        NOT NULL DEFAULT 'ready' CHECK (status IN ('ready', 'running', 'done', 'dead')),
  attempts     int         NOT NULL DEFAULT 0,   max_attempts int NOT NULL DEFAULT 20,
  run_at       timestamptz NOT NULL DEFAULT now(),
  locked_until timestamptz,          last_error text
);
CREATE INDEX jobs_due ON jobs (queue, run_at) WHERE status IN ('ready', 'running');
```

The worker claims a batch (taking over jobs whose lease expired with a crashed worker) and runs each
under a semaphore permit and a timeout shorter than the lease:

```rust
use std::{sync::Arc, time::Duration};
use sqlx::PgPool;
use tokio::{sync::Semaphore, task::JoinSet, time::error::Elapsed};
use tokio_util::sync::CancellationToken;

#[derive(sqlx::FromRow)]
pub struct Job { pub id: i64, pub kind: String, pub args: serde_json::Value, pub attempts: i32 }
pub enum JobError { Retry(anyhow::Error), Permanent(anyhow::Error) }

const CLAIM: &str = "UPDATE jobs SET status = 'running', attempts = attempts + 1,
       locked_until = now() + interval '5 minutes'
 WHERE id IN (SELECT id FROM jobs WHERE queue = $1
                AND (status = 'ready' AND run_at <= now() OR status = 'running' AND locked_until < now())
              ORDER BY run_at LIMIT $2 FOR UPDATE SKIP LOCKED)
 RETURNING id, kind, args, attempts";

async fn handle(pool: &PgPool, job: &Job) -> Result<(), JobError> {
    Err(JobError::Permanent(anyhow::anyhow!("unknown kind {}", job.kind))) // ... match job.kind
}
async fn finish(pool: &PgPool, job: &Job, outcome: Result<Result<(), JobError>, Elapsed>) -> sqlx::Result<()> {
    Ok(()) // ... mark done, or reschedule with backoff() or dead-letter; both fenced by `attempts`
}

pub async fn run_queue(pool: PgPool, queue: &'static str, slots: usize, stop: CancellationToken) -> sqlx::Result<()> {
    let permits = Arc::new(Semaphore::new(slots));
    let mut running = JoinSet::new();
    while !stop.is_cancelled() {
        while let Some(done) = running.try_join_next() {
            if let Err(e) = done { tracing::error!(error = %e, "job task panicked") }
        }
        let free = permits.available_permits() as i64;
        let jobs: Vec<Job> =
            if free == 0 { Vec::new() } else { sqlx::query_as(CLAIM).bind(queue).bind(free).fetch_all(&pool).await? };
        if jobs.is_empty() {
            tokio::select! { _ = stop.cancelled() => break, _ = tokio::time::sleep(Duration::from_secs(1)) => continue }
        }
        for job in jobs {
            let Ok(permit) = permits.clone().acquire_owned().await else { break };
            let pool = pool.clone();
            running.spawn(async move {
                let _permit = permit;
                let outcome = tokio::time::timeout(Duration::from_secs(240), handle(&pool, &job)).await;
                if let Err(e) = finish(&pool, &job, outcome).await { tracing::error!(error = %e, job = job.id) }
            });
        }
    }
    while running.join_next().await.is_some() {} // the caller bounds this wait (runtime-language.md)
    Ok(())
}
```

- `attempts` doubles as a fencing token: completion and failure updates carry `WHERE id = $1 AND
  attempts = $2`, so a worker whose lease expired cannot overwrite the result of the worker that
  took over. A failure sets `status = 'dead'` once `attempts` reaches `max_attempts`, otherwise
  `ready` with `run_at = now() + backoff`.
- A `dedupe_key` unique forever suits per-period keys; for "one pending job per entity" use a
  partial unique index on `status IN ('ready', 'running')` instead.

By stage: no queue at Prototype until something must be retried or outlive the request; the Postgres
queue at Launch; leave it at Scale only on a signal from the table below. Throughput: hundreds of
jobs per second comfortably, low thousands with tuning (rule of thumb). The table churns: a
long-running transaction anywhere in the database holds back vacuum, and dequeue slowing over hours
points to bloat, not to the workers. Workers hold connections, so count them in the pool budget;
`LISTEN` needs a direct session connection, not a transaction-mode pooler. Completed jobs need a
retention policy, or the table becomes the largest in the database.

Move off it when one of these is measured, not anticipated:

| Signal | Move to |
|---|---|
| Sustained throughput beyond what the primary absorbs, or queue churn hurting product queries | Redis-backed queue (apalis's Redis storage) or a managed queue (SQS and similar) |
| Need for features the library lacks: per-group rate limits, job dependency flows, very large fan-out | Redis-backed queue |
| Multi-step workflows with waits and compensation | Durable execution engine (below) |

Leaving Postgres gives up transactional enqueue, so the outbox becomes necessary
(`consistency-concurrency.md`). A Redis holding jobs needs `maxmemory-policy noeviction` and
persistence, unlike a cache Redis (`0x:data-stores`, `caching-redis.md`).

## Retries, backoff and dead letters

| Error | Action |
|---|---|
| Network error, timeout, 429, 5xx, deadlock or serialization failure | Retry with backoff |
| Validation failure, 4xx other than 408 and 429, entity deleted | Fail permanently, no retry |
| Unclassified error | Retry a bounded number of times, then dead-letter |

```rust
use std::time::Duration;

/// Full jitter: uniform between zero and the capped exponential delay. Without it, every job that
/// failed in the same outage retries in the same second and knocks the dependency down again.
pub fn backoff(attempt: u32, base: Duration, cap: Duration) -> Duration {
    let ceiling = base.saturating_mul(2u32.saturating_pow(attempt)).min(cap);
    ceiling.mul_f64(rand::random::<f64>())
}
```

- Size the schedule to outlast a realistic outage: a base of 10-30 s, a cap around an hour and
  enough attempts to span several hours suits third-party calls. Three quick retries cover a blip
  and nothing else. Honor `Retry-After` when the provider sends it.
- Always set a maximum attempt count: a poison message otherwise retries forever and, in an ordered
  queue, blocks everything behind it.
- After the last attempt the job goes to a dead-letter queue or a `dead` state that keeps the
  payload, every error and timestamps; alert on any arrival for critical queues. A dead-letter queue
  nobody reads is a delete with extra steps: build list-inspect-replay with the queue.
- Retry at one layer, normally the queue, and turn the SDK's own retries down: SDK, handler and
  queue retries multiply.

## Scheduled jobs exactly once

A spawned `tokio::time::interval` loop or an in-process cron crate runs once per instance, and not
at all during the gap of a deploy. Use one trigger, then deduplicate:

1. Trigger from one place: the queue crate's cron support, the platform's scheduler (an HTTP call:
   authenticate it with a secret header), or a leader chosen with `pg_try_advisory_lock`
   (session-scoped, so it needs a direct connection, not a transaction-mode pooler).
2. The trigger only enqueues a job with a deterministic key for the period
   (`daily-digest:2026-11-22`); duplicates collapse on the key. The job itself is idempotent too.

- Catch up instead of trusting the tick: the job processes "everything due since the last successful
  watermark", not "today". A missed run then heals on the next one.
- Prevent overlap when a run can outlast its interval: one running instance per job name.
- Schedule in UTC. A local time between 02:00 and 03:00 runs twice or never on daylight-saving days.
  For "9 am in each user's time zone", run hourly and select the users for whom it is 9.
- Spread load (not everything at minute zero, jitter on per-tenant schedules). A scheduled job fails
  by not running: it reports success to a heartbeat check that alerts when the report is missing
  (dead man's switch).

## Timeouts, concurrency and priorities

- Every job runs under `tokio::time::timeout`, shorter than the lease (the lock or visibility
  timeout); the timeout drops the handler at its next `.await`, so a half-done step must be safe to
  rerun. A lease shorter than the job hands it to a second worker while the first still runs: the
  most common cause of "jobs run twice". Long jobs extend the lease with a heartbeat.
- A CPU-bound job on a Tokio worker thread starves the task that extends the lease, so another
  worker takes the job over and runs it again. Move CPU work to `spawn_blocking`.
- Concurrency for I/O jobs is set by what is downstream (database pool, a provider's rate limit),
  not by CPU. A queue that calls one API gets a rate limit matching that API.
- Prefer separate queues by latency class over numeric priorities in one queue: `critical` (password
  reset, seconds), `default` (minutes), `bulk` (imports and backfills, hours), each with its own
  concurrency. Priorities inside one queue starve the low end, and one slow bulk job type can occupy
  every worker. Per-tenant fairness: `multi-tenancy.md`.

## Job arguments

Pass identifiers; load current state in the handler. A job runs later: a snapshot is stale by then,
large payloads hit size limits, and personal data ends up in queue storage and logs. Pass the value
itself only when the job needs it as it was at enqueue time, or the row may be deleted. Row not
found in the handler is a normal outcome: finish without retrying. If it appears right after
creation, the job was enqueued before the transaction committed: enqueue inside the transaction
(Postgres queue) or after commit, never before.

Arguments are a contract across deploys: old workers receive new jobs during a rollout, and delayed
or retrying jobs written by old code run days later.

- Additive changes only: a new argument is optional with a default (`#[serde(default)]`); deploy the
  consumer before the producer.
- A changed meaning or a removed argument is a new job kind (`send_invoice.v2`); the old handler
  stays until its queue is empty. Never rename a kind or its serde tag while jobs are in flight.
- Deserialize into a typed struct and validate with garde at handler entry; a deserialize or
  validation error fails permanently instead of crash-looping the worker.
- Keep serde's default of ignoring unknown fields: `deny_unknown_fields` makes an old worker reject
  every job that carries a field the new producer added.

## Monitoring and scaling workers

| Metric | Why | Starting alert |
|---|---|---|
| Age of the oldest ready job, per queue | The user-facing measure: how late the work is | `critical` over 60 s for 5 min; `default` over 10 min |
| Depth, per queue | Capacity planning; a deep queue of fast jobs is healthy, so depth alone is a poor alert | Sustained growth over an hour |
| Failure rate and dead-letter count | Broken handler or dependency | Any dead-lettered job in `critical` |
| Duration p95, per job type | Finds the job nearing its timeout | Above 80% of the timeout |
| Jobs running longer than their timeout | Stuck workers, lost locks | Any |

Workers needed is roughly arrival rate times average duration, divided by concurrency per worker.
Autoscale on queue age or backlog, not CPU: I/O-bound workers idle at low CPU while the queue grows.
Cap the scale by downstream limits: more workers than the database has connections turns a slow
queue into an outage. Shutdown: stop claiming, finish or release the current job in time.

## Durable execution engines

Use one when a process has several steps with side effects and any of: waits of hours or days, a
webhook or human approval to wait for, compensation on failure, or more than about three steps that
must each run once. Two or three steps without waits fit chained jobs plus a state-machine row. How
they work is also where the traps are:

- Workflow code is re-executed from a recorded history after every wake-up; completed steps return
  their recorded result instead of running again. Therefore workflow code must be deterministic:
  clock, randomness, network and database access go inside steps.
- Steps are still at-least-once at the boundary (a step can finish and crash before its result is
  recorded), so steps keep idempotency keys. Store references, not large payloads.
- Changing workflow code with runs in flight is the hard part: old runs replay against the new
  code. Use the engine's versioning mechanism and keep old branches until old runs finish.

Pick a hosted engine or a library that persists to the existing Postgres. From Rust: Restate
publishes a Rust SDK; underway runs durable steps on Postgres; Temporal's Rust SDK has trailed its
others, so check its status; cloud workflow services call HTTP endpoints in any language.
Self-hosting a workflow cluster is a Scale decision with people to run it.

## Draining or replaying a poisoned queue

1. Pause consumption; do not purge. Export the failed payloads first.
2. Find the shape: group failures by job type and error. One job type or one tenant means poison
   data; everything failing since a deploy means roll back.
3. Fix forward or route around: deploy the fix, or move the poison jobs aside by filter so healthy
   work resumes.
4. Before replaying, answer per job type. Is the handler idempotent? If not, reconcile against the
   provider instead. Is the job still wanted? A password-reset email from six hours ago is harmful,
   not late: carry an expiry and let the handler discard stale jobs. Will the replay flood
   something? Ten thousand emails or API calls at once trip rate limits and spam filters.
5. Replay a small batch, check effects and error rate, then continue at a throttled rate with
   bounded concurrency. For jobs that half-ran, ask the external system what happened (look up by
   idempotency key) rather than assuming either outcome.

## Ask the user

- **Which background work is a promise to a customer (receipt, password reset, payout, export) and
  how late may it be?** That defines the queues, their alerts and what `critical` means. Assume
  account email within a minute, everything else within ten.
- **When a job fails for good, who is told: the customer, the founder or nobody?** Dead letters need
  an owner. Assume an alert to the founder and a visible failed status for the user.
- **For scheduled sends, whose clock applies?** UTC, the organization's zone or each user's zone
  changes the design. Assume the organization's configured time zone.
