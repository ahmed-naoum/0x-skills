# Monolith, modules, services and events

Read this when: laying out a new backend, choosing between one Axum binary for UI and API and a
separate API service, drawing module boundaries, placing error handling, or deciding whether to
extract a service, introduce events, or adopt event sourcing.

## The shape by stage

| Stage | Shape | Processes |
|---|---|---|
| Prototype | One crate, one binary, one Postgres. Modules by feature, no enforced boundaries yet | `serve` |
| Launch | Modular monolith in a Cargo workspace (`runtime-language.md`): capability modules with re-exported interfaces, one binary with a `worker` subcommand | `serve`, `worker` |
| Scale | Same monolith; extract a service only for a reason in the extraction table below | `serve`, `worker`, plus the few extracted services |

A monolith keeps the two things a small team cannot afford to lose: a function call instead of a
network call, and one database transaction across the whole use case. The first "second service"
is almost always the worker process, which is the same binary with a different subcommand and
not a service boundary at all.

## One Axum binary or a separate API service

One Axum binary serves the Leptos app (server rendering, hydration, server functions) and the JSON
API while all of these hold: one web client, request-response work that finishes in seconds, and
background work that fits the worker process.

| Signal | Add |
|---|---|
| Work outlives the request or must be retried | The worker subcommand, not an API service |
| The web tier runs on serverless functions, where long-lived connections end at the duration limit | A long-running realtime service, or a hosted realtime provider |
| A second client (mobile app, public API, partner) needs a stable, versioned contract | A versioned `/api/v1` router with its own tests and an OpenAPI document, in the same binary first |
| UI builds (cargo-leptos, WASM) slow API deploys, or the API must scale on its own | A second binary crate for the API in the same workspace, on the same `app` crate |
| A workload that needs another language | A service in that language (`runtime-language.md`) |

Rules that hold either way:

- Leptos server functions are public HTTP endpoints. The `#[server]` macro adds no
  authentication: each one validates input and authorizes the caller as a hand-written route does.
- A server function's error travels to the browser as written. Return expected failures as a
  typed error with a stable code; never wrap internal error text (`e.to_string()`) into it.
- The API for a mobile app cannot change in lockstep with a web deploy: old app versions live
  for months. That alone justifies an explicit, versioned contract (`0x:api-design`).
- A separate API service lives in the same workspace and depends on the same crates. Splitting
  the repository is a separate, later decision.

## Layout and module boundaries

Draw modules around business capabilities (billing, projects, notifications, identity), not
technical layers (`handlers/`, `services/`, `models/`). A capability changes for one business
reason; a layer changes for every reason. The workspace's crates separate dependency weight
(pure domain, SQL, HTTP); inside them, modules follow capabilities.

```text
crates/app/src/
  lib.rs            pub mod billing; pub mod projects;
  billing/
    mod.rs          the interface: pub use of the use cases and types others may call
    service.rs      use cases (mod service; private to billing)
    repo.rs         queries on tables billing owns (or crates/data/src/billing.rs)
    events.rs       events billing publishes
  projects/
crates/web/         routes: parse, authenticate, call a use case, map the result
crates/server/      main: serve | worker | migrate
```

- Declare submodules private (`mod repo;`) and re-export the interface from `billing/mod.rs`.
  Rust's privacy rules then reject `crate::billing::repo::...` from another module at compile
  time; no lint is needed.
- Modules inside one crate may use each other in a cycle; crates may not. When the direction
  between two capabilities matters, make one a crate and Cargo enforces it.
- Each table has one owning module, and only the owner writes it. Others read through the owner's
  functions. Foreign keys across modules stay: referential integrity is worth more than
  theoretical extractability.
- Use cases take `&mut PgConnection`, so a caller passes `&mut *tx` and one operation spanning two
  modules stays atomic. Do not give this up to make modules look like services.
- At Prototype keep only the module-per-feature habit; tighten visibility at Launch, when the
  first module has a second consumer.

## Business logic outside transport

A use case is a plain async function: `create_invoice(ctx, conn, input)`. `ctx` carries the
actor, the tenant, the deadline and the request ID. It knows nothing of HTTP, cookies, headers,
queue messages or command-line arguments.

| Adapter | Does | Does not |
|---|---|---|
| Axum handler, Leptos server function | Parse and validate, authenticate, build `ctx`, call the use case, map the result | Query the database, hold business rules |
| Job handler | Deserialize and validate arguments, rebuild `ctx` (including tenant), call the use case, classify errors as retryable or not | Duplicate logic that the API also runs |
| CLI subcommand, backfill, webhook receiver | Same pattern | Bypass the use case "because it is internal" |

Authorization that depends on the resource belongs inside the use case, so jobs, CLI and a future
API cannot skip it (`0x:auth-identity`, `authorization.md`). The test of the split: the use case
runs in a `#[sqlx::test]` with no HTTP in sight, and a new entry point needs a new adapter and
nothing else.

