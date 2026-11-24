# Language, runtime and process model

Read this when: choosing a backend language or JavaScript runtime, or when a server process blocks,
pauses under load, runs out of memory, or drops requests when it is stopped.

## Choosing the language

Decide in this order and stop at the first rule that answers.

1. The project already has a backend: stay in its language. A rewrite buys nothing a user can see.
2. The founder knows one stack deeply (Rails, Django, Laravel, .NET, JVM): use it. A
   batteries-included framework known well beats the house default learned on the job.
3. The workload forces a choice (table below).
4. Otherwise TypeScript on Node.js, in the same repository as the frontend.

| Workload | Choice | Why | Main trap |
|---|---|---|---|
| Typical product: CRUD, APIs, I/O-bound | TypeScript on Node | One language, types and validation schemas shared with the UI | CPU work blocks the single thread |
| ML, data science, scientific libraries | Python (FastAPI) as a service beside the TypeScript app | The libraries exist only there | CPU parallelism needs processes; a sync call inside an async handler blocks the loop exactly as in Node |
| Very many long-lived connections, proxies, CPU work per request, binaries shipped to customers | Go | Uses every core without ceremony, static binary, small memory | No shared types with the UI: generate clients from an OpenAPI or protobuf contract |
| One measured hot path (media, parsing, compression) | Rust as a library or small service | No GC pauses, predictable memory | Slow to write; never the CRUD layer |

A second language enters as a separate service for one capability, never as a parallel
general-purpose backend. Its cost is a second CI pipeline, dependency audit stream, image and
runbook, plus a network contract where there was a function call. Calling an LLM API is not a
reason for Python: the TypeScript SDKs are first-class.

## JavaScript runtime: Node.js, Bun or Deno

| Runtime | Run production on it when | Watch for |
|---|---|---|
| Node.js, an LTS line | Default | Nothing else to check: every library, host and APM agent targets it first |
| Bun | The project already runs on it, or fast startup and built-in tooling matter and the whole dependency set and test suite pass on it | Node API coverage is high but not complete; native addons, auto-instrumentation and some frameworks lag; differences tend to show under load, not in unit tests |
| Deno | The permission sandbox (`--allow-net=host`, `--allow-read=path`) is wanted for semi-trusted code, or the target is its hosting platform | npm packages work through `npm:` specifiers and `package.json`, but packages with native addons or deep Node internals can fail |

Bun for development with Node in production means two runtimes that must agree: do it for a
measured gain only. Edge runtimes: `0x:cloud-infrastructure` (`serverless-edge.md`).

Pin the runtime in every place that reads it, and make them agree:

- `.nvmrc` or `.node-version` (CI reads it: `node-version-file` in `actions/setup-node`).
- `engines.node` in `package.json`, and `packageManager` for the exact pnpm version.
- The Docker base image tag (major at minimum, digest for reproducible builds). Prefer a
  Debian-slim image over Alpine when native modules are involved: musl builds are a recurring
  source of install failures and slow fallbacks.
- The host's runtime setting on a PaaS.

Drift shows up as "works locally, fails in CI" with a syntax error or a missing API. Run a line
that is in LTS: through Node 26 only even majors reach it and odd ones lose support within
months; from Node 27 there is one major a year, LTS from October (confirm on the nodejs.org
release schedule). Move to a new LTS a few months after it is declared, before the old line
reaches end of life. Node 25 and later do not bundle Corepack: install pnpm explicitly.

## Built-ins before dependencies

Check the pinned runtime's documentation before adding a utility package. Each dependency is
supply-chain surface and an upgrade to track.

| Need | Built-in | Usually replaces |
|---|---|---|
| HTTP client with timeout | `fetch`, `AbortSignal.timeout(ms)`, `AbortSignal.any([...])` | axios, node-fetch, got |
| IDs and random tokens | `crypto.randomUUID()`, `crypto.randomBytes(n)` | uuid |
| HMAC, hashes, constant-time compare | `node:crypto` (`createHmac`, `createHash`, `timingSafeEqual`), `crypto.subtle` | crypto-js |
| Load `.env` | `node --env-file=.env`, `--env-file-if-exists`, `process.loadEnvFile()` | dotenv |
| Restart on change | `node --watch` | nodemon |
| Run TypeScript | Type stripping (next section) | ts-node, tsx for most scripts |
| CLI flags | `util.parseArgs` | yargs, commander for small tools |
| Deep copy | `structuredClone` | lodash.clonedeep |
| Sleep, timers | `node:timers/promises` | delay |
| Piping with backpressure | `pipeline` from `node:stream/promises` | pump |
| Paths in ESM | `import.meta.dirname`, `import.meta.filename` | `fileURLToPath` boilerplate |
| WebSocket client | global `WebSocket` | ws on the client side (a server still needs a library) |
| Package scripts | `node --run <script>` | calling the package manager for trivial scripts |

