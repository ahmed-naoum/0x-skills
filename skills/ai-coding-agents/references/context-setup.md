# Context and project setup

Read this when: preparing a repository so agents work well in it, writing or pruning CLAUDE.md
or AGENTS.md, adding setup and test commands, deciding which hooks, skills, commands or MCP
servers to add, or a long session is getting worse.

## What pays off, in order

1. **A way to run everything**: setup, dev server, tests, typecheck, lint, all non-interactive.
   Without this, nothing else matters; the agent cannot check its own work.
2. **The project instruction file**: what the agent cannot infer from the code.
3. **Exemplar code**: one clearly canonical example of each pattern.
4. **Deterministic guards**: hooks and CI for what must happen every time.
5. **Extensions**: commands, skills, subagents and MCP servers for recurring work.

At Prototype, items 1 and 2 are enough. Add hooks at Launch, when a repeated mistake has cost
something. Extensions grow from real repetition, not from a catalog.

## The instruction file: CLAUDE.md and AGENTS.md

Claude Code reads `CLAUDE.md` at the project root, a user-level `~/.claude/CLAUDE.md` for
personal preferences, and `CLAUDE.md` files in subdirectories when it works in that part of the
tree. Claude Code reads `CLAUDE.md`, not `AGENTS.md`; many other agents (Codex, Cursor and
others) read `AGENTS.md`. When more than one tool is used on the repository, keep one source of
truth: put the shared content in `AGENTS.md` and make `CLAUDE.md` a thin file whose first line
is `@AGENTS.md` (an import, expanded at session start), followed by anything Claude-specific.
Prefer the import to a symlink, which needs extra privileges on Windows. If a later Claude Code
version reads `AGENTS.md` natively, drop the import so the content is not loaded twice.

| Put in | Example |
|---|---|
| Exact commands | `pnpm vitest run path/to/file.test.ts` for one file; `pnpm check` before committing |
| A short map | "API routes in `src/app/api`, data access only through `src/db/queries`" |
| Conventions that differ from what a model would assume | "Money is integer minor units; never floats" |
| Traps the code does not reveal | "`src/db/schema.gen.ts` is generated: run `pnpm db:generate`, never edit" |
| Canonical examples | "New feature modules copy `src/features/reports`" |
| Definition of done | "typecheck, lint and affected tests pass; screenshots for UI changes" |
| Paths not to touch | "`legacy/` is frozen; migrations already merged are never edited" |

| Keep out | Why |
|---|---|
| Rules the formatter or linter enforces | A hook enforces them for free; prose wastes context every turn |
| General programming advice | The model knows it; it dilutes the project-specific lines |
| Long architecture prose | Link it as a file to read when relevant, or import only what is always needed |
| Secrets, URLs with tokens, customer names | The file is sent to the model and committed |
| Personal preferences | They belong in the user-level file, not the shared one |
| Task notes and plans | They go stale; keep them in the issue or a plan file |

Numbers and maintenance:

- **Size.** Rule of thumb: keep the root file under about 150 lines. Every line is read on
  every turn and competes with the rest for attention. In a monorepo, put package-specific
  notes in that package's own file.
- **Grow it from mistakes.** Each time the agent repeats a mistake, add one line. If the
  mistake must never happen (editing `.env`, touching applied migrations), use a hook or a
  permission rule instead: instructions are followed most of the time, hooks every time.
- **Prune monthly.** Delete lines about problems that no longer occur.
- **Prevent drift.** Commands named in the file are `package.json` scripts, so renaming one
  breaks visibly. Review changes to these files like code; they steer every run.
- `/init` in Claude Code drafts a first version. Cut it hard: it describes what the code shows
  and misses the traps, which are the point.

```markdown
# Acme app

## Commands
- Setup from a fresh clone: `pnpm install && pnpm setup`
- Dev server: `pnpm dev` (port from PORT, default 3000)
- All checks: `pnpm check` (typecheck, lint, unit tests). Run before every commit.
- One test file: `pnpm vitest run <path>`; e2e: `pnpm test:e2e`

## Map
- `src/app` routes and pages; `src/features/<name>` feature modules
- `src/db/queries` is the only place that talks to the database

## Rules
- Validate every request body and webhook payload with Zod at the route.
- Every query on tenant data filters by `workspaceId`. Copy `src/features/reports`.
- Never edit an applied migration; generate a new one with `pnpm db:generate`.
- No new dependencies without asking.

## Done means
`pnpm check` passes, new behavior has tests, UI changes come with screenshots.
```

## One-command setup

From a fresh clone, one command reaches a running app and green tests with no prompts. The
same command serves new humans, local agents and cloud agent environments (as their setup
script), so it gets exercised constantly and stays working.

