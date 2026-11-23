---
name: ai-coding-agents
description: "Gets reliable work out of coding agents such as Claude Code, Codex or Cursor: scoping and briefs, CLAUDE.md and AGENTS.md, hooks, skills and MCP servers, verification and review depth for AI-written code, parallel worktrees, headless CI and scheduled runs, permissions, secrets and team AI policy. Use when delegating a feature, when an agent goes off track, or when setting up agents for a repository."
---

# Building with AI coding agents

## Stance

A coding agent is a fast, tireless junior with no memory of the project and a strong urge to
finish. Its output is set less by the wording of the prompt than by the system around it: how
the task is scoped, how fast and honest the feedback loop is, how the result is reviewed, and
what the environment physically allows. An experienced practitioner tunes that system (briefs,
checks, controls, review capacity) and treats prompt phrasing as the last lever, not the first.

- **Delegate outcomes with a machine-checkable done.** Acceptance criteria as commands,
  negative cases spelled out, one exemplar file to copy, an out-of-scope list. Without a done
  check, the agent decides when it is done.
- **Plan before code, small verified steps after.** A plan reviews in a minute; a wrong diff
  costs an hour. Commit at every green step, because git is the undo and the tool's own
  checkpoints do not reverse shell side effects.
- **The feedback loop is the quality lever.** Typecheck, lint and targeted tests in seconds, a
  runnable app and a browser for UI. An agent fixes what its checks reveal and little else.
- **Proof, not claims.** Command output with test counts, failing-then-passing runs,
  screenshots. A summary saying "verified" is a claim; CI on a clean checkout is evidence.
- **Review by blast radius, not diff size.** Auth, money, migrations, permissions, CI and agent
  configuration are read line by line; the code the founder must debug at 3 a.m. stays in the
  founder's head.
- **Two corrections, then restart.** A context carrying a wrong approach keeps reproducing it.
  Revert, put the lesson into the brief, start a fresh session.
- **Constraints beat instructions.** Hooks, permission rules, sandboxes, branch rulesets and the
  absence of production credentials hold every time; a line in CLAUDE.md holds most of the
  time. Anything that must never happen gets a structural control.
- **Review capacity is the bottleneck.** Parallel and scheduled agents pay only when their
  output is reviewed; unreviewed agent pull requests are cost and attack surface.
- **Measure outcomes, not impressions.** Cycle time, rework and defects by task type; perceived
  speed-ups have been shown to be unreliable.

Follow the project first: if it already has an instruction file, settings, hooks or CI agents,
extend them rather than replacing them. The defaults below are for new decisions.

## Route

| If the task is … | Read |
|---|---|
| "How do I break this down for the agent", writing a brief or acceptance criteria, what to delegate and what to keep, asking for options before code, an agent going off track, editing files it was not asked to, looping on the same fix | `references/delegation-specs.md` |
| Writing or pruning CLAUDE.md or AGENTS.md, the agent repeating a mistake, setup and test commands for agents, what context to give, long sessions degrading, compacting and handoff notes, which hooks, skills, commands or MCP servers to add | `references/context-setup.md` |
| Checking agent output before merge, reviewing AI-written code without reading every line, agents weakening tests or inventing APIs, extra care for auth, payments and migrations, test-first with agents, an AI review bot in CI, losing track of the architecture | `references/verification-review.md` |
| Several agents at once, git worktrees, cloud sandboxes, splitting work so agents do not collide, agents in CI or GitHub Actions, scheduled dependency, flaky-test or doc tasks, writer and reviewer agents, whether agents actually speed delivery | `references/parallel-automation.md` |
| What an agent may run, read or reach, approval for pushes and deploys, secrets and network, what code or customer data may go to AI tools, a team AI policy, prompt injection, agent spend and budgets | `references/permissions-governance.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Task size | Diff reviewable in about 30 minutes, with a runnable done check | A known one-line fix: do it by hand |
| Workflow | Explore, reviewed plan, one commit per green step, pull request | A few-line change: the brief is the plan |
| Instruction file | `AGENTS.md` as source of truth, `CLAUDE.md` importing it, under about 150 lines | Only Claude Code is used: `CLAUDE.md` alone |
| Guards | Format hook after edits, protected-files hook, typecheck on Stop | |
| Extensions | CLIs before MCP servers; a command after the third repetition | |
| Review depth | Risk tiers 0, 1, 2; tier 2 line by line | |
| Tests | Failing tests first for behavior changes, frozen during implementation | Throwaway prototype code |
| Parallelism | One implementation agent at Prototype; two or three in worktrees at Launch | Read-only helpers at any stage |
| Permission mode | Prompts or classifier-approved auto mode, plus deny rules for secrets and destructive commands, OS sandbox on; accept edits on an agent branch | Skipping all checks only in a container or VM with an egress allowlist and no credentials |
| Credentials | Development database and test-mode keys only | Never: no production credentials where agents run |
| Merging | A human merges; agents push branches | Never |
| CI agents | Triggered by mention or maintainer label; capped turns, timeout, minimal token | |
| Data to AI tools | Own code under business terms; no secrets, no production customer data | A contract or regulation restricts code as well |
| Spend | Separate keys per use, provider spend limits, monthly review | |

By stage:

- **Prototype**: one agent, a lean instruction file, one-command setup, plan mode for anything
  multi-file, commit per green step. Skip scheduled agents, AI review bots and measurement.
- **Launch**: protected-files and typecheck hooks, risk tiers with code owners on auth, billing
  and migrations, rulesets on `main`, no production credentials on the dev machine, two or
  three agents in worktrees, first scheduled task, spend limits.
- **Scale**: written AI policy, managed settings, CI agents for triage and maintenance, AI
  review on ready pull requests, labeled agent work with cycle-time, rework and defect tracking.

## Before you call it done

1. The brief has acceptance criteria with runnable checks, negative cases and an out-of-scope list.
2. The diff touches only files named in the brief or plan; every other file has a stated reason.
3. Typecheck, lint and tests pass in CI on a clean checkout, and the test count shows the new
   tests ran.
4. Test files, test and lint config, `tsconfig`, CI workflows and agent config are unchanged,
   or each change is explained and accepted.
5. New tests fail when the implementation is broken on purpose; none assert nothing.
6. Every new dependency exists, is the intended package and was approved.
7. UI changes come with screenshots of the empty, error and narrow-width states.
8. Tier 2 paths were reviewed line by line, with a cross-tenant test for any new data access.
9. The person merging can explain the change in two sentences: what changed and why it is safe.
10. Any mistake the agent made twice produced a line in the instruction file, or a hook.
11. No production credential, live key or customer data was reachable from the agent's
    environment.
12. Destructive commands, pushes to protected branches and deploys need human approval or are
    impossible with the agent's token.
13. Unattended runs set the permission mode and tool allowlist explicitly, have a turn cap, a
    timeout, a concurrency limit and a spend cap, and their output is a pull request or an issue.
14. Agent-authored pull requests are labeled so merge rate, rework and defects can be measured.

## Not this skill

- LLM features inside the product itself → `0x:ai-features`
- Claude API usage, model IDs and SDK details → `claude-api`
- Reviewing a specific diff for bugs → `code-review`
- Writing the tests and lint setup agents rely on → `0x:code-quality`
- License and IP status of AI-generated code → `0x:privacy-compliance`
- Product specs and acceptance criteria as product decisions → `0x:product-discovery`
- Branching, pull request practice and git recovery → `0x:git-collaboration`
- CI pipeline mechanics and pipeline secrets → `0x:ci-cd-release`
