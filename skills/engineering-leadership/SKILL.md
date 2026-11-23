---
name: engineering-leadership
description: "Makes the technical calls a CTO makes: whole-stack choice, build versus buy and vendor evaluation, ADRs and design docs, estimates, plans and scope cuts, technical debt, self-hosted offers, due diligence, and hiring and onboarding engineers or contractors. Use when choosing a stack, weighing a vendor, writing an ADR, asking how long something takes, ranking tech debt or making a first engineering hire."
---

# Engineering leadership and technical strategy

## Stance

An experienced CTO at a small company spends almost no time on most technical decisions and a
lot of time on a few. The job is to keep everything that does not differentiate boring, to
protect the handful of choices that cannot be undone, to make delivery predictable by keeping
work small, and to translate technical concerns into money, time, customers and risk that the
business can trade off.

- **Reversibility sets the pace.** Two-way doors are decided in minutes with the default;
  one-way doors (data model and IDs, tenancy, user identity, payment provider, public
  contracts, data region) get a spike and a decision record. The cost of a decision is mostly
  the cost of undoing it.
- **Boring by default, novelty on a budget.** About three innovation tokens, spent only where
  the product differentiates. Every unusual technology brings undocumented failure modes and a
  thin hiring pool, and at a small company the person paged is the founder.
- **Buy the commodity, build the differentiator, know the exit.** Compare yearly ownership cost
  at the volume expected in 12 to 24 months, upkeep and on-call included, and check that data
  can leave before it goes in.
- **Write decisions where the code lives.** A log line for most choices, one page for one-way
  doors. The future self, the coding agent, the first hire and the due diligence reviewer all
  ask "why?", and only a written record answers.
- **Small slices, ranges, throughput.** Work ships in increments of two days or less, dates are
  ranges with stated confidence, and forecasts come from items finished per week.
- **Scope is the lever; quality is the floor.** When a date slips, cut scope early. Never cut
  authorization, data integrity, billing correctness, tests on critical paths or rollback.
- **Debt is borrowed on purpose and repaid by interest.** Each shortcut has an observable
  repayment trigger; debt in cold code costs nothing, debt in hot code or in safety is urgent.
- **The company owns everything.** Repositories, accounts and IP assignments from day one,
  because contractor-held accounts and missing assignments are common due diligence red flags
  and hard to fix later. Employment and IP law differ by country: name the jurisdiction and
  send contracts to a local lawyer.

Follow the project first: existing stack, decision records and norms win over the defaults
below, which are for new decisions and for "what should I choose?".

## Route

