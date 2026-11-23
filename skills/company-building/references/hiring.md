# Hiring

Read this when: deciding whether to hire and whom first, writing a job description or scorecard,
sourcing candidates, designing an interview process, checking references or suspecting a fake
remote candidate, hiring in another country, setting pay, making an offer, or hiring a first marketer.

Engineering-specific loops (technical exercises, engineering levels, engineer onboarding) →
`0x:engineering-leadership`. This file is the role-independent process and the legal and pay frame
around it. Employment law varies by country and US state; have offer and contract templates
reviewed once per jurisdiction.

## Whether to hire, and whom first

Hire to remove the constraint on this quarter's objective, not to fill an org chart.

1. List where the founder's hours went over the last two weeks and what slipped.
2. Name the bottleneck: the one function whose capacity limits the objective (shipping, sales
   conversations, support load, operations).
3. Try cheaper fixes first: stop the work, automate it, outsource it, or bring in a part-time
   contractor for a few weeks. If a contractor clears the bottleneck, keep the contractor.
4. Hire when the work is recurring, core, judgment-heavy and fills at least half a role for the
   foreseeable future.

| Bottleneck | Typical first hire | Not yet |
|---|---|---|
| The founder cannot ship the core product fast enough | Senior generalist engineer | Engineering manager |
| Support and operations consume the founder's week | Support or operations generalist | Head of customer success |
| Founder-led sales works and demand exceeds the founder's calendar | Seller who has sold to this exact buyer | VP of Sales |
| Demand is the problem and no channel works yet | No hire; the founder tests channels, perhaps with a specialist contractor | Head of Marketing |

- Hire people who do the work themselves until there is a team to manage. An executive hired before
  a playbook exists has nothing to scale, and that hire often ends within a year.
- Budget the fully loaded cost: salary plus employer taxes, benefits, equipment, software and
  recruiting fees. As a rule of thumb, US loaded cost runs well above base salary; in much of Europe
  employer social contributions alone add a large share. Check the runway effect first →
  `0x:startup-finance`.
- The founder must know what good looks like in the function before hiring for it →
  `founder-effectiveness.md`.

## Scorecard, then job description

Write the scorecard first. It defines success, so it drives sourcing, interview questions, the
offer conversation and the 90-day review.

```text
Role: Support and operations lead
Mission: Customers get fast, correct answers; the founder spends under 3 hours a week on support.
Outcomes (measurable, dated):
  1. First response within 4 business hours for 95% of tickets by day 60.
  2. Help center covers the 30 most common ticket reasons by day 90; tickets per account falling.
  3. Owns billing operations (refunds, failed payments, invoices); month-end checks done by day 5.
Competencies (each tied to an outcome): clear writing, ownership, calm with angry customers,
  basic SQL to answer own questions, builds process without bureaucracy.
```

The job description is the scorecard rewritten for the candidate:

- Lead with the mission and the outcomes ("In your first 90 days you will..."), then the company,
  then requirements.
- List only real requirements. Long lists of years and tools make strong candidates rule themselves
  out and add nothing to selection.
- Publish the pay range. Several US states and cities require it in job posts. The EU pay
  transparency directive requires the starting pay or its range before the interview and bans
  asking about pay history; its transposition deadline was 7 June 2026 and most member states were
  late, so check the national law in force.
- State location, time-zone overlap, process steps and timeline.
- Cut "rockstar", "ninja", "work hard, play hard", "we are a family", and age-coded phrases such as
  "digital native" or "recent graduate".

## Sourcing

| Channel | Signal and volume | Use for |
|---|---|---|
| Referrals from founders' and team's networks | Highest signal, low volume | The first few hires |
| Communities of the craft (open-source projects, forums, chat groups, meetups) | High signal | Specialists |
| Direct outreach to people doing the job at relevant companies | Medium; needs volume | Every role, once the network runs dry |
| Job boards | High volume, low signal, attracts fraud | After the process is structured |
| Contingency recruiters | Fee is a share of first-year pay | Senior roles, or when founder time is the constraint |

- Ask the network "Who is the best support lead you have worked with?" A specific question yields
  names; "Do you know anyone looking?" yields nothing.
- Outreach: a personal reason for writing, the mission and one outcome, the pay range, and a small
  ask (a 20-minute call). Follow up twice over two weeks. Expect dozens of contacts per hire and
  track them in a pipeline sheet or applicant tracking system.
- A pipeline drawn only from the founder's network mirrors the founder. Add channels deliberately.

## Structured interviews

Selection research consistently finds that structured interviews and work samples predict job
performance better than unstructured conversations. Structure means the same questions, the same
rating scale and independent scoring.

