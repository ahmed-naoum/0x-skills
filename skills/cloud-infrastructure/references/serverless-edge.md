# Serverless and edge runtimes

Read this when: code runs in functions (AWS Lambda, Vercel or Netlify functions, Cloud Run scaled to zero, Azure Functions) or in edge isolates (Cloudflare Workers, edge middleware), and the task involves cold starts, limits, state, database connections, background work or runaway invocations.

## The execution model, stated as constraints

Every design decision follows from five facts. Check each against the platform's current documentation for the exact numbers.

| Fact | Consequence |
|---|---|
| An instance may be created for any request and destroyed after any response | No in-memory state is shared or durable: sessions, rate-limit counters, caches, in-process schedulers and websockets registries all break silently |
| After the response is sent the instance may be frozen mid-instruction | Un-awaited promises (logging, analytics, emails, cache writes) are lost or run minutes later on the next thaw |
| Each invocation has a hard time limit (seconds on edge and default tiers, up to minutes on function platforms) | Long work must be split, queued or moved to a container |
| The platform scales by adding instances, with no regard for what is downstream | A traffic spike becomes a connection storm on the database and a spending spike on every metered API |
| Request and response bodies, bundle size, memory and `/tmp` are capped | Large uploads go direct to object storage with signed URLs; large responses stream |

## Cold starts

A cold start is: fetch the bundle, start the runtime, run module-level code, then handle the request. The first two are the platform's; the third is the application's, and usually the largest part.

Reduce in this order, measuring after each:

1. **Shrink what loads.** Bundle and tree-shake; import SDK sub-clients rather than whole SDKs; lazy-`import()` heavy modules used by rare routes (PDF, image and spreadsheet libraries, large validation or ORM clients with generated engines). Check the bundle analyzer output per function, not per app.
2. **Do less at module scope.** No network calls, schema introspection or config fetching at import time unless every request needs it. Do create clients (database, HTTP) at module scope so warm invocations reuse them; create them lazily on first use.
3. **Give it more memory.** On platforms where CPU scales with memory (Lambda), a larger setting starts faster and often costs the same because duration falls.
4. **Pay for warmth only for user-facing paths**: provisioned or minimum instances, or the platform's snapshot or pre-warm feature. This turns a per-request price into an always-on price; rerun the break-even in `platform-choice.md`.
5. **Change the unit.** If p99 latency on a core path is dominated by cold starts and traffic is steady enough to keep a process busy, an always-on container is the fix, not a warming cron. Scheduled pings keep one instance warm and do nothing for the second concurrent request.

Measure with the platform's init-duration metric and p99 (not average) latency, split by cold versus warm. A rule of thumb for a Node function: a few hundred milliseconds of init is normal, over one second means the bundle or module-scope work needs attention. Isolates start in single-digit milliseconds because they skip the process and runtime boot; that is their main advantage.

## Web-standard code that ports

Write handlers against the standard APIs every modern runtime shares (Node, Deno, Bun, Workers, browser): `fetch`, `Request`, `Response`, `Headers`, `URL`, `URLSearchParams`, `ReadableStream`/`TransformStream`, `TextEncoder`/`TextDecoder`, `crypto.subtle`, `crypto.randomUUID()`, `AbortController`, `AbortSignal.timeout()`, `structuredClone`, `FormData`, `Blob`.

```ts
export async function handle(req: Request, env: { DATABASE_URL: string }): Promise<Response> {
  const url = new URL(req.url);
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  const body = await req.json();              // validate with a schema before use
  const upstream = await fetch("https://api.example.com/v1/items", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(5000),
  });
  return new Response(upstream.body, { status: upstream.status, headers: { "content-type": "application/json" } });
}
```

Portability rules:

- A handler is `(Request, env) => Response`. Next.js route handlers, Hono, and Workers all take this shape; Hono is the default when a small framework is wanted that runs unchanged on Node, Bun, Deno, Workers and Lambda adapters.
- Pass configuration in (the `env` argument) instead of reading `process.env` deep in modules: isolates deliver bindings per request, and module-scope reads may see nothing.
- Use `Uint8Array` and Web Crypto in shared code rather than `Buffer` and `node:crypto`; keep Node-only code (`fs`, `child_process`, native addons, `net`) in modules that only Node entry points import.
- Stream instead of buffering: return `upstream.body` or a `ReadableStream`; a buffered large response hits memory and body-size caps. Every outbound `fetch` gets a timeout; the platform's own limit is otherwise the only one and it bills for the wait.
- Check a dependency's runtime support before adopting it for edge code: anything with native bindings or raw TCP assumptions will not load.

## Edge or in-region

The edge is close to the user; the data is not. The question is how many round trips to the data a request makes.

