# Estimation, planning and delivery

Read this when: answering "how long will this take?", slicing and sizing a feature or project,
planning several weeks of work, checking whether delivery is on course, deciding what to cut
when a date is at risk, or agreeing a date with a customer, investor or co-founder.

## Slicing work into shippable increments

Each increment is a vertical slice (data, API, UI) that someone can use in production, ideally
behind a flag, and takes two days or less. A piece estimated above five days is not understood
yet: split it, or spike it first (`build-vs-buy.md`).

| Technique | Example |
|---|---|
| Happy path first, edge cases after | Import the standard CSV; malformed rows next |
| One user type or plan first | Workspace admins before members |
| Manual behind the curtain | Founder approves sign-ups by hand before automating it |
| Hard-code, then configure | One email template; template settings later |
| Read before write | Show the data before allowing edits |
| One integration first | One calendar provider before the second |
| Single before bulk | Invite one person before CSV invites |

Example, "team invitations": (1) an admin invites one email address and the invitee joins, with
no email sent; the link is copied by hand; (2) the invitation email; (3) expiry and resend;
(4) roles; (5) bulk invite. Slice 1 is in production on day one and exposes the data-model
questions while they are cheap.

Size each slice roughly: S under half a day, M up to two days, L up to five days (split it).
With coding agents, writing code is rarely the long part. Review, verification, integration,
production data migrations, third-party approvals and unknowns dominate; estimate those
explicitly instead of estimating typing time.

## Ranges, not single numbers

A single number is heard as a promise. Give a range and say what it means: a date with roughly
even odds (the 50 percent date) and a date that is very likely to hold (the 90 percent date).
For each item, note a best, likely and bad case; the bad cases drive the 90 percent date.

Estimates made at the idea stage are commonly off by a factor of several in either direction;
ranges narrow only after the riskiest unknowns are resolved, not because more time was spent
estimating. Widen the range for any of these: first use of a technology, a new vendor
integration, migrating production data, an external approval, work that depends on another team.

Calibrate: record estimate and actual for a month of your own tasks and compute the ratio.
Multiply new estimates by it. For most people it is above one, and it is stable enough to use.

## Re-forecasting from throughput

Once work is underway, stop re-estimating items and count finished ones. With slices of similar
size, throughput (items finished per week) forecasts better than any estimate. Track scope
added separately: most slips are scope growth, not slow work.

```text
Remaining: 24 items. Finished in the last four weeks: 5, 7, 4, 6.
Scope frozen:   24 / 7 = 3.4 weeks at best, 24 / 4 = 6 weeks at worst  ->  "4 to 6 weeks"
Scope growing:  6 items added in four weeks = 1.5 per week
                net progress 2.5 to 5.5 per week  ->  "4.5 to 10 weeks unless scope is frozen"
```

Re-forecast weekly and publish the range when it moves. The second line above is usually the
conversation to have: freeze scope or accept the later date.

## Planning a multi-week project

Order work by risk first, then value. An unknown discovered in week five kills the plan; the
same unknown found in week one is a scope change.

| When | What |
|---|---|
| Days 1-2 | One-page design doc (`decision-records.md`); list unknowns ranked by likelihood times impact; start every long-lead item |
| Week 1 | Walking skeleton: the thinnest end-to-end path deployed to production behind a flag, plus the riskiest unknown |
| Middle weeks | Increments by risk, then value; a demo every week |
| Last 20-25% of the time | Planned buffer: hardening, data migration, rollout, docs, support preparation |
| Release | Progressive rollout behind the flag; done means in users' hands and measured |

Long-lead items to start on day one, because they run on someone else's queue: app store
review, verification of an OAuth app requesting sensitive scopes, payment provider account and
payout verification, DNS and email sender setup, an enterprise customer's security review, an
auditor's calendar, partner API access, legal review of new terms.

Weekly demo rules: working software, not slides; in production behind a flag where possible;
show what was cut as well as what was built; the stakeholder makes trade-off decisions at the
demo, so the demo is where scope gets negotiated, not the deadline.

## When the project slips: cut scope, not quality

