# A/B tests and their statistical traps

Read this when: someone wants to A/B test a change, asks whether there is enough traffic,
needs an experiment designed or a result interpreted, or wants to know the long-term effect of
a feature or a lifecycle program.

## First question: is there enough traffic?

Sample size per arm for a conversion rate, at 5% two-sided significance and 80% power (rule of
thumb accurate enough for planning):

```text
n per arm ≈ 16 × p × (1 − p) / δ²
p = baseline conversion rate, δ = absolute difference to detect (p × relative lift)
```

For small p this reduces to a number worth memorizing: **conversions needed per arm ≈ 16 / r²**,
where r is the relative lift to detect.

| Relative lift to detect | Conversions per arm | Units per arm at 5% baseline | At 20% baseline |
|---|---|---|---|
| 5% | ~6,400 | ~122,000 | ~26,000 |
| 10% | ~1,600 | ~30,000 | ~6,400 |
| 20% | ~400 | ~7,600 | ~1,600 |
| 50% | ~64 | ~1,200 | ~260 |

Decision:

1. Take the weekly number of units reaching the point where variants differ (not total
   traffic) and the baseline rate of the primary metric.
2. Compute the smallest lift detectable within **4 weeks** (two arms). Rule of thumb: a test
   that needs longer than 4–6 weeks is not worth running; cookies churn, the product changes
   under it, and the opportunity cost of the slot is too high.
3. If that lift is larger than the change could plausibly produce, do not run the test.

Typical consequence: a product with a few hundred signups a week can only detect lifts of
30–50% or more on signup-to-activation, and cannot test anything on paid conversion. Most
Prototype and early Launch products are below the threshold for almost every test, and should
say so instead of running underpowered tests whose "winners" are noise. An underpowered test
that reaches significance overstates the effect and may have the sign wrong.

What to do instead when traffic is too low:

| Method | Use for | Caveat |
|---|---|---|
| Ship and compare signup cohorts before/after | changes expected to be large | write down every other change that week; seasonality and channel mix confound |
| Make bigger bets | redesign the step, not the button color | large effects are the only detectable ones |
| Test higher in the funnel | landing page headline, pricing page | more units; the metric is further from revenue |
| Move to a more frequent metric | activation step instead of paid conversion | only valid if the proxy is known to track the goal |
| Qualitative testing | 5 usability sessions, session replays, customer calls | finds what is broken; does not size the effect (`0x:ui-ux-design`, `0x:product-discovery`) |
| Fake-door or painted-door test | demand for a feature not yet built | be honest with users on the next screen |
| Staged rollout with guardrails | safety, not optimization | answers "did it break", not "is it better" (`0x:ci-cd-release`) |

## Design

Decide all of this before the first user is exposed, and write it in the brief:

| Element | Rule |
|---|---|
| Hypothesis | "Because [evidence], changing X for [population] will move [metric] by about [size]" |
| Primary metric | exactly one; the decision rests on it; prefer a metric counted per randomization unit |
| Minimum detectable effect | the smallest lift that would change the decision, not the lift hoped for |
| Sample size and duration | from the formula; whole weeks, at least 1 and preferably 2, to cover weekday and weekend behavior |
| Guardrails | 2–4 metrics that must not get worse (retention, refunds, errors, latency, support contacts), each with a threshold |
| Secondary metrics | few, declared in advance, treated as exploratory |
| Population and trigger | who is eligible, and the exact moment a unit counts as exposed |
| Split | 50/50 unless risk demands a ramp; unequal splits cost power |
| Stopping rule | see below |
| Decision rule | what happens on win, loss, and flat; "flat" needs a default (usually: ship the simpler variant) |

Stopping rule, one of:

- **Fixed horizon** (default without a sequential engine): run to the planned sample size and
  whole weeks, look at significance once, at the end. Stop early only for harm: a guardrail
  breach or a bug.
- **Sequential or Bayesian with the tool's built-in rule**: early stopping is valid only if the
  statistics engine is designed for continuous monitoring. Use the tool's method consistently;
  do not read a fixed-horizon p-value daily and call it sequential.

A Bayesian "probability of being best" does not remove the need for a planned sample size:
with little data it swings widely, and stopping the first time it crosses 95% is peeking under
another name.