| If the task is … | Read |
|---|---|
| "What stack should I start on?", setting technical direction, splitting time between features, reliability and debt, explaining a technical risk to an investor or co-founder, planning for growth, preparing for technical due diligence, a customer asking to run the product in their own cloud or on-premises | `references/technical-strategy.md` |
| "Should we build this or buy a service?", evaluating or comparing vendors, self-hosting open source versus a managed service, running a spike to choose, startup credits and contract renewals, leaving a vendor that is shutting down or raising prices | `references/build-vs-buy.md` |
| Writing an ADR or design doc, keeping a decision log, reviewing a design for risks, revisiting an old decision, settling who decides what | `references/decision-records.md` |
| "How long will this take?", breaking a feature into increments, planning a multi-week project, re-forecasting a slipping date, what to cut, negotiating a deadline, measuring delivery speed, coordinating with other teams | `references/estimation-planning.md` |
| "We have too much tech debt", deciding which shortcuts are acceptable, building a debt register, justifying a refactor or migration in business terms, removing an unused feature or system, code that keeps getting harder to change | `references/technical-debt.md` |
| First engineering hire, interviewing engineers, vetting a contractor or agency, onboarding a new engineer, writing engineering norms, hiring specialists, a first engineering manager or a career ladder | `references/hiring-engineers.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Stack | TypeScript strict, Next.js App Router, managed PostgreSQL with Drizzle, Stripe, a PaaS, GitHub Actions, Vitest and Playwright | A concrete constraint names the row that changes |
| New technology | No; about three innovation tokens in total | It differentiates the product and passes the adoption test in `technical-strategy.md` |
| Build or buy | Buy commodities, build the core domain | Managed bill exceeds a meaningful share of an engineer and someone can run it; residency or air-gap needs |
| Vendor contract | Monthly | Proven for a quarter → annual with a renewal price cap and export rights |
| Decision records | Log line per non-obvious choice; ADR per one-way door; design doc for work over two weeks | |
| Estimates | Ranges with a 50 and a 90 percent date; slices of two days or less | |
| Project plan | Production walking skeleton and riskiest unknown in week one, weekly demo, 20-25% buffer | |
| Slipping | Cut scope at one-third of elapsed time | Date is soft and nothing external depends on it → move the date |
| Time split | Prototype about 90% features; Launch about 70 / 15-20 / 10-15 (features / reliability / debt); Scale about 50-60 / 20 / 20-25 | Incidents, error budget burn or a security issue override |
| Debt | Deliberate, marked in code, register of about 20 items, monthly review | |
| Self-hosted offer | No; a dedicated stack in your own cloud first | A deal pays several times the yearly upkeep |
| First hire | Senior full-stack generalist | Product core is a specialty |
| Contractors | Paid one-to-two-week trial; company owns repos, accounts and IP; assignment and classification checked under the law of the contractor's country | Continuous core work → an employee, through a local entity or an employer of record |
| Delivery measures | None at Prototype; four keys monthly from Launch; team level only | |

By stage:

- **Prototype**: default stack, decision log, thin slices, deliberate debt with triggers,
  contractors only for bounded work, nothing measured formally.
- **Launch**: ADRs for one-way doors, design docs for large work, debt register and reserved
  debt time, vendor register with renewal dates, delivery measures monthly, IP assignments and
  account ownership verified.
- **Scale**: design reviews with pre-mortems, written decision rights, dependency coordination,
  specialists, a first manager and a career ladder, due diligence folder kept current.

## Before you call it done

1. Every one-way door in the work has an ADR with real alternatives, negative consequences and
   observable revisit triggers.
2. Any technology outside the default stack has a recorded reason, passes the adoption test and
   names its exit.
3. Build-versus-buy comparisons use yearly cost at the volume expected in 12 to 24 months,
   including upkeep and on-call, and state the exit path.
4. Each vendor on the critical path has a confirmed full data export, a price computed at ten
   times current usage, and its notice deadline in the vendor register.
5. Every spike had a written decision rule before it started, and its code was not merged.
6. Estimates are ranges with a 50 and a 90 percent date; no item over five days is unsplit.
7. A multi-week plan puts a production walking skeleton and the riskiest unknown in week one,
   and every long-lead item is started on day one.
8. A slip response cuts scope and leaves the quality floor intact: authorization, data
   integrity, billing, critical-path tests, rollback.
9. Each shortcut is marked in code and in the register with an observable repayment trigger.
10. A refactor or migration proposal states today's cost, the investment range, payback,
    shippable increments and abort criteria.
11. A retired feature's code, jobs, flags, infrastructure, vendor subscriptions, keys and data
    (per retention rules) are gone, not only its UI.
12. The company owns every repository and account, and every founder, employee and contractor
    has a signed IP assignment valid where they work (a "work made for hire" clause alone is
    not one), plus a confirmatory assignment for work done before signing.
13. A new engineer can merge and deploy a trivial change on day one by following the README.
14. A risk explained to a stakeholder states likelihood, business impact, options with their
    costs including doing nothing, and a recommendation.
15. Any advice on contractors, offers, equity, on-call terms or probation names the country
    (and US state) whose law applies and says which step needs a local employment lawyer.

## Not this skill

- Choosing a backend runtime or designing a system's modules and services →
  `0x:backend-architecture`
- Choosing the hosting platform → `0x:cloud-infrastructure`
- General hiring, compensation, org structure, managing people and firing →
  `0x:company-building`
- What the product should do and feature prioritization → `0x:product-discovery`
- Carrying out a refactor or rewrite in the code → `0x:code-quality`
- Vendor privacy review, DPAs and subprocessor lists → `0x:privacy-compliance`
