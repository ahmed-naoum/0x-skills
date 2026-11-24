# Third-party integrations and resilience

Read this when: calling an external API or another service, storing a customer's OAuth connection,
syncing data with an outside system, or when a slow or failing dependency turns into your own
outage. Webhooks and your own API's rate limits: `0x:api-design` (`webhooks.md`,
`idempotency-rate-limits.md`); LLM provider fallbacks: `0x:ai-features` (`cost-latency.md`).

## Timeouts on every outbound call

A call without a timeout waits as long as the other side likes. In a vendor brownout each waiting
request holds a socket, a database connection and memory, and the app stops answering with nothing
of its own broken: the most common way a third party takes a product down, and the cheapest to fix.

| Client | Default behavior | Set |
|---|---|---|
| `reqwest::Client` | No connect timeout and no total timeout | `connect_timeout` and `timeout` on the builder; one client per vendor, built once and cloned, since it holds the connection pool |
| Vendor crates (async-stripe, the AWS SDK) | Their own defaults, sometimes long, often with built-in retries | Timeout and retry settings explicitly at construction |
| SQLx and Postgres | Statements run unbounded; the pool waits 30 s for a connection | `statement_timeout` on the application role and a short `acquire_timeout` (`runtime-language.md`) |
| `redis` crate | Recent releases default to 1 s connect and 500 ms response timeouts on async connections; older ones had none | Set both explicitly; raise the response timeout for slow commands rather than removing it |

The request's deadline caps every attempt, and a retry budget caps retries across all callers:

```rust
use std::time::Duration;
use reqwest::{RequestBuilder, Response, StatusCode, header::RETRY_AFTER};
use tokio::time::{Instant, sleep_until, timeout_at};
use tower::retry::budget::{Budget, TpsBudget};

#[derive(Debug, thiserror::Error)]
pub enum CallError {
    #[error("deadline reached")] Deadline,
    #[error("vendor answered {0}")] Status(StatusCode),
    #[error(transparent)] Http(#[from] reqwest::Error),
}

/// Request path only. `build` must be idempotent or set the same idempotency key every time.
pub async fn call(build: impl Fn() -> RequestBuilder, budget: &TpsBudget, deadline: Instant) -> Result<Response, CallError> {
    budget.deposit();
    let mut attempt = 0;
    loop {
        attempt += 1;
        let sent = timeout_at(deadline, build().send()).await.map_err(|_| CallError::Deadline)?;
        let retryable = match &sent {
            Ok(r) => matches!(r.status().as_u16(), 408 | 429 | 500 | 502 | 503 | 504),
            Err(e) => e.is_connect() || e.is_timeout(),
        };
        if !retryable || attempt == 3 || !budget.withdraw() {
            let r = sent?;
            return if r.status().is_success() { Ok(r) } else { Err(CallError::Status(r.status())) };
        }
        let hint = sent.ok().and_then(|r| r.headers().get(RETRY_AFTER)?.to_str().ok()?.parse::<u64>().ok());
        let jitter = Duration::from_millis(200 << attempt).mul_f64(rand::random::<f64>());
        let at = Instant::now() + hint.map(Duration::from_secs).unwrap_or(jitter).min(Duration::from_secs(2));
        if at >= deadline { return Err(CallError::Deadline) }
        sleep_until(at).await;
    }
}
```

- Budget: 1-5 s for a call a user is waiting on, 10-30 s inside a job, from the dependency's
  observed p99 with margin and below the caller's remaining deadline. Streams (LLM output, large
  downloads) need an idle timeout between chunks instead: a client with `read_timeout`.
- A timeout on a write means the outcome is unknown, not failed. Retry with the same idempotency key
  or query the vendor; never tell the user "failed" and let them submit again without one.
- Record duration, outcome and vendor for every outbound call as a metric. Without it the first
  question in an incident ("is it them or us?") takes an hour.

## Retries and circuit breakers

| Response | Retry? |
|---|---|
| Connection error, timeout, 408, 429, 500, 502, 503, 504 | Yes, if the call is idempotent or carries an idempotency key |
| 400, 401, 403, 404, 409, 422, or a POST without an idempotency key | No: the same request gets the same answer, or a retry duplicates the effect |

On the request path, two or three attempts inside the deadline, as `call` does; in a job,
full-jitter backoff over hours (`background-jobs.md`). Honor `Retry-After` on 429 and 503, capped.
Retry at one layer: if the job retries, set the SDK's retries to zero, or three layers of three
attempts become twenty-seven calls.

