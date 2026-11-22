---
name: product-analytics
description: "Instruments a product and decides what to measure: event tracking plans, analytics tool setup, activation and funnels, cohort retention, north-star metrics and scorecards, A/B test design, and attribution. Use when the user asks what events to track, how to set up PostHog, where users drop off, whether retention is good, whether traffic allows an A/B test, or which channel signups come from."
---

# Product analytics and experimentation

## Stance

Analytics exists to change decisions. A solo founder needs a small number of trusted numbers,
each with one definition, tied to the questions that decide what gets built next. Most
analytics failures are not statistical: they are events that silently broke, two definitions
of the same word, per-user numbers for a per-account business, and conclusions drawn from
samples too small to carry them. Work from the question backward to the event, and say plainly
when the data cannot answer.

- **Questions first, events second.** Write the decisions the data must inform, then track
  what they need. Tracking everything produces a dataset nobody trusts or queries.
- **Facts are emitted by the server.** Signup, activation, payment and cancellation are
  recorded where they become true, after commit. Client events are lost to blockers and closed
  tabs, and can be forged; they are for behavior only the browser sees.
- **One definition per metric, written down.** Unit, window, filters and source of truth are
  fixed in a metric dictionary in the repository. Money comes from billing, entity counts from
  the database, behavior from analytics.
- **The unit is the customer.** For B2B that is the account, in events, funnels, retention and
  experiment randomization. Per-user analysis of an account-based product answers a different
  question.
- **Retention before acquisition.** A retention curve that does not flatten means no lasting
  value yet; more signups only fill a leaking bucket. Activation is defined by what predicts
  retention, not by what onboarding happens to end with.
- **Cohorts, not totals.** Rates are computed on cohorts whose observation window has closed.
  Totals and blended averages hide mix shift and make recent periods look worse than they are.
- **Small numbers get counts and names, not percentages.** Below roughly 100 units per group,
  read the list of customers and talk to them; a percentage there is noise presented as fact.
- **A correlation is a hypothesis.** "Users who do X retain better" is explained by intent or
  segment at least as often as by X. Only an experiment, or a dated cohort comparison when
  traffic is too low for one, tests it.
- **Most early products cannot A/B test.** Compute the detectable effect before designing
  anything. An underpowered test produces confident noise; larger bets, cohort comparisons and
  watching users are the honest alternatives.

## Route

| If the task is | Read |
|---|---|
| Deciding what to track and how to name it, picking or setting up PostHog or another tool, wiring `identify` and accounts, moving events server-side, respecting consent in instrumentation, testing that tracking works, changing the plan safely | `references/event-tracking.md` |
| Defining the activation event, finding where users drop between signup and paying, segmenting a funnel, measuring time to first value, studying feature adoption, judging whether a finding is causal | `references/funnels-activation.md` |
| Defining "active", building retention curves, answering "is retention good", churn and net revenue retention by cohort, retention by channel or plan, engagement depth, explaining stalled growth | `references/retention-cohorts.md` |
| Choosing the north-star metric, building a metric tree to revenue, fixing "everyone reports a different number", setting guardrails, specifying the weekly scorecard, running a metrics review | `references/north-star-metrics.md` |
| Asking whether there is enough traffic to test, designing an A/B test, reading a result, checking assignment and sample-ratio mismatch, choosing the randomization unit, holdouts, writing the experiment record | `references/experiments.md` |
| Finding which channels produce signups and revenue, UTM conventions, a "how did you hear about us" question, sending conversions to ad platforms, a large "direct" bucket, AI-referral traffic, testing whether a channel is incremental | `references/attribution.md` |

## Defaults at a glance

Follow what the project already uses; these apply to greenfield choices.

| Decision | Prototype | Launch | Scale |
|---|---|---|---|
| Tool | One product suite (PostHog-style), or nothing but the database and conversations | Same suite: funnels, retention, flags, experiments | Suite plus warehouse export for cross-system and finance-grade numbers |
| Custom events | 5–10 | 15–30, in a tracking plan in the repository | Governed plan with owners; unused events removed |
| Event names | `object_action`, snake_case, past tense | Enforced by a typed wrapper | Schema review on change |
| Fact events | Server-side from the start | Reconciled daily against the database | Outbox table and job |
| Identity | Database user ID; `identify` on login, `reset` on logout | Plus account group on every event (B2B) | Same |
| Consent | No tracking storage before opt-in where required | Consent flag honored client and server | Same, audited |
| Activation | A reasoned hypothesis | Validated against week-4 retention; one server event | Reviewed twice a year |
| Retention | Who came back, by name | Weekly cohorts on the core action; churn list with reasons | Segmented curves, NRR and GRR by cohort |
| Scorecard | None | 5–9 numbers, weekly, automated | Per-team inputs under one north star |
| Experiments | None; talk to users | Only where the detectable lift is plausible within 4 weeks; program holdouts for email | Sequential engine, guardrails, feature holdouts |
| Attribution | Ask each signup | First and last touch stored at signup, plus a self-report question | Server-side conversion upload, incrementality tests |

Other defaults:

- Time zone UTC, ISO weeks, incomplete periods masked.
- Funnel unit and randomization unit: account for B2B, user for consumer.
- Funnel window: trial length plus 7 days.
- Planning formula for a conversion test: about 16 ÷ (relative lift)² conversions per arm.
- Internal and test accounts excluded by property in every official insight.
- Separate analytics projects for development, staging and production.

## Before you call it done

1. Every new event is in the tracking plan with an exact trigger, source, properties and the
   question it answers, and follows the naming convention.
2. Signup, activation and billing events are emitted server-side after commit, once per
   occurrence, including when the webhook is replayed.
3. Daily counts of a fact event match the database within the agreed tolerance, and an alert
   exists for the count falling to zero.
4. `identify` uses the database ID, is guarded against empty or placeholder values, and
   `reset` runs on logout; B2B events carry the account group.
5. No emails, names, free text or tokenized URLs appear in event properties; replay masks
   inputs; the SDK stores nothing before consent where consent is required.
6. All analytics calls go through the typed wrapper, and a test asserts the critical funnel
   events fire once with valid payloads.
7. Each metric shown has an entry in the metric dictionary stating unit, window, filters and
   source of truth, and the chart states them too.
8. Rates are computed on closed cohorts; the current incomplete period is masked or labeled.
9. Any segment or cohort being compared has enough units to mean something, or is reported as
   counts.
10. Causal language is used only for experiment results; other findings are stated as
    associations with the next test named.
11. An experiment has a written brief with one primary metric, a sample size, guardrails, and
    a stopping and decision rule fixed before launch; the sample-ratio check passed before the
    result was read; the result is reported as an effect with an interval and recorded.
12. First-touch source is stored on the user or account row at signup, UTM values follow the
    written convention, and channel reports go through to activation and revenue.
13. Conversions sent to ad platforms respect the user's advertising consent and are
    deduplicated against the pixel.
14. Internal, test and impersonation traffic is excluded from every reported number.

## Not this skill

- Running the analysis: SQL queries, statistics and dashboards from data → `data`
- Chart design and visualization choices → `dataviz`
- Cookie consent and the legal limits on tracking → `0x:privacy-compliance`
- Warehouse loading, pipelines and data modeling → `0x:data-stores`
- Feature-flag rollout mechanics → `0x:ci-cd-release`
- MRR, burn, runway and financial reporting → `0x:startup-finance`
