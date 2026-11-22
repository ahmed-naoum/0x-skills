# Validation, errors, pagination and payloads

Read this when: defining what an endpoint accepts and returns, adding a list endpoint, choosing an
error format, or designing PATCH, batch or long-running operations.

## Validate at the boundary, in and out

Every surface (route handler, server function, RPC procedure, webhook receiver, queue consumer)
parses its input with a schema before any other code runs, and the rest of the code receives the
parsed, typed value. TypeScript types prove nothing about bytes from the network.

- **Parse, do not check.** Use the schema's output (`schema.parse(body)`), never the raw input
  after validating it; coercions, defaults and stripped keys only exist in the output.
- **Validate all four inputs**: path params, query string, headers that carry meaning, body.
  Query values are strings: coerce explicitly (`z.coerce.number().int().min(1).max(100)`), and
  remember that naive boolean coercion turns the string `"false"` into `true`.
- **Bound everything.** Every string has a max length, every array a max item count, every number
  a range, every nested object a known depth. Unbounded inputs are the cheapest denial of service.
- **Decide unknown-field policy for requests and state it.** Zod's `z.object` silently drops
  unknown keys; `z.strictObject` rejects them. Rejecting is the better default for a public API:
  a typo (`emial`) fails loudly instead of being ignored, and no client can come to depend on
  sending junk. Responses are the opposite: clients must ignore fields they do not know.
- **Never pass a parsed body straight to the ORM.** Mass assignment (`role`, `tenant_id`,
  `price` set by the client) comes from spreading the request into an insert. The schema lists
  the writable fields; server-owned fields are set by code.
- **Shape output through a schema too.** Serialize responses from an explicit response type, not
  from the database row. A new column (password hash, internal note, cost price) then stays
  private by default instead of public by default.
- **Syntactic validation belongs in the schema; rules needing the database belong in the domain
  layer** (uniqueness, ownership, state transitions) and return 409 or 422 in the same error shape.

## Errors: RFC 9457 problem details

