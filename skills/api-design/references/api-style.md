# Choosing and shaping an API style

Read this when: starting an API, adding a new surface (mobile app, partner integration, internal
service), or reviewing whether the existing endpoints are named, structured and described consistently.

## Pick the style per consumer, not per product

The question is never "REST or GraphQL for this product". It is "who calls this surface, who
deploys them, and how long do their old versions live". One product commonly has two or three surfaces.

| Consumer | Default | Why | Flips when |
|---|---|---|---|
| Own web UI in the same repo and deploy (Next.js) | No API. Server components read through the data layer; server functions mutate | Nothing to version, type safety for free, one deploy | A second client appears that cannot call server functions |
| Own SPA or mobile app, TypeScript, same monorepo | Typed RPC (tRPC, or an OpenAPI-typed client over route handlers) | End-to-end types without a spec to maintain | Client is not TypeScript, or third parties need it too |
| Own native mobile app (Swift, Kotlin) | REST + OpenAPI with generated clients | Old app versions live for months; needs a real contract | |
| Third-party developers, partners, Zapier-style tools | REST + OpenAPI, JSON, API keys | Every language and tool speaks it; curl-able; cacheable | Almost never |
| Many client teams with divergent data needs over one graph | GraphQL | Clients compose their own reads | Only with people to run it; not a solo default |
| Service to service, internal, polyglot or streaming | Connect or gRPC over Protobuf | Strict schema, deadlines, streaming, codegen in every language | Only one service exists: call a function instead |
| AI agents | MCP server over the same domain layer | See `public-api-platform.md` | |

Rules that settle most arguments:

- **Do not build an API for a UI in the same deploy.** A REST layer between a Next.js page and its
  own database doubles the code and adds a contract nobody else consumes. Build the API when a
  second consumer exists.
- **Keep one domain layer under every surface.** Server functions, route handlers, tRPC procedures
  and MCP tools should all be thin adapters that parse input, authorize, call the same domain
  function and shape output. Adding a surface is then an afternoon; without it, each surface drifts.
- **Server functions and tRPC procedures are public HTTP endpoints.** Anyone can call them with
  any arguments, whatever the UI shows. Each one validates input and checks authorization itself.
- **Typed RPC is not a public contract.** tRPC couples client and server builds; it is right
  exactly while both ship from one repo. Do not hand it to outsiders, and do not let a mobile app
  with a release cycle depend on it without treating procedure inputs as a versioned contract.
- **Do not choose GraphQL to avoid designing endpoints.** It moves the cost to query-cost control,
  authorization per field, N+1 batching and cache design, which is more work, not less.

Deploy skew applies to every style: a browser tab runs yesterday's JavaScript against today's
server, and a mobile app runs last year's. Any surface whose client is not deployed atomically with
the server needs the compatibility rules in `versioning-evolution.md`, including server functions.

## Resources, names and URLs

Consistency beats any particular convention: a developer who has used two endpoints should guess
the third correctly. Fix these once, in a short conventions section of the API description, before
the second endpoint is written.

- **Paths are plural nouns for collections, with an ID for one item**: `/invoices`,
  `/invoices/{id}`. Lowercase, hyphens between words. No verbs, no file extensions, no trailing slash.
- **Nest one level at most, and only for true ownership**: `/projects/{id}/members`. Anything with
  its own global ID is also addressable flat (`/members/{id}`); deep paths like
  `/orgs/1/projects/2/tasks/3/comments/4` force clients to carry IDs they do not need.
- **Tenant comes from the credential, not the path**, unless a credential can act across tenants.
  A tenant ID in the URL that is not checked against the credential is the classic
  cross-tenant read; see `0x:auth-identity` for the authorization model.
- **Actions that are not CRUD are POST on a sub-path**: `POST /invoices/{id}/void`,
  `POST /exports`. Prefer modeling the action as a resource (`POST /refunds` rather than
  `POST /charges/{id}/refund`) when it has its own state, history or ID.
- **One casing for JSON fields everywhere.** `snake_case` is the common choice for public JSON
  APIs and reads the same in every language; `camelCase` is natural when all consumers are
  TypeScript. Never mix, and never let the ORM's column naming leak the choice by accident.
- **IDs are opaque strings with a type prefix** (`inv_`, `cus_`): support and logs can tell what
  an ID is, and a wrong-type ID fails fast. Details in `requests-responses.md`.
