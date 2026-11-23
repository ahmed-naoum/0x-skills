# Scoping and delegating work

Read this when: deciding what to hand to a coding agent and how to brief it, splitting a large
feature into agent-sized tasks, or an agent run is drifting and needs redirecting or restarting.

## The agent-sized task

A task is ready to delegate when all four hold:

1. **One reviewable change.** Rule of thumb: a diff you can review properly in under 30 minutes,
   usually a few hundred changed lines at most, excluding generated files and snapshots.
2. **A done check a machine can run.** A command that goes from red to green, or a screenshot
   compared with a stated expectation. "Make it better" has no done check.
3. **The files it may touch are nameable in advance.** If you cannot say where the change goes,
   the first task is investigation, not implementation.
4. **The decisions are already made.** If the task needs a design choice, split off an
   "options, no code" task first.

| Task shape | How to hand it over |
|---|---|
| You already know the one-line fix | Do it yourself; briefing costs more than typing |
| Small, obvious, single file | One prompt with the done check; no written spec |
| Meets all four criteria | Written brief (below), plan, then implementation |
| Fails criterion 1 | Split into tasks with checkpoints |
| Fails criterion 3 | Investigation task: "find where X happens, report files and call paths, edit nothing" |
| Fails criterion 4 | Options task first, decide, then delegate |

## What to delegate first: blast radius against verifiability

Delegate in proportion to how well mistakes are caught automatically and how much damage an
uncaught mistake does.

| | Mistakes caught by types and tests | Mistakes hard to catch |
|---|---|---|
| **Low blast radius** | Delegate freely: tests for existing behavior, call-site migrations, typed refactors, CRUD copying an existing module, scripts, fixtures, docs | Delegate, then review closely: UI copy and layout, logging, error messages, performance tweaks |
| **High blast radius** | Delegate in small steps with deep review: new endpoints behind existing auth guards, schema additions, background jobs | Write it yourself or pair line by line: authorization rules, money movement, destructive migrations, security boundaries |

The first weeks with agents on a repository decide whether trust is calibrated. Start in the
top-left cell. Each mistake there is cheap and teaches what belongs in the project instruction
file (see `context-setup.md`). Move to harder cells only when the feedback loop catches most
errors before review.

## Code you write or deeply read yourself

Some code must stay in the founder's head because it is what gets debugged under pressure,
argued about with customers, or examined after a breach. An agent may draft it; the human
rewrites or reads every line until each line's failure mode is clear without the agent.

| Area | Why it stays yours |
|---|---|
| Domain model and core schema | Every later task builds on it; a wrong shape compounds for years |
| Authorization rules (who sees what, tenant scoping) | One missing check is a data breach; agents copy guards inconsistently |
| Money paths: charges, refunds, credits, entitlements | Errors move real money and surface as chargebacks |
| Migrations that rewrite or delete production data | Not reversible by reverting code |
| Trust boundaries: input validation, sessions, crypto, webhooks | Agents produce plausible code that skips the one check that matters |
| Public API and webhook contracts | Other people depend on them; changes are hard to take back |
| Module boundaries and the architecture skeleton | Agents follow the structure they find; they rarely improve it |

Test for "deeply read": the change can be explained in two sentences (what changed, why it is
safe) and debugged at 3 a.m. without asking the agent what it does.

## The brief

Write the brief as a file or an issue so it survives context resets and can be reused when a
run is restarted. The product decision (what the feature should do and for whom) comes from
`0x:product-discovery`; the brief wraps that decision for an agent.

```markdown
## Goal
Members can export a workspace's invoices for a date range as CSV from the billing page.

## Context (read these first)
- Pattern to copy: src/features/reports/export-orders.ts and its test
- Query layer: src/db/queries/invoices.ts (add the query there, no SQL in the route)
- Guard: requireWorkspaceMember() in src/auth/guards.ts

## Constraints
- Do not change the invoices schema or any migration
- No new dependencies; use the existing toCsv() helper
- Amounts stay integer minor units; format only at the CSV edge

## Acceptance criteria
- GET /api/workspaces/:id/invoices/export?from&to returns text/csv with the header in docs/export-format.md
- A member of workspace A gets 404 for workspace B (test)
- A range over 366 days returns 400 (test)
- pnpm typecheck, pnpm lint and pnpm vitest run src/features/billing pass

## Out of scope
- Scheduled exports, PDF, any UI beyond one button

## Deliver
Plan first and wait for approval. Then one commit per green step, and a summary:
each file changed and why, test output, anything uncertain.
```

What makes the difference:

- **"Pattern to copy" beats describing conventions.** Agents imitate the code they read; one
  named exemplar file carries more convention than a paragraph.
- **Acceptance criteria are observable behavior plus commands.** Include the negative cases
  (wrong tenant, bad input) explicitly; agents test the happy path unless told otherwise.
- **"Out of scope" prevents the most common over-reach.** Without it, adjacent improvements
  appear in the diff and double the review.