A circuit breaker makes callers of a failing dependency fail in milliseconds and lets it recover:

- Closed: calls pass. Open: calls fail immediately for a cool-down (10-30 s). Half-open: one probe
  passes; success closes, failure reopens.
- Trip on failure rate over a rolling window with a minimum volume (a rule-of-thumb start: half of
  at least twenty calls in ten seconds, then tune from the metric). Count timeouts and 5xx, not 4xx.
  At low traffic it never collects enough samples: timeouts plus a fallback suffice.
- One breaker per dependency, and per endpoint or account where they fail independently. Per-process
  state is fine: each instance learns within seconds.
- Rust has no dominant breaker crate (`failsafe` exists; check its maintenance). The state machine
  is small enough to own in the vendor adapter: an atomic state, counts per window, a reopen time.
  Export its state as a metric and alert when one stays open.

## Degrading gracefully

Classify every dependency once, in a list kept in the repository:

| Class | Meaning | Examples | When it is down |
|---|---|---|---|
| Critical | The product cannot answer without it | Primary database, session validation | Fail fast with a clear error page; this is the outage to prevent by redundancy, not by fallback |
| Degradable | A feature is worse or missing | Search, recommendations, AI features, avatars, maps, analytics | Hide or disable the feature with a message, or fall back to a simpler path (database search) |
| Deferrable | The effect can happen later | Email, CRM sync, webhooks out, invoicing documents | Enqueue and confirm to the user; the job retries |

- Do not call a vendor on the request path to answer a question your own database could answer.
  Entitlements are the standard case: keep plan and access state locally, updated by webhooks and
  reconciliation, so a payment provider outage does not lock paying users out.
- Serve stale on error for read-mostly data (exchange rates, remote configuration, feature flag
  definitions): keep the last good value past its expiry and use it when refresh fails.
- Fail closed where the dependency is a safety control (fraud screening, sanctions checks,
  authorization). Decide this per dependency with the user; it is a business risk choice.
- Readiness checks must not include third parties, or a vendor outage marks every instance unready
  and the balancer takes the product offline; liveness checks nothing external
  (`0x:site-reliability`). Give each integration a kill switch (a flag) for incidents.
- Prove it: in staging, block the vendor's hostname or inject latency with a fault proxy, then load
  the pages that use it. A page that hangs has an unbounded call somewhere.

## Vendors behind an interface

Wrap vendors whose replacement would touch the whole codebase: email, SMS, object storage, LLM,
search, analytics, payments.

- The interface speaks the product's language (`send_email(Email { to, template, data })`,
  `charge_order(&order)`), not the vendor's request shapes; only the adapter depends on the vendor
  crate. The adapter holds timeout, retry, breaker, metrics and error mapping, and vendor errors
  become the application's own `thiserror` variants (`architecture-shape.md`).
- In Rust the interface is a trait whose methods return `impl Future<Output = ...> + Send`: a plain
  `async fn` in a trait promises no `Send` future, and Axum handlers and spawned jobs need one. Such
  a trait is not object-safe, so make the app state generic over it or use an enum of
  implementations; `Arc<dyn Trait>` needs boxed futures (the `async-trait` crate).
- Store vendor IDs in explicit columns (`provider`, `provider_customer_id`), never as a domain key.
- The payoff is immediate: a fake implementation for tests and local development, and one place to
  change when the vendor changes its API. Do not build the second implementation, a plugin system or
  a lowest-common-denominator abstraction in advance. Payment providers differ in semantics, not
  only syntax: an adapter limits the blast radius of a switch, not its cost.
- Keep your own copy of the data needed to leave: customer and subscription state, templates in the
  repository, files in storage you control. Confirm the vendor has an export before depending on it
  (`0x:engineering-leadership`, `build-vs-buy.md`).

## Pinning API versions

- Set the API version explicitly in the client or request header; relying on the account's default
  means a dashboard click, or a new account in another environment, changes production. Webhook
  payloads often have their own version setting: pin both and upgrade them together.
- Commit `Cargo.lock` and pin community vendor crates exactly (`=` in `Cargo.toml`). A crate
  generated from the vendor's API specification targets one API version (async-stripe does), so
  upgrading the crate upgrades the API.
- Read vendor responses tolerantly with serde: no `deny_unknown_fields`, `Option` or
  `#[serde(default)]` on fields that may vanish, and a `#[serde(other)]` catch-all variant on enums.
  Strict types on someone else's payload turn their additive change into your outage.