## Errors by kind

| Kind | Examples | In code | To the client | Telemetry |
|---|---|---|---|---|
| Expected failure | Validation, not found, conflict, forbidden, quota reached, card declined | A `thiserror` variant with a stable code | 4xx with the code and an actionable message | Count as a metric; not an error-tracker event |
| Dependency failure | Timeout, upstream 5xx, connection refused | A variant holding the cause in `#[source]`, marked retryable | 502, 503 or 504 with "try again"; retry where safe | Error tracker with a rate alert, not per event |
| Bug | Broken invariant, impossible state, a panic | Do not match it away; let it reach the boundary | 500 with a generic message and the request ID | Error tracker, every one |

`thiserror` enums in `domain` and `app`, `anyhow` only in `main`, scripts and CLI. One
`IntoResponse` implementation maps every error to a status and code:

```rust
use axum::{Json, http::StatusCode, response::{IntoResponse, Response}};
use serde_json::json;

#[derive(Debug, thiserror::Error)]
pub enum BillingError {
    #[error("plan limit reached")]
    PlanLimit,
    #[error("invoice not found")]
    NotFound,
    #[error("database")]
    Db(#[from] sqlx::Error),
}

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("invalid input")]
    Invalid(#[from] garde::Report),
    #[error(transparent)]
    Billing(#[from] BillingError),
    #[error("database")]
    Db(#[from] sqlx::Error),
    #[error("{vendor} unavailable")]
    Upstream { vendor: &'static str, #[source] source: reqwest::Error },
}

fn unique_violation(e: &sqlx::Error) -> bool {
    matches!(e, sqlx::Error::Database(db) if db.is_unique_violation())
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, code) = match &self {
            AppError::Invalid(_) => (StatusCode::UNPROCESSABLE_ENTITY, "invalid_input"),
            AppError::Billing(BillingError::PlanLimit) => (StatusCode::CONFLICT, "plan_limit_reached"),
            AppError::Billing(BillingError::NotFound) => (StatusCode::NOT_FOUND, "not_found"),
            AppError::Upstream { .. } => (StatusCode::SERVICE_UNAVAILABLE, "upstream_unavailable"),
            AppError::Db(e) | AppError::Billing(BillingError::Db(e)) if unique_violation(e) => {
                (StatusCode::CONFLICT, "already_exists")
            }
            AppError::Db(_) | AppError::Billing(BillingError::Db(_)) => {
                (StatusCode::INTERNAL_SERVER_ERROR, "internal")
            }
        };
        if status.is_server_error() {
            tracing::error!(error = ?self, "request failed"); // full chain to logs, never to the body
        }
        (status, Json(json!({ "code": code }))).into_response()
    }
}
```

- `#[from] sqlx::Error` alone makes every database error a 500, including unique violations that
  are expected conflicts. Match the cases that mean something, as above.
- `?` in the middle of business code propagates; add context with a variant that keeps the cause
  in `#[source]`, not by formatting it into a string.
- Error codes are stable strings (`plan_limit_reached`); clients branch on the code, never on the
  message. The response shape is owned by `0x:api-design` (`requests-responses.md`).
- Nothing internal reaches the client: no `Display` of an `sqlx::Error`, `anyhow` chain or
  upstream body. An `impl From<anyhow::Error> for AppError` that keeps the message is how it leaks.
- Panics are bugs: `runtime-language.md` covers catching them at the boundary.
- An error matched and discarded (`let _ = ...`, `.ok()`) needs a comment saying why losing it is
  correct.

## Stateless servers and horizontal scale

Anything held in process memory or on local disk breaks when a second instance starts, or when
the first restarts. Find it before scaling:

| In-process state | Breaks as | Move to |
|---|---|---|
| tower-sessions `MemoryStore` | Users logged out at random | A Postgres or Redis session store (`0x:auth-identity`) |
| Rate-limit counters (tower_governor, a `DashMap`) | Limit multiplied by instance count | Redis or the database |
| A `moka` or `HashMap` cache used as truth | Instances disagree | Database as truth, cache with TTL |
| Uploads on local disk | File missing on the other instance, gone after deploy | Object storage (`file-uploads.md`) |
| A spawned loop on `tokio::time::interval` as cron | Job runs once per instance | Scheduler with a dedupe key (`background-jobs.md`) |
| An `mpsc` channel or detached spawn as a job queue | Work lost on restart | Durable queue |
| WebSocket rooms in a `HashMap` of senders | Messages reach only one instance's clients | Pub/sub backplane (`realtime.md`) |
| A `Mutex` as cross-request exclusion | No exclusion across instances | Database constraint or lock (`consistency-concurrency.md`) |

