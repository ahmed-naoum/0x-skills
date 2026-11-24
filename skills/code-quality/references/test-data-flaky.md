# Test data and flaky tests

Read this when: tests pass alone but fail together, a test fails intermittently, CI needs
re-runs to go green, tests depend on fragile shared data, the suite needs parallelizing, or
local, preview and performance environments need realistic data.

## Factories, not shared fixtures

A shared fixture file (one big seed all tests read) couples every test to every other: changing
a row for one test breaks ten, and no test shows which data it depends on. Each test should
create exactly the data it needs and state only the fields that matter to it. A factory struct
with `Default` and struct-update syntax does this. Fragment (`Role` is the app's enum, `User`
its row type):

```rust
static SEQ: AtomicU64 = AtomicU64::new(0);

/// Valid and unique by default; a test states only the fields it is about.
pub struct UserFactory {
    pub email: String,
    pub name: String,
    pub role: Role,
}

impl Default for UserFactory {
    fn default() -> Self {
        let n = SEQ.fetch_add(1, Ordering::Relaxed);
        Self {
            email: format!("user{n}-{}@example.test", Uuid::new_v4()),
            name: format!("User {n}"),
            role: Role::Member,
        }
    }
}

impl UserFactory {
    pub async fn insert(self, pool: &PgPool) -> sqlx::Result<User> {
        sqlx::query_as("INSERT INTO users (email, name, role) VALUES ($1, $2, $3) RETURNING id, email")
            .bind(self.email)
            .bind(self.name)
            .bind(self.role.as_str())
            .fetch_one(pool)
            .await
    }
}

#[sqlx::test]
async fn only_admins_can_invite(pool: PgPool) -> sqlx::Result<()> {
    let admin = UserFactory { role: Role::Admin, ..Default::default() }.insert(&pool).await?;
    let member = UserFactory::default().insert(&pool).await?;
    // ...
    Ok(())
}
```

Rules:

- **Valid by default.** A factory with no overrides produces a row that passes every
  constraint. Tests override only what they are about.
- **Unique by construction.** Emails, slugs and external IDs include a counter or UUID, so
  parallel tests and re-runs never collide on unique indexes.
- **Factories create their parents.** An invoice factory makes its customer and organization
  unless given one. Provide scenario helpers for common graphs (an org with three members) so
  setup stays one line.
- **Go through the same constraints as production.** A new `NOT NULL` column then breaks the
  factory once, not 200 tests.
- **No randomness that changes behavior.** Random names are fine; a random role or plan makes
  failures unreproducible.
- **Builders for pure values**: for unit tests, a function returning a valid in-memory struct,
  overridden with struct-update syntax (`Subscription { status: Status::PastDue, ..sample() }`).
- **Where factories live.** Code under `#[cfg(test)]` is invisible to other crates, to the
  `tests/` directory and to binaries. Put factories in a small test-support crate that other
  crates take as a dev-dependency and the seed binary depends on.

Reference data that is truly static and read-only (countries, plan catalog) can be loaded once
by migrations; that is the only acceptable shared data.

## Seed scripts for local and preview environments

A new clone and every preview deploy should reach a usable, populated app with one command.
Without it, each developer and each agent session builds data by clicking, and bugs that need
volume never appear before production.

- One idempotent seed binary (`cargo run -p testkit --bin seed`, or an `xtask` command),
  built on the same factories as the tests so it cannot drift from the schema. Safe to run
  twice: upsert on stable keys or reset first.
- Deterministic: fixed seed, fixed reference "now", so screenshots and demos are stable.
- Content that exercises the UI: an empty account, a typical account, and a heavy account
  (thousands of rows to force pagination and slow queries); long names, non-Latin text, a
  right-to-left string, missing optional fields; every status of every state machine
  (trialing, active, past due, canceled); several roles with credentials printed at the end
  of the run. Fixed passwords are for local use only: a preview reachable from the internet
  gets generated passwords or sits behind access protection.
