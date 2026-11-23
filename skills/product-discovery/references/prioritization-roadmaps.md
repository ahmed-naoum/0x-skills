# Prioritization and roadmaps

Read this when: choosing what to build next, scoring a backlog, answering a feature request,
planning a quarter, publishing a roadmap, judging a shipped feature, removing one, or handing a
product area to someone else.

## Prioritize against one goal with impact, confidence and effort

Score only against the current goal metric (choosing it is `0x:product-analytics`). "Good for
the product in general" scores everything high and decides nothing.

| Factor | Scale | Set it from |
|---|---|---|
| Impact | 3 massive, 2 high, 1 medium, 0.5 low, 0.25 minimal, on the goal metric | Accounts affected, revenue at stake, which funnel step |
| Confidence | 100% measured, 80% several customers' behavior, 50% a few interviews or requests; below 50% is a guess to test, not score | The evidence, never the enthusiasm |
| Effort | Person-weeks, rounded up (RICE uses person-months; keep one unit per backlog) | A range; re-estimate anything over two weeks after a spike |

Score = Impact × Confidence ÷ Effort. These are Intercom's RICE scales; adding Reach (accounts
affected per quarter) as a multiplier gives full RICE, worth it when items touch very different
numbers of users. ICE variants instead rate impact, confidence and ease 1–10; never mix scales
within one backlog, because the rankings stop being comparable.

- Score only the top twenty candidates. Archive anything untouched for six months; what matters
  comes back.
- The score ranks, judgment decides: take the top five, then check dependencies, sequencing and
  strategy.
- Low confidence on high impact means "run a cheap test first", not "build" or "drop".
- Bugs that lose money or data or expose security are not scored; they jump the queue.
- Recurring traps: impact inflated for the founder's favorite, effort that leaves out testing,
  migration, docs and support, and maintenance cost never counted at all.

## Decide which requests to refuse, and say no well

Every built feature costs something forever: support, tests, docs, interface clutter, and
constraints on every later change. The default answer to a request is "not now". It becomes yes
when it passes all four:

1. It serves the ICP's core job, not a different job or a different customer type.
2. The underlying problem, not the requested solution, appears across several ICP accounts;
   count them and the revenue they represent.
3. It does not turn the product into one customer's custom software.
4. Build plus maintenance cost is justified by its score against the current goal.

Before deciding, find the problem behind the request: "What would that let you do? When did you
last need it? What did you do instead?" Many requests dissolve into an existing feature, a docs
gap, or a smaller fix.

A large customer demanding custom work is a separate decision: decline, or sell it as paid custom
work under its own terms (`0x:sales-support`), knowing the result must still be maintained.

```text
Thanks for laying out how you use <area>; the <their problem, in their words> part is clear.
We're not building <request> right now because we're focused on <current goal> for <ICP>.
Meanwhile, <workaround, export, integration, or an honest pointer elsewhere>.
I've logged this with your name and will tell you directly if that changes.
```

- Restate their problem so they know it was heard, give the real reason, offer a path.
- Never say "it's on the roadmap" when it is not. Customers plan around it, and it can turn into
  a contract dispute.
- Log every request with requester, account, segment, revenue and underlying problem
  (`feedback-loops.md`). The log turns refusals into evidence and makes closing the loop possible.

## Balance customer requests, strategic bets and maintenance

Allocate capacity explicitly, or the loudest category takes all of it. A starting split at Launch
(rule of thumb, revisit each quarter):

| Bucket | Share | Contains |
|---|---|---|
| Core job and customer-driven work | About half | Fixes to the main path, top problems from the request log |
| Strategic bets | About a quarter | A new segment, a new capability, expansion revenue |
| Maintenance and reliability | About a quarter | Bugs, upgrades, debt that slows delivery, operations |

| Signal | Shift toward |
|---|---|
| Incidents, a growing bug count, delivery slowing | Maintenance (`0x:engineering-leadership` for debt) |
| Churn or weak activation | Core job |
| Strong retention, flat growth | Bets on acquisition or expansion |
| Prototype stage | Almost all learning; maintenance near zero |
| Scale stage | Maintenance grows with the codebase and the team |

Plan to about 70% of capacity. Unplanned work (incidents, escalations, the request that truly
cannot wait) always arrives, and a plan at 100% is a plan to slip.

## Run a quarterly roadmap tied to metrics

A half-day each quarter, one page of output:

1. **Review.** The goal metric against its target, what shipped, what each shipped item did to
   its own success metric, what was learned.
2. **Choose the goal.** One metric, two at most: the input metric most likely to move the business
   now (`0x:product-analytics` for metric trees).
3. **Gather candidates** from the ranked problem table, the request log, churn and win/loss
   findings, and data. Each links to its evidence; a candidate without evidence is a hypothesis to
   test, not a bet to build.
4. **Score and choose** two or three bets that fit about 70% of capacity, plus the maintenance
   share.
5. **Write an outcome target per bet**: metric, baseline, target, read date.
6. **Check at mid-quarter.** Keep, cut or swap bets on evidence. Finishing a failing bet because
   it was planned is the sunk-cost trap.
7. **Close** by recording results against targets before the next planning session.

Opinions enter only with evidence attached: "customers want X" must link to its counted problem
row. At Prototype skip quarters and plan in two-week cycles; the quarterly process pays off from
Launch, once there is a metric to move.

## Publish a now, next, later roadmap without dates

