---
name: backend-architecture
description: "Structures the server side of a product: runtime choice, monolith and service boundaries, cross-system consistency, multi-tenancy, background jobs, realtime, file uploads and resilient integrations. Use when laying out a backend, choosing a runtime, moving work to a queue, fixing duplicate or stuck jobs, isolating tenants, adding live updates or uploads, or when a slow third-party API takes the app down."
---

# Backend architecture and server-side patterns

## Stance

A small team's backend is one codebase, one Postgres and two process types (`web`, `worker`) for
far longer than fashion suggests. The expert's work is not adding components; it is making the
few that exist correct under retries, concurrency, restarts and other people's outages. Follow
what the project already uses before applying any default below.

- **One deployable until a measured reason says otherwise.** A function call and a single
  database transaction are the two things a split takes away, and sagas, contracts and extra
  pipelines are what it gives back.
- **The database enforces invariants.** A check in application code is a read followed by a
  write, and another request fits between them. Constraints and guarded updates close the gap.
- **Everything runs at least twice.** Requests are retried, jobs redelivered, webhooks
  duplicated, deploys kill work midway. Every handler with a side effect is idempotent by a key
  derived from the business entity.
- **Never write to two systems and assume both succeed.** Commit an intent or an outbox row in
  the transaction, then let a retried job perform the second effect.
- **Every wait is bounded.** Timeouts on outbound calls, limits on queues, pools and
  connections, deadlines passed down. An unbounded wait is how a vendor's incident becomes yours.
- **Process memory and local disk are disposable.** A deploy is already a second instance:
  sessions, schedules, locks, uploads and queues live in shared stores.
- **Tenant scope is structural.** The tenant comes from the verified membership and is applied
  by the data layer, cache keys, jobs and file paths, not remembered per query.
- **The live channel and the cache are optimizations.** Every screen is correct after a plain
  reload, and every derived store can be rebuilt from the database.
- **Reconcile what cannot be made atomic.** Anything eventual drifts; a job that compares both
  sides finds it before a customer does.

## Route

| If the task is | Read |
|---|---|
| Picking a backend language or JavaScript runtime, running TypeScript directly, a request that freezes all others, memory kills, GC pauses, dropped requests on deploy or SIGTERM, sizing workers and pools | `references/runtime-language.md` |
| Laying out a new backend, monolith versus services, Next.js server versus a separate API, module boundaries, where business logic and error handling go, stateless scaling, introducing events, event sourcing or CQRS | `references/architecture-shape.md` |
| A flow that touches the database plus a payment provider, queue, index or email; double submits and races; status fields; outbox; sagas; distributed locks; stale reads after a write; reconciliation | `references/consistency-concurrency.md` |
| Making the app multi-tenant, organizations and memberships, row-level security, cross-tenant leak tests, per-customer settings, noisy tenants, customer domains, data residency, a dedicated database for one customer | `references/multi-tenancy.md` |
| Moving slow work out of the request, cron and scheduled jobs, retries and dead letters, jobs running twice, stuck or piling up, queue choice, long multi-step workflows, replaying failed jobs | `references/background-jobs.md` |
| Live updates, notifications, progress, chat, presence, typing, cursors, collaborative editing, offline sync, WebSockets across instances, audio or video calls | `references/realtime.md` |
| Uploads, presigned URLs, large or resumable uploads, serving user files safely, image and video processing, CSV import and export, PDF generation, malware scanning | `references/file-uploads.md` |
| Calling an external API, timeouts, retries, circuit breakers, a vendor outage or rate limit hurting the app, vendor lock-in, API version upgrades, storing customers' OAuth tokens, overload, two-way sync | `references/integrations-resilience.md` |

## Defaults at a glance