- A guard that refuses to run against production: check an explicit environment variable and
  the database host, and exit non-zero otherwise. Seeding production by accident is a real
  incident class.
- Preview environments: seed on creation as a deploy step; never point previews at the
  production database. Environment wiring is in `0x:ci-cd-release`.

## Isolating tests

| Method | How | Speed | Limits |
|---|---|---|---|
| Database per test | `#[sqlx::test]` creates one, migrates it and hands the test a pool | Fast enough for most suites; parallel-safe | Migration time per test grows with the migration count |
| Transaction per test | The test opens a transaction, passes it to the code, drops it to roll back | Fastest | Code must take a connection (`&mut PgConnection`), not the pool; cannot test commits, several connections or real concurrency |
| Truncate between tests | `TRUNCATE ... RESTART IDENTITY CASCADE` of the touched tables | Medium | Tests sharing the database cannot run in parallel |
| Unique data, shared database | Every test creates its own tenant and queries only within it | Fast, parallel-safe, also works for end-to-end against a deployed app | Global queries (counts, "latest N") and global unique keys still collide |

Default: `#[sqlx::test]`. Designing functions to take `&mut PgConnection` also lets a caller
compose them in one transaction, and lets a test run them inside one:

```rust
/// Takes a connection, not the pool, so a caller (or a test) decides the transaction.
pub async fn rename_org(conn: &mut PgConnection, id: Uuid, name: &str) -> sqlx::Result<u64> {
    let done = sqlx::query("UPDATE orgs SET name = $2 WHERE id = $1")
        .bind(id)
        .bind(name)
        .execute(&mut *conn)
        .await?;
    Ok(done.rows_affected())
}
```

In a test, `let mut tx = pool.begin().await?;` then `rename_org(&mut tx, ...)`; queries on the
transaction itself are written `.execute(&mut *tx)`. Dropping `tx` without `commit` rolls back.

Shared process state needs the same treatment, and Rust adds a trap: `cargo test` runs a
binary's tests as parallel threads of one process, so environment variables, `static` values,
`OnceLock` and `LazyLock` initializers, the current directory and the global tracing
subscriber are shared. Edition 2024 makes `std::env::set_var` `unsafe` for this reason; pass a
config struct instead of mutating the environment. cargo-nextest runs each test in its own
process, which removes these collisions without fixing the design. Other shared resources:
Redis (a key prefix per test), files (a temp directory per test), ports (bind `127.0.0.1:0`
and read the assigned port), fake servers (one wiremock server per test).

## Clocks and randomness

Any test whose result depends on when or how often it runs is a future flake.

- **Inject wall-clock time** into logic: a `now` parameter, or a `Clock` trait
  (`fn now(&self) -> OffsetDateTime`, `Send + Sync`) held as `Arc<dyn Clock>` in the
  application state: `SystemClock` in production, `FixedClock(datetime!(2026-03-31 23:30 UTC))`
  in tests. This is the one place a trait for a test is right: the clock has no wire to fake.

- **Pause Tokio time for timers.** With `#[tokio::test(start_paused = true)]`, sleeps,
  timeouts and intervals complete instantly and in order, so backoff and debounce are tested
  without waiting (`retry` below takes attempts, a base delay and the operation, and doubles
  the delay after each failure). Traps: only `tokio::time` is paused, not `SystemTime` or `now_utc()`; it
  needs the single-threaded test runtime; and when every task is idle the paused clock jumps to
  the next timer, so a test waiting on real I/O (a database, a wiremock server) sees its
  timeouts fire at once. Use paused time for code whose waiting is all timers.

```rust
#[tokio::test(start_paused = true)] // tokio::time is virtual: sleeps complete at once, in order
async fn gives_up_after_three_attempts_with_doubling_backoff() {
    let start = tokio::time::Instant::now();
    let mut calls = 0;
    let res: Result<(), &str> = retry(3, Duration::from_millis(100), || {
        calls += 1;
        async { Err("503") }
    })
    .await;
    assert_eq!(res, Err("503"));
    assert_eq!(calls, 3);
    assert_eq!(start.elapsed(), Duration::from_millis(300)); // 100 + 200
}
```

