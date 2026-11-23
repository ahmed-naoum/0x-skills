# Operating cadence, process and culture

Read this when: setting the weekly, monthly and quarterly rhythm; asking what happens to the
company if the founder is hit by a bus; moving to async work and written decisions; buried in
back-office tasks; writing values or norms; building a handbook; or there are too many meetings.

## The operating rhythm

A rhythm is a fixed set of recurring artifacts, each with an owner and an output. The habit
matters more than the tool.

| Cadence | Artifact | Time box | Produces | From |
|---|---|---|---|---|
| Daily | Async check-in, only if blockers otherwise go unseen | 5 minutes to write | Unblocking | Launch, with a team |
| Weekly | Metrics snapshot and written update: shipped, numbers against goals, next week's top three, blocked or needs decision | 1 h solo; 30-45 min team meeting for decisions | Priorities and decisions | Prototype |
| Monthly | Business review: revenue, cash and runway, funnel, retention, support load, hiring; investor update | 2 h | Course corrections | Launch |
| Quarterly | Reread the strategy page, grade and set goals, retrospective on how the company works, subscription and access review, continuity drill | Half to full day | Next quarter's goals and process changes | Prototype |
| Annually | Strategy and budget, compensation review, compliance calendar reset, insurance renewal | 1-2 days | Plan and budget | Launch |

Solo version: a one-hour Friday review (metrics, customer conversations, what shipped, next week's
three priorities); the first Monday of the month for money and metrics; one day a quarter away
from the code for strategy and goals.

- Report the same metrics, in the same order, every week. Changing what is reported hides trends.
- The written update exists before the meeting; the meeting covers only exceptions and decisions.
- A skipped weekly review is the first sign of drift. A shorter review beats a skipped one.
- Plan at less than full capacity: support, maintenance and incidents arrive every week.
- Investor updates → `0x:startup-finance`; metric definitions → `0x:product-analytics`.

## A deputy if the founder is unreachable

The test: if the founder vanished tonight for two weeks (illness, accident, lost phone, travel
without access, death), would the product keep running, would customers and staff be paid and
billed, and could someone legally act for the company? Three layers must exist.

**1. Legal authority.**

- A second person able to act: a second director, or an officer given authority by board
  resolution. A sole-director company has no one with authority; that is the main gap to close.
  Alternatives: a limited power of attorney for defined acts, or a local alternate-director mechanism.
- Bank: a second authorized user or signatory, with limits.
- US single-member LLC: name a successor or designee in the operating agreement. Without one, state
  default rules on a sole member's death can leave no one authorized and, in some states, dissolve
  the company.
- The founder's shares pass under a will or estate plan, and probate can take months. The founder's
  personal estate plan covers the shares and points to the continuity runbook.
- Key-person insurance when co-founders or investors depend on one person.

**2. Account authority.** Every critical account has a second owner or a tested break-glass path.

| Account | Why it is critical | Minimum |
|---|---|---|
| Domain registrar and DNS | An expired or lost domain stops everything | Auto-renew, second admin, registrar lock |
| Email domain admin | Password resets for every other account flow through it | Second super-admin |
| Cloud organization or root | Production | Second admin; break-glass credentials with hardware MFA in sealed storage |
| Code hosting organization | Code and deploy pipelines | Second owner |
| Payment provider | Revenue and payouts | Second admin; the ownership-transfer process known |
| Bank, payroll, accounting | Paying people and bills | Second user |
| App store developer accounts | Mobile releases | Transfer of the account-holder role is slow; know the process |
| Password manager | Holds everything else | Emergency access or recovery configured for the deputy |
| Support desk, social accounts | Talking to customers | Second admin |

- Use the password manager's emergency-access feature with a waiting period, so the founder can deny
  a request when merely away.
- Register a backup hardware security key on every critical account; store it with the deputy or in
  a safe.
- Bills that keep the company alive (cloud, domain, email, payroll provider) on automatic payment,
  with a backup card the deputy can update.

**3. The runbook**, an "if I am unreachable" page in the restricted part of the handbook:

- who the deputy is, what they may do, and what they must not (no new contracts, no shutdowns);
- whom to call: co-founder, lawyer, accountant, key investors, family contact;
- how to keep the service up: status page, alerts, rollback, which vendors must be paid
  (operational runbooks → `0x:site-reliability`);
- message templates for customers and staff; where the formation documents, cap table, contracts,
  insurance policies and vault live.

Test it: the deputy uses the break-glass path into each critical account with the founder present,
yearly at Launch and quarterly at Scale. Fix every failure found. An untested plan does not exist.
Log break-glass use and bind the deputy by confidentiality terms, since the access reaches customer
data. Admin-account hardening → `0x:web-security`.

## Async-first, written decisions

Write by default. Meet when writing is failing.

| Write | Meet |
|---|---|
| Status, plans, proposals | Conflict or strong disagreement |
| Decisions with their context | Sensitive feedback or personal matters |
| Anything someone will need later | A thread past about three rounds without converging |
| Questions that can wait a few hours | High-ambiguity brainstorming, kickoffs, relationship building |

A decision record, kept in one searchable log:

```text
Decision: Support replies drafted by the help desk's AI, sent only after human approval.
Owner: Sam    Date: 2026-11-23    Reversible: yes; revisit in February
Context: three lines on the problem and the constraint.
Options: A, B, C, each with a one-line trade-off.
Decision and reason: ...
Dissent: Alex preferred B because ...; committed.
```

- One owner decides after consulting; everyone commits; reopen only with new information.
- Reversible decisions are made fast and low in the organization. Irreversible ones get more writing,
  more consultation and the founder's sign-off.
- Response-time norms in writing, for example: chat within the working day, email within two
  working days, a phone call for urgent matters. Define urgent: customer harm, money or security.
