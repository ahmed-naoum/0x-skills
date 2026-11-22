# Third-party integrations and resilience

Read this when: calling an external API or another service, storing a customer's OAuth
connection, syncing data with an outside system, or when a slow or failing dependency turns into
your own outage.

Receiving and sending webhooks, and rate limits on your own API, are in `0x:api-design`
(`webhooks.md`, `idempotency-rate-limits.md`). LLM provider fallbacks are in `0x:ai-features`
(`cost-latency.md`).

## Timeouts on every outbound call

A call without a timeout waits as long as the other side likes. During a vendor brownout each
waiting request holds a socket, a database connection and memory, and the application stops
answering although nothing of its own is broken. This is the most common way a third party
takes a product down, and the cheapest to prevent.

| Client | Default behavior | Set |
|---|---|---|
| `fetch` in Node | No overall deadline; the underlying client only limits header and body idle time, in minutes | `signal: AbortSignal.timeout(ms)` on every call, combined with the request's signal |
| Vendor SDKs | Often a minute or more, plus built-in retries | The client's timeout and retry options, explicitly, at construction |
| Postgres | Statements run unbounded | `statement_timeout` on the application role, a connect timeout and a pool acquire timeout |
| Redis | Commands queue while disconnected | Connect and command timeouts; a bounded offline queue |
| Anything else | Assume none | Read the client's documentation once and write the value down |

```ts
const res = await fetch(url, {
  signal: AbortSignal.any([ctx.signal, AbortSignal.timeout(3_000)]),
});
```

- Budget: 1-5 s for a call a user is waiting on, 10-30 s inside a job. Derive the value from the
  dependency's observed p99 with margin, and keep it below the caller's remaining deadline
  (`runtime-language.md`).
- Streams (LLM output, large downloads) need an idle timeout between chunks rather than one
  total deadline.
- A timeout on a write means the outcome is unknown, not failed. Retry with the same idempotency
  key or query the vendor; never tell the user "failed" and let them submit again without one.
- Record duration, outcome and vendor for every outbound call as a metric. Without it the first
  question in an incident ("is it them or us?") takes an hour.

## Retries and circuit breakers

Retry only what is both safe and likely to help.

| Response | Retry? |
|---|---|
| Connection error, timeout, 408, 429, 500, 502, 503, 504 | Yes, if the call is idempotent or carries an idempotency key |
| 400, 401, 403, 404, 409, 422 | No. The same request gets the same answer |
| POST without an idempotency key | No. Add the key, or reconcile instead |

```ts
const delayMs = Math.random() * Math.min(capMs, baseMs * 2 ** attempt); // full jitter
```

- On the request path: at most two or three attempts inside the request's total deadline. In a
  job: long backoff over hours (`background-jobs.md`).
- Honor `Retry-After` on 429 and 503, capped at a maximum you choose.
- Retry at one layer. If the job retries, set the SDK's retries to zero, or three layers of
  three attempts become twenty-seven calls.

A circuit breaker stops calling a dependency that is failing, so callers fail in milliseconds
instead of waiting for a timeout each time, and the dependency gets room to recover.

- Closed: calls pass. Open: calls fail immediately for a cool-down (10-30 s). Half-open: one
  probe passes; success closes, failure reopens.
- Trip on failure rate over a rolling window with a minimum volume (a rule-of-thumb start: half
  of at least twenty calls in ten seconds, then tune from the metric). Count timeouts and 5xx; a
  4xx is the caller's fault and does not count.
- One breaker per dependency, and per endpoint or account where they fail independently.
  Per-process state is fine: each instance learns within seconds.
- Use a maintained library (cockatiel, opossum). Expose breaker state as a metric and alert when
  one stays open.
- At low traffic a breaker never collects enough samples. Timeouts plus a fallback are enough
  until Launch-level volume on that call.

Add a concurrency cap per dependency (a semaphore: at most N calls in flight, reject beyond)
for any vendor called on hot paths. It keeps one slow vendor from taking every socket and
worker, which a breaker only does after failures accumulate.

