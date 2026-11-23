# Verifying and reviewing agent work

Read this when: deciding how agent output is checked before it merges, setting up the feedback
loop an agent runs against, reviewing an agent's diff, deciding how deep to review, or adding
AI review to CI.

## The feedback loop decides the quality

An agent converges on whatever its checks reward. With fast, specific checks it fixes most of
its own mistakes before a human sees them; with none, the reviewer becomes the test suite.
Invest here before investing in prompts.

| Check | Target time (rule of thumb) | When the agent runs it |
|---|---|---|
| Typecheck | Seconds | After each batch of edits (Stop hook, see `context-setup.md`) |
| Format and lint on changed files | Seconds | After each edit (PostToolUse hook) |
| Tests for the touched module | Under 30 seconds | At every plan step |
| Full unit and integration suite | A few minutes | Before each commit |
| End-to-end smoke | Minutes | Before the pull request |
| Running app, looked at in a browser | | Every UI change |

```bash
pnpm typecheck                                      # tsc --noEmit
pnpm vitest run src/features/billing                # one module
pnpm vitest related --run src/features/billing/export.ts   # tests that import a file
pnpm playwright test --grep @smoke                  # tagged smoke subset
```

A UI the agent cannot see is a UI it cannot verify. Give it a way to load pages and take
screenshots (a browser automation MCP server or Playwright scripts) and a seeded account to
log in with. A slow or flaky suite trains agents, and people, to ignore red; fixing that is
`0x:code-quality` work and pays back on every run.

## Proof, not claims

An agent's summary is a claim; command output and CI are evidence. Require with every
completed task:

- The commands run, with the tail of their output and the test count, not only "passed".
  A filter that matched no tests, or a skipped file, can look like success.
- For a bug fix: the failing output before the fix and the passing output after.
- The tests added, each with one line on what behavior it pins.
- For UI: screenshots of the relevant states (empty, loading, error, long content, narrow
  width), taken from the running app.
- Every changed file with one line on why, and anything skipped or uncertain.

"Verified" with no output attached means not verified. CI re-runs everything from a clean
checkout; treat a red CI after a green agent report as the normal case to plan for, not an
anomaly.

## Review every diff like a junior's pull request

Agents write like a fast, confident junior with no memory of the project's history: plausible,
eager to finish, and unaware of what was tried before. Review in this order, because the early
steps catch most problems for the least effort:

1. **Scope.** `git diff --stat main...HEAD` against the brief. Every unexpected file is a
   question before anything else is read.
2. **Tests.** Read them before the code. Do they encode the acceptance criteria, including the
   negative cases? Would they fail without the change?
3. **Interfaces.** Exported signatures, schemas, API shapes, configuration, environment
   variables, new dependencies.
4. **Mechanical scan** for patterns that hide problems (below).
5. **The logic**, error handling, naming and duplication.
6. **Run it.** Pull the branch and use the feature once.

```bash
git diff --stat main...HEAD
git diff main...HEAD -U0 | grep -E '^\+.*(\.only\(|\.skip\(|@ts-ignore|@ts-expect-error|eslint-disable|as any|TODO)'
git diff --name-only main...HEAD -- '*.test.*' '*.spec.*' 'vitest.config.*' 'playwright.config.*' \
  'eslint.config.*' 'tsconfig*.json' '.github/' 'package.json' '.claude/' 'CLAUDE.md' 'AGENTS.md'
```

The last command lists changes to tests, tooling and agent configuration. Each needs a reason;
a test or config change nobody asked for is the most common way an agent turns red into green.

Review depth follows the risk tier, not the size of the diff:

| Tier | Examples | Review |
|---|---|---|
| 0 | Docs, test-only changes, internal scripts, copy | Skim scope and CI result |
| 1 | Feature code following an existing pattern, UI | Full review in the order above; run it |
| 2 | Auth and authorization, payments, migrations, permissions, deletion, crypto, infrastructure, CI and agent config | Line by line; write or check the critical tests yourself; second reviewer where one exists |

## Failure modes

| Symptom in the diff | Cause | How to catch it |
|---|---|---|
| Method, option or config key that does not exist | Training on other versions or other libraries | Typecheck; for untyped config, ask for the doc link and check it |
| New dependency with an unfamiliar or slightly-off name | Invented package name; attackers register commonly invented names | Check every new dependency: `npm view <name> repository.url` and its publish history; reject unknown publishers |
| Expected value changed, assertion removed, `.skip`, looser matcher, raised timeout | Rewarded for green | Diff test files separately; freeze tests written first (below) |
| Coverage threshold lowered, lint rule disabled, `strict` loosened, CI step removed | Same, one level up | The config-file list above; CODEOWNERS on tooling paths |
| Reformatted or renamed files unrelated to the task | "While I was here" | Formatter hook so noise never appears; reject or split |
| `catch` that returns a default, `?? []` hiding a null, silent retries | Making errors disappear instead of handling them | Read every new `catch`; ask what the caller should see on failure |
| Helper duplicating one that exists | Did not search | Ask which existing utilities were considered; search for similar names |
| Special case that matches only the test input | Satisfying the test, not the behavior | Read the implementation for test-specific values; add a second case |
| Copied legacy pattern | It was the nearest example | Label legacy code; name the canonical exemplar in the brief |
| Stub, placeholder data or mock left in a production path | Unfinished step reported as done | Search the diff for TODO, mock and placeholder strings |
| Endpoint without authorization, tenant filter missing | Copied a route without its guard | Tier 2 review; cross-tenant test |
| "Done" with checks never run | Optimistic summary | Require output; rely on CI |

## Extra scrutiny: auth, payments and migrations

