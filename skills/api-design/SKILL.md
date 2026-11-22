---
name: api-design
description: "Designs, documents and evolves HTTP APIs and webhooks: REST, tRPC, GraphQL or server functions, contracts, errors, pagination, idempotency, rate limits, versioning, API keys and MCP servers. Use when designing or reviewing endpoints, making a POST safe to retry, adding rate limits, receiving or sending webhooks, changing an API without breaking clients, or launching a public API."
---

# API design

## Stance

An API is a promise to code the team does not deploy. The implementation behind it can be
rewritten in an afternoon; the contract, once someone depends on it, can only be added to. So the
expert spends effort where it is irreversible (names, shapes, error and retry semantics, what is
exposed at all) and stays cheap everywhere else. Before applying anything here, read what the
project already does (framework, validation library, existing endpoint conventions) and stay
consistent with it; a second convention is worse than an imperfect first one.

- **Choose the style per consumer.** A UI in the same deploy needs no API; a TypeScript client in
  the same repo gets typed RPC; outsiders get REST with OpenAPI. One product has several surfaces
  over one domain layer, and each surface is a thin adapter.
- **Every network call happens zero, one or many times.** Clients, proxies, queues and users
  retry. Each write must define what a duplicate does, and each event consumer must tolerate
  duplicates, reordering and delay. Designing this later means reconciling corrupted data.
- **Additive only.** Removing, renaming, retyping, tightening and changing defaults all break
  someone. Design responses so they can grow (objects, not bare arrays or scalars; open enums),
  and tell clients on day one to ignore what they do not recognize.
- **Validate at the boundary, in both directions.** Parse every input against a schema with
  bounds; build every response from an explicit shape, never from the database row. This is
  where injection, mass assignment and accidental data exposure are stopped.
- **One shape for everything repeated.** One error format, one list envelope, one pagination
  scheme, one casing, one date format. Integrators learn the API from two endpoints and guess the rest.
- **Expose tasks, not tables.** An API that mirrors the schema makes every migration a breaking
  change and leaks what should stay private. Publish the smallest surface that serves the
  consumer's task; adding later is free, removing is not.
- **Bound every request.** Page size, body size, duration, cost and rate all have explicit
  limits with documented responses. The unbounded endpoint is the one that causes the outage.
- **Anything public is a security boundary.** Server functions, RPC procedures and webhook
  receivers are open HTTP endpoints: each authenticates, authorizes per tenant and validates,
  whatever the UI in front of it does.

## Route

