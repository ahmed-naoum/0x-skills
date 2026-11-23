# Prospecting, outreach and pipeline

Read this when: building a prospect list, asking for introductions, writing cold email or a
follow-up sequence, setting up a CRM and its stages, or deciding when and how to hand sales to a
hired rep.

## Order of work by stage

| Stage | Where the next customers come from | What to build, and nothing more |
|---|---|---|
| Prototype | Founder's network, design partners, people complaining in public about the problem | A spreadsheet of names and a forwardable blurb; nothing automated |
| Launch | Warm introductions first, then targeted cold outreach to one narrow segment | A CRM with enforced stages, a separate sending domain, one sequence per segment |
| Scale | Repeatable outbound plus inbound, worked by hired reps | Written playbook, quota and commission plan, weekly pipeline review, call recordings |

The founder closes the first customers personally. Those calls are where the ideal customer
profile (ICP), the pitch, the price and the objections are discovered; no hire can learn them on
the founder's behalf, and a process nobody has run cannot be handed over.

## Qualified prospect list from the ICP

An ICP is usable only when it is narrow enough to produce a list by query.

| Element | Usable definition (shape, not a recommendation) | Unusable |
|---|---|---|
| Segment | B2B software companies, 20 to 200 staff, selling to mid-market | "Tech companies" |
| Buyer | Head of Support who owns the help-desk budget | "Decision makers" |
| Observable pain signal | Hiring support agents, public status page with frequent incidents, uses tool X | "Wants efficiency" |
| Trigger (why now) | New executive in the role, just raised, current tool being retired, audit date | None recorded |
| Disqualifiers | Under 10 staff, on-premises only, a sector the product cannot legally serve | None recorded |

1. Start from the three to five best customers or design partners (at Prototype, the people with
   the sharpest pain in interviews). Write down what they share and what made them act when they did.
2. Turn each attribute into a filter: firmographics in a B2B contact database (LinkedIn Sales
   Navigator, Apollo or similar), technographics from tech-stack detection, hiring signals from job
   posts, public signals from changelogs, communities, GitHub and competitors' review pages.
3. Build 50 to 150 accounts per segment, not thousands. Tier them: **A** (fit plus a live trigger:
   individual research), **B** (fit, no trigger: segment-level message), **C** (park).
4. Give every A account a "reason to contact now" column. An empty cell means the email will be generic.
5. Pick one to three people per account: the person who feels the pain and the person who owns the
   budget. Verify every address with a verification service before the first send.
6. Record each contact's source. GDPR and UK GDPR require telling a named contact where their data
   came from, at the latest in the first message; the column also shows which channel produces
   customers.

When outbound fails, check list fit before rewriting copy: the right message to the wrong list
gets nothing, and a plain message to a list with a live trigger gets replies.

## Warm introductions first

A warm introduction converts to a meeting far more often than a cold email. Exhaust them before
buying data.

- Sources: former colleagues and employers, investors and their portfolio companies, advisors,
  communities where the ICP gathers, people who engaged with the founder's writing, and existing
  customers. End every good customer call with "who else do you know who has this problem?"
- Use double opt-in: the connector asks the target first. Hand the connector a forwardable note of
  three to five sentences: who you are, the problem you solve and for whom, one proof point, and a
  small ask (20 minutes to compare notes). It must work forwarded without edits.
- Tell the connector the outcome and thank them; that is what earns the second introduction.
- At Prototype, ask for a problem conversation, not a sale (interview method → `0x:product-discovery`).
  Start charging as soon as there is something to pay for: a design partner who pays behaves like
  a customer, one who does not behaves like an advisor.

## CRM: every deal with stage, next step and close date