- **Time zones.** Compute in UTC and convert with an explicit zone from the user's settings.
  The `time` crate's local-offset lookup fails in multi-threaded Unix processes, the test
  harness included. Set the test database's `TimeZone` to UTC; add far-from-UTC cases.
- Choose fixed dates that are not special by accident, and add deliberate cases for month end,
  leap day, year end and both DST transitions. Database-side time (`now()`, column defaults)
  ignores the application's clock: pass timestamps from the application where tests assert on
  them.
- **Seed randomness** (a seeded `StdRng`) and print the seed on failure. proptest records
  failing seeds in `proptest-regressions/`; commit them.
- **`HashMap` iteration order differs between runs** by design. Output built by iterating one
  (JSON, CSV, logs, SQL) changes order between runs: sort, or use `BTreeMap` or an
  insertion-ordered map where order is visible.
- In browser tests the page clock cannot be frozen from WebDriver; give the app under test a
  fixed `Clock` through its test configuration, guarded like any test-only switch.

## Finding the root cause of a flake

First make it fail on demand; a flake that cannot be reproduced cannot be confirmed fixed.

```bash
for i in $(seq 1 50); do cargo nextest run -p billing renew || break; done   # loop one test
cargo test -p billing -- --test-threads=1      # passes serially, fails in parallel: shared state
cargo test --test e2e -- --ignored --test-threads=4   # browser tests under parallel load
```

Then classify by how it fails:

| Evidence | Cause | Fix |
|---|---|---|
| Fails with other tests, passes alone or with `--test-threads=1` | Shared state: database rows, a `static`, an env var, a global subscriber, a port | Isolate or remove the shared thing; nextest's process per test helps only with process state |
| Fails alone, passes in the full run | Depends on another test's leftovers | Make the test create its own data |
| Fails more under load or on CI, timing-related errors | Race: assertion before the async work finished, a spawned task not awaited, a fixed sleep, event ordering assumed | Wait on the condition (await the `JoinHandle`, poll the state), not on time |
| Hangs until the slow-test timeout | Blocking call on the single-threaded test runtime, a `std::sync::Mutex` held across `.await`, waiting on a channel whose sender is still alive | `spawn_blocking`, async-aware locking, drop senders; see debugging.md |
| Fails at certain hours or dates, or only in CI's zone | Real clock or time zone | Inject time, pin zone |
| Connection, DNS or timeout errors to an external host | Real network in a test | Fake at the boundary; fail on unexpected requests |
| Fails when parallelism rises | Collisions on unique keys, ports or files, or Postgres out of connections | Unique data, per-test resources, fewer threads or more `max_connections` |
| Different element or text order between runs | Unordered query or `HashMap` iteration assumed stable | Add `ORDER BY` in the product code (often a real bug) or sort in the assertion |
| Browser test: click has no effect, intermittent | Acting before hydration or during animation | Wait for the hydration marker and the interactive state |

A meaningful share of flakes are real product races that users also hit, only less visibly.
Rule that out before blaming the test.

## Quarantine policy

One flaky test teaches everyone to re-run; after that, real failures get re-run too. The
policy that keeps CI trusted:

1. **Detect.** Retries stay on in CI for browser tests only, and nextest reports a pass on
   retry as flaky, not passed. Review the flaky list weekly.
2. **Quarantine the same day** when a test fails on main without a code cause twice: mark it
   `#[ignore = "quarantined: <issue link>"]` and keep running ignored tests in a non-blocking
   job so data keeps coming.
3. **Time limit.** A quarantined test is fixed or deleted within about two weeks. A test that
   nobody will fix protects nothing; if the behavior matters, rewrite it at a lower layer.
