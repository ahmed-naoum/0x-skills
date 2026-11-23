# Reviews, complaints and reputation

Read this when: a customer is angry in private or in public, a bad review or viral complaint
appeared, apologizing after an outage or mistake, deciding when and how to ask for reviews or
referrals, setting up mention monitoring, running NPS or CSAT, or building references for sales.

## Asking for reviews and referrals at the right moment

Ask right after the customer has felt the value:

- Reached first value or a milestone (first report sent, go-live).
- Said they are happy: a thank-you in a ticket, a positive CSAT comment, a high NPS score.
- Had a problem solved fast.
- Renewed or expanded, or saw a measured result in a business review.

Mechanics:

- A person asks, in one or two sentences, with a direct link to the review form. Make it a
  two-minute task.
- Choose one or two sites where buyers in the segment look: for B2B software G2, Capterra and its
  sister sites, TrustRadius; for mobile the app stores, through the platform's native in-app
  review prompt; for local services Google Business Profile; for consumer products Trustpilot and
  similar.
- Do not choose whom to ask by predicted sentiment ("review gating"). Google's review policy
  forbids selectively soliciting positive reviews, other platforms ban it too, and consumer
  regulators can treat it as deceptive. Asking everyone who reaches a defined milestone is fine.
- No fake reviews, no undisclosed reviews by staff or relatives, no paying for positive reviews.
  The US FTC's 2024 rule on consumer reviews bans fake reviews, incentives conditioned on
  sentiment, undisclosed insider reviews and review suppression, with civil penalties per
  violation; the UK (DMCC Act, since April 2025) and EU consumer law ban fake reviews and hidden
  incentives. Platform-run incentive programs (a disclosed gift card for any honest review) follow
  that platform's rules; Google does not allow incentives for reviews at all.
- Never offer anything to remove or change a negative review.

Referrals: at the same moments, ask "who else do you know who has this problem?" and give a
forwardable blurb. In B2B, account credit for both sides usually works better than cash (program
mechanics → `0x:growth-marketing`). Tell the referrer what came of it.

## De-escalating an angry customer

1. Respond fast. Speed lowers the temperature more than any wording.
2. Acknowledge the specific problem and what it cost them, in their terms. "We apologize for any
   inconvenience" is the opposite.
3. Do not argue facts in the first reply, even wrong ones; ask questions to understand.
4. Own what is yours, plainly. Do not blame a vendor, a colleague or the customer.
5. Say what will happen and by when, then deliver, earlier if possible.
6. Move complex or high-value cases to a call; voice de-escalates faster than email.
7. Ask what a good outcome looks like for them; it is often less than feared.
8. Follow up a week after resolution: "Is everything working now?" Customers whose problem was
   handled well often become more loyal than before.

Do not use saved replies, open with "per our policy", get defensive, over-promise, or give partial
truths that surface later. When the amount is small and the case unclear, refund: a refused small
refund costs more as a chargeback, a public review and lost time (`support-operations.md`).

Boundaries: an abusive customer can be told calmly that the conversation continues when it is
respectful; document it, and refund and part ways if needed. Threats of violence end the
conversation; document them and involve the founder and, if warranted, the authorities.

## Answering a bad review or viral complaint publicly

The audience is the next prospect who reads it, not the reviewer.

Reply to a bad review within one or two business days, from a named person, in three to five
sentences: thank them, acknowledge the specific issue, state facts without arguing, say what has
changed or will change, give a direct contact.

- Never disclose the customer's account details, usage or support history in public. It is a
  privacy breach and the fastest way to look hostile.
- Once resolved, it is fine to ask whether they would consider updating the review; never make
  help conditional on it.
- Fake, competitor or policy-violating reviews: report through the platform's process with
  evidence; do not accuse in public.
- On review sites and app stores, reply to every negative review; in communities, reply when there
  is something useful to add.

Viral complaint on Hacker News, Reddit, X or LinkedIn:

| When | Action |
|---|---|
| First hour or two | One named person replies publicly: acknowledges, says what is known, what is being done, when the next update comes. Nobody else on the team joins in |
| Same day | Contact the person privately; fix or mitigate |
| After the fix | Follow up in the same thread: what happened and what changed |

- If the complaint is right, say so in the first sentence. Admitting a clear mistake ends threads;
  defending it extends them.
- Do not delete critical posts in your own community, threaten legal action, or ask friends or
  staff to post in support. Each becomes the next story.
- A claim of a security or data problem: verify before denying anything. A possible breach goes to
  the breach-response process (`0x:web-security`).

## Apologizing and compensating after an outage or mistake

