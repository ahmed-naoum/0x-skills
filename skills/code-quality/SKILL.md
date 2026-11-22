---
name: code-quality
description: Keeps code correct and changeable through test strategy, unit, integration, end-to-end, contract and visual tests, test data, debugging method, refactoring, linting, strict types and developer documentation. Use when asked to write tests or decide what to test, set up Vitest or Playwright, fix a flaky or slow suite, find the cause of a bug or memory leak, refactor or rewrite code, tighten TypeScript, or write docs.
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
- **Push every check to the cheapest layer that can observe the failure.** Types and lint
  before unit tests, unit before integration, integration before browser. Each step up costs
  roughly ten times more to run, diagnose and maintain.
- **Use the real thing inside the system and fake only at its edge.** A real database of the
  production engine, the real HTTP layer and the real modules; fakes for third-party networks,
  the clock and randomness. Mocks of internal code test the mock and freeze the design.
- **A red result must mean a defect.** A test that fails for any other reason trains everyone
  to re-run and ignore. Flaky tests are quarantined the same day and fixed or deleted within
  weeks; warnings are either errors or off.
- **No fix without a reproduction, no reproduction without a regression test.** A bug that was
  never made to fail on demand cannot be shown fixed. The failing test is the proof before and
  the guard after.
- **Change structure or behavior, never both in one step.** Small behavior-preserving steps
  under green tests, committed separately from behavior changes, keep review, bisect and
  revert usable.
- **Assert on what users and callers observe.** Outputs, persisted state, visible text and
  roles survive refactoring; internals, call order and CSS paths break on every change while
  missing real bugs.
- **Automate the rule or drop it.** Style, strictness, boundaries, release criteria and doc
  examples are enforced by a tool in CI or they erode. A rule that is routinely waived
  teaches that all rules are optional.
- **Design decides testability.** Pure decision functions with time, randomness and I/O
  passed in need no mocks. When a test is hard to write, fix the design, not the test.

## Route

| If the task is | Read |
|---|---|
| Deciding what to test, how much is enough, whether to write tests first, planning a pre-launch bug bash, or writing down what must pass before a release | `references/test-strategy.md` |
| Writing tests for business logic, database code, API routes or React components; deciding what to mock; covering timeouts, retries and races; a slow unit suite; property-based or mutation testing | `references/unit-integration-tests.md` |
| Setting up Playwright, testing a sign-up, sign-in, checkout or email journey in a browser, a browser test failing only in CI, screenshot diffing, or guarding an API against breaking its clients | `references/e2e-contract-visual.md` |
| Tests that pass alone and fail together, intermittent failures, a seed script, factories, test isolation, fake clocks, parallelizing or sharding, or production-shaped data for migration tests | `references/test-data-flaky.md` |
| A bug report to triage, a bug whose cause is unknown, a production-only bug, finding the commit that broke something, a server memory leak, or an intermittent race | `references/debugging.md` |
| Cleaning up or restructuring code, changing untested legacy code, removing dead code, a codemod, a framework or Node major upgrade, or "rewrite or fix in place?" | `references/refactoring.md` |
| Setting up or tightening TypeScript, ESLint, Biome, Prettier or pre-commit hooks; finding unused code or circular imports; generating types from a schema; enforcing module boundaries | `references/static-analysis-types.md` |
| Writing a README, setup instructions, architecture notes, code comments, developer guides or a handover package, or fixing stale docs | `references/technical-docs.md` |

A bug that needs a test, or a refactor that needs characterization tests, uses two files: the
method file first, then the test file for the layer.

## Defaults at a glance

Follow the project's existing runner, linter and conventions before any of these.