- Across time zones, keep a few hours of overlap and make decisions in writing so everyone can weigh
  in within a day.
- Architecture decision records and design docs → `0x:engineering-leadership`.

## Replace status meetings with documents

Status meetings move information that reading moves faster. Keep the meetings that decide,
resolve conflict or build relationships.

| Meeting | Keep | Instead |
|---|---|---|
| Daily status standup | Rarely | Async check-in; meet only on blockers |
| Weekly status round | No | Written updates, read in advance |
| Weekly team meeting | Yes, 30-45 min | Agenda: decisions and exceptions from the updates |
| Decision meeting | Yes | Pre-read, a named decider, outcome logged |
| One-on-ones | Yes | (`managing-people.md`) |
| Retrospective and planning | Yes, monthly or quarterly | |
| Incident review | Yes | `0x:site-reliability` |

- Every kept meeting has an owner, a stated outcome ("decide X"), a pre-read sent a day ahead or read
  silently in the first minutes, and the smallest group that can decide.
- Decisions reach the log within a day; actions get an owner and a date.
- Default to shorter slots (25 or 50 minutes) and protect half-day blocks with no meetings for focused
  work; makers lose a whole block to one meeting in its middle.
- Once a quarter, remove every recurring meeting from calendars and restore only those people miss.

## Values and working norms

Values help only when they settle a trade-off.

- Phrase each as a choice between two good things: "customer outcome over internal convenience",
  "ship small and often over complete and late", "written over spoken".
- Test: would a reasonable company choose the opposite? Nobody chooses against "integrity" or
  "excellence", so those guide nothing.
- Three to five values, each with a real decision it changed. Write them after watching what the
  team actually rewards; aspirational lists written on day one are ignored.
- Use them: as a competency in hiring scorecards, in feedback, and in decision records.
- The real test is the high performer who violates a value. Keeping that person tells everyone what
  the actual values are.

Working norms are concrete rules, kept in the handbook: working hours and availability; response
times; meeting-free time; how to disagree (in the thread, then to the owner, then commit); how to
raise a concern, including anonymously, and the harassment-reporting route; on-call and vacation
coverage; where documents, tasks, decisions and conversations live.

## The company handbook

One place that answers how the company works, so the founder does not have to.

| Section | Contents |
|---|---|
| Company | Strategy page, values, this quarter's goals |
| How we work | Cadence, norms, tools, decision log, meeting rules |
| Who owns what | Ownership map, org chart, deputies |
| People policies | Leave, expenses, equipment, remote work, code of conduct, harassment and grievance procedures, reviews |
| Security | Password manager, MFA, devices, data handling, offboarding |
| Pay and benefits | Band philosophy, benefits, pay dates |
| Onboarding | The onboarding page |
| Continuity | The deputy runbook, access-restricted |

- When a question has a handbook answer, answer with a link. When it does not, write the answer into
  the handbook first, then link.
- Every page has an owner and a last-reviewed date; review quarterly. Keep history (a wiki with
  versions, or a repository) and announce policy changes.
- Some written policies and statements are legally required, for example the UK's written statement
  of employment particulars from day one and disciplinary and grievance procedures; US states
  require specific notices. Have an employment lawyer review the people policies. In the US, state
  that the handbook is not a contract; elsewhere some policies can become contractual terms.
- GitLab's public handbook is the best-known handbook-first example: borrow the structure, not the size.

## Staying small by automating the back office

The aim is to keep revenue per person high: buy standard functions, automate rule-based work,
keep judgment with people.

1. Inventory recurring back-office tasks for a month: task, frequency, minutes, cost of an error.
2. Classify each: buy, automate, outsource, keep.
3. Start where time times frequency is highest and errors are cheap and reversible.

| Function | Buy | Automate on top |
|---|---|---|
| Bookkeeping | Accounting software with bank feeds; a monthly bookkeeper | Receipt capture and matching; categorization rules |
| Billing | Payment provider's billing, portal and dunning (`0x:payments-billing`) | Follow-ups on failed payments |
| Payroll and HR | Payroll provider, PEO or EOR; HR records | Onboarding and offboarding checklists from HR events |
| Support | Help desk with macros and a help center | AI drafts with approval; tagging and routing |
| Contracts | E-signature and templates | Contract data into the CRM |
| Sales operations | CRM | Enrichment, call notes, follow-up drafts |
| Access | SSO and a password manager | Deprovisioning triggered by offboarding |

Rules for business agents (LLM agents operating tools):

- Agents prepare; people commit. Anything that moves money, signs or commits the company, writes to
  customers in a new way, changes access or deletes data needs a human approval.
- Run new agent tasks in suggest mode first, measure the error rate on a sample, then let reversible,
  low-cost tasks run unattended.
- Each agent gets its own least-privilege credentials and an audit log, never the founder's admin
  account. Permission design → `0x:ai-coding-agents`.
- Personal data sent to an AI vendor needs its terms and data processing agreement in order →
  `0x:privacy-compliance`.
- Every automation has an owner and a failure alert. An automation that fails silently is worse than
  the manual task it replaced.
- Review subscriptions quarterly: owner, cost, last use, SSO. Cancel what nobody uses; fewer tools
  also means fewer accounts to revoke at offboarding.

## Ask the user

- Who could legally act for the company and reach the critical accounts if you were unreachable for
  two weeks? Default: name one person and set up all three layers this quarter.
- Which decisions do you keep for yourself? Default: strategy, hiring and firing, pricing, and
  spending above a set amount.
- How much meeting time does the team want, across which time zones? Default: async-first with one
  short weekly decision meeting.
- Which values have you acted on when it cost something? Default: draft them from three recent hard
  decisions.
- Which back-office task takes the most of your month? Default: automate or outsource that first.
