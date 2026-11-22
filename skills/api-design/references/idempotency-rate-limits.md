# Idempotency, concurrency control and rate limits

Read this when: a client may retry a write (every client over a network does), two actors may
edit the same resource, or callers need to be limited, metered or told when to retry.

## Why every write needs a retry story

A client that gets a timeout cannot know whether the write happened. It will retry: the SDK does
it, the mobile OS does it, the user double-clicks, the queue redelivers. So each write endpoint
must answer "what happens when this exact request arrives twice", and the answer is designed, not
discovered. Three tools, cheapest first:

| Tool | How | Fits |
|---|---|---|
| Naturally idempotent operation | `PUT` to a client-chosen ID; "set status to X" instead of "toggle"; "set quantity to 5" instead of "add 1" | Updates and upserts |
| Unique constraint on a business key | `INSERT ... ON CONFLICT (tenant_id, external_ref) DO NOTHING`, then return the existing row | Creates where the client has a natural reference (order number, source event ID) |
| Idempotency key | Client sends a unique key per logical operation; server stores the outcome and replays it | Creates and actions with side effects: payments, sends, provisioning |

Use an idempotency key on every POST that creates something or triggers an external side effect,
on a public API from the first version, and on internal endpoints as soon as money, email or
third-party calls are involved (Launch). At Prototype, unique constraints on the obvious business
keys are enough.

## Idempotency keys: the protocol

The client sends `Idempotency-Key: <unique value>` (a UUID is the norm) and reuses the same value
for every retry of the same logical operation. The header name follows the convention set by
payment APIs and an IETF draft. Server behavior:

| Situation | Response |
|---|---|
| Key unseen | Record it as in progress, execute, store the outcome, respond |
| Key seen, same request, completed | Replay the stored status and body; do not execute. Mark the replay with a response header |
| Key seen, same request, still in progress | 409 with a code such as `idempotency_in_progress` and `Retry-After`; never execute a second copy in parallel |
| Key seen, different request body | 422 with `idempotency_key_reused`: the client has a bug, and replaying would return a result for a different request |
| Key missing on an endpoint that requires it | 400. Require it on public money-moving endpoints; elsewhere treat it as optional |

```sql
CREATE TABLE idempotency_keys (
  tenant_id     uuid        NOT NULL,
  key           text        NOT NULL,
  request_hash  bytea       NOT NULL,        -- SHA-256 of method + route + canonical body
  status        text        NOT NULL DEFAULT 'in_progress',
  response_code int,
  response_body jsonb,
  created_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, key)
);
```

Decisions inside the mechanism:

- **Scope the key to the credential's tenant** (and include the route in the fingerprint). A
  global key namespace lets one customer collide with, or probe, another's keys.
- **Claim the key atomically**: `INSERT ... ON CONFLICT DO NOTHING RETURNING`; zero rows returned
  means another request owns it. A read-then-write check has the exact race the key exists to prevent.
- **Fingerprint the request**: hash the method, route and the parsed body (serialized with
  sorted keys), not the raw bytes, so harmless whitespace differences do not read as a different request.
- **Put the key row, the business write and the stored response in one database transaction**
  whenever the operation is database-only. Commit makes all three true together; a crash leaves
  nothing, and the retry runs cleanly.
- **When an external call is involved**, the transaction cannot cover it. Derive a downstream
  idempotency key from the incoming one and pass it on (payment providers accept one), so a
  re-execution after a crash is absorbed by the provider. Record progress in steps so a retry
  resumes instead of restarting. The outbox pattern in `0x:backend-architecture`
  (`consistency-concurrency.md`) covers the general case.
- **What to store**: final outcomes, including deterministic 4xx (validation, insufficient
  funds), so the retry sees the same answer. Do not store outcomes where nothing happened and a
  retry should genuinely re-run: 429, 503 before execution, auth failures. For a 500 after
  unknown partial work, keep the key locked or stored; releasing it invites a duplicate.
- **Stale in-progress rows**: a crashed request leaves a row in progress. Give it a lease (a
  timestamp older than the request timeout means abandoned) and let the next retry take over,
  which is safe only when execution is transactional or resumable as above.
- **Retention**: keep keys at least 24 hours, longer than the longest client or queue retry
  window, and document the number. Delete older rows with a scheduled job.
- **Store the response body as returned**, not a pointer to the resource: a replay must show the
  original result even if the resource changed since.

Check: send the same POST with the same key twice concurrently and twice sequentially; exactly one
row and one side effect exist, both responses carry the same resource ID, and a third request with
the same key and a different body gets 422.

## Optimistic concurrency with ETags

Without a version check, two clients that read, edit and write back silently overwrite each
other (last write wins). Add it where humans or integrations edit the same record: settings,
documents, inventory, anything with a form that stays open. Skip it for append-only resources and
for fields that are set, not edited.

1. Keep a `version integer` on the row, incremented on every update (or use `updated_at` with
   enough precision; a counter is safer).
