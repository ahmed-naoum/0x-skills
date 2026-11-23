# Proposals, contracts, custom work and collection

Read this when: writing a proposal or quote, turning a verbal yes into a signed contract,
answering redlines on an MSA, deciding which terms to give up, scoping or pricing custom work,
storing contracts and tracking renewals, or collecting a prepayment or an overdue invoice.

This file gives the commercial mechanics and common market positions. A lawyer drafts the
standard terms once and reviews the first enterprise MSA; the fallback playbook below then
handles most redlines without one. The DPA, privacy terms and terms of service themselves →
`0x:privacy-compliance`.

## Proposal

A proposal confirms a decision the buyer has made in conversation; it does not persuade. Send it
after discovery and a demo, walk through it live with the economic buyer, and never email it into
silence. One to three pages:

| Section | Content |
|---|---|
| Their situation | The problem and its cost, in the words and numbers from discovery |
| Outcome | What changes for them, with the measures agreed |
| Scope | What is included, and explicitly what is not |
| Options | Two or three that differ in scope or commitment, the recommended one marked, each priced |
| Timeline | Signature to go-live, including what they must provide |
| Terms | Term length, billing frequency, payment terms, renewal, link to the standard terms |
| Next step | The signature step and date, and an expiry date for the offer (commonly 30 days) |

Options must differ in what the buyer gets; the same scope at three prices invites haggling. The
expiry date creates a decision point. Wherever possible the proposal is the order form, ready for
e-signature, so proposal and contract are one document.

## Order form on standard terms

The fastest contract is a one- or two-page order form referencing standard terms at a versioned
URL: customer legal entity and address, signatory, plan and quantity, price and discount with its
duration, start and end dates, billing frequency and payment terms, auto-renewal and notice
period, PO number if they use one, "governed by the Subscription Agreement at [URL], version
[date]", and every agreed special term listed explicitly.

- Draft the standard terms as a reasonable middle position. One-sided terms produce more redlines
  and slower deals than the protection is worth.
- Sign through an e-signature tool (DocuSign, Dropbox Sign, PandaDoc or similar); keep the signed
  PDF with the terms version. Self-serve buyers accept terms at checkout, recorded with timestamp
  and version.
- When a buyer insists on their own paper, ask whether ours can be used with their changes first.
  Their template is usually written for buying services, takes longer, and needs legal review;
  if it is unavoidable, apply the same fallback playbook to it.

## Storing contracts and tracking renewals

