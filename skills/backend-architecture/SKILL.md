---
name: backend-architecture
description: "Structures a product's Rust server side: the Tokio runtime, workspace layout, service boundaries, cross-system consistency, multi-tenancy, jobs, realtime, uploads and resilient integrations. Use when laying out an Axum backend, fixing stalls or dying tasks, moving work to a queue, fixing duplicate or stuck jobs, isolating tenants, adding live updates or uploads, or when a slow third-party API takes the app down."
---

# Backend architecture and server-side patterns

## Stance

A small team's backend is one Cargo workspace, one Postgres and one binary run as `serve` and
`worker` for far longer than fashion suggests. The expert's work is not adding components; it is
making the few that exist correct under retries, concurrency, restarts and other people's
outages. Follow what the project already uses before applying any default below.

- **One deployable until a measured reason says otherwise.** A function call and a single
  database transaction are the two things a split takes away, and sagas, contracts and extra
  pipelines are what it gives back.
- **The runtime is shared.** Tokio switches tasks only at `.await`: CPU work and blocking calls
  go to `spawn_blocking`, no lock guard lives across an `.await`, and every long-lived task is
  supervised, or one request stalls the rest and failures vanish without a trace.
- **The database enforces invariants.** A check in application code is a read followed by a
  write, and another request fits between them. Constraints and guarded updates close the gap.
- **Everything runs at least twice.** Requests are retried, jobs redelivered, webhooks
  duplicated, deploys kill work midway. Every handler with a side effect is idempotent by a key
  derived from the business entity.
- **Never write to two systems and assume both succeed.** Commit an intent or an outbox row in
  the transaction, then let a retried job perform the second effect.
- **Every wait and every queue is bounded.** Timeouts on outbound calls, limits on channels,
  spawns, pools and connections, deadlines passed down. An unbounded wait is how a vendor's
  incident becomes yours; an unbounded queue is how a slow consumer becomes an OOM kill.
- **Process memory and local disk are disposable.** A deploy is already a second instance:
  sessions, schedules, locks, uploads and queues live in shared stores.
- **Tenant scope is structural.** The tenant comes from the verified membership and is applied
  by the data layer, cache keys, jobs and file paths, not remembered per query.
- **Derived state is an optimization, and it drifts.** Every screen is correct after a plain
  reload, every cache or index can be rebuilt from the database, and a reconciliation job finds
  what an eventual path lost before a customer does.

## Route

| If the task is | Read |
|---|---|
| One slow request freezes the others, spawned tasks leak or die silently, dropped requests on deploy or SIGTERM, memory growth or OOM kills, sizing Tokio threads and pools, Cargo workspace layout, slow compile times, whether another language is justified | `references/runtime-language.md` |
| Laying out a new backend, monolith versus services, one Axum binary for UI and API or a separate API service, module boundaries, where business logic and error types go (thiserror, anyhow, `IntoResponse`), stateless scaling, introducing events, event sourcing or CQRS | `references/architecture-shape.md` |
| A flow that touches the database plus a payment provider, queue, index or email; double submits and races; status fields; outbox; sagas; distributed locks; stale reads after a write; reconciliation | `references/consistency-concurrency.md` |
| Making the app multi-tenant, organizations and memberships, row-level security, cross-tenant leak tests, per-customer settings, noisy tenants, customer domains, data residency, a dedicated database for one customer | `references/multi-tenancy.md` |
| Moving slow work out of the request, cron and scheduled jobs, retries and dead letters, jobs running twice, stuck or piling up, queue choice, long multi-step workflows, replaying failed jobs | `references/background-jobs.md` |
| Live updates, notifications, progress, chat, presence, typing, cursors, collaborative editing, offline sync, WebSockets across instances, audio or video calls | `references/realtime.md` |
| Uploads, presigned URLs, large or resumable uploads, serving user files safely, image and video processing, CSV import and export, PDF generation, malware scanning | `references/file-uploads.md` |
| Calling an external API, timeouts, retries, circuit breakers, a vendor outage or rate limit hurting the app, vendor lock-in, API version upgrades, storing customers' OAuth tokens, overload and load shedding, two-way sync | `references/integrations-resilience.md` |

## Defaults at a glance

