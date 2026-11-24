# Debugging method

Read this when: a bug is reported or its cause is unknown, a failure cannot be reproduced, a bug
or panic appears only in production, a server's memory keeps growing, an async task stalls,
or a failure is intermittent.

Order of work: capture the report and set severity; reproduce at the cheapest layer that shows
it; read the actual error and test one hypothesis at a time; narrow by halving; write the
regression test and watch it fail; fix the cause and check for siblings; confirm where it was
reported. Skipping the reproduction or the failing test is the usual reason a bug "comes back".
Rule of thumb: after 30 to 45 minutes in which the hypothesis space has not shrunk, stop
guessing and switch to a mechanical method (bisect, or instrument and wait).

## Bug report and triage

A report is usable when a stranger can follow it. Rewrite incoming reports into this shape
before starting, and ask for whatever is missing:

```text
Title: <what breaks, where> (not "checkout broken")
Steps: numbered, from a known starting state (account, plan, role, data)
Expected / Actual: one line each; exact error text, not a paraphrase
Environment: URL, release or commit, browser and OS or API client, time with time zone
Identifiers: user or tenant ID, request or trace ID, error-tracker event link
Frequency: always / sometimes (n of m tries) / once
Evidence: screenshot, recording, HAR, log excerpt
```

Severity is impact per affected user; priority is severity times reach, less a workaround.

| Severity | Meaning | Response at Launch stage |
|---|---|---|
| S1 | Data loss or corruption, security exposure, wrong charge, or the product is unusable for everyone | Stop other work; mitigate first (rollback, flag off), then diagnose |
| S2 | A core journey is broken for a segment, or for everyone with no workaround | Fix today; blocks releases |
| S3 | A feature misbehaves and a workaround exists | Schedule within the current cycle |
| S4 | Cosmetic or rare, minor annoyance | Batch, or close with a reason |

Reach: count affected accounts from the error tracker and logs, not complaints. For S1 and S2,
mitigate by the fastest reversible means before diagnosing (`0x:site-reliability`). Close
"cannot reproduce" only after adding the logging that would capture the next occurrence.

## Reproduce before fixing

A fix without a reproduction is a guess that may coincide with the symptom going away. Work
down this ladder until it fails on demand:

1. The exact steps on the reported environment and release.
2. The same steps locally on the same commit with production-like settings: a `--release` build
   (integer overflow panics in debug and wraps in release, `debug_assert!` is compiled out,
   timing differs), the pinned toolchain, the same Cargo features and flags.
3. The same data shape: the account's rows, volume, nulls, Unicode, time zone, locale, role.
4. The same conditions: slow network, double submit, two tabs, expired session, cold cache, a
   second instance, a clock near midnight or a DST change.
5. Still intermittent: loop it and measure the failure rate (last section), so that "fixed"
   is a rate change and not a hope.

Then shrink to the smallest failing case; it usually names the cause. With no reproduction
reachable, ship instrumentation for the next occurrence; a speculative fix is labeled unconfirmed.

## Read the error, one hypothesis at a time

- Read the whole message. A panic names its thread and location
  (`panicked at src/billing/renew.rs:42:17`); `RUST_BACKTRACE=1` adds the stack, and the first
  frame in the project's own code is the lead. Print errors with their cause chain (`{:#}` or
  `{:?}` on `anyhow::Error`); a `map_err(|e| e.to_string())` upstream threw the chain away and
  is worth fixing first. In a log, the earliest error is the cause candidate.
- When behavior ignores an edit, prove the running code is the edited code (change a log line):
  stale binary or image, `cargo leptos watch` not rebuilding the WASM, the wrong feature set
  (`ssr` and `hydrate` compile different code), the wrong env file.