| Area | Default |
|---|---|
| Suite shape | Wide integration middle: routes tested through HTTP against real Postgres, pure logic unit-tested, 5 to 15 browser journeys |
| Runners | Vitest for unit and integration, Playwright for end-to-end, Testing Library for components |
| Database in tests | Same engine and major version as production, real migrations applied, one database per worker from a template, per-test transaction rollback where the code allows |
| Third parties | Network-level fakes (MSW) from recorded sandbox responses, unhandled requests fail the test, scheduled drift check against the sandbox |
| Test data | Factories that are valid and unique by default; one idempotent seed script built on them, guarded against production |
| Time and randomness | Injected or frozen; test process pinned to UTC plus explicit far-zone cases |
| Browser tests | Production build, role and label locators, saved auth state, no fixed sleeps, trace on first retry, retries in CI only |
| Flaky tests | Pass-on-retry counts as flaky; quarantine the same day, fix or delete in about two weeks |
| Types | `strict` plus `noUncheckedIndexedAccess`; `tsc --noEmit` as the first CI job |
| Lint and format | Biome on greenfield, or ESLint flat config with typescript-eslint type-checked rules plus Prettier; tool defaults; zero warnings |
| Hooks | Format and lint staged files in under about 3 seconds; type check and tests on pre-push or CI only |
| Bug fixes | Reproduce, bisect when theories run out, failing regression test first, fix the cause |
| Refactoring | Only code the current task touches; structural commits separate; incremental replacement over rewrite |
| Docs | Markdown in the repository, changed in the same pull request; README, one-page architecture notes, agent instruction file |

By stage:

| | Prototype | Launch | Scale |
|---|---|---|---|
| Tests | Smoke test of the main path, plus money, auth and data-loss tests once any real user exists | Risk-first set, integration tests per route, critical journeys end to end, written release criteria | Sharded CI, post-deploy smoke subset, mutation testing on critical modules, contract checks for independent consumers |
| Static checks | Strict types and a formatter from the first commit (free at the start, costly later) | Type-aware lint rules, unused-code check, generated types with a drift check | Import-boundary rules, ratchets on legacy strictness |
| Debugging | Read the error, reproduce, fix | Severity levels, regression test per bug, source maps and request IDs in telemetry | Flag-scoped production debugging, read-only roles, monthly escaped-defect review |
| Refactoring | Do not; the code may be deleted | As part of the change that needs it | Planned strangler migrations for foundation problems |
| Docs | README and `.env.example` | Tested quickstart, architecture notes, deploy and rollback notes | How-to guides, owners and review dates, ownership map |

## Before you call it done

1. Type check and lint pass with zero warnings on the final state, and CI runs both.
2. Every new test was seen failing for the right reason (written first, or the code was
   broken once to confirm the test notices).
3. A bug fix includes a regression test that failed before the fix, and sibling occurrences
   of the same pattern were searched for.
4. Changes touching money, auth or tenant data have tests for the unauthorized, wrong-tenant,
   duplicate-delivery and partial-failure cases, asserting on database state.
5. No test reaches the real network, real clock or shared mutable data: unhandled requests
   fail, time is frozen or injected, data comes from factories.
6. No fixed sleeps, no raised timeouts or retry counts used as a fix, no `.skip` or `.only`
   left behind without a linked issue.
7. New tests pass alone, in a shuffled order, and repeated (20 or more runs for anything
   involving concurrency or the browser).
8. Assertions are on outputs, persisted state or user-visible behavior; no mocks of the
   project's own modules or the database.
9. The default local test run is still fast (about a minute for changed code) and CI stays
   under about 10 minutes, or the slow part was identified.
10. Refactoring commits change no behavior and are separate from behavioral commits; tests
    did not need rewriting to stay green.
11. Code made unreachable by the change is deleted, along with its tests, flags, dependencies
    and docs.
12. No new `any`, non-null assertion, `@ts-ignore` or lint disable without a stated reason;
    generated types were regenerated and show no drift.
13. Docs the change made false are updated in the same change: README commands, env example,
    architecture notes, agent instruction file.
14. Setup instructions and any documented command were run, not assumed.

## Not this skill

- Reviewing the current diff for bugs → `code-review`
- The CI pipeline that runs the checks, and deploys → `0x:ci-cd-release`
- Load tests and performance profiling → `0x:web-performance`
- Security testing and penetration tests → `0x:web-security`
- Pull-request conventions and code-review practice → `0x:git-collaboration`
- Help-center articles and customer-facing support docs → `0x:sales-support`