| Decision | Prototype | Launch | Scale |
|---|---|---|---|
| Language and runtime | Rust stable on Tokio, pinned toolchain, one crate | Cargo workspace: `domain`, `data`, `app`, `web`, `server` crates | Second language only as a service for one capability |
| Shape | One binary, modules by feature | Modular monolith: private submodules behind re-exported interfaces, one binary run as `serve` and `worker` | Extract a service only for a different resource profile, runtime, fault or compliance boundary |
| API surface | One Axum binary serving Leptos and JSON routes | Same; a versioned `/api/v1` router when a second client needs a contract | A separate API binary in the same workspace when it must deploy or scale alone |
| Errors | `thiserror` enums, one `IntoResponse` mapping | Same; expected failures as stable codes, internal text never sent | Same |
| CPU-heavy work | `spawn_blocking` | Same, under a semaphore sized near the core count | Separate worker or service for heavy media |
| Jobs | None, or a hosted queue calling HTTP endpoints | Postgres jobs table claimed with `FOR UPDATE SKIP LOCKED` (or apalis), enqueued in the business transaction, queues by latency class | Redis-backed or managed queue when measured; durable execution for long workflows |
| Schedules | Platform cron | One trigger, deterministic job key per period, heartbeat monitor | Same |
| Cross-system writes | Intent row plus idempotency key for money | Outbox or transactional enqueue; reconciliation for money | Reconciliation per integration; CDC relay if needed |
| Tenancy | `org_id` on every row, memberships table | Tenant transaction handle plus row-level security, isolation tests in CI | Per-tenant quotas and fair queues; dedicated database for the few who pay for it |
| Realtime | Polling | SSE down, POST up; hosted service on serverless | Own WebSocket tier with a pub/sub backplane when volume justifies it |
| Uploads | Direct to storage, presigned | Content verification, separate user-content origin, processing in jobs | Multipart, malware quarantine where customers require it |
| Outbound calls | `reqwest` client with connect and total timeouts | One retry layer, vendor adapters behind traits, degradation classes | Breakers, concurrency caps, retry budgets, load shedding |
| Shutdown | Exec-form entrypoint, Tokio SIGTERM handler | Readiness fail, drain, cancel workers by token, bounded wait, close pool; verified under load | Same, including long-lived connections |

Numbers to start from, all rules of thumb to confirm by measurement: 10-100 microseconds between
`.await` points; runtime lag p99 under 10 ms; database pool 10 per process (SQLx's default)
within the server's connection budget, acquire timeout about 3 s; outbound timeout 1-5 s on the
request path and 10-30 s in jobs; job retries with full jitter spanning hours; alert on the age
of the oldest ready job, not on depth.

## Before you call it done

1. Every outbound call (HTTP, SDK, database, Redis) has an explicit timeout shorter than its
   caller's deadline; grep for `Client::new()` and builders without `.timeout(`: reqwest has none.
2. No CPU work or blocking IO runs on async workers: hashing, media, PDFs and large parsing go
   through `spawn_blocking` under a semaphore, and runtime lag is exported as a metric.
3. No `std::sync::Mutex` guard or `dashmap` reference lives across an `.await`; no channel is
   unbounded; no `tokio::spawn` runs per item without a permit; no `unwrap()` sits in a request
   path (clippy `unwrap_used` denied in the `app` and `web` crates).
4. Every long-lived task is in a `JoinSet` owned by `main`, and SIGTERM drains it: a deploy under
   load produces zero non-2xx responses and no lost or duplicated jobs.
5. Every handler with a side effect can run twice with the same input and change nothing the
   second time; a test calls it twice.
6. No code path writes to the database and to another system as two unlinked steps, and no
   transaction stays open across a network call (an `.await` on `reqwest` between `begin` and
   `commit`).
7. Status changes are guarded updates (`WHERE status = ...`), and the zero-rows case is handled.
8. Nothing that must survive a restart lives in process memory or on local disk; two instances
   behind a round-robin proxy behave like one.
9. Each job type has a timeout shorter than its lease, a maximum attempt count, a dead-letter
   destination someone is alerted about, and ID arguments deserialized and validated at entry;
   scheduled work is triggered once, catches up from a watermark and has a heartbeat alert.
10. Tenant-owned tables carry `org_id`; cache keys, job arguments, storage keys and channels are
    tenant-scoped; a test fetches, updates and lists another tenant's data and fails.
11. Realtime clients recover from a dropped connection without losing or duplicating events,
    each subscription is authorized on the server, and per-connection buffers are bounded.
12. Uploads are size-limited by the signature or measured in storage and deleted when over,
    verified by content, and served from a separate origin with `nosniff` and a restrictive
    disposition; an oversized test upload fails.
13. With each third-party hostname blocked in staging, core pages still load and deferred work
    is queued, not lost.
14. Use cases are callable without HTTP; routes, jobs and CLI are thin adapters, and one
    `IntoResponse` mapping turns errors into status codes without leaking internal text.
15. Queue age, runtime lag, pool wait time, outbound call latency per vendor and reconciliation
    findings are exported as metrics with alerts.

## Not this skill

- Endpoint contracts, pagination, API rate limits and generic webhooks → `0x:api-design`
- Schema design, transactions, locks and query tuning → `0x:postgres-database`
- Choosing and running Redis, search, object storage or streams → `0x:data-stores`
- Roles, permissions and per-object access checks → `0x:auth-identity`
- Sending email, SMS and push notifications → `0x:email-notifications`
- Profiling slow endpoints and load testing → `0x:web-performance`
