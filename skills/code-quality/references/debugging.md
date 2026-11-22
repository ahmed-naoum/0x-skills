# Debugging method

Read this when: a bug is reported or its cause is unknown, a failure cannot be reproduced, a bug
appears only in production, a server process leaks memory, or a failure is intermittent.

## The order of work

1. Capture the report in a reproducible form and set severity.
2. Reproduce it, at the cheapest layer that still shows it.
3. Read the actual error. Form one hypothesis, design the observation that would disprove it,
   look, record the result.
4. Narrow by halving: history, input, configuration, or code path.
5. Write the regression test and watch it fail.
6. Fix the cause, watch the test pass, check for siblings of the same bug.
7. Confirm in the environment where it was reported.

Skipping step 2 or 5 is the usual reason a bug "comes back": it was never shown to be fixed.
Time-box: if 30 to 45 minutes pass without the hypothesis space getting smaller, stop guessing
and switch to a mechanical method (bisect, or instrument and wait).

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

Severity is impact per affected user; priority is severity times reach, with workaround as a
discount.

| Severity | Meaning | Response at Launch stage |
|---|---|---|
| S1 | Data loss or corruption, security exposure, wrong charge, or the product is unusable for everyone | Stop other work; mitigate first (rollback, flag off), then diagnose |
| S2 | A core journey is broken for a segment, or for everyone with no workaround | Fix today; blocks releases |
| S3 | A feature misbehaves and a workaround exists | Schedule within the current cycle |
| S4 | Cosmetic or rare, minor annoyance | Batch, or close with a reason |

Reach: count affected users or accounts from the error tracker and logs, not from the number
of complaints; most users do not report. One enterprise customer blocked can outrank many free
users mildly annoyed, which is a business call. For S1 and S2, mitigation and diagnosis are
separate tracks: restore service by the fastest reversible means before understanding the
cause (incident handling is in `0x:site-reliability`). Close "cannot reproduce" reports only
after adding the logging that would capture the next occurrence.

## Reproduce before fixing

A fix without a reproduction is a guess that may coincide with the symptom going away. Work
down this ladder until it fails on demand:

1. Follow the exact steps on the reported environment and release.
2. Same steps locally on the same commit with production-like settings (production build,
   same Node major, same flags).
3. Recreate the data shape: the specific account's rows, volume, nulls, Unicode, time zone,
   locale, role.
4. Recreate the conditions: slow network, double submit, two tabs, expired session, cold
   cache, a second instance, clock near midnight or a DST change.
5. If it stays intermittent, loop it and measure the failure rate (see the last section), so
   that "fixed" can be stated as a rate change and not as a hope.

Then shrink: remove steps, data and code until the smallest case that still fails remains.
The minimal case usually names the cause. When no reproduction is reachable, do not ship a
speculative fix on its own; ship instrumentation that will identify the cause at the next
occurrence, optionally with the speculative fix behind it, and say that it is unconfirmed.

## Read the error, one hypothesis at a time

- Read the whole message and the whole stack. Find the first frame in the project's own code;
  frames above it are usually messengers. Follow `cause` chains to the bottom.
- In a log with many errors, the first one in time is the cause candidate; later ones are
  usually consequences.
- Check that the error is current: stale build, cached bundle, wrong branch, wrong environment
  variable file, a server not restarted. Prove the running code is the edited code (change a
  log line) when behavior ignores an edit.
- Search the exact message in the codebase and the dependency's issue tracker before
  theorizing; it identifies the throw site.
- State the hypothesis as a prediction: "if the session cookie is missing on the callback
  request, the handler logs `no session` before the redirect". Then make the one observation.
  Change one thing at a time; two simultaneous changes that fix the bug leave it unexplained.
- Keep notes of what was tried and seen. Notes prevent re-testing the same idea and are the
  raw material for the commit message.
- Question the assumptions held most firmly: "that function is never called with null",
  "the migration ran", "that value is cached". Verify each by observation; most long hunts end
  at an unchecked assumption.
- Explain why the bug occurred and why it was not caught. A fix that makes the symptom vanish
  without that explanation is a mask (a retry, a null check, a longer timeout).

## Bisecting