- Search the exact message in the code and the dependency's issue tracker before theorizing.
- State the hypothesis as a prediction ("if the session cookie is missing on the callback, the
  handler logs `no session` before the redirect"), then make that one observation. Change one
  thing at a time; two simultaneous changes that fix the bug leave it unexplained.
- Verify the most firmly held assumptions ("never called with an empty list", "the migration
  ran") by observation; most long hunts end at an unchecked one.
- Explain why the bug occurred and why it was not caught. A fix without that explanation is a
  mask (a retry, an `unwrap_or_default`, a longer timeout).

## Bisecting

Use when it worked before and it is unclear which change broke it: it terminates in log2(n)
steps, so prefer it over reasoning once the first theories fail. `git bisect run` takes a
command: exit 0 marks good, 1 to 127 except 125 marks bad, 125 skips. Two Rust traps shape the
script: a commit that does not compile must exit 125, not cargo's 101; and a test filter that
matches nothing makes `cargo test` succeed with zero tests, which bisect records as good. Keep
the script outside the tree:

```bash
#!/usr/bin/env bash
# ~/bisect-check.sh, run with: git bisect start; git bisect bad; git bisect good v1.4.0
#                              git bisect run ~/bisect-check.sh; git bisect reset
cargo build --release --quiet || exit 125          # cannot build this commit: skip it
out=$(cargo test --release -p billing renewal_month_end 2>&1); code=$?
grep -q "running [1-9]" <<<"$out" || exit 125       # the test does not exist here: skip
exit "$code"
```

The same halving applies when history is not the variable:

| Variable | How to halve |
|---|---|
| Input | Delete half of the failing payload, file or dataset; keep the half that still fails |
| Dependencies | Diff `Cargo.lock` between good and bad; move half of the changed crates back with `cargo update -p <crate> --precise <version>` |
| Configuration | Diff environment variables, Cargo features and flags between working and failing; flip half |
| Code path | Return early or stub half of the pipeline; see whether the wrong value exists at the midpoint |
| Time | Compare the deploy, migration, flag-change and vendor-incident timeline with the first occurrence |

## Debugger, breakpoints and logpoints

Print statements answer the question thought of in advance; a debugger answers the next one
without a re-run, and in Rust a re-run can mean a minute of compiling. Use it when state is
complex, the path is unknown, or the code is a dependency's.

- `rust-lldb` and `rust-gdb` ship with rustup and pretty-print `String`, `Vec` and `Option`.
  In VS Code, CodeLLDB with rust-analyzer's "Debug" action above a test or `main` needs no
  setup. Debug a dev build; optimized code shows variables as optimized out.
- **Break on panic:** a breakpoint on `rust_panic` (`b rust_panic`) stops at the panic site
  with the stack intact, before unwinding.
- **Conditional breakpoints and logpoints** (CodeLLDB has both): a condition such as
  `order_id == 123` stops at the one bad iteration; a logpoint logs and continues, so nothing
  is edited, recompiled or left behind. Expression evaluation is limited (trait and generic
  method calls often fail); read fields instead of calling methods.
- Async stacks show executor frames; for "where is this task waiting", tracing spans and
  tokio-console (last section) answer better. `dbg!(expr)` prints and returns its value;
  `clippy::dbg_macro` keeps it out of commits.

Logging wins when timing matters (pausing hides races), the failure is rare, or the process
cannot pause: `tracing` fields with the request ID and the discriminating values.

## The regression test

Before changing the code, write the test that encodes the report at the cheapest layer that
shows the failure, and run it: it must fail with the reported symptom, not with a setup or
compile error. Then fix, and see it pass. Test the class, not only the instance (an off-by-one
at month end gets the leap-day and year-end cases too). Search for siblings of the same pattern,
add the clippy lint that bans it if one exists, and fix or list them. If only an end-to-end
test reproduces it, keep that only for a critical journey; otherwise extract the logic and
test it lower.

## From a production error to a local reproduction

Gather from the error tracker and telemetry before touching code:

| Item | Use |
|---|---|
| Release or commit SHA of the failing deploy | Check out exactly that commit; `main` may differ |
| Symbolized stack trace | The panic or error site. Release builds need `debug = "line-tables-only"` (or debug info uploaded to the error tracker); a stripped binary gives addresses only |
| Request: method, route, parameters, body shape, headers (redacted) | Replay it |
| Trace and request ID | Pull every log line and span for that request across services |
| User, tenant, role, plan, feature flags evaluated | Recreate the same branch of the code |
| Preceding requests and actions; first seen, frequency, correlated deploy | The sequence many bugs need, what changed, how urgent |

Recreate state with factories from the logged identifiers and field values; copy real rows only
under the anonymization rules in test-data-flaky.md. Replay the request with `curl` or as a
router `oneshot` test, which then becomes the regression test.

When it will not reproduce locally, the difference between environments is the clue:

| Production has | Local lacks |
|---|---|
| Several instances and real concurrency | Races, per-instance in-memory state, non-sticky sessions |
| Production data volume and old rows | Slow queries, timeouts, legacy nulls, rows written by old code |
| CDN, proxy and cache layers | Stale or cross-user cached responses, stripped headers, size and time limits |
| A release build, often a static musl binary | Overflow that wraps instead of panicking; musl's allocator, slow under many threads |
| Real third parties | Rate limits, slow responses, webhooks out of order |
| Platform limits | Memory ceilings (an OOM kill leaves no panic, only exit 137), CPU throttling, read-only disk |
| Real users' clocks, locales and devices | Time zone math, old browsers, extensions, slow WASM startup |

If telemetry cannot answer "which request, user, release and inputs", fix that first: a request
ID in every span, release tags and panic capture in the error tracker (`0x:site-reliability`).

## Debugging in production safely

The rule: observe without changing state, with a bounded blast radius, and leave no access or
debug code behind.

- **Read-only data access.** Query a replica, or connect with a role that has only `SELECT`,
  and bound the session:

```sql
BEGIN TRANSACTION READ ONLY;
SET LOCAL statement_timeout = '5s';  -- LOCAL: a pooled connection must not keep the setting
-- queries
ROLLBACK;
```

  A heavy ad-hoc query on the primary is a self-inflicted outage; add `LIMIT`, filter on
  indexed columns, and run `EXPLAIN` first on large tables.
- **Never fix data by hand in a console** without a reviewed script, a transaction, a row
  count check before commit and a backup of the affected rows. Manual writes are an S1 source.
- **Targeted verbosity at run time.** Wrap the `EnvFilter` in a `tracing_subscriber::reload`
  layer and keep its handle in the application state; an authenticated admin route then raises
  the level for one module, or for one tenant's spans (filter directives can match span
  fields), and a timer resets it. No redeploy, no global debug logging.
- **Sampled logs** for high-volume paths: 1 in N requests, but always errors and the flagged
  target. Unsampled debug logging on a hot path can itself cause the incident and the bill.
- **No secrets or personal data in debug output.** `#[derive(Debug)]` prints every field, so a
  struct holding a token leaks it through `?value` in a log line; wrap such fields in a type
  with a redacting `Debug` (the `secrecy` crate), and log identifiers, not bodies.
- **Do not attach a debugger** to a serving process: it stops every runtime thread on that
  instance. Record what was accessed and why, and revoke temporary access when done.

Flag mechanics are in `0x:ci-cd-release`; log pipelines and sampling in `0x:site-reliability`.

## Memory that keeps growing in a Rust server

First tell a leak from allocator behavior. Watch resident memory over hours under steady load,
next to the app's own counts: alive Tokio tasks (`Handle::current().metrics().num_alive_tasks()`),
cache entries, channel lengths. Memory that rises and plateaus is warm-up or cache fill. With
glibc's allocator, memory freed after a burst often stays in per-thread arenas, so resident
memory stays high with no leak; switching the global allocator (jemalloc or mimalloc) or
setting `MALLOC_ARENA_MAX=2` tells the two apart. A leak grows in proportion to work done.

Safe Rust rarely leaks in the C sense; it keeps things alive. Usual causes: a `HashMap` in
shared state keyed by user or request with no bound or expiry (use moka with a capacity and
TTL); an unbounded channel whose consumer is slower than its producer (a bounded channel makes
producers wait); tasks spawned per request that wait forever (the alive-task count climbs);
`Arc` cycles (back-references belong in `Weak`); `Box::leak` or `mem::forget` in a loop; a
client or pool created per request instead of once.

Procedure, on a local or staging copy running the release build with line tables:

1. Run the server under heaptrack (`heaptrack ./target/release/app`). It intercepts `malloc`,
   so it sees the system allocator only; for a jemalloc build use jemalloc's own heap profiler.
2. Warm up, apply a known amount of load (for example 10,000 requests to the suspected routes;
   load tools are in `0x:web-performance`), and stop the server cleanly.
3. Read the report (`heaptrack_print` or the GUI) by call stack: allocations still live at exit
   and the peak contributors. Repeat with twice the load: the call site whose live bytes double
   is the leak; noise does not scale.
4. Fix, repeat the same load, and confirm the growth is gone.

A scheduled restart or a higher memory limit is mitigation, not a fix. Heap profiles hold
whatever was in memory, secrets and customer data included.

## Intermittent concurrency failures and async stalls

Safe Rust rules out data races; what remains are logical races (check-then-act across an
`.await`, or between database connections), deadlocks and stalls. Pausing in a debugger hides
them, so the method is different:

1. **Get a failure rate.** Loop the smallest test that shows it:
   `for i in $(seq 1 200); do cargo nextest run -p orders reserve >/dev/null 2>&1 || echo "fail $i"; done`.
   Raise the rate with concurrency (a `JoinSet` of 20 calls against a real database;
   `flavor = "multi_thread"` for in-process races) and by loading the machine.
2. **Find stalls with tokio-console.** Build with `RUSTFLAGS="--cfg tokio_unstable"`, add the
   console-subscriber layer in dev builds, run `tokio-console`. A task with long poll times
   blocks the runtime (synchronous I/O, CPU work, `std::thread::sleep`): move that work to
   `spawn_blocking`. A task idle forever waits on a sender, lock or notify that never comes.
3. **Log the interleaving, narrowly**: actor ID, sequence number, `Instant`, values read and
   written, into a buffer dumped only when the invariant check fails; printing changes timing.
4. **Widen the window to prove it.** A test-only `yield_now().await` or sleep between the read
   and the write makes the failure 100%; that deterministic version is the regression test.
5. **Fix by construction, not by timing.** A unique constraint, a row lock, an idempotency key,
   one task owning the state, or one atomic statement whose row count is checked:
   `reserve_seat` runs `UPDATE events SET seats_left = seats_left - 1 WHERE id = $1 AND
   seats_left > 0` and returns `rows_affected() == 1`. The test that proves it:

```rust
#[sqlx::test]
async fn last_seat_is_sold_exactly_once(pool: PgPool) -> sqlx::Result<()> {
    sqlx::query("INSERT INTO events (id, seats_left) VALUES (1, 1)").execute(&pool).await?;
    let mut tasks = tokio::task::JoinSet::new();
    for _ in 0..20 {
        let pool = pool.clone();
        tasks.spawn(async move { reserve_seat(&pool, 1).await });
    }
    let mut sold = 0;
    while let Some(joined) = tasks.join_next().await {
        if joined.expect("task panicked")? {
            sold += 1;
        }
    }
    assert_eq!(sold, 1);
    Ok(())
}
```

6. **Prove by rate.** With a failure rate of 1 in N, an unfixed bug still passes 3N runs in a
   row about 5% of the time and 5N under 1%; run at least that, plus the test from step 4.

Silent task deaths look like stalls: a spawned task that panics or returns an error just ends,
and nobody awaits its `JoinHandle` (the default panic hook only prints to stderr). Spawn
background work through one helper that awaits the handle in a second task and logs both
`Ok(Err(_))` and a `JoinError` whose `is_panic()` is true, so the error tracker sees it.

Deadlocks: a `std::sync::Mutex` guard held across `.await` (`await_holding_lock`), two locks
taken in different orders, or Postgres deadlocks, whose report names both statements; take
locks in one order, keep transactions short (`0x:postgres-database`, `0x:backend-architecture`).

## Ask the user

- **How many users are affected, and is money or data involved?** Sets severity and whether to
  mitigate before diagnosing. Assume S2 for a broken core journey and S1 for anything touching
  charges, access or stored data.
- **Is a rollback or turning the feature off acceptable right now?** It is the fastest
  mitigation but removes the feature for everyone. Assume yes for S1.
- **May production data be queried or copied to reproduce this?** Privacy and contract limits
  apply. Assume read-only queries by identifier are fine and copies must be anonymized.
- **Is a restart or more memory acceptable as a stopgap for a leak?** It costs money and hides
  the trend. Assume yes for days, not as the resolution.