| Column | Contains | Commitment |
|---|---|---|
| Now | Being built | High; "this month" only when confident |
| Next | Shaped, likely within one to three months | Medium; order can change |
| Later | Problems under consideration | Low; may never happen |

- Write items as problems or outcomes ("faster month-end close for multi-entity clients"), not
  features, so the solution can change without breaking a promise.
- No dates beyond Now. Dates on a public roadmap become commitments that customers and their
  managers plan around.
- Say on the page that it changes, update it monthly, and move shipped items to the changelog.
- Public voting measures what vocal users want, not what retains the ICP. Count votes as one
  signal, weighted by segment and revenue.
- Keep roadmap items out of contracts and sales promises. A deal that depends on a future feature
  is a custom-work decision (`0x:sales-support`), made deliberately.
- Skip a public roadmap at Prototype. At Launch it helps sales and cuts "is this coming?" tickets;
  keep a more detailed private version for planning.

## Judge a shipped feature: kill, iterate or double down

Set the read date and thresholds in the spec (`specs.md`) and read four to eight weeks after full
rollout. Measurement mechanics are `0x:product-analytics`.

| Adoption (share of active accounts using it) | Repeat use by adopters | Reading | Decision |
|---|---|---|---|
| Low | High | Valuable but undiscovered or hard to reach | Double down on exposure: placement, onboarding, announcement |
| High | Low | Tried once, did not deliver | Watch sessions, ask adopters; iterate once, then kill |
| Low | Low | Not wanted | Kill |
| High | High | Working | Double down: deepen, extend, charge for it |

- Check the goal metric and guardrails, not only usage. A popular feature that does not move
  retention is a cost with fans.
- With a few dozen accounts the numbers mislead; talk to adopters and non-adopters before deciding.
- Pivoting a feature keeps the job and changes the solution: state what the iteration tests and
  set one more read date.
- Killing early is cheap. Killing after a year of customers relying on it requires the
  deprecation process below.

## Deprecate a feature

1. **Measure who uses it**: accounts, revenue, last use, frequency, and whether it is promised in
   contracts or on the pricing page. Check terms and contracts for notice obligations
   (`0x:privacy-compliance`, `0x:sales-support`).
2. **Decide replacement or removal**, and the migration path: an alternative feature, an export,
   or an integration.
3. **Talk to the heaviest users first**, personally, before announcing. They expose the migration
   problems and are the accounts most at risk.
4. **Announce** by email, an in-product banner where the feature is used, and the docs: what is
   going, why, the date, the alternative, how to export. Notice, as a rule of thumb: a few weeks
   for a minor free feature, months for anything paid, built into workflows, or exposed through an
   API (`0x:api-design` for API deprecation).
5. **Stop new adoption first**: hide it for new accounts with a flag (`0x:ci-cd-release`), then
   remove it for existing ones on the announced date.
6. **Remind** a week before and on the day; keep export available throughout.
7. **Remove the code and the data** under the retention policy (`0x:data-stores`).

If paying customers lose something they pay for, decide in advance whether a credit, a price
change or a longer notice applies. A surprise removal triggers churn and disputes.

## Delegate a product area with outcome targets

When an engineer, contractor or first product hire takes over an area, hand over an outcome, not
a feature list.

```text
Area:            Team onboarding.
Outcome:         Share of new workspaces with 3+ active members in week four,
                 from <baseline> to <target> by <date>.
Constraints:     No pricing changes. No new third-party integrations. Core editor out of scope.
Decision rights: Decide and ship anything inside the constraints. Consult on anything shown on
                 the pricing page or emailed to all users. The founder decides ICP changes.
Context:         Links to the ranked problem table, interview cards and the funnel dashboard.
Check-in:        30 minutes weekly on the metric and what was learned, not on task status.
```

- Give them data access and customer access. An outcome without access to evidence is a feature
  list in disguise.
- Name what they decide alone; vagueness turns into the founder approving every detail.
- Judge the outcome and the quality of the reasoning, not the volume of output.
- Managing people beyond this belongs to `0x:company-building`.

## Hire a first product manager when founder attention is the bottleneck

Before product-market fit the founder is the product manager; discovery is too central to hand
off. Signs that it is time:

- Engineers repeatedly wait on decisions or build from thin specs.
- Customer evidence piles up unsynthesized, and the weekly conversations have stopped.
- Product work crowds out what only the founder can do: selling, hiring, fundraising, strategy.
- There are more product areas than one person can hold in their head in enough detail.

Try the cheaper fix first: senior engineers who own areas end to end, including talking to
customers, with outcome targets as above.

The first hire is hands-on: has run interviews and written specs that shipped, is comfortable
with data, and is close to the domain; not a head of product expecting a team. The founder keeps
vision, strategy and the ICP; the product manager takes the discovery cadence, specs, the request
log and prioritization within that strategy. The hiring process is `0x:company-building`.

## Ask the user

- **What is the one metric this quarter is about?** Everything scores against it. Default:
  activation at Launch, retention once activation is healthy.
- **How much capacity is there, in person-weeks?** Default: plan to 70% of it.
- **What has already been promised, and to whom?** Promises constrain the plan and must be kept or
  renegotiated explicitly. Default: assume none until checked.
- **Should the roadmap be public?** Default: no at Prototype; a now, next, later page at Launch.
- **How much weight do the largest customers get?** Default: weight requests by ICP fit first and
  revenue second; no single account sets the roadmap.