```json
{
  "scripts": {
    "setup": "docker compose up -d --wait && pnpm db:migrate && pnpm db:seed",
    "dev": "next dev",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "check": "pnpm typecheck && pnpm lint && pnpm test"
  }
}
```

Requirements: idempotent (running it twice is harmless), local services in Docker Compose, a
committed `.env.example` whose values work locally (test-mode keys only, never live ones), a
seed script that creates a usable account, and test commands that accept a path.

| Symptom | Cause | Fix |
|---|---|---|
| Agent hangs on a command | Interactive prompt or watch mode (`vitest` without `run`) | Non-interactive flags; scripts that exit |
| Agent hangs after starting the app | Dev server blocks the shell | Document how to run it in the background, or start it yourself |
| Tests pass locally, fail for the agent | Tests need network, a real third-party API, or local state | Mocks or provider sandboxes; seed per test run |
| Agent runs the full suite after every edit | No documented way to run a subset | Document path-scoped and related-test commands |
| Agent ignores red tests | Flaky tests taught it red is noise | Fix or quarantine flakes (`0x:code-quality`) |
| Setup works only on one laptop | Steps live in someone's memory | Put every step in the script; run it in CI |

## Give the agent what it needs, not everything

Context is a budget: irrelevant files lower accuracy and raise the cost of every turn.

- Name one to three exemplar files to copy, and the files that constrain the change (schema,
  types, the guard to reuse).
- Paste real error output and stack traces verbatim; a paraphrase drops the line that matters.
- State library versions when they matter ("Next.js App Router, not pages; Zod 4 API"). Agents
  write APIs from older versions they saw more of. For fast-moving libraries, give the doc page
  or a docs tool rather than trusting memory.
- Do not paste whole directories or dump the repository. Point at paths and let the agent read.
- Send exploration to a subagent or a separate session, so search results do not fill the
  context the implementation needs.

## An agent-legible codebase

What makes a codebase easy for a new hire on day one makes it easy for an agent on every run.

| Property | Why it matters for agents | Cheap move |
|---|---|---|
| Strict types end to end | Type errors are the fastest correct feedback | `strict: true`; no `any` in new code; typed data layer |
| Small modules with one job | The relevant code fits in context; edits stay local | Split files past a few hundred lines when touching them |
| One way to do each thing | Agents copy whatever they find; two patterns means a coin flip | Mark the canonical module; label legacy "do not copy" or delete it |
| Explicit names, little metaprogramming | Search finds the code; behavior is visible | Avoid magic registration and string-built identifiers |
| Tests next to code | The agent finds and runs the right tests | `foo.ts` beside `foo.test.ts` |
| Validation at boundaries | Bad input fails loudly where it enters | Schemas on routes, webhooks, env |
| Errors that say what to do | The agent reads error text and acts on it | "Run pnpm db:generate" beats "schema mismatch" |
| Deterministic tests | Red means something | Fixed clocks, seeded data, no shared state |

## Long sessions

Quality degrades as context fills: early instructions lose weight, failed attempts stay in
view and get repeated, and each turn costs more. Treat a session as one task.

- `/clear` between unrelated tasks. A fresh session with a good brief beats a long one.
- `/compact` at task boundaries, not in the middle of debugging, and say what to keep:
  `/compact keep the failing test names, the root-cause hypothesis and the remaining plan steps`.
- `/context` shows what fills the window; large file reads and MCP tool definitions are the
  usual culprits.
- `claude --continue` resumes the last session and `claude --resume` picks one; resuming a
  very long session brings its clutter back.

Before ending a session, or when quality drops, have the agent write a handoff note, commit it
on the branch (or put it in the issue), then start fresh with "read HANDOFF.md and continue".

```markdown
# Handoff: invoice export
Branch agent/invoice-export, last green commit 3f2c1a9
Done: query + route + tests for steps 1-3 of plans/invoice-export.md
Next: step 4 (button on billing page), then e2e
Tried and failed: streaming the CSV with Response streams; the test runner cannot read it.
  Switched to building the string; fine below 10k rows.
Open: should soft-deleted invoices appear? Asked the user.
Verify: pnpm vitest run src/features/billing
```

"Tried and failed, and why" is the most valuable section: without it the next session repeats
the dead end.

## Hooks, skills, commands, subagents, MCP: which for what

| Need | Mechanism |
|---|---|
| Must happen every time (format after edit, block edits to `.env`, typecheck before finishing) | Hook |
| Recurring procedure with knowledge, loaded when the task matches | Skill |
| A prompt typed repeatedly, invoked by name | Custom slash command |
| Investigation or review in its own context with restricted tools | Subagent |
| Live access to a system with no usable CLI | MCP server |
| A system with a good CLI (`gh`, `psql`, provider CLIs in test mode) | The CLI plus permission rules; no MCP |