1. Acknowledge quickly: a status-page update in the first hour of an incident (`0x:site-reliability`).
2. Apologize without hedging: "we" and an active verb, never "mistakes were made".
3. Explain what happened in plain language, without blaming a vendor.
4. State the impact on them specifically: which data, which time range, which actions failed.
5. Say what was done and what changes to prevent a repeat.
6. Compensate in proportion, and give a contact for questions.

| Situation | Compensation |
|---|---|
| Contractual SLA missed | Credits as the contract defines, applied automatically rather than waiting for claims |
| Painful outage within the SLA | Goodwill credit for the affected period, for affected accounts |
| Billing error | Refund and corrected invoices, sent before the customer notices |
| Data lost or corrupted | Restore what is possible, an exact account of what is lost, a credit, a founder call for key accounts |
| A mistake affecting one customer | The fix plus a credit proportionate to the impact |

- Contact affected key accounts individually before they notice.
- A factual account and an apology rarely need to concede legal liability. Large cash payments, or
  written admissions in a serious incident (a data breach, financial loss to the customer), go to a
  lawyer first. Breach notification duties → `0x:privacy-compliance` and `0x:web-security`.
- B2B customers expect a written root-cause summary within a few business days.

## Monitoring mentions

| Source | How |
|---|---|
| Review sites and app stores | New-review notifications into a shared channel |
| Social networks | Saved searches or alerts for brand and product names; a listening tool at Scale |
| Communities: Reddit, Hacker News, niche forums, Discord or Slack groups | Keyword alert services for Reddit and Hacker News; membership in the communities where the ICP gathers |
| The web | Search-engine alerts for the brand, the founder's name, "product alternative", "product down" |
| Competitors | Alerts on "competitor alternative": these are sales leads |

- Keywords: brand, product, domain, founder's name, common misspellings.
- One channel, one owner who checks daily at Launch, and an agreed rule for what gets a reply and
  from whom.
- When someone asks for alternatives to a competitor, answer helpfully and disclose the
  affiliation ("founder here"); the community's rules come first.

## Measuring satisfaction with NPS or CSAT and acting on detractors

| | CSAT | NPS |
|---|---|---|
| Question | "How satisfied were you with ...?" (1 to 5, or good or bad) | "How likely are you to recommend ... to a colleague?" (0 to 10) |
| Scope | One interaction: a ticket, onboarding | The whole relationship |
| When | Right after the interaction | At a fixed lifecycle point, then periodically, at most about twice a year per person |
| Score | Share of satisfied responses | Percentage of promoters (9 to 10) minus percentage of detractors (0 to 6) |

- Always ask "what is the main reason for your score?"; the comment is worth more than the number.
- Small samples swing wildly: with a few dozen responses, a ten-point move is noise. Watch trends
  and themes, not single readings.
- Inner loop: every detractor gets a personal reply within a few days from someone who can act,
  asking what would fix it; log the outcome.
- Promoters get the review, referral or reference ask above.
- Outer loop: monthly themes from comments into product decisions (`0x:product-discovery`);
  analysis → `0x:product-analytics`.
- In B2B, survey several roles per account and read by account: a promoter user with a detractor
  economic buyer is a renewal risk.
- Do not survey during or right after an incident unless measuring the incident, and do not tie
  pay to the score; it gets gamed.

## Reference-customer program for sales

Late-stage enterprise buyers ask to speak with a similar customer. Prepare before the request.

- Recruit from green-health promoters. Ask explicitly and record consent and its scope: logo on
  the site, quote, case study, reference calls, speaking. Many customers' contracts or policies
  forbid publicity without written consent; add an opt-in publicity clause to the order form, and
  still ask before using it.
- Match references to prospects by industry, size, use case and the competitor replaced.
- Protect references from overuse: log every call in the CRM, cap calls per reference per quarter,
  offer them only to qualified late-stage deals, brief the reference beforehand and thank them after.
- Give back: early access, an advisory-board seat, public recognition, a gift within their
  company's gift policy. A discount for being a reference is traded in negotiation and written
  into the contract (`proposals-contracts.md`).
- Case study: the problem, why they chose the product, the implementation, a measurable result in
  their own approved numbers, a quote. The customer approves the final text and logo use.
- Public testimonials from customers who received something of value must disclose that
  connection under US endorsement rules and similar laws elsewhere.

## Ask the user

- **Which review sites do our buyers read?** Default: one B2B review site, plus the app store for
  a mobile product.
- **Who speaks publicly for the company?** Default: the founder, and nobody else during a viral
  thread.
- **How much goodwill compensation may be given after an incident?** Default: SLA credits applied
  automatically; goodwill credit up to one month, approved by the founder.
- **NPS, CSAT or both?** Default: CSAT on tickets from Launch; NPS once there are a few hundred
  active users.
- **May we name customers publicly?** Default: only with written permission per customer.