Upgrade: read the changelog between versions and list breaking items in the adapter; run its
integration tests in the vendor's sandbox; replay recorded webhook fixtures of the new version; ship
behind a flag or to one environment and watch the adapter's error metric; finish with one small real
production transaction, as sandboxes differ in data, limits and timing. A scheduled sandbox smoke
test (create, read, clean up) catches vendor-side drift: add it at Launch for payments and core-flow
vendors. Route deprecation email to a read inbox; calendar sunset dates.

## Respecting vendor rate limits

Learn the limit's shape first: per second or per minute, concurrent requests, a daily quota, cost
points per query, and whether it applies per API key or per connected customer account.

- All calls to one vendor go through one client, the one place to limit. An in-process limiter (the
  `governor` crate) is multiplied by the number of instances: keep the token bucket in Redis, or run
  the calls through a queue whose limiter is global.
- Split interactive and bulk traffic: bulk work (backfills, syncs, campaigns) goes through a queue
  limited to half or two thirds of the quota (rule of thumb), so clicks never wait on it.
- Per-account limits get a bucket per account, so one busy customer cannot starve the others.
- Read the vendor's rate-limit headers and slow down before the limit. On a 429, pause the whole
  queue for that vendor or account until `Retry-After`; retrying jobs one by one keeps hammering.
  Concurrency limits need a semaphore (`try_acquire` fails fast); a rate limiter does not enforce
  them.
- Reduce calls before buying quota: batch endpoints, cached reads, webhooks instead of polling,
  conditional requests where supported.

## Customers' OAuth tokens

- Encrypt access and refresh tokens before storing, with an AEAD such as AES-256-GCM (`aes-gcm`): a
  fresh random nonce per encryption stored beside the ciphertext (a repeated nonce under one key
  breaks GCM), a key from a secret manager or KMS rather than the database, and a key ID per row for
  rotation (`0x:web-security`, `secrets.md`).
- Hold tokens in `secrecy::SecretString`, so a derived `Debug` or a `tracing` field prints a
  redaction. Never log them, never send them to the browser.
- Store per connection: provider, external account ID, granted scopes (users can decline some),
  encrypted tokens, `expires_at`, status. Request the minimum scopes, and offline access explicitly
  where the provider requires it to issue a refresh token. Refresh before use when the token is
  within a few minutes of expiry; do not wait for a 401.
- Refresh must be single-flight per connection across instances, which a `tokio::sync::Mutex` is
  not. Many providers rotate the refresh token on use; two concurrent refreshes present the same old
  token, and the provider may treat the second as theft and revoke the grant. Take a short lease
  with a guarded update, and let losers wait and re-read:

```sql
UPDATE connections SET refreshing_until = now() + interval '30 seconds'
WHERE id = $1 AND (refreshing_until IS NULL OR refreshing_until < now())
RETURNING id;
```

- Persist a rotated refresh token as soon as the response arrives: an unsaved one is a lost link.
- `invalid_grant` on refresh is permanent (access revoked, token expired from disuse, a password or
  policy change): mark the connection `needs_reauth`, stop its jobs, ask the user to reconnect.
- Apps that have not passed a provider's review may get short-lived refresh tokens (Google: about a
  week in testing status), so every connection breaks on one schedule. Check before Launch.
- On disconnect or account deletion, revoke at the provider and delete the tokens.

## Load shedding and backpressure

Under overload, a server that accepts everything serves nothing: queues grow, every request exceeds
its client's timeout, and the work done is thrown away. Reject early and cheaply instead:

```rust
use axum::{BoxError, Router, error_handling::HandleErrorLayer, http::{StatusCode, header}, response::{IntoResponse, Response}};
use tower::{ServiceBuilder, limit::GlobalConcurrencyLimitLayer, load_shed::error::Overloaded};

async fn overloaded(err: BoxError) -> Response {
    if err.is::<Overloaded>() {
        return (StatusCode::SERVICE_UNAVAILABLE, [(header::RETRY_AFTER, "5")]).into_response();
    }
    tracing::error!(error = %err, "middleware failed");
    StatusCode::INTERNAL_SERVER_ERROR.into_response()
}

/// Past `max` requests in flight on this instance, answer 503 at once instead of queueing.
pub fn shed_load(app: Router, max: usize) -> Router {
    let limit = GlobalConcurrencyLimitLayer::new(max); // one limit shared by every route
    app.layer(ServiceBuilder::new().layer(HandleErrorLayer::new(overloaded)).load_shed().layer(limit))
}
```