Hooks live in `.claude/settings.json`. A hook command receives the event as JSON on stdin.
Exit code 2 is the blocking code, and stderr goes to the agent: on PreToolUse it cancels the
tool call; on PostToolUse the tool has already run, so it only reports the problem; on Stop it
refuses to let the agent finish. Exit 1 and other non-zero codes are shown as errors but block
nothing, so a protection hook that exits 1 protects nothing.

```json
{
  "hooks": {
    "PreToolUse": [{ "matcher": "Edit|MultiEdit|Write", "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect.sh" }] }],
    "PostToolUse": [{ "matcher": "Edit|MultiEdit|Write", "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format.sh" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typecheck.sh" }] }]
  }
}
```

```bash
#!/usr/bin/env bash
# .claude/hooks/protect.sh: refuse hand edits to secrets, lockfile and migration files
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  *.env|*.env.*|*pnpm-lock.yaml|*/drizzle/*.sql) echo "Protected file: $f. Ask the user." >&2; exit 2 ;;
esac
exit 0
```

```bash
#!/usr/bin/env bash
# .claude/hooks/format.sh: format the edited file, never block
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in *.ts|*.tsx|*.js|*.json|*.css|*.md) pnpm exec prettier --write "$f" >/dev/null 2>&1 ;; esac
exit 0
```

```bash
#!/usr/bin/env bash
# .claude/hooks/typecheck.sh: do not let the agent stop with type errors
input=$(cat)
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active')" = "true" ] && exit 0
if ! out=$(pnpm -s typecheck 2>&1); then
  printf 'Typecheck fails; fix before finishing:\n%s\n' "$(printf '%s' "$out" | tail -n 40)" >&2
  exit 2
fi
```

The `stop_hook_active` check stops an endless loop when the agent cannot fix the error. Make
hook scripts executable (`chmod +x`), require `jq` in the setup script, and keep them fast
(seconds); a PostToolUse hook runs after every edit. Test a blocking hook once by asking the
agent to edit `.env` and confirming the refusal appears.

MCP servers worth adding for a typical web product: a browser automation server (Playwright)
so the agent can see the UI it builds; a docs server for fast-moving libraries; read access to
the error tracker; read-only access to a development database. Each server's tool definitions
take context in every session, it runs with whatever credentials it is given, and a
third-party server is a dependency with your tokens: prefer vendor-official ones, pin versions,
and never give one production write access. Share project servers through a committed
`.mcp.json` (`claude mcp add --scope project ...`); keep personal ones in user scope.

## Reusable commands and skills

When the same multi-line instruction is typed a third time, make it a command. When it needs
reference material, or should be picked up automatically when the task matches, make it a
skill. Commit both: they are prompt-shaped code and get reviewed like code.

```markdown
---
description: Fix a GitHub issue end to end
argument-hint: issue number
---
Fix issue #$ARGUMENTS.
1. Run `gh issue view $ARGUMENTS`; restate the problem and the acceptance criteria.
2. Write a failing test that reproduces it and show the failure output.
3. Make the smallest fix; run `pnpm check`.
4. Commit as "fix: <summary> (#$ARGUMENTS)" and list each changed file with the reason.
```

Saved as `.claude/commands/fix-issue.md`, this runs as `/fix-issue 123`. Recent Claude Code
versions have merged commands into skills: existing `.claude/commands/` files keep working, and
new ones are better written as `.claude/skills/<name>/SKILL.md`, which also creates `/name`
and can carry supporting files. A skill has `name` and `description` frontmatter; the
description decides when the agent loads it on its own, so write it in the words a task
arrives in. Keep its body to the
procedure and move long reference material into files it points to.

Good candidates in a web product: add a migration, add an endpoint with authorization and
tests, triage an error-tracker issue, upgrade a dependency, write an end-to-end test, cut a
release.

## Ask the user

- **Which agent tools does the team use?** It decides whether `AGENTS.md` is the source of
  truth. Default: `AGENTS.md` plus a `CLAUDE.md` that imports it once more than one tool is used.
- **Can the app and its services run locally in Docker?** One-command setup depends on it.
  Default: yes, with Compose for Postgres and other services.
- **Which external systems should agents read?** Each connection is context cost and risk.
  Default: none at first; CLIs before MCP servers; read-only when added.
- **Which module is the canonical example of each pattern?** Agents copy what they see.
  Default: ask the user to name one per pattern and label the rest legacy.