| Step | Time | Purpose | Who |
|---|---|---|---|
| Screen | 30 min | Motivation, logistics, pay range, right to work | Founder |
| Work sample | 2 to 4 h; paid if it runs longer than a couple of hours | A real task from the job, scored against a written rubric | Candidate; two reviewers |
| Structured deep dive | 60 to 90 min | Career walkthrough with outcomes; behavioral questions per competency | Founder plus one |
| Team conversation | 45 min | Working style, values, the candidate's questions | Future peer |
| References | 2 to 4 calls | Verify outcomes and patterns | Founder |

- Keep first contact to offer within about three weeks; strong candidates are gone after that.
- Each interviewer covers assigned competencies, rates on a 1 to 4 scale (no neutral midpoint) and
  writes evidence before talking to anyone. The debrief starts from written scores, which prevents
  anchoring on the most senior voice.
- Behavioral questions ("Tell me about the last time you...") with follow-ups: what exactly did you
  do, what happened, what would you change. Hypotheticals invite rehearsed answers.
- The same work sample for every candidate, taken from real work but never unpaid client work.
- Hire only on a clear yes. A "maybe" is a no. A well-evidenced no on a must-have competency blocks.
- Ask only job-related questions: nothing about age, family plans, pregnancy, religion, health or
  national origin; in the US ask whether the candidate is authorized to work, not about citizenship.
  Protected characteristics vary by jurisdiction.
- Recording or AI summarization needs the candidate's consent in many places. Automated screening
  and scoring tools are regulated: New York City requires bias audits; Illinois requires notice and
  consent before AI analyzes video interviews; the EU AI Act already bans emotion recognition at
  work, interviews included, and makes recruitment and screening AI high-risk with obligations from
  2 December 2027 (as amended in 2026). Keep a human deciding → `0x:privacy-compliance`.

## References and identity

References:

- Ask for former managers, not friends. Do not contact the current employer without consent.
- Ask: "What were their biggest results?", "Where do they do their best and worst work?", "On a
  scale of 1 to 10, how would you rate them, and what would make it a 10?", "Would you hire them
  again, enthusiastically?"
- Faint praise, long pauses and "it depends" mean something. A former manager who would not rehire
  is a strong signal.
- US background checks through a screening company require a standalone disclosure, written
  authorization, and a pre-adverse-action notice before rejecting on the report (FCRA). Many states
  and cities delay criminal-history questions until after a conditional offer. In the EU, criminal
  record checks are lawful only where national law allows them for the role; in the UK, checks
  beyond a basic one are limited to eligible roles.

Fraudulent remote candidates are a real and growing risk: identity theft, proxy interviewers,
real-time face and voice swapping, and organized schemes, including state-backed ones US
authorities have warned about publicly, that place workers under false identities to collect
salaries and gain system access.

Signals:

- Camera refused, or video with lip-sync lag or artifacts; a different face or voice between rounds.
- Answers that lag as if read; inability to go deeper on claimed past work.
- A thin or new online footprint, unreachable former employers, a stock-looking photo.
- Locale or time-zone mismatch with the claimed location; VoIP numbers; heavy VPN use.
- Equipment to be shipped somewhere other than the ID address; pay to an account in another name or
  to crypto.
- Several applications with identical résumé text.

Controls for every remote hire with system access:

1. Camera on in every interview; include unscripted moments (screen share, a whiteboard sketch,
   a spontaneous question about their surroundings or city).
2. Verify the identity document against the live person before the offer is final, through an
   identity-verification service or a live call.
3. Call references on numbers found independently (company switchboard), not those supplied.
4. Ship equipment only to the verified address. Pay only into an account in the person's legal name.
5. First weeks: least-privilege access, no production secrets, alerts on remote-access tools and on
   logins from unexpected countries → `0x:web-security`.
6. Meet in person at least once where feasible. Work-authorization document checks (such as the US
   I-9) do not reliably catch a stolen identity.

## Contractor, employee or employer of record

Status is decided by how the work is actually done, not by the contract's label. Misclassification
brings back taxes, social contributions, benefits, penalties and employment rights.

| Signal | Points to employee | Points to contractor |
|---|---|---|
| Control | The company sets hours, methods and tools | The worker decides how; the company defines deliverables |
| Integration | Part of the team, core ongoing work, company email | Separate project, own business |
| Duration and exclusivity | Open-ended, full-time for one client | Defined end, several clients |
| Money | Paid for time, no business risk, company equipment | Invoices, own equipment, can profit or lose |
| Substitution | Must do the work personally | Can send someone else |