| Run at the edge | Run in-region, beside the database |
|---|---|
| Redirects, rewrites, header and cookie manipulation | Anything making more than one database query |
| Verifying a signed session token or JWT (signature check only) | Session lookups against the primary database |
| Geolocation, locale and A/B bucketing | Transactions, writes that must be read back immediately |
| Bot and rate-limit screening, cache-key normalization | Calls to third-party APIs hosted in one region |
| Serving cached or static content, stitching cached fragments | Server rendering of per-user pages from the database |
| Thin proxies to a nearby cache or globally replicated read store | CPU-heavy work: image, PDF, large JSON, crypto beyond a signature |

Arithmetic that settles it: an edge function 150 ms from the database making three sequential queries adds about 900 ms of round trips that an in-region function would not; the user's single 150 ms trip to the region is cheaper. Edge wins only when the response needs zero or one origin trip, or the data is itself replicated near the edge and can be stale.

Defaults: render and run API logic in the database's region (set the function region explicitly; platform defaults are often a US region regardless of where the database lives). Use the edge for the left column, and prefer the CDN's cache over edge compute whenever a cached response would do (`0x:web-networking` `http-caching.md`).

## Edge-runtime limits

- **Partial Node API.** Compatibility layers cover a growing subset (Workers' `nodejs_compat` flag, for example), but file system access, child processes, native addons and arbitrary sockets are absent or restricted. Database access goes through an HTTP or WebSocket driver, the platform's connection service (Cloudflare Hyperdrive, for example), or the platform's own socket API. Test in the platform's local emulator (`wrangler dev`) rather than plain Node; code that passes in Node fails at deploy.
- **CPU time, not wall time, is capped**, often at tens of milliseconds on entry tiers and configurable upward on paid ones. Awaiting `fetch` does not count; parsing a multi-megabyte JSON body, hashing passwords, rendering large pages and image work do. Symptom: intermittent "exceeded CPU" errors on large inputs only. Fix: move that work in-region.
- **Small memory and bundle caps** (on the order of a hundred-odd MB of memory and a few MB of compressed script). Stream; do not accumulate.
- **Subrequest caps** per invocation. A fan-out loop over many URLs fails partway; batch upstream or use a queue.
- **Key-value stores at the edge are eventually consistent.** A write may take up to a minute or so to be visible in other locations, and a read-after-write from a different location returns the old value. Use them for config, flags, cached lookups and anything tolerant of staleness. Do not use them for counters, inventory, session revocation that must be immediate, or locks; those need a strongly consistent primitive (a single-region database, or the platform's coordination object such as Durable Objects).
- **No shared memory between requests that can be relied on.** A module-level `Map` is a per-isolate, per-location cache that may vanish at any time: fine as an optimization, wrong as a source of truth.
- **Per-request secrets and bindings**, not global environment; see the portability rules above.

## Concurrency caps: protecting the database and the budget

Unbounded function concurrency is the usual cause of "too many connections" and of surprise bills. The fix is a cap at every layer.

**Database connections.** Peak connections = concurrent instances × pool size per instance. A Postgres server accepts a few hundred at most, each costing memory.

| Layer | Setting |
|---|---|
| Client pool in the function | `max: 1` on platforms that run one request per instance; a small number (up to about 5) where an instance serves many requests concurrently. Short idle timeout so frozen instances do not hold connections |
| Pooler in front of Postgres | Required: PgBouncer in transaction mode, the provider's pooler endpoint (Neon, Supabase), RDS Proxy, Hyperdrive. Point the app at the pooler; point migrations at the direct endpoint |
| Function concurrency | Cap so that `max concurrency × pool size` stays under the pooler's or database's limit with headroom for migrations and admin |

Transaction-mode pooling breaks session state: `SET` that should persist, session advisory locks, `LISTEN`, and named prepared statements unless the pooler version and driver setting support them. Symptoms are intermittent "prepared statement does not exist" errors; fix with the driver's option to disable prepared statements or the pooler's prepared-statement support. An HTTP-based driver sidesteps connection limits at the cost of interactive transactions being limited or slower. Pooler operation is in `0x:postgres-database` `postgres-operations.md`.

**Budget.** Set, per function or project: a maximum concurrency (Lambda reserved concurrency, Cloud Run `max-instances`, the PaaS's instance or concurrency limit), the shortest timeout that the slowest legitimate request needs (a hung upstream then costs seconds, not minutes), and the platform's spend limit or budget alert. A cap turns overload into throttling (HTTP 429 or 503), which is the intended outcome: decide what the client sees, and make sure webhook providers will retry. Reserve separate, smaller caps for expensive functions (LLM calls, image processing) so that abuse of one endpoint cannot consume the whole account's concurrency. Budget mechanics are in `cost-control.md`.

## Background and scheduled work

Order of preference:

1. **A few hundred milliseconds of post-response work** (logging, analytics, cache refresh): use the platform's keep-alive primitive so the instance is not frozen: `ctx.waitUntil(promise)` on Workers, `waitUntil` from the Vercel functions package, `after()` in Next.js. It extends life up to the function limit, with no retry if it fails. Never a bare un-awaited promise.
2. **Anything that must happen** (send the email, fulfill the order, process the upload): write a job or outbox row in the same transaction as the state change, or publish to a queue, and return. A consumer function processes it with retries. Choices: a Postgres-backed queue drained by a container worker or by a scheduled function; the cloud's queue (SQS, Cloud Tasks, Cloudflare Queues); or a hosted durable-execution service (Inngest, Trigger.dev, Step Functions, Cloudflare Workflows) when jobs have several steps, sleeps or fan-out.
3. **Work longer than the function limit**: checkpointed steps on a durable-execution service, or a container job (ECS or Cloud Run job, a worker on the container PaaS). Do not chain functions by having each invoke the next over HTTP; see the next section.

Scheduled work: platform cron (Vercel cron, Cloudflare Cron Triggers, EventBridge Scheduler, Cloud Scheduler). Three properties to design for: delivery is at-least-once and occasionally late or duplicated, so the job must be idempotent (claim work with a row lock or a unique run key); the endpoint is a public URL unless protected, so verify the platform's secret header or signature; and a run that outlasts its interval overlaps with the next, so take a lock or make each run process a bounded batch. Never rely on `setInterval` or an in-process scheduler in a function. Job design itself is in `0x:backend-architecture` `background-jobs.md`.

Queue consumers on Lambda-style platforms: set the queue's visibility timeout to several times the function timeout (AWS recommends at least six times), report per-message failures (partial batch response) so one bad message does not replay the whole batch, set a maximum receive count with a dead-letter queue, and alarm on dead-letter depth and on the age of the oldest message.

## Recursive triggers and retry loops

The expensive incidents are loops: each invocation causes at least one more, at machine speed, until someone notices the bill.

| Loop | How it arises | Guard |
|---|---|---|
| Storage trigger writes to its own source | A function fires on object creation and writes its output (thumbnail, converted file) to the same bucket | Separate output bucket; if impossible, a prefix or suffix filter on the trigger plus an explicit check in code that returns early on already-processed keys |
| Database trigger or stream updates the same table | A change handler updates the row it was triggered by | Compare old and new values and exit when the handler's own field changed; write derived data to another table |
| Queue poison message | A message that always fails is retried forever | Maximum receive count and a dead-letter queue on every queue; a maximum event age on async invocations |
| Function calls itself or a peer over HTTP, including through a webhook | A handler triggers an action whose webhook invokes the same handler | Carry a hop counter or origin marker in a header or payload and refuse above a small depth; ignore events caused by the system's own API key |
| Retry amplification | Client retries × gateway retries × function retries × SDK retries multiply | Retry at one layer only, with exponential backoff, jitter and a cap; make handlers idempotent so a retry is harmless (`0x:api-design` `idempotency-rate-limits.md`) |
| Unbounded fan-out | One event enqueues N events, each of which enqueues N more | Bound N in code; cap consumer concurrency |

Platform loop detection exists on some services for some trigger combinations; treat it as a backstop, not a design. The independent defenses are the same as for budget: a concurrency cap on every function (bounds the burn rate), a billing alarm with a short evaluation window on invocation count, and a rehearsed kill switch. Know the kill switch before it is needed: set the function's concurrency to zero (`aws lambda put-function-concurrency --function-name <name> --reserved-concurrent-executions 0`), disable the trigger or event source mapping, or pause the project on the PaaS. Purge or redirect the queue afterwards, or the loop resumes when the cap is lifted.

## Ask the user

- **What should users see when the concurrency cap is hit: an error, a queue, or slower responses?** Caps are mandatory; the behavior at the cap is a product decision. Default: 503 with `Retry-After` for interactive requests, queueing for webhooks and background work.
- **What monthly spend on functions and metered APIs would be alarming, and should the project pause automatically when reached?** Sets caps and whether a hard stop is acceptable for the business. Default: alert at 50 and 100 percent of a stated budget; hard pause only at Prototype.
- **Is occasional loss of post-response work (analytics events, non-critical emails) acceptable?** Decides `waitUntil` versus a queue. Default: acceptable for analytics, not for anything the user was told would happen.
- **Is first-request latency on rarely used paths a problem worth paying for?** Decides provisioned warmth. Default: pay only for sign-in, checkout and the main app shell, and only after measuring.
- **Where are most users, and where is the database?** Decides the function region and whether anything belongs at the edge. Default: one region, the database's.