2. Return it on reads as `ETag: "42"` (a quoted string).
3. The client sends `If-Match: "42"` on PUT, PATCH or DELETE.
4. Apply the write conditionally and check the affected row count:

```sql
UPDATE documents SET body = $1, version = version + 1
WHERE id = $2 AND tenant_id = $3 AND version = $4;
```

5. Zero rows: return **412 Precondition Failed** with the current representation or version, so
   the client can re-read, merge and retry. If the endpoint requires the header and it is
   missing, return **428 Precondition Required**.

Traps: `If-Match` uses strong comparison, so a weak validator (`W/"42"`) never matches, and some
proxies weaken ETags when they compress a response (nginx does when it gzips). If ETags arrive
weakened or stripped, send the version in the body as well and accept it there. The check and the
write must be one statement or one transaction; comparing in application code and then updating
reintroduces the race. Decide per resource whether the header is required (data integrity
matters more than convenience) or optional (unconditional writes allowed), and document it. Row
locking and isolation levels are in `0x:postgres-database`, `transactions-concurrency.md`.

## Rate limiting: what to limit and how to answer

Limits exist for different reasons, and each wants its own mechanism:

| Purpose | Key | Where | Typical shape |
|---|---|---|---|
| Stop floods and scraping | IP, or IP prefix | CDN or edge (`0x:web-networking`, `cdn-edge.md`) | Coarse, high ceilings |
| Fairness between customers | API key, tenant | Application, shared store | Per-second or per-minute bucket, by plan |
| Protect a scarce resource | Tenant, per operation | Application | Cost points, concurrency ceiling |
| Commercial quota | Tenant, per billing period | Metering store | Monthly counter, see below |

- **Key authenticated traffic by tenant or API key, not by IP.** Customers share NAT addresses
  and run from many machines. Limit per tenant overall, and optionally per key within it so one
  leaked or runaway key cannot spend the whole allowance.
- **Unauthenticated endpoints** (login, signup, password reset, public forms) are limited by IP
  and by target (account, email) together, with stricter numbers. For IPv6, key on the /64
  prefix; a single address is free to rotate. Abuse defense beyond counting is in
  `0x:auth-identity`, `abuse-defense.md`.
- **Check the limit after authentication, before expensive work**, and count failed requests too
  (otherwise invalid requests are free).
- **Decide failure mode per limiter.** If the limit store is down: fail open for ordinary
  fairness limits (availability matters more), fail closed for login and for operations that
  cost money per call.

The 429 response is part of the contract:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 12
Content-Type: application/problem+json

{ "type": "https://api.example.com/problems/rate-limited", "title": "Rate limit exceeded",
  "status": 429, "code": "rate_limited", "detail": "Limit of 100 requests per minute for this key." }