Variance reduction worth knowing at Scale: adjusting the metric by each unit's pre-experiment
value of the same metric (CUPED) shortens tests for metrics with history, such as engagement
or revenue per existing user. It does nothing for new-user conversion, where there is no
pre-period.

## Assignment and sample-ratio mismatch

Assignment must be deterministic, sticky and independent across experiments:

```ts
import { createHash } from "node:crypto";

export function variant(experimentKey: string, unitId: string, split = 0.5) {
  const h = createHash("sha256").update(`${experimentKey}:${unitId}`).digest();
  const bucket = h.readUInt32BE(0) / 0x100000000; // uniform in [0, 1)
  return bucket < split ? "control" : "test";
}
```

- Hashing the experiment key with the unit ID gives each experiment an independent split. A
  shared hash of the ID alone puts the same users in "test" for every experiment.
- A flag tool does this already; prefer it (`0x:ci-cd-release` owns flag mechanics). Check
  that it keeps assignment stable when the rollout percentage changes and across the
  anonymous-to-identified transition, or a user sees both variants at login.
- **Log exposure at the moment the unit actually encounters the difference**, not at
  assignment or page load. Including users who never reached the changed screen dilutes the
  effect toward zero. Analyze only exposed units, and trigger exposure identically in both
  arms.
- Evaluate the flag on the server for anything visible at first paint. Client-side evaluation
  after render causes flicker, which changes behavior and loses users unevenly between arms.
- Do not change the split mid-test in a way that reassigns users, and do not restart with the
  same key after fixing a bug: use a new key so earlier exposure does not contaminate.

**Sample-ratio mismatch (SRM)** is the check to run before reading any result. If the observed
split differs from the designed one by more than chance allows, assignment or logging is
broken and the result is invalid, whichever arm it favors.

```text
chi² = Σ (observed − expected)² / expected        over the arms
two arms: SRM if chi² > 10.83   (p < 0.001, 1 degree of freedom)
example: designed 50/50, observed 50,000 vs 51,000 → chi² = 9.9, borderline;
         observed 50,000 vs 51,500 → chi² = 22.2, SRM: do not read the result
```

Usual causes: exposure logged in one arm's code path only; one variant crashes, redirects or
loads slower so its event is lost; bots hitting one variant; a filter applied after assignment
that correlates with the variant; caching that serves one variant's HTML to everyone. Find
the cause and rerun. Do not "correct" the data.

## Traps when reading results

| Trap | What happens | Defense |
|---|---|---|
| Peeking | checking a fixed-horizon test daily and stopping at the first p < 0.05 raises the false-positive rate to several times the nominal 5% | fixed horizon, or a sequential method by design |
| Multiple metrics | with 20 metrics at 5%, one "significant" result is expected by chance | one primary metric; correct the rest (Bonferroni: α ÷ number of comparisons) or treat as exploratory |
| Multiple variants | each extra arm is another chance of a false win and needs its own sample | A/B, not A/B/C/D, unless traffic is abundant |
| Segment mining | "it won for mobile users in Germany" found after the fact | segments declared in advance; a post-hoc segment is a hypothesis for the next test |
| Novelty and primacy | a new thing draws clicks that fade; a change to a habit depresses use that recovers | run 2+ weeks; plot the effect by days since first exposure; compare new users separately from existing ones |
| Winner's curse | the measured lift of a winner overstates the true lift, most in underpowered tests | expect less after shipping; confirm with a holdout when it matters |
| Ratio metrics | revenue per session randomized by user: sessions are not independent | analyze at the randomization unit |
| Outliers | one large customer decides a revenue metric | cap (winsorize) or use conversion; inspect the top units |
| Interference | users in different arms affect each other (teams, marketplaces, shared inventory) | randomize by account or cluster |
| "No significant difference" read as "no effect" | an underpowered test cannot tell | report the confidence interval; flat within a narrow interval is a finding, flat within a wide one is nothing |
| Twyman's law | a result that looks too good is usually a bug | check SRM, instrumentation and one arm's raw events before celebrating |

