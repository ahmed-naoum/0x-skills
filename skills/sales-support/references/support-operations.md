# Support operations

Read this when: setting up support, choosing response targets, triaging tickets, writing help
articles or saved replies, handling refund and cancellation requests, deploying an AI support
agent, deciding which admin powers support gets, reviewing ticket trends or quality, or hiring the
first support person.

## Shared inbox and response targets

Route support@ and the in-app contact form into a help desk (Help Scout, Zendesk, Intercom, Front,
Plain or similar), never a personal mailbox. Needed from Launch: assignment, statuses, saved
replies, internal notes, history per customer, and a sidebar with account data (plan, revenue,
account age, open invoices, recent errors for this user, link to the admin tool).

- Channels: email and an in-app form first. Add live chat only when someone staffs it during
  stated hours; an unanswered chat is worse than an email promise. Phone for high-value plans
  only. A community forum once there are enough users to answer each other.
- The contact form collects what triage needs: account (from the session), category, and for bugs
  what they did, expected and saw, plus a screenshot. Suggest matching articles as they type.

Starting targets, to adapt; publish only what can be met every week:

| Priority | Examples | First response | Updates |
|---|---|---|---|
| Urgent | Product down, data loss, security issue, wrong charges across accounts | 1 business hour; outside hours through on-call (`0x:site-reliability`) | For product-wide incidents, the status-page cadence of the incident's severity (every 30 minutes for SEV1, `0x:site-reliability`), with the status page linked in replies; otherwise every few hours until resolved |
| High | Core feature broken for one account, a user blocked from working | 4 business hours | Daily |
| Normal | How-to, minor bug, billing question | 1 business day | When something changes |
| Low | Feature request, feedback | 2 business days | When decided or shipped |

- Measure in business hours; state the hours and time zone publicly. Auto-acknowledge with the
  expected response time and the top articles; this alone removes "did you get my email?" tickets.
- Contractual response times belong only in enterprise contracts that pay for them
  (`proposals-contracts.md`).
- A solo founder meets a one-business-day target with two fixed support blocks a day, which
  protects engineering time; only urgent tickets page a phone.

## Triage: reproduce, classify, close the loop

1. Identify the account, plan, and how many users or accounts are affected.
2. Reproduce with the same plan, role, browser and data, using logs, the error tracker and
   read-only impersonation. If it cannot be reproduced, ask for everything missing in one message.
3. Classify:

| Class | Meaning | Route |
|---|---|---|
| Bug | The product does not do what it is meant to | Tracker issue with repro steps, linked tickets, count of affected accounts |
| Gap | It works as designed but not as they need | Request log with customer, account value and the underlying job (`0x:product-discovery`) |
| Confusion | It works; they could not tell how | Answer, then fix the article or interface copy that misled them |
| Account or billing | Access, invoices, plan changes, refunds | Policy below; mechanics `0x:payments-billing` |
| Incident | Many accounts, same symptom | Incident process; one status-page update instead of many replies |
| Security or abuse | Vulnerability report, compromised account | Security process (`0x:web-security`); never detailed in public |

4. Prioritize by impact times breadth, not by how loudly the customer writes.
5. Reply with what was found and what happens next, with a time. "We'll look into it" is not an answer.
6. Close the loop: when a linked bug is fixed or a requested feature ships, tell every linked
   customer personally. It converts an old annoyance into goodwill and is the most neglected step.

Keep a ticket "waiting on engineering", not "solved", while its bug is open; solved-but-unfixed
hides the backlog. Count confusion as a product defect with a documentation or copy fix.

## Help articles and saved replies for the top ten questions

1. Export the last one to three months of tickets and cluster them by question. The top ten
   usually cover a large share of volume; check the actual share.
2. For each cluster write one help article and one saved reply that links to it.
3. Article: title in the customer's words ("How do I add a teammate?"), the answer in the first two
   lines, steps with a screenshot only where a step is not obvious, related links, last-updated date.
4. Saved reply: first line written by hand, the answer, the link, "reply if this does not solve
   it". Never send one unedited to an upset customer.
5. Make articles searchable and suggested in the contact form and linked from the matching screen.
6. Link each article to the features it describes and put "update affected articles" in the
   release checklist. Stale articles create tickets and feed wrong answers to any AI agent.

## Refunds and cancellations by written policy

Write the policy once, publish it, and let support apply it without asking. Consumer law can
grant more than this: EU and UK consumers have a 14-day withdrawal right for online purchases
(with conditions for services already started), and EU law now requires an online withdrawal
button for it. Check each market (`0x:privacy-compliance`).

| Case | Default |
|---|---|
| Monthly plan canceled | Cancel in the product anytime; access to the end of the paid period; no partial refund |
| Unhappy after first payment | Full refund within a stated window (commonly 14 to 30 days), no questions |
| Forgotten annual renewal | Refund if asked shortly after renewal with little use since; otherwise move to monthly |
| Billing error, or outage beyond the SLA | Refund or credit proactively, without waiting to be asked |
| Duplicate charge | Refund immediately |
| B2B annual contract mid-term | Per contract, normally no refund; offer a downgrade at renewal |
| Repeated refund requests | Decline after the first; note the account |

- Authority in writing: support refunds up to one month's fee (or a set amount) alone; above it,
  the founder approves. Nobody negotiates case by case.
- Ask the reason once, offer one fitting alternative (pause, downgrade, a fix), then do what they
  asked without friction. A refused small refund often returns as a chargeback that costs more
  (mechanics → `0x:payments-billing`; save offers → `success-churn.md`).
