# Checkout experience and payment errors

Read this when: designing or fixing what the customer sees while paying: totals, error and
decline messages, confirmation pages and receipts, abandoned-checkout recovery, or when the
question is why payments fail and how to raise the share that succeed.

## Show the real total before commitment

The amount on the pay button must equal the amount charged. Every surprise between the pricing
page and the card statement becomes an abandoned checkout or, later, a dispute.

- **Currency**: show the currency the charge will be made in, with its ISO code where the symbol
  is ambiguous (`$` is used by many currencies). Format with `Intl.NumberFormat` using the
  customer's locale and the charge currency; never format by string concatenation.
- **Tax**: consumers in the EU, UK, Australia and most of the world expect tax-inclusive
  prices, and consumer law in many places requires it. US buyers expect tax added at checkout.
  B2B buyers everywhere expect net prices with tax as a separate line. Decide inclusive or
  exclusive per market and state it next to the price ("incl. VAT", "plus tax").
- **Tax needs a location.** Collect country (and postal code where rates vary by region, as in
  the US and Canada) before showing the total, and recompute when it changes. Compute tax with
  the same engine that will charge it; a client-side estimate that differs by a cent produces
  support mail.
- **Recurring terms on the same screen as the button**: amount, interval, when the trial ends
  and what is charged then, and that it renews until canceled. Card networks and consumer rules
  both expect this; the legal detail is in `0x:privacy-compliance`.
- **Line items**: subtotal, discount (with the code applied), shipping, tax, total. For plan
  changes show the prorated amount due today and the next renewal amount and date.
- Local currency pricing is a decision, not a formatting step: either explicit prices per
  currency or the provider's automatic conversion at checkout (see `invoices-tax.md`). Do not
  display converted prices and then charge in the base currency.

Check: for three test customers (US, Germany consumer, Germany business with VAT ID) the
displayed total, the provider's charged amount and the invoice total are identical.

## Errors and declines: every code leads to an action

Failures fall into classes that need different treatment. Keep the provider's code in the logs
and on the payment attempt row; show the customer a mapped message. With Stripe, read the
error `code` first and, when it is `card_declined`, the `decline_code` for the reason; a few
reasons (`expired_card`, `incorrect_cvc`, `incorrect_number`, `processing_error`) arrive as
the `code` itself. Whether the issuer or the provider's risk engine refused is on the charge
(`outcome.type` of `issuer_declined` or `blocked`).

| Class | Examples (Stripe codes) | Customer sees | System does |
|---|---|---|---|
| Customer-fixable input | `incorrect_number`, `incorrect_cvc`, `expired_card`, `incorrect_zip` | The specific field problem, inline on the field | Keep the form filled; allow immediate retry |
| Customer-fixable funds or limits | `insufficient_funds`, `card_velocity_exceeded`, `withdrawal_count_limit_exceeded` | "The card was declined for insufficient funds. Try another card or payment method." | Offer other methods prominently |
| Authentication | `authentication_required`, abandoned or failed 3DS | "Your bank needs you to confirm this payment." with a button to retry authentication | Re-run confirmation on-session |
| Issuer refused, no reason | `generic_decline`, `do_not_honor`, `transaction_not_allowed` | "Your bank declined the payment. Try another card, or contact your bank." | No automatic retry with the same card |
| Suspected fraud or lost card | `fraudulent`, `lost_card`, `stolen_card`, `pickup_card`, blocked by fraud rules | The same generic decline message | Never reveal the reason: it teaches card testers which cards are live. Log and count |
| Method unsupported | `card_not_supported`, `currency_not_supported` | "This card cannot be used for this purchase. Try another." | Check whether the method list is wrong for the market |
| Transient | `processing_error`, `issuer_not_available`, `try_again_later`, provider 5xx, timeouts | "Something went wrong on our side. You have not been charged." only if that is known; otherwise "We are confirming your payment" | Idempotent retry or the unknown-outcome path in `checkout-integration.md` |
| Integration bug | invalid request, auth error, rate limit | Generic apology with a reference ID | Page the developer: these are never the customer's fault |

Rules:

- **Unknown codes get the generic decline message and an alert**, not a stack trace or a raw
  provider string. Providers add codes; the mapping needs a default branch.
