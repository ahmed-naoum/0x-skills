# Hiring and onboarding engineers

Read this when: considering the first engineering hire, choosing between an employee, a
contractor and an agency, designing an engineering interview, vetting a contractor, onboarding
an engineer, writing engineering norms, or deciding when to add specialists or a first
engineering manager. General hiring process, compensation, employment law and managing people
belong to `0x:company-building`; equity plans to `0x:startup-finance`.

Employment and IP law are national, and in the US partly state law. Every legal rule below
names where it applies; anything not named is practice, not law. Before the first contract in
a new country, a local employment lawyer reviews the template and the classification.

## When to make the first engineering hire

Hire when all of these hold:

- Engineering capacity, not demand or product clarity, limits revenue: there is a backlog of
  validated work that customers pay for or are waiting on.
- The work is continuous for months. A bounded project is a contractor's job.
- The money covers the fully loaded cost for a long stretch (rule of thumb: 12 to 18 months)
  beyond what the current runway already needs. Employer payroll taxes, social contributions,
  mandatory benefits and notice costs vary widely by country; get the loaded figure from a
  local accountant or an employer-of-record quote, not from the salary alone.
- The founder can give about a quarter of their time for the first months: context, reviews,
  answering questions. A hire without that support stalls.

Before product-market fit, prefer contractors for bounded work over employees building
speculative features.

| Situation | First hire |
|---|---|
| Technical founder, product needs breadth | Senior full-stack generalist who has shipped a product in a small company |
| Non-technical founder | A technical co-founder or a senior founding engineer with meaningful equity (plan mechanics differ by country, see below); meanwhile a fractional CTO plus a vetted contractor |
| Product core is a specialty (ML, mobile, data infrastructure) | That specialist, provided they are product-minded |
| Founder buried in support and operations | Possibly not an engineer: a support or operations hire frees more engineering time |

Avoid as a first hire: a junior engineer (needs mentoring nobody has time to give), a narrow
specialist who cannot work across the stack, and anyone whose first plan is a rewrite. With
coding agents, a first engineer's leverage is judgment: specifying work, reviewing generated
code and proving it correct. Test for exactly that.

Equity for early engineers is country-specific. A four-year vest with a one-year cliff is the
common US convention. US stock options need a strike price at fair market value, usually set by
an independent (409A) valuation, or the holder faces tax penalties; UK startups commonly use
tax-advantaged EMI options, which only employees can hold; German startups have often used
virtual share plans. Promise nothing in writing until the plan exists, set up by a lawyer in the
company's country (`0x:startup-finance`).

## Interviewing with a work sample from your own product

Move fast: strong candidates are usually in several processes at once. Decide within 48 hours of the final
step.

1. **Screen, 30 minutes.** What they built, the hardest production problem they owned, why this
   company; your pay range, their location and start date in the first five minutes, not the
   last. State the range instead of asking for current or past pay: many US states and cities
   ban pay-history questions and several require a range in the job posting, and the EU Pay
   Transparency Directive (national laws due June 2026, many late) requires giving applicants
   the range before the interview and bans pay-history questions. Apply the candidate's
   location.
2. **Work sample, 2 to 4 hours.** A real, sanitized task from the product: a trimmed copy of the
   repo with seeded data, a small feature to add and an existing bug near it. Pay for take-home
   work over about two hours, or run it live.
3. **Review conversation, 60 minutes.** The candidate walks through the submission; change one
   requirement and extend it together; discuss what they would do with another day.
4. **Design discussion, 45 to 60 minutes,** on the product's real architecture and constraints
   ("we need per-workspace rate limits; how?"), not a famous-company design exercise.
5. **References.** At least two former managers or close peers, with the candidate's consent.
   Ask what the person needed to do their best work and whether they would hire them again.
   Background checks are regulated: in the US, a check through a third party needs written
   disclosure and authorization (FCRA) and many states and cities limit criminal-history
   questions; in the EU and UK, checks are personal-data processing under the GDPR and are
   narrowly limited.

Write the rubric before the first candidate, ask every candidate the same things, and have each
interviewer score independently before any discussion, so the loudest opinion does not set the
outcome.