Jurisdiction mechanisms (check current law): the US uses a common-law control test for federal tax,
and some states are stricter (California's ABC test presumes employment unless, among other
conditions, the work is outside the usual course of the hiring company's business). The UK applies
employment-status tests plus IR35 for contractors working through their own company, where a small
client leaves the status decision to the contractor's company and medium and large clients decide
it themselves. Germany pursues false self-employment (Scheinselbständigkeit) with back-charged
social contributions and offers a formal status determination by the pension insurer. France asks
whether there is subordination (instructions, supervision, sanctions); a worker's self-employed
registration only creates a rebuttable presumption. Elsewhere, ask a local employment lawyer which
test applies and whether a formal ruling is available.

| Situation | Default |
|---|---|
| Defined project of weeks to months; worker has other clients | Contractor agreement with IP assignment |
| Full-time and ongoing, in a country where the company has an entity | Employee through a payroll provider |
| Full-time and ongoing, in a country without an entity | Employer of record (EOR): a provider employs the person locally for a monthly fee on top of pay |
| Several people in one country, or EOR fees exceed entity costs | Own local entity with local payroll |

EOR traps: the EOR is the legal employer, so confirm its contract assigns IP to the company and
includes confidentiality, or sign a direct agreement. Termination still follows local law and
notice. A salesperson abroad who negotiates and signs contracts can create a taxable presence for
the company there; take tax advice. A long-running "contractor" paid through a platform is still a
misclassification risk; the platform moves paperwork, not liability.

## Compensation bands

- Use at least two data sources: startup salary-benchmarking tools (several draw on payroll or
  cap-table data), posted ranges in job ads, government statistics, and offers seen in the
  pipeline. Self-reported data skews high.
- Choose a positioning per component and apply it to everyone, in writing: for example, cash at the
  market median for the location tier and equity above market.
- One band per level, a range around a midpoint. Hire inside the band; exceptions become visible
  and are resented.
- Location: one global band (simple, attractive, expensive) or location tiers (cheaper, more
  administration). Decide once and record it.
- Equity per level as a number of options and a percentage of fully diluted shares; pool and
  vesting mechanics → `0x:startup-finance`.
- Many US states and cities, and the EU directive, prohibit asking for salary history. Ask for
  expectations instead.
- Check pay equity across people in the same role once there are several of them.

## Offer and close

- Founder makes a verbal offer by call, then sends the written offer within a day. Give about a
  week to decide; 24 to 48-hour exploding offers damage trust before day one.
- Explain equity plainly: number of options, exercise price, vesting and cliff, the exercise window
  after leaving, percentage of fully diluted shares, that preferred investors are paid first in a
  sale, and that the equity may be worth nothing. Never quote a value based on a hoped-for exit.
- Do not promise a future title, a promotion, a team to manage, a raise at the next round, an
  acquisition or job security. Recruiting statements can become evidence of a promise; put real
  commitments in the letter and nothing else.
- Close on the candidate's own motivators, learned during the process. Offer a call with a team
  member or an investor.
- Decide the walk-away before a counteroffer arrives; a bidding war breaks the bands.
- Outside the US the offer leads to a written employment contract: EU law requires the main terms
  in writing within the first week and the rest within a month, the UK a written statement of
  particulars by day one; probation, notice and any non-compete compensation follow local law.
- Make contingencies explicit: signed PIIA (or the IP and confidentiality clauses of the contract),
  right-to-work verification, a background check if one is used. Then hand over to onboarding →
  `managing-people.md`.
- After a decline, ask why and keep in touch; strong candidates often return.

## The first marketing lead

Hire after at least one acquisition channel works with founder effort, so the hire scales a channel
rather than searching for demand. Before that, test channels in person or with a specialist
contractor (`0x:growth-marketing`).

- Profile: a hands-on generalist who has personally grown a channel, with numbers, at a company of
  similar stage and price point. Marketers used to agencies, large budgets and a brand team often
  struggle without them.
- Work sample: share real data and ask for a 30-day plan for one channel, with expected numbers and
  the first experiments.
- Agree on a definition of a qualified signup or lead with whoever sells before day one; otherwise
  marketing optimizes for cheap volume.

| Metric | Ownership |
|---|---|
| Qualified signups or pipeline created, by channel | Owned |
| Cost per qualified signup or customer, against budget | Owned |
| Experiments run and documented per month | Owned |
| Signup-to-activation conversion | Shared with product |
| Revenue closed | Shared with sales or the founder |

Review at 90 days against the channel's leading indicators, not revenue alone; revenue lags.

## Ask the user

- What is blocking this quarter's objective, and what was tried before hiring? It decides whether
  to hire at all; default to a contractor trial for a few weeks.
- What fully loaded monthly cost can the company carry, and for how long? A hire that shortens
  runway into danger is the wrong hire; default to keeping at least a year of runway after it.
- Where may the person live, and does the company have an entity there? Default: employee in the
  home country, employer of record elsewhere.
- What is the pay philosophy: market cash, or less cash and more equity; one global band or
  location tiers? Default: median cash for the hire's location tier.
- Should full identity verification apply to remote candidates? Default: yes, for any role with
  access to systems, customer data or money.
