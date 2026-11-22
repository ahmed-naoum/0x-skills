# Backend latency and profiling

Read this when: an endpoint, server-rendered page or server action is slow, latency needs
tracking per endpoint, or occasional requests take far longer than the typical one.

## First split: waiting or working

A slow request is either waiting on something (database, another service, a lock, a free
connection) or burning CPU. The two need different tools, and web backends are waiting far more
often than working.

| Evidence | Meaning | Tool |
|---|---|---|
| Wall time high, process CPU low | Waiting: I/O, lock, pool, downstream | Tracing, query logs |
| Wall time high, one core pinned | CPU-bound: serialization, rendering, crypto, a loop | CPU profile, flame graph |
| Fast alone, slow under concurrency | Contention: pool, locks, event loop, rate-limited dependency | Pool and lock metrics, event-loop delay |
| Slow only sometimes, same input | Tail causes: cold start, GC, cache miss, noisy dependency | Percentiles plus per-request traces of the slow ones |

Do not start with a CPU profiler on a route that spends its time in `await`; the flame graph
will be nearly empty and say nothing.

## Find the slow span

The procedure for one slow endpoint:

1. **Reproduce with production-sized data.** Most slow endpoints are fast on a development
   database with 50 rows. Use the largest account's data on staging, or measure in production.
2. **Get a per-request breakdown.** With OpenTelemetry tracing in place, open the trace of a
   slow request and read the spans: each query, each outbound HTTP call, with durations and
   whether they ran one after another. Without tracing, wrap the suspects with timers and emit
   one structured log line per request, or a `Server-Timing` header visible in browser DevTools.
3. **Count the queries.** Log the number of queries per request. A count that grows with the
   number of rows returned is an N+1: one query for the list, one per item. Fix with a join, an
   `IN (...)` batch, or the ORM's eager loading. This is the single most common finding.
4. **Classify what the trace shows:**

| Trace shape | Cause | Fix |
|---|---|---|
| One long database span | Slow query: missing index, large scan, sort without index | `EXPLAIN (ANALYZE, BUFFERS)`, then `0x:postgres-database` |
| Dozens or hundreds of short database spans | N+1, or a per-item loop | Batch |
| Several independent spans in sequence | Sequential awaits | Run in parallel (below) |
| One long outbound HTTP span | Slow third party | Timeout, cache, move out of the request path to a job; see `0x:backend-architecture` |
| A gap before the first query | Waiting for a pool connection, cold start, or middleware (auth lookup, session fetch) | Measure pool acquire time; cache or shorten the middleware |
| A query that is fast alone but slow in the trace | Lock wait behind another transaction | Lock diagnostics (tail section) |
| Gaps with no span at all | CPU work or event-loop blocking in own code | CPU profile |
| Everything fast, response still slow | Serialization, compression, or a huge payload | Payload section |

5. **Fix the largest span, measure again.** Stop when the endpoint meets its budget; the second
   and third causes are often not worth their complexity.

Repeated identical lookups inside one request (the same user or permissions row fetched by
several layers) should be loaded once per request and passed down or memoized per request; in
React server rendering, `cache()` does this for the duration of one render.

## Run independent I/O in parallel

Sequential awaits add up; parallel awaits cost the slowest one.

```ts
// 3 round trips in sequence: a + b + c
const user = await getUser(id);
const orders = await getOrders(id);
const flags = await getFlags(id);

// In parallel: max(a, b, c)
const [user, orders, flags] = await Promise.all([getUser(id), getOrders(id), getFlags(id)]);
```

Rules:

- Parallelize only calls that do not depend on each other's results. A dependent chain is a
  design problem: fetch the dependency in the same query, or carry the needed id in the session.
- `Promise.all` rejects on the first failure while the others keep running. When partial results
  are acceptable (an optional recommendations block), use `Promise.allSettled` and degrade.
- Do not start promises and await them one by one later; if a later one rejects before it is
  awaited, the rejection is unhandled. Pass them to `Promise.all` together.
- Each parallel query takes its own pool connection. Ten parallel queries per request times
  twenty concurrent requests is two hundred connections wanted from a pool of ten: the requests
  now queue for connections and the endpoint is slower than before. Bound fan-out (a small
  concurrency limiter for lists), and prefer one query with a join over five parallel ones.
- Inside one database transaction, queries share a connection and run one at a time whatever
  the code says; `Promise.all` there adds nothing and can break with some drivers.
- In React server components, sibling components fetch in parallel, but awaits within one
  component, and a parent that awaits before rendering its children, are sequential. Start the
  fetches at the top and pass promises down, or split into siblings under Suspense.

## Track percentiles per endpoint

Averages hide the experience: a mean of 120 ms can sit on top of a p99 of 4 s. Track p50, p95
and p99 per route from Launch.