- Cancellation works in the product without contacting anyone. Consumer laws in several places
  require online cancellation without obstruction for anyone who signed up online (California's
  automatic renewal law, Germany's cancellation button; the US FTC pursues hard-to-cancel
  subscriptions under ROSCA), and hidden cancellation drives chargebacks.
- Confirm in writing: amount refunded, when it appears, when access ends, how to export data.

## AI support agent: what it answers, when a human takes over

An AI agent answers well only what the help center already answers well; fix the top articles first.

| The agent may | A human must take over when |
|---|---|
| Answer how-to questions grounded in articles, with the link | The customer asks for a human: honor it immediately |
| Report status and known incidents | Refunds or credits outside the automatic policy, or a billing dispute |
| Read account facts after authentication (plan, usage, invoice copies) | Ownership or email changes, account recovery, MFA reset |
| Collect repro details for a bug | Security reports, data export or deletion requests, legal or privacy questions |
| Perform low-risk actions through the audited admin API, with limits enforced in code | Anger, distress, or cancellation intent on a valuable account |
| | Two answers have not resolved it, or retrieval confidence is low |

- Handover carries the transcript and collected details into the ticket; the customer never
  repeats themselves and is told when a human will reply.
- Say that it is an AI. The EU AI Act requires it from August 2026 for systems that talk with
  people, some US states have bot-disclosure laws, and customers react worse when they find out
  later.
- Limits on money and access live in code behind the same audited API humans use, never only in
  the prompt.
- Measure resolution by sampling transcripts weekly, not by "the customer stopped replying". Hunt
  for invented policies: companies have been held to what their chatbots said (in 2024 a Canadian
  tribunal made Air Canada pay after its chatbot misstated a refund policy).
- Building the agent (retrieval, guardrails, evals) → `0x:ai-features`.

## Admin actions support gets without an engineer

Build the admin tool in the order of "can an engineer run this query?" requests. Every action is
gated by role and written to an append-only audit log: actor, target, action, before and after,
reason, ticket ID, time.

| Tier | Actions | Who |
|---|---|---|
| Read | Account, users, plan, usage, invoices, recent errors and events, flag states | All support |
| Low-risk write | Resend invite or verification, extend trial within a limit, credit within a limit, unlock after lockout, reset onboarding | Support |
| Sensitive | Change account email or owner, merge accounts, restore deleted data, refund above the limit, remove MFA after identity verification | Second approver or founder, following a written identity-check procedure |
| Never in the tool | Passwords, secrets, tokens, full card data, bulk exports of customer data, deletion outside the deletion process | Nobody |

Impersonation ("view as user"):

- Read-only by default. Write access only with explicit, time-limited consent from a B2B
  customer, recorded in the product or the ticket.
- Short session, visible banner, no billing, security or credential changes, no sending messages
  as the user.
- Logged as the staff member acting for the user, never as the user; where the product shows
  customers an audit log, the entry appears there.
- Staff accounts need MFA; access is reviewed when roles change. Admin-tool hardening →
  `0x:web-security`; disclosure in the terms → `0x:privacy-compliance`.

## Tagging root causes and reviewing trends

- One required root-cause tag at close, from a fixed list of 10 to 20 in two parts: area (billing,
  onboarding, import, an integration, permissions) and class (bug, gap, confusion, account).
  Free-form tags sprawl into uselessness; prune and merge them quarterly.
- Monthly review, under an hour, founder plus whoever ships product: top five drivers by volume
  and by change; an owner and a fix for each (article, copy, design, bug); check whether last
  month's fixes shrank their tags.
- Track contacts per 100 active accounts. Raw ticket count rises with growth and hides improvement.

## Quality: CSAT, response time, sampling

| Metric | Shows | Trap |
|---|---|---|
| First response time, median and 90th percentile, business hours | Responsiveness | Auto-acknowledgments do not count |
| Resolution time with reopen rate | Effort and correctness | Closing early looks fast until reopen rate rises |
| CSAT: one question after resolution, optional comment | The customer's view per ticket | Low, polarized response; read every negative comment |
| Age of the oldest open ticket | Hidden debt | Averages hide it |

Each week, review five to ten closed tickets per agent, and the AI agent's transcripts, against a
rubric: correct, complete, tone, policy followed, tagged, loop closed. Coach on patterns, not
single tickets. The founder keeps reading a sample after delegating: support is the most direct
view of what the product really does to people.

## Hiring the first support person

Hire when the founder spends more than about a day a week on support week after week, or targets
slip, and the top questions are already documented. First check whether the top drivers can be
removed in the product instead.

Look for clear warm writing, technical curiosity (reproduces bugs, reads logs, can run a read-only
query) and calm under anger. Use a paid exercise: five real anonymized tickets, including an angry
one and an ambiguous bug. A hire in another time zone extends coverage.

Hand over a playbook: product and plans, top accounts, response targets, refund and escalation
policy, what may be promised, triage classes and bug template, tools and admin tiers, saved replies
and article ownership, known issues, escalation paths to engineering, security, billing and the
founder, and a tone guide with good and bad examples. Ramp: first week shadowing and reading;
second week drafts reviewed before sending; then the queue with daily review, moving to weekly
sampling.

## Ask the user

- **Which hours and targets can be promised?** Default: the table above, business hours in the
  founder's time zone.
- **What is the refund policy?** Default: the table above, published on the site.
- **How much may support refund without approval?** Default: one month's fee.
- **Should an AI agent answer first?** Default: only after the top articles exist, with the
  handover rules above.
- **May support impersonate users?** Default: read-only, logged, time-limited, write only with
  customer consent.