Levers in order: scope, then date, then people. Adding people late makes a project later for
weeks (Brooks's law) because of onboarding and coordination; with agents, adding parallel
sessions late has the same effect on review load. Quality is not a lever.

The floor that is never cut:

- Authorization checks and input validation on every new endpoint.
- Data integrity: database constraints, online and reversible migrations, backups.
- Billing correctness.
- Tests on the critical paths the work touches.
- Error tracking, and a way to know the feature is broken.
- A rollback path.

Cuts that work:

| Cut | Replace with | Cost later |
|---|---|---|
| Settings and configurability | Hard-coded defaults | A settings slice when asked for |
| Admin UI | A script or SQL runbook in the repo | Founder time per request |
| Second platform or integration | One first | Lost users of the other, measured |
| Edge cases | An explicit "not supported yet" error, logged and counted | Fix the most common ones |
| Automation | A manual process run by the founder | Hours per week; automate when it hurts |
| Bulk operations | One at a time | |
| Self-serve onboarding | Sales-assisted setup | Founder time per customer |
| Polish beyond basic empty and error states | Plain version | Polish later with data |

Check at about one-third of the elapsed time: compare finished slices with the plan and cut
then, while cuts are cheap. Cutting in the last week leaves half-built features in the code.
Add each cut to the backlog and each shortcut to the debt register (`technical-debt.md`).

## Measuring delivery: the four keys

The DORA research program's four measures describe delivery performance at team level. Speed
and stability improve together, because small, frequent changes are easier to verify and undo.

| Measure | Definition | Small-team source | Rule-of-thumb target for a web product |
|---|---|---|---|
| Deployment frequency | Production deploys per day or week | Successful deploy runs on the main branch | Daily or more |
| Lead time for changes | Change started to running in production | Pull request opened to merged, plus merge to deploy | Under a day |
| Change failure rate | Share of deploys causing an incident, rollback or hotfix | Deploys tagged rollback or hotfix | Under about 15% |
| Recovery time | Time to restore service after a failed deploy | Incident log | Under an hour |

```bash
# Successful runs of the deploy workflow on main, among the last 100
gh run list --workflow deploy.yml --branch main --limit 100 --json conclusion,createdAt \
  --jq '[.[] | select(.conclusion == "success")] | length'
# Open-to-merge times for recent pull requests
gh pr list --state merged --limit 50 --json number,createdAt,mergedAt
```

Skip formal measurement at Prototype. At Launch, look monthly; at Scale, put them on a
dashboard. Use them for trends of the team and the system, never to rank individuals: once a
measure becomes a target for a person, it gets gamed. If failure rate climbs with frequency,
invest in tests and flags rather than deploying less. Improving the pipeline is `0x:ci-cd-release`;
recovery practice is `0x:site-reliability`.

## Negotiating commitments

Separate three things that get blurred: a target (what someone hopes for), an estimate (a
forecast with a range) and a commitment (a promise). Only commitments should reach customers.

- Never accept a date without a written scope list and a written "not included" list.
- Fixed date means variable scope; fixed scope means variable date. If both are fixed, quality
  pays silently; refuse that shape and say why.
- Offer options instead of a yes or no: "A by March 1; A and B by March 20; or A with C cut by
  February 15."
- Commit externally to the 90 percent date; plan internally to the 50 percent date.
- Announce a slip as soon as the forecast moves, with the new range and the options. A warning
  in week two is a planning input; the same news at the deadline is a breach of trust.
- Features promised in a sales contract need written scope, acceptance criteria and engineering
  sign-off before signature (`0x:sales-support` for the contract side).

```text
"Here is what fits by the 15th: A and B. C adds about two weeks. Options: ship A and B on the
15th and C on the 29th, or move everything to the 29th. I recommend the first, because A is
what the pilot customer is waiting for."
```

## Coordinating dependencies across teams

This becomes real at Scale, or earlier with contractors, agencies and partners.

- Map dependencies at kickoff: who delivers what, by when, with an owner on each side. Treat
  each one as a risk item.
- Agree contracts first (API schema, event shapes), then build against mocks on both sides.
- Integrate one thin path through every dependency in the first two weeks, not at the end.
- Remove dependencies where possible: make the change in the other team's code through a pull
  request they review, or reshape scope so it is not needed.
- Find the critical path, the chain whose delay moves the end date, and manage that closely;
  other dependencies need only a weekly check.
- Hold a short weekly sync about dependencies only, with a shared list of dates.
- Escalate a slipping external dependency the day it slips, not at the integration date.

## Ask the user

- **Is the date or the scope fixed, and why?** A trade show or a contract makes the date real;
  an internal wish does not. Default: the date is soft and scope is negotiated weekly.
- **Who needs the forecast, and do they get the 50 or the 90 percent date?** Default: the 90
  percent date for anyone outside the company, the range for co-founders.
- **What can be done manually by the founder for the first customers?** It often halves scope.
  Default: anything under an hour a week stays manual.
- **Which features have been promised to customers, in writing or verbally?** Hidden promises
  are the commonest cause of fixed scope. Default: assume none until listed.
- **Is there a cost to being late beyond embarrassment?** Penalty clauses, a funding milestone
  or a launch window change how much buffer to plan. Default: none; plan a 20 percent buffer.
