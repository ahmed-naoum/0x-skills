# Payment provider and checkout integration

Read this when: choosing a payment provider, or wiring a payment flow end to end, from the pay
button to confirmed state in the database. Also when a payment "succeeded but the order is not
paid", or a customer was charged twice.

## Choosing a provider

Decide in this order; the first question that produces a hard "no" ends the evaluation.

1. **Can the business open and keep an account?** Check the provider's supported countries for
   the legal entity, and its restricted-business list for the product. A provider that later
   decides the business is out of policy freezes payouts; that risk outweighs any fee difference.
2. **Who is the seller of record?** A payment processor (Stripe, Adyen, Braintree) moves money
   and the business is the seller, liable for tax in every place it sells. A merchant of record
   (Paddle, Lemon Squeezy, Polar) is the legal seller, resells the product, and takes on tax,
   invoices and most dispute handling for a higher percentage. See `invoices-tax.md`.
3. **Payment methods the buyers actually use.** Cards cover the US and UK well. Elsewhere a
   missing local method costs more conversion than any fee saves (table below).
4. **Payout terms.** Payout delay, rolling reserve, minimum payout, payout currencies and whether
   the first payout is held longer. Cash-flow-sensitive businesses (physical goods bought up
   front, marketplaces) feel this more than the fee.
5. **Fees, in full.** Compare the blended rate on the real mix: domestic vs international
   cards, currency conversion, dispute fee, refund policy on the original fee (many processors
   keep it), billing or tax add-ons charged as a percent of volume. Quote current rates from the
   pricing page at decision time; they change.

| Situation | Default |
|---|---|
| SaaS or digital product, founder willing to own tax (or US-only at first) | Stripe: Checkout + Billing + Tax |
| Selling to consumers in many countries, founder wants no tax work | Merchant of record |
| Entity in a country Stripe does not support | Merchant of record, or a locally supported processor |
| Physical goods store | The commerce platform's built-in payments (see `commerce.md`) |
| Marketplace paying out to sellers | Stripe Connect or equivalent (see `ledger-reconciliation.md`) |
| High-risk category (adult, gambling, nutraceuticals, crypto, travel) | A specialist high-risk processor; mainstream ones close such accounts |

Negotiated interchange-plus pricing and direct acquirer relationships are Scale topics; below
meaningful volume nobody will negotiate.

## Integration surface: keep card data off the servers

| Surface | Use when | Cost |
|---|---|---|
| Hosted checkout page (Stripe Checkout, Paddle overlay) | Default at Prototype and Launch | Least control of layout |
| Embedded hosted checkout (iframe on own page) | The page must stay on the product's domain | Slightly more wiring |
| Provider-hosted fields (Payment Element) + PaymentIntents | Custom multi-step checkout, cart UIs, Scale | Own the state machine, errors, 3DS handling |
| Raw card numbers posted to own server | Not an option | Full PCI scope; do not build it |

Hosted pages and provider iframes keep the business in the lightest PCI self-assessment
category; the scope rules themselves belong to `0x:privacy-compliance`. Two rules follow
regardless of surface: card numbers, CVC and full magnetic data never appear in the app's
requests, logs, error tracker or support tools; and the page that hosts the provider script has
a tight CSP and no third-party scripts that can read the DOM around the fields.

Hosted checkout also brings wallets, local methods, 3-D Secure, tax display, coupons and saved
cards without code. Move to Payment Element only when a concrete requirement cannot be met.

## Create the payment on the server, from IDs

The client sends *what* is being bought (price or product IDs, quantities, coupon code). The
server looks up amounts, computes the total and creates the payment. An amount, currency or
"total" field accepted from the browser is a price-tampering bug.

```ts
const session = await stripe.checkout.sessions.create(
  {
    mode: "payment",
    line_items: [{ price: plan.stripePriceId, quantity: 1 }],
    client_reference_id: order.id,
    metadata: { order_id: order.id },
    success_url: `${origin}/orders/${order.id}?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${origin}/cart`,
  },
  { idempotencyKey: `checkout:${attempt.id}` },
);
```

- Create the local `order` (status `pending`) and a `payment_attempt` row *before* calling the
  provider, and put the order ID in the provider object's metadata. The webhook then has a
  deterministic way back to the row, and a crash between the two leaves a pending order, which
  is harmless, instead of a charge with no order.
- For subscriptions also set metadata on the subscription itself (`subscription_data.metadata`);
  session metadata does not propagate to later invoices.
- Authenticate the caller and derive the customer from the session, never from a client-sent
  customer ID. One provider customer per account, stored in a column with a unique constraint.
- Validate entitlement to the price server-side: a hidden or legacy price ID sent by a client
  must be rejected, not charged.