- **Singletons have no ID**: `/me`, `/account/settings`.

Methods and status codes carry meaning that clients, proxies and retry logic rely on:

| Method | Use | Safe to retry blindly | Success |
|---|---|---|---|
| GET | Read; no side effects, no body | Yes | 200 |
| POST | Create or run an action | No, unless idempotency key | 201 + `Location` for create; 200 for action; 202 for async |
| PUT | Replace the whole resource, or create at a client-chosen ID | Yes | 200 or 204 |
| PATCH | Partial update | Not by definition; make it so | 200 with the updated resource |
| DELETE | Remove | Yes | 204; repeat delete returns 404 or 204, pick one and document it |

| Status | Meaning to commit to |
|---|---|
| 400 | Malformed request: unparseable JSON, wrong content type |
| 401 | No valid credential. 403: valid credential, not allowed |
| 404 | Not found, and also "exists in another tenant": do not confirm existence across tenants |
| 409 | Conflict with current state (duplicate, illegal state transition) |
| 412 / 428 | Precondition failed / required (`If-Match`) |
| 422 | Well-formed but fails validation. Pick 400 or 422 for validation once and never mix |
| 429 | Rate limited, with `Retry-After` |
| 500 / 503 | Bug / temporarily unable, with `Retry-After` when known |

Never return 200 with an error in the body: monitoring, retries, caches and SDKs all key on the
status code. Return the created or updated resource from writes so clients do not need a second read.

## Contract first

Agree the contract before either side is implemented, because the contract is the expensive thing
to change and the implementation is cheap. The sequence that works, including when Claude writes
both sides:

1. Write the consumer's tasks as calls: three to five concrete request and response examples per
   flow, with real-looking values. Examples expose missing fields and awkward shapes faster than schemas.
2. Turn them into schemas (Zod, or OpenAPI directly), including the error cases and the list shape.
3. Review against the checks below. Change it now.
4. Generate types and, if the consumer is being built in parallel, a mock from the schema.
5. Implement the server against the schema; the schema validates requests at runtime, so the
   contract and the code cannot disagree silently.

Review checks for a contract: every list is paginated; every write says how it behaves on retry;
every field has one type and a stated nullability; errors use the shared shape; names match the
existing conventions; nothing exposes a column name, internal enum or auto-increment ID that the
team would not want to keep for years; the response contains what the next screen needs, so the
client does not fan out into N follow-up calls.

Design from the consumer's task, not from the tables. An API that mirrors the schema turns every
migration into a breaking change and makes clients orchestrate multi-step writes that should be
one transaction on the server.

## OpenAPI and typed clients

Use OpenAPI 3.1 (its schemas are JSON Schema 2020-12, so one schema serves validation and
documentation). Two workable sources of truth; pick one and never hand-edit the other:

| Approach | How | Choose when |
|---|---|---|
| Code-first from schemas | Zod schemas define routes; the OpenAPI document is generated (Hono with `@hono/zod-openapi`, `zod-openapi`, ts-rest, Fastify with a type provider) | TypeScript server; default. The validator and the document cannot drift |
| Spec-first | Hand-written `openapi.yaml`; server types and client generated from it | Several server languages, or the API is designed with partners before code exists |

Decorators or comments that describe routes separately from the validation code are the trap:
the document drifts from behavior within weeks. Whatever generates the document must be the same
object that validates the request.

Details that pay later:

- **Commit the generated `openapi.yaml`** (or JSON) and fail CI when regeneration changes it.
  This makes contract changes visible in review and enables the breaking-change diff in
  `versioning-evolution.md`.
- **`operationId` is a public name.** Generators turn it into SDK method names; set it
  deliberately (`listInvoices`, `createInvoice`) and never rename it casually.
- **Use `components/schemas` with `$ref`**, not inline schemas: named types generate named
  types. Define the error and the list envelope once and reference them.
- **Mark `required` and nullability precisely.** A generated client is only as good as these; a
  field that is "sometimes missing" becomes `T | undefined` on every access for every user.
- **Put an `example` on every operation**; docs and mocks are built from them.
- **Lint the document in CI** (Spectral or Redocly CLI) for the conventions above: casing,
  pagination parameters, error responses on every operation.

Typed client for TypeScript consumers, without a heavy generator:

```bash
pnpm dlx openapi-typescript ./openapi.yaml -o ./src/api/schema.d.ts
```

