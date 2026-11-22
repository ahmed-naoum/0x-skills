# North-star metric and metric trees

Read this when: choosing the number the company steers by, building a metric tree from product
inputs to revenue, writing metric definitions so reports agree, setting guardrails, specifying
the weekly scorecard, or setting up a weekly metrics review.

## Choose the north-star metric

The north-star metric (NSM) counts how much value customers received in a period. Revenue is
the consequence and lags it; signups and page views precede value and can grow while the
product fails. A good NSM sits between the two.

Test each candidate against all of these:

| Test | Question | Fails when |
|---|---|---|
| Value | Does it go up only when customers get what they came for? | counts logins, signups, sessions, time spent |
| Leads revenue | Does a sustained rise predict revenue a few months later? | it can rise while revenue falls |
| Movable | Can product and growth work move it within weeks? | it is an annual outcome (ARR, NPS survey) |
| Measurable weekly | Is it computed from events that already exist and are trusted? | needs a survey or a manual count |
| Hard to game | Is the cheapest way to raise it also good for customers? | it rises through spam, discounts, or forced actions |
| Understandable | Can it be said in one sentence without a formula? | it is a weighted index |

Typical forms, by how the product creates value:

| Product | NSM form | Example |
|---|---|---|
| B2B workflow SaaS | weekly active accounts doing the core action | accounts publishing at least one report per week |
| Collaboration | weekly active teams with 2+ contributors | teams with 2+ members editing |
| Transaction or marketplace | completed transactions or their value | orders delivered |
| Usage-priced API | successful billable units by active customers | production API calls by paying accounts |
| Consumer attention | time or sessions with quality content, with a quality threshold | weekly users completing 3+ lessons |

Rules:

- **Include a quality threshold in the definition** ("accounts with 3+ published reports", not
  "reports published"). A raw count is dominated by a few heavy accounts and by automation.
- **Prefer a count of customers receiving value over a sum of activity** at Launch. Counts of
  accounts are robust to outliers and map directly to revenue through price.
- **One NSM for the company.** A second "north star" for a team is an input metric.
- **Stage**: at Prototype there is no NSM; the number to watch is conversations with users and
  the count of people who came back unprompted. Choose the NSM once there is repeat usage to
  count. Revisit at each change of business model or core use case, not each quarter.
- Revenue (MRR) is always reported next to the NSM. If the two diverge for more than a couple
  of months, the NSM is wrong or pricing is (`0x:pricing-monetization`).

## Input metrics and the metric tree

The NSM cannot be worked on directly. Decompose it into inputs that a specific piece of work
can move this month. Two decompositions cover most products; build both and check they agree.

**Arithmetic (flow) decomposition** of an active-accounts NSM:

```text
weekly active accounts (NSM)
= new activated accounts          = signups x activation rate
+ retained active accounts        = last week's actives x retention rate
+ resurrected accounts
```

**Revenue tree**, linking the same inputs to money:

```text
MRR = paying accounts x average revenue per account (ARPA)
  paying accounts = previous paying + new paying - churned
    new paying    = visitors x visit->signup x signup->activated x activated->paid
    churned       = previous paying x logo churn rate
  ARPA            = plan mix x price + seats or usage expansion - discounts
```

Each leaf should name one event-based metric, the lever that moves it, and an owner:

| Input | Metric | Typical levers |
|---|---|---|
| Acquisition | qualified signups per week, by channel | channels, landing page, positioning (`0x:growth-marketing`) |
| Activation | share of signup cohort activated within T days | onboarding, time to first value |
| Engagement | core actions per active account; seats active | features, notifications, integrations |
| Retention | week-N retention of activated cohorts; logo churn | product depth, support, reliability |
| Monetization | activated-to-paid rate; ARPA; expansion | pricing, packaging, paywall placement |

How to use the tree:

- **Find the constraint.** Compute each stage and ask which, improved by a plausible amount,
  moves the root most. With multiplicative stages a relative gain anywhere gives the same
  relative gain at the root, so the choice turns on which stage is furthest below what is
  achievable and cheapest to change. Before product-market fit that is nearly always
  activation and retention, not acquisition.
- **Sensitivity check**: change one input by 10% in a spreadsheet model of the tree and read
  the effect on MRR after 6 and 12 months. Retention changes compound and usually win over a
  year; acquisition changes show up fastest.
- **Stop at inputs a team can move.** A tree deeper than three levels is not used. Three to
  five inputs are worked on at once; the rest are monitored.
- The tree is a model of the business. When an input moves and the root does not, the model is
  wrong at that edge: fix the tree rather than explaining the result away.

## Write each definition once

"Everyone reports a different number" is almost always a definition problem, not a data
problem. The same word ("active users", "conversion", "churn") is computed with a different
unit, window, filter or source in each tool. Keep one metric dictionary in the repository (for
example `docs/metrics.md`) and point every dashboard at it.

Each entry:

```markdown
### Activation rate
- Definition: share of accounts created in a signup week that fire `activated` within 7 days.
- Unit: account. Grain: signup week (Mon–Sun, UTC).
- Numerator: distinct accounts with `activated` at <= created_at + 7 days.
- Denominator: accounts created in the week.
- Exclusions: is_internal, test accounts, accounts created by invite into an existing company.
- Source of truth: product analytics insight "Activation rate (official)"; SQL in metrics/activation.sql.
- Reporting lag: a week is final 7 days after it ends.
- Owner: <name>. Changed: 2026-03-02, window 14 -> 7 days, history restated.
```

The decisions that cause every disagreement, to settle explicitly per metric:

