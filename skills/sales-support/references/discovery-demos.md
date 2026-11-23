# Discovery calls, demos and pilots

Read this when: preparing for or debriefing a sales call, qualifying a lead, building or giving a
demo, answering an objection, proposing or running a pilot, planning the path to signature, or
deciding whether a deal still deserves time.

## The order of a sale

Discovery → qualified → tailored demo → pilot (only if needed) → proposal → close plan → signature.
Most lost deals were lost in discovery: the seller demoed before knowing the pain, never met the
person who signs, and did not know how the buyer purchases. Demoing on the first call because the
buyer asked is the most common founder error; ask two or three discovery questions first, then
show only what maps to the answers, and book the full demo.

## Discovery call

A 30 to 45 minute call where the buyer talks most of the time (rule of thumb: two-thirds or more).

| Minutes | Part | Purpose |
|---|---|---|
| 0–3 | Upfront agreement | Confirm time and purpose; say either side may conclude it is not a fit; name the likely next step |
| 3–25 | Situation and pain | How they do it today, what breaks, what they have tried |
| 25–35 | Impact and decision | What it costs, why now, who decides and how |
| 35–45 | Summary and next step | Read back what you heard; book the next meeting before hanging up |

Ask about past and present behavior, not hypotheticals; "would you use X?" gets polite lies.

| Purpose | Questions |
|---|---|
| Situation | "Walk me through how you handle X today. Who is involved? What tools?" |
| Pain | "What happened the last time it went wrong? What have you tried to fix it?" |
| Impact | "What does that cost per month in hours, money or risk? Who else feels it?" |
| Why now | "Why look at this now rather than last year? What happens if nothing changes by [date]?" |
| Decision criteria | "What would a solution have to do for you to choose it? What would rule one out?" |
| Decision process | "Last time you bought a tool like this: who signed, did security or legal review it, how long did it take?" |
| Budget | "How was the last tool like this paid for? Is there budget, or would it come from elsewhere?" |
| Competition | "What else are you considering, including building it or doing nothing?" |

- Follow the pain down three levels: problem → consequence → consequence for the business or the
  person. "Annoying" is not a pain; "we lose two renewals a quarter" is.
- Write their numbers and words down. They go into the proposal and the champion's business case.
- Close with a read-back: "So the problem is X, it costs about Y, it must be fixed before Z, and A
  and B decide. Is that right?" Corrections here are worth more than anything said earlier.
- Book the next step on the calendar during the call. "I'll send something over" is not a step.
- Same day: recap email with the summary and next step, notes and stage in the CRM.

## Qualification: pain, budget, authority, timeline

| Criterion | Qualified | Red flag |
|---|---|---|
| Pain | Specific, quantified, felt by someone with influence | "Just exploring", "nice to have", no number |
| Budget | Budget exists, or they can explain how money was found last time | No path to money; refuses to discuss price |
| Authority | Signer and approval path known; signer met or meeting agreed | "I'll take it to my boss" with no access offered |
| Timeline | Tied to an event: a contract ending, a launch, an audit, a hire | "Sometime this year" |

A deal enters Qualified only with all four answered; unknowns become questions for the next call,
not assumptions. Disqualifying early is a win: it frees the scarcest resource, the founder's
calendar. At small companies budget is rarely pre-allocated, so the real question is whether the
pain costs clearly more than the price. At large companies budget follows the fiscal year: ask
when it starts and when next year's is set.

For deals large enough to involve procurement, extend to MEDDICC: Metrics (the quantified
outcome), Economic buyer, Decision criteria, Decision process, Identify pain, Champion,
Competition. Each letter is a CRM field; a blank one is the next call's agenda.

## Demo tailored to the stated problem

Prepare:

- Re-read the discovery notes; list the two or three problems they named; map each to one workflow.
- Ask the champion who attends and what each person cares about.
- Use a dedicated demo account seeded with realistic data for their industry (their own sample
  data if quick and they agree), feature flags in a known state, and a reset script. Never demo
  inside a real customer's account. Keep a recording of the main flow in case the live one breaks.

Run:

1. Restate their problem in their words and ask if it is still right. Adjust if not.
2. Show the outcome first (the finished report, the solved state), then how they get there.
3. Per section: say what you will show and why it matters to them, show it, ask "how does that
   compare with how you do it today?"
4. Stop showing at 20 to 25 minutes. Use the rest for questions, objections and the next step.

- Show only what maps to their pain. A feature tour bores buyers and invites objections to
  features they never cared about.
- Unbuilt features: say "not yet" plainly. Never present a mockup as live, and never promise a
  roadmap date to win a deal; it becomes a contractual expectation and a churn reason.
- Mixed audiences: executives want outcome, cost and risk in five minutes; users want their daily
  workflow; IT wants SSO, security and integration. Split sessions when the group is mixed.
- Afterwards: recap email mapping what they saw to each problem, answers to open questions, next step.

## Handling objections

Acknowledge, ask a question to find the real objection, answer that one, confirm it is resolved.
The first objection stated is often not the real one.