## Degrading gracefully

Classify every dependency once, in a list kept in the repository:

| Class | Meaning | Examples | When it is down |
|---|---|---|---|
| Critical | The product cannot answer without it | Primary database, session validation | Fail fast with a clear error page; this is the outage to prevent by redundancy, not by fallback |
| Degradable | A feature is worse or missing | Search, recommendations, AI features, avatars, maps, analytics | Hide or disable the feature with a message, or fall back to a simpler path (database search) |
| Deferrable | The effect can happen later | Email, CRM sync, webhooks out, invoicing documents | Enqueue and confirm to the user; the job retries |

- Do not call a vendor on the request path to answer a question your own database could answer.
  Entitlements are the standard case: keep plan and access state locally, updated by webhooks
  and reconciliation, so a payment provider outage does not lock paying users out.
- Serve stale on error for read-mostly data (exchange rates, remote configuration, feature flag
  definitions): keep the last good value past its normal expiry and use it when the refresh
  fails.
- Fail closed where the dependency is a safety control (fraud screening, sanctions checks,
  authorization). Decide this per dependency with the user; it is a business risk choice.
- Readiness checks must not include third parties. Otherwise a vendor outage marks every
  instance unready and the load balancer takes the whole product offline. Liveness checks
  nothing external at all (`0x:site-reliability`).
- Give each integration a kill switch (a flag) so it can be turned off in seconds during an
  incident without a deploy.
- Prove it: in staging, block the vendor's hostname or inject latency with a fault proxy, then
  load the pages that use it. A page that hangs has an unbounded call somewhere.

## Vendors behind an interface

Wrap vendors whose replacement would otherwise touch the whole codebase: email, SMS, object
storage, LLM, search, analytics, payments.

- The interface speaks the product's language (`sendEmail({ to, template, data })`,
  `chargeOrder(order)`), not the vendor's request shapes.
- Exactly one module imports the vendor SDK. Enforce with the same lint rule that guards module
  boundaries.
- The adapter is where timeout, retry, breaker, metrics and error mapping live. Vendor errors
  become the application's own kinds (`architecture-shape.md`).
- Store vendor identifiers in explicit columns (`provider`, `provider_customer_id`), never as
  the primary key of a domain entity.
- The payoff is immediate, not hypothetical: a fake implementation for tests and local
  development, and one place to change when the vendor changes its API.
- Do not build the second implementation, a plugin system or a lowest-common-denominator
  abstraction in advance. Payment providers differ in semantics, not only in syntax: an adapter
  limits the blast radius of a switch, it does not make it free.
- Keep your own copy of the data that would be needed to leave: customer and subscription
  state, templates in the repository, files in storage you control. Confirm the vendor has an
  export before depending on it (`0x:engineering-leadership`, `build-vs-buy.md`).

## Pinning API versions

- Set the API version explicitly in the client or request header. Relying on the account's
  default version means a dashboard click, or a new account in another environment, changes
  production behavior.
- Webhook payloads have their own version setting at many vendors, separate from the request
  version. Pin both and upgrade them together.
- Pin the SDK to an exact version in the lockfile; an SDK major often implies a new API version.
- Read vendor responses tolerantly: validate the fields used, ignore unknown fields, and handle
  an unknown enum value as an explicit default branch. Strict schemas on someone else's payload
  turn their additive change into your outage.
- Route the vendor's deprecation and changelog email to an address that is read, and put sunset
  dates in the calendar.

Upgrade sequence:

1. Read the changelog between the pinned and target versions; list the breaking items that
   touch code in the adapter.
2. Upgrade in the vendor's sandbox or test mode. Run the adapter's integration tests there.
3. Replay recorded webhook fixtures of the new version through the handlers.
4. Ship behind a flag or to one environment first; watch the adapter's error metric.
5. Sandboxes differ from production in data, limits and timing. Finish with one small real
   transaction in production.

