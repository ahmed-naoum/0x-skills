# Parallel and automated agents

Read this when: running more than one agent at once, running agents unattended in CI, in cloud
sandboxes or on a schedule, wiring writer and reviewer agents together, or deciding whether
agents actually speed up delivery.

## The limit is review, not compute

Parallel agents multiply output; the capacity to review, integrate and understand it does not
grow with them. Rule of thumb: a solo developer sustains two or three concurrent implementation
agents, rarely four. Past that, pull requests queue, conflicts multiply and review quality drops, which is
where defects slip in. Read-only agents (investigation, research, review) parallelize far more
cheaply because their output is short and nothing merges.

By stage: at Prototype, one implementation agent plus occasional read-only helpers. At Launch,
two or three agents in worktrees and the first scheduled task. At Scale, CI agents for triage
and maintenance, and the measurement below.

## Isolation options

| Option | Isolated | Shared, so watch it | Good for |
|---|---|---|---|
| Git worktrees on one machine | Working directory, branch, index | Repository history, local database, ports, Docker resources, caches | Two to four local agents |
| Separate clones | Everything in the repository | Machine services | Rarely worth it over worktrees |
| Container or devcontainer per agent | Processes, files, network | Host only via mounts | Unattended local runs |
| Vendor cloud sandboxes | A machine per task | Secrets configured in the environment | Fire-and-forget tasks, many at once |
| CI runners | Ephemeral machine per job | Repository secrets and token scope | Triggered and scheduled automation |

For cloud sandboxes, the environment's setup script is the project's one-command setup
(`context-setup.md`); if it does not work unattended, every cloud task starts broken.

## Worktrees without collisions

```bash
git fetch origin
git worktree add -b agent/invoice-export ../app-invoice-export origin/main
cd ../app-invoice-export
cp ../app/.env.local .env.local          # gitignored files are not in the new worktree
pnpm install
createdb app_invoice_export              # own database, then point DATABASE_URL at it
```

Recent agent tools, Claude Code among them, can create a worktree per session themselves;
that covers the checkout only. Each worktree needs its own port (`PORT=3001 pnpm dev`), database or schema, Docker Compose
project name (`docker compose -p invoice-export up -d`, or `COMPOSE_PROJECT_NAME`) and
end-to-end base URL. Two agents migrating one shared local database corrupt each other's runs
in ways that look like code bugs. Put these steps in a `scripts/worktree.sh <name>` so every
worktree is created the same way, and clean up with `git worktree remove ../app-invoice-export`,
`git branch -d agent/invoice-export` and dropping the database. `git worktree list` shows what
is still open.

## Partition by files, not by feature names

Before starting parallel tasks, list the files each will touch. Any overlap means serialize the
tasks or merge them into one.

- **Hot files have one owner per round**: schema and migrations, route registries, navigation
  config, translation catalogs, generated types, shared constants, the lockfile, the changelog.
  Alternatively land a small "contract" change first that adds every shared entry, then fan out.
- **One migration at a time.** Two branches each generating a migration produce ordering or
  journal conflicts in most migration tools, and the merge is easy to get subtly wrong.
- **One agent adds dependencies per round.** On a lockfile conflict, take the version from
  `main`, re-apply the `package.json` change and regenerate with `pnpm install`; never hand-merge
  a lockfile.
- **Merge order:** foundational and smallest first. After each merge, the remaining branches
  rebase onto `main` and rerun their checks; an agent can do the rebase, a human checks the result.

| Splits that work | Splits that collide |
|---|---|
| Independent features in different modules | Frontend and backend of one feature before the API contract exists |
| Tests for different, already-written modules | Two refactors of the same area |
| Implementation in one, docs or migration guide in another | Anything that touches the schema in more than one branch |
| Read-only investigations of separate questions | Parallel work on a codebase with no tests (nothing detects the breakage) |

## Scheduled agent tasks

Good recurring work is narrow, well-checked and boring to do by hand.