| Dimension | Strong signal | Weak signal |
|---|---|---|
| Correctness and testing | Tests the critical case, handles errors and empty states | Happy path only |
| Reading existing code | Follows the codebase's conventions | Rewrites what was there |
| Judgment | Names the trade-off, asks the one clarifying question that matters | Over-builds, or misses the obvious risk |
| Verifying generated code | Runs it, tests it, can explain every line | Pastes output, cannot explain it |
| Communication | A clear written description of what changed and why | Needs prompting to explain |
| Product sense | Asks who the user is and what they are trying to do | Treats the task as a puzzle |

State the AI tool policy in advance. Default: allow the tools the job uses, and score how the
candidate verifies and explains the result. Avoid algorithm puzzles unrelated to the work,
unpaid multi-day assignments and unstructured "culture fit" conversations, which mostly measure
similarity to the interviewer.

## Contractors and agencies: paid trial, company owns everything

| Option | Good for | Watch for |
|---|---|---|
| Freelance contractor | Bounded work with a clear spec; a specialist skill | Availability; knowledge living in one head |
| Agency | A team for a project when nobody can manage individuals | Seniors sell, juniors build; proprietary frameworks; hosting on their accounts |
| Fractional CTO or advisor | Non-technical founders: architecture, hiring, vendor review | Conflict of interest if the same firm sells the build hours |

Start with a paid trial of one to two weeks on a real, non-critical task, under the same rules
as the team: a pull request into the company's repository, CI green, tests, a written
description. Judge quality, communication, estimate against actual, and how ambiguity is
handled. Only then sign a larger engagement.

Set up ownership before the first line of code:

- **Contract**: a present assignment ("hereby assigns") of all work product to the company, a
  license to any pre-existing code the contractor brings, confidentiality, and a confirmatory
  assignment covering anything written before signature. National law decides what is valid:
  - **US**: copyright in a contractor's code stays with the contractor unless assigned in
    writing; "work made for hire" covers contractors only in nine statutory categories that
    software rarely fits, so the assignment clause is what transfers it. In California, a
    signed work-made-for-hire clause can make an individual contractor a statutory employee
    for workers' compensation and unemployment insurance (Labor Code 3351.5(c)), so use an
    assignment without that wording there.
  - **UK**: a contractor owns the copyright unless they sign a written assignment; an
    employee's work made in the course of employment belongs to the employer.
  - **Germany and Austria**: copyright itself cannot be transferred and moral rights cannot be
    fully waived; the contract grants exclusive, unlimited, transferable rights of use instead.
    **France**: economic rights can be assigned, but each right must be listed with its scope,
    territory and duration. Across the EU, the employer exercises the economic rights in
    software employees write in their duties; contractors keep theirs unless granted.
  Have a lawyer in the contractor's country review the template once.
- **Restrictive covenants**: do not rely on a non-compete. California voids them for employees
  even when signed elsewhere, other US states restrict them, and the FTC's 2024 nationwide ban
  was vacated and abandoned in 2025, so state law governs. In Germany, a post-employment
  non-compete binds an employee only if the employer pays at least half the last pay for its
  duration (two years at most). Rely on confidentiality and IP assignment, plus
  non-solicitation where local law allows it.
- **Repositories** in the company's GitHub organization from day one; the contractor is a
  member or outside collaborator, never an owner.
- **Accounts** (cloud, domain registrar, app stores, payments, email provider) owned by the
  company under company email addresses; contractors get least-privilege access through their
  own named logins; no shared passwords; secrets only in the company's secret store.
- **Deploys** go through the pipeline, never from a contractor's laptop.
- **Licenses**: third-party code declared; no copyleft dependency added without approval
  (`0x:privacy-compliance`).
- **Deliverables** include a README, runbook and decision records, not just code.
- **Payment** against merged and deployed milestones; hourly work capped per period.
- **Offboarding**: remove from the GitHub organization, cloud IAM and vendor dashboards, and
  rotate every secret they could read.

Agency red flags: insisting on their own repository or hosting, "we hand over the code at the
end", no tests, and a team roster that changes after signature.

### Contractor or employee: the law decides, not the contract

Classification follows how the work is done. Signs that make a contractor an employee in most
countries: set hours, a place on the on-call rotation, day-to-day direction from the founder,
company equipment, a single client, and an open-ended engagement on core product work. Getting
it wrong means back taxes, social contributions, penalties and employee rights owed
retroactively.

