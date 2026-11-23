# Funnels and activation

Read this when: defining the activation event, finding where users drop between signup and
paying, segmenting a funnel, measuring time to first value, studying feature adoption, or
deciding whether a funnel finding is a cause or only a correlation.

## Define activation

Activation is the earliest observable behavior after which a new user or account is much more
likely to still be active later. It is a prediction about retention, not a milestone picked
because it sounds right. "Completed onboarding" is rarely it: onboarding completion measures
compliance with a checklist, not received value.

Shape: **unit did action N times within T days of signup**. For example "account created 2
projects and invited 1 teammate within 7 days". All four parts are choices:

| Part | Rule |
|---|---|
| Unit | The account for B2B (one user can activate a whole account), the user for consumer |
| Action | The core value action, the thing the product exists to do, completed, not started |
| N | The smallest count that separates retained from churned; often 1–3 |
| T | Short enough to act on: within the first session for simple tools, 7 days as a common ceiling, the trial length at most |

Procedure when there is history (rule of thumb: 200 or more signups old enough to judge
retention, so each cell of the table in step 3 holds tens of accounts; with less, see the
paragraph after the list):

1. Define "retained" first, for example active in week 4 or 8, or still paying at month 3
   (`references/retention-cohorts.md`).
2. List 5–10 candidate early behaviors, each with a count and window.
3. For each candidate compute a 2×2 table: did it or not, retained or not.
4. Prefer the candidate that is both **predictive** (retention among those who did it is
   several times retention among those who did not) and **reachable but not universal**
   (rule of thumb: 20–60% of signups do it). A behavior 95% of users perform cannot
   discriminate; one that 2% perform identifies fans, not a lever.
5. Check the candidate holds within the main segments (plan, channel). If it only works because
   one segment dominates, it is a segment marker, not an activation event.
6. Fix the definition in the metric dictionary (`references/north-star-metrics.md`) and emit
   one server-side event `activated` the moment the condition becomes true, so every tool counts
   it identically.

With little history (Prototype, early Launch): choose by reasoning. Take the action that
delivers the product's promise once, completed with the user's real data, and treat it as a
hypothesis. Check it against the retained users by hand, and by asking five of them what made
the product click. Revisit after every major product change and at least twice a year.

Measure it as **activation rate by signup cohort**: of accounts signed up in week W, the share
activated within T days. Report only cohorts whose window has fully closed; a cohort that is
three days old always looks worse, and including it produces a fake downward trend at the right
edge of every chart.

## Find the biggest drop in signup-to-paid

Stage: at Prototype, with tens of signups, write the funnel as names per step and talk to the
people who stopped; rates start to mean something at Launch volume.

Lay the whole path out as ordered, unambiguous steps before looking at any number:

`landing_page_viewed → signup_started → signed_up → email_verified → first core action →
activated → trial ending or paywall seen → checkout_started → subscription_started`

Then:

1. **Count unique units entering each step in one cohort**, with a conversion window that
   matches the real sales cycle (trial length plus a few days). Counting events instead of
   units, or mixing cohorts, are the two errors that make funnels disagree.
2. **Compute both step conversion and absolute loss.** The biggest percentage drop is not
   always the biggest opportunity. Rank steps by "units lost × plausible recovery". A step
   losing 70% of 1,000 units matters more than one losing 90% of 40.
3. **Judge each step by its kind.** Visitor-to-signup is low for almost every product (often
   single-digit percent, depending on the traffic source) and is mostly a traffic-quality
   matter (`0x:growth-marketing`); a large loss between
   `signed_up` and the first core action is almost always the product's fault and usually the
   highest-leverage fix at Launch.
4. **Look at the losers, not only the count.** Watch 10–20 session replays of users who
   dropped at the worst step, and read their support messages. The funnel says where; only
   observation says why.
5. **Check the instrument before the product.** A sudden cliff at one step is more often a
   broken event, an ad-blocked client event, or a redirect that loses identity (email
   verification opened on another device, OAuth return, checkout on the payment provider's
   domain) than a real behavior. Reconcile the first and last steps against the database.

Funnel settings that change the answer and must be stated on the chart:

| Setting | Default | Trap |
|---|---|---|
| Unit | account (B2B), user (consumer) | per-user funnels hide that a teammate completed the step |
| Order | sequential, other events allowed between | "strict" order undercounts real paths |
| Window | first step to last within trial length + 7 days | too short hides slow converters; too long delays every read |
| Counting | first time ever | repeat entries inflate top-of-funnel |
| Cohort date | date of first step | charting by completion date mixes cohorts |

A funnel across an identity break (anonymous visitor to signed-up user) only works if
`identify` links the anonymous ID. Otherwise report it as two funnels: visit → signup from
aggregate counts, signup → paid per account.

## Segment the funnel

An aggregate funnel is an average of very different populations. Break it by the dimensions
that were fixed before the user entered the funnel:

| Dimension | What it reveals | Note |
|---|---|---|
| Acquisition source (first touch) | channels that bring signups that never activate | join on first-touch source stored at signup (`references/attribution.md`) |
| Device and platform | a broken or cramped mobile signup; desktop-only products with mobile ad traffic | segment by device of the first step |
| Plan or intended plan | free vs trial vs paid behave like different products | use plan at the time of the event |
| Signup method | SSO vs email vs invited users | invited users skip steps; separate them or the funnel flatters itself |
| Company size or persona | whether the product fits the segment being sold to | from an onboarding question or enrichment |
| Signup cohort (week) | whether a release changed anything | the only honest before/after view |

