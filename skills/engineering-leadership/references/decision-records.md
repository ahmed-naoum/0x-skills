# Decision records and design docs

Read this when: a technical decision should be written down, reviewed or revisited; before a
large change; when someone asks "why is it built like this?"; or when the facts behind an
earlier choice have changed.

## Three artifacts, sized to the decision

| Artifact | Use for | Length | Location |
|---|---|---|---|
| Decision log line | Any non-obvious choice, two-way doors included | One line | `docs/decisions/log.md` |
| Architecture decision record (ADR) | One-way doors; anything costing more than about a week to reverse; anything someone will ask "why" about in six months | One page at most | `docs/decisions/NNNN-short-title.md` |
| Design doc | Work over about two weeks; changes to the data model, a cross-cutting concern or a security boundary; work someone else will build | Two to six pages | `docs/design/YYYY-MM-short-title.md` |

Keep all three in the repository. They are versioned with the code they explain, reviewed in
pull requests, found by coding agents and by new hires, and they survive a change of wiki tool.
Point to the folder from the project's agent instructions file so agents respect deliberate
choices instead of "fixing" them (`0x:ai-coding-agents` covers that file).

## The decision log, even when solo

A solo founder needs it most: the reason behind a choice is forgotten within months, every
coding-agent session starts without memory, due diligence asks for it, and the first hire reads
it in their first week.

```markdown
# Decision log

| Date | Decision | Because | Revisit when |
|---|---|---|---|
| 2026-02-10 | Jobs on a Postgres-backed queue | One fewer system to run; low job volume | Sustained backlog, or per-tenant rate limits needed |
| 2026-03-04 | No staging; preview deploy per pull request | Solo, previews cover review | Second engineer or first enterprise customer |
| 2026-03-18 | Store money as integer minor units | Rounding errors in invoices | Never |
```

Rules:

- Write the line in the same pull request as the change, not later.
- "Because" names the constraint or fact, not a virtue: "low job volume", not "simplicity".
- "Revisit when" is an observable condition (a number, an event, a team size), never "later".
- When an agent session makes a non-obvious choice (a library picked, a pattern rejected, a
  shortcut taken), the same change appends a line.
- Promote a line to an ADR when it turns out to be a one-way door.

## Architecture decision records

Michael Nygard's format, extended with alternatives and revisit triggers:

```markdown
# 0007. Hosted auth provider, own users table as source of identity

Status: Accepted (2026-04-02)
<!-- Proposed | Accepted | Superseded by 0012 | Deprecated -->
Decider: <name>. Consulted: <names>.

## Context
Facts at the time, with numbers: users, traffic, cost, team size, deadline, constraints.

## Decision
We will ...

## Alternatives considered
- <Option>: why not, in one or two lines. Include "do nothing".

## Consequences
What gets easier, what gets harder, follow-up work, cost. Negatives are required.

## Revisit when
Observable triggers.
```

Rules:

- Number sequentially and never reuse a number; one decision per record.
- The numbers in Context are what make "revisit when" testable later. Without them a future
  reader cannot tell whether the world has changed.
- Consequences must include the downsides. A record with only upsides is advocacy and will not
  be trusted.
- An accepted record is immutable apart from its status line and links. A change of mind is a
  new record.
- Write it before or with the implementing pull request; approving that pull request approves
  the record.

Common mistakes: backfilling records for every past choice (backfill only the five to ten
one-way doors already taken), records for trivial choices (that is a log line), and records
that describe what was built without saying why.

## Design docs before large changes

Write one when the work exceeds about two weeks, changes the data model or a public contract,
crosses a security or tenancy boundary, involves an irreversible migration, or will be built by
someone other than the author. Product requirements (what users need and why) belong in a spec
owned by `0x:product-discovery`; the design doc is how engineering will meet them.

```markdown
# <Title>   Status: Draft | In review | Approved | Done   Author, date

1. Problem and context: evidence (numbers, tickets, incidents), not opinion.
2. Goals and non-goals: non-goals stop scope creep; write at least three.
3. Proposal: data model and migrations first, then APIs and events, then flows and UI.
4. Alternatives: at least two real ones plus "do nothing", each with why not.
5. Risks: failure modes, security, privacy, cost at ten times the load, performance.
6. Rollout and rollback: deploy order, backfills, flags, the irreversible step marked.
7. Verification: tests, and how production will show it works or is broken.
8. Open questions: each with an owner and a date.
9. Effort: a range, and what would change it.
```

Write the data model and the migration plan before any UI: they are the parts that cannot be
undone. A doc longer than about six pages usually describes two projects; split it. When solo,
a one-page version still pays for itself, and it is the best specification to hand a coding
agent (`0x:ai-coding-agents`).