| Where | Test | Trap for a software company |
|---|---|---|
| US federal | IRS common-law control test for tax; Department of Labor economic-reality test for wage law, under revision since 2026, so check the current rule | A full-time "contractor" managed like staff |
| California | ABC test: free from control, work outside the usual course of the hiring business, an independently established business | An individual engineer building a software company's product usually fails the second prong |
| UK | IR35 off-payroll rules: medium and large clients decide status themselves; for small clients the contractor's own company decides | A deemed employee treated as outside IR35 |
| Germany | False self-employment (Scheinselbständigkeit), judged by integration and direction | Years of back social-security contributions; a status determination by the Deutsche Rentenversicherung settles it in advance |

For continuous core work by someone in a country where the company has no entity, use an
employer-of-record service or an entity rather than a long-term contractor agreement; a person
working like an employee abroad can also create a taxable presence there. Contractors fit
Prototype and bounded projects; at Launch, review every long-running contractor and convert
those who have become staff in all but name. Employees also sign an invention and IP
assignment at hire: California and several other US states void claims to inventions made on
the employee's own time without company resources and unrelated to the business, and require
the agreement to say so; in Germany, an employer that takes an employee's invention owes
statutory compensation.

## Onboarding to a first production deploy within a week

Prepare before day one:

- One-command local setup with seeded data, tested on a clean machine within the last month.
- A README with a one-page architecture overview, how to run tests, how deploys work, and where
  logs and errors are.
- An access checklist granted before day one: GitHub, hosting, error tracker, analytics, docs,
  chat, password manager. No production database write access in the first week.
- Three starter tasks in different areas: a trivial change, a small bug, a small feature.

| When | Outcome |
|---|---|
| Day 1 | Accounts work, app runs locally, a trivial change merged and deployed through the normal pipeline |
| Days 2-3 | A small real bug fixed and deployed; architecture walkthrough; read the decision log and debt register |
| Days 4-5 | A small feature in production behind a flag, reviewed together |
| Weeks 2-4 | Owns a feature end to end, including a design note and rollout |
| Days 30, 60, 90 | Check-ins; shadowing on-call by day 60 and joining the rotation by day 90, where one exists |

The new hire fixes every setup friction they hit in the README or scripts during week one;
fresh eyes are the only time that friction is visible. Track time to first merged pull request
and first deploy for each hire; if it grows, the setup is decaying.

Set the probation period in the employment contract before day one, because its length and
effect are national law. Most US states employ at will (Montana is the main exception), so
probation there is a practice, not a legal status. Germany allows a probation of up to six
months with two weeks' notice, after which dismissal protection applies in businesses with more
than ten employees. In the UK, the qualifying period for unfair-dismissal claims falls from two
years to six months for dismissals from 1 January 2027. Review the hire well before probation
ends; performance management and dismissal are `0x:company-building`.

## Engineering norms

Write one short document (`CONTRIBUTING.md` or `docs/engineering.md`) when the second engineer
arrives, before habits form. Enforce what can be enforced with tools: branch protection,
required checks, CODEOWNERS.

| Norm | Default for a small team |
|---|---|
| Code review | Every change through a pull request with one approval; small pull requests (rule of thumb: a few hundred changed lines at most); review within one working day; the author merges and deploys |
| Testing bar | Tests for auth, billing, data mutations and anything that broke before; CI green to merge; a skipped flaky test needs an issue and an owner |
| Definition of done | In production, behind a flag if incomplete, observable (errors tracked, key event recorded), docs updated |
| On-call | The founder until there are two or three engineers; then a weekly rotation with a backup, paging only for user-facing impact, time off after a night page |
| Documentation | Decision log and ADRs, design docs for work over two weeks, a runbook for every alert |
| Coding agents | Allowed; the author owns every line; agent pull requests reviewed like any other; no secrets or production personal data in prompts |
| Access | Least privilege; production data access logged and reviewed |

On-call pay and rest are employment law, set in each contract: in the EU, standby that heavily
restricts free time can count as working time and the daily rest of 11 consecutive hours
applies; in the US, non-exempt employees must be paid for on-call time that restricts them,
while salaried exempt engineers usually are not paid extra. Keep contractors off the rotation,
since it is a sign of employment.

