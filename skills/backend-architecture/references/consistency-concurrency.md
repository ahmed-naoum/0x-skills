# Consistency and concurrency across systems

Read this when: a workflow spans several steps or systems (database plus payment provider, queue,
search index, email, object storage) and must stay correct under retries, double clicks, races,
crashes mid-step and messages that arrive twice or out of order.

Single-database transactions, isolation levels and row locks are in `0x:postgres-database`
(`transactions-concurrency.md`). This file starts where one transaction is no longer enough.

## Where strong consistency is required

Inside one Postgres, everything can be strongly consistent for free: use a transaction and a
constraint. The decision appears the moment a second system holds state.

| Must be strong (one transaction, enforced by constraint) | Eventual is fine (seconds of lag) |
|---|---|
| Money: balances, charges, credits, refunds | Search index, analytics, activity feeds |
| Inventory and seat counts at a hard limit | Counters shown for display (likes, views) |
| Uniqueness: email, slug, one active subscription per org | Notifications and email |
| Permission and access revocation | Caches, recommendations, derived read tables |
| State transitions of an order, payout, job | Usage totals shown on a dashboard |

Test for a doubtful case: "two requests see a value five seconds stale; what is the worst
outcome?" If the answer involves money, security or a broken promise to a customer, it is strong.
Put the invariant in the database (`UNIQUE`, `CHECK`, foreign key, exclusion constraint), not only
in application code: the application check is a read followed by a write, and another request
fits between them.

## Workflows as state machines

Any entity with a lifecycle gets one `status` column with a closed set of values, a transition
table in code, and guarded transitions. Several booleans (`is_paid`, `is_shipped`, `is_canceled`)
encode eight combinations of which most are invalid and all are reachable.

```ts
const transitions = {
  pending:   ['paid', 'canceled', 'expired'],
  paid:      ['fulfilled', 'refunded'],
  fulfilled: ['refunded'],
  canceled:  [], expired: [], refunded: [],
} as const satisfies Record<Status, readonly Status[]>;
```

The guard lives in the write itself, so the check and the change are one atomic statement:

```sql
UPDATE orders SET status = 'paid', paid_at = now()
WHERE id = $1 AND status = 'pending'
RETURNING id;
```

- Zero rows returned means another actor moved it first or the transition is invalid. Read the
  current status: already `paid` by the same event is success (idempotent); anything else is a
  conflict to report, not to overwrite.
- Never read the status, check it in application code, then write unconditionally. That is the
  race this pattern removes.
- Insert a row into a transitions table (entity, from, to, actor, reason, time) in the same
  transaction. It is the audit trail and the debugging tool.
- Timeouts are transitions too: a scheduled job moves `pending` to `expired` with the same guard.
- Before calling an external system, move to an in-flight status (`charging`) and commit. A crash
  then leaves evidence, and a sweeper can find rows stuck in an in-flight status for more than a
  few minutes and ask the provider what happened.
- Add a `CHECK` or enum on the column so a typo cannot create a ninth state. A state-machine
  library is optional; the map and the guarded update are the substance.

## Dual writes

A dual write is any code path that changes two systems and assumes both succeed. A crash, timeout
or deploy between them leaves the systems disagreeing, silently. Ordering the calls differently
only changes which inconsistency occurs.

| Pair | Failure when written naively | Pattern |
|---|---|---|
| Database, then queue or event | Commit succeeds, publish fails: the event never happens. Publish first: consumers act on a row that rolled back | Transactional outbox, or a Postgres-backed queue enqueued in the same transaction |
| Database and external API (charge, provision) | API succeeded, local commit failed or timed out: money moved with no record | Intent row committed first with an idempotency key, then the call, then record the outcome; a sweeper resolves stuck intents |
| Database and search index or cache | Index holds data that was rolled back, or misses a committed change | Database is truth; update the derived store asynchronously from the outbox; keep a full rebuild command |
| Database and object storage | Row points to a missing object, or objects exist with no row | Upload to a pending key, then commit the row; expire orphans with a lifecycle rule |

Never hold a database transaction open across a network call to another system. It pins a
connection and row locks for the duration of someone else's latency, and a rollback cannot undo
the remote effect anyway.

The intent pattern for an external call:

1. In one transaction: insert the intent (`status = 'pending'`, idempotency key derived from the
   business entity, such as `charge:{order_id}`). Commit.