These areas combine high blast radius with mistakes that tests written by the same agent
rarely catch, because the agent's tests share its blind spot.

| Area | What agents get wrong | Check yourself |
|---|---|---|
| Authentication and authorization | New route without the guard; query filtered by ID but not by tenant; trusting a user or workspace ID from the request body; cookie or session flags changed | Write the cross-tenant test: a user of A requests B's resource and gets 404 or 403. Compare guards with a sibling route (`0x:auth-identity`) |
| Payments | Amount or price taken from the client; webhook without signature check or event dedupe; retry without an idempotency key; floating-point money | Run the payments checklist in `0x:payments-billing` |
| Migrations | Table-rewriting change on a large table; `NOT NULL` without default or backfill; destructive change in one step; editing an applied migration; backfill inside the migration | Expand and contract; run against a production-sized copy; read the generated SQL (`0x:postgres-database`) |
| Deletion and retention jobs | Missing tenant filter, wrong date comparison | Dry-run mode that counts rows first |
| CI, infrastructure, agent config | Widened permissions, new secrets in jobs, hooks that run commands | Treat as security changes (`permissions-governance.md`) |

Enforce it structurally: a `CODEOWNERS` file listing these paths with required code-owner
review, and a pull request template checkbox for "touches tier 2 paths". The agent never runs
a migration against a shared or production database; migrations ship through the deploy
pipeline.

## Failing tests first, and tests that assert something

Tests written after the code tend to describe what the code does, bugs included. Tests written
first describe what it should do, and they are the cheapest artifact to review.

1. The agent writes tests from the acceptance criteria only, with no implementation.
2. It runs them and shows the failure. They must fail **for the right reason**: an assertion
   about the behavior, not an import error, a typo or a missing fixture.
3. The human reviews the tests. This is the spec in executable form.
4. Commit the tests.
5. The agent implements without touching them. Check that
   `git diff <tests-commit> HEAD -- '*.test.*'` is empty. If a test is truly wrong, the agent
   stops and explains instead of editing it.
6. Sanity mutation: break the implementation on purpose (invert a condition, return early)
   and confirm a test fails. For critical modules, run a mutation testing tool periodically.

Reject tests that:

- assert nothing, or only `toBeDefined()` or `toBeTruthy()` on a computed value;
- snapshot logic output that nobody will read when it changes;
- mock the module under test, or mock so much that only the mocks are exercised;
- compute the expected value with the same logic as the implementation;
- catch the error they should be asserting on;
- carry a name that promises more than the assertions check.

Lint for the first case: the `expect-expect` rule of the Vitest ESLint plugin flags tests
without assertions, and `expect.hasAssertions()` guards async tests whose assertions might not
run.

## AI code review in CI, human merge approval

An AI reviewer on every pull request catches a useful share of bugs cheaply, provided it stays
an extra reviewer and never becomes the approver.

- **Approval stays human.** Keep the repository setting that lets GitHub Actions create and
  approve pull requests off unless a workflow needs it, and never count a bot approval. Rulesets
  on `main`: pull request required, status checks required, force pushes blocked. In a team,
  one human approval, "require approval of the most recent reviewable push" (so an agent push
  after approval resets it), and code-owner review on tier 2 paths.
- **Solo founder.** GitHub does not let an author approve their own pull request, so the
  control is different: agents never merge, their tokens cannot bypass rulesets, and the
  founder merges after green CI and their own review.
- **Independent context.** The reviewer sees the diff and the brief, not the author's session.
  A model reviewing inside the conversation that produced the code tends to agree with it.
- **Prompt for signal.** Correctness, security, missing tests, scope against the description;
  only high-confidence findings, each with file and line; no style comments (the linter owns
  style). If most comments get dismissed, tighten the prompt or turn it off; noise trains
  everyone to ignore it.
- **Cost.** Run on pull requests marked ready for review, not on every push to a draft; skip
  or use a lighter prompt on dependency-bot pull requests.

Hunting bugs in one specific diff is the `code-review` skill. The workflow mechanics of CI and
its secrets are `0x:ci-cd-release`.

## Keep your own model of the architecture

Agents add code faster than a person absorbs it. After a few months of merging what passes
CI, the founder owns a system they cannot debug during an incident. Counter it deliberately:

- **No merge that cannot be explained in two sentences**: what changed and why it is safe.
- **Own the architecture document.** A short `docs/architecture.md`: modules, data flow,
  invariants, where each kind of logic lives. Agents may propose updates in their pull
  requests; a human edits and accepts them.
- **Encode boundaries as checks.** Import restrictions (ESLint rules or dependency-cruiser) so
  a module reaching into another's internals fails CI instead of relying on memory.
- **Monthly walk-through.** Have an agent list the most-changed modules and the new
  dependencies of the month; read those hot spots. Ask it to explain one module and compare
  with the mental model; each disagreement is a doc fix or a code fix.
- **Keep hands on the core.** Write some core code yourself, and debug incidents yourself
  first before asking an agent; that is where the model of the system is rebuilt.
- Structural decisions go into decision records (`0x:engineering-leadership`).

## Ask the user

- **Which paths in this product are high risk?** They get line-by-line review and code
  owners. Default: auth, billing, migrations, permissions, deletion jobs, infrastructure, CI
  and agent configuration.
- **How much review time is realistic per pull request?** It sets task size and how much
  automation is worth adding. Default: 30 minutes for tier 1, unlimited for tier 2.
- **Should an AI reviewer run on every pull request?** It costs money and attention. Default:
  on ready-for-review pull requests, high-confidence findings only.
- **Who may merge?** Default: humans only; no agent or bot token can merge or bypass rules.