- Store amounts as integers in the currency's minor unit, with the currency next to them. Not
  every currency has two decimals (JPY has none; some have three); use the provider's table.

## The webhook is the source of truth

The success redirect proves only that a browser reached a URL. Customers close the tab, lose
signal, or pay by a method that confirms hours later; a redirect can also be replayed. Fulfil
(grant access, mark paid, ship) only from a verified webhook or from a server-side fetch of the
provider object.

```ts
export async function POST(req: Request) {
  const body = await req.text(); // raw bytes: parsing first breaks the signature
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body, req.headers.get("stripe-signature")!, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return new Response("invalid signature", { status: 400 });
  }
  // insert event.id into processed_events (unique); on conflict, return 200
  // enqueue or handle; return 2xx fast
  return new Response(null, { status: 200 });
}
```

Rules that prevent the usual incidents:

- **Dedupe on event ID** with a unique constraint; providers deliver at least once.
- **Do not rely on order.** `customer.subscription.updated` can arrive before `created`. Make
  handlers converge: fetch the current object from the API and upsert its state, instead of
  applying the event payload as a delta.
- **Fulfilment is idempotent and transactional**: `update orders set status = 'paid' where id =
  $1 and status = 'pending'`, and do the side effects only if a row changed.
- **Return 2xx fast; do slow work in a job.** A handler that times out is retried, and after
  enough failures the provider disables the endpoint. Alert on webhook failure rate.
- **The success page may fulfil too**, through the same idempotent function, by retrieving the
  session server-side. That removes the "paid but no access for a few seconds" gap without
  trusting the redirect. If the object is not yet paid, show "confirming payment" and poll the
  app's own order status.
- **Backstop with reconciliation.** A scheduled job lists recent provider payments and repairs
  any order still pending (see `ledger-reconciliation.md`). Webhooks get lost during deploys
  and outages.
- Separate endpoint secrets for test and live; pin the API version of the webhook endpoint so a
  dashboard upgrade does not change payload shapes under the handler.

Events to handle for one-time payments with Stripe Checkout: `checkout.session.completed`
(check `payment_status`: it is `unpaid` for delayed methods), `checkout.session.async_payment_succeeded`,
`checkout.session.async_payment_failed`, `checkout.session.expired`, `charge.refunded`,
`charge.dispute.created`. Generic signature and retry mechanics: `0x:api-design` (`webhooks.md`).

## One attempt, one idempotency key, one charge

An idempotency key tells the provider "this is the same request as before; return the first
result". Generate it per *payment attempt*, persist it before the call, and reuse it on every
retry of that attempt.

- Key = the `payment_attempt` row ID (or a UUID stored on it). A key generated inside the retry
  loop, or from a timestamp, protects nothing.
- A new attempt (customer changed card after a decline) gets a new row and a new key. Reusing a
  key with different parameters is an error by design.
- Keys expire on the provider side (on the order of a day for Stripe). After that the key no
  longer protects; query instead of retrying.
- The provider key covers the provider call only. The app's own endpoint needs its own guard,
  below.

## Reload, back button, double click, second tab

| Vector | Guard |
|---|---|
| Double click, impatient resubmit | Disable the button on submit; server takes a row lock or uses a unique constraint on the open attempt |
| Reload of a POST result page | Post/redirect/get: respond with a redirect to an order URL that only reads state |
| Back button after paying | The checkout route loads the order first; if it is `paid` or `processing`, redirect to the confirmation page |
| Second tab or device | One open checkout session per order: return the existing session URL if still open; expire superseded sessions via the API |
| Two sessions both paid anyway | Webhook sees a payment for an already-paid order: record it, refund it automatically, alert |

The database is the final guard: a partial unique index allowing one succeeded payment per
order (see `ledger-reconciliation.md`). UI guards reduce frequency; only the constraint makes a
double fulfilment impossible, and the auto-refund path handles the double charge that slipped
through at the provider.

## 3-D Secure and asynchronous states

A payment is a state machine, not a boolean. Map every provider state; do not collapse unknown
states to "failed".

| Provider state (Stripe PaymentIntent) | Meaning | App behavior |
|---|---|---|
| `requires_payment_method` | Not attempted, or last attempt failed | Let the customer try again; show the decline message |
| `requires_action` | Customer must authenticate (3DS, bank redirect, voucher) | Hand control to the provider SDK; order stays pending |
| `processing` | Submitted, outcome not known (bank debits, some wallets) | "Payment received, confirming"; do not fulfil unless policy allows |
| `requires_capture` | Authorized, not captured | Capture before the authorization expires (about a week for cards; check the provider) |
| `succeeded` | Money is coming | Fulfil |
| `canceled` | Abandoned or voided | Release stock, close the order |