Move from a spreadsheet to a CRM at about ten open deals or a second person selling. Use a
lightweight hosted CRM (HubSpot's free tier, Pipedrive, Attio or similar) that the founder opens
daily. Do not build one.

Stages are defined by what the buyer has done, so that two people put the same deal in the same stage:

| Stage | Exit criterion (verifiable) |
|---|---|
| Prospect | On a list, not contacted |
| Contacted | In a sequence or introduced |
| Meeting booked | Calendar invite accepted |
| Qualified | Discovery done: pain, impact, signer, process and timeline known (`discovery-demos.md`) |
| Evaluation | Tailored demo given or pilot running against written success criteria |
| Proposal | Proposal walked through live with the economic buyer present |
| Contracting | Verbal yes; security, legal or procurement under way |
| Closed won / lost | Signed, or dead with a loss reason from a fixed list |

Required on every open deal: annual contract value, stage, next step with a date, expected close
date, champion and economic buyer, source, competitor (including "do nothing").

- No open deal without a dated next step. A passed next-step date is fixed today or the deal closes.
- The close date is when the buyer's process lets them sign, not the date hoped for. Log each
  push; two pushes without new information mark a deal at risk.
- Write call notes into the CRM within the hour. At hand-over to a rep, the notes are all that exists.
- Close deals with no buyer activity for 30 to 60 days as "no decision"; reopen when they wake.
  An inflated pipeline is worse than a thin one because it hides the need to prospect.
- Probability-weighted forecasts mean something only once exit criteria are enforced. Before that,
  forecast deal by deal.

## Cold outreach that earns replies

| Part | Rule | Reason |
|---|---|---|
| Subject | Two to five plain words about them; no fake "Re:" or "Fwd:" | Deceptive subjects raise complaints and are illegal under US CAN-SPAM |
| First line | The trigger observed at their company, not a compliment or a line about you | Proves it is not mass mail |
| Problem | One hypothesis of the pain, in their vocabulary | Relevance earns the reply, not features |
| Proof | One concrete result from a similar customer, or one credible reason you can solve it | Replaces adjectives |
| Ask | An interest question ("Worth comparing notes?"), not a fixed 30-minute slot | A small yes is easier than a calendar commitment |
| Form | Under about 100 words, plain text, no images or attachments, no links in the first touch | Links, images and tracking reduce inbox placement |
| Footer | Name, company, postal address, a plain opt-out line; for EU and UK contacts, a link to a privacy notice that names the data source | Required in several jurisdictions; lowers complaint rates |

```text
Subject: support hiring at Acme

Hi Dana, I saw Acme is hiring its third support agent this quarter.

At that size the same few questions usually fill half the queue.
[Similar customer] cut first-response time from [X] to [Y] by answering those in the product.

Worth comparing notes?

Sam, founder, Example Inc., [postal address]
Not relevant? Reply "no" and I will not write again.
```

Personalize on the trigger and the problem, not on trivia (school, hobbies); trivia reads as a
template. Measure positive replies and meetings per 100 prospects per segment, never opens. Rule
of thumb: no positive reply after 100 to 200 sends to one segment means the segment or the problem
hypothesis is wrong, and more volume will not fix it.

### Deliverability for cold email

Mechanics of authentication and reputation → `0x:email-notifications`. Cold-specific rules:

- **Never send cold email from the primary domain** that carries product, billing and password-reset
  mail. Use a separate related domain (for example try-example.com) with its own mailboxes, so a
  reputation hit cannot block transactional mail.
- SPF, DKIM and DMARC aligned on that domain, a real website or redirect on it, and mailboxes that
  receive and are read. Never send from a no-reply address.
- Warm new mailboxes for a few weeks before real volume. Keep each mailbox to tens of messages a
  day (rule of thumb); add mailboxes rather than volume per mailbox.
- Keep spam complaints well below the mailbox providers' ceilings (Google's sender guidelines ask
  for under 0.1% as measured in Postmaster Tools and treat 0.3% or more as non-compliant; check the
  current guidelines); keep bounces under about 2% (rule of thumb) by verifying.
- Turn off open and click tracking. Tracking pixels and rewritten links hurt placement, and privacy
  proxies (Apple Mail Privacy Protection) make open rates meaningless.
- Law differs by recipient country; this is a summary to check, not advice. The US (CAN-SPAM)
  allows B2B cold email with honest headers and subject, a postal address and an opt-out honored
  within 10 business days. The UK (PECR) allows it to corporate subscribers such as companies and
  LLPs with an opt-out, but sole traders and most partnerships count as individuals and need
  consent. Germany requires prior express consent for email advertising even to businesses; some
  other EU states are similarly strict while others (France, for one) allow B2B email relevant to
  the recipient's role. Canada (CASL) requires consent; implied consent covers narrow cases such as
  an address conspicuously published for the role with no notice refusing solicitations. GDPR and
  UK GDPR also govern the list itself (a lawful basis, usually legitimate interests with a written
  assessment). Check before each new country → `0x:privacy-compliance`.

## Follow-up sequence without becoming spam

| Day | Touch | Content |
|---|---|---|
| 1 | Email | The first email above |
| 3 | LinkedIn connection request | No pitch in the note |
| 6 | Email, same thread | One new thing: a relevant resource, a sharper question, a different angle |
| 11 | Email to a second contact, or a call | Coordinated with the first; mention the colleague only if natural |
| 18 | Closing email, same thread | "I will stop here; if X becomes a priority, reply anytime." |