Use when it worked before and it is unclear which change broke it. It is mechanical and
terminates in log2(n) steps, so prefer it over reasoning once the first theories fail.

```bash
git bisect start
git bisect bad                 # current commit fails
git bisect good v1.4.0         # a commit or tag known to work
git bisect run pnpm vitest run src/billing/renew.test.ts
git bisect reset
```

`git bisect run` takes any command: exit code 0 marks good, 1 to 127 except 125 marks bad, and
125 skips a commit that cannot be tested (does not build). Write the check as a script kept
outside the tracked tree, so checkouts do not change it. Reinstall dependencies in the script
when the lockfile changes between commits. Bisect needs commits that each build; that is one
reason to keep refactoring and behavior changes in separate small commits.

The same halving applies when history is not the variable:

| Variable | How to halve |
|---|---|
| Input | Delete half of the failing payload, file or dataset; keep the half that still fails |
| Dependencies | Diff the lockfile between good and bad; revert half of the version changes |
| Configuration | Diff environment variables and flags between the working and failing environment; flip half |
| Code path | Return early or stub half of the pipeline; see whether the wrong value already exists at the midpoint |
| Data | Run against a copy with half of the rows or tenants |
| Time | Compare the deploy, migration, flag-change and vendor-incident timeline against the first occurrence in the error tracker |

## Debugger, breakpoints and logpoints

Print statements answer the question thought of in advance; a debugger answers the next
question without a re-run. Use it when state is complex, the path is unknown, or the code is
a dependency's.

- Node: `node --inspect-brk script.js`, then attach from `chrome://inspect` or the editor. In
  VS Code, a JavaScript Debug Terminal attaches to any Node process started in it, including
  `pnpm dev` and test runs, with no configuration.
- Vitest: `vitest --inspect-brk --no-file-parallelism` so one process holds the breakpoint.
- Playwright: `npx playwright test --debug`, or `await page.pause()` at the point of interest.
- Browser: the Sources panel; `debugger;` in code as a temporary breakpoint.

Techniques that pay:

- **Conditional breakpoint** (`order.id === 'ord_123'`) for the one bad iteration in a loop.
- **Logpoint**: a breakpoint that logs an expression and continues. Nothing is edited, rebuilt
  or left behind in a commit.
- **Pause on exceptions**, including caught ones, to stop at the throw site of an error that a
  `catch` swallows or rewraps.
- **Walk the call stack** and inspect each frame's variables to find where the bad value
  first appears, then set the next breakpoint earlier. Watch expressions and DOM or XHR
  breakpoints do the same in the browser.
- Source maps must be on for stacks and breakpoints to map to source: `node
  --enable-source-maps` for compiled server code.

Logging is the better tool when timing matters (pausing hides races), when the failure is
rare, or when the process cannot be paused (production). Make debug logs structured, with the
request ID and the values that discriminate between hypotheses, and remove or demote them in
the fix commit.

## The regression test

Before changing the code, write the test that encodes the report at the cheapest layer that
shows the failure, and run it: it must fail, and fail with the reported symptom, not with a
setup error. Then fix, and see it pass. This proves the reproduction, proves the fix, and
keeps the bug from returning.

- Name it after the behavior, with the issue reference in a comment: `does not double-charge
  when the webhook is delivered twice`.
- Test the class, not only the instance: if the bug was an off-by-one at a month end, add the
  other boundaries (leap day, year end).
- Look for siblings: search for the same pattern elsewhere and fix those in the same change or
  list them.
- Commit test and fix together; the pull request should show the failing output before the fix.
- If the only test that reproduces it is an end-to-end test, keep it only if the journey is
  critical; otherwise extract the faulty logic and test it lower.

## From a production error to a local reproduction

Gather from the error tracker and telemetry before touching code:

| Item | Use |
|---|---|
| Release or commit SHA of the failing deploy | Check out exactly that commit; `main` may differ |
| Stack trace mapped through source maps | The throw site; upload source maps per release or stacks are unreadable |
| Request: method, route, parameters, body shape, headers (redacted) | Replay it |
| Trace and request ID | Pull every log line and span for that request across services |
| User, tenant, role, plan, feature flags evaluated | Recreate the same branch of the code |
| Breadcrumbs: preceding requests, navigation, clicks | The sequence, since many bugs need two steps |
| First seen, frequency, affected count, correlated deploy | What changed, and how urgent |