A scheduled smoke test against the sandbox (create, read, clean up) catches drift on the
vendor's side before customers do. Add it at Launch for the payment provider and any vendor on
the core flow.

## Respecting vendor rate limits

Learn the limit's shape first: per second or per minute, concurrent requests, a daily quota,
cost points per query, and whether it applies per API key or per connected customer account.

- All calls to one vendor go through one client so there is one place to limit.
- An in-process limiter is multiplied by the number of instances. Keep the token bucket in
  Redis, or run the calls through a queue whose limiter is global.
- Split interactive and bulk traffic. Bulk work (backfills, syncs, campaigns) goes through a
  queue limited to a fraction of the quota (half to two thirds as a rule of thumb), so a user's
  click never waits behind an import.
- When limits are per connected account, the bucket key is the account; one busy customer then
  cannot starve the others.
- Read the vendor's rate-limit headers and slow down before the limit, not after the 429.
- On a 429, pause the whole queue for that vendor or account until `Retry-After`. Retrying each
  job individually keeps hammering.
- A concurrency limit needs a semaphore; a rate limiter does not enforce it.
- Reduce calls before buying quota: batch endpoints, caching of reads, webhooks instead of
  polling, conditional requests where supported.

## Customers' OAuth tokens

Tokens for a customer's account at another service are credentials to their data.

- Encrypt access and refresh tokens at the application layer before storing, with a key held in
  a secret manager or KMS, not in the database (`0x:web-security`, `secrets.md`). Never log
  them, never send them to the browser.
- Store per connection: provider, external account ID, granted scopes, encrypted tokens,
  `expires_at`, status. Check the scopes actually granted: users can decline some.
- Request the minimum scopes, and request offline access explicitly where the provider requires
  it to issue a refresh token.
- Refresh before use when the token is within a few minutes of expiry. Do not wait for a 401.
- Refresh must be single-flight per connection. Many providers rotate the refresh token on use;
  two concurrent refreshes present the same old token, and the provider may treat the second as
  theft and revoke the grant. Take a short lease with a guarded update, and let losers wait and
  re-read:

```sql
UPDATE connections SET refreshing_until = now() + interval '30 seconds'
WHERE id = $1 AND (refreshing_until IS NULL OR refreshing_until < now())
RETURNING id;
```

- Persist the new refresh token as soon as the response arrives, before anything else can fail.
  A rotated token that was not saved is a lost connection.
- `invalid_grant` on refresh is permanent: the user revoked access, the token expired from
  disuse, or a password or policy change killed it. Mark the connection `needs_reauth`, stop its
  jobs, and ask the user to reconnect. Retrying does nothing.
- Some providers issue short-lived refresh tokens to apps that have not passed their review
  (Google expires them after about a week while the app is in testing status). Symptom: every
  connection breaks on the same schedule. Check the provider's rules before Launch.
- On disconnect or account deletion, revoke at the provider and delete the tokens.

## Load shedding and backpressure

Under overload, a server that accepts everything serves nothing: queues grow, every request
exceeds its client's timeout, and the work done is thrown away. Reject early and cheaply instead.

- Bound every queue: the HTTP server's in-flight requests, the pool's wait list, worker-thread
  queues, in-memory buffers. Unbounded means the bound is the memory limit.
- Cap in-flight requests per instance and answer `503` with `Retry-After` beyond the cap. A
  health signal such as event-loop delay or heap use can drive the same decision (for Fastify,
  `@fastify/under-pressure`).
- Keep the pool acquire timeout short, a second or two. A saturated database then produces fast
  errors instead of a pile of waiting requests.
- Drop work whose caller has gone: check the abort signal before starting expensive steps.
- Shed by priority. Health checks, sign-in, checkout and payment webhooks stay; bulk API
  clients, exports, crawlers and background refreshes go first.
- Degrade before rejecting where possible: smaller pages, no live suggestions, cached results.
- Streams: use `pipeline` and respect a `write()` that returns `false`. Ignoring it buffers the
  whole payload in memory for a slow client.