- Never say "you have not been charged" unless the state is known. After a timeout the honest
  message is that the payment is being confirmed.
- An authorization can appear as a pending line on the customer's statement even when the
  payment failed or was voided. Say so in the failure copy and in the support macro: "any
  pending charge will disappear within a few days".
- Put the error where the eye is: next to the pay button and in an `aria-live` region; keep
  focus management and field semantics per `0x:accessibility`.
- Preserve everything typed. A decline that clears the form makes a second attempt much less
  likely; only the card fields, which the provider owns, may reset.
- Offer a different method after the first decline, not after the third.
- Rate-limit attempts per session, account and card fingerprint; unlimited retries are a
  card-testing surface (see `refunds-disputes-fraud.md`).

## Confirmation on every outcome path

Every path ends on a page with a stable URL that reads state from the server and can be
reloaded, bookmarked and opened on another device after sign-in.

| Outcome | Page shows | Also sent |
|---|---|---|
| Paid | Order or invoice number, what was bought, amount and currency, payment method last four, what happens next and when (access now, ships by date), link to the receipt and to manage the purchase | Receipt email within a minute |
| Confirming (async method, webhook not yet in) | "Payment received, confirming", order number, that an email follows, no second pay button | Email when confirmed or failed |
| Action pending (voucher, bank transfer) | The payment instructions, reference, amount, deadline | The same instructions by email |
| Failed | What failed in plain words, that no money was taken (or that a pending hold will drop), a retry button that reuses the order | Nothing, or one recovery email (below) |
| Canceled by customer | The cart, intact | Nothing |

- The order number shown is the one support can search for. Do not expose the provider's
  internal IDs as the primary reference, but store them next to it.
- The receipt email is transactional: it is sent regardless of marketing consent, from the
  webhook-driven fulfillment function so it is sent exactly once. Either the provider's receipt
  or the app's, not both. Delivery setup: `0x:email-notifications`.
- The confirmation page must not re-trigger fulfillment or analytics purchase events on reload:
  fire the conversion event once, keyed on the order ID.
- For subscriptions, state the next charge date and amount and where to cancel. Customers who
  cannot find the cancel path use their bank instead.

## Monitoring conversion and declines

Aggregate rates hide the failures that matter. Track these, split by payment method, card
country, currency, device and new vs returning customer:

| Metric | Definition | Signal |
|---|---|---|
| Checkout conversion | Paid orders ÷ checkout sessions started | Drop after a deploy → integration or UI bug |
| Authorization rate | Approved ÷ attempted charges (exclude blocked-by-own-rules) | Drop in one country or brand → issuer or routing issue |
| Decline mix | Share of each decline code | Rise in `do_not_honor` from one country → issuer distrust; rise in input errors → form bug |
| 3DS challenge and completion rate | Challenged ÷ attempts; completed ÷ challenged | Low completion → broken redirect or return URL |
| Method share | Payments by method per country | A local method at zero share where it should be popular → not displayed |
| Time to confirmation | Payment success to fulfillment | Webhook lag or failures |

Instrumentation: emit one server-side event per payment attempt with the outcome, decline code,
method, card country and amount, from the same code that updates the attempt row. Client-side
funnel events (viewed checkout, submitted) come from product analytics; funnel design and
experiments belong to `0x:product-analytics`.

Alerts worth having at Launch: zero successful payments for N minutes during hours that
normally have some; authorization rate below a floor over a sliding window; webhook endpoint
failures; a spike in attempt count without a matching rise in successes (card testing).

Baselines differ so much by market, method and business model that an absolute "good"
authorization rate is not transferable; compare against the product's own trailing weeks, and
card-not-present recurring charges against one-time charges separately.

## Recovering abandoned checkouts

Skip at Prototype. At Launch, do saved carts and the failed-payment message; add reminder
emails once consent is collected and there is enough volume to see their effect.

- **Saved carts first.** The cart persists server-side against the account or a long-lived
  cart token, so returning shows the same items (see `commerce.md`). A recovery link without a
  saved cart is a link to an empty page.
- **Capture the email early**, as the first field, and store it with the pending order. Without
  an address there is nothing to recover.
