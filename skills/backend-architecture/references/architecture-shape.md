# Monolith, modules, services and events

Read this when: laying out a new backend, deciding between the framework's server and a separate
API service, drawing module boundaries, placing error handling, or deciding whether to extract a
service, introduce events, or adopt event sourcing.

## The shape by stage

| Stage | Shape | Processes |
|---|---|---|
| Prototype | One codebase, one deployable, one Postgres. Folders by feature, no enforced boundaries yet | `web` |
| Launch | Modular monolith: modules with public interfaces, a worker entrypoint from the same codebase | `web`, `worker` |
| Scale | Same monolith; extract a service only for a reason in the extraction table below | `web`, `worker`, plus the few extracted services |

A monolith keeps the two things a small team cannot afford to lose: a function call instead of a
network call, and one database transaction across the whole use case. The first "second service"
is almost always the worker process, which is the same code with a different entrypoint and not a
service boundary at all.

## Framework server or separate API service

Stay inside the meta-framework (Next.js route handlers and server functions) while all of these
hold: one web client, request-response work that fits the host's duration and body limits, and
background work that can run in a worker or hosted queue.

| Signal | Add |
|---|---|
| Work outlives the host's function duration limit, or must be retried | A worker process or hosted job service, not an API service |
| WebSockets or other long-lived connections on a serverless host (they end at the function's duration limit even where upgrades are accepted) | A long-running realtime service, or a hosted realtime provider |
| A second client (mobile app, public API, partner integration) needs a stable, versioned contract | A separate API service (Hono or Fastify) or a clearly versioned `/api/v1` surface with its own tests |
| CPU-heavy or non-JavaScript workload | A service in the fitting runtime (`runtime-language.md`) |
| Backend must deploy and scale independently of the UI | A separate API service |

Rules that hold either way:

- Server functions (server actions) are public HTTP endpoints. Each one validates input and
  authorizes the caller as if it were a hand-written route.
- The API surface for a mobile app cannot change in lockstep with a web deploy: old app versions
  live for months. That alone justifies an explicit, versioned contract (`0x:api-design`).
- A separate API service in the same language lives in the same repository and imports the same
  modules. Splitting the repository is a separate, later decision.

## Layout and module boundaries

Draw modules around business capabilities (billing, projects, notifications, identity), not
technical layers (`controllers/`, `services/`, `models/`). A capability changes for one business
reason; a layer changes for every reason.

```text
src/
  modules/
    billing/
      index.ts        public interface: the only file other modules may import
      service.ts      use cases
      repo.ts         queries against tables this module owns
      events.ts       events this module publishes
    projects/
  platform/           db, queue, logger, config, clock, vendor adapters
  app/                routes: parse, authenticate, call a module, map the result
  worker.ts           job entrypoint
  cli/                scripts and backfills
```

- Other modules import only `modules/<name>/index.ts`. Enforce it with a lint rule
  (`no-restricted-imports` patterns or dependency-cruiser) in CI; an unenforced boundary is gone
  within a quarter.
- Each table has one owning module, and only the owner writes it. Others read through the owner's
  query functions. Foreign keys across modules stay: referential integrity is worth more than
  theoretical extractability.
- Use cases accept an optional transaction handle so one operation spanning two modules stays
  atomic. Do not give this up to make the modules look like services.
- Dependencies point one way. If billing and projects import each other, either one concept is
  split across two modules or an event is missing.
- At Prototype skip enforcement and keep only the folder-per-feature habit. Add the lint rule at
  Launch, when the first module has a second consumer.

## Business logic outside transport

A use case is a plain function: `createInvoice(ctx, input)`. `ctx` carries the actor, the tenant,
the database or transaction handle, a logger and an abort signal. It knows nothing of HTTP,
cookies, headers, queue messages or `argv`.

| Adapter | Does | Does not |
|---|---|---|
| Route handler, server function | Parse and validate, authenticate, build `ctx`, call the use case, map result to status and body | Query the database, hold business rules |
| Job handler | Validate arguments, rebuild `ctx` (including tenant), call the use case, classify errors as retryable or not | Duplicate logic that the API also runs |
| CLI, backfill, webhook receiver | Same pattern | Bypass the use case "because it is internal" |

Authorization that depends on the resource belongs inside the use case, so jobs, CLI and a future
API cannot skip it (`0x:auth-identity`, `authorization.md`). The test of the split: the use case
is callable from a unit test with no HTTP mock, and a new entry point needs a new adapter and
nothing else.

## Errors by kind

| Kind | Examples | In code | To the client | Telemetry |
|---|---|---|---|---|
| Expected failure | Validation, not found, conflict, forbidden, quota reached, card declined | Typed result or typed error with a stable `code` | 4xx with the code and an actionable message | Count as a metric; not an error-tracker event |
| Dependency failure | Timeout, upstream 5xx, connection refused | Wrap with `cause`, mark retryable | 502, 503 or 504 with "try again"; retry where safe | Error tracker with a rate alert, not per event |
| Bug | `TypeError`, broken invariant, impossible state | Do not catch locally; let it reach the boundary | 500 with a generic message and a request ID | Error tracker, every one |

- One catch at each boundary (HTTP middleware, job runner, CLI main) does the mapping. `try/catch`
  in the middle of business code exists only to add context (`new Error('charging order', {
  cause: err })`) or to handle a specific expected failure.
- Error codes are stable strings (`plan_limit_reached`); clients branch on the code, never on the
  message. The response shape is owned by `0x:api-design` (`requests-responses.md`).
- Nothing internal reaches the client: no stack trace, SQL text or upstream response body.
- In Next.js production builds, messages of errors thrown on the server are masked before they
  reach the browser. Return expected failures from server functions as values (`{ ok: false,
  code }`); throw only for bugs.
- On `uncaughtException`, log, flush and exit: the process state is unknown and the supervisor
  restarts it. An unhandled rejection crashes current Node by default; keep that behavior.
- A caught-and-ignored error is the most expensive kind: `catch {}` needs a comment saying why
  losing the error is correct.

## Stateless servers and horizontal scale

Anything held in process memory or on local disk breaks when a second instance starts, or when
the first restarts. Find it before scaling:

| In-process state | Breaks as | Move to |
|---|---|---|
| Sessions in memory | Users logged out at random | Session store in the database or Redis (`0x:auth-identity`) |
| Rate-limit counters, login-attempt counters | Limit multiplied by instance count | Redis or the database |
| Cache used as truth | Instances disagree | Database as truth, cache with TTL |
| Uploads on local disk | File missing on the other instance, gone after deploy | Object storage (`file-uploads.md`) |
| `setInterval` or in-process cron | Job runs once per instance | Scheduler with a dedupe key (`background-jobs.md`) |
| In-memory job queue, fire-and-forget promises | Work lost on restart | Durable queue |
| WebSocket room membership in a `Map` | Messages reach only one instance's clients | Pub/sub backplane (`realtime.md`) |
| In-process mutex | No exclusion across instances | Database constraint or lock (`consistency-concurrency.md`) |

Check by running two instances behind a round-robin proxy locally and killing one mid-session.
Avoid sticky sessions as a fix: they hide the state and fail on every deploy. Do this work at
Launch even with one instance, because a deploy already behaves like a second instance.

## Events between modules

Start in-process. An event is a fact in the past tense (`invoice.paid`) carrying IDs, a schema
version and `occurredAt`; the publisher does not know who listens.

| Use | Mechanism |
|---|---|
| The caller needs the result or must fail if the reaction fails | A function call on the other module's interface, not an event |
| The reaction must commit atomically with the change | In-process handler inside the same transaction |
| The reaction can lag (email, search index, analytics, webhooks out) | Outbox row or job enqueued in the same transaction, handled by the worker (`consistency-concurrency.md`) |

Signs of a distributed monolith, in a monolith or across services:

- Two services must be deployed together, or share a database.
- One user request passes through a chain of synchronous calls, so availability multiplies down.
- An "event" is a command in disguise (`send_welcome_email_requested`) and the publisher waits
  for a reply event.
- A shared library of domain models forces every consumer to upgrade in lockstep.
- Nobody can say what happens after `order.created` without searching the codebase. Keep a
  registry file listing each event, its schema and its subscribers.

Event schemas change additively only; a breaking change is a new event name. Carry a correlation
ID from the originating request through every event and job, or tracing a failure becomes
archaeology.

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

1. Make the boundary real inside the monolith first: public interface only, own tables, no
   foreign joins. If this is hard, extraction would have been worse.
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
(upcasting), projections lag and need rebuild tooling, current state is not queryable with ad hoc
SQL, and erasure requests collide with an immutable log (the usual answer is per-subject
encryption keys that can be destroyed). If it is adopted, confine it to the one module that needs
it.

## Ask the user

- **Will there be a mobile app, public API or partner integration within a year?** It decides
  whether the API needs a stable versioned contract now. Assume web only, and keep use cases
  transport-free so the answer can change cheaply.
- **Where is this hosted, and does the host allow long-running processes?** Serverless-only
  hosting pushes jobs and realtime to hosted services. Assume a PaaS with a `web` and a `worker`
  process.
- **Is there a contractual or regulatory need for a full audit history of some data?** Only that
  justifies event sourcing in one module. Assume an audit table is enough.
- **Is any part expected to need very different resources (GPU, heavy media, untrusted code)?**
  That part is the first extraction candidate. Assume none.
- **How many people will deploy this in the next year?** Under about five, module boundaries
  solve coordination; services do not. Assume one.
