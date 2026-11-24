# Test strategy

Read this when: deciding what to test, at which layer, how much is enough, whether to write the
test first, or what must pass before a release goes out.

## The question a strategy answers

A test is worth writing when the expected cost of the bug it catches (probability x damage x
time to notice) exceeds the cost of writing and maintaining the test. Three consequences follow:

- Tests are allocated by risk, not spread evenly. A pricing function gets twenty cases; a
  settings page gets none until it breaks once.
- The cheapest layer that can observe the failure wins. A rounding bug belongs in a unit test,
  a missing `WHERE org_id` in an integration test against a real database, a broken redirect
  after login in one end-to-end test.
- A test that fails for reasons other than a product defect has negative value: it trains the
  owner to ignore red. Delete or fix it the week it starts.

## What goes at each layer

| Layer | Put here | Do not put here | Budget |
|---|---|---|---|
| Compiler and clippy | Shape errors, absent values (`Option`), ignored `Result` or future, non-exhaustive `match`, data races, `Send` across `.await`, panicking patterns | Business rules | Seconds, in the editor through rust-analyzer |
| Unit (pure logic) | Pricing, proration, permission decisions, parsers, state machines, date math, validation and newtype constructors | Anything whose only content is calling a library | Milliseconds each |
| Integration (real Postgres, the Axum router) | Queries, transactions, constraints, tenant isolation, route auth and error mapping, server functions, job handlers, webhook handlers | Third-party networks (fake them at the boundary) | Tens of ms each; whole suite in a few minutes |
| End to end (browser) | The 5 to 15 journeys that earn or protect revenue: sign up, sign in, pay, the core action, upgrade, cancel | Edge cases, validation messages, permutations | Whole suite under about 10 minutes in CI |
| Manual and exploratory | New features before release, real devices, real payment methods, anything visual and subjective | Regression checks a machine can repeat | A bug bash per significant release |

For a typical web product the shape is a wide integration middle, not a classic pyramid: most
defects live in the seams (query + auth + validation + serialization), and a handler tested
through the router against a real database covers all four at once. Keep unit tests for code
with real branching logic; keep end-to-end tests few.

Rust moves work out of the test suite: the compiler already proves what a TypeScript suite
spends tests on (null handling, shapes, exhaustive cases), so do not test what a type
guarantees. It also adds a cost the old stack did not have: every test binary must compile and
link before it runs, so the number of test binaries and the dependency weight of test code
matter as much as test run time (unit-integration-tests.md).

### What to skip on purpose

- Framework and library behavior (that serde parses a derived struct, that SQLx binds a
  parameter, that the router routes).
- What the type system proves: if only `Email::parse` can build an `Email`, callers need no
  tests that they validate it (static-analysis-types.md).
- Trivial getters, pass-through components, generated code.
- Static marketing pages: a link checker and one smoke test are enough.
- Snapshot tests of large rendered trees: they fail on every change and get updated blindly.
- Code that will be thrown away within the week. Prototype stage code needs a smoke test of the
  main path and nothing else, except for the three areas below.

## Risk-first order: money, auth, data loss

These three are tested from the first real user onward, at any stage, because their failures are
silent, expensive and hard to reverse. Write these before anything else:

| Area | Minimum set |
|---|---|
| Money | Amount computation in integer minor units for every plan, coupon, proration and tax path, with overflow handled; webhook handler is idempotent (same event twice changes state once); out-of-order events (`updated` before `created`); failed payment leaves entitlements correct; refund path |
| Auth and access | Each protected route rejects no session (401) and wrong role (403); user A cannot read or write user B's or tenant B's rows, tested per resource with two tenants seeded; password reset and email-change tokens are single use and expire; sign-out invalidates the session |
| Data loss | Every destructive action (delete, bulk update, import overwrite) hits only intended rows; migrations tested on seeded data, and those on large or hot tables rehearsed on a production-sized copy (`0x:postgres-database`); restore from backup has been done once for real; cascades delete what is expected and no more |

Write the cross-tenant test as a table over every resource route, so adding a route without
adding it to the table is visible in review. It is the single highest-value test in a
multi-tenant product.

Details for payments flows are in `0x:payments-billing`, for authorization in `0x:auth-identity`,
for restore drills in `0x:postgres-database`.

## Design for testability

The goal is that the logic worth testing can run with no network and no database, and that the
code which does touch them is thin enough to cover with a few integration tests.

- **Functional core, imperative shell.** A handler does: extract and validate input, load data,
  call a pure decision function, persist the result, emit effects. Only the decision function
  has branches; test it exhaustively with plain values. The shell gets a handful of integration
  tests.
- **Return decisions, do not perform them.** The decision is a value, often an enum, that the
  caller executes. Assertions are on data, with no mocks:

