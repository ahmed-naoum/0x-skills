# How to write a 0x skill

You are writing one skill in a set of about thirty that together cover web development from the
machine to the customer. This file is the standard for all of them. Read it fully before writing.

## Who reads what you write

**Claude, mid-task**, working for one person: a solo developer-founder who builds web products
with Claude Code. That person is capable but is not an expert in your area, and they want Claude
to work the way a principal engineer who has also founded companies would.

The reader is a strong model that already knows the textbook. Explaining what DNS is, or what a
unit test is, adds nothing: it will be skimmed and it costs context. **A line earns its place
only if it changes what the reader does.** That means:

- **Defaults**: what to choose when nobody has said, and the condition under which the default flips.
- **Decision rules**: "if X, do Y, because Z". Tables when there are several cases.
- **Sequences**: the order of steps where the order matters and people get it wrong.
- **Numbers**: thresholds, budgets, limits, with units.
- **Failure modes**: symptom → cause → fix. What breaks in production, not in tutorials.
- **Checks**: how to prove the work is right: a command, a test, a thing to look at.
- **What to skip**: what a small team should deliberately not do yet.

If a paragraph could appear unchanged in a beginner tutorial, cut it or replace it with the
decision the tutorial never tells you how to make.

## The user's situation, which shapes every default

- One person or a very small team. Attention is the scarcest resource. Prefer boring,
  well-supported technology and the fewest moving parts; every extra system is something to
  monitor, patch and pay for.
- **Stages.** Advice differs by stage; say which stage it applies to, using exactly these names:
  - **Prototype**: no real users yet. Speed matters, most rigor can wait.
  - **Launch**: real users and first paying customers. Data loss, security and billing errors are now real.
  - **Scale**: meaningful traffic or revenue and a team. Reliability, cost and process start to dominate.
  The most useful sentence in many sections is "skip this until Launch" or "this becomes mandatory at Scale".
- **Follow the project first.** Before applying any default, look at what the project already
  uses (framework, ORM, host, test runner) and stay consistent with it. Defaults are for
  greenfield decisions and for when the user asks what to choose.

## House defaults

Thirty skills written separately must not contradict each other. When you need to name a
default, use these, and present alternatives as alternatives. Do not turn the skill into a
tutorial for these tools: the principles must hold for any stack.

| Area | Default | Notes |
|---|---|---|
| Language | TypeScript, strict mode, end to end | |
| Runtime, packages | Node.js current LTS, pnpm | |
| Web framework | Next.js App Router with React, server components by default | |
| Styling | Tailwind CSS with accessible headless primitives (Radix-style) | |
| Validation | Schema validation at every trust boundary (Zod) | |
| Database | PostgreSQL, managed | The default answer to "which database?" |
| Data access | A typed SQL-first layer (Drizzle); raw SQL where it is clearer | Keep Prisma if the project has it |
| Auth | A maintained library or provider; never hand-rolled crypto or session code | |
| Payments | Stripe; a merchant of record (e.g. Paddle) when the user wants tax handled for them | |
| Background jobs | Postgres-backed queue first; Redis-backed when volume or features demand it | |
| Cache | HTTP and CDN caching first, then Redis | |
| Hosting | A PaaS first; containers on a cloud when the PaaS limits you; Kubernetes only with people to run it | |
| CI/CD | GitHub Actions | |
| Infrastructure as code | Terraform or OpenTofu | |
| Tests | Vitest for unit and integration, Playwright for end-to-end | |
| Errors, telemetry | An error tracker plus OpenTelemetry to a hosted backend; structured JSON logs | |
| Product analytics | PostHog-style: events, funnels, flags, experiments in one tool | |
| Transactional email | A provider with good deliverability (Postmark, Resend, SES) | |
| LLM features | Claude through the Anthropic API | API details belong to the `claude-api` skill |

## Accuracy: the rule that matters most

Claude will follow what you write. **A wrong default in a skill is worse than no skill.**

- State only what you are sure is true and current in 2026.
- For anything that changes (version numbers, prices, quotas, vendor features, browser support,
  legal thresholds and deadlines), either verify it with a web search if you have that tool, or
  write it durably ("check the provider's current limit") instead of inventing a number.
- Commands and code must be correct. If you can run or syntax-check a snippet here, do it. Keep
  snippets short: show the hard part, not the boilerplate.
