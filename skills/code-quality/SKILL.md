---
name: code-quality
description: Keeps Rust code correct and changeable with test strategy, unit, integration, end-to-end, contract and visual tests, debugging, refactoring, clippy, types, unsafe policy and developer docs. Use when asked to write tests or decide what to test, set up cargo-nextest, sqlx::test or browser tests, fix a flaky or slow suite, find a bug or memory leak, refactor or rewrite, configure clippy and lints, or write a README.
---

# Testing, debugging, refactoring and documentation

## Stance

Quality work is risk management under a fixed attention budget. A solo founder cannot test,
document or clean everything, so each check is placed where a failure would cost the most and
at the cheapest layer that can see it. The measure is not coverage or tidiness; it is whether
changes reach production without breaking things and whether the next change stays cheap.

- **Allocate by risk, not evenly.** Money, access control and data loss get thorough tests
  from the first real user; a settings page gets none until it breaks. Their failures are
  silent, expensive and hard to reverse.
- **Push every check to the cheapest layer that can observe the failure.** The compiler and
  clippy before unit tests, unit before integration, integration before browser. Each step up
  costs far more to run, diagnose and maintain (as a rule of thumb, about an order of
  magnitude), and in Rust compile and link time is part of that cost.
- **Use the real thing inside the system and fake only at its edge.** A real Postgres of the
  production major, the real Axum router with its middleware and the real modules; fakes for
  third-party HTTP, the clock and randomness. Mocks of internal code, and traits invented only
  so a test can swap them, test the mock and freeze the design.
- **A red result must mean a defect.** A test that fails for any other reason trains everyone
  to re-run and ignore. Flaky tests are quarantined the same day and fixed or deleted within
  weeks; warnings are denied in CI or switched off.
- **No fix without a reproduction, no reproduction without a regression test.** A bug that was
  never made to fail on demand cannot be shown fixed. The failing test is the proof before and
  the guard after.
- **Change structure or behavior, never both in one step.** Small behavior-preserving steps
  under green tests, committed separately from behavior changes, keep review, bisect and
  revert usable.
- **Assert on what users and callers observe.** Outputs, persisted state, visible text and
  labels survive refactoring; internals, call order and CSS paths break on every change while
  missing real bugs.
- **Automate the rule or drop it.** Style, lint levels, crate boundaries, release criteria and
  doc examples are enforced by a tool in CI or they erode. A rule that is routinely waived
  teaches that all rules are optional.
- **Design decides testability.** Pure decision functions with time, randomness and I/O passed
  in need no mocks, and a type that cannot hold an invalid value needs no test for it. When a
  test is hard to write, fix the design, not the test.

## Route

| If the task is | Read |
|---|---|
| Deciding what to test, how much is enough, whether to write tests first, planning a pre-launch bug bash, or writing down what must pass before a release | `references/test-strategy.md` |
| Writing tests for business logic, SQLx queries, Axum routes or Leptos components; deciding what to fake; covering timeouts, retries and races; a slow or slow-to-compile suite; proptest or cargo-mutants | `references/unit-integration-tests.md` |
| Browser tests with thirtyfour, a sign-up, sign-in, checkout or email journey, a browser test failing only in CI, screenshot diffing, guarding an API or server function against breaking its clients, or whether Playwright is worth a Node toolchain | `references/e2e-contract-visual.md` |
| Tests that pass alone and fail together, intermittent failures, factories and a seed binary, test isolation, frozen clocks and paused Tokio time, nextest retries and sharding, or production-shaped data for migration tests | `references/test-data-flaky.md` |
| A bug report to triage, a bug whose cause is unknown, a production-only bug or panic, finding the commit that broke something, a server whose memory keeps growing, an async stall or an intermittent race | `references/debugging.md` |
| Cleaning up or restructuring code, changing untested legacy code, removing dead code, a mechanical change across many files, a Rust edition or major crate upgrade, porting an existing app to Rust, or "rewrite or fix in place?" | `references/refactoring.md` |
| Setting up or tightening clippy, rustfmt, workspace lints, pre-commit hooks or the unsafe policy; newtypes and enums for domain states; unused dependencies; compile-time checked queries; enforcing crate boundaries | `references/static-analysis-types.md` |
| Writing a README, setup instructions, architecture notes, code comments, rustdoc, developer guides or a handover package, or fixing stale docs | `references/technical-docs.md` |

A bug that needs a test, or a refactor that needs characterization tests, uses two files: the
method file first, then the test file for the layer.

## Defaults at a glance

Follow the project's existing runner, linter and conventions before any of these.

