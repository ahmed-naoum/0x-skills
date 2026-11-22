# Refunds, chargebacks and fraud

Read this when: issuing or automating refunds, a dispute (chargeback) has arrived, dispute or
fraud rates are rising, a card-testing attack is under way, a billing bug charged customers
wrongly, or the concern is the processor freezing the account or holding payouts.

## Refunds

A refund is a new money movement linked to the original payment, not an undo. Model it as its
own row and drive state from the provider.

| Rule | Why |
|---|---|
| Refund through the provider API against the original payment, with an idempotency key from the local refund row | A retried request must not refund twice |
| Cap server-side: sum of refunds ≤ captured amount, checked under a lock on the payment | Concurrent partial refunds from two support agents otherwise over-refund |
| Record `pending` locally, finalize on the refund webhook | Refunds can fail (closed card, expired method) days later; a failed refund needs a manual payout by other means |
| Refund goes to the original payment method | Refunding to a different destination is a money-laundering and fraud vector; processors and law restrict it |
| Tell the customer the timing: several business days to appear on a card statement | Prevents the "where is my refund" ticket and the dispute that follows |
| Issue a credit note for the refunded amount | Keeps tax reporting right, see `invoices-tax.md` |

Entitlements after a refund, decided per product rather than left implicit:

| Case | Billing | Access |
|---|---|---|
| Full refund of a one-time purchase | Refund all | Revoke: license key, download, order canceled, stock returned if applicable |
| Full refund of a subscription payment | Refund and cancel the subscription immediately | Ends now. Refunding without canceling leaves it renewing |
| Partial refund as a goodwill gesture | Refund part | Unchanged |
| Partial refund for removed seats or items | Refund the prorated part | Reduce quantity; update the provider subscription too |
| Refund of prepaid credits | Refund unused paid credits only | Deduct the credits in the same transaction (see `usage-billing.md`) |

- The processing fee on the original charge is usually not returned by the processor, and for
  currency-converted payments the exchange rate has moved. A refund costs more than zero;
  account for the fee as an expense, not as part of the refund.
- A refund policy that is short, public and generous (for example a no-questions window after
  first purchase) is cheaper than disputes. Automate refunds inside the window for self-serve.
- Refund abuse: track refunds per customer and payment fingerprint; repeat refunders lose the
  self-serve path.
- **Do not refund a payment that already has an open dispute**: the bank has already taken the
  money back, and a refund on top pays twice. Respond to the dispute instead.

## Preventing disputes

Most "friendly fraud" disputes come from a customer not recognizing a charge or not finding how
to cancel. The preventive measures are cheap.

- **Statement descriptor** the customer recognizes: the product name they know, not the legal
  entity, within the length the card networks allow, plus a support URL or phone in the
  provider's public business details. Check how it renders on a real statement.
- **Receipt for every charge**, including renewals, with the product name, amount, the date of
  the next charge and a one-click path to manage or cancel.
- **Reminders** before a trial converts and before annual renewals.
- **Cancellation in the product**, without contacting support. A customer who cannot cancel in
  a minute disputes instead.
- **Fast, visible support** and fast refunds: answer billing mail within a day; refund first
  when the amount is small relative to a dispute fee.
- **Early dispute signals**: card networks and processors issue fraud warnings and pre-dispute
  alerts before a formal chargeback. For a fraud warning on a charge that is not clearly
  legitimate, refunding immediately and cutting access is usually cheaper than waiting: the
  chargeback then normally does not follow, saving the fee and the count against the dispute
  ratio. Automate this for low amounts. Dispute-deflection services that auto-refund on an
  inquiry are worth enabling once dispute volume is regular.
- **Delivery evidence by default**: log the sign-in, IP, device and usage tied to each purchase,
  and acceptance of terms with timestamp. That log is the evidence file later.

## Contesting a chargeback

When a dispute opens, the disputed amount and a dispute fee are debited immediately; winning
returns the amount, often not the fee.

1. **Webhook → ticket** the same day (`charge.dispute.created`). The response deadline is set
   by the network and shown on the dispute, typically one to three weeks; it is absolute, and
   only one submission is allowed.
2. **Decide whether to fight.** Fight when the customer demonstrably used the product or
   received the goods. Accept when it is true fraud (stolen card: the cardholder is right),
   when evidence is thin, or when the amount is below the cost of the time. Accepting promptly
   is not penalized more than losing.
3. **Suspend the account** behind the disputed payment and cancel its subscription so no
   further charges become further disputes. Restore on a win or a withdrawn dispute.