| Task | Trigger | What the agent does | Guard |
|---|---|---|---|
| Breaking dependency updates | A bump pull request from Renovate or Dependabot fails CI | Reads the changelog, fixes call sites, explains | Patch and minor only; majors need a human brief |
| Flaky tests | Weekly | Lists tests that failed then passed on retry in CI history, reproduces with repetition (`pnpm playwright test <file> --repeat-each=20`), fixes the root cause | Reject fixes that only add retries, sleeps or longer timeouts |
| Docs and instruction sync | Weekly | Compares merged changes with docs, README and the commands in CLAUDE.md or AGENTS.md | Docs paths only |
| Error triage | Daily | New top errors from the tracker become issues with analysis and a suspected commit | Issues only, no code |
| Lint and dead-code debt | Weekly | One small batch per run | Size cap per pull request |

Every scheduled task follows the same rules:

1. One purpose, with the prompt committed in the repository and reviewed like code.
2. Output is a pull request or an issue. Never a push to `main`, never a deploy.
3. Idempotent: it checks for its own open pull request or issue before opening another.
4. Bounded: maximum turns, job timeout, at most one pull request per run.
5. Labeled (for example `agent:scheduled`) so merge rate can be measured.
6. Failures notify someone; success stays quiet.
7. Kill rule: if few of its pull requests are merged over a month, narrow it or turn it off.
   Unreviewed agent pull requests are noise, cost and attack surface.

Scheduling itself is either a CI cron or the agent vendor's scheduled cloud tasks; choose
whichever already holds the needed secrets with the smallest scope.

## Headless agents in CI

Claude Code runs non-interactively with `-p`. Set the permission mode explicitly rather than
inheriting a default that may change between versions: `dontAsk` refuses every tool call that
no allow rule covers, so the allowlist is the whole permission model of the run.

```bash
claude -p "Read ci-output.txt, find the root cause of the failing test, fix it, run pnpm test. Do not edit test files." \
  --permission-mode dontAsk \
  --allowedTools "Read" "Grep" "Glob" "Edit" "Bash(pnpm test)" "Bash(pnpm test *)" "Bash(pnpm typecheck)" \
  --max-turns 25 \
  --max-budget-usd 5 \
  --output-format json > result.json
```

Current rule syntax puts a space and `*` after the command; older versions and many examples
use a `:*` suffix, which newer versions treat as legacy. Pin the Claude Code version in CI and
check its permissions docs, because a rule that silently fails to match turns into a refusal
(safe) or, with a broader mode, into an unexpected approval. `--max-budget-usd` caps spend
under API billing in print mode; check how it behaves with a subscription login before relying
on it. "Do not edit test files" in the prompt is advice; a PreToolUse hook that refuses edits
to `*.test.*` is the control.

On GitHub, the maintained route is Anthropic's Claude Code action, installed with
`/install-github-app` from Claude Code, which also sets up the GitHub App.

```yaml
name: agent
on:
  issue_comment:
    types: [created]
jobs:
  agent:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    timeout-minutes: 30
    concurrency: agent-${{ github.event.issue.number }}
    permissions:
      contents: write
      pull-requests: write
      issues: write
      id-token: write
    steps:
      - uses: actions/checkout@v6
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          claude_args: "--max-turns 20"
```

`id-token: write` lets the action fetch the GitHub OIDC token it uses to obtain its app
token; drop it only if the action's README says your auth setup does not need it. Check the
README for the current major versions of both actions before copying. For a schedule, use a
separate workflow with `on: schedule` (plus `workflow_dispatch` for manual runs) and pass the
task in the action's `prompt` input; the `if:` on comment text above would skip scheduled runs.

| Trap | Effect | Fix |
|---|---|---|
| Pushes and pull requests made with the default `GITHUB_TOKEN` do not trigger other workflows | Agent pull requests show no CI, and look clean | Use a GitHub App token (the official app does); confirm CI ran before reviewing |
| Anyone can comment on a public repository | Strangers can steer an agent that holds write access and secrets | Keep the action's check that the actor has write access; trigger on a maintainer-applied label for issues |
| `pull_request_target` with the fork's code checked out | Untrusted code runs with repository secrets | Never combine them; run agents on forks with read-only tokens and no secrets |
| Deploy or cloud secrets available in the agent job | One injected instruction away from production | Agent jobs get the model API key and a minimal token only |
| No caps | A loop burns budget for hours | `timeout-minutes`, `--max-turns`, a `concurrency` group |
| Same prompt, different result | Non-determinism read as flakiness | Output is always a pull request for review, never an action |