- Record a duration **histogram** per route template (`/orders/:id`, never the raw path, or the
  metric cardinality explodes), method and status class. OpenTelemetry HTTP server
  instrumentation produces this; the hosted backend computes the percentiles.
- Percentiles cannot be averaged or summed across instances or time windows. Aggregate the
  histograms, then compute.
- Measure at the server and, where possible, at the edge or load balancer too. The difference
  is queueing in front of the app, which the app's own timer never sees.
- Rank endpoints by **total time** (requests × mean duration) to find where the system spends
  its capacity, and by p95 to find where users suffer. They are different lists.
- A user loading a page makes many requests; the chance that at least one hits the p99 is high.
  That is why p99 matters for endpoints called several times per page view.

Slow-query logging, from Launch:

- PostgreSQL: set `log_min_duration_statement` to a threshold such as 200 to 500 ms so every
  slower statement is logged with its duration, and enable `pg_stat_statements` to rank
  statements by total and mean time. Managed providers expose both as settings or dashboards.
- In the application: log any query over the threshold with the route and a trace id, so the
  slow statement can be tied to the endpoint that issued it.
- Review the top statements by total time on a schedule (monthly at Launch); reading plans and
  indexing are in `0x:postgres-database`.

## Latency budget per hop

For each critical request (page render, checkout, search), write down the target and divide it.
A budget turns "it feels slow" into "the database hop is 3x over".

Example, as an illustration: a server-rendered page with a 500 ms p95 target for the response.

| Hop | Budget (p95) | Timeout |
|---|---|---|
| Edge, TLS, routing to origin | 50 ms | n/a |
| Auth and session lookup | 20 ms | 200 ms |
| Database, all queries together | 150 ms | Statement timeout a few seconds |
| One downstream service call | 150 ms | 1 s, then degrade |
| Render and serialization | 80 ms | n/a |
| Slack | 50 ms | n/a |

Rules:

- Budgets for sequential hops add; for parallel hops the largest counts. Draw the request as a
  small dependency graph first.
- Every outbound call gets a timeout derived from the budget, and a decision about what the
  response is when it fires (omit the block, serve stale, fail). An outbound call without a
  timeout has an unbounded budget. In Node, `fetch(url, { signal: AbortSignal.timeout(1000) })`.
- Anything that cannot fit in the budget leaves the request path: precompute it, or run it as a
  job and report progress.
- Fan-out multiplies tail risk: a request that waits on ten backends each within budget 99% of
  the time is itself within budget only about 90% of the time.
- Put the budget where it will be seen: as alert thresholds on the route's p95 and as span
  expectations in the trace view.

## CPU profiling with a flame graph

Use when the trace has unexplained gaps, a core is pinned, or event-loop delay is high.

```bash
node --cpu-prof --cpu-prof-dir=./profiles server.js     # writes a .cpuprofile on exit
```

Exercise the slow route under realistic load for a short time, stop the process, and open the
file in Chrome DevTools (Performance panel, load profile) or any flame-graph viewer. For a live
process, start it with `--inspect` and record from DevTools; in production prefer a continuous
profiler from the telemetry vendor over attaching a debugger. Profile a production build with
production-like data.

Reading: width is time on CPU, the vertical axis is the call stack. Look for wide plateaus
(functions with large self time) and for a wide parent made of many narrow identical children
(a hot loop). Ignore depth.

Usual hot paths in a Node web backend:

| Hot frame | Fix |
|---|---|
| `JSON.stringify` or `JSON.parse` on large objects | Smaller payloads, pagination, streaming; do not parse and re-serialize pass-through data |
| ORM row hydration for thousands of rows | Select fewer columns and rows; raw query for bulk reads |
| Schema validation of huge arrays | Validate at the boundary once; validate the envelope and sample or stream the items |
| Synchronous crypto, password hashing, compression | Async variants (which use the thread pool), or a worker |
| Regular expressions on long input | Bound input length; rewrite patterns with nested quantifiers |
| Server rendering of very large trees | Paginate, cache the rendered fragment, stream |
| Logging: serializing large objects per request | Log fields, not objects; lower the level in hot paths |
| Sorting, grouping, joining in application code | Let the database do it |

Node runs JavaScript on one thread: 200 ms of CPU in one request delays every other request on
that instance by 200 ms. Watch event-loop delay (`perf_hooks.monitorEventLoopDelay`) as a
metric; if its p99 is tens of milliseconds or more, something is blocking. Move unavoidable
heavy computation to a worker thread or a background job.

## Precompute expensive results

When a result is expensive, read often and tolerates being slightly old, compute it at write
time or on a schedule rather than at read time.