Check by running two instances behind a round-robin proxy locally and killing one mid-session.
Avoid sticky sessions as a fix: they hide the state and fail on every deploy. Do this work at
Launch even with one instance, because a deploy already behaves like a second instance.

## Events between modules

Start in-process. An event is a fact in the past tense (`invoice.paid`) carrying IDs, a schema
version and `occurred_at`; the publisher does not know who listens.

| Use | Mechanism |
|---|---|
| The caller needs the result or must fail if the reaction fails | A function call on the other module's interface, not an event |
| The reaction must commit atomically with the change | A function taking the same `&mut PgConnection`, inside the transaction |
| The reaction can lag (email, search index, analytics, webhooks out) | Outbox row or job enqueued in the same transaction, handled by the worker (`consistency-concurrency.md`) |

A `tokio::sync::broadcast` bus is not a third option: it drops events for slow receivers and loses
everything on restart. Use it only for hints such as cache invalidation and live updates.

Signs of a distributed monolith, in a monolith or across services:

- Two services must be deployed together, or share a database.
- One user request passes through a chain of synchronous calls, so availability multiplies down.
- An "event" is a command in disguise (`send_welcome_email_requested`) and the publisher waits
  for a reply event.
- A shared crate of domain types forces every consumer to upgrade in lockstep.
- Nobody can say what happens after `order.created` without searching the codebase. Keep a
  registry file listing each event, its schema and its subscribers.

Event schemas change additively only; a breaking change is a new event name. Carry a correlation
ID from the originating request through every event and job (a `tracing` span field), or tracing
a failure becomes archaeology.

## Extracting a service

Extract only for a reason from the left column.

| Real reasons | Not reasons |
|---|---|
| Different resource profile: GPU, CPU-bound, memory-hungry, many long-lived connections | "Microservices scale better" |
| Needs another runtime or language | The module is large |
| Fault isolation: a crash-prone renderer, execution of untrusted code | Cleaner architecture |
| Security or compliance boundary: shrink audit scope, isolate secrets | Anticipated team growth |
| Deploy contention between real teams (Scale) | A rewrite someone wants to do |

What extraction costs, permanently: no shared transaction (sagas and reconciliation instead),
timeouts and retries on every call, a versioned contract, a separate pipeline and dashboard, and
a slower local setup.

Sequence:

1. Make the boundary real inside the monolith first: interface only, own tables, no foreign
   joins. If this is hard, extraction would have been worse.
2. Write the contract (OpenAPI, protobuf or JSON Schema), version it, and add contract tests on
   both sides (`0x:code-quality`, `e2e-contract-visual.md`).
3. Move data ownership. The service owns its tables in its own database or schema; nobody else
   connects to them.
4. Route calls through the module's existing interface behind a flag. Shadow or dual-run, compare
   results, then switch.
5. Name the owner: who is paged, where the runbook, dashboard and SLO live. For a solo founder
   the owner is always the same person, which is the strongest argument against extracting.

## Event sourcing and CQRS

Default: do neither. Reach for the cheaper tool that meets the actual requirement.

| Requirement | Cheaper tool |
|---|---|
| Audit trail: who changed what, when | Append-only audit table written in the same transaction |
| Money must add up | Double-entry ledger (`0x:payments-billing`, `ledger-reconciliation.md`) |
| Reads are slow or too many | Indexes, read replicas, materialized views, then a denormalized read table fed from the outbox |
| "What did this look like last month?" | Versioned rows with validity ranges, or a history table |
| Undo | Soft delete plus the audit table |

A denormalized read table updated asynchronously is CQRS at the scale that pays off: one write
model, one or two projections, eventual by seconds. Full event sourcing is justified only when
the history is the product (a ledger, a legally required audit record, an operation log for
collaborative documents). Its costs are permanent: every past event schema must stay readable
(upcasting, so serde types for old versions stay in the code), projections lag and need rebuild
tooling, current state is not queryable with ad hoc SQL, and erasure requests collide with an
immutable log (the usual answer is per-subject encryption keys that can be destroyed). If it is
adopted, confine it to the one module that needs it.

## Ask the user

- **Will there be a mobile app, public API or partner integration within a year?** It decides
  whether the API needs a stable versioned contract now. Assume web only, and keep use cases
  transport-free so the answer can change cheaply.
- **Where is this hosted, and does the host allow long-running processes?** Serverless-only
  hosting pushes jobs and realtime to hosted services. Assume a container PaaS running `serve`
  and `worker`.
- **Is there a contractual or regulatory need for a full audit history of some data?** Only that
  justifies event sourcing in one module. Assume an audit table is enough.
- **Is any part expected to need very different resources (GPU, heavy media, untrusted code)?**
  That part is the first extraction candidate. Assume none.
- **How many people will deploy this in the next year?** Under about five, module boundaries
  solve coordination; services do not. Assume one.