Rules:

- Segment by **pre-funnel attributes** only. Segmenting by something that happens inside the
  funnel ("users who used feature X convert better") is a selection effect, covered below.
- **Minimum size** (rule of thumb): do not read a segment with fewer than about 100 units at
  the step being compared, or about 30 conversions. With 20 users, one person is 5 points.
- **Mix shift**: when the overall rate moves, check whether each segment moved or only the mix
  did. A campaign that doubles low-intent traffic lowers overall conversion while every
  segment is unchanged, and rates can even move in opposite directions in aggregate and within
  every segment (Simpson's paradox). Always show segment rates next to segment volumes.
- Cut at most two dimensions at once; beyond that the cells are too small to mean anything at
  Launch volume.

## Time to first value

Time to first value (TTFV) is the elapsed time from signup to the first completed core value
action. It predicts activation because motivation decays within the first session.

- Report the **median and the 75th or 90th percentile**, never the mean: the distribution has a
  long tail and the mean describes nobody.
- Report it alongside **the share who never get there**. A median computed only over users who
  reached value improves when slow users give up, which is survivorship. The honest view is a
  cumulative curve: share of the cohort that has reached first value by 5 minutes, 1 hour,
  1 day, 7 days.
- Decompose the path into intervals between consecutive steps and find the longest wait and
  the largest loss. Typical delays, in the order to suspect them: email verification before
  anything can be done; an empty state that needs data import or an integration; a required
  teammate, approval or admin permission; credit card or sales call before use; setup that
  needs a developer; long processing with no progress feedback.
- Fixes follow from the cause: defer verification, offer sample data or templates, let one
  person succeed alone before asking for invites, move configuration after the first result.
  UX design of those states belongs to `0x:ui-ux-design`.
- Some delays are external (waiting for a DNS change, a data sync). Measure active time and
  wall-clock time separately when that applies, and send a notification when the wait ends.

## Feature adoption and what retained users do differently

Measure a feature at four levels, because "used it once" hides everything that matters:

| Level | Definition | Reads as |
|---|---|---|
| Exposed | saw the entry point | discoverability problem if low |
| Tried | used once | value-proposition problem if exposed but not tried |
| Adopted | used in at least 2–3 separate periods | usability or value problem if tried but not repeated |
| Habitual | used at the feature's natural frequency | the only level that should count as success |

Use active eligible accounts as the denominator: a feature gated to a paid plan cannot be
adopted by free accounts, and a new feature's rate against all-time signups is meaningless.

To find what retained users do differently: split a signup cohort into retained and churned
by a fixed later date, then compare the share of each group that performed each behavior
during the **first week only**. Using behavior from the whole lifetime is circular, because
retained users were around longer to do everything. Rank behaviors by the difference in
retention, weighted by reach. The output is a list of hypotheses for experiments and
onboarding changes, not a list of causes.

A two-axis view for prioritizing features: adoption breadth (share of active accounts using
it) against retention of those users. High breadth and high retention is core; low breadth and
high retention deserves promotion and an experiment; high breadth and low retention is a
commodity; low on both is a candidate for removal.

## Correlation is not causation

Almost every funnel finding has the form "users who do X convert or retain better". Four
explanations compete, and only one justifies pushing everyone to do X:

| Explanation | Example | How to tell |
|---|---|---|
| X causes the outcome | integrating a data source makes the product useful | an experiment that raises X also raises the outcome |
| Intent causes both | motivated users invite teammates and also stay | forcing X on unmotivated users does nothing |
| Reverse or time bias | retained users had more time to do X | restrict X to a fixed early window |
| Segment marker | X is only available to, or typical of, larger customers | effect vanishes within segments |

Working rules:

- Fix the window for the behavior before the window for the outcome, and do not let them
  overlap.
- Check dose-response: if more of X goes with steadily more retention, a causal reading is
  more plausible than if only "any vs none" differs.
- Compare within segment before believing an overall difference.
- Treat the finding as a hypothesis ranked by plausibility and cost to test. Then test it:
  an A/B test when traffic allows (`references/experiments.md`), otherwise a dated
  before/after comparison of cohorts with every other change that week written down.
- A change that lifts the rate of X without moving the outcome has shown that X was a marker.
  That is a real result: record it and stop optimizing X.
- State findings in the language of the evidence: "accounts that connected a data source in
  week one retained at twice the rate" is true; "connecting a data source doubles retention" is
  a claim nobody has tested.

## Ask the user

- **What does a customer get from the product when it works?** The activation event must be a
  completed instance of that. Default: the first completed core action with the user's own data.
- **Is success per user or per account?** Sets the funnel unit. Default: account for B2B.
- **How long is the real decision cycle (trial length, typical days from signup to payment)?**
  Sets the funnel window. Default: trial length plus 7 days; 30 days when there is no trial.
- **Which segments does the business care about?** Decides which properties must exist at
  signup. Default: first-touch source, device, plan, signup method.
- **Is there a sales-assisted path?** Deals closed by a person bypass product funnel steps and
  must be marked, or the self-serve funnel is polluted. Default: tag them `sales_assisted` and
  report the self-serve funnel separately.