```ts
import createClient from "openapi-fetch";
import type { paths } from "./api/schema";

const api = createClient<paths>({ baseUrl: "https://api.example.com" });
const { data, error } = await api.GET("/invoices/{id}", { params: { path: { id } } });
```

Types only, no runtime code generated, so regenerating is safe to automate. Full multi-language
SDKs are a separate decision: see `public-api-platform.md`.

## GraphQL, when it is chosen

Adopt it only with a clear reason from the table above. Then these are not optional, because a
GraphQL endpoint lets the caller write the query plan:

- **Authorize in the domain layer or resolver, per object and field**, never only at the route.
  Any type reachable by any path through the graph is exposed.
- **Batch every relation.** One DataLoader (or equivalent) per request for each parent-to-child
  lookup; without it a list of 50 with two nested relations is 101 queries. Create loaders per
  request, never globally, or one user's cached rows are served to another.
- **Limit what a query may cost before executing it**: maximum depth, maximum cost computed from
  list sizes (each list field's `first` multiplies the cost of its children), a cap on aliases
  and on batched operations per HTTP request, and a per-request timeout. Rate-limit by computed
  cost, not by request count: one request can be a thousand times another.
- **Persisted queries for first-party clients.** The build extracts every operation, the server
  accepts only known hashes (a "trusted documents" allowlist). This removes arbitrary queries
  from the attack surface, allows GET with CDN caching, and makes operations nameable in
  metrics. Automatic persisted queries without an allowlist save bytes but add no protection.
- **Disabling introspection is not access control**; field suggestions and client bundles leak
  the schema. Use it as noise reduction on top of the allowlist.
- **Schema shape**: Relay-style connections (`edges`, `pageInfo`, `first`/`after`) for every
  list; mutations take one `input` object and return a payload type; expected business failures
  are data (a union or an `errors` field on the payload), while the top-level `errors` array is
  for bugs and transport faults; keep fields nullable unless the resolver cannot fail, because one
  failed non-null field nulls its whole parent.
- **Evolve without versions**: add fields, mark old ones `@deprecated`, remove after measured
  field usage reaches zero.

A public GraphQL API cannot use an allowlist, so cost analysis and cost-based rate limits carry
the whole load. That is the main reason REST stays the default for third parties.

## gRPC and Connect between services

Skip until there are separately deployed services that talk synchronously. A monolith with
modules calls functions (`0x:backend-architecture` covers when to split). When it does pay:
several languages, streaming, or enough internal calls that hand-written HTTP clients become the bug source.

| Decision | Rule |
|---|---|
| gRPC or Connect | Connect by default: the same Protobuf service is callable as gRPC, gRPC-Web, or plain HTTP POST with JSON, so curl, browsers and ordinary load balancers work. Pure gRPC needs HTTP/2 end to end and a proxy for browsers |
| Schema hygiene | Never reuse or renumber a field number; `reserved` the number and name of a deleted field. Never change a field's type. Adding fields is safe |
| Tooling | Buf: `buf lint` and `buf breaking --against` the main branch in CI |
| Deadlines | Every call carries a deadline, propagated downstream; a call without one holds resources forever when a peer stalls |
| Load balancing | HTTP/2 multiplexes on one long-lived connection, so a connection-level (L4) balancer pins all traffic to one backend. Use a request-level (L7) balancer or client-side balancing |
| Errors | Use the status codes (`NOT_FOUND`, `FAILED_PRECONDITION`, `UNAVAILABLE`) with structured details; retry only `UNAVAILABLE` and only for idempotent methods |
| Edge | Keep Protobuf internal; expose REST and JSON publicly unless customers ask otherwise |

## Ask the user

- **Who will call this, besides the product's own UI, in the next six months?** Decides whether
  any API is needed now. Default: nobody; build server functions and a clean domain layer, add
  REST when the second consumer is real.
- **Is there, or will there be, a native mobile app?** Its old versions pin the contract for
  months. Default: assume not; if yes, use REST with OpenAPI from the start for the mobile surface.
- **Is a public or partner API on the roadmap?** If yes, name resources and fields now as if
  they were public, since internal names tend to ship. Default: design internal endpoints to the
  public conventions anyway; it costs little.
- **Does an existing team or customer require GraphQL or gRPC?** Only an external requirement
  justifies them at Prototype or Launch. Default: no.