- **Name the trap you already know about** ("the invoices table has soft-deleted rows; filter
  `deleted_at is null`"). Knowledge the code does not show is the most valuable line in the brief.
- **State the dependency rule.** Default: no new dependency without asking.

## Spec, plan, then small verified steps

1. **Explore.** The agent reads the named files and reports what it found, editing nothing.
   In Claude Code use plan mode (Shift+Tab cycles modes) or say "do not edit files yet".
2. **Plan.** Numbered steps, each with the files it touches and the check that proves it.
   Review the plan: it is the cheapest point to catch a wrong direction. Fix the plan, not code.
3. **Persist the plan** in the brief file or the issue, so a fresh session can pick it up.
4. **Implement one step at a time.** The agent runs that step's check and commits on green.
5. **Checkpoint** at the boundaries set in the plan (after the data layer, after the API,
   before the UI): review and, where possible, merge before the next layer builds on it.
6. **Finish** with the full check suite, the summary and a pull request.

Commit per green step because git is the reliable undo. Claude Code's checkpoints (Esc twice,
or `/rewind`) restore conversation and file edits made through its edit tools, but not effects
of shell commands: a migration that ran, files deleted by `rm`, packages installed.

Skip the written plan for changes of a few lines where the brief already is the plan. Keep it
for anything spanning more than one module, because a plan reviewed in one minute replaces a
diff reviewed in thirty.

## Breaking a large feature into tasks with checkpoints

Start with a **contract task**: types, schema, interfaces and stubbed routes, reviewed deeply.
Later tasks implement against it, so mistakes in it multiply. Then cut vertical slices that
each end in a working, mergeable state, behind a feature flag if users must not see it yet.

Example: team invitations.

| # | Task | Done check | Checkpoint |
|---|---|---|---|
| 1 | Schema, migration, types for invitations | Migration up and down on a local copy; types compile | Human deep review, merge |
| 2 | Create, accept, revoke on the server, with authorization | Tests incl. cross-workspace and expired-token cases | Review, merge |
| 3 | Invitation email through the existing email wrapper | Unit test on the rendered template; one test send in the provider's sandbox | |
| 4 | UI: invite form and pending list from existing components | Screenshots: empty, filled, error, narrow width | Review screenshots |
| 5 | End-to-end test of invite and accept | Playwright test green twice in a row | |
| 6 | Flag removal, docs, cleanup | Full suite | Merge |

Rules for the split:

- Dependencies first; nothing builds on an unmerged task unless stacking is intended.
- Each shared file (schema, route registry, navigation, translation catalogs, lockfile) is
  touched by one task only. This also makes tasks 3 and 4 safe to run in parallel
  (see `parallel-automation.md`).
- A checkpoint is where a human reviews and merges before continuing. Place one after every
  task that later tasks depend on; skip it for leaf tasks.

## Options and trade-offs before code

Ask for options first when the choice is hard to reverse: a new library, a data model, sync or
async processing, where state lives, a new service, a caching layer.

```text
Do not write code. Give two or three options for <decision> in this codebase.
For each: how it works here (files touched), what it makes easy and hard later,
failure modes, operational cost, effort. Include the simplest option that could work
and an option with no new dependency. Recommend one and say what would change your mind.
```

Traps: agents favor the option they have already started on, and the most elaborate design
reads as the most competent. Asking for the simplest option and for what would change the
recommendation counters both. Record the decision where structural choices are kept
(`0x:engineering-leadership`, decision records), then delegate the implementation.

## Interrupt, redirect or restart

Watch the first minutes of a run closely; most bad runs announce themselves early.

| Signal | Action |
|---|---|
| Reading many unrelated files, wandering | Interrupt (Esc), point it at the right file |
| Editing files outside the brief | Interrupt, revert those files, restate the constraint |
| Changing a test, an expected value or a lint rule to get green | Stop. Revert the test. "Tests are the spec; fix the code or explain why the test is wrong" |
| Same fix attempted a second and third time | Stop asking for fixes; ask for a diagnosis: what the error says, the hypothesis, how to confirm it |
| Adding a dependency, abstraction or config nobody asked for | Interrupt and restate scope |
| "Done" without command output | Ask for the commands run and their output |
| Forgetting earlier constraints, quality dropping, context nearly full | Write a handoff note, start a fresh session (`context-setup.md`) |
| Implementation diverging from the approved plan | Stop; either amend the plan explicitly or revert to the last checkpoint |

**Redirect or restart.** Correct once or twice in the same session. If the same problem comes
back after two corrections, the context is carrying the wrong approach and more argument
reinforces it. Revert to the last good commit, add what was learned to the brief (that lesson
is the real output of the failed run), and start a fresh session with `/clear` or a new one.
Restarting costs minutes; a polluted session keeps costing.

```bash
git status && git diff --stat            # what the run actually changed
git restore --source=HEAD -- src/other/  # drop edits outside scope, keep the rest
git reset --hard <last-green-sha>        # on the agent's own branch only: discard the run
```

## Ask the user

- **Which parts of the code do you want to keep writing or reading line by line yourself?**
  It sets the boundary of delegation. Default: authorization, billing, data model, destructive
  migrations and public contracts.
- **How much review time can you give per day?** Review capacity, not agent speed, limits
  throughput. Default: one agent at a time, tasks reviewable in 30 minutes.
- **May the agent add dependencies?** Each one is maintenance and supply-chain risk. Default:
  only after asking, with the reason and the alternatives considered.
- **What is explicitly out of scope for this feature?** Unstated scope gets filled in by the
  agent. Default: nothing beyond the acceptance criteria.
- **Who makes design decisions?** Default: the agent proposes options, the user decides, the
  decision is recorded before implementation starts.
