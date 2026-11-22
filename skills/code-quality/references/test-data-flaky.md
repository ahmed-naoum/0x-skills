# Test data and flaky tests

Read this when: tests pass alone but fail together, a test fails intermittently, CI needs
re-runs to go green, tests depend on fragile shared data, the suite needs parallelizing, or
local, preview and performance environments need realistic data.

## Factories, not shared fixtures

A shared fixture file (one big seed all tests read) couples every test to every other: changing
a row for one test breaks ten, and no test shows which data it depends on. Each test should
create exactly the data it needs and state only the fields that matter to it.

```ts
let n = 0;
export async function createUser(db: Db, overrides: Partial<NewUser> = {}) {
  n += 1;
  const [user] = await db.insert(users).values({
    email: `user${n}-${crypto.randomUUID()}@example.test`,
    name: `User ${n}`,
    role: 'member',
    ...overrides,
  }).returning();
  return user;
}

// in a test: only the relevant fact is visible
const admin = await createUser(db, { role: 'admin' });
```

Rules:

- **Valid by default.** A factory with no arguments produces a row that passes every
  constraint. Tests override only what they are about.
- **Unique by construction.** Emails, slugs and external IDs include a counter or UUID, so
  parallel tests and re-runs never collide on unique indexes.
- **Factories create their parents.** `createInvoice()` makes its customer and organization
  unless given one. Provide scenario helpers for common graphs
  (`createOrgWithMembers({ members: 3 })`) so setup stays one line.
- **Go through the same code or constraints as production.** Insert through the typed schema
  so a new required column breaks the factory once, not 200 tests.
- **No randomness that changes behavior.** Random names are fine; a random role or plan makes
  failures unreproducible. If a faker library is used, seed it (`faker.seed(1)`).
- **Builders for pure objects**: for unit tests, a plain function returning an in-memory
  object (`buildSubscription({ status: 'past_due' })`) with no database.

Reference data that is truly static and read-only (countries, plan catalog) can be loaded once
by migrations or a base seed; that is the only acceptable shared data.

## Seed scripts for local and preview environments

A new clone and every preview deploy should reach a usable, populated app with one command.
Without it, each developer and each agent session builds data by clicking, and bugs that need
volume never appear before production.

- One idempotent script (`pnpm db:seed`), built on the same factories as the tests so it
  cannot drift from the schema. Safe to run twice: upsert on stable keys or reset first.
- Deterministic: fixed seed, fixed reference "now", so screenshots and demos are stable.
- Content that exercises the UI: an empty account, a typical account, and a heavy account
  (thousands of rows to force pagination and slow queries); long names, non-Latin text, a
  right-to-left string, missing optional fields; every status of every state machine
  (trialing, active, past due, canceled); several roles with known credentials printed at the
  end of the run.
- A guard that refuses to run against production: check an explicit environment variable and
  the database host, and exit non-zero otherwise. Seeding production by accident is a real
  incident class.
- Preview environments: seed on creation as a deploy step; never point previews at the
  production database. Environment wiring is in `0x:ci-cd-release`.

## Isolating tests

| Method | How | Speed | Limits |
|---|---|---|---|
| Transaction per test | Begin before each test, run the code on that connection, roll back after | Fastest | Code under test must use the test's connection; cannot test commit behavior, multiple connections, real concurrency, or code that manages its own top-level transactions unless they become savepoints |
| Truncate between tests | `TRUNCATE ... RESTART IDENTITY CASCADE` of the touched tables after each test | Medium; cost grows with table count | Tests in the same database cannot run in parallel |
| Database per worker | Create one database per parallel worker from a migrated template, then transaction or truncate inside it | Fast, parallel-safe | Slightly more setup; the default once the suite is parallel |
| Unique data, shared database | Every test creates its own tenant and only queries within it | Fast, parallel-safe, also works for end-to-end against a deployed app | Global queries (counts, "latest N") and unique global keys still collide |

Default: database per worker created from a template, with per-test transaction rollback where
the code allows and truncation for the tests that need real commits (concurrency, multiple
connections). In Postgres:

```sql
CREATE DATABASE app_test_3 TEMPLATE app_test_template;
```

The template must have no open connections while it is copied. Name the worker databases from
the runner's worker identifier (Vitest sets `VITEST_POOL_ID`; Playwright exposes
`testInfo.parallelIndex`).

Other shared state needs the same treatment: Redis (a key prefix or logical database per
worker, flushed between tests), files (a temp directory per test), ports (ask the OS for a free
port by listening on 0), module-level caches and singletons (reset in `afterEach`, or better,
remove), environment variables (restore after mutation), fake servers (reset handlers after
each test).

## Clocks and randomness

Any test whose result depends on when or how often it runs is a future flake.

- **Inject time** into logic (`now` parameter). For code that reads the clock directly, freeze
  it:

```ts
beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-03-10T12:00:00Z'));
});
afterEach(() => vi.useRealTimers());
```

- Advance instead of waiting: `await vi.advanceTimersByTimeAsync(30_000)` for timeouts,
  backoff and debounce. Fake timers can stall libraries that rely on real timers (database
  drivers, some HTTP clients); when a test hangs under fake timers, fake only `Date`
  (`vi.useFakeTimers({ toFake: ['Date'] })`).