Then recreate state: build the same data shape with factories from the logged identifiers and
field values; copy real rows only under the anonymization rules in test-data-flaky.md. Replay
the request with `curl` or as an integration test, which then becomes the regression test.

When it will not reproduce locally, the difference between environments is the clue:

| Production has | Local lacks |
|---|---|
| Several instances and real concurrency | Races, in-memory state that differs per instance, non-sticky sessions |
| Production data volume and old rows | Slow queries, timeouts, legacy nulls, rows written by old code |
| CDN, proxy and cache layers | Stale or cross-user cached responses, stripped headers, body size and time limits |
| Minified production build | Dev-only behavior, different error messages, hydration mismatches |
| Real third parties | Rate limits, slow responses, webhooks out of order |
| Platform limits | Memory ceilings, function timeouts, cold starts, read-only filesystems |
| UTC clock, other locales, real user devices | Time zone and locale math, old browsers, extensions |

If the telemetry cannot answer "which request, which user, which release, which inputs", the
first fix is the telemetry: request IDs in every log line, release tagging in the error
tracker, input shapes logged at trust boundaries (setup is in `0x:site-reliability`).

## Debugging in production safely

The rule: observe without changing state, with a bounded blast radius, and leave no access or
debug code behind.

- **Read-only data access.** Query a replica, or connect with a role that has only `SELECT`,
  and bound the session:

```sql
SET statement_timeout = '5s';
BEGIN TRANSACTION READ ONLY;
-- queries
ROLLBACK;
```

  A heavy ad-hoc query on the primary is a self-inflicted outage; add `LIMIT`, filter on
  indexed columns, and run `EXPLAIN` first on large tables.
- **Never fix data by hand in a console** without a reviewed script, a transaction, a row
  count check before commit and a backup of the affected rows. Manual writes are an S1 source.
- **Targeted verbosity by flag.** Turn debug logging on for one user, tenant or request header
  through a feature flag or a runtime log-level setting, not through a redeploy with debug on
  globally. Give the flag an expiry.
- **Sampled logs** for high-volume paths: log 1 in N requests, but always log errors and the
  flagged target. Unsampled debug logging on a hot path can itself cause the incident and the
  bill.
- **No secrets or personal data in debug output**: log identifiers and shapes, not bodies,
  tokens, or card and password fields.
- **Do not attach a pausing debugger** to a serving process: a breakpoint halts every request
  on that instance, and an open inspector port is remote code execution for whoever reaches it.
- **Reproduce on one instance or a canary** behind a flag for the affected account when the
  bug needs production conditions; ship the instrumentation the same way as code, through
  review and deploy.
- Record what was accessed and why, and revoke temporary access when done.

Flag mechanics are in `0x:ci-cd-release`; log pipelines and sampling in `0x:site-reliability`.

## Memory leak in a Node server

First confirm it is a leak. Plot `process.memoryUsage()` over hours: a leak shows `heapUsed`
after each major garbage collection rising steadily under steady load, ending in an
out-of-memory kill or a V8 "heap out of memory" abort. Memory that rises and then plateaus is
warm-up or cache fill. If `rss` grows while `heapUsed` stays flat, the growth is outside the
JavaScript heap (Buffers, native modules, `external` and `arrayBuffers` in the same output),
and heap snapshots will not show it.

Procedure, on a local or staging copy running the production build:

1. Start with the inspector (`node --inspect server.js`) and open DevTools from
   `chrome://inspect`, Memory tab.
2. Warm up with load (a tool such as autocannon against the suspected routes), then take
   snapshot 1. Taking a snapshot runs a garbage collection first.
3. Apply a known amount of load, for example 10,000 requests, and take snapshot 2. Repeat for
   snapshot 3.
4. Open snapshot 3 in Comparison view against snapshot 1 and sort by size delta or by count
   delta. Leaked objects grow in proportion to the load between snapshots; noise does not.
   A count that grows by a multiple of the request count is the signature.