- In Europe and the UK, strong customer authentication applies to most customer-initiated card
  payments. Hosted checkout handles the challenge. With hosted fields, call the SDK's confirm
  function and handle its redirect return; the return URL must re-read state from the server.
- **Off-session charges** (renewals, usage top-ups) need the card saved with the intent to
  reuse it (`setup_future_usage: "off_session"` or a SetupIntent), which records the mandate.
  When an off-session charge still demands authentication, the charge fails with an
  authentication-required error: email the customer a link to complete it on-session.
- **Delayed methods** (SEPA and ACH debit, bank transfers, vouchers) succeed or fail days later,
  and debits can be returned after success. Decide per product: grant access at `processing`
  for low-cost digital goods and revoke on failure, or wait for `succeeded` for anything
  shippable or resellable.
- Separate authorization and capture only when needed (ship-then-charge, variable final
  amount). An uncaptured authorization that expires is lost revenue with no error anywhere.

## Unknown outcome after a timeout

A timeout or 5xx on a create or confirm call means the outcome is unknown, not failed. Creating a
fresh payment at this point is how customers get charged twice.

1. Retry the *same* request with the *same* idempotency key, with backoff. The official SDKs do
   this for network errors when retries are enabled; confirm the setting rather than assume it.
2. If still unknown, mark the attempt `unknown`, tell the customer "we are confirming your
   payment, do not pay again", and let them leave.
3. A job resolves it: retrieve the provider object by its ID if one was stored, otherwise search
   by the order ID in metadata. Found and succeeded → fulfil. Found and failed, or not found
   after the key's lifetime → mark failed and invite a retry with a new attempt.
4. The webhook may resolve it first; both paths call the same idempotent fulfilment function.

Set an explicit client timeout on provider calls (tens of seconds, above the provider's own
processing time) so a hung request becomes a handled `unknown` instead of a platform kill.

## Wallets and local payment methods

Wallets raise mobile conversion more than any other single change, because the customer types
nothing. Turn them on at Launch.

- Prefer the provider's dynamic method selection (dashboard-controlled, chosen by currency,
  country and device) over a hard-coded method list; a hard-coded list silently hides every
  method added later.
- Apple Pay on the web requires the domain to be registered with the provider when the fields
  run on the product's own domain; a provider-hosted page needs nothing. Wallets appear only
  when the device has a card provisioned, so test on real devices.
- A method is offered only if the presentment currency matches (iDEAL needs EUR, Pix needs
  BRL). Charging everyone in USD removes most local methods.

| Market | Methods worth enabling beyond cards and wallets |
|---|---|
| Netherlands | iDEAL |
| Belgium | Bancontact |
| Germany, Austria | SEPA Direct Debit, PayPal, buy-now-pay-later for goods |
| Poland | BLIK |
| Brazil | Pix (and installments on cards) |
| India | UPI |
| US B2B, large invoices | ACH debit or bank transfer |

Know each method's properties before enabling it: whether it confirms instantly, whether it
supports recurring charges, its refund path, and its dispute window (bank debits can be
reversed by the payer for weeks with little recourse).

## A second processor

Skip until Scale, with two exceptions: the business category is borderline for the primary
provider, or a single country's outage or decline rate is already costing measurable revenue.

- Cheap insurance at Launch: keep a second account approved and dormant (PayPal or another
  processor), keep a bank buffer outside the processor, and know the provider's data-export
  path. Processors migrate vaulted cards to another PCI-compliant processor on request; it takes
  weeks, so it is a recovery path, not failover.
- Real redundancy needs **portable tokens**: card data vaulted independently of either processor
  (a PCI vault or orchestration layer, or network tokens that the business controls), plus an
  internal payments interface so the app does not call one vendor's API from everywhere.
- Subscription logic inside one provider's billing product is the hard lock-in. A second
  processor then means running billing logic in-house or in a processor-neutral billing system.
- Route by rule (currency, country, card brand), not by blind failover: retrying a hard decline
  on another processor wastes fees and looks like fraud to issuers.

## Ask the user

- **Which countries is the company registered in and selling to?** It decides which providers
  are available and which local methods matter. Default: Stripe if the entity's country is
  supported, cards and wallets only at first.
- **Do you want to handle sales tax and VAT yourself?** If no, default to a merchant of record
  and accept the higher fee.
- **For slow payment methods (bank debits), should access start before the money is confirmed?**
  Default: yes for low-cost digital access, no for physical goods and anything transferable.
- **Is the product in a category payment providers restrict?** Check the list before
  integrating. Default: assume not, but read the restricted-business page once.
- **Charge at order time or at shipment?** Default: charge at order time; authorize-then-capture
  only where law or the business model requires it.