4. **Match the evidence to the reason code**; evidence that answers a different claim loses.

| Reason | Evidence that wins |
|---|---|
| Fraudulent / unauthorized | Proof the cardholder used the product: logins and usage from an IP and device matching earlier undisputed payments, 3-D Secure authentication result, AVS and CVC match, account email matching the cardholder, delivery to the billing address |
| Product not received | Carrier tracking with delivery confirmation; for digital goods, access and download logs after purchase |
| Subscription canceled / credit not processed | Terms and cancellation policy as shown at checkout, proof that no cancellation was requested (or its date), usage after the claimed cancellation, renewal reminder sent |
| Not as described | The product description at purchase, correspondence, refund policy accepted |
| Duplicate | Two distinct orders, each with its own delivery; or acknowledge and accept if truly duplicate |

5. **Write for a bank analyst with two minutes**: a one-paragraph summary, then labeled
   exhibits, no jargon, customer-facing screenshots rather than database dumps.
6. **Talk to the customer** when there is a relationship: many disputes are mistakes, and a
   customer can withdraw one with their bank. Get the withdrawal in writing and submit it.
7. **Record the outcome** and the reason in the ledger: amount reversed, fee, win or loss.

A payment authenticated with 3-D Secure generally shifts liability for *fraud* disputes to the
issuer. It does not protect against the other reason codes.

## Dispute and fraud rate against network thresholds

Card networks run monitoring programs that place merchants with excessive disputes or reported
fraud into remediation, with fines, higher fees and eventually loss of card acceptance.
Processors act earlier than the networks, with reserves or termination.

- The ratios are counted in transactions, per network, per month, and the dispute counts
  against the month it arrives while the sale may be months old. A small merchant with few
  sales can cross a percentage threshold with a handful of disputes; programs have minimum
  counts, but processors' own risk teams do not wait for them.
- Program names, formulas and thresholds change (Visa restructured its programs in 2025 to
  combine fraud reports and disputes into one ratio). Look up the current thresholds; as a
  durable internal alarm, treat a monthly dispute ratio approaching half a percent of card
  transactions as an incident, well below where formal programs have historically begun (around
  one percent).
- Track weekly: disputes ÷ transactions, fraud warnings ÷ transactions, by network, product,
  acquisition channel and country. A spike confined to one channel or affiliate is the usual
  finding.
- Card-testing bursts inflate fraud counts even when every test charge was small. Blocking the
  attack and refunding the successful test charges before they are reported both matter.

## Card testing

Attackers validate stolen card numbers with many small charges or card-saving attempts. Signs:
a surge of attempts with a high decline rate, many cards per IP or per account, small or
minimum amounts, new accounts with disposable emails, a free trial or donation form as the
target, attempts continuing at night.

Response, in order of speed:

1. **Make the endpoint expensive to reach**: require a signed-in session or a server-issued
   single-use checkout token; invisible bot challenge (CAPTCHA) on payment and card-setup
   submission; rate limits per IP, per account, per device and per card fingerprint. An
   unauthenticated endpoint that creates payment or setup intents is the hole in most cases.
2. **Velocity rules at the provider**: block after N declines per card, per IP or per email in
   a window; block when one customer adds many distinct cards.
3. **Raise friction where the attack lands**: require CVC and postal code checks to pass,
   request 3-D Secure for risky attempts, block card countries the product does not sell to,
   block prepaid cards only if the data supports it.
4. **Remove the cheap oracle**: no zero-amount or minimal-amount validation without a challenge;
   identical generic decline messages (see `checkout-experience.md`).
5. **Clean up**: refund successful fraudulent charges proactively, cancel the accounts, and
   tell the processor an attack was mitigated. Unanswered card testing leads to disputes weeks
   later and to the processor restricting the account.

Alert: attempts per minute and decline rate against trailing baselines. General bot defense and
rate-limit architecture: `0x:web-security`.

## Tuning fraud rules against false declines

Every fraud rule also declines some good customers, and a blocked good customer costs the sale
and usually the customer. Tune with data, not anecdotes.

- Separate three outcomes in the data: declined by issuer, blocked by own rules or the
  provider's risk engine, and approved-then-disputed. Only the second is under direct control.
- For each rule, estimate what it blocks: review a sample of blocked attempts for signs of
  legitimacy (existing customer, later successful payment with another card, support contact).
  A rule whose blocks are mostly later-successful customers is costing money.
