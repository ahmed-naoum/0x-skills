# Rust, Tokio and the process model

Read this when: the server stalls under load or one slow request freezes the others, spawned tasks
leak or die without a trace, a deploy drops requests or jobs, memory keeps growing, or compile
times and the Cargo workspace layout slow the team down.

## Workspace layout

Rust on Tokio is the default. Keep an existing backend's language rather than rewrite it; add a
second language only as a small service for a library that exists nowhere else, such as model
training (`architecture-shape.md`). An LLM API is not such a reason (`0x:ai-features`).

```text
Cargo.toml            [workspace] members, [workspace.dependencies], [workspace.lints], profiles
rust-toolchain.toml   pinned toolchain, read by rustup on laptops and in CI
crates/
  domain/   newtypes, state machines, typed errors; no IO crates; also compiles to WASM
  data/     SQLx pool, queries per capability, migrations/, .sqlx/ offline query data
  app/      use cases per capability (billing/, projects/), on domain and data
  web/      Axum router, extractors, the one error-to-response mapping, the Leptos app
  server/   the binary: config, telemetry, runtime, subcommands serve | worker | migrate
```

| Rule | Reason |
|---|---|
| Dependencies point down: server, web, app, data, domain | Cargo rejects cycles between crates, so the direction is enforced by the compiler |
| `domain` has no tokio, sqlx or axum | Fast to test, and the Leptos client can reuse its types and validation in WASM |
| Only `data` uses the `query!` macros | They need `DATABASE_URL` or the committed `.sqlx/` data at compile time; one crate holds that cost |
| One binary with subcommands for web, worker and migrations | One image, one build, one version; the platform runs it with different commands |
| Versions declared once in `[workspace.dependencies]` | Two versions of a crate in the graph double its compile time and cause "expected `X`, found `X`" errors |
| `#![forbid(unsafe_code)]` in every application crate | Unsafe needs a reviewed reason (`0x:code-quality`, `static-analysis-types.md`) |

At Prototype one crate with these as modules is fine. Split at Launch, or once an incremental
`cargo check` after a one-line change takes over about ten seconds (rule of thumb). Crates split
by dependency weight; modules inside them by business capability (`architecture-shape.md`).

## Keeping the runtime unblocked

Tokio runs many tasks on a few worker threads and switches only at `.await`. A task that computes
or blocks without awaiting holds its thread, and every task queued behind it waits, health checks
and timers included. Rule of thumb from Tokio's maintainers: 10-100 microseconds at most between
`.await` points.

| Blocker | Fix |
|---|---|
| CPU work: password hashing, images, PDFs, compression, multi-megabyte JSON, large sorts | `spawn_blocking` under a semaphore (below); parallel number crunching on a rayon pool fed by a bounded channel |
| Blocking IO: `std::fs` on large files, `std::thread::sleep`, `reqwest::blocking`, synchronous SDKs or database drivers | The async equivalent (`tokio::fs`, `tokio::time::sleep`, async `reqwest`), or `spawn_blocking` |
| A loop over many items with no `.await` | Do it in SQL; otherwise move it to `spawn_blocking` |
| `Runtime::block_on` inside async code | Panics ("cannot start a runtime from within a runtime"); restructure so the caller awaits |
| Regex on user input | The `regex` crate is linear-time; bound the input length anyway |

```rust
use std::sync::Arc;
use tokio::{sync::Semaphore, task::JoinError};

#[derive(Debug, thiserror::Error)]
pub enum CpuError {
    #[error("cpu pool closed")] Closed,
    #[error("cpu task panicked")] Panicked(#[source] JoinError),
}

/// CPU-heavy work off the async workers, at most `max_parallel` at a time.
#[derive(Clone)]
pub struct CpuPool(Arc<Semaphore>);

impl CpuPool {
    pub fn new(max_parallel: usize) -> Self { Self(Arc::new(Semaphore::new(max_parallel))) }

    pub async fn run<T, F>(&self, f: F) -> Result<T, CpuError>
    where
        F: FnOnce() -> T + Send + 'static,
        T: Send + 'static,
    {
        let _permit = self.0.acquire().await.map_err(|_| CpuError::Closed)?;
        tokio::task::spawn_blocking(f).await.map_err(CpuError::Panicked)
    }
}
```

- The blocking pool grows to 512 threads by default. CPU work there without a bound
  oversubscribes the cores; size the semaphore near the core count.
- A `spawn_blocking` closure cannot be cancelled. A timeout around it frees the caller, not the
  thread.

