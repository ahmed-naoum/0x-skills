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

Not queues, although they look like one:

- A promise that is not awaited (`void sendEmail()`). The work dies with the process on the next
  deploy, and its failure is an unhandled rejection.
- `after()` or `waitUntil()` on serverless hosts. They extend the invocation, without retry or
  persistence. Acceptable for telemetry, never for anything a customer would miss.
- An in-memory array drained by `setInterval`.

Jobs need a long-running worker process: the same codebase, a second entrypoint. On a host
without one, use a hosted queue or durable-execution service that calls back into HTTP endpoints
(Inngest, Trigger.dev, QStash are examples), and treat those endpoints as public: verify the
signature.

## Idempotent handlers

Delivery is at-least-once in every real queue. A handler runs twice when the worker crashes after
the effect but before the acknowledgment, when a lock or visibility timeout expires under a slow
job, when a timed-out attempt had in fact succeeded, and when the same job was enqueued twice
(double click, redelivered webhook). Write every handler so a second run changes nothing.

| Effect | Make it idempotent with |
|---|---|
| Database change | Guarded state transition, upsert, or a unique constraint on the business key |
| Third-party API call | The provider's idempotency key, derived from the business entity: `charge:{orderId}` |
| Email, SMS, push | A sent-log row with a unique key (`receipt:{orderId}`) claimed before sending and marked sent after, plus the provider's idempotency key where it has one. Without that key, a crash between the two steps forces the lost-or-repeated choice below |
| Duplicate enqueue | A deterministic job key so the queue collapses duplicates |
| Several effects in one job | Split into one job per effect, or checkpoint after each step |

- The key never contains the attempt number, a timestamp or a random value generated inside the
  handler. Then every retry is a new operation and the key protects nothing.
- "Check whether it was done, then do it" without a constraint is a race between two workers.
- For an effect that cannot be made idempotent, choose deliberately: record before acting gives
  at-most-once (may be lost), record after gives at-least-once (may repeat). Receipts tolerate a
  repeat; payouts do not.

## Postgres-backed queue first

Reasons it is the default: a job enqueued in the same transaction as the business write exists
if and only if that write committed (no dual write, no outbox to build); there is no extra
system to run; and the queue can be inspected and repaired with SQL. The mechanism is
`SELECT ... FOR UPDATE SKIP LOCKED`. Use a maintained library rather than writing one: pg-boss or
Graphile Worker for Node; River (Go), Oban (Elixir), Procrastinate (Python), Solid Queue or
GoodJob (Rails).

By stage: at Prototype add no queue until something must be retried or outlive the request (on
a host without workers, a hosted job service); at Launch run the Postgres queue with a `worker`
process; at Scale leave it only on a signal from the table further down.

What to know while running it:

- Throughput is comfortable in the hundreds of jobs per second and reaches the low thousands with
  tuning (rule of thumb; depends on job size and hardware).
- The job table churns. A long-running transaction anywhere in the database holds back vacuum and
  dequeue gets slower over hours: that pattern points to bloat, not to the workers.
- Workers hold connections; count them in the pool budget. `LISTEN` needs a direct session
  connection, not a transaction-mode pooler.
- Completed jobs need a retention policy, or the table becomes the largest in the database.

Move off it when one of these is measured, not anticipated:

| Signal | Move to |
|---|---|
| Sustained throughput beyond what the primary absorbs, or queue churn hurting product queries | Redis-backed queue (BullMQ) or a managed queue (SQS and similar) |
| Need for features the library lacks: per-group rate limits, job dependency flows, very large fan-out | Redis-backed queue |
| No long-running process on the host | Hosted queue or durable-execution service |
| Multi-step workflows with waits and compensation | Durable execution engine (below) |

Leaving Postgres gives up transactional enqueue, so the outbox becomes necessary
(`consistency-concurrency.md`). A Redis that holds jobs must not evict: set `maxmemory-policy
noeviction` and enable persistence, or jobs disappear under memory pressure. A cache Redis and a
queue Redis therefore want different configurations (`0x:data-stores`, `caching-redis.md`).

## Retries, backoff and dead letters

Classify the error before retrying:

| Error | Action |
|---|---|
| Network error, timeout, 429, 5xx, deadlock or serialization failure | Retry with backoff |
| Validation failure, 4xx other than 408 and 429, entity deleted | Fail permanently, no retry |
| Unknown exception | Retry a bounded number of times, then dead-letter |

```ts
const delayMs = Math.random() * Math.min(capMs, baseMs * 2 ** attempt); // full jitter
```

- Without jitter, every job that failed in the same outage retries in the same second and
  knocks the dependency down again.
- Size the schedule to outlast a realistic outage: a base of 10-30 s, a cap around an hour and
  enough attempts to span several hours suits third-party calls. Three quick retries cover a
  blip and nothing else.
- Honor `Retry-After` when the provider sends it.
- Always set a maximum attempt count. A job that can never succeed (a poison message) otherwise
  retries forever and, in an ordered queue, blocks everything behind it.
- After the last attempt the job goes to a dead-letter queue or a `failed` state that keeps the
  payload, every error and timestamps. Alert on any arrival for critical queues. A dead-letter
  queue nobody reads is a delete with extra steps: build the list-inspect-replay command with
  the queue.
- Retries multiply across layers: SDK retries times handler retries times queue retries. Retry at
  one layer, normally the queue, and turn the SDK's own retries down.

## Scheduled jobs exactly once

`setInterval` or an in-process cron library runs once per instance, and not at all during the
gap of a deploy. Use one trigger, then deduplicate:

1. Trigger from one place: the queue library's cron feature, the platform's scheduler, or a
   leader chosen with `pg_try_advisory_lock` (session-scoped, so it needs a direct connection,
   not a transaction-mode pooler).
2. The trigger only enqueues a job with a deterministic key for the period
   (`daily-digest:2026-11-22`). A duplicate trigger collapses on the key.
3. The job itself is idempotent, like any other.

- Catch up instead of trusting the tick: the job processes "everything due since the last
  successful watermark", not "today". A missed run then heals on the next one.
- Prevent overlap when a run can outlast its interval: one running instance per job name.
- Schedule in UTC. A local time between 02:00 and 03:00 runs twice or never on daylight-saving
  days. For "9 am in each user's time zone", run hourly and select the users for whom it is 9.
