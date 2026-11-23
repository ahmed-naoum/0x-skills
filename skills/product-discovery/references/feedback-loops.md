# Feedback loops and product-market fit

Read this when: onboarding the first users, adding a feedback widget or micro-survey, turning
support into product input, learning why customers leave or do not buy, running a beta, telling
users a request shipped, or judging whether the product has product-market fit.

## One pipeline for all feedback

Every source flows into one log, deduplicated by underlying problem:

| Source | Captured as |
|---|---|
| Onboarding calls and interviews | Stumble-log entries and observations |
| In-app widget and micro-surveys | Tagged items with account context |
| Support tickets, sales and success calls | Tagged items |
| Cancellations and exit interviews | Churn reasons |
| Win/loss interviews | Objections |
| Beta programs | Tagged items per feature |

Each item links to a problem record holding: the problem in the customer's words, segment, number
of accounts, their revenue, the requesters (needed to close the loop), and links to evidence.
Prioritization reads from these records (`prioritization-roadmaps.md`); the research repository
keeps the evidence (`customer-interviews.md`).

At Prototype a spreadsheet is enough. At Launch, helpdesk tags plus one table of problem records.
A dedicated feedback tool earns its place at Scale, when several people feed the log.

## Onboard the first fifty users by hand

- Send the welcome email from the founder's own address, offering a 30-minute setup call with a
  booking link. Make the call the default path, not an optional extra.
- On the call the user shares the screen and drives. The founder does not take control or explain
  ahead of the user; silence until they are stuck is the method.
- Do the unscalable work: import their data, configure the account, fix small things the same day.
- Log every stumble immediately, in one place:

```text
| Date  | User | Step           | What happened                          | Kind      | Severity | Fix                    |
|-------|------|----------------|----------------------------------------|-----------|----------|------------------------|
| 11-20 | U-14 | Connect source | Could not find the API key in their tool | Confusion | Blocked  | Inline link to its docs |
```

Kinds: confusion, missing capability, bug, and expectation mismatch (they expected the product to
do something else, which is a positioning signal for `0x:growth-marketing`).

- Each week, fix the top stumbles by frequency times severity, then check whether the next users
  still hit them.
- Track time from sign-up to first outcome, and whether it was reached unassisted.
- Move to self-serve when calls stop surfacing new stumbles, usually somewhere around fifty users.
  Then watch session recordings and keep calling a sample. Replay scripts generally need opt-in
  consent in the EU and UK and have drawn wiretap claims in US states that require all-party
  consent: ship them with consent where required, notice everywhere and masked inputs
  (`0x:privacy-compliance`).

Activation measurement is `0x:product-analytics`; structured onboarding programs for larger
accounts are `0x:sales-support`; formal usability testing is `0x:ui-ux-design`.

## Collect in-app feedback at the moment of use

Feedback asked for right after an experience is specific; feedback asked for in a quarterly email
is a mood.

- **A micro-survey after the core action or after a failure**: one question answerable in one tap,
  such as "Did this give you what you needed? Yes / No" or a short ease scale, followed by one
  optional open question on any low answer.
- **A persistent feedback entry point** that attaches context automatically: user and account IDs,
  plan, page or screen, app version, browser, recent errors. Context turns "it's broken" into a
  reproducible report. Mask form inputs in any screenshot or recording.
- **Frequency caps**: at most one prompt per user every few weeks, never mid-task, never in a first
  session before the user has reached the outcome.
- **A personal reply to every written piece of feedback** at Launch. Replies draw out the detail
  that makes it actionable and show that feedback goes somewhere, which increases future feedback.
- Route everything into the same log as support, with the same tags.

Relationship scores such as NPS swing widely at small samples and do not say what to fix. Prefer
task-level questions until there are hundreds of active accounts, then run relationship surveys
at most quarterly.

## Turn support tickets and calls into counted product feedback

Tag every conversation on three axes:

| Axis | Values (keep each list short) |
|---|---|
| Type | Bug, how-to or confusion, feature request, billing, account, data request |
| Area | The product areas, using the roadmap's names |
| Problem | The underlying problem record, not the requested solution |