2. Call the provider with that idempotency key and a timeout.
3. Record the outcome with a guarded transition (`pending` to `succeeded` or `failed`).
4. A timeout is not a failure: the outcome is unknown. Leave the intent pending; retry with the
   same key or query the provider. The sweeper does this for intents the process never finished.

## Transactional outbox

Write the event to a table in the same transaction as the business change. A relay publishes it
afterwards. The event exists if and only if the change committed.

```sql
CREATE TABLE outbox (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  topic        text        NOT NULL,
  key          text        NOT NULL,   -- entity id, for per-entity ordering
  payload      jsonb       NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz
);
CREATE INDEX outbox_pending ON outbox (id) WHERE processed_at IS NULL;
```

```sql
-- relay, inside a transaction: claim, publish, then mark processed
SELECT id, topic, key, payload FROM outbox
WHERE processed_at IS NULL
ORDER BY id
LIMIT 100
FOR UPDATE SKIP LOCKED;
```

- If the job queue already lives in Postgres (pg-boss, Graphile Worker), enqueueing the job
  inside the business transaction is the outbox. Do not build a second one.
- Delivery is at-least-once: the relay can publish and crash before marking the row. Consumers
  deduplicate (next section).
- The relay is the one bounded exception to "no transaction across a network call": it locks
  only outbox rows. Keep the batch small and the publish timeout at a few seconds, or claim rows
  with a lease column and publish outside any transaction.
- Select on `processed_at IS NULL`, never on "id greater than the last one seen". Identity values
  are assigned before commit, so a lower id can become visible after a higher one and a
  high-water-mark reader skips it forever.
- Two relays with `SKIP LOCKED` can publish batches out of order. If per-entity order matters,
  run one relay (guarded by an advisory lock) or partition by a hash of `key`.
- `LISTEN/NOTIFY` is a wake-up hint for the relay, not the delivery mechanism: notifications are
  lost when no listener is connected and do not pass through a transaction-mode pooler. Always
  poll as well.
- Delete processed rows after a retention window, and alert when the oldest unprocessed row is
  older than a minute or two: that is a stalled relay.
- Change-data-capture from the replication log replaces the polling relay at Scale; the table and
  the contract stay the same.

## Consumers that survive real delivery

Every consumer of a queue, outbox or webhook sees duplicates, reordering and long delays. Design
for all three or the handler is wrong on the first provider incident.

| Problem | Technique |
|---|---|
| Duplicate | Make the effect naturally idempotent (upsert, set a value instead of incrementing, guarded transition), or record `(consumer, event_id)` in a table with a primary key in the same transaction as the effect and skip on conflict |
| Reordered | Carry a per-entity version or sequence and apply only if it is greater than the stored one; or treat the event as a hint and fetch the current state from the source |
| Delayed by hours or days | Never assume the payload is current; re-read state; tolerate "entity no longer exists" as a normal outcome |
| Arrives before the local row exists | Webhook beats the response of the request that created the object: upsert by provider ID, or retry with backoff |
| Never arrives | Reconciliation (last section) |

```sql
INSERT INTO processed_events (consumer, event_id) VALUES ($1, $2)
ON CONFLICT DO NOTHING;   -- affected rows = 0 means already handled: stop here
```

"Thin event, then fetch" is the most robust default for third-party webhooks: use the event only
to learn which object changed, fetch that object from the provider, and write what the provider
says now. It makes duplicates and reordering harmless at the cost of one API call.

## Read-your-writes

Users forgive stale data from others; they do not forgive their own change disappearing. Lag
comes from read replicas, search indexes, caches, CDN copies and asynchronous projections.

| Technique | Use when |
|---|---|
| Return the written entity from the mutation and update client state from the response | Always; it is free |
| Read from the primary for that user for a few seconds after their write (marker in the session or a cookie) | Read replicas serve user-facing pages |
| Record the WAL position after the write (`pg_current_wal_lsn()`) and wait on the replica until `pg_last_wal_replay_lsn()` passes it, with a timeout that falls back to the primary. PostgreSQL 19 adds a `WAIT FOR LSN` command for this; older versions poll | Replica reads must be exact and the marker approach is too coarse |
| Merge the just-written item into list or search results on the client, or show it as "indexing" | The lagging store is a search index or projection |
| Optimistic UI with a pending marker, reconciled when the server answers | Latency matters more than certainty; never for payments |

Default: do not route user-facing reads to replicas until Scale, and then use the primary-pinning
marker. After a mutation in a framework with a server cache, invalidate the affected paths or
tags in the same action (`0x:react-nextjs`, `data-state.md`).