4. **Cap.** If more than a handful are quarantined, stop feature work on that area and fix the
   shared cause (usually isolation), because the suite no longer covers it.

Do not raise retry counts or timeouts as a fix. Retries are for collecting evidence, timeouts
for real slowness with a known bound. Never retry unit and integration tests by default: a
retried race in server code is a hidden production bug. Scope retries in nextest's config:

```toml
# .config/nextest.toml
[profile.ci]
fail-fast = false
slow-timeout = { period = "60s", terminate-after = 3 }

[[profile.ci.overrides]]
filter = "binary(e2e)"
retries = 2
```

## Parallelizing and sharding

Parallelism within a machine comes first; sharding across CI machines comes when one machine's
wall-clock passes about 10 minutes.

Preconditions, in order: tests are order-independent and pass under nextest and plain
`cargo test`, each test has its own database and other stateful resources, data is unique by
construction, no test relies on a fixed port or a global file.

- Threads: the CPU count for unit tests; fewer for database or browser tests, since Postgres
  and the app also need CPU. On small CI runners, 2 browser sessions is a common ceiling.
- Each `#[sqlx::test]` opens its own pool. Keep test threads times connections per test under
  Postgres `max_connections`; exhaustion shows up as random timeouts.
- Compile once, run in shards: build with `cargo nextest archive`, pass the archive to each
  shard job, and run `cargo nextest run --archive-file <file> --partition count:1/4`. Shards
  that each compile the workspace waste most of their time.
- Tests that need a resource exclusively go in a nextest test group with one thread, not a
  global `--test-threads=1`.
- End-to-end tests in parallel against one app instance share its caches, rate limits and
  background jobs. Raise or disable rate limits in the test configuration (never through a
  bypass that also exists in production), or tests throttle each other.
- A serial group is a smell of shared state; accept one only for a true multi-step journey.

## Production-shaped data for performance and migration tests

Small seeds cannot show a migration that locks a 50-million-row table or a query plan that
flips at scale. Options, safest first:

| Option | Use for | Notes |
|---|---|---|
| Synthetic data at production volume and distribution | Query plans, pagination, migration duration | Generate with `generate_series` or the seed factories in bulk; match row counts, skew (a few huge tenants, many tiny), null rates and index selectivity. No privacy exposure |
| Anonymized copy of production | Migrations against real edge cases, data-quality bugs, realistic plans | Requires the process below |
| Restore of a production backup, untouched | Restore drills only, in an environment with production-grade access control | Never as a general dev or staging database |

Anonymization process: transform inside the trusted environment and export only the result;
start from an allowlist (every column is dropped or replaced unless listed as safe), not a
blocklist that misses the column added last month; replace direct identifiers (names, emails,
phones, addresses, IPs) with deterministic fakes so joins and uniqueness survive; null or
regenerate secrets, tokens, password hashes, payment references and free-text fields (free
text is where personal data hides); keep distributions, sizes and foreign keys; rewrite emails
to a non-deliverable domain so no test can mail a real customer; disable outbound integrations
in that environment. Pseudonymized data can still be personal data under privacy law; whether a
given copy is acceptable is a `0x:privacy-compliance` question.

For migrations: time each migration against the production-sized copy, watch lock duration,
and run the previous application version's tests against the migrated schema to prove backward
compatibility. Migration technique is in `0x:postgres-database`; load testing in
`0x:web-performance`.

## Ask the user

- **May a copy of production data, even anonymized, leave the production environment?** This
  is a legal and customer-contract question. Assume no: use synthetic data at production scale.
- **How long may a known-flaky test stay quarantined before it is deleted?** Assume two weeks.
- **What do realistic accounts look like (rows per tenant, largest customer, typical usage)?**
  Shapes the seed and the heavy account. Assume one empty, one typical and one account with
  about 100 times the typical volume.
- **Is paying for more CI parallelism acceptable to keep feedback under 10 minutes?** Assume
  yes up to a small fixed budget; fix slow tests and compile time first.