Keep one repository (a folder per customer, or the CRM's document store) and a registry row per
contract:

| Field | Why it matters |
|---|---|
| Start, end, term | Renewal timing |
| Auto-renewal and the non-renewal notice period | The customer's notice deadline is when the renewal is really decided |
| Price, discount and its expiry, price-increase clause or cap | What may change at renewal, and how much notice an increase needs |
| Payment terms, billing frequency, PO requirements | Collection |
| Non-standard commitments: SLA, breach-notification time, data location, termination for convenience | These are obligations someone has to operate |
| Signatories, terms version, concessions granted | Disputes and the next negotiation |

Set two reminders per contract: about 120 days before the end (renewal work starts,
`success-churn.md`) and 30 days before the customer's notice deadline. Keep an obligation register
with an owner per promise: "notify Customer X of security incidents within 48 hours" must be in
the incident runbook, or it will be breached in the first incident.

## Negotiating discounts, annual prepay and terms

Never give without getting. Every concession is traded for something of value to you.

| They ask for | Trade it for |
|---|---|
| A discount | Annual prepay, multi-year term, signature by a date, more volume, a case study or reference |
| Price lock across renewals | A multi-year commitment |
| Monthly billing on an annual contract | Quarterly as the middle; or a higher price, since it costs cash and collection effort |
| Payment terms beyond net 30 | Accept only for a strategic logo, or at list price with no other discount |
| A longer pilot | A signed conditional order form |

- Discount the first year (a ramp), not the list price, so renewal returns to list. The order
  form shows list price, the discount and when it ends.
- Prefer non-price concessions: onboarding hours, extra training, a longer export window.
- Hold any discount until the end. Offered early, it becomes the floor for the next ask,
  including procurement's.
- Refuse most-favored-customer pricing: it makes every future discount retroactive.
- Discount limits and the value of annual prepay are policy → `0x:pricing-monetization`.

## Concede, trade or refuse

Positions common for a small SaaS vendor; confirm with counsel on the first contracts.

| Term requested | Position |
|---|---|
| Mutual confidentiality; termination for material breach after a 30-day cure period | Concede |
| Data export window and deletion on termination; notice of new subprocessors with right to object | Concede (they belong in the DPA anyway) |
| Their governing law and venue | Trade, or concede when the jurisdiction is reasonable and the deal strategic |
| Payment terms beyond net 30 | Trade |
| SLA with service credits | Trade; credits capped and the sole remedy |
| Higher cap for data breach and confidentiality (supercap) | Trade, as a fixed multiple of annual fees within insurance limits |
| Termination for convenience | Trade; never with a refund of prepaid fees in year one |
| Cap on renewal price increases | Trade for term length |
| Unlimited liability beyond the standard carve-outs | Refuse |
| Most-favored-customer pricing; exclusivity or non-compete | Refuse |
| Ownership of the product, improvements or feedback | Refuse; the customer owns its data and bespoke deliverables only |
| Source-code escrow for multi-tenant SaaS | Refuse; offer data export and termination assistance |
| Penalties or liquidated damages beyond service credits | Refuse |
| Unlimited on-site audits | Refuse; offer the SOC 2 report or questionnaire, plus audit for cause with notice at their cost |
| Acceptance testing of a subscription | Refuse; acceptance belongs to custom work under a statement of work |

## Enterprise MSA: liability caps, SLA, indemnity, termination

| Clause | Common market position | Trap |
|---|---|---|
| Liability cap | Each party capped at fees paid or payable in the 12 months before the claim; mutual exclusion of indirect and consequential damages | A cap only on their side, or a cap equal to the total value of a multi-year deal |
| Carve-outs | Confidentiality breach, IP infringement indemnity, gross negligence or willful misconduct, customer's payment obligations | "Data protection breach" uncapped; replace with a supercap and check it against the cyber policy's limit |
| SLA | Monthly uptime target excluding announced maintenance (99.9% allows about 43 minutes a month); credits as a capped share of monthly fees; termination only for repeated misses | Promising a number the system has not demonstrated; measure first → `0x:site-reliability` |
| Indemnity | Vendor defends third-party IP infringement claims, excluding customer modifications and combinations; customer covers its content | Indemnity for "any breach" or "any claim arising from the agreement", which bypasses the cap |
| Termination | For material breach with cure; on insolvency; customer data exportable for a window (often 30 days) | Convenience termination with pro-rata refund of an annual prepayment turns annual into monthly |
| Assignment | Either party may assign to a successor in a merger or acquisition | Consent-only assignment can block selling the company |
| Insurance | Maintain listed policies at stated limits | Limits above what is actually insured; check with the broker before signing |

Read every carve-out against the cap together: a long exception list can quietly make most
liability unlimited.

## Redlines with a fallback playbook

Write one row per clause that recurs, with who may approve each level:

| Clause | Standard | Fallback 1 | Final fallback | Walk away |
|---|---|---|---|---|
| Liability cap | 12 months' fees | 12 months' fees with a fixed minimum | Supercap of a small multiple of annual fees for data and confidentiality | Unlimited |
| Payment terms | Net 30 | Net 45 | Net 60 with annual prepay | Payment only on their acceptance |
| Termination for convenience | None | 90 days' notice, no refund | Pro-rata refund only after year one of a multi-year term | Refund in year one |

1. Take redlines in tracked changes and run a document comparison against your last version on
   every returned draft; unmarked edits happen.
2. Accept harmless changes quickly, counter playbook items with a one-line reason in a comment,
   escalate only what the playbook does not cover.
3. Return one complete response per round. Fewer rounds close faster.
4. When stuck, get on a call with their lawyer; most hard redlines hide one worry (breach
   liability, ability to leave) that a narrower clause solves.
5. Record each concession in the registry; a concession must not silently become the standard.

## Collecting annual prepayments and overdue invoices

Before the first invoice, ask: where do invoices go, is a PO needed, are we set up as a supplier?
Supplier setup is often the real delay (`procurement-security.md`). Invoice an annual prepayment
on signature or start date at net 30, with their exact legal entity, the PO number and the
requested address. Offer card and bank transfer with a hosted pay link (mechanics →
`0x:payments-billing`).

| When | Action |
|---|---|
| 7 days before due | Reminder with the invoice and pay link |
| Due date | Reminder |
| +7 days | Email accounts payable and the champion: is anything missing (PO, supplier setup, wrong entity)? |
| +14 days | Phone call; the champion escalates internally |
| +30 days | Formal notice citing the contract: late interest and a suspension date |
| Per contract, often +45 to +60 | Suspend access after written notice; keep the data |
| Beyond | Collections or legal action only where the amount justifies it |

Most late enterprise payments are process failures, not unwillingness: fix the process before
escalating tone. Suspension for non-payment after notice, and late interest within local legal
limits, must be in the terms; without them the only lever is goodwill. Collect the deposit before
starting services work.

## Statement of work for custom work

| Section | Content |
|---|---|
| Objective | The business outcome in one paragraph |
| Deliverables | Each item described precisely enough to test |
| Out of scope | The things the buyer is most likely to assume are included |
| Dependencies | Data, access and a decision-maker from the customer; feedback within N business days; their delays move the schedule |
| Milestones | Dated, with dependencies |
| Acceptance | Conformance to the deliverable description; N business days to accept or list specific nonconformities; silence counts as acceptance; fix-and-resubmit loop |
| Change control | Every change written, estimated in cost and schedule, and signed before work starts |
| Payment | Deposit on signature, the rest by milestone on acceptance |
| IP | Vendor keeps pre-existing IP, tools and generic improvements; customer owns or licenses bespoke deliverables once paid |
| Warranty | Defects reported within N days fixed free; then maintenance terms |

Traps: acceptance with no deadline (payment never comes), "and anything else needed" in scope,
assigning IP in the product core, and free changes "while you are in there".

## Pricing services without subsidizing the customer

| Model | Use when | Protect with |
|---|---|---|
| Fixed bid | Scope is clear and the work has been done before | Contingency on the estimate (rule of thumb: 20 to 30%), strict change control, deposit |
| Time and materials (day or hourly rate) | Scope is uncertain or exploratory | Estimate range, a cap that needs re-approval, weekly hours report |
| Retainer | Ongoing work or premium support | Monthly fee for a bucket of hours; unused hours expire or roll over once; overage at the rate |

- Derive the rate from cost: loaded annual cost divided by realistically billable hours, plus
  margin. A founder bills far fewer hours than they work (sales, support, admin); a rate that
  counts only coding hours subsidizes the customer.
- Charge for implementation on product deals, or show it on the order form at list with a 100%
  discount so its value is visible and chargeable next time.
- Custom features: if generalizable and the IP stays with you, price lower, because other
  customers will pay for it too. If only one customer will use it, add an annual maintenance fee,
  because the code costs something every release.
- Services are a way to land and grow subscriptions, not the business, unless the founder decides
  otherwise; low-margin custom work crowds out the product.

## Ask the user

- **How much liability risk is acceptable?** Sets the cap, supercap and insurance. Default: 12
  months' fees, supercap only for data and confidentiality.
- **Is there budget for a lawyer?** Default: one engagement to draft standard terms and the
  playbook, then only for clauses outside it.
- **Above what deal size will we accept the customer's paper?** Default: only for deals worth
  several months of revenue.
- **Payment terms and billing frequency to offer?** Default: annual prepay, net 30, card or transfer.
- **Will we do custom work at all, and at what rate?** Default: only when it lands a subscription,
  under a signed statement of work with a deposit.