| Area | Default |
|---|---|
| Suite shape | Wide integration middle: Axum routes tested through the router against real Postgres, pure logic unit-tested, 5 to 15 browser journeys |
| Runners | `cargo test` to write and run single tests, cargo-nextest for the suite locally and in CI, `cargo test --doc` for doctests (nextest skips them) |
| Database in tests | `#[sqlx::test]`: a fresh database per test with the real migrations, same Postgres major as production; functions take `&mut PgConnection` where the caller owns the transaction |
| Third parties | One client struct per vendor with its base URL from config; wiremock servers from recorded sandbox responses, `.expect(n)` on each mock; a scheduled drift check against the sandbox |
| Test data | Factory structs with `Default` that are valid and unique; in a test-support crate shared with the seed binary, which refuses to run against production |
| Time and randomness | A `Clock` passed in, paused Tokio time for timers, seeded generators, proptest regression files committed |
| Components | Leptos views rendered to HTML on the server for output; wasm-bindgen-test in a headless browser for interaction |
| Browser tests | thirtyfour against a release build, label, text and test-ID selectors, a hydration marker before acting, no fixed sleeps, screenshot and HTML saved on failure, retries in CI only |
| Flaky tests | Pass-on-retry counts as flaky; quarantine the same day, fix or delete in about two weeks |
| Types | Newtypes and enums so invalid states do not compile; `unsafe_code = "forbid"`; SQLx `query!` macros with `.sqlx` offline data committed |
| Lint and format | `[workspace.lints]` in the root `Cargo.toml`, `[lints] workspace = true` in every crate; `cargo clippy --all-targets --all-features -- -D warnings` and `cargo fmt --check`; rustfmt defaults; toolchain pinned |
| Hooks | `cargo fmt --check` and a secret scan in pre-commit, under about 3 seconds; clippy and tests on pre-push or CI only |
| Bug fixes | Reproduce, bisect when theories run out, failing regression test first, fix the cause |
| Refactoring | Only code the current task touches; rust-analyzer for renames and moves; structural commits separate; incremental replacement over rewrite |
| Docs | Markdown in the repository, changed in the same pull request; README, one-page architecture notes, rustdoc with tested examples on shared crates, agent instruction file |

By stage:

| | Prototype | Launch | Scale |
|---|---|---|---|
| Tests | Smoke test of the main path, plus money, auth and data-loss tests once any real user exists | Risk-first set, integration tests per route, critical journeys end to end, written release criteria | Sharded nextest runs, post-deploy smoke subset, mutation testing on critical modules, contract checks for independent consumers |
| Static checks | rustfmt, default clippy, pinned toolchain and forbidden `unsafe` from the first commit (free at the start, costly later) | Workspace lints against `unwrap`, indexing and lossy casts in request paths, `cargo sqlx prepare --check`, unused-dependency check | Crate boundaries enforced, a ratchet on `#[expect]` counts, Miri on any crate with `unsafe` |
| Debugging | Read the error and the panic location, reproduce, fix | Severity levels, regression test per bug, line tables in release builds, request IDs in tracing spans, panics captured by the error tracker | Flag-scoped log levels in production, read-only roles, monthly escaped-defect review |
| Refactoring | Do not; the code may be deleted | As part of the change that needs it | Planned strangler migrations for foundation problems |
| Docs | README and `.env.example` | Tested quickstart, architecture notes, deploy and rollback notes | How-to guides, owners and review dates, ownership map |

## Before you call it done

1. `cargo fmt --check` and `cargo clippy --all-targets --all-features -- -D warnings` pass on
   the final state (for Leptos, for the server and the WASM client features), and CI runs both.
2. Every new test was seen failing for the right reason (written first, or the code was
   broken once to confirm the test notices).
3. A bug fix includes a regression test that failed before the fix, and sibling occurrences
   of the same pattern were searched for.
4. Changes touching money, auth or tenant data have tests for the unauthorized, wrong-tenant,
   duplicate-delivery and partial-failure cases, asserting on database state.
5. No test reaches the real network, real clock or shared mutable data: unexpected requests
   fail, time is injected or paused, data comes from factories.
6. No fixed sleeps, no raised timeouts or retry counts used as a fix, no `#[ignore]` left
   without a linked issue in its reason.
7. New tests pass alone, in the full parallel run, and repeated (20 or more runs for anything
   involving concurrency or the browser).
8. Assertions are on outputs, persisted state or user-visible behavior; no mocks of the
   project's own modules or the database.
9. The default local run is still fast (about a minute for changed code, compile included)
   and CI stays under about 10 minutes, or the slow part was identified.
10. Refactoring commits change no behavior and are separate from behavioral commits; tests
    did not need rewriting to stay green.
11. Code made unreachable by the change is deleted, along with its tests, flags, dependencies,
    features and docs.
12. No new `unwrap()` or `expect()` in a request path, `unsafe`, `as` cast on money, or
    `#[allow]` without a reason; `cargo sqlx prepare --check` shows no drift.
13. Docs the change made false are updated in the same change: README commands, env example,
    architecture notes, rustdoc, agent instruction file.
14. Setup instructions and any documented command were run, not assumed.

## Not this skill

- Reviewing the current diff for bugs → `code-review`
- The CI pipeline that runs the checks, and deploys → `0x:ci-cd-release`
- Load tests and performance profiling → `0x:web-performance`
- Security testing and penetration tests → `0x:web-security`
- Pull-request conventions and code-review practice → `0x:git-collaboration`
- Help-center articles and customer-facing support docs → `0x:sales-support`
