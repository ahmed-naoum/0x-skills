---
name: product-discovery
description: "Decides what to build and why: customer interviews, problem and demand validation, MVP scoping, specs and PRDs, prioritization, roadmaps and product-market fit. Use when asking if an idea is worth building, planning or synthesizing customer interviews, cutting an MVP, writing a spec, prioritizing a backlog or feature requests, planning a quarter, or deciding whether to pivot."
---

# Product discovery and management

## Stance

An experienced product founder assumes the idea is wrong in some important way and treats the
work as finding out which way, as cheaply as possible, before code makes it expensive. They trust
what customers did over what customers say they will do, decide in advance which result would
change their mind, and treat every feature as a permanent cost that must earn its place.

- **Past behavior is evidence; opinions about the future are not.** Ask about the last time,
  current spend and workarounds. Compliments and "I would use that" predict nothing.
- **Commitment is the only proof of demand.** Money, time, introductions and data access, ranked
  by what they cost the customer. An email signup costs nothing and proves little.
- **Narrow first.** One ICP that can be named 100 times over, one job, one happy path. Broad
  targets average the evidence into mush and produce products nobody loves.
- **Write the threshold before the test.** Without a pass line and a kill line set in advance,
  every result reads as encouraging.
- **Test the riskiest assumption the cheapest way.** Often that is not code: a concierge service,
  a pre-sale, a spike on real data.
- **Problems, not requests.** Log the underlying problem with account counts and revenue; a
  requested solution is a hypothesis.
- **"Not now" is the default answer.** Each feature carries support, testing and complexity
  forever, and must win against the one current goal metric.
- **Every claim links to evidence; every request links to its requester.** So insights can be
  checked, decisions revisited, and loops closed when things ship.
- **Fit is measured, per segment.** A flattening retention curve, 40% "very disappointed", organic
  pull; never sign-ups or praise.

Follow the project first: if the founder already has a research log, a spec format, a backlog
tool or a roadmap, work within it. The defaults below are for new decisions.

## Route

| If the task is … | Read |
|---|---|
| Finding people to talk to, writing an interview guide, "what should I ask?", turning interview notes into what to build, writing a survey, keeping research going after launch, a research repository | `references/customer-interviews.md` |
| "Is this idea worth building?", choosing between ideas, defining the ICP, mapping competitors and alternatives, landing-page or fake-door tests, pre-orders, LOIs, design partners, market size | `references/problem-validation.md` |
| "Scope the MVP", "what can I cut?", what to fake or do by hand, how long the first version should take, when it is good enough to charge, where polish matters | `references/mvp-scoping.md` |
| Writing a spec or PRD, user stories and acceptance criteria, edge cases and error behavior, defining success for a feature, reviewing a spec, a press release and FAQ for a big bet | `references/specs.md` |
| Prioritizing a backlog, answering or refusing a feature request, planning a quarter, a public roadmap, judging a shipped feature, removing a feature, delegating a product area, a first PM hire | `references/prioritization-roadmaps.md` |
| Onboarding first users, in-app feedback, tagging support for product input, churn reasons, win/loss, a beta program, telling users a request shipped, "do we have product-market fit?" | `references/feedback-loops.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Research method | Problem interviews about past behavior, 5–8 per segment | Options known and counts needed → survey; "can they use it?" → usability test |
| Who interviews | The founder, weekly | Scale: everyone making product decisions keeps the habit |
| Proof of demand | Pre-order or LOI signed by a budget holder | Low-price consumer product → paid sign-ups or deposits |
| Demand test | Outreach, concierge and pre-sale | Existing product with users → fake door behind a flag |
| Validation decision | Threshold, time box and kill line written before the test | Never skipped |
| ICP | One segment with 100 nameable prospects | Expand once retention flattens there |
| MVP | One user, one job, one happy path, first real user in 2–6 weeks | Riskiest assumption is feasibility → spike on real data first |
| Manual versus build | Manual or bought until it costs about a day a week | Customers are waiting on the manual step |
| Charging | From the first customer, founding discount with an end date | Design partners → at the end of the partnership |
| Spec | One page with non-goals, a measured baseline and listed events | Under a day → issue with criteria; multi-week bet → press release and FAQ first |
| Prioritization | Impact × confidence ÷ effort against one goal metric, top 20 only | Very different reach per item → add reach (RICE) |
| Capacity | About half core job, a quarter bets, a quarter maintenance; plan to 70% | Incidents rising → more maintenance; churn → more core |
| Feature requests | "Not now", logged with requester and underlying problem | Passes all four request tests |
| Roadmap | Private at Prototype; now, next, later at Launch, no dates past Now | |
| Feedback store | Helpdesk tags plus one table of problem records | Scale → a dedicated feedback tool |
| Fit judgment | Retention floor, 40% survey with about 40 qualified answers, organic pull | |

By stage:

- **Prototype**: interviews, the 100-name ICP list, scored ideas, a demand test with a written
  threshold, pre-sales, a concierge or narrow MVP. Skip quarterly planning, public roadmaps,
  research tools and relationship surveys.
- **Launch**: weekly customer conversations, hand onboarding of the first fifty users, one-page
  specs with measured baselines, the request log with requesters, churn reasons, quarterly
  planning against one metric, a now, next, later roadmap, the fit survey.
- **Scale**: a research repository with linked evidence, win/loss at volume, beta programs per
  major feature, formal deprecations, delegated areas with outcome targets, a first PM.

## Before you call it done

1. The problem statement names a findable who, a frequency, a cost with units, and the current
   workaround.
2. The ICP is backed by a list of at least 100 named prospects with a contact route for each.
3. Every interview has a card (job, trigger, current solution, spend, pain rung, quotes) written
   the same day.
4. The ranked problem table shows unprompted counts as "n of N" per segment, linked to interview
   IDs; segments are not merged.
5. Every demand test had its threshold, time box and kill line written before it started, and the
   resulting decision is recorded.
6. Willingness to pay rests on money or a budget holder's signature, not on stated intent.
7. The MVP is a numbered happy path that tests the riskiest assumption; every other feature is
   marked build, fake, manual, buy or cut.
8. The cheap-now items are present: account model, maintained auth, a restored backup, analytics
   on the happy path, account deletion.
9. The spec has non-goals, a baseline measured before building, a target with a read date, the
   events to add, and an edge-case table covering empty, limits, concurrency, permissions and
   failure.
10. Every acceptance criterion can be judged pass or fail by someone who has not talked to the
    founder.
11. Backlog scores are against the one current goal metric, with confidence set from evidence.
12. Every feature request is logged with requester, account, revenue and underlying problem, and
    every refused requester got a reason and an alternative.
13. A public roadmap has no dates beyond Now and states items as problems or outcomes.
14. Each shipped feature has a read date and a recorded keep, iterate or kill decision, and its
    requesters were told it shipped.
15. At least one customer conversation happened this week.

## Not this skill

- Event tracking, funnels, retention analysis and A/B tests → `0x:product-analytics`
- Wireframes, flows, usability tests and interface copy → `0x:ui-ux-design`
- Positioning, launch and acquisition channels → `0x:growth-marketing`
- Price points, plans and packaging → `0x:pricing-monetization`
- Engineering estimates, technical planning and build-versus-buy → `0x:engineering-leadership`
- Briefing a coding agent to implement the spec → `0x:ai-coding-agents`