| Decision | Options that differ | Default |
|---|---|---|
| Unit | user, account, subscription, visitor | account for B2B |
| Time zone and week | UTC vs local; Monday vs Sunday start | UTC, ISO week (Monday) |
| Window | calendar period vs rolling N days | rolling for trends, calendar for reports |
| Date attribution | by cohort date vs by event date | cohort date for rates |
| Filters | internal, test, trial, free, refunded, fraud | exclude internal and test everywhere |
| Source of truth | analytics tool, product database, billing system | billing for money, database for counts of entities, analytics for behavior |
| Incomplete periods | shown or masked | masked |

Rules: one source of truth per metric, named in the entry. Money comes from the billing system,
never from analytics events. Counts of entities (accounts, subscriptions) come from the
database. Behavior comes from analytics. Mark one saved insight or query per metric as official
and derive every other chart from it. When a definition changes, restate history and record
the date; never leave a silent break in a series. Two tools will not match exactly: agree on an
acceptable gap (a few percent between analytics and the database is normal for client events)
and investigate only beyond it.

## Guardrails and counter-metrics

Any single number, once it is a target, is raised by the cheapest available means. For each
metric being pushed, name the harm that the cheapest route would cause and watch that too.

| Pushed metric | Cheapest bad route | Counter-metric |
|---|---|---|
| Signups | low-intent traffic, removing friction that qualifies | activation rate; cost per activated account |
| Activation rate | lowering the bar; forced steps | week-4 retention of activated cohorts |
| Engagement or sessions | notifications, dark patterns | unsubscribe and opt-out rates; retention |
| Trial-to-paid | discounts, hidden cancellation | refunds, chargebacks, 90-day paid retention, ARPA |
| Revenue or ARPA | price increases on captive customers | logo churn, GRR, support complaints |
| Feature adoption | forcing the feature into every flow | task completion time; core action rate |
| Ship velocity | skipping quality | error rate, p95 latency, support tickets per active account |

Rules: a guardrail has a threshold decided in advance ("do not ship if week-4 retention of the
cohort drops more than 2 points"), not a vague intent to keep an eye on it. Keep two or three
always-on guardrails for the company: reliability (error rate or uptime; see
`0x:site-reliability`), customer pain (support contacts per active account), and money quality
(refund or churn rate). Pair every rate with its volume, since a rate improves when the
denominator shrinks. Experiments carry the same guardrails (`references/experiments.md`).

## The weekly scorecard

One page, the same every week, readable in two minutes. It is a table, not a dashboard:

| Metric | Owner | This week | Last week | 4-week avg | Target | Status |
|---|---|---|---|---|---|---|
| NSM: weekly active accounts (3+ reports) | | | | | | |
| New qualified signups | | | | | | |
| Activation rate (cohort closed this week) | | | | | | |
| Week-4 retention (latest complete cohort) | | | | | | |
| New paying customers | | | | | | |
| MRR and net new MRR (from billing) | | | | | | |
| Logo churn (count and names) | | | | | | |
| Guardrail: error rate or support contacts per active account | | | | | | |

Specification rules:

- **5 to 9 rows.** The NSM, one row per input being worked on, revenue, and the guardrails.
  A metric nobody would act on does not get a row.
- **One named owner per row**, even when the company is one person and every name is the same:
  the column forces the question "who notices when this moves".
- **Targets come from the tree**: set the revenue goal, back out what each input must be, and
  write that as the target. A target with no derivation is a wish. Give a threshold for
  red/yellow/green decided in advance.
- **Weekly grain, same cut-off every week** (for example Monday 00:00 UTC), and trailing
  4-week average next to the weekly value so one noisy week does not cause a reaction.
- **Lagging cohort metrics are labeled with their cohort**: this week's retention row describes
  users who signed up four weeks ago.
- **Counts instead of rates when numbers are small.** "3 of 41 churned" with names is more
  honest than "7.3%" at Launch.
- Generate it automatically from the official queries (a scheduled job writing to a document
  or channel). A scorecard assembled by hand is abandoned within two months. Building the
  queries and charts belongs to the `data` and `dataviz` skills.

## The weekly review

The scorecard exists to produce decisions. A review that only reads numbers aloud is a
status ritual and should be replaced by the scorecard email.

Format, 30 minutes, same slot every week, also for a solo founder (as a written note):

1. **Before**: scorecard distributed; each owner writes one line per red or surprising row:
   what happened, suspected cause, proposed action.
2. **5 min**: read the scorecard in silence; mark what is off target or moved beyond normal
   week-to-week variation.
3. **15 min**: discuss only those rows. For each, classify the movement: instrumentation or
   definition change, mix shift, seasonality or calendar effect, a release, or an external
   event. Check annotations for deploys and campaigns first.
4. **10 min**: decisions. Each ends as one of: change priority, start or stop an experiment,
   investigate (with an owner and a date), or explicitly do nothing.
5. **After**: write the decisions in a running log with the date. Open next week's review by
   reading last week's actions.

Rules that keep it useful: do not react to one data point; require a move beyond the usual
range of the last 8 weeks or two consecutive weeks in one direction. Do not debug data in the
meeting; assign it. Once a quarter, review the scorecard itself: remove rows that never led to
a decision, and check the tree still explains revenue.

## Ask the user

- **What does a customer get from the product, in one sentence?** The NSM counts that.
  Default: weekly accounts completing the core action at a minimum count.
- **What is the revenue goal for the next two quarters?** Targets for inputs are derived from
  it. Default: no target set; report trends and 4-week averages until one exists.
- **Which stage is the constraint right now, in the founder's view?** Compared with what the
  tree shows; disagreement is worth a conversation. Default: activation and early retention.
- **What must not get worse while pushing growth?** Becomes the guardrails. Default: error
  rate, refunds or churn, support contacts per active account.
- **Who reads the scorecard, and where (email, chat channel, document)?** Decides delivery.
  Default: a weekly message on Monday morning, generated automatically.