- **Pin the time zone** for the test process (`TZ=UTC` in the test script) and add a few
  explicit tests in a far-from-UTC zone for date logic. Tests that only pass in the author's
  zone fail in CI or for two hours every evening.
- Choose fixed dates that are not special by accident, and add deliberate cases for month end,
  leap day, year end and both DST transitions. Database-side time (`now()`,
  `DEFAULT CURRENT_TIMESTAMP`) is not affected by the test runner's fake clock: pass timestamps
  from the application where tests assert on them.
- **Seed randomness** and print the seed on failure. Inject ID and token generators where the
  test asserts on them; otherwise assert on shape, not value.
- In browser tests, use the Playwright clock API (`page.clock`) to fix or advance page time.

## Finding the root cause of a flake

First make it fail on demand; a flake that cannot be reproduced cannot be confirmed fixed.

```bash
npx playwright test e2e/checkout.spec.ts --repeat-each=30 --workers=4
pnpm vitest run --sequence.shuffle              # order dependence; prints the seed
for i in $(seq 1 50); do pnpm vitest run src/billing/renew.test.ts || break; done
```

Then classify by how it fails:

| Evidence | Cause | Fix |
|---|---|---|
| Fails only with other tests, or only in a certain order; passes alone | Shared state: database rows, module singleton, env var, leftover mock, fake timers not restored | Shuffle with the printed seed to reproduce; bisect the file list; isolate or reset the shared thing |
| Fails alone, passes in the full run | Depends on another test's leftovers | Make the test create its own data |
| Fails more under load or on CI, timing-related errors | Race: assertion before the async work finished, missing `await`, fixed sleep too short, event ordering assumed | Wait on the condition, not on time; await every promise (lint rule in static-analysis-types.md) |
| Fails at certain hours or dates, or only in CI's zone | Real clock or time zone | Freeze time, pin zone |
| Fails with connection, DNS or timeout errors to an external host | Real network in a test | Fake at the boundary; fail on unhandled requests |
| Fails when parallelism rises | Collisions on unique keys, ports, files, or exhausted connection pool | Unique data, per-worker resources, pool sized for workers |
| Different element or text order between runs | Unordered query or object-key iteration assumed stable | Add `ORDER BY` in the product code (often a real bug) or sort in the assertion |
| Browser test: click has no effect, intermittent | Acting before hydration or during animation | Wait for the interactive state |
| Memory or slow creep, late tests time out | Leaked handles, servers or containers not closed | Close in teardown; run with fewer files to confirm |

A meaningful share of flakes are real product races that users also hit, only less visibly.
Rule that out before blaming the test.

## Quarantine policy

One flaky test teaches everyone to re-run; after that, real failures get re-run too. The
policy that keeps CI trusted:

1. **Detect.** Retries stay on in CI for browser tests, but a pass-on-retry is recorded as
   flaky, not passed. Review the flaky list weekly; for a stricter gate on main, Playwright
   can fail the run on flaky tests (`--fail-on-flaky-tests`).
2. **Quarantine the same day** when a test fails on main without a code cause twice: mark it
   (`test.fixme` in Playwright, `it.skip` or a `@quarantine` tag excluded from the blocking
   job) and open an issue linked in a comment on the test. A quarantined test still runs in a
   non-blocking job so data keeps coming.
3. **Time limit.** A quarantined test is fixed or deleted within about two weeks. A test that
   nobody will fix protects nothing; if the behavior matters, rewrite it at a lower layer.
4. **Cap.** If more than a handful are quarantined, stop feature work on that area and fix the
   shared cause (usually isolation), because the suite no longer covers it.

Do not raise retry counts or timeouts as a fix. Retries are for collecting traces, timeouts for
real slowness with a known bound. Never add retries to unit and integration tests by default: a
retried race in server code is a hidden production bug.

## Parallelizing and sharding

Parallelism within a machine (workers) comes first; sharding across CI machines comes when one
machine's wall-clock passes about 10 minutes.

Preconditions, in order: tests are order-independent (prove with a shuffled run), each worker
has its own database and other stateful resources, data is unique by construction, no test
relies on a fixed port or a global file.

- Workers: start at the number of CPU cores for unit tests; fewer for database or browser
  tests, since the database and the app under test also need CPU. On small CI runners, 2
  workers for browser tests is a common ceiling.
- Size the database's `max_connections` and each worker's pool so
  workers x pool size stays under the limit; pool exhaustion shows up as random timeouts.
- Shard in CI with a job matrix: `npx playwright test --shard=${{ matrix.shard }}/4` or
  `vitest run --shard=1/4`. Each shard uploads its own report; merge them in a final job.
  Shards split by file, so one huge file unbalances the run: split it.
- End-to-end tests in parallel against one app instance share that app's caches, rate limits
  and background jobs. Exempt test tenants from rate limits by configuration, or tests throttle
  each other.
- Serial mode for a group of tests is a smell that they share state. Use it only for a true
  multi-step journey, and prefer one longer test.

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
  yes up to a small fixed budget; fix slow tests first.
- **Are there demo or sales accounts that need stable seeded data?** If so, the seed script
  doubles as the demo dataset and its content needs review. Assume no.
