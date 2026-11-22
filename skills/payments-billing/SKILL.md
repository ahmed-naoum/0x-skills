---
name: payments-billing
description: "Takes money correctly: checkout integration and payment webhooks, subscriptions and entitlements, usage and credit billing, invoices and tax, refunds, chargebacks and fraud, ledger and reconciliation, carts and inventory. Use when integrating Stripe or Paddle, adding subscriptions or trials, fixing double charges or paid-but-no-access, or handling VAT or sales tax, disputes, failed renewals or payouts."
---

# Payments, billing and commerce

## Stance

Payment code is the one part of a product where a bug moves real money in the wrong direction
and the customer finds out from their bank. An experienced payments engineer assumes every
request can be duplicated, every response can be lost, every event can arrive twice or out of
order, and the provider and the database will disagree at some point. The work is to make each
of those harmless, and to rent everything else from the provider.

- **The provider is the source of truth for money; the database is a mirror.** State changes
  come from verified webhooks or server-side fetches, through one idempotent sync function.
  The browser redirect proves nothing: tabs close, and URLs can be replayed.
- **Amounts are computed on the server from IDs.** Anything priced by the client is a tampering
  bug. One pricing function feeds the display, the charge, the order and the invoice.
- **A payment is a state machine with an "unknown" state.** A timeout is not a failure. Resolve
  by querying or retrying with the same idempotency key; creating a new charge is how customers
  get charged twice.
- **Constraints, not care, prevent double charges.** One persisted idempotency key per attempt,
  guarded state transitions, and unique indexes in the database. UI guards only reduce how
  often the constraint is hit.
- **Card data never touches the app.** Hosted checkout or provider-hosted fields only; this
  keeps PCI scope minimal and removes the most damaging breach a small company can have.
- **Entitlements are separate from billing.** Feature code asks what the account may do; a
  layer derives that from the mirrored billing state plus overrides, and never calls the
  provider in the request path, so a billing outage does not lock customers out.
- **Money records are append-only.** Invoices are corrected by credit notes, ledger entries by
  reversals, refunds are new rows. Editing history destroys the ability to answer a customer,
  an auditor or a tax authority.
- **Reconcile daily.** Webhooks get lost and people click in dashboards. A scheduled comparison
  of provider and database, repairing toward the provider, turns silent drift into a short delay.
- **Most disputes are confusion, not fraud.** A recognizable statement descriptor, a receipt for
  every charge, renewal reminders and one-click cancellation cost less than any dispute.

Follow the project first: if it already uses a provider, billing library or commerce platform,
work within it. The defaults below are for new decisions.

## Route