```

Always send `Retry-After` in seconds: it is the one header every client library understands.
Also expose the limit state on successful responses so well-behaved clients slow down before
hitting it. The header names are not settled: an IETF draft defines `RateLimit` and
`RateLimit-Policy` fields and has changed shape between revisions, while `X-RateLimit-Limit`,
`X-RateLimit-Remaining` and `X-RateLimit-Reset` remain the de facto convention. Pick one set,
document the unit of the reset value (seconds until reset is less error-prone than a timestamp),
and keep it. Give quota exhaustion a different `code` (`quota_exceeded`) from short-term
throttling, because the client's correct reaction differs: wait seconds versus upgrade or wait
for the period to end.

## Algorithm and store

| Algorithm | Behavior | State per key | Choose when |
|---|---|---|---|
| Fixed window | Counter reset each window | 1 counter | Coarse quotas. Allows up to twice the limit across a window boundary |
| Sliding window counter | Current window plus weighted previous window | 2 counters | Default for "N per minute" limits: smooth enough, cheap |
| Sliding log | Timestamp per request | N entries | Exactness is required and N is small (login attempts) |
| Token bucket | Refills at a rate up to a burst capacity | Tokens + timestamp | Default for API traffic: allows short bursts, enforces an average; supports cost per request |
| GCRA | Token-bucket behavior from one stored timestamp | 1 value | Same as token bucket with less state; what several Redis limiters implement |

Store: a per-process in-memory limiter is correct only with one long-lived instance. With several
instances each allows the full limit, and on serverless the state vanishes between invocations.
Use Redis (or a compatible managed store) with the check-and-update done atomically in one Lua
script or a maintained library (`rate-limiter-flexible`, `@upstash/ratelimit`); separate GET and
SET calls race under concurrency and let bursts through. Postgres is fine for low-frequency
counters (per-day, per-month quotas, login attempts), not for per-request checks on a hot path.

A token bucket that also supports cost per request:

```lua
-- KEYS[1] = bucket key; ARGV = capacity, refill per second, now (ms), cost
local cap, rate, now, cost = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3]), tonumber(ARGV[4])
local b = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(b[1]) or cap
local ts = tonumber(b[2]) or now
tokens = math.min(cap, tokens + math.max(0, now - ts) / 1000 * rate)
local allowed = tokens >= cost
if allowed then tokens = tokens - cost end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(cap / rate * 1000))
return { allowed and 1 or 0, math.floor(tokens) }
```

When denied, `Retry-After` is `ceil((cost - tokens) / rate)` seconds. Passing the clock from the
application assumes app servers agree on time to within the precision that matters. Starting
numbers when nobody has decided: a burst of 2 to 5 times the per-second rate, limits set well
above what the product's own UI produces at its busiest, and separate, lower buckets for writes
and for expensive endpoints. Measure real usage before tightening; a limit that the customer's
normal integration trips is an outage for them.

## Metering and quotas

Short-term rate limits and period quotas are different systems: one protects the service and may
be approximate, the other is a commercial promise and must be defensible on an invoice.

- **Count asynchronously.** Do not write a row to Postgres per request. Increment a Redis
  counter keyed by tenant, key and period (`usage:{tenant}:{yyyy-mm}`), or emit a usage event to
  the log pipeline, and flush aggregates to durable storage on a schedule. Losing a few
  seconds of counts on a crash is usually acceptable for quotas, not for billing.
- **For billed usage, the durable record is an event with its own idempotency key**, aggregated
  later; pricing, invoicing and overage rules are in `0x:payments-billing`, `usage-billing.md`.
- **Record dimensions needed later**: tenant, key ID, route template (not the raw path), status
  class, cost units. Per-key usage is also the evidence for deprecations.
- **Enforce against the cached counter**, accepting slight overshoot; exactness at the boundary
  is not worth a synchronous write.
- **Expose it**: remaining quota in response headers, a `GET /usage` endpoint, a dashboard page,
  and proactive notice at about 80% and 100%. A customer who learns about the quota from a
  production 429 files a ticket or churns.
- **Hard stop or overage** is a business choice; hard stops on a paying customer's production
  traffic are rarely what anyone wants.

## Cost-based limits and concurrency ceilings

Request counts mislead when requests differ by orders of magnitude (a 100-row export versus a
single read, an LLM-backed endpoint, a search with wide filters).

- **Cost points**: assign each operation a cost and charge the bucket accordingly (the script
  above takes `cost`). Charge by actual work where it is only known afterward: deduct a base
  cost up front and the remainder on completion.
- **Concurrency ceiling per tenant** for long or heavy operations: at most N running exports,
  imports or generations. Implement as a counter or set in Redis with a TTL on each slot, so a
  crashed worker cannot hold a slot forever. Answer over-limit requests with 429 and a specific
  code, or accept them into a queue with a per-tenant cap, which is kinder for jobs.
- **Hard caps that need no counter**: maximum page size, maximum batch size, maximum date range
  on reports, statement timeouts. They bound the cost of any single request.
- **Global load shedding**: when queue depth or latency crosses a threshold, reject low-priority
  work early with 503 and `Retry-After` rather than letting every request time out together.

## Telling clients what to retry

Publish this table and implement it in any SDK shipped; clients left to guess either never retry
or retry everything in a tight loop.

| Response | Retry? | How |
|---|---|---|
| Connection error, timeout | Yes | Backoff; for POST only with an idempotency key |
| 408, 502, 503, 504 | Yes | Backoff; honor `Retry-After` |
| 429 | Yes | Wait at least `Retry-After` |
| 409 `idempotency_in_progress` | Yes | Short delay, same key |
| 500 | Yes, bounded | Same key; the failure may repeat |
| 409 (state conflict), 412 | No blind retry | Re-read, re-decide, send a new request |
| 400, 401, 403, 404, 422 | No | Fix the request or credential |

Backoff with full jitter: `delay = random(0, min(cap, base * 2^attempt))`, with a base near
0.5 s, a cap near 30 s, and 3 to 5 attempts for interactive calls (more for background workers).
Jitter is not optional: without it, every client that failed together retries together and
recreates the spike that caused the failure. `Retry-After` from the server overrides the computed
delay when it is longer. A retry must reuse the original idempotency key; generating a new key
per attempt defeats the mechanism. Outbound retry policy toward third parties, circuit breakers
and timeouts are in `0x:backend-architecture`, `integrations-resilience.md`.

## Ask the user

- **Which operations would hurt if they happened twice?** (charges, emails, orders, provisioning).
  These get required idempotency keys. Default: every POST that moves money, sends a message or
  calls a third party.
- **What limits should each plan have?** A pricing and packaging choice. Default: one generous
  limit for everyone until usage data exists, with stricter limits only on auth and costly endpoints.
- **When a customer exceeds a monthly quota, block or bill overage?** Default: do not block
  paying customers; notify, then discuss an upgrade.
- **Is losing a concurrent edit acceptable for this resource?** If not, require `If-Match`.
  Default: required for documents and settings edited by several people, optional elsewhere.
- **Should the limiter fail open or closed when its store is down?** A risk choice. Default:
  open for general API traffic, closed for login and paid third-party calls.