## Sagas

A saga replaces a transaction that would span systems with a sequence of local steps, each with
a compensating action. Prefer orchestration (one coordinator function whose progress is stored
as a state machine row) over choreography (services reacting to each other's events): the whole
flow is readable in one place, which a small team needs.

1. Order the steps: reversible ones first (reserve stock, authorize a card), then the pivot (the
   step that cannot be undone: capture, send, ship), then steps that only need retrying until
   they succeed (receipt, index, notify).
2. Persist progress after every step, so a restarted coordinator resumes instead of repeating.
3. Every step and every compensation is idempotent and retried with backoff.
4. Compensation is a new business action, not a rollback: a refund, a release, an apology email.
   Other people may already have seen the intermediate state.
5. A compensation that keeps failing goes to a human queue with full context. Decide who that is.

Two or three steps without waits fit a state machine row plus jobs. Longer flows, waits for
days, or human approval belong in a durable execution engine (`background-jobs.md`).

## Distributed locks

First check whether a lock is needed at all. In order of preference:

1. A constraint or guarded update makes the race harmless. No lock.
2. All contenders share the Postgres: `SELECT ... FOR UPDATE` on the row, or
   `pg_advisory_xact_lock(key)`. Released at transaction end, cannot expire mid-work. Use the
   transaction-scoped form: session-scoped advisory locks break behind a transaction-mode pooler.
3. Only then a lock in Redis or another store.

A lock with an expiry can be lost while the holder still believes it holds it (GC pause, slow
network, suspended VM). A lock without an expiry is held forever after a crash. So:

- Acquire with an expiry and a random token: `SET lock:{name} {token} NX PX 30000`.
- Release only your own lock, atomically:

```lua
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
end
return 0
```

- Expiry is longer than the worst-case work, or the holder renews it and stops when renewal fails.
- If the lock only saves duplicate effort (two workers warming the same cache), the above is
  enough. If two holders at once would corrupt data, it is not: add a fencing token. The lock
  service hands out a strictly increasing number with each grant, and the protected resource
  rejects any write carrying a number lower than the last it accepted:

```sql
UPDATE documents SET body = $1, fence = $2
WHERE id = $3 AND fence < $2;   -- 0 rows: a newer holder exists, abort
```

Without a resource that checks the token, no expiring lock guarantees mutual exclusion,
whichever algorithm issues it. When correctness depends on the lock, move the exclusion into the
database that holds the data.

## Reconciliation jobs

Every at-least-once, eventual or cross-system path drifts eventually. A reconciliation job is
the control that finds the drift before a customer does. Mandatory at Launch for anything
involving money; add others as each integration appears.

Invariants worth checking:

- Every local `succeeded` payment has exactly one matching provider charge, and the reverse.
- Every active provider subscription has an active local entitlement, and the reverse.
- Ledger entries sum to the stored balance.
- No row has sat in an in-flight status (`charging`, `processing`, `syncing`) past its limit.
- No outbox row or job is unprocessed past its limit.
- Every file row has an object in storage; cached counters equal `count(*)`.

Design rules:

- Detect first, repair later. Start read-only: report the IDs that violate the invariant and
  alert when the count is above zero after a grace period.
- Ignore items younger than a few minutes; in-flight work is not drift.
- Automate a repair only for a drift class that is understood, and log every repair.
- Scan a window by `updated_at` with overlap, paginate provider listings, and run against a
  replica at Scale. A nightly full pass plus an hourly recent-window pass is a sound start.
- Treat every finding as a bug report: the job is the safety net, the fix belongs upstream.

## Ask the user

- **Which operations move money or grant access?** Those get strong consistency, idempotency
  keys and reconciliation from the first paying customer. Assume payments, credits, seats and
  plan entitlements.
- **When a multi-step process fails halfway, what should the customer see?** Refund, retry later
  or manual follow-up is a business choice that defines the compensations. Assume automatic
  retry, then refund and notify.
- **Who handles cases automation cannot resolve, and how fast?** Stuck sagas and reconciliation
  findings need an owner. Assume the founder, alerted the same day.
- **How stale may dashboards, search and counters be?** It decides whether projections can be
  asynchronous. Assume a few seconds is acceptable everywhere except the user's own writes.
- **Is overselling ever acceptable (seats, stock, bookings)?** If a small oversell is cheaper
  than a rejected sale, the hard limit can be soft. Assume no overselling.