Connect the helpdesk to account data so account, plan, revenue and segment attach automatically;
fields typed in by hand go stale.

- Weekly: counts by type and area, the top five problems by accounts affected, and the trend
  against last week. Confusion tickets are product or documentation debt and belong in the count,
  not only in the help center.
- Sales, success and onboarding calls get a two-line note with the same tags in the same system.
- Curate the problem list: merge duplicates weekly, prune quarterly. A taxonomy with hundreds of
  tags gets ignored.
- Whoever answers the ticket tags it. Tagging later from memory does not happen.

Support operations themselves (tools, response times, macros) are `0x:sales-support`.

## Run churn-reason surveys and exit interviews

Cancellation flow: one optional, skippable question with fixed options plus free text, with the
cancel action still on screen; never a gate that makes cancelling harder. Many jurisdictions
require online cancellation to be about as easy as signing up and restrict save flows. In the US,
state auto-renewal laws (California's among the strictest) and FTC enforcement under existing law
continue even though the FTC's 2024 click-to-cancel rule was vacated in 2025; Germany requires a
cancellation button for consumer contracts concluded online; the UK has a subscription regime
pending. These rules change often: check the current ones before designing the flow
(`0x:privacy-compliance`; save offers are `0x:sales-support`).

```text
Why are you cancelling?
( ) It's too expensive for the value I get
( ) It's missing something I need: ______
( ) I switched to another product: ______
( ) It was too hard to set up or use
( ) Too many bugs or reliability problems
( ) I don't need it anymore (project ended, business changed)
( ) Temporary; I'll be back
( ) Other: ______
```

Stated reasons are polite simplifications; read them against behavior before acting:

| Churned accounts that… | Usually means | Owner |
|---|---|---|
| Never reached the first outcome | Onboarding or fit problem, whatever reason was ticked | Onboarding, ICP targeting |
| Activated, then usage declined before cancelling | Value faded, or a competitor or workaround won | Core product |
| Chose "too expensive" with low usage | Not enough value, not a price problem | Core product, onboarding |
| Chose "too expensive" with high usage | A real price or packaging issue | `0x:pricing-monetization` |
| Lost access through a failed payment | Involuntary churn, not a product signal | Dunning, `0x:payments-billing` |

Exit interviews: offer a 15-minute call to churned accounts that fit the ICP, with a small thank
you. Ask for the timeline: when they first thought about leaving, what happened then, what they
use now, what would have kept them. Five to ten of these usually explain more than all the
ticked boxes (rule of thumb). Save offers and retention playbooks are `0x:sales-support`; churn-rate analysis is
`0x:product-analytics`.

## Run win/loss interviews and fix the top objection

Interview the decision-maker within a few weeks of the decision, for won and lost deals alike. In
self-serve products the equivalent is trial users who converted and trial users who did not.

Ask what triggered the search, which alternatives they considered, how they evaluated, what almost
stopped them (wins), what decided it, and what would have changed the outcome (losses). Keep the
person who ran the sale out of the interview where possible; buyers soften criticism for the
person who sold to them. A founder interviewing alone should say plainly that honest criticism is
the point, and ask directly what the competitor did better.

Tally objections by category: missing capability, price, trust or security, integration,
switching effort, timing, incumbent relationship. After about eight to ten interviews per outcome
(rule of thumb) the top objection is usually clear. Route it:

| Top objection | Fix lives in |
|---|---|
| A missing capability shared across ICP deals | Product: scope it (`specs.md`) |
| They did not grasp what it does or who it is for | Positioning, `0x:growth-marketing` |
| Security review, procurement, references | `0x:sales-support` |
| Price or plan structure | `0x:pricing-monetization` |
| Switching effort | Product: import, migration help, done-for-you setup |

Fix one objection at a time and compare the win rate over the next comparable set of deals;
fixing three at once teaches nothing about which one mattered.

## Run a beta or early-access program

| Type | Size | Entry | Use for |
|---|---|---|---|
| Private alpha | 5–10 hand-picked accounts | Invitation | Risky or unfinished work, with close contact |
| Closed beta | Dozens, from an opt-in list | Per-account feature flag (`0x:ci-cd-release`) | Validating with a broader ICP sample |
| Open beta | Anyone, clearly labeled | Opt-in toggle | Edge cases, load, announcing early |

- Select participants who fit the ICP and actively use the product; eager volunteers often have
  unusual needs that pull the feature sideways.
- Set expectations in writing: what is unfinished, whether data is safe, how long it lasts,
  whether it will cost money afterward, and that it may change or be withdrawn.
- One feedback channel (a shared channel or a dedicated address) and a scheduled check-in with
  each alpha account.
- Write exit criteria before starting: a number of accounts completing the job, no open
  data-integrity bugs, the success metric moving, support load acceptable. A beta without exit
  criteria never ends.
- "Beta" excuses missing polish, never data loss or security holes.

## Tell users when the thing they asked for ships

The request log exists so this step is possible. When a feature ships:

1. Pull every requester from its problem record.
2. Send each a short personal note from the founder's address: "You asked about <problem> on
   <date>. It's live: <one-line how-to>. Thanks for pushing on this."
3. Announce it more broadly in the changelog and in-product (`0x:git-collaboration` for release
   notes, `0x:growth-marketing` for announcements).
4. Track adoption among requesters. If they do not use it, ask why; it is the cheapest test of
   whether the solution matched their problem.

Close the loop on refusals when a decision changes, and on user-reported bugs when the fix ships.
Users who see their feedback acted on give more of it and stay longer.

## Judge product-market fit from retention, the 40% survey and organic pull

Read three independent signals, and trust them only when they agree.

**Retention.** Plot cohort retention on the core action (`0x:product-analytics`). A curve that
flattens to a stable floor above zero means some segment keeps getting value; a curve still
sliding toward zero means no fit yet, whatever the sign-ups say. A healthy floor depends on the
category and natural usage frequency; compare against the product's own earlier cohorts.

**The 40% survey.** Ask users who have experienced the core value (used the core of the product
at least twice, the latest time within about two weeks): "How would you feel if you could no longer use <product>?" Very disappointed / Somewhat
disappointed / Not disappointed / I no longer use it. 40% or more answering "very disappointed" is
the widely used benchmark.

- Read it only after roughly 40 responses from qualified users (where Superhuman found it became
  directionally right); below that, report counts. Surveying 60–80 users often yields 40.
- Segment the answers. The segment with the highest "very disappointed" share is the ICP to focus
  on; ask that group for the main benefit and who else would benefit.
- Ask everyone how the product could be better. Keep only the "somewhat disappointed"
  respondents who name the same main benefit as the "very disappointed" group; what holds them
  back is the roadmap toward fit. Set aside requests from those who do not value that benefit.

**Organic pull.** Customers arrive and expand without being pushed: a growing share of sign-ups
heard about it from a colleague or friend, inbound requests name a specific use case, accounts add
teammates and teams unprompted, sales cycles shorten, and users complain loudly when it is down.

Not signals of fit: launch-day spikes, press coverage, sign-ups bought with ads, compliments,
investor interest.

Fit is per segment. A flattening curve, a passing survey and pull in one segment mean narrow to it
and grow there. None of the three after several honest iterations on the core job means going
back to `problem-validation.md` to pivot the segment or the problem.

## Ask the user

- **Will the founder personally run onboarding calls for the first users?** Default: yes, for
  roughly the first fifty.
- **Where should feedback live?** Default: helpdesk tags plus one table of problem records.
- **May sessions be recorded?** It needs notice, consent where required, and masking. Default:
  watched calls with consent; in-product recordings only with consent where required (EU and UK
  users, US all-party-consent states), notice and masked inputs (`0x:privacy-compliance`).
- **What are beta participants promised about price afterward?** Default: a founding discount for
  a fixed period, decided before anyone is invited.
- **What counts as fit for this business?** Default: a flattening retention curve plus at least
  40% "very disappointed" in one named segment.