Keep the library where the built-in is thinner than the job: schema validation (Zod), structured
logging (pino), the Postgres driver, password hashing (owned by the auth library), and date and
time-zone math unless the pinned runtime has `Temporal` (on by default from Node 26). `node:test`
is fine for a small package; an app that already uses Vitest keeps Vitest.

## Running TypeScript directly in Node

Current LTS lines execute `.ts` files by erasing the types (older 22.x releases need
`--experimental-strip-types`). Erasure does not type-check and does not read `tsconfig.json`. It
suits workers, scripts, CLIs and a standalone API service; a Next.js app is compiled by its own
bundler and is unaffected.

```jsonc
// tsconfig.json: the options that keep code runnable by type stripping
{
  "compilerOptions": {
    "target": "esnext",
    "module": "nodenext",
    "noEmit": true,
    "strict": true,
    "erasableSyntaxOnly": true,              // rejects enum, namespace, parameter properties
    "verbatimModuleSyntax": true,            // forces `import type` for type-only imports
    "rewriteRelativeImportExtensions": true  // lets imports be written as "./x.ts"
  }
}
```

- Set `"type": "module"` in `package.json` and write ESM only. Relative imports carry the real
  extension (`./user.ts`); there is no directory-index or extensionless resolution.
- `paths` aliases are not resolved at run time. Use `"imports"` in `package.json` (`"#db/*":
  "./src/db/*"`), which Node and TypeScript both honor.
- Replace `enum` with an `as const` object plus a union type. Decorators are not supported.
- Files under `node_modules` are not stripped: a published package ships JavaScript.
- Type errors never stop execution. `tsc --noEmit` runs in CI and before commit, always.
- Positions are preserved (types become whitespace), so stack traces need no source maps.
- JSON imports need the attribute: `import cfg from './cfg.json' with { type: 'json' }`.
- CommonJS dependencies import fine from ESM. Going the other way, current LTS lines can
  `require()` an ESM module only if its graph has no top-level `await`.

Bundling (esbuild, tsup) still pays for serverless cold starts and small images, not for running.

## Keeping the event loop unblocked

Fifty milliseconds of synchronous work in one request delays every other request in flight by
fifty milliseconds. Measure before guessing:

```ts
import { monitorEventLoopDelay } from 'node:perf_hooks';

const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();
setInterval(() => {
  // Values are ns and include the 20 ms sampling interval: an idle loop reads about 20 ms.
  metrics.gauge('event_loop_delay_p99_ms', Math.max(0, h.percentile(99) / 1e6 - 20));
  h.reset();
}, 10_000).unref();
```

Rule of thumb: p99 loop delay under 20-50 ms is healthy; sustained over 100 ms is user-visible;
over about a second, health checks time out and the orchestrator restarts the process, which is
the usual cause of "random restarts under load".

| Blocker | Fix |
|---|---|
| `JSON.parse` or `stringify` of multi-megabyte bodies | Cap body size, paginate, or stream newline-delimited JSON |
| `*Sync` calls on the request path (`readFileSync`, `pbkdf2Sync`, `gzipSync`) | Async variants, which run on the libuv thread pool |
| Regex with nested quantifiers on user input | Bound input length before matching; rewrite the pattern or use a linear-time engine (RE2) |
| Sorting, grouping or joining large arrays in memory | Do it in SQL; otherwise chunk and yield with `await setImmediate()` from `node:timers/promises` |
| A long `for await` loop that only resolves promises | Microtasks never yield to I/O: yield explicitly every N items |
| Image, PDF, spreadsheet or CSV processing | Background job or worker thread |

The libuv thread pool has four threads by default, shared by `fs`, `dns.lookup`, async crypto
(`pbkdf2`, `scrypt`, `randomBytes`) and zlib. Symptom: CPU is idle, yet file reads and outbound
requests (which resolve DNS) stall while password hashing or compression runs. Raise
`UV_THREADPOOL_SIZE` in the process environment, or move the hashing elsewhere.

A full database pool looks the same from outside: every request waits for a connection. Check
pool wait time before blaming the loop. `node --cpu-prof` writes a profile that Chrome DevTools
opens; profiling method is in `0x:web-performance` (`backend-latency.md`).

## Where CPU-heavy work goes

| CPU time per operation | Place |
|---|---|
| Under about 10 ms | Inline |
| 10-100 ms and the response needs the result | Worker-thread pool (piscina) |
| Over 100 ms, or the response does not need the result | Background job on a separate worker process (`background-jobs.md`) |
| Sustained heavy work: video, inference, large data crunching | A managed service, or a small service in a runtime built for it |