- `Router::layer` wraps each route separately, and `ConcurrencyLimitLayer` makes a semaphore per
  wrapped service: a per-route limit. Routes added after `.layer` are outside it: add health checks
  afterwards, and give bulk routes (exports, bulk API clients, crawlers) a lower limit of their own,
  so they are shed while sign-in, checkout and payment webhooks stay.
- Bound every other queue too (pool wait list, channels, buffers: `runtime-language.md`), with a
  pool acquire timeout of about 3 s, lower when shedding, so a saturated database fails fast.
- A disconnect drops the handler, so its work stops at the next `.await`; work handed to
  `spawn_blocking` or a spawned task does not: check a `CancellationToken` or the deadline first.
- Streams: build the body with `Body::from_stream` from a bounded source, so a slow client slows the
  producer; a task pushing into an unbounded channel buffers the whole payload in memory.
- Degrade before rejecting (smaller pages, no live suggestions, cached results). Autoscaling takes
  minutes, shedding milliseconds; volumetric abuse stops at the edge (`0x:web-networking`).

Check with a load test past capacity: successful throughput should flatten, not collapse, and
recover by itself when load drops (`0x:web-performance`, `load-testing.md`).

## Retry storms, budgets and hedging

A brief failure plus naive retries multiplies load exactly when the dependency is weakest.

- Retry budget: retries may add at most about 10% to a client's request volume. Each request
  deposits a fraction of a token, each retry withdraws one; no token, no retry. tower's `TpsBudget`
  implements it and works outside tower too, as in `call` above:
  `TpsBudget::new(Duration::from_secs(10), 10, 0.1)` allows 10% plus a floor of 10 per second.
- No retries through an open breaker, and none at more than one layer of a call chain.
- Your own clients are part of the storm. Browser (Leptos) and mobile code retries with backoff and
  jitter, honors `Retry-After` and stops after a few attempts; a shipped app cannot be recalled.
- After recovery traffic returns at once: jitter reconnects, coalesce identical cache refills
  (moka's `get_with` runs one loader per key), and replay backlogs at a throttled rate.
- Hedging (a second copy of a slow request) is for idempotent reads only: send it after the
  dependency's p95, cancel the loser (dropping its future does), cap hedges at a few percent of
  traffic, and skip it unless a vendor's tail latency is a measured problem. Never hedge a write.

## Two-way sync with external systems

Avoid true bidirectional sync when a one-way sync plus a link to the other system satisfies the
customer. When both sides must edit, decide these before writing code:

- **Source of truth per field**, not per record: the CRM owns the deal owner, the product owns usage
  numbers. Most conflicts vanish with this rule.
- **A mapping table**: connection, local ID, remote ID, remote version or ETag, a hash of the last
  synced content, last synced time.
- **Inbound**: treat webhooks as hints and fetch the object; also poll incrementally with the
  provider's cursor or `updated_since`, overlapping the window, because webhooks get lost. Use the
  provider's sync token where one exists, and handle its "expired, resync fully" answer.
- **Outbound**: outbox, then one rate-limited idempotent job per changed entity.
- **Echo suppression**: a local write comes back as a remote webhook. Compare the incoming content
  with the last synced hash and stop when equal, or skip changes authored by the integration's own
  user. Timestamps do not solve this.
- **Conflicts**: compare both sides with the last synced state. One side changed: apply. Both
  changed a field: its source of truth wins. Surface conflicts only where data loss would matter,
  and keep the losing value in a log.
- **Deletes**: distinguish deleted from "no longer visible to this token"; archive locally rather
  than hard-delete on a missing remote record.
- **Initial import** is a resumable, paginated, rate-limited job with visible progress; **per-record
  failures** go to a sync log the customer can see, and never stop the batch.

Run a periodic full comparison as reconciliation (`consistency-concurrency.md`). Before a third
adapter of one category (CRMs, accounting, HR), weigh a unified-API vendor: build versus buy.

## Ask the user

- **Which vendor outages may block the core flow, and which must not?** It sets each dependency's
  class and where fallbacks are built. Assume only the database and sign-in may block.
- **When a safety check (fraud screening) is down, proceed or refuse?** Fail-open loses money to
  fraud, fail-closed loses sales. Assume refuse for payouts and high-value actions, review the rest.
- **What vendor plan and quota are paid for?** Limits decide queue rates and whether bulk work is
  feasible. Assume the lowest paid tier and check the vendor's current limits.
- **In a two-way sync, which system wins for each field?** It is the customer's business rule.
  Assume the external system of record wins for the fields it originated.
- **How much lock-in is acceptable for each vendor?** It decides how much adapter and export work is
  worth doing. Assume adapters for email, storage and LLM; the payment provider behind one module.