- Spread load: not everything at minute zero, and add jitter to per-tenant schedules.
- A scheduled job fails silently by not running. Monitor it with a heartbeat: the job reports
  success to a check that alerts when the report is missing (dead man's switch).
- A platform scheduler that calls an HTTP endpoint needs that endpoint authenticated with a
  secret header and safe to call twice.

## Timeouts, concurrency and priorities

- Every job has a timeout, and the handler receives an abort signal it passes to outbound calls.
- The queue's lock or visibility timeout must exceed the job timeout. If it is shorter, the queue
  hands the job to a second worker while the first is still running: the most common cause of
  "jobs run twice". Long jobs extend the lock with a heartbeat.
- A CPU-bound job that blocks the event loop stops the heartbeat, so the queue marks the job
  stalled and reruns it. Move CPU work to a child process or worker thread.
- Concurrency for I/O jobs is set by what is downstream (database pool, a provider's rate limit),
  not by CPU. A queue that calls one API gets a rate limit matching that API.
- Prefer separate queues by latency class over numeric priorities in one queue: `critical`
  (password reset, seconds), `default` (minutes), `bulk` (imports and backfills, hours), each
  with its own concurrency. Priorities inside one queue starve the low end, and one slow bulk job
  type can occupy every worker.
- Per-tenant fairness is in `multi-tenancy.md`.

## Job arguments

Pass identifiers; load current state in the handler. A job runs later: a snapshot is stale by
then, large payloads hit size limits, and personal data ends up in queue storage and logs. Pass
the value itself only when the job needs it as it was at enqueue time, or the row may be deleted.

- Row not found in the handler is a normal outcome: finish without retrying.
- If "not found" appears right after creation, the job was enqueued before the transaction
  committed. Enqueue inside the transaction (Postgres queue) or after commit, never before.

Arguments are a contract across deploys: old workers receive new jobs during a rollout, and
delayed or retrying jobs written by old code run days later.

- Additive changes only. A new argument is optional with a default; deploy the consumer before
  the producer.
- A changed meaning or a removed argument is a new job name (`send-invoice.v2`); the old handler
  stays until its queue is empty.
- Never rename a job or handler class while jobs are in flight.
- Validate arguments with a schema at handler entry; invalid arguments fail permanently to the
  dead-letter queue instead of crash-looping the worker.

## Monitoring and scaling workers

| Metric | Why | Starting alert |
|---|---|---|
| Age of the oldest ready job, per queue | The user-facing measure: how late the work is | `critical` over 60 s for 5 min; `default` over 10 min |
| Depth, per queue | Capacity planning; a deep queue of fast jobs is healthy, so depth alone is a poor alert | Sustained growth over an hour |
| Failure rate and dead-letter count | Broken handler or dependency | Any dead-lettered job in `critical` |
| Duration p95, per job type | Finds the job nearing its timeout | Above 80% of the timeout |
| Jobs running longer than their timeout | Stuck workers, lost locks | Any |

Workers needed is roughly arrival rate times average duration, divided by concurrency per
worker. Autoscale on queue age or backlog, not CPU: I/O-bound workers sit at low CPU while the
queue grows. Cap the scale by downstream limits; more workers than the database has connections
turns a slow queue into an outage. Workers shut down gracefully: stop fetching, finish or
release the current job within the grace period (`runtime-language.md`).

## Durable execution engines

Use one when a process has several steps with side effects and any of: waits of hours or days,
waiting for a webhook or human approval, compensation on failure, or more than about three steps
that must each run once. Two or three steps without waits fit chained jobs plus a state-machine
row.

How they work, which is also where the traps are:

- Workflow code is re-executed from a recorded history after every wake-up; completed steps
  return their recorded result instead of running again. Therefore workflow code must be
  deterministic: clock, randomness, network and database access go inside steps.
- Steps are still at-least-once at the boundary (a step can finish and crash before its result
  is recorded). Steps keep idempotency keys.
- Changing workflow code while runs are in flight is the hard part: a run started on the old
  code replays against the new code. Use the engine's versioning mechanism and keep old branches
  until old runs finish.
- Step results are stored; pass references, not large payloads.

For a small team, pick a hosted engine or a library that persists to the existing Postgres
(Inngest, Trigger.dev, DBOS, Restate, Temporal Cloud and cloud-vendor workflow services are the
field). Self-hosting a workflow cluster is a Scale decision with people to run it.

## Draining or replaying a poisoned queue

1. Pause consumption; do not purge. Export the failed payloads first.
2. Find the shape: group failures by job type and error. One job type or one tenant means poison
   data; everything failing since a deploy means roll back.
3. Fix forward or route around: deploy the fix, or move the poison jobs aside by filter so
   healthy work resumes.
4. Before replaying, answer per job type:
   - Is the handler idempotent? If not, reconcile against the provider instead of replaying.
   - Is the job still wanted? Drop expired work by age: a password-reset email from six hours
     ago is harmful, not late. Carry an enqueue time or expiry on such jobs and let the handler
     discard stale ones.
   - Will the replay flood something? Ten thousand emails or API calls at once trip rate limits
     and spam filters.
5. Replay a small batch, check effects and error rate, then continue at a throttled rate with
   bounded concurrency.
6. For jobs that half-ran, ask the external system what happened (look up by idempotency key)
   rather than assuming either outcome.

## Ask the user

- **Which background work is a promise to a customer (receipt, password reset, payout, export)
  and how late may it be?** That defines the queues, their alerts and what `critical` means.
  Assume account email within a minute, everything else within ten.
- **Does the host run a long-lived worker process?** It decides between a Postgres queue with a
  worker and a hosted job service. Assume yes on a PaaS; no on serverless-only hosting.
- **When a job fails for good, who is told: the customer, the founder or nobody?** Dead letters
  need an owner. Assume an alert to the founder and a visible failed status for the user.
- **For scheduled sends, whose clock applies?** UTC, the organization's zone or each user's zone
  changes the design. Assume the organization's configured time zone.
- **After an outage, should missed work be caught up or skipped?** Digests may be skipped;
  invoices may not. Assume catch up for money and data, skip for notifications past their use.