5. Select an instance of the growing constructor and read its **retainers** path, from the
   object up to a GC root. The retainer chain names the leak: a module-level `Map`, an event
   emitter's listener array, a timer, a closure.
6. Fix, repeat the same load, and confirm the delta is gone.

Usual causes, in rough order of frequency: a cache or `Map` keyed by user or request with no
size bound or expiry; listeners added per request to a long-lived emitter and not removed
(Node's `MaxListenersExceededWarning` is this bug announcing itself); `setInterval` or timers
never cleared; per-request data pushed to a module-level array or closed over by a long-lived
function; promises that never settle holding their closure; a client or connection pool
created per request.

When it reproduces only in production: `v8.writeHeapSnapshot()` behind an authenticated admin
trigger, or start Node with `--heapsnapshot-signal=SIGUSR2` and signal the process; the flag
`--heapsnapshot-near-heap-limit=<n>` writes snapshots just before an out-of-memory abort.
Cautions: writing a snapshot blocks the event loop for seconds to minutes on a large heap and
needs spare memory of about the heap size again, so take the instance out of rotation first;
the file contains everything in memory, including secrets and customer data, so handle it as
production data. Raising `--max-old-space-size` or restarting on a schedule buys time and is
an acceptable mitigation, not a fix. CPU and latency profiling are in `0x:web-performance`.

## Intermittent concurrency failures

Symptoms: fails 1 time in N, fails only under load or only in CI, duplicate rows, lost
updates, deadlock errors, "impossible" states. Pausing in a debugger hides these, so the
method is different:

1. **Get a failure rate.** Loop the smallest test that shows it and count:

```bash
for i in $(seq 1 200); do pnpm vitest run src/orders/reserve.test.ts >/dev/null 2>&1 || echo "fail $i"; done
```

   Raise the rate by running the operation concurrently (`Promise.all` of 20 calls against a
   real database with separate connections) and by loading the machine. A 1 in 200 failure
   turned into 1 in 3 is debuggable.
2. **Log the interleaving, narrowly.** At each step of the suspected critical section log an
   actor ID (request or worker), a sequence number, a monotonic timestamp
   (`performance.now()`), and the values read and written. Logging to the console changes
   timing and can hide the race; append to an in-memory buffer and dump it only when the
   invariant check fails.
3. **Find the window.** Read two failing interleavings side by side. Nearly all reduce to
   check-then-act (read, decide, write, with another actor in between), a missing `await`, a
   shared mutable variable across requests, or lock ordering.
4. **Widen the window to prove it.** Insert a deliberate delay or a test-only hook between the
   read and the write so the failure becomes 100%. That deterministic version is the
   regression test.
5. **Fix by construction, not by timing.** A unique constraint, an atomic statement
   (`UPDATE ... SET stock = stock - 1 WHERE stock > 0`, then check the row count), a row lock,
   an idempotency key, or a queue with one consumer per key. Sleeps, retries and reordering
   only lower the rate. Patterns are in `0x:postgres-database` and `0x:backend-architecture`.
6. **Prove by rate.** Rerun the stress loop for many times the iterations that used to produce
   a failure. Zero failures in 3 times the previous mean interval is weak evidence; aim for
   10 times or more, plus the deterministic test from step 4.

For deadlocks, read the database's deadlock report: it names both statements and the locks
held and awaited; fix by acquiring locks in one consistent order or shortening transactions.

## Ask the user

- **How many users are affected, and is money or data involved?** Sets severity and whether to
  mitigate before diagnosing. Assume S2 for a broken core journey and S1 for anything touching
  charges, access or stored data.
- **Is a rollback or turning the feature off acceptable right now?** It is the fastest
  mitigation but removes the feature for everyone. Assume yes for S1.
- **May production data be queried or copied to reproduce this?** Privacy and contract limits
  apply. Assume read-only queries by identifier are fine and copies must be anonymized.
- **When did it last work, and what changed around then?** Deploys, flags, migrations, vendor
  changes, traffic. Assume the most recent deploy until the timeline says otherwise.
- **Is a restart or more memory acceptable as a stopgap for a leak?** It costs money and hides
  the trend. Assume yes for days, not as the resolution.