- Three to five touches over two to three weeks. Each adds information; "just bumping this" adds none.
- Automated stop rules: any reply (a "not now" becomes a dated recontact task, never a continued
  sequence), bounce, opt-out, meeting booked, open deal or existing customer at the account.
  Out-of-office replies pause the sequence until the return date.
- One suppression list shared across every mailbox, tool and the CRM. An opt-out applies to the
  whole company and does not expire.
- At most two people per account in sequence at once, with coordinated messages; never the same
  email to five people at one company.
- Recontact a "not now" at exactly the time they named. It is now a warm lead.
- Calls carry their own rules: in the UK screen numbers against the Corporate Telephone Preference
  Service; in Germany a B2B cold call needs at least presumed interest; in the US, no autodialed or
  prerecorded calls or texts to mobiles without consent. Check before adding a call step.

## First salesperson: only after founder-led sales repeats

Hire when all of these hold:

- The founder has closed roughly 10 to 20 customers in one segment (rule of thumb) through steps
  that are written down.
- Win rate from Qualified, average deal size, sales-cycle length, top objections and their
  answers are known from the CRM rather than estimated.
- Qualified demand exceeds what the founder can work, or an outbound motion produces meetings
  predictably.
- Deal size and margin can pay for a rep: their annual quota must be several times their cost.

Hire someone who has sold at an early company without brand, inbound leads or a support team, not
a big-company rep whose success came from those. Common advice is to hire two at once so a miss
can be attributed to the rep or to the process; a solo founder with one hire uses their own
numbers as the comparison. Expect a new account executive to take a quarter or two to reach full
productivity and budget cash for it. The founder keeps joining late-stage calls and runs the
weekly pipeline review. The classic failure is hiring a rep to "figure out sales": the rep fails
and the founder wrongly concludes the market is bad.

## Playbook a hired rep can repeat

Write it from recorded calls and the CRM, not from memory, and revise it monthly. The test: after
a week of reading and shadowing, a new rep runs a discovery call the founder would rate as good.

- ICP, tiers and disqualifiers; the triggers that make an account worth contacting now
- Personas: what each role cares about, their words for the pain, the proof that moves them
- Outreach templates and sequences per segment, with their measured reply rates
- Discovery questions, qualification criteria and stage exit criteria (`discovery-demos.md`)
- Demo script per persona, demo-environment reset steps, the three moments that land
- Objections with the answers that worked, competitor notes, "we build it ourselves" answer
- Pricing, discount authority and what to trade for it (`0x:pricing-monetization` owns policy)
- Security, legal and procurement steps with links to the packs (`procurement-security.md`)
- Five recorded calls that won and two that lost, with notes on why

## Quota, commission and weekly pipeline review

Rules of thumb for SaaS, to adjust with an advisor who has built comp plans in the segment:

| Item | Common practice |
|---|---|
| On-target earnings split | Account executive about 50/50 base and variable; SDR nearer 70/30 |
| Annual quota | About four to five times the rep's on-target earnings; below about three, the role does not pay for itself |
| Commission rate | Variable pay divided by quota, on first-year contract value |
| When paid | On cash collected (safest for a small company) or on signature with clawback if unpaid or canceled early |
| Over quota | Accelerated rate above 100%; no caps, which make reps delay deals |
| New rep | Ramped quota for the first months |

Write the plan down and have it signed, defining what counts as a booking, when commission is
paid, and what happens on non-payment, churn or a discount. Pay on net contract value so the plan
never rewards discounting. Undefined terms are where commission disputes come from.

Weekly pipeline review, 30 to 45 minutes, deal by deal: new deals, stage moves, passed next steps,
close-date pushes, deals older than the median time in their stage, and the commit list for the
period. Ask "what has the buyer done since last week?", not "how do you feel about it?". Hold open
qualified pipeline at about three times the period's target (rule of thumb).

## Ask the user

- **Which segment goes first?** One narrow ICP is the most important decision here. Default: the
  segment of the best current customers or design partners.
- **Whose networks can be asked for introductions?** Investors, former employers and customers
  differ in reach. Default: list 30 names before any cold email.
- **Which countries are prospects in?** Cold-email legality differs. Default: US and UK only until
  checked.
- **Budget for data, sending domain and CRM?** Default: free CRM tier, one data tool, one separate
  domain with two mailboxes.
- **Will the founder sell, and for how long?** Default: founder sells until the hiring gate is met.
- **Commission budget and payment basis?** Default: paid on cash collected, with a written plan.
