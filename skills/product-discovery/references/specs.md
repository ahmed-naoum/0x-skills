# Specs and requirements

Read this when: writing down what a feature or product must do before it is designed or built: a
one-page spec or PRD, user stories with acceptance criteria, edge cases and error behavior, how
success will be measured, a spec review, or a press release and FAQ for a larger bet.

## Size the document to the work

| Work | Document | Length |
|---|---|---|
| Under a day, behavior obvious | Issue with acceptance criteria | A few lines |
| Days to about two weeks | One-page spec | One page |
| Several weeks, a new segment, or a change customers will feel (pricing, data model, removal) | Press release and FAQ first, then a one-page spec per slice | Two pages plus one |
| How it will be built: architecture, data model, migration | Technical design doc → `0x:engineering-leadership` | Separate |

A spec says what and why; a design doc says how. Mixed, the document is too technical for
customers to review and too vague to build from.

## The one-page spec

```markdown
# <Feature name>   (status: draft | reviewed | building | shipped, updated <date>)

## Problem
Who has it, how often, what it costs them. Evidence: links to interview cards, tickets and
requests, with counts, segments and revenue at stake.

## Goal and success metric
Primary: <metric>, baseline <value, measured on date>, target <value> by <date>.
Guardrail: <metric that must not get worse>.

## Non-goals
- Not doing <X> in this version, because <reason>.

## User and job
When <situation>, <user> wants to <job> so they can <outcome>.

## Solution outline
The flow as numbered steps, with links to sketches. No pixel-level design.

## Requirements
User stories with acceptance criteria.

## States and edge cases
Table: case -> expected behavior.

## Measurement
Events and properties to add; where and when the metric will be read.

## Rollout
Flag, beta group, data migration, announcement, who to tell.

## Open questions
Question, owner, decide-by date.
```

- Non-goals are the most valuable section. They stop scope creep from teammates, customers and
  coding agents, and record what was consciously deferred.
- The problem section carries linked evidence. A problem that reads "users want X" means
  discovery was skipped.
- Keep it to one page. When it grows, split it into two features or move the how into a design
  doc.
- Update it when decisions change during the build, with a dated change note. A stale spec is
  worse than none, because people and agents follow it.

## Write user stories with testable acceptance criteria

Story form: "As a <role>, I want <capability>, so that <outcome>." The "so that" names a real
outcome from the job; if it restates the capability, the story has no reason to exist.

Acceptance criteria in Given/When/Then, one observable behavior per line:

```gherkin
Scenario: Invite a teammate who already has an account
  Given I am an owner of workspace "Acme"
  And "sam@example.com" has an account but is not a member of "Acme"
  When I invite "sam@example.com" as a member
  Then Sam sees "Acme" in the workspace switcher after the next page load
  And Sam receives exactly one email with a link that opens "Acme"
  And no second account is created for "sam@example.com"
```

- Someone who has not spoken to the founder (a teammate, a coding agent, an end-to-end test) can
  decide pass or fail without asking a question.
- Replace adjectives with numbers or examples. "Fast" becomes "results appear within 1 second for
  10,000 rows"; "easy" becomes "three steps from the dashboard".
- Include negative criteria, the things that must not happen: no duplicate email, no access for
  removed members, no second charge on retry.
- Name exact values, roles and messages where they matter, and point to the copy source rather
  than paraphrasing it.
- One criterion, one test. A criterion that cannot be automated is either vague or needs a
  written manual check.
- Keep each story shippable in a day or two. A two-week story hides several undecided decisions.

## Specify states, edge cases and error behavior before building

Decide behavior up front; otherwise the implementation decides by accident, differently in each
place. Visual treatment of states belongs to `0x:ui-ux-design`; the spec decides what happens.

Walk this list for every feature and write a row for each case that applies:

| Dimension | Cases |
|---|---|
| Volume | None (empty state), one, many, at the plan limit, over the limit |
| Input | Maximum length, unicode and emoji, surrounding spaces, duplicates, pasted formatting |
| Time | Time zones, daylight-saving shifts, dates far in the past or future, a deadline passing mid-flow |
| Concurrency | Two users editing the same thing, double submit, two tabs, retry after timeout |
| References | The linked object was deleted, archived or moved; access lost mid-flow |
| Permissions | Per role: can see, can edit, cannot see; what a removed member sees |
| Plan and billing | Free versus paid, trial expiring mid-flow, downgrade with data over the new limit |
| Failure | Third party down or slow, partial failure in a multi-step action, network loss |
| Lifecycle | Data created before the feature existed, undo and reversibility, account deletion |
| Abuse | Spam, enumeration, oversized uploads, scripted use of the endpoint |