- Compare the expected loss: `fraud prevented = blocked fraud × (amount + dispute fee + ratio
  pressure)` against `sales lost = blocked good orders × margin × lifetime value`. For digital
  goods with near-zero marginal cost the tolerance for fraud is higher than for physical goods
  or anything resellable (gift cards, credits, electronics).
- Prefer step-up over block: send borderline attempts to 3-D Secure or manual review instead
  of declining. Authentication shifts fraud liability and keeps the good customer.
- Test rule changes in the provider's backtest or shadow mode before enforcing, change one rule
  at a time, and watch block rate, authorization rate and fraud warnings for the following
  weeks (disputes lag by weeks to months).
- Issuer decline codes are data too: rising `do_not_honor` on one country or BIN range after a
  rule change suggests issuers distrust the traffic being let through.
- Allow-list known-good customers (paid history with no disputes) past generic rules.

At Launch: provider defaults plus velocity rules and the endpoint hardening above. Custom rule
sets and manual review queues are for when fraud losses or false declines are measurable.

## Correcting a billing bug

A bug overcharged, double-charged or under-entitled a set of customers. Proceed as an incident.

1. **Stop the bleeding**: disable the faulty path (pause the job, feature-flag the price), and
   confirm no further wrong charges are being created.
2. **Build the affected list from the provider's records**, joined to the database: payment ID,
   customer, charged amount, correct amount, difference. Have a second query or person verify
   the list; a wrong correction is a second incident.
3. **Choose the remedy per group**: refund to the payment method (default for overcharges;
   required if the customer asks), account credit (acceptable for small amounts on active
   subscribers, with the option to get money back), or extended service. Under-charges are
   usually absorbed; back-billing customers for the company's bug costs more goodwill than it
   recovers, and may not be permitted.
4. **Script the correction idempotently**: a table with one row per affected payment and a
   status; the idempotency key is the row ID; dry-run mode that prints totals; provider rate
   limits respected; resumable. Run a small batch, verify at the provider, then the rest.
5. **Fix entitlements in the same pass**: restore access wrongly removed, extend periods.
6. **Issue credit notes** for the corrected invoices and re-check tax.
7. **Tell customers before they notice**: what happened, the exact amount, when the refund will
   appear, nothing to do. Proactive notice prevents disputes on the erroneous charges.
8. **Reconcile afterward**: sum of refunds equals the computed difference; add the missing
   constraint or test that would have caught it; write the postmortem (`0x:site-reliability`).

## Processor terms, reserves and freezes

A processor can hold payouts or close the account with little notice when it sees risk. The
triggers are predictable: a product on or near the restricted list, a sudden volume spike,
rising disputes or refunds, card testing, long gaps between payment and delivery (preorders,
annual prepayments, events, crowdfunding), mismatched business details, or unanswered
verification requests.

- Read the restricted and prohibited business lists before building, and describe the business
  accurately at onboarding. Mis-categorization discovered later is treated as deception.
- Tell the processor ahead of expected spikes: a launch, a sale, a press event.
- Answer verification and information requests within the day; unanswered requests escalate to
  payout holds automatically.
- Keep refunds and disputes low, and deliver promptly after charging. Charging long before
  delivery is the pattern that earns a rolling reserve.
- **Keep an operating buffer outside the processor**: sweep payouts on the fastest schedule to
  the bank, and hold enough cash to cover refunds, payroll and bills for the length of a
  plausible hold (weeks to a few months). A negative processor balance from refunds during a
  freeze is debited from the bank account.
- Keep exportable records (customers, subscriptions, invoices) current, and the fallback from
  `checkout-integration.md` ready: a second approved account and the card-data migration path.
- During a freeze: comply quickly and completely, keep serving customers, do not open duplicate
  accounts under other names with the same processor (that makes closure permanent).

## Ask the user

- **What is the refund policy?** It drives automation and dispute evidence. Default: full
  refund on request within a short window after first purchase (14 or 30 days), case by case
  afterwards, no prorated refunds on annual plans except by exception.
- **Who may issue refunds, and up to what amount without approval?** Default: the founder only
  at Launch; support staff with a per-refund cap later.
- **On a fraud warning for a small charge, refund automatically?** Default: yes, refund and
  suspend the account below a set amount.
- **Fight disputes or accept them?** Default: fight when usage or delivery evidence exists and
  the amount exceeds roughly an hour of time; accept true fraud.
- **How many weeks of expenses are held outside the payment processor?** Default: recommend at
  least a month, more for businesses that charge long before delivering.