- Law, tax, accounting and finance: explain the mechanism, the common practice, and where
  jurisdictions differ; say plainly where a qualified professional is needed. Do not present
  jurisdiction-specific rules as universal.
- Never invent statistics, benchmarks, quotes or case studies. A rule of thumb is fine if you
  label it as one.
- When you are unsure of something you still think belongs, list it in your final report under
  `doubts` so the fact-checker looks at it first.

## What to produce

Write into the skill's folder (the path is in your task). The plan entry for your skill gives
its name, summary, `useWhen`, `notFor`, and its reference files with the leaves each must cover.
`index.md` in the plan folder lists every sibling skill with its reference files: use it to see
who owns a neighboring topic, and point there in one line instead of covering it again.

```
<skill-name>/
├── SKILL.md
└── references/
    ├── <file>.md        one per reference in the plan, same file names
    └── ...
```

### SKILL.md (at most 160 lines)

Frontmatter with exactly two fields:

```yaml
---
name: <skill-name>
description: <what it does>. Use when <concrete triggers>.
---
```

- `description`: 250–420 characters, one paragraph, no line breaks, third person. First what the
  skill lets Claude do, then when to use it, using the words a user would actually type. It is
  the only thing Claude sees when deciding whether to load the skill, so it must be specific
  enough to win the right requests and not steal the wrong ones. Do not use angle brackets.
  Keep it on one line; if it contains a colon followed by a space, wrap the whole value in
  double quotes so it stays valid YAML.

Body, in this order:

1. **Stance** (a short paragraph, then 5–9 principles): how an expert thinks in this area. The
   principles that settle most decisions before any detail is needed. Each with its reason.
2. **Route** (a table): "If the task is … read `references/<file>.md`". Every reference file
   appears; the wording is the task as it arrives, not the file's title.
3. **Defaults at a glance**: the choices to make unless told otherwise, by stage where it differs.
4. **Before you call it done**: the 8–15 checks for work in this area. Concrete and verifiable.
5. **Not this skill**: each `notFor` entry from the plan as one line: topic → which skill.
   Write sibling skills as `0x:<name>`; installed ones by the name given in the plan.

### Reference files (aim for 140–260 lines each)

Start with:

```markdown
# <Title>

Read this when: <one or two lines, the situations>.
```

Then the content, organized however serves the topic. Most files want some of: a decision table,
the procedure with its commands, the numbers, failure modes, checks. Finish with:

```markdown
## Ask the user
```

The decisions Claude cannot make from the code because they are business, money, risk or legal
choices. Each: the question in plain words, why it matters, and the default to assume if they
do not know. Three to six entries; skip the section only if there truly are none.

**Every leaf listed for the file in the plan must be covered**: after reading the file, Claude
must be able to do that thing well. Not one heading per leaf, but none may be skipped or reduced
to a mention. Leaves marked `core` get the most room; `expert` leaves can be tighter but must
still give the decision rule and the main trap.

If a file passes 300 lines, add a short table of contents at the top.

### Scripts (optional, rare)

Add `scripts/<name>` only when it replaces a multi-step check Claude would otherwise re-derive
every time, it needs no dependencies beyond bash, Python's standard library or Node's, and
**you ran it here and it works**. This machine has no outbound network except package
registries, so do not write a script you cannot test without the network. At most two per skill.

## Style

- Plain, direct prose. Imperative for instructions. Give the reason with the rule: a reader who
  understands why can handle the case you did not foresee.
- US spelling. No emojis. No hype, no "best practices" without saying what and why.
- Reserve absolute words (never, always) for real invariants such as security rules, and then
  say what breaks.
- Tables for decisions and comparisons; fenced code blocks with a language tag for commands and
  code; short paragraphs otherwise. Do not bullet-point continuous reasoning.
- Name real tools as defaults, but make the principle survive without the tool.
- Do not write an introduction about why the topic matters, and do not write a summary.
- Do not mention this standard, the plan, "leaves", or the writing process in the skill itself.

## Before you report

Run the checker and fix everything it prints, errors and warnings both. The exact command,
with the folders for this build, is in your task:

```bash
python3 <plan folder>/check_skill.py <skill-name> <build folder>
```

## Your final report

Return, as your final message, a short plain list:

- `files`: each file written, with its line count.
- `leaves`: confirm every leaf of every reference is covered, or name any you could not cover and why.
- `doubts`: specific claims you are least sure of (file and the claim).
- `pointers`: places where you referred the reader to another skill.