```rust
use time::{Duration, OffsetDateTime};

pub struct Subscription {
    pub price_cents: u64,
    pub period_end: OffsetDateTime,
    pub cancel_at_period_end: bool,
}

#[derive(Debug, PartialEq)]
pub enum Renewal {
    NotDue,
    Expire,
    Charge { amount_cents: u64, next_period_end: OffsetDateTime },
}

/// Pure: no clock, database or network. The handler loads, calls this, then executes the result.
pub fn decide_renewal(sub: &Subscription, now: OffsetDateTime) -> Renewal {
    if now < sub.period_end {
        return Renewal::NotDue;
    }
    if sub.cancel_at_period_end {
        return Renewal::Expire;
    }
    Renewal::Charge {
        amount_cents: sub.price_cents,
        next_period_end: sub.period_end + Duration::days(30),
    }
}
```

- **Pass time, randomness and IDs in.** `now: OffsetDateTime` as a parameter or a `Clock` in
  the application state (test-data-flaky.md); never `OffsetDateTime::now_utc()`, a thread-local
  random generator or `Uuid::new_v4()` inside logic whose output a test checks.
- **One wrapper per third party.** Stripe, email, storage and LLM calls each go through one
  struct the app owns, with a narrow API in the app's vocabulary (`billing.charge(...)`) and
  its base URL taken from config, so a test points it at a local fake server. Do not add a
  trait only so a test can swap in a mock: the generics or `dyn` spread through every
  signature, and the mock skips the serialization and error handling where the bugs are. A
  trait earns its place when a second real implementation exists or the boundary has no wire
  to fake (the clock).
- **No hidden globals.** A `static` holding config, a pool or a client, initialized on first
  use (`LazyLock`, `OnceLock`), is shared by every test, and `cargo test` runs a binary's tests
  as threads of one process, so the first test to touch it decides its value. Build the state
  in `main` (the composition root) and pass it through Axum `State`.

Signals of an untestable design: a test needs more than about three fakes; a test must reach
into private state; setup is longer than the assertions; a logic change requires a browser to
verify; a function takes `&PgPool` and also makes an HTTP call and decides prices. Fix the
design, not the test.

## Test-driven development: when it pays

| Situation | Approach |
|---|---|
| Behavior is clear, internal design is open (pricing rules, parser, state machine, permission matrix) | Test first. The tests fix the interface and let the implementation be reshaped freely |
| Bug fix | Always test first: the failing test is the reproduction (see debugging.md) |
| Behavior itself is unknown (new UI, exploratory integration, spike) | Build first, then write tests once the shape survives a day. Tests written during a spike are thrown away with it |
| Glue code with no branching | No unit test; one integration test covers it |

The loop: write one failing test for the next smallest behavior, watch it fail for the right
reason (an assertion, not a compile error or a missing database), make it pass the simplest
way, refactor with the bar green. A test that has never been seen failing is unverified: when
writing tests after the code, break the code once to confirm the test notices. In Rust the
first red is often a compile error; stub the function with `todo!()` so the test compiles and
fails at run time.

When working with a coding agent, writing the tests first and committing them before the
implementation gives the agent a fixed target and stops it from editing tests to fit the code.

## Pre-launch bug bash

Run before first public Launch and before any release that changes signup, checkout or the core
flow. Automated tests do not replace it: they check what was thought of.

1. **Build under test:** the release build (`cargo leptos build --release`) on the
   production-like environment, with real third parties in test mode. Never the watch server:
   a debug build is slower, panics on integer overflow where release wraps, and can hide
   hydration and caching problems.
2. **Charter, 60 to 90 minutes, time-boxed.** One page listing journeys (sign up, verify email,
   onboard, core action, pay, upgrade, cancel, delete account) and personas (new user, returning
   user, admin, invited member). Each participant takes different journeys and devices.
3. **Device matrix:** at minimum one real iPhone with Safari, one real mid-range Android with
   Chrome, one desktop Chromium browser, desktop Safari, desktop Firefox. Browsers on iOS run
   on WebKit almost everywhere (other engines are permitted only in some regions), so one
   iPhone covers them; simulators miss keyboard, safe-area, autofill and performance problems.
   A low-end Android also shows how long the WASM bundle takes to download and hydrate.
4. **Hostile conditions:** throttle to the slowest network preset in DevTools and repeat
   signup and checkout; click before the page has hydrated; go offline mid-submit;
   double-click every submit button; use back and refresh in the middle of multi-step flows;
   open the same flow in two tabs; paste a 5,000 character string and emoji into text fields;
   use a password manager and browser autofill; set the device to a non-UTC time zone and a
   non-English locale; set system font size to large; follow every transactional email link
   on a phone.
5. **Logging:** one shared list; each entry has steps, expected, actual, device, screenshot or
   recording, severity. No fixing during the session.
6. **Triage immediately after:** blockers fixed before launch, the rest scheduled or closed.
   Every blocker gets an automated test at the cheapest layer that would have caught it.