For triage (read the issue, reproduce, comment with analysis), give the job `contents: read`
and `issues: write` only.

## Multi-agent workflows with independent verification

| Pattern | Shape | Use when |
|---|---|---|
| Writer and independent reviewer | Reviewer gets the brief and the diff in a fresh context, read-only tools, reports findings; the writer fixes | Default for tier 1 and 2 work run unattended |
| Test writer and implementer | One agent writes failing tests from the spec; another implements and may not edit them | Behavior is clear and testable |
| Fan-out research, single integrator | Several read-only subagents answer separate questions; one agent or the human integrates | Understanding a large codebase or comparing options |
| Planner and workers | Planner writes task files with file ownership; workers run in worktrees; merges happen one at a time | A feature already split as in `delegation-specs.md` |
| Best of N | The same well-specified task run two or three times; keep the best | UI and copy, where taste decides; costs N times |

Verification counts only if it is independent of what it verifies:

- It does not trust the producer's report: tests are re-run from a clean checkout, in CI.
- The verifier does not see the producer's reasoning, so it cannot be talked into agreement.
- The verifier cannot edit what it verifies.
- The loop has an objective stop (checks pass and no high-severity findings) and a hard cap,
  for example three rounds, after which a human decides. Writer-reviewer loops without a cap
  oscillate and burn budget.

A Claude Code subagent for review, in `.claude/agents/reviewer.md`:

```markdown
---
name: reviewer
description: Reviews a finished change against its brief. Use after an implementation step completes.
tools: Read, Grep, Glob
---
You review; you never edit. Compare the diff you are given with the brief.
Report only high-confidence problems: correctness, security, missing negative tests,
changes outside scope. For each: file, line, problem, why it matters.
```

Multi-agent runs multiply token use. Use them when the work is genuinely parallel or the
independent check is worth the cost, not as a default.

## Measuring whether agents speed delivery

Perceived speed is unreliable: in METR's 2025 randomized study, experienced open-source
developers took longer on tasks when using AI tools while believing they had been faster.
METR now treats that result as historical for current tools and reports that later effects
are hard to measure; the lasting lesson is the gap between impression and measurement.
Measure outcomes, not impressions.

| Metric | Definition | Watch for |
|---|---|---|
| Cycle time | Pull request opened to merged, median and 75th percentile | Falls while review time rises: the work moved to the reviewer |
| Review time and rounds | Time waiting for review, number of change requests | Grows when agents out-produce review capacity |
| Rework rate | Share of merged pull requests followed within 14 days by a fix or revert touching the same files | The cost of shallow review |
| Change failure rate | Deploys causing a rollback, hotfix or incident | Should not rise as agent share rises |
| Escaped defects | Production bugs per week, tagged by origin | |
| Agent pull request merge rate | Merged over opened, by task type | Low rate means wasted effort or a bad task type |
| Spend per merged pull request | Model spend over merged agent pull requests | Rising with flat output |

```bash
gh pr list --state merged --label agent --limit 200 \
  --json number,createdAt,mergedAt,additions,deletions
```

Method: label agent-authored pull requests (or use a commit trailer), take a baseline of four
to eight weeks, and compare medians within a task type (bug fix, feature, refactor), never raw
totals. Pull request count is not a metric: agents split work into more pieces. Decide what to
delegate more or less of from rework and defects, not volume. Skip formal measurement at
Prototype; start it at Launch once agents write a meaningful share of merged code.

## Ask the user

- **How many agent pull requests can you review per day?** It sets the useful degree of
  parallelism. Default: two concurrent implementation agents.
- **Which recurring chores cost you time today?** Scheduled agents should replace real toil.
  Default: start with failing dependency updates or flaky tests, one task at a time.
- **What monthly spend is acceptable for unattended agents?** Default: a small cap with alerts,
  reviewed after the first month.
- **Is the repository public, or do outsiders open issues and pull requests?** It decides who
  may trigger agents. Default: maintainers only, read-only tokens for anything triggered by
  outside content.