Each worker thread is a separate V8 isolate with its own heap (tens of megabytes) and a startup
cost, so pool them and never spawn one per request. Data crossing the boundary is copied by
structured clone: transfer `ArrayBuffer`s or pass a storage key instead of a large object. Size
the pool at cores minus one, bound its queue, and reject when full, or memory grows without
limit. On a one-vCPU instance a worker thread keeps the loop responsive but adds no capacity.
Native addons such as sharp already run off the main thread.

## Sizing workers, threads and pools

- **Node web processes**: one per vCPU. Scale with platform replicas; use `cluster` or a process
  manager only on a single VM. Fractional-vCPU instances are fine for I/O-bound work, but CPU
  throttling shows up as p99 spikes during GC and TLS handshakes.
- **Memory**: container limit = V8 heap limit plus 25-30% for buffers, native memory and stacks.
  Set `--max-old-space-size` (in MB) explicitly to about 70-75% of the container limit.
- **Database pool**: `web instances x pool max + workers x pool max <= max_connections - reserve`
  (reserve for migrations, admin and replication). Start at 5-10 per Node process. Past a small
  multiple of the database's cores, more active connections add contention, not throughput:
  let requests queue in the pool with an acquire timeout. Autoscaled or serverless compute needs
  a pooler in front of Postgres (`0x:postgres-database`, `postgres-operations.md`).
- **Job workers**: concurrency for I/O jobs is set by downstream limits (pool size, third-party
  rate limits); for CPU jobs it equals cores.
- **Python**: Gunicorn sync workers about `2 x cores + 1` (rule of thumb for I/O-bound apps);
  async workers one per core. Each worker is a process with its own memory and its own pool.
- **Go**: `GOMAXPROCS` must match the container CPU limit (Go 1.25 and later read the cgroup
  limit; older ones need `automaxprocs`), and `GOMEMLIMIT` about 90% of container memory.

`os.availableParallelism()` may report host cores instead of the container's quota: take worker
counts from an environment variable set next to the CPU limit. Confirm any sizing with a load
test: capacity is where p99 bends, not where CPU reaches 100%.

## Graceful shutdown

Deploys, scale-downs and node replacements send SIGTERM, then SIGKILL after a grace period (a few
seconds to 30 s by default, by platform: read it). The order of steps is what people get wrong.

1. On SIGTERM, fail the readiness check (503) and keep serving.
2. Wait until the load balancer stops routing here: its deregistration step, or check interval ×
   failure threshold where it learns from health checks (10 s is a starting value;
   `0x:web-networking`). On Kubernetes, endpoint removal races the signal, so a `preStop` sleep
   or this in-process wait is required.
3. Stop accepting: `server.close()`. Close idle keep-alive connections.
4. Stop fetching jobs; let running jobs finish or release them to the queue.
5. Wait for in-flight work with a deadline a few seconds shorter than the platform's grace period.
6. Close the queue client, database pool and Redis; flush logs, traces and the error tracker.
7. Exit 0. A hard timer forces exit 1 if anything hangs.

```ts
let shuttingDown = false; // the readiness handler returns 503 once this is true

async function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  setTimeout(() => process.exit(1), 25_000).unref();   // below the platform grace period
  await sleep(10_000);                                 // load balancer drains
  const closed = new Promise<void>((resolve) => server.close(() => resolve()));
  const idle = setInterval(() => server.closeIdleConnections(), 1_000);
  await closed;
  clearInterval(idle);
  await worker.stop();
  await pool.end();
  process.exit(0);
}
process.on('SIGTERM', () => void shutdown());
process.on('SIGINT', () => void shutdown());
```

| Symptom | Cause | Fix |
|---|---|---|
| Handler never runs; container dies after the full grace period | `CMD npm start`, `pnpm start` or shell-form `CMD`: the wrapper is PID 1 and does not forward the signal | Exec form `CMD ["node", "server.js"]`; add an init (`--init`, tini) if the process spawns children |
| A few 502s on every deploy | Process exits while the balancer still routes to it | Steps 1-2; check the balancer's deregistration delay |
| Sporadic 502s with no deploy | Node closes idle keep-alive sockets before the balancer does. The default was 5 s for years and was raised to 65 s in 2026; the first line that ships it varies: print `server.keepAliveTimeout` on the pinned runtime | Set `server.keepAliveTimeout` explicitly above the balancer idle timeout, and `server.headersTimeout` above that |
| Shutdown hangs until SIGKILL | WebSocket or SSE connections never end on their own | Send a close frame or end the stream; clients reconnect elsewhere |
| Jobs run twice after deploys | Job longer than the grace period is killed, then retried | Make it resumable and idempotent, or raise the grace period for the worker service |