- **Consent decides what may be sent.** A reminder about an unfinished purchase is marketing in
  most privacy regimes unless the customer agreed or a soft opt-in applies. Collect consent at
  the email field, or limit the message to a strictly service-related notice; the rules are in
  `0x:privacy-compliance`. Some hosted checkouts can show a promotional-consent checkbox and
  hand back a recovery URL when the session expires (Stripe: `consent_collection.promotions`
  and `after_expiration.recovery`, the URL arriving on `checkout.session.expired`). The
  consent option is not offered in every country, so confirm it before designing around it.
- **Sequence** (rule of thumb): one reminder about an hour after abandonment, one the next day,
  then stop. The link restores the exact cart and price; if the price or stock changed, say so
  on landing. Suppress immediately once the order is paid, on any device.
- **Do not lead with a discount.** Customers learn to abandon on purpose. Use a discount only in
  the last message, if at all, with a single-use code.
- A failed payment is a different case from an abandoned cart: the intent is proven. One
  message with the failure reason in plain words and a link that retries the same order
  recovers more than any cart reminder.
- Expire stale checkout sessions and release reserved stock when they expire.

## Raising authorization rate

Expert territory; most of the gain comes from a few moves, in this order of payoff.

1. **Stop self-inflicted declines.** Review the provider's fraud rules: an overly strict rule
   blocks good customers silently. Measure blocked-by-rule separately from issuer declines
   (see `refunds-disputes-fraud.md`).
2. **Send complete data.** Postal code and CVC on first charges, the customer's name and email,
   a correct statement descriptor, and the right flags for stored-credential and
   merchant-initiated transactions. Issuers score on these; missing data lowers approval.
3. **Authenticate when it helps.** In regions with mandated authentication, a charge sent
   without it is soft-declined and must be re-run with a challenge; let the provider's
   authentication engine request exemptions rather than forcing 3DS on every charge, which
   costs conversion where it is not required.
4. **Keep credentials fresh.** Enable network tokens and the card account updater where the
   provider offers them; they replace expired and reissued cards without customer action.
5. **Order methods by local preference.** Put the wallet and the dominant local method first on
   mobile; cards first only where cards dominate. Let the provider's ordering optimize unless
   data from the product shows otherwise.
6. **Retry by decline class.**

| Decline class | Retry policy |
|---|---|
| Hard: stolen, lost, closed account, invalid number, "do not try again" | Never retry. Networks charge for repeated attempts on dead credentials, and the attempts erode issuer trust in the merchant |
| Soft: insufficient funds, generic decline, issuer unavailable | Retry on a schedule, not immediately (rule of thumb: after a day, then spaced over one to two weeks, at a different time of day and near common paydays) |
| Authentication required | Do not retry off-session; bring the customer on-session |
| Technical: timeout, processing error | Idempotent retry within seconds to minutes |

   Card networks cap how many times one declined transaction may be reattempted (on the
   order of tens of attempts per card in 30 days, and none after a "do not retry" response)
   and charge a fee per excess attempt. The limits differ by network and have changed, so
   read the processor's current excessive-retry page. The provider's built-in retry logic
   respects the caps; a hand-rolled cron does not. Use the provider's smart retries for
   subscriptions before building anything (see `subscriptions.md`).
7. **Local acquiring** (charging through an entity in the cardholder's country) raises approval
   for cross-border volume. It needs local entities and is a Scale decision.

Skip until Scale: multi-acquirer routing, issuer-level analysis, custom retry models. At Launch
do steps 1, 2, 4 and the provider's default retries, and measure.

## Ask the user

- **Are prices shown with tax included or added at checkout?** It changes margins and what
  consumers expect. Default: inclusive for consumer sales outside North America, exclusive for
  the US, Canada and all B2B.
- **Which currencies to charge in?** Default: one base currency at Prototype; add the buyer's
  currency for the top two or three markets at Launch.
- **May the product email people who started checkout but did not pay?** It depends on consent
  and jurisdiction. Default: only where the customer ticked a consent box or a soft opt-in
  clearly applies; otherwise no reminder.
- **Who sends receipts: the provider or the app?** Default: the provider's receipt at Prototype
  and Launch, branded; the app's own once invoices need custom content.
- **What should support be able to see about a failed payment?** Default: order, attempts,
  decline code and mapped message; never card numbers.