Solo: recruit two or three outsiders for an hour; the author is blind to their own assumptions.
Watching one person who has never seen the product attempt signup finds more than a day of
self-testing.

## Release criteria

Criteria are written down so that a contractor, a CI job or a tired founder at midnight can
answer "can this ship?" without judgment calls. Each criterion is a yes or no with a place to
look. A workable Launch-stage set:

- `cargo fmt --check`, clippy with warnings denied, `cargo sqlx prepare --check`, `cargo deny
  check`, and the unit, integration and doctest suites green on the release commit.
- End-to-end suite for critical journeys green against the preview deploy of that commit (staging
  where one exists, `0x:ci-cd-release`).
- No open bug of severity S1 or S2 (definitions in debugging.md); known S3 bugs listed.
- Each migration is backward compatible with the previous app version, or a maintenance window
  is announced; migrations on large or hot tables were rehearsed on a production-sized copy
  (`0x:postgres-database`, migrations.md).
- Rollback path stated and tested for this release (previous image redeployable, flags off).
- The production smoke test passes, and error rate and latency stay normal through the
  post-deploy watch.
- For changes to billing, auth or data deletion: a second pair of eyes or a manual run of the
  affected journey in test mode, recorded in the pull request.

Put the automated ones in CI as required checks so they enforce themselves (pipeline setup is in
`0x:ci-cd-release`), and keep the manual ones in a short checklist in the pull-request template.
A criterion that is routinely waived is deleted or automated; a waived rule teaches that all
rules are optional.

By stage: Prototype needs "it builds and the main path works". Launch needs the list above.
Scale adds staged rollout with automatic halt on error-rate regression, and an error budget that
freezes feature releases when exhausted (see `0x:site-reliability`).

## Judging the suite

Coverage measures which lines ran, not whether anything was asserted. Use it to find untested
areas, not as a target: a global threshold produces assertion-free tests of easy code. Measure
it with cargo-llvm-cov (`cargo llvm-cov nextest` runs the suite through nextest). Useful uses:
a per-module floor on the money, auth and permissions code (as a rule of thumb, 90% or more
branch coverage there), and "coverage must not drop" on changed files.

The measures that show whether the suite works:

| Measure | How to get it | Read it as |
|---|---|---|
| Escaped defects | Tag each production bug with the layer that should have caught it | A cluster in one layer or module says where the next tests go |
| Change failure rate | Share of deploys that needed a rollback, hotfix or patch | Rising rate with a green suite means the suite tests the wrong things |
| Time to green | Local run and CI wall-clock for the default suite, compile included | Over about 10 minutes in CI, people batch changes and stop running tests locally |
| Flake rate | Share of CI runs that pass on re-run with no code change (nextest reports these as flaky) | Rule of thumb: above about 1% of runs, trust is eroding; see test-data-flaky.md |
| Test churn | Tests modified per behavior-preserving refactor | High churn means tests are bound to implementation |
| Mutation score on critical modules | cargo-mutants, see unit-integration-tests.md | Missed mutants are missing assertions |

Run a five-minute review of escaped defects monthly at Launch. For each: which test would have
caught it, at which layer, and is there a class of similar bugs. Write the test for the class,
not only the instance.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Suite is green, production breaks weekly | Tests mock the seams where bugs live | Move weight to integration tests with a real database and faked third-party HTTP |
| Every refactor breaks dozens of tests | Tests assert on internals, call order, or mock expectations | Assert on outputs and persisted state through public interfaces |
| End-to-end suite takes 40 minutes and flakes | Edge cases tested through the browser | Push cases down to integration; keep one happy path and one key failure per journey |
| High coverage, bugs in covered code | Lines executed without meaningful assertions | Mutation-test the module; add assertions on results and side effects |
| Minutes pass before the first test runs | Compile and link time: many integration-test binaries, heavy dev profile | One integration-test binary, nextest, a faster linker (unit-integration-tests.md) |
| Nobody runs tests locally | Slow or needs manual setup | One command, starts its own dependencies, default run under a minute |

## Ask the user

- **Which failures would cost real money or trust?** Sets the risk-first list beyond the
  defaults. Assume: payments, sign-in, cross-account data access and irreversible deletes.
- **What stage is the product at?** Prototype gets a smoke test and the money, auth and data
  loss set only; Launch gets the full release criteria. Assume Launch if there are paying users.
- **Which browsers and devices do customers actually use?** Drives the bug-bash and end-to-end
  matrix. Assume current Chrome, Safari (desktop and iOS) and Firefox, plus one Android phone.
- **Who besides the founder can decide a release is good?** If the answer is nobody, criteria
  must be fully automated. Assume nobody.
- **How long may the default test run take before it gets skipped?** Assume under 1 minute
  locally for the unit and integration run on changed code, and under 10 minutes for full CI.