Frameworks that own the server expose their own hook (Fastify `app.close()`; self-hosted Next.js
installs signal handlers unless `NEXT_MANUAL_SIG_HANDLE` is set). Serverless functions get no
useful SIGTERM: flush per invocation. Prove the result by running a load generator through a
deploy and counting non-2xx responses; the target is zero. Deploy mechanics are in
`0x:ci-cd-release` (`deploy-rollback.md`).

## Deadlines and cancellation

Give each request one deadline at the edge and pass it down as an `AbortSignal`; every outbound
call and long loop takes the signal.

```ts
const signal = AbortSignal.any([request.signal, AbortSignal.timeout(8_000)]);
const res = await fetch(url, { signal });
```

- Fetch-style handlers (Next.js route handlers, Hono) expose `request.signal`, meant to abort
  when the client disconnects; with `node:http`, abort from `res.on('close')` when
  `res.writableFinished` is false. Hosts and proxies differ in whether the disconnect arrives:
  close a client mid-request on the real deployment and log the abort before relying on it.
- Aborting closes the caller's side only. The upstream may still complete the action, and a
  Postgres query keeps running unless a cancel is sent: set `statement_timeout` as the backstop.
- Check for cancellation between steps and around reads, expensive computation and LLM streams
  (abort the upstream stream so tokens stop being billed). Never abandon a state-changing
  sequence halfway: finish it or let the transaction roll back.
- At every hop the downstream timeout is shorter than the upstream one. Otherwise the caller
  gives up while the callee keeps working, which is how overload feeds itself. Between services,
  send the remaining budget in a header (gRPC carries deadlines natively).
- `AbortSignal.timeout` rejects with `TimeoutError`, a manual abort with `AbortError`
  (`err.name`). Map a timeout to 504; log a client disconnect at info level and keep it out of
  the error tracker.

## Garbage collection and memory limits

| Symptom | Cause | Fix |
|---|---|---|
| Killed with exit code 137 (OOMKilled), no JavaScript error | Container limit reached before V8's heap limit, or native memory grew | Set `--max-old-space-size` to about 70-75% of the limit |
| `JavaScript heap out of memory` | Heap limit reached: a leak, or a whole dataset buffered | Stream instead of buffering; take heap snapshots; raise the limit only for legitimately large data |
| Periodic p99 bumps with sawtooth memory | Major GC pauses on a large heap, or constant scavenges from a high allocation rate | Allocate less on the hot path; raise `--max-semi-space-size` (MB) for allocation-heavy servers; prefer more instances with small heaps over one large heap |
| RSS grows while `heapUsed` stays flat | Buffers, native addons or glibc arena fragmentation | Inspect `external` and `arrayBuffers` in `process.memoryUsage()`; set `MALLOC_ARENA_MAX=2` or use jemalloc |
| Slow growth over days | Unbounded `Map` cache, listeners added per request, closures held by timers | Diff two heap snapshots taken minutes apart; bound every cache with size and TTL |

`--trace-gc` prints each collection with its pause; a `PerformanceObserver` on `gc` entries turns
that into a metric. `--heapsnapshot-near-heap-limit=2` writes snapshots as the limit approaches,
and `--heapsnapshot-signal=SIGUSR2` on demand. A snapshot pauses the process for seconds and
needs memory and disk about the size of the heap, so take the instance out of rotation first.
Export RSS, `heapUsed`, GC pause time and event-loop delay together: they explain each other.

Scheduled restarts hide a leak; that is an acceptable stopgap at Launch if an alert on memory
slope exists, and it is not a fix. In Python, recycle workers with `--max-requests` plus
`--max-requests-jitter` so they do not all restart at once.

## Ask the user

- **Is there an existing backend or a language you know deeply?** It outranks every default here.
  Assume TypeScript on Node if there is neither.
- **Will the product need ML models, heavy data processing or media work in-house?** It decides
  whether a Python or Go service appears beside the main app. Assume no; call managed APIs.
- **Where will it run: serverless functions or long-running processes?** Worker threads,
  WebSockets, in-process pools and SIGTERM handling only apply to the second. Assume a
  long-running process on a PaaS.
- **What is the longest task that must survive a deploy?** It sets the grace period and whether
  work must be made resumable. Assume 30 seconds and make anything longer a resumable job.
- **How much is p99 latency worth?** Fractional-vCPU instances are cheaper and spikier. Assume one
  full vCPU per web instance at Launch.