Measure instead of guessing: a probe task sleeps 250 ms in a loop and records how late it wakes.
Rule of thumb: p99 lag under 10 ms is healthy, sustained over 100 ms is user-visible, and over
about a second health checks time out and the orchestrator restarts the process ("random restarts
under load"). `tokio-console` shows which task polls too long (it needs the `tokio_unstable` build
flag: staging, not production). A full database pool looks the same from outside, so check pool
wait time first. Profiling method: `0x:web-performance` (`backend-latency.md`).

## Locks and `.await`

| Lock | Use when | Trap |
|---|---|---|
| `std::sync::Mutex`, `RwLock` | Short critical sections with no `.await` inside | The guard is not `Send`: held across `.await` in a handler or spawned task, it fails to compile ("future cannot be sent between threads safely"). In a non-`Send` context it compiles and can deadlock the thread |
| `tokio::sync::Mutex` | The lock must be held across `.await` (one connection, ordered writes to one file) | Compiles everywhere, so a guard held across a slow network call silently serializes every caller |
| One task owning the state, fed by a bounded `mpsc` with `oneshot` replies | Long or IO-bound work on shared state | One more task to supervise |
| `moka`, `dashmap` | Hot caches and maps | A `dashmap` reference held across `.await` blocks its whole shard |

Release the guard in a block before awaiting, so the scope shows it:

```rust
use std::{collections::HashSet, sync::Mutex};

pub struct Seen(Mutex<HashSet<u64>>);

pub async fn first_visit(seen: &Seen, http: &reqwest::Client, user: u64) -> reqwest::Result<()> {
    let is_new = {
        let mut set = seen.0.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
        set.insert(user)
    }; // guard dropped here, before any .await
    if is_new { http.post("https://crm.example.com/visits").send().await?; }
    Ok(())
}
```

## Supervising spawned tasks

Dropping a `JoinHandle` detaches the task: a panic goes to stderr and nowhere else, a returned
error goes nowhere, and the task keeps running through shutdown.

- Spawn every long-lived task (job worker, outbox relay, lag probe, pub/sub listener) into a
  `JoinSet` owned by `main`. Any exit before shutdown is an incident: log it, then exit so the
  platform restarts the process (shutdown snippet below).