For each error case, state four things: what the user sees and can do next, whether their input
is preserved, whether the action is safe to retry, and what is logged or alerted.

```text
| Case                                   | Expected behavior                                              |
|----------------------------------------|----------------------------------------------------------------|
| Invitee already in the workspace       | Inline "Already a member"; no email sent                       |
| Email provider times out               | Invite saved as pending, retried in background; owner sees "Sending" |
| Owner removes the invite before accept | Link shows "This invitation is no longer valid"                |
| Workspace at its seat limit            | Blocked before sending, with a link to upgrade                 |
```

Most production bugs and support tickets come from the cases decided here. A missing row is a
decision left to whoever writes the code, including a coding agent.

## Define how success will be measured and instrumented

- One primary metric the feature should move, tied to the job, with a baseline measured before
  building. Without the baseline, nobody can tell afterward whether it worked.
- A target and a read date, for example: "Share of new workspaces that invite a teammate in week
  one, from 18% to 30%, read four weeks after full rollout" (illustrative numbers).
- One or two guardrails that must not get worse: support tickets per account, error rate,
  conversion on a neighboring step.
- The events and properties to add, listed in the spec so instrumentation ships with the feature
  rather than after it. Naming and taxonomy follow `0x:product-analytics`.
- The decision for each outcome, written now: target hit → keep and move on; partial → one
  iteration on the cause found in sessions; no movement → remove or rethink
  (`prioritization-roadmaps.md`).
- With few users, numbers are noise; add a qualitative bar such as "five of the next ten new
  accounts complete the flow unassisted in a watched session".
- An A/B test only when traffic supports it. At Prototype and early Launch, before-and-after plus
  watched sessions is the honest method (`0x:product-analytics` for experiment design).

## Review the spec before committing

With customers, two or three from the ICP, ideally those who asked:

- Walk through the flow in plain words or a rough sketch, then ask them to apply it to their last
  real instance of the job: "Last time this came up, how would this have gone?"
- Listen for the step where their real case breaks the flow. Do not ask whether they like it;
  approval is cheap and uninformative.

With a teammate, an engineer, or a model as reviewer:

- Ambiguity pass: every place where two reasonable implementers would build different things.
- Edge-case pass: run the dimension table above.
- Pre-mortem: "Three months after launch this failed. Why?" Each answer becomes a risk to
  mitigate, a non-goal or an open question.
- Cost pass: find the one requirement that doubles the work and decide whether it is worth it
  (`0x:engineering-leadership` for estimates).

Time-box the review to a day or two, resolve or assign every open question, record decisions in
the spec and mark it reviewed. Working alone, the founder gets most of the value by having the
spec critiqued for ambiguity and missing states, and by rereading it the next morning before
building.

## Write a press release and FAQ first for a larger bet

Write the launch announcement before the spec when the bet is multi-week, opens a new segment,
or changes what customers pay for. If the announcement does not excite the target customer, the
feature will not either, and that is cheapest to learn now.

Press release, one page, dated on the intended launch day:

1. A headline naming the customer and the benefit, in their words.
2. One sentence: who it is for and what changes for them.
3. The problem as the customer experiences it.
4. The solution, at the level of what the customer can now do.
5. A founder quote on why it matters.
6. How it works and how to start, in two or three sentences.
7. A plausible customer quote describing the outcome (hypothetical; never published as real).

| External FAQ (customer questions) | Internal FAQ (the hard questions) |
|---|---|
| What does it cost? | What must be true for this to work? |
| What does it not do? | What is the riskiest assumption, and how is it tested first? |
| How do I move my existing data? | What does it cost to build and run, and what does it displace? |
| Where is my data, is it secure? | What result would make us stop? |
| How is it different from <alternative>? | How is success measured, and by when? |

Show the press release to three to five ICP customers before building. Their questions become the
FAQ, and their indifference is the cheapest kill signal available. Then write the one-page spec
for the first slice. Briefing a coding agent from the finished spec is `0x:ai-coding-agents`.

## Ask the user

- **What result makes this feature a success, and by when?** Default: one primary metric with a
  baseline, read four weeks after full rollout.
- **What is explicitly out of scope?** Default: everything not needed on the main job path,
  listed by name.
- **Who reviews the spec?** Default: two customers who asked for it plus one technical reviewer.
- **Is there a date that matters (a customer commitment, a launch, a contract)?** It decides how
  much scope gets cut. Default: no fixed date; scope fits the appetite.
- **Does it roll out behind a flag or to a beta group first?** Default: yes for anything that
  changes existing users' workflows (`0x:ci-cd-release`).