| If the task is | Read |
|---|---|
| Starting an API or a new surface; choosing REST, tRPC, GraphQL, gRPC or server functions; naming resources and URLs; agreeing a contract; writing OpenAPI or generating a typed client | `references/api-style.md` |
| Defining what an endpoint accepts and returns: validation, error format, pagination, filtering and sorting, dates, money and IDs in JSON, size and time caps, PATCH semantics, long-running jobs, batch endpoints | `references/requests-responses.md` |
| Making a POST safe to retry; idempotency keys; lost updates and `If-Match`; rate limits, quotas and 429 responses; usage metering; retry and backoff guidance | `references/idempotency-rate-limits.md` |
| Receiving another service's webhooks, or sending webhooks to customers: signatures, async processing, ordering, reconciliation, retries, SSRF protection, endpoint management, payload design | `references/webhooks.md` |
| Changing an API that has consumers; deciding whether a change is breaking; versioning scheme; deprecation policy; OpenAPI diff in CI; sunsetting an endpoint; serving two versions | `references/versioning-evolution.md` |
| Opening the product to outside developers or AI agents: whether to launch a public API, API keys, reference docs, quickstart, SDKs, sandbox, OAuth apps, an MCP server | `references/public-api-platform.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Surface for the product's own Next.js UI | Server components for reads, server functions for writes, no REST layer | A second client exists |
| Surface for outsiders and native apps | REST, JSON, OpenAPI 3.1 generated from the Zod schemas that validate requests | An external requirement for GraphQL or gRPC |
| Domain logic | One domain layer; every surface is an adapter that parses, authorizes, calls, shapes | |
| Paths and fields | Plural nouns, one nesting level, actions as `POST /things/{id}/verb`; one JSON casing | Project already has a convention: follow it |
| IDs | Opaque prefixed strings; never exposed sequential integers | |
| Errors | RFC 9457 `application/problem+json` with a stable `code`, per-field `errors[]`, `request_id` | |
| Lists | Keyset pagination, opaque cursor, total order with ID tie-breaker, `limit` default 20 to 50 and max 100, no total count | Small bounded admin list: offset is acceptable |
| Dates, money | RFC 3339 UTC strings; integer minor units plus currency code | |
| Partial update | PATCH with merge-patch semantics: absent is untouched, `null` clears, arrays replace | |
| Slow work | 202 plus a pollable job resource when p99 exceeds a few seconds | |
| Retried writes | `Idempotency-Key` on POSTs with side effects, stored with the response for at least 24 h | Operation is naturally idempotent or covered by a unique constraint |
| Concurrent edits | Version column, `ETag`, `If-Match`, 412 on mismatch | Append-only resources: skip |
| Rate limits | Per tenant and key, 429 with `Retry-After`, state in a store every instance shares: a token bucket in Redis where the project already runs Redis, otherwise an atomic Postgres counter; edge limits by IP in front | Single long-lived instance: in-memory is enough. Limiter shows up in database load: move it to Redis |
| Inbound webhooks | Verify on raw bytes, store in an inbox table, 2xx, process in a worker, reconcile by polling | |
| Outbound webhooks | Outbox, HMAC signature with timestamp, retries over days, delivery log, SSRF checks on resolved IPs | |
| Versioning | `/v1` in the path, evolved additively; no `/v2` planned | Regular breaking changes: date-pinned versions with a transform layer |
| Credentials for a public API | Prefixed, hashed, scoped API keys owned by the organization | Third parties act for users: OAuth |

By stage:

- **Prototype**: schema validation on every input, one error shape, pagination on lists, unique
  constraints on business keys. Skip idempotency-key storage, rate-limit infrastructure, outbound
  webhooks, versioning machinery, public API, SDKs.
- **Launch**: idempotency keys wherever money, messages or third-party calls are involved;
  per-tenant rate limits and stricter ones on auth endpoints; inbound webhooks with inbox,
  dedup and reconciliation; explicit body and time caps; committed OpenAPI document if anything
  outside the repo consumes the API.
- **Scale**: public API with keys, docs, deprecation policy and breaking-change checks in CI;
  usage metering and quotas; cost-based and concurrency limits; outbound webhooks with customer
  self-service; SDKs, sandbox, OAuth and MCP as demand appears.

## Before you call it done

1. Every input (path, query, headers used, body) is parsed by a schema with length, range and
   item bounds, and handlers use the parsed value only.
2. Responses are built from an explicit shape; adding a database column cannot change any response.
3. Every handler authorizes against the caller's tenant; a valid ID from another tenant returns 404.
4. Malformed JSON, unknown route, wrong method, oversized body and bad credential all return the
   same problem-details shape with a stable `code` and a `request_id`; no 5xx leaks internals.
5. Every list endpoint is paginated with a total order, has a max page size, and returns an
   object envelope; walking it while inserting rows yields no skips or duplicates.
6. Dates are RFC 3339 UTC, money is never a float, IDs are strings, and null-versus-absent
   follows one rule.
7. Each POST with side effects has a stated duplicate behavior; sending it twice concurrently
   with the same idempotency key produces one side effect, and the second caller gets the
   replayed response or a 409 in-progress, never a second execution.
8. PATCH leaves absent fields untouched (no schema defaults applied), and resources that can be
   edited concurrently reject stale writes with 412.
9. Limits exist for body size, request duration, page and batch size, and rate; 429 and 503
   carry `Retry-After`; the limiter's store is shared across instances; IP-keyed limits take the
   client address from the trusted proxy hop, not from a client-set `X-Forwarded-For`.
10. Webhook receivers verify the signature over raw bytes in constant time, check timestamp
    freshness, deduplicate on event ID, respond before processing, and have a reconciliation job.
11. Outbound webhook URLs are checked against private address ranges at send time on the
    resolved IP, redirects are not followed, and each delivery is logged and replayable.
12. The change was compared against the breaking-change table; the OpenAPI document is
    regenerated, committed and diffed against main in CI.
13. Deprecated surfaces emit deprecation signals and their per-consumer usage is measurable.
14. API keys are stored hashed, shown once, scoped, revocable at once, and never appear in logs or URLs.
15. Docs and examples match the behavior: the quickstart was run end to end from a clean environment.

## Not this skill

- User login, sessions and permission models behind the endpoints → `0x:auth-identity`
- Service boundaries, background jobs and realtime transports → `0x:backend-architecture`
- Payment-provider webhooks and billing state → `0x:payments-billing`
- HTTP caching headers, CDN rules and edge rate limiting → `0x:web-networking`
- Contract tests and other API test automation → `0x:code-quality`
- Claude API parameters, tool-use syntax and SDK usage → `claude-api`