- Autoscaling reacts in minutes; shedding acts in milliseconds. Both are needed. Volumetric
  abuse is handled at the edge first (`0x:web-networking`, `cdn-edge.md`).

Check with a load test past capacity: successful throughput should flatten, not collapse, and
recover by itself when load drops (`0x:web-performance`, `load-testing.md`).

## Retry storms, budgets and hedging

A brief failure plus naive retries multiplies load exactly when the dependency is weakest, and
can keep it down after the original cause is gone.

- Retry budget: retries may add at most about 10% to a client's request volume. Implementation:
  a token bucket where each success adds 0.1 token and each retry spends one; no token, no
  retry.
- No retries through an open breaker, and none at more than one layer of a call chain.
- Your own clients are part of the storm. Browser and mobile code retries with backoff and
  jitter, honors `Retry-After`, and stops after a few attempts. A shipped app version with a
  tight retry loop cannot be recalled.
- After recovery, traffic returns at once: cold caches refill, clients reconnect, queues replay.
  Jitter reconnects, coalesce identical cache refills, and replay backlogs at a throttled rate.
- Hedging (sending a second copy of a slow request) is for idempotent reads only. Send the hedge
  after the dependency's p95 latency, cancel the loser, and cap hedges at a few percent of
  traffic. Never hedge a write. Skip hedging entirely unless a vendor's tail latency is a
  measured problem.

## Two-way sync with external systems

Avoid true bidirectional sync when a one-way sync plus a link to the other system satisfies the
customer. When both sides must edit, decide these before writing code:

- **Source of truth per field**, not per record: the CRM owns the deal owner, the product owns
  usage numbers. Most conflicts vanish with this rule.
- **A mapping table**: connection, local ID, remote ID, remote version or ETag, a hash of the
  last synced content, last synced time.
- **Inbound**: treat webhooks as hints and fetch the object; also poll incrementally with the
  provider's cursor or `updated_since`, overlapping the window, because webhooks get lost. Use
  the provider's sync token where one exists, and handle its "token expired, resync fully"
  answer.
- **Outbound**: outbox, then one rate-limited idempotent job per changed entity.
- **Echo suppression**: a local write produces a remote webhook, which looks like a remote
  change. Compare the incoming content with the last synced hash and stop when equal, or skip
  changes authored by the integration's own user. Timestamps do not solve this.
- **Conflicts**: compare both sides with the last synced state. Only one side changed: apply.
  Both changed the same field: the field's source of truth wins. Surface conflicts to the user
  only where data loss would matter, and keep the losing value in a log.
- **Deletes**: distinguish deleted from "no longer visible to this token". Archive locally
  rather than hard-delete on a missing remote record.
- **Initial import**: a resumable, paginated, rate-limited job with visible progress.
- **Per-record failures** go to a sync log the customer can see; one bad record never stops the
  batch.

Run a periodic full comparison as reconciliation (`consistency-concurrency.md`). When the
product needs many integrations of one category (CRMs, accounting, HR systems), a unified-API
vendor is a build-versus-buy decision worth raising before writing the third adapter.

## Ask the user

- **Which vendor outages may block the core flow, and which must not?** It sets the class of
  each dependency and where fallbacks are built. Assume only the database and sign-in may block.
- **When a safety check such as fraud screening is unavailable, proceed or refuse?** Fail-open
  loses money to fraud, fail-closed loses sales. Assume refuse for payouts and high-value
  actions, proceed with review for the rest.
- **What vendor plan and quota are paid for?** Limits decide queue rates and whether bulk work
  is feasible. Assume the lowest paid tier and check the vendor's current limits.
- **In a two-way sync, which system wins for each field?** It is the customer's business rule,
  not a technical choice. Assume the external system of record wins for the fields it
  originated.
- **How much lock-in is acceptable for each vendor?** It decides how much adapter and data
  export work is worth doing. Assume an adapter for email, storage and LLM; direct use for the
  payment provider behind one module.