| Objection | Usually means | Response |
|---|---|---|
| "Too expensive" | Value not established, or compared with a cheaper category | Return to the quantified impact; compare price with the cost of the problem; trade rather than cut (annual prepay, longer term, smaller scope, case study); policy → `0x:pricing-monetization` |
| "No budget this year" | Low priority, or a real budget cycle | Ask what would have to be true to fund it; offer a smaller start below their approval threshold; book a call before their budget is set |
| "We need your SOC 2 / security review" | Real procurement step, or a stall | Send the security pack the same day (`procurement-security.md`); ask who reviews and what their bar is; offer a call with that reviewer |
| "Not right now" | Competing priority, or weak pain | Ask what is ahead of it and what waiting six months costs; set a dated follow-up tied to their event |
| "We'll build it ourselves" | Spare engineering capacity, or fear of lock-in | Compare build plus maintenance plus delay with the price; answer lock-in with API and export |
| "You're too small to rely on" | Vendor risk | Data export, termination rights, references, uptime history; runway only if asked |
| "Need to think about it" | An unstated concern | "What would you want to think through? Usually it is price, risk or timing." |
| "Send me some information" | Brush-off | Ask one discovery question; if nothing lands, agree a dated follow-up |

## Stakeholder map

| Role | Who | What they need | Test |
|---|---|---|---|
| Champion | Has influence, wants you to win, sells when you are not in the room | Business case, one-page summary, answers to internal objections | Gives you access to the economic buyer and shares internal facts (process, rivals, concerns). One who will not is a friendly contact, not a champion |
| Economic buyer | Can approve the spend without asking anyone | Outcome, cost, risk, fit with priorities | Has said yes to the priority and the budget |
| Technical evaluator | IT, security, engineering lead | Integration, security, admin effort | Has signed off the review |
| Users | Use it daily | Less work, fits their workflow | Active in the trial or pilot |
| Blocker | Owner of the current tool, security, a team that loses scope | Their concern answered | Concern named and answered in writing |

- At a 20-person company one person holds several roles; at an enterprise, expect many people in
  the decision.
- Multithread every deal that would die if the champion left: two or three real relationships.
  Champions change jobs, get busy and lose internal arguments.
- Record name, role, stance (supporter, neutral, opposed) and last contact in the CRM after each call.
- Reach the economic buyer through the champion, not around them: "for a project this size we
  usually spend 20 minutes with whoever owns the budget, to make sure we solve what matters to them."

## Paid pilot with success criteria and conversion terms

Use a pilot when the buyer needs proof on their data or users before a large commitment and the
deal justifies the work. Skip it for small deals: a monthly plan with easy cancellation is the pilot.

| Term | Default |
|---|---|
| Price | Paid, a meaningful fraction of the annual price, credited to year one on conversion. Unpaid pilots get no attention on the buyer's side |
| Length | 30 to 60 days; 90 only with a reason. Long pilots lose their sponsor |
| Scope | One team, one or two use cases, named users |
| Success criteria | Two to four measurable criteria agreed in writing with the economic buyer, each with how and by whom it is measured |
| Conversion | Written before the start: criteria met → converts to [plan] at [price] from [date]; ideally a signed order form with a pilot clause |
| Cadence | Named owner each side, weekly 30-minute check-in, end-of-pilot review booked at kickoff with the economic buyer |

Traps: no criteria, so the pilot never ends; criteria set by users while someone else decides;
unpaid custom development called a pilot; extending instead of deciding. Treat an extension
request as a signal and ask which criterion is unmet.

## Mutual close plan

A shared document with every step from today to the buyer's go-live, an owner and a date on both
sides, built backwards from their compelling event. Introduce it once qualified: "To hit your
April go-live, this is what usually has to happen; can we check it together?"

| Date | Step | Owner |
|---|---|---|
| Mar 3 | Demo for the operations team | Us, champion |
| Mar 10 | Security questionnaire returned | Us |
| Mar 14 | Budget approved | Economic buyer |
| Mar 17 | Contract redlines returned | Their legal |
| Mar 24 | Supplier setup in their procurement system | Us, their accounts payable |
| Mar 28 | Signature | Economic buyer |
| Apr 1 | Kickoff (`customer-onboarding.md`) | Both |
| Apr 15 | Team live, before their quarter starts | Both |

Review it in every call. A buyer who will not put dates on it is saying the priority is low. Dates
slipping without new information mark a deal at risk; dates slipping with a reason are normal.

## Recognizing a deal that will not close

Two or more of these, and the deal is probably dead:

- No quantified pain after discovery; the problem is "interesting" rather than costly.
- No access to the economic buyer after two or three meetings.
- Close date pushed repeatedly with no new reason; no reaction to the close plan.
- Requests for free custom work, an open-ended free pilot, or roadmap commitments as a condition.
- Requirements outside the ICP (on-premises, a feature only they need) that would bend the product.
- Contract demands that belong in the refuse column (`proposals-contracts.md`).
- The champion silent for weeks.

"No decision" loses more deals than competitors do. Ask directly: "It sounds like this is not a
priority right now; should we close the file for now?" This often restarts an honest conversation.
If it does not, close as lost with a reason, set a recontact date tied to their event, and move
on. Give each stage a maximum age (rule of thumb: about twice the median time won deals spent
there); past it, re-qualify or close.

## Ask the user

- **Smallest deal worth a sales call?** Below it, send people to self-serve. Default: deals under
  a few thousand a year go self-serve with an optional short call.
- **Are pilots offered, and at what price?** Default: paid, credited on conversion, only above
  that threshold.
- **Which customizations or roadmap items may be promised?** Default: none with dates; paid custom
  work only through a statement of work.
- **What security material exists today?** Determines the answer to the most common enterprise
  objection. Default: assume none and build the pack in `procurement-security.md`.
- **Who may approve a discount, and how much?** Default: founder only, within the policy set in
  `0x:pricing-monetization`.