## Design review that surfaces risks early

Review at roughly 60 to 80 percent complete, when the direction is clear and details are still
cheap to change. A finished doc gets rubber-stamped. Take a second, shorter look right before
the irreversible step.

1. The author states the decision needed and marks the one-way parts.
2. Reviewers read and comment in writing first, within one to two days.
3. Meet for 30 to 45 minutes only on unresolved comments, or skip the meeting.
4. Run a pre-mortem: "It is six months later and this failed. Why?" Each reviewer writes
   reasons independently before anyone discusses, so the first speaker does not anchor the rest.
5. Close with an outcome (approved, approved with changes, rework), a risk list with owners, the
   doc updated, and an ADR for each one-way door.

Questions every review asks:

- What happens when each dependency is slow, down or returns nonsense?
- Which step is irreversible, and what is the rollback for every step before it?
- Can migrations run online, how long will the backfill take, and can data be lost?
- Which trust boundaries, authorization checks, secrets or personal data are new?
- How will we know it is broken in production: which alert, dashboard, runbook?
- What does it cost at ten times the load?
- What is the smallest version that tests the riskiest assumption?

Spend review time in proportion to irreversibility. Naming, style and library minutiae belong in
code review; reviewers who drift there should be redirected to the one-way parts.

When solo, run the review in a fresh agent session that did not write the doc, so it has no
authorship bias: ask it for the three most likely ways the design fails in production, the
trigger and cheapest mitigation for each, and a list of irreversible steps. For a true one-way
door with a lot at stake, an hour of a paid experienced advisor is cheap.

## Revisiting and superseding a decision

Revisit when a "revisit when" trigger fires, workarounds pile up around a decision, the same
"why do we do X?" question keeps coming, a fact in the Context section is no longer true (scale,
team, vendor price, regulation), or a new option removes the original constraint. Spend fifteen
minutes each quarter skimming the log and ADRs against their triggers.

To supersede:

1. Write a new ADR with fresh Context that links the old one and states which fact changed.
2. Set the old record's status to "Superseded by NNNN". Change nothing else in it.
3. Plan the migration if code must change (`build-vs-buy.md` for vendors, `0x:code-quality`
   for refactors).
4. Update the agent instructions and docs that cite the old decision.

Traps:

- **Sunk cost.** Months already invested are not a reason to continue; the question is the cost
  from here on of each option.
- **Flip-flopping.** Reversing without a changed fact. Require the new record to name the fact.
- **Silent drift.** The code no longer follows a record and nobody superseded it. Fix the code
  or supersede the record; a decision record that lies is worse than none.

## Who decides

Every decision has exactly one decider. Others are consulted before or informed after.
Consensus is not required: the decider listens, decides by a stated date, records dissent under
Consequences, and the team commits.

| Decision | Decides | Consulted | Informed |
|---|---|---|---|
| Two-way door inside one area (library, internal structure) | Engineer doing the work | Pull-request reviewer | Log line |
| Team convention (lint rules, testing bar, folder layout) | Technical lead or founder-CTO | All engineers | All engineers |
| One-way door (data model, tenancy, public API, vendor holding data) | Founder-CTO | Affected engineers, whoever runs security | Whole team, co-founders |
| Spend or contract above the agreed threshold | Founder who owns the budget | Technical lead | Whoever does the books |
| Security exception | Founder-CTO, in writing, with an expiry date | Whoever runs security | Team |
| Proposal from a contractor or agency | Founder for one-way doors; contractor within the agreed module | | |

Rules:

- Write the decision rights into the engineering norms so nobody has to ask.
- Give each decision a date. An undecided question blocks people longer than a wrong decision
  that can be reversed.
- If two owners disagree, timebox the discussion (two working days is a reasonable default),
  then the founder-CTO decides and records why.
- Coding agents and contractors propose one-way doors; a named person decides and records them.
- Frameworks such as RACI or RAPID add roles for larger organizations; below about twenty
  engineers, decider, consulted and informed are enough.

## Ask the user

- **Where should decision records live?** Default: `docs/decisions/` and `docs/design/` in the
  main repository, because agents and new hires find them there.
- **Who has the final say on one-way technical doors?** In a founding team this must be
  explicit to avoid stalemates. Default: the technical founder, after consulting the others.
- **Above what spend or contract length must a decision go to the founders?** Default: any new
  recurring cost above a few hundred dollars a month, or any annual commitment.
- **When solo, is there an advisor for reviewing one-way doors?** Default: use a fresh agent
  session as reviewer and save paid advice for data-model, tenancy and vendor lock-in choices.