| Pattern | Use when | Cost |
|---|---|---|
| Counter or summary column maintained on write (in the same transaction) | Counts and totals shown everywhere: unread count, order total | Write path does more; contention on hot rows |
| Summary table filled by a background job | Dashboards, leaderboards, reports; minutes of staleness are fine | A job to run and monitor; define behavior when it falls behind |
| Materialized view, refreshed on schedule | The aggregate is one SQL query; whole-view refresh is affordable | Refresh recomputes everything; `REFRESH MATERIALIZED VIEW CONCURRENTLY` avoids blocking readers and needs a unique index on the view |
| Incremental rollup (per-day buckets, append only) | Time-series analytics over growing data | Late-arriving and corrected data need a recompute path |
| Result generated by a job and stored (export, PDF, AI summary) | Takes seconds or more per request | Status tracking and notification; see `0x:backend-architecture` |

Decide the staleness contract first and show it in the product if it matters ("updated 5
minutes ago"). Keep a way to rebuild the derived data from the source of truth; it will drift.
A cache differs from precomputation in that a miss still pays the full cost in a user's
request; for a five-second aggregate, that is not acceptable, so precompute. Adding Redis is
covered in `0x:data-stores`.

## Payload size and serialization

- Select only the columns and rows the response needs. `SELECT *` into a JSON response ships
  internal fields, costs serialization time and leaks data.
- Paginate every list endpoint; an unbounded list is fast until the largest customer uses it.
  Contracts for pagination are in `0x:api-design`.
- Compress text responses over about 1 KB (Brotli or gzip, usually at the CDN or proxy). Do not
  compress images, video or already-compressed files.
- In React server rendering, props passed from server to client components are serialized into
  the document. Passing full records where three fields are used inflates HTML and hydration.
- Avoid double work: parsing a downstream JSON body only to stringify it again, or converting
  between shapes several times per request.
- Large exports and feeds: stream rows to the response instead of building one array in memory.
- Support conditional requests (`ETag` with `304`) for large, rarely changing resources.

Check: `curl -s -o /dev/null -w '%{size_download} bytes  %{time_starttransfer}s\n' -H 'Accept-Encoding: br, gzip' <url>`.
A JSON response over a few hundred KB compressed deserves a design question, not tuning.

## Tail latency

When p50 is fine and p99 is many times worse, look for something intermittent.

| Cause | Signature | Confirm | Fix |
|---|---|---|---|
| Cold start (serverless, scale-to-zero) | First request after idle or during scale-out is slow | Slow requests correlate with new instances | Minimum instances or provisioned concurrency; smaller server bundle; lazy-init heavy clients |
| Connection pool wait | Latency climbs with concurrency while the database is not busy | Measure time to acquire a connection; pool "waiting" count above zero | Shorter transactions; no outbound calls while holding a connection; right-size the pool; a pooler in front of Postgres for serverless |
| Lock contention | A normally fast write or query sometimes waits seconds | Postgres `log_lock_waits`, `pg_stat_activity` wait events, long-running transactions | Short transactions, consistent lock order, `lock_timeout`; see `0x:postgres-database` |
| Garbage collection | Pauses grow with heap size; memory sawtooth | `node --trace-gc`, GC metrics from the runtime | Allocate less per request, stream large data, fix leaks; raise the heap limit only with memory to spare |
| Event-loop blocking | All requests on one instance stall together | Event-loop delay metric spikes | CPU profile; move work off the loop |
| Cache miss or expiry stampede | Periodic spikes at expiry times; many identical recomputations at once | Miss rate against latency | Serve stale while revalidating; one recomputation per key; jitter on lifetimes |
| New connections per request | Extra handshake time on outbound calls | Connect time in traces | Reuse clients and keep-alive; create SDK clients once per process |
| Retries and timeouts downstream | Latency clusters at the timeout value or its multiples | Histogram has a second hump | Tighter timeouts, hedging only for idempotent reads |
| Noisy neighbors, throttled CPU | Slow at random on shared or burstable instances | CPU steal or throttling metrics | Different instance class |

Investigate with traces of the slow requests themselves (keep slow and failed traces even when
sampling the rest); a dashboard average cannot explain a tail.

## Ask the user

- **Which requests are critical, and what is the target for each?** Budgets need a number.
  Default: p95 under 500 ms for page responses and under 300 ms for interactive API calls;
  background and export operations are jobs with progress.
- **How stale may aggregates be?** Decides between live queries and precomputation. Default:
  dashboards and counts up to a few minutes old, anything financial exact.
- **What should happen when a dependency is slow?** Omit, serve stale or fail is a product
  decision. Default: degrade optional blocks, fail fast with a clear message for required ones.
- **Is paying for warm instances acceptable?** Removing cold starts costs money every hour.
  Default: one warm instance for user-facing routes at Launch.