Report every result as an effect size with an interval ("+4% relative, 95% interval −1% to
+9%"), not as "significant" or "not". The interval is what the decision needs.

## Randomization unit

| Unit | Use when | Cost |
|---|---|---|
| User | default for logged-in consumer features and individual experience | cross-device consistency needs a stable user ID |
| Account (workspace, company) | B2B, anything collaborative or visible to teammates, and every pricing or packaging test | far fewer units, so much less power; often makes the test infeasible |
| Anonymous visitor (device) | marketing pages and signup flow before login | one person on two devices can see both arms; cookie loss reassigns |
| Session or request | stateless ranking or search changes where inconsistency is invisible | never for anything the user would notice changing; cannot measure retention |

Rules: the unit of analysis equals the unit of randomization. Randomizing by account and
counting users as independent observations overstates significance, because users in one
account behave alike. Choose the unit by where interference stops: if two units can see or
affect each other's experience, they belong to one cluster. Never show different prices to
members of the same account, and check the legal and trust implications of any price test with
`0x:pricing-monetization` before running it.

## Holdouts for long-term effects

An A/B test of two weeks measures a short-term proxy. A holdout measures what happens over
months: a small random group (commonly 5–10%) is kept from a feature, from all features shipped
in a quarter, or from a lifecycle program, and compared later on retention and revenue.

| Holdout | Answers | Notes |
|---|---|---|
| Feature holdout | did the shipped winner keep its effect; did it change retention | keep 5–10% on the old experience for 1–3 months after launch |
| Global holdout | cumulative effect of everything shipped in a period | Scale only; needs large traffic and discipline to exclude the group from every launch |
| Program holdout | incremental effect of emails, notifications, onboarding sequences | cheapest and most valuable for a small team: withhold the campaign from a random 10% |

Rules: decide duration and the metric before starting; a holdout with no end date becomes a
permanently worse product for those users. Do not hold out security fixes, bug fixes, or
anything customers pay for and were promised; in B2B, holding a paid feature back from an
account is usually unacceptable. Holdout power follows the same formula, and the small arm
dominates: a 5% holdout of a small base detects only large effects. Skip global holdouts until
Scale; use program holdouts for lifecycle email from Launch.

## Brief and decision record

One page per experiment, kept in the repository or a shared document, written before launch
and completed after. The record is the asset: without it the same idea is retested in a year.

```markdown
# EXP-014 Sample data in empty project            Owner: <name>   Status: decided
## Before
Hypothesis: Because 46% of signups never create a first report, pre-loading sample data for
new accounts will raise 7-day activation by >= 20% relative.
Evidence: funnel 2026-10; 12 replays; 4 interviews.
Unit: account. Population: new self-serve signups. Exposure: first project page view.
Primary: activation within 7 days. MDE: 20% relative. Baseline: 31%.
Sample: 900 accounts per arm (~5 weeks at current signups). Split 50/50.
Guardrails: week-4 retention not down > 2 pts; support contacts per account not up > 15%.
Stopping: fixed horizon; early stop only on guardrail breach or bug.
Decision rule: ship if primary interval excludes 0 and guardrails hold; if flat, do not ship.
## After
Dates, units per arm, SRM check (chi², pass/fail).
Result: primary effect with interval; each guardrail; secondaries marked exploratory.
Decision: ship / do not ship / iterate, and why.
Learning: what this changes about the model of the user. Follow-ups.
```

Rules: write the decision rule before data exists, so the result cannot choose its own
interpretation. Record losers and flat results with the same care as winners; they are the
majority and prevent repeats. Keep an index of experiments with one-line outcomes. Remove the
losing code path and the flag when the decision is made.

## Ask the user

- **How many users reach this step per week, and what is the current conversion rate?**
  Determines whether any test is possible. Default: read both from the analytics tool; if
  unknown, assume the test is not feasible until measured.
- **What is the smallest improvement that would change what gets built?** Sets the minimum
  detectable effect. Default: 20% relative for early-stage products.
- **What must not get worse?** Becomes the guardrails. Default: retention of the exposed
  cohort, refunds or cancellations, error rate, support contacts.
- **Can different customers see different experiences or prices?** Contract terms, enterprise
  customers and trust may forbid it. Default: no price experiments on existing customers;
  account-level randomization for B2B.
- **How long can the decision wait?** A test longer than the patience available will be
  stopped early and misread. Default: cap at 4 weeks; otherwise ship and compare cohorts.