One error shape for the whole API, including errors produced by the framework, the auth
middleware, the rate limiter and the 404 handler. Clients write one error path; a second shape
from a proxy or default handler is where their code breaks.

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Request validation failed",
  "status": 422,
  "detail": "2 fields are invalid.",
  "instance": "/invoices",
  "code": "validation_error",
  "request_id": "req_01JD3Y7Q2W",
  "errors": [
    { "pointer": "/customer_id", "code": "required", "detail": "is required" },
    { "pointer": "/lines/0/quantity", "code": "too_small", "detail": "must be at least 1" }
  ]
}
```

- `type`, `title`, `status`, `detail`, `instance` are the standard members; everything else is an
  extension, which the RFC allows. `type` is a URI that identifies the problem class; make it
  resolve to documentation when the API is public.
- **`code` is the contract**: a stable, documented, lower-snake string clients branch on.
  `title` and `detail` are for humans and will be reworded; say in the docs that they are not
  stable, because clients will otherwise string-match them.
- **`errors[]` with a JSON Pointer per field** lets a form attach messages to inputs. Return all
  field errors at once, not the first.
- **`request_id` on every response** (also as a header), logged server-side. It turns a support
  ticket into one log query.
- **5xx bodies carry no internals**: no stack trace, SQL, file path or upstream error text. Log
  the cause under the request ID; return a generic problem.
- Use the most specific accurate status; do not invent sub-statuses, put the distinction in `code`.
- A 401 also needs `WWW-Authenticate`; a 429 and a 503 need `Retry-After`.

Check: trigger a malformed JSON body, an unknown route, a wrong method, an oversized body and an
expired credential, and confirm all five return `application/problem+json` in this shape.

## Pagination

Every endpoint that returns a list is paginated from its first version. Adding pagination later
is a breaking change, and the unpaginated list is the endpoint that takes the service down when
one customer grows.

Default: **keyset pagination behind an opaque cursor**, ordered by a stable total order.

```sql
SELECT * FROM invoices
WHERE tenant_id = $1 AND (created_at, id) < ($2, $3)   -- omit on the first page
ORDER BY created_at DESC, id DESC
LIMIT $4 + 1;                                           -- one extra row answers has_more
```

```json
{ "data": [ ... ], "has_more": true, "next_cursor": "eyJjIjoiMjAyNi0xMS0yMFQxMDo..." }
```

- **The order must be total.** Sorting on `created_at` alone skips or repeats rows that share a
  timestamp at a page boundary. Always append the unique ID as tie-breaker, and have an index
  matching the full order (`tenant_id, created_at DESC, id DESC`).
- **The cursor is opaque**: base64url of the sort-key values (plus a version marker). Clients
  must not build or parse it, which keeps the freedom to change the ordering strategy. Validate
  it on input and return 400 for a bad one. Sign it only if a forged cursor could reveal
  something the filters would not.
- **Precision trap**: Postgres timestamps have microsecond precision, a JavaScript `Date` has
  milliseconds. A cursor built from a `Date` rounds the boundary and silently drops or repeats
  rows. Carry the value as the database's text form, or order by a column that survives the round trip.
- **A cursor is only valid with the filters and sort it was issued for.** Either encode them in
  the cursor and reject a mismatch, or document that changing parameters mid-walk is undefined.
- **Page size**: `limit` with a default (20 to 50) and a hard max (100 is a common choice).
  Clamp or reject above the max, consistently.
- **No total count by default.** `COUNT(*)` over a filtered set costs more than the page as the
  table grows. Offer `has_more`; provide a count only where the UI truly needs it, as a
  separate opt-in or a capped count ("1000+").
- **Wrap lists in an object**, never a bare top-level array: an array cannot gain `next_cursor`
  or metadata later without breaking every client.

Offset pagination (`?page=3`) is acceptable only for small, bounded, admin-style lists that need
"jump to page N". It reads and discards every skipped row, and rows shift between pages when data
is inserted or deleted during the walk. Never use it for exports or sync, which must see each row once.

For sync consumers ("give me everything changed since last time"), order by a monotonic
`updated_at, id` or a sequence and let the final cursor be stored and reused later.

## Representing values in JSON

| Value | Representation | Trap it avoids |
|---|---|---|
| Instant | RFC 3339 string in UTC with `Z`: `"2026-11-22T09:30:00Z"` | Local times without offset; epoch seconds vs milliseconds confusion |
| Calendar date | `"2026-11-22"`, never an instant at midnight | Birthdays and due dates shifting by a day across time zones |
| Future local event | Local date-time plus IANA zone (`"Europe/Berlin"`) as separate fields | Zone rules change; a stored UTC instant goes wrong |
| Duration | Integer with the unit in the name (`timeout_seconds`), or ISO 8601 duration | Unitless numbers |
| Money | Integer minor units plus ISO 4217 code: `{"amount": 1999, "currency": "USD"}`, or a decimal string | Floats (`0.1 + 0.2`); assuming two decimals (JPY has zero, KWD three) |
| Other decimals, big integers | String | JSON numbers pass through IEEE doubles in most clients; integers above 2^53 lose digits |
| ID | String, always, even when the database uses integers | 64-bit IDs corrupt in JavaScript; a string leaves room to change ID schemes |
| Enum | Lower-snake string (`"past_due"`); documented as open: clients must handle unknown values | Integer codes; booleans that later need a third state |
| Absent value | Choose one: always present with `null`, or omitted. Apply everywhere | Clients cannot tell "not set" from "not returned" |

Prefer a status enum over a boolean whenever the concept may grow (`is_active` becomes
`active | paused | archived` within a year). Use UUIDv7 or another time-ordered ID under the
prefix for new tables so IDs index well and sort roughly by creation; do not expose sequential
integers, which leak volume and invite enumeration. Send and require `Content-Type:
application/json` with UTF-8.

## Filtering, sorting and field selection

The query interface is an allowlist that maps public names to internal queries. It is not a
pass-through to the database.

- **Filters**: one query parameter per filterable field, equality by default
  (`?status=open&customer_id=cus_1`); ranges with a fixed suffix or bracket convention
  (`created_after=`, or `created[gte]=`), chosen once. Each public filter maps in code to a
  column and operator. Reject unknown parameters with 400 rather than ignoring them, or a typo
  silently returns the unfiltered list.
- **Sorting**: `?sort=-created_at` from a short allowlist. Every allowed sort needs a supporting
  index and the ID tie-breaker, and the cursor must encode that sort's keys. Offering "sort by
  any column" is a promise to index every column.
- **Search**: a single `q` parameter with documented, loose semantics, so the engine behind it
  can change.
- **Field selection and expansion**: skip `?fields=` until payload size is a measured problem.
  Prefer `?expand=customer` (or `include=`) from an allowlist to embed related objects, with a
  depth cap of one or two; each expansion is a batched query, not a per-row lookup.
- **Never accept** raw column names, ORM `where` objects, SQL fragments or an open filter
  language from the client. They couple clients to the schema, allow unindexed scans on demand,
  and let callers filter on fields they cannot read (a filter on a hidden field leaks it bit by bit).
- Filters always apply inside the caller's tenant and permissions; they narrow, never widen.

## Caps: size, headers, time

Set explicit limits at the outermost layer that can enforce them, and again in the app. Defaults
differ per layer and the lowest one wins, usually by surprise.

| Limit | Starting value | Response |
|---|---|---|
| JSON body | 100 KB to 1 MB; raise per route, not globally | 413 |
| File upload | Not through the API body: direct-to-storage upload (`0x:backend-architecture`, `file-uploads.md`) | |
| Header size | Leave the server default (Node's is 16 KB total); the usual cause of overflow is cookie bloat | 431 |
| URL length | Keep under about 2,000 characters; move large filters to a POST search endpoint | 414 |
| Request duration | 10 to 30 s for interactive endpoints; anything longer becomes a job | 504 from the proxy, or 503 |
| Array items, string length, nesting | In the schema, per field | 422 |

Known defaults to check rather than assume: Express's JSON parser limits bodies to 100 KB;
Next.js server functions limit the body to 1 MB unless configured; nginx's
`client_max_body_size` defaults to 1 MB; serverless platforms impose their own payload and
duration ceilings. When a request works locally and fails in production with 413 or 502, compare these.

Timeouts shrink inward: client > CDN or load balancer > app request timeout > database
`statement_timeout` and outbound call timeouts. If an inner layer can outlive an outer one, the
client sees a bare gateway error while the server keeps working on a response nobody will read.
Enforce the body cap while reading the stream, before the whole body is buffered in memory.

## Partial updates

Default: `PATCH` with JSON Merge Patch semantics (RFC 7396): fields present are set, fields
absent are untouched, `null` clears a field. Nested objects merge recursively; **arrays are
replaced whole**. State these three rules in the docs.

| Client sends | Meaning |
|---|---|
| Field absent | Leave unchanged |
| Field `null` | Clear (422 if the field is not nullable) |
| Field with value | Set |
| Array | Replace the entire array |

Traps:

- **Defaults in the update schema.** Reusing the create schema with `.partial()` keeps its
  `.default()` values, so an absent field is parsed as its default and overwrites stored data.
  Define the update schema without defaults.
- **`undefined` and `null` collapse** in careless code (`if (!body.name)`, spreading into an
  update). Build the update from keys that are present (`key in body`), and keep `.optional()`
  (may be absent) and `.nullable()` (may be null) as separate decisions per field.
- **PUT means full replacement**: a field the client omits is reset. If the handler actually
  merges, it is a PATCH with the wrong name, and a client that follows the HTTP definition loses data.
- **Collections inside a resource** (members, tags, line items) do not fit merge patch beyond
  small arrays. Give them sub-resource endpoints (`POST /projects/{id}/members`,
  `DELETE .../members/{id}`) instead of adopting JSON Patch (RFC 6902), which few clients build correctly.
- Concurrent PATCHes lose updates silently without a version check; see `If-Match` in
  `idempotency-rate-limits.md`.

## Long-running operations

Turn an operation into a job when its p99 can exceed a few seconds or approach the platform's
request limit: exports, imports, report generation, bulk changes, anything calling a slow third party.

1. `POST /exports` validates, enqueues, and returns **202 Accepted** with the job resource and
   `Location: /exports/exp_123`. Accept an idempotency key so a retried POST does not start two jobs.
2. `GET /exports/exp_123` returns
   `{ "id", "status": "queued|running|succeeded|failed|canceled", "progress", "created_at", "completed_at", "result", "error" }`.
   `result` appears on success (data or a short-lived download URL); `error` is a problem object.
3. Send `Retry-After` on the status response to set the polling pace; document a floor (for
   example, no faster than once per second).
4. Offer `POST /exports/exp_123/cancel` if the work is expensive, and a completion webhook for
   integrators who should not poll.
5. Expire finished jobs and their results after a stated retention; return 404 or 410 afterward.

The job is a normal resource: listable, tenant-scoped, authorized like any other. Do not hold the
HTTP connection open for minutes instead; proxies, mobile networks and serverless limits cut it,
and the client cannot tell whether the work happened. Queue mechanics are in
`0x:backend-architecture`, `background-jobs.md`.

## Batch endpoints

Add a batch endpoint only when clients demonstrably loop over a single-item endpoint at volume.
Decide atomicity first and put it in the name or the docs:

| Mode | Behavior | Use when |
|---|---|---|
| Atomic | One transaction; any invalid item fails the whole request with 4xx and per-item errors | Items depend on each other (ledger lines, a reorder). Default when unsure: easiest for clients to reason about |
| Independent | Each item succeeds or fails alone; the response is 200 with one result per item | Bulk imports, notifications, items owned by different entities |

For independent mode: return results in request order, each with the index or client-supplied
reference, a per-item status and either the resource or a problem object, plus a summary
(`succeeded`, `failed`). The client must never have to diff to find which items failed. Use 200
with this body rather than 207, which belongs to WebDAV and which generic clients do not treat
specially; reserve 4xx for a request that is invalid as a whole (malformed, over the item cap).
Cap items per request (100 is a reasonable start) and the total body size, give each item its own
idempotency reference if the batch can be retried, and move very large batches to the job pattern above.

## Ask the user

- **Is money in this API, and in which currencies?** Decides minor-unit handling and the
  zero-decimal cases. Default: integer minor units with an explicit currency on every amount.
- **How large can one customer's list realistically get in two years?** Decides whether counts,
  arbitrary sorts or offset paging are affordable. Default: assume large; cursors, no totals.
- **Do integrators need to sync all data incrementally?** If yes, design an `updated_at`-ordered
  listing and deletion visibility (tombstones or a deleted-events feed) now. Default: not yet.
- **Should unknown request fields be rejected?** Strictness helps integrators find mistakes but
  makes some future changes noisier. Default: reject on public APIs, strip on internal ones.
- **How long may job results and downloadable files be kept?** A retention and privacy choice.
  Default: 24 hours for download links, 30 days for job records.