| If the task is … | Read |
|---|---|
| Choosing Stripe vs a merchant of record, wiring a pay button to a confirmed order, handling payment webhooks, 3-D Secure, idempotency keys, wallets, or "the payment went through but the order is not paid" | `references/checkout-integration.md` |
| What the customer sees while paying: totals with tax and currency, decline messages, confirmation and receipt pages, abandoned-checkout emails, checkout and decline-rate monitoring, raising authorization rate | `references/checkout-experience.md` |
| Adding recurring plans, trials, upgrades and downgrades, cancel or pause, a customer portal, feature gating by plan, seats and add-ons, failed renewals and dunning, test clocks, moving customers to new prices | `references/subscriptions.md` |
| Charging by consumption: metering events, quotas, overages, prepaid credits and top-ups, seats plus usage, a usage page with spend alerts and caps, checking metered totals before invoicing | `references/usage-billing.md` |
| "Do I need to charge VAT or sales tax?", merchant of record vs own tax handling, compliant invoices, tax IDs, credit notes, e-invoicing, bank transfers and purchase orders, multiple currencies | `references/invoices-tax.md` |
| Refunding, a chargeback arrived, dispute rate rising, card-testing attack, fraud rules blocking good customers, cleaning up after a billing bug, fear of a processor freeze | `references/refunds-disputes-fraud.md` |
| Designing order, payment and ledger tables, "I was charged twice", provider and database disagree, matching payouts to the bank, export to accounting, double-entry ledger, marketplace payouts | `references/ledger-reconciliation.md` |
| Selling goods, tickets or bookable units: platform vs custom, product and variant model, cart, discounts and shipping, stock or seat reservation, fulfillment, returns, license keys, channel and warehouse sync | `references/commerce.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Provider | Stripe | Founder wants tax handled, or the entity's country is unsupported → merchant of record (Paddle or similar) |
| Checkout surface | Provider-hosted checkout page | A concrete layout or flow requirement → provider-hosted fields with PaymentIntents |
| Fulfillment trigger | Verified webhook, plus the success page calling the same idempotent function after a server-side fetch | Never the redirect alone |
| Idempotency | Key = persisted payment-attempt ID, reused on retries | New attempt after a decline → new row, new key |
| Money in the database | Integer minor units + ISO currency code | No exceptions |
| Subscription management | Hosted checkout, provider customer portal, webhook-synced mirror | Seat management in-app or unusual plans → custom UI calling the provider API |
| Upgrade / downgrade | Upgrade now with prorated charge; downgrade and cancel at period end, no refund | User states another policy |
| Failed renewal | Provider smart retries and dunning emails; full access during retries, then free tier, data kept | |
| Trial | No card, one per account | Card-up-front when conversion matters more than sign-ups; then send a pre-charge reminder |
| Usage billing | Not at Prototype. Own append-only usage events as system of record, provider for invoicing | |
| Tax | Tax engine in monitoring mode from the first sale; register before collecting | Merchant of record removes this |
| Invoice correction | Credit note plus new invoice | Draft invoices can be edited |
| Fraud controls | Provider defaults, velocity rules, bot challenge and auth on payment endpoints | Custom rules once losses or false declines are measurable |
| Ledger | Mirrored provider objects and an event log | App holds balances (credits, wallets, seller earnings) → immutable double-entry ledger |
| Commerce | Hosted platform for physical goods; provider products and checkout for a handful of digital items | Unusual sellable unit (slots, seats, rentals) → custom model |
| Second processor | Skip until Scale; keep a dormant second account and a cash buffer outside the processor | Borderline business category → earlier |

By stage:

- **Prototype**: hosted checkout, one webhook handler with signature check and event dedupe,
  provider IDs on the account. Test mode only until the flow is right. Skip tax, ledger, dunning
  tuning and usage billing.
- **Launch**: everything in "Before you call it done"; daily reconciliation; tax decision made;
  refund policy published; dispute and webhook-failure alerts; lifecycle tests on simulated
  clocks.
- **Scale**: payout-level reconciliation and accounting export, fraud-rule tuning with data,
  authorization-rate work, double-entry ledger, processor redundancy, negotiated pricing.

## Before you call it done

1. No amount, price or currency is accepted from the client; totals are computed server-side
   from IDs, and the displayed total equals the charged total and the invoice total.
2. No card number or CVC reaches the app's servers, logs or error tracker; payment fields are
   provider-hosted.
3. The webhook endpoint verifies the signature on the raw body, dedupes on event ID with a
   unique constraint, returns 2xx quickly, and its failures raise an alert.
4. Handlers fetch current provider state and upsert; delivering the same event twice and
   delivering events out of order both leave the database correct (tested).
5. Every provider call that creates or moves money sends an idempotency key persisted before
   the call; a timeout leads to the unknown-outcome path, not to a new charge.
6. Double submit, reload, back button and a second tab cannot produce two fulfilled payments
   for one order; a database constraint enforces it, and a stray second payment is refunded.
7. Every provider payment state is mapped, including requires-action, processing and delayed
   failure; 3-D Secure and one delayed method were exercised in test mode.
8. Every decline and error code maps to a customer message with a next action, with a default
   branch; fraud-related reasons are not revealed.
9. Each outcome path ends on a reloadable page with an order reference, and exactly one receipt
   is sent.
10. Subscription status maps explicitly to access, including past-due grace, paused and
    canceled-at-period-end; entitlement checks read local state only.
11. Trial end, renewal failure and recovery, upgrade, downgrade, cancel and reactivate were run
    on the provider's simulated clock with assertions on entitlements.
12. Refunds are capped at the captured amount under a lock, update entitlements, and produce a
    credit note; disputes open a ticket with the deadline and suspend the account.
13. A scheduled reconciliation job compares provider and database, repairs through the sync
    function, records its result and alerts when it fails or finds unresolved items.
14. Live and test keys and webhook secrets are separate, live keys are restricted to what the
    app needs, and no secret is in the client bundle or the repository.
15. The tax decision is recorded (merchant of record, or engine plus registrations), and
    invoices carry the legal entity, tax IDs and sequential numbers.

## Not this skill

- What to charge, plan design and pricing strategy → `0x:pricing-monetization`
- Generic webhook and idempotency-key mechanics → `0x:api-design`
- PCI DSS scope, SAQ and consumer-law rules on renewal and cancellation → `0x:privacy-compliance`
- Bookkeeping, revenue recognition and tax filing → `0x:startup-finance`
- Cancellation save offers and churn reduction → `0x:sales-support`
- Checkout page conversion experiments → `0x:product-analytics`