Details live elsewhere: pull-request practice in `0x:git-collaboration`, test strategy in
`0x:code-quality`, on-call in `0x:site-reliability`, agent rules in `0x:ai-coding-agents`.

## When to hire specialists

Default: generalists, managed services and fractional specialists, until one specialty is a
steady, substantial load. A specialist hired early either sits idle or builds infrastructure for
problems the company does not have.

| Specialist | Hire when | Until then |
|---|---|---|
| Platform, DevOps or SRE | Infrastructure and CI consume most of one engineer's time; self-run Kubernetes or multi-region | A PaaS, managed services, product engineers owning their deploys |
| QA | Rarely as a gate; consider for regulated domains, hardware, many client platforms, or heavy exploratory testing | Engineers own automated tests; end-to-end tests on critical flows |
| Data | Decisions wait on data that engineers spend days each month extracting; several sources need a warehouse | Product analytics tool; SQL on a read replica |
| Security | Security questionnaires and audits arrive with most deals; regulated data; after a serious incident | Fractional security lead, compliance automation, secure defaults |
| AI or ML | Core value depends on model quality beyond prompting and retrieval: fine-tuning, own models, evaluation at scale | Product engineers using the Anthropic API with evaluations (`0x:ai-features`) |
| Mobile | A native app is a core channel, not a wrapper | PWA or cross-platform work by web engineers |

## A first engineering manager and a career ladder

The moment comes when the founder-CTO has roughly five to eight direct reports and one-to-ones,
hiring and coordination crowd out technical decisions, or the team splits in two. Before that,
the founder decides whether to stay technical (architecture, hiring, strategy) and hire a
manager, or to manage and hand technical direction to a senior engineer.

- **Promote** an engineer who wants the role and already mentors, hires and unblocks others.
  Frame it as a trial of about six months with an honorable path back to individual work at the
  same level; management is a different job, not a reward. Write the path back into the
  promotion letter: in many countries, changing a role or pay later needs the employee's
  consent.
- **Hire externally** when the team will double within a year, nobody internal wants it, or
  scaling experience is missing. Check that a candidate from a large company has managed in
  small, under-resourced settings.

Create a career ladder at roughly five to eight engineers or at the first promotion or raise
question; earlier it is bureaucracy. Make it dual-track: from senior level, the individual and
management tracks run in parallel with equal pay potential, so good engineers are not pushed
into management to progress.

| Level | Scope |
|---|---|
| Engineer | Delivers well-defined work with guidance |
| Senior engineer | Owns features end to end, unblocks themselves, reviews others |
| Staff engineer | Sets technical direction across the team; multiplies others |
| Principal engineer | Shapes company-wide technical strategy; rare before Scale |
| Engineering manager | Team outcomes, hiring and growth of people; parallel to senior and staff |

Describe each level on four dimensions (scope and impact, technical skill, collaboration,
ownership and judgment) with observable examples, not years of experience, on one page.
In the EU, the Pay Transparency Directive requires employers to give staff the criteria for pay
and pay progression (member states may spare employers under 50 people the progression part);
a ladder with observable criteria is the base for meeting it. Compensation bands and the review process are `0x:company-building`.

## Ask the user

- **What budget exists for engineering capacity, and for how long?** It decides employee,
  contractor or agency. Default: contractor on a paid trial until revenue covers a hire for
  more than a year.
- **Employee or contractor, and in which country (and US state) does the person work?** That
  law decides classification, IP transfer, notice and on-call pay. Default: a contractor only
  for bounded work; continuous core work through an employee via a local entity or an employer
  of record; a local employment lawyer reviews the template first.
- **Will early engineers get equity, and is there a plan?** Grants made without a plan and a
  valuation create tax problems for the holder. Default: promise nothing in writing until a
  lawyer in the company's country has set up the plan (`0x:startup-finance`).
- **How much time overlap and which language must the team share?** Default: at least four
  working hours of overlap with the founder.
- **Who owns the company's accounts and repositories today?** If a contractor or agency holds
  them, transfer them before anything else. Default: assume transfer is needed and check.
- **Does the founder want to keep building or to manage?** It decides whether the first senior
  hire is a manager or a technical lead. Default: the founder stays technical until about five
  engineers.