| Decision | Prototype | Launch | Scale |
|---|---|---|---|
| Language and runtime | TypeScript on a Node.js LTS line, pinned | Same | Second language only as a service for one capability |
| Shape | One deployable, folders by feature | Modular monolith, lint-enforced module interfaces, `web` + `worker` | Extract a service only for a different resource profile, runtime, fault or compliance boundary |
| API surface | The meta-framework's server | Same; separate API service when a second client needs a versioned contract | Same |
| Jobs | Hosted job service or none | Postgres-backed queue, enqueue in the business transaction, queues by latency class | Redis-backed or managed queue when measured; durable execution for long workflows |
| Schedules | Platform cron | One trigger, deterministic job key per period, heartbeat monitor | Same |
| Cross-system writes | Intent row plus idempotency key for money | Outbox or transactional enqueue; reconciliation for money | Reconciliation per integration; CDC relay if needed |
| Tenancy | `org_id` on every row, memberships table | Scoped data layer plus row-level security, isolation tests in CI | Per-tenant quotas and fair queues; dedicated database for the few who pay for it |
| Realtime | Polling | SSE down, POST up; hosted service on serverless | Own WebSocket tier with a pub/sub backplane when volume justifies it |
| Uploads | Direct to storage, presigned | Content verification, separate user-content origin, processing in jobs | Multipart, malware quarantine where customers require it |
| Outbound calls | Timeout on each | Timeouts, one retry layer, vendor adapters, degradation classes | Breakers, concurrency caps, retry budgets, load shedding |
| Shutdown | Exec-form start command | Readiness fail, drain, finish, close, exit; verified under load | Same, including long-lived connections |

Numbers to start from, all rules of thumb to confirm by measurement: p99 event-loop delay under
50 ms; V8 heap limit at 70-75% of container memory; 5-10 database connections per Node process
within the server's connection budget; outbound timeout 1-5 s on the request path and 10-30 s
in jobs; job retries with full jitter spanning hours; alert on the age of the oldest ready job,
not on depth.

## Before you call it done

1. Every outbound call (HTTP, SDK, database, Redis) has an explicit timeout shorter than its
   caller's deadline; grep for `fetch(` without a signal.
2. Every handler with a side effect can run twice with the same input and change nothing the
   second time; a test calls it twice.
3. No code path writes to the database and to another system as two unlinked steps; there is an
   intent row, outbox row or transactional enqueue.
4. No database transaction stays open across a network call to another system.
5. Status changes are guarded updates (`WHERE status = ...`), and the zero-rows case is handled.
6. Nothing that must survive a restart lives in process memory or on local disk; two instances
   behind a round-robin proxy behave like one.
7. SIGTERM reaches the process (exec-form command), and a deploy under load produces zero
   non-2xx responses and no lost or duplicated jobs.
8. Each job type has a timeout, a maximum attempt count, a dead-letter destination someone is
   alerted about, and arguments that are IDs validated at handler entry.
9. Scheduled work is triggered once across instances, catches up from a watermark, and has a
   heartbeat alert for "did not run".
10. Tenant-owned tables carry `org_id`; cache keys, job arguments, storage keys and channels are
    tenant-scoped; a test fetches, updates and lists another tenant's data and fails.
11. Realtime clients recover from a dropped connection without losing or duplicating events,
    and each subscription is authorized on the server.
12. Uploads are size-limited by the signature (or measured in storage and deleted when over, on
    stores without presigned POST), verified by content after upload, and served from a
    separate origin with `nosniff` and a restrictive disposition; an oversized test upload fails.
13. With each third-party hostname blocked in staging, core pages still load and deferred work
    is queued, not lost.
14. Use cases are callable without HTTP; routes, jobs and CLI are thin adapters around them.
15. Queue age, event-loop delay, pool wait time, outbound call latency per vendor and
    reconciliation findings are exported as metrics with alerts.

## Not this skill

- Endpoint contracts, pagination, API rate limits and generic webhooks → `0x:api-design`
- Schema design, transactions, locks and query tuning → `0x:postgres-database`
- Choosing and running Redis, search, object storage or streams → `0x:data-stores`
- Roles, permissions and per-object access checks → `0x:auth-identity`
- Sending email, SMS and push notifications → `0x:email-notifications`
- Profiling slow endpoints and load testing → `0x:web-performance`