- `JoinError::is_panic()` separates a panic from a cancellation. A panic hook that reports to
  the error tracker (Sentry's panic integration) catches the panics nobody joins.
- A per-request `tokio::spawn` that must outlive the response is a job queue without
  persistence: enqueue a job instead (`background-jobs.md`).
- A handler panic drops that connection (a reset, or a 502 from the proxy); tower-http's
  `CatchPanicLayer` (feature `catch-panic`) turns it into a logged 500. Keep unwinding:
  `panic = "abort"` in the release profile turns one request's panic into a process crash.
- `unwrap()` and `expect()` on request data are panics waiting for input. Return typed errors;
  clippy's `unwrap_used` lint, denied in `app` and `web`, keeps them out.

## Bounding concurrency

Every spawn per item, unbounded channel and `join_all` over a user-sized list is a queue whose
only bound is memory.

| Unbounded | Bounded |
|---|---|
| `tokio::spawn` per message or row | A `Semaphore` permit acquired before spawning |
| `join_all(urls.map(fetch))` | `futures::stream::iter(urls).map(fetch).buffer_unordered(8)` |
| `mpsc::unbounded_channel()` | `mpsc::channel(n)`: `send().await` waits when full (backpressure), `try_send` fails fast (shed) |
| `broadcast` with slow receivers | Bounded already: it drops for laggards and reports `Lagged`; resync the receiver (`realtime.md`) |
| Requests in flight | tower concurrency limit plus load shedding (`integrations-resilience.md`) |

Use `send().await` where the producer can wait (a pipeline of jobs) and `try_send` where it cannot
(fan-out to WebSocket clients: drop the slow client, not the server).

## Sizing threads and pools

- **Tokio workers**: one per CPU detected. Set `TOKIO_WORKER_THREADS` next to the container's CPU
  limit rather than trusting detection of a fractional quota. One process per container: Tokio
  already uses every core.
- **Blocking pool**: leave `max_blocking_threads` at its default and bound CPU work with the
  semaphore above.
- **Database pool**: `web instances x max + workers x max <= max_connections - reserve` (reserve
  for migrations, admin, replication). Start at 10 per process, SQLx's default. Past a small
  multiple of the database's cores, more active connections add contention, not throughput.
  Autoscaled or serverless compute needs a pooler (`0x:postgres-database`,
  `postgres-operations.md`).
- **Acquire timeout**: SQLx waits 30 s for a connection by default; at about 3 s
  (`PgPoolOptions::acquire_timeout`) a saturated pool fails fast instead of piling up requests.
- **Job workers**: concurrency per queue follows downstream limits (pool size, vendor rate
  limits); CPU-bound jobs get one per core.

Confirm with a load test: capacity is where p99 bends, not where CPU reaches 100%.

## Graceful shutdown

Deploys and scale-downs send SIGTERM, then SIGKILL after a grace period (a few seconds to 30 s by
platform: read it). The order is what people get wrong:

1. On SIGTERM, fail the readiness check (503) and keep serving.
2. Wait until the balancer stops routing here, 10 s to start (`0x:web-networking`); on Kubernetes
   endpoint removal races the signal.
3. Stop accepting; finish in-flight requests.
4. Stop claiming jobs; end SSE and WebSocket streams, or step 3 never completes.
5. Wait with a deadline a few seconds shorter than the grace period.
6. Close the pool; flush logs, traces and the error tracker. Exit.

```rust
use std::sync::{Arc, atomic::{AtomicBool, Ordering}};
use std::time::Duration;
use axum::{Router, http::StatusCode, routing::get};
use tokio::{net::TcpListener, signal::unix::{SignalKind, signal}, task::JoinSet};
use tokio_util::sync::CancellationToken;

pub async fn run(listener: TcpListener, app: Router, pool: sqlx::PgPool) -> anyhow::Result<()> {
    let ready = Arc::new(AtomicBool::new(true));
    let probe = ready.clone();
    let app = app.route("/readyz", get(move || async move {
        if probe.load(Ordering::Relaxed) { StatusCode::OK } else { StatusCode::SERVICE_UNAVAILABLE }
    }));
    let (stop_http, stop_work) = (CancellationToken::new(), CancellationToken::new());
    let mut tasks: JoinSet<anyhow::Result<()>> = JoinSet::new();
    let work = stop_work.clone();
    tasks.spawn(async move { work.cancelled().await; Ok(()) }); // ... the job worker loop
    let stop = stop_http.clone();
    let server = axum::serve(listener, app).with_graceful_shutdown(async move { stop.cancelled().await });
    tasks.spawn(async move { Ok(server.await?) });

    let mut sigterm = signal(SignalKind::terminate())?;
    tokio::select! {
        _ = sigterm.recv() => tracing::info!("SIGTERM, draining"),
        Some(exit) = tasks.join_next() => tracing::error!(?exit, "supervised task ended early"),
    }
    ready.store(false, Ordering::Relaxed);
    tokio::time::sleep(Duration::from_secs(10)).await; // balancer drains
    stop_http.cancel();
    stop_work.cancel(); // workers stop claiming, streams end
    let drain = async { while let Some(exit) = tasks.join_next().await { tracing::info!(?exit) } };
    if tokio::time::timeout(Duration::from_secs(15), drain).await.is_err() {
        tasks.abort_all(); // jobs still running go back to the queue when their lease expires
    }
    pool.close().await;
    Ok(())
}
```

| Symptom | Cause | Fix |
|---|---|---|
| Container always dies after the full grace period | Shell-form `CMD`: `/bin/sh` is PID 1 and does not forward the signal; or the binary is PID 1 with no handler, and PID 1 ignores signals it does not handle | Exec form `ENTRYPOINT ["/app/server", "serve"]` and a Tokio signal handler; an init (`tini`) if it spawns children |
| A few 502s on every deploy | Exit while the balancer still routes here | Steps 1-2; check the balancer's deregistration delay |
| Sporadic 502s with no deploy | The server closes idle keep-alive connections before the balancer does | Find the server's idle timeout on the pinned hyper version and keep it above the balancer's |
| Shutdown hangs until SIGKILL | Open SSE or WebSocket streams keep connections busy | End streams on the cancellation token (`realtime.md`) |
| Jobs run twice after deploys | A job longer than the grace period is killed, then retried | Resumable, idempotent jobs, or a longer grace period for the worker |

Serverless functions get no useful SIGTERM: flush per invocation. Prove the result with a load
generator running through a deploy: zero non-2xx responses. Deploy mechanics: `0x:ci-cd-release`
(`deploy-rollback.md`).

## Deadlines and cancellation

In Rust, cancelling is dropping the future. A timeout, a lost `select!` branch or a client
disconnect drops the handler, which stops at its next `.await`, wherever that is. Forgetting to
propagate cancellation is rare; stopping halfway through a state change is the common bug.

- One deadline per request at the edge (tower-http `TimeoutLayer`), carried as an `Instant` in
  the use-case context; outbound calls use `tokio::time::timeout_at(deadline, call)`. Each hop's
  timeout is shorter than its caller's; between services, send the remaining budget in a header.
- Multi-step writes go in one transaction: an SQLx `Transaction` dropped without `commit` rolls
  back. A sequence with an external effect goes into a job, or a task tracked by the process
  (`tokio_util::task::TaskTracker`), so a disconnect cannot cut it in half.
- In a `select!` loop use only cancel-safe operations (`mpsc::Receiver::recv`,
  `CancellationToken::cancelled`, `sleep`; Tokio's documentation states each method's cancel
  safety). A dropped `read_exact` or multi-step helper loses what it had read.
- Dropping an SQLx query future does not stop the statement on the server: `statement_timeout`
  on the application role is the backstop.
- Whether a disconnect reaches the handler depends on hyper noticing the closed socket and on
  every proxy between: close a client mid-request on the real deployment and log the drop. Map a
  deadline hit to 504; log a client disconnect at info level, outside the error tracker.

## Memory growth

There is no garbage collector and no heap limit flag: the process grows until the container limit
kills it with exit code 137 (OOMKilled), and there is no out-of-memory error to catch. Limits go
on the inputs.

| Symptom | Cause | Fix |
|---|---|---|
| Growth with traffic that never returns | A `HashMap` used as a cache, `moka` without `max_capacity`, unbounded channels behind a slow consumer | Bound every cache by size and TTL; bounded channels |
| Spikes on large requests or exports | Whole bodies or result sets in a `Vec`; extractors such as `Bytes`, `String` and `Json` buffer the body | Keep axum's 2 MB `DefaultBodyLimit` and raise it per route only; stream uploads to storage and rows to the response |
| Alive task count climbs | Per-connection loops never stopped on disconnect; retries without a limit | Export Tokio's alive-task metric; every spawned loop watches a cancellation token |
| RSS high and flat while live data is small, worse with more threads | glibc malloc fragmentation across per-thread arenas | jemalloc (`tikv-jemallocator`) or mimalloc as the global allocator, or `MALLOC_ARENA_MAX=2`; measure before and after |
| Static musl binary slow under concurrency | musl's allocator contends across threads | mimalloc or jemalloc in musl builds, or a glibc build in a distroless image |
| Slow leak | `Arc` cycles never drop | `Weak` for back-references |

Heap profiling: jemalloc's profiler (`jemalloc_pprof`) or `heaptrack` on a staging instance.
Export RSS, alive tasks, channel depths and cache sizes together: they explain each other.
Scheduled restarts hide a leak; acceptable as a Launch stopgap with a memory-slope alert, not a fix.

## Compile times

| Lever | Effect |
|---|---|
| The crate split above | A change rebuilds one small crate and its dependents |
| A fast linker | Recent stable Rust links with `lld` by default on x86_64 Linux; elsewhere set `lld` or `mold` in `.cargo/config.toml` |
| `debug = "line-tables-only"` in the dev and test profiles | Less debug info to emit and link; backtraces keep file and line |
| `SQLX_OFFLINE=true` in CI with committed `.sqlx/`, and `cargo sqlx prepare --check` | No database at compile time; stale query data fails CI |
| Heavy macros and deep generics in leaf crates | Each `query!`, serde derive and generic handler type costs compile time |
| `default-features = false` on heavy crates | Fewer transitive crates (cloud SDKs, TLS stacks, codecs) |
| `cargo build --timings` | Shows which crates dominate; look before optimizing |
| CI cache (`Swatinem/rust-cache`) and `cargo-chef` in Docker builds | Dependencies compiled once, not per push (`0x:ci-cd-release`; `0x:cloud-infrastructure`, `docker-images.md`) |
| `#[axum::debug_handler]` (the `macros` feature) on a handler that fails Axum's `Handler` bound | Names the argument at fault instead of a long, opaque error |

## Ask the user

- **Is there an existing backend in another language, or a library that exists only elsewhere?**
  It outranks the Rust default. Assume Rust only, with managed APIs for ML.
- **Where will it run: long-running containers or serverless functions?** Shutdown handling,
  in-process pools and WebSockets apply only to the first. Assume a container PaaS.
- **What is the longest task that must survive a deploy?** It sets the grace period and whether
  work must be resumable. Assume 30 seconds; anything longer becomes a resumable job.
- **How many instances, and which database plan?** The pool budget comes from its connection
  limit. Assume two web and one worker instance on a small managed Postgres.
- **How much is p99 latency worth?** Fractional-vCPU instances are cheaper and spikier. Assume
  one full vCPU per web instance at Launch.
