# Subscriptions and entitlements

Read this when: implementing recurring billing: sign-up, trials, upgrades and downgrades,
cancel and pause, failed renewals, seats and add-ons, moving customers to new prices, or
deciding what a customer is allowed to use at any moment.

## The shape that works for a small team

Let the provider own the billing state machine; own only a mirror of it and the entitlements
derived from it.

| Piece | Who owns it | Notes |
|---|---|---|
| Sign-up payment | Hosted checkout in subscription mode | One provider customer per account or workspace, created once |
| Card updates, invoices, cancel, plan switch | Provider's customer portal | Configure which plans can be switched to and whether cancel is immediate or at period end |
| Renewals, retries, proration, tax | Provider billing engine | Do not run a renewal cron |
| Subscription mirror | App database, written only by the webhook sync | Columns below |
| What the customer may use | Entitlements layer in the app | Derived from the mirror plus overrides |

Build custom plan-change UI only when the portal cannot express the product (seat management
inside the app is the usual first case). Even then, call the provider's API and wait for the
webhook; do not write subscription state directly from the request handler.

Mirror, per subscription: provider customer ID, subscription ID (unique), status, price or plan
key, quantity, `current_period_end`, `cancel_at_period_end`, `trial_end`, pause state, and the
provider's last-updated time. Bill the workspace or organization, not the individual user, if
the product has teams; moving a subscription between owners later is painful.

## One sync function, called from every event

```ts
// Called for every subscription-related event and from the checkout success page.
async function syncSubscription(stripeSubscriptionId: string) {
  const sub = await stripe.subscriptions.retrieve(stripeSubscriptionId);
  await db.upsertSubscriptionMirror(sub);       // keyed on sub.id
  await recomputeEntitlements(sub.metadata.account_id);
}
```

Fetching the current object and upserting makes event order and duplicates irrelevant. Applying
event payloads as deltas does not, because events arrive out of order.

Events to subscribe to (Stripe names; other providers have equivalents):

| Event | Why |
|---|---|
| `checkout.session.completed` | Links the new subscription and customer to the account |
| `customer.subscription.created` / `.updated` / `.deleted` | Every status, plan, quantity and cancel-flag change |
| `invoice.paid` | Renewal succeeded; extend access, record revenue |
| `invoice.payment_failed` | Start dunning communication |
| `invoice.payment_action_required` | Renewal needs customer authentication; email a link |
| `customer.subscription.trial_will_end` | Sent a few days before trial end; send the reminder |
| `charge.refunded`, `charge.dispute.created` | Access decisions, see `refunds-disputes-fraud.md` |

A nightly job re-syncs every non-terminal subscription from the provider as a backstop. "Paid
but no access" tickets are almost always a missed or failed webhook; the job turns them into a
self-healing delay.

## Status to access

| Provider status (Stripe) | Meaning | Access |
|---|---|---|
| `trialing` | In trial | Full plan access |
| `active` | Paid up (also when collection is paused) | Full |
| `incomplete` | First payment not yet completed (3DS or failure) | None; prompt to finish payment |
| `incomplete_expired` | First payment never completed within the provider's window | None; treat as never subscribed |
| `past_due` | A renewal failed; retries in progress | Full during a grace period, with a banner |
| `unpaid` | Retries exhausted, subscription kept open | Restricted: read-only or export-only |
| `paused` | Trial ended without a payment method, where configured | None or free tier |
| `canceled` | Ended | Free tier; keep the data for a stated retention period |

Decide the grace period explicitly; the default is to keep full access while the provider's
retry schedule runs (commonly one to three weeks), then downgrade. Cutting access on the first
failed charge punishes expired cards; never cutting it gives the product away. Keep
`current_period_end` out of access checks for `active` subscriptions: the renewal webhook can
lag the timestamp by minutes to hours, so status decides and the date is display only.

## Trials

| Trial type | Mechanics | Trade-off |
|---|---|---|
| No card, in the app only | No provider subscription until conversion; `trial_ends_at` on the account | Most sign-ups, lower conversion, no involuntary charges |
| No card, provider subscription | Subscription with a trial and payment method optional; set the end behavior to cancel or pause when no method exists | Billing data from day one |
| Card up front | Checkout collects the card, first charge at trial end | Fewer sign-ups, higher conversion, more disputes without a reminder |

With card-up-front trials, send a reminder before the first charge stating amount and date,
and make cancel one click. Card networks require specific disclosures and reminders for trials
that convert to paid, and surprise trial charges are a leading dispute source. Prevent trial
farming with one trial per account and per payment-method fingerprint, not per email.

## Plan changes

| Change | Default behavior | Why |
|---|---|---|
| Upgrade | Immediately; charge the prorated difference now | The customer wants the feature now; deferring the charge to the next invoice loses it when the card fails |
| Downgrade | At period end, no refund; schedule the change | Avoids refunds and credit balances; the customer keeps what was paid for |
| Monthly → annual | Immediately; credit unused time, start a new period now | Billing anchor resets |
| Annual → monthly | At period end | Avoids a large prorated refund |
| Quantity up (seats) | Immediately, prorated | See seats |
| Quantity down | At period end | Same reasoning as downgrade |

- State the proration behavior on every update call instead of relying on the account default
  (Stripe: `proration_behavior` of `always_invoice` to charge now, `create_prorations` to add to
  the next invoice, `none`). Show the customer the amount first using the provider's invoice
  preview endpoint; never compute proration by hand in the UI.
- An upgrade whose immediate payment fails must not leave the customer on the higher plan.
  Use the provider option that keeps the old state until payment succeeds, or roll back on
  failure, and test this path.
- Scheduled changes (Stripe subscription schedules, or a `pending_plan` column applied on the
  renewal event) must be visible in the UI: "Changes to Basic on 3 March".
- Downgrades can leave the account over the new plan's limits. Decide per limit: block the
  downgrade until usage fits, or allow it and make the excess read-only. Never delete data.

## Cancel, pause, reactivate

| Action | Billing | Access |
|---|---|---|
| Cancel (default) | Set cancel-at-period-end | Full until `current_period_end`, then free tier |
| Cancel immediately | Cancel now; refund per policy | Ends now |
| Undo cancel before period end | Clear the cancel flag | Unchanged; no new charge |
| Resubscribe after end | New checkout, new subscription on the same customer | Restored; data still there if within retention |
| Pause | Pause collection or schedule a resume date | Product decision: none or read-only |
| Resume | Clear the pause; next invoice on the normal date or now | Restored |

- Cancellation must be as easy as sign-up and reachable in the product; several jurisdictions
  require this, see `0x:privacy-compliance`. Save offers belong to `0x:sales-support`.
- Trap: with Stripe's pause-collection feature the subscription status stays `active`. Read the
  pause field in the sync and map it to access explicitly.
- The cancel flag is state to display: show "Cancels on <date>" and a reactivate button.
- Deleting an account must cancel its subscription at the provider in the same operation;
  orphaned subscriptions keep charging and end as disputes.

## Entitlements: a layer of their own

Feature code asks one question, `can(account, "feature")` or `limit(account, "seats")`, and
never reads plan names or provider status.

- A plan-to-entitlements map in code or a table: `pro → { projects: 50, sso: false }`. Grandfathered
  plans keep their own row, so changing today's Pro does not change old customers.
- Per-account overrides with an expiry and a reason: sales deals, support gestures, beta access,
  compensation after an incident. Without overrides, the first enterprise customer forces plan
  logic into feature code.
- Effective entitlements = plan entitlements from the mirror, adjusted by status (table above),
  then overrides. Recompute on every sync; cache per account; invalidate on recompute.
- Enforce on the server at the point of use. A hidden button is not enforcement.
- Billing outages must not lock customers out: entitlement checks read the local mirror and
  never call the provider in the request path.

Provider-side entitlement features exist and are fine as the plan map's source; the override and
status logic still lives in the app.

## Failed renewals

Involuntary churn from failed cards is commonly a large share of total churn in subscription
businesses and is the cheapest to recover. Configure, in this order:

1. **Provider smart retries**, with the schedule spread over two to three weeks. Do not write a
   retry cron; network retry caps and hard-decline rules are easy to violate.
2. **Card account updater and network tokens**, on by default with some providers; verify.
3. **Dunning emails**: on first failure (reason in plain words, link to update the card), midway,
   and a final notice before downgrade. The link goes to the portal's payment-method page or a
   hosted invoice page, signed in or tokenized, one click.
4. **In-app banner** for `past_due`, visible to billing admins.
5. **Pre-dunning**: email before a card expires and before annual renewals; annual renewals fail
   and get disputed more because the customer forgot.
6. **End state**: after the last retry, mark `unpaid` or cancel, downgrade to free, keep data,
   and make paying the open invoice restore access immediately.

Authentication-required failures on renewals need the customer on-session; retries cannot fix
them. Measure recovery rate (recovered ÷ failed invoices) monthly.

## Seats, add-ons, annual plans

- **Seats**: subscription quantity = billable seats. Decide and document what a billable seat
  is (active members, not pending invites, is the usual choice). Adding a seat updates quantity
  with proration; removing seats takes effect at renewal. Serialize quantity updates per
  account (row lock or job queue): two concurrent invites otherwise both read N and write N+1.
- **Add-ons**: extra subscription items on the same subscription, each with its own price and
  quantity, so there is one invoice and one renewal date. Entitlements sum across items.
- **Annual**: a separate price per plan with the yearly interval. Decide the refund policy for
  mid-term cancellation before the first sale (default: no prorated refund, access to term
  end, case-by-case exceptions). Send a renewal reminder ahead of the charge; some jurisdictions
  require it.
- One subscription per account. Multiple subscriptions per customer multiply every edge case.

## Testing lifecycles with simulated clocks

Renewals, trial endings and dunning cannot be tested by waiting. Use the provider's time
simulation (Stripe test clocks): create a clock, create the customer on it, attach a
subscription, advance the clock, and watch the webhooks drive the app.

Scenarios to script before Launch, asserting the mirror and entitlements after each step:

1. Trial start → reminder event → trial end with a good card → `active`.
2. Trial end with no card, and with a declining card.
3. Renewal fails → `past_due` → retry succeeds; and → retries exhausted → downgraded.
4. Upgrade mid-period with proration; upgrade whose payment requires 3DS; whose payment fails.
5. Downgrade scheduled → applied at renewal.
6. Cancel at period end → undo → cancel again → period ends → resubscribe.
7. Seat added and removed mid-period.
8. Refund and dispute on a subscription payment.

Use the provider's test cards for declines and 3DS, and forward webhooks to the local server
with the provider's CLI. Customers on a simulated clock are test-mode only and cannot be mixed
with normally-clocked objects.

## Migrating subscribers between prices

Prices at the provider are immutable in amount; a price change means a new price object and a
migration of subscriptions.

1. Create the new price; keep the old one active but hidden from sign-up.
2. Decide the cohort rule: grandfather forever, grandfather until a date, or migrate at next
   renewal. Pricing strategy and notice wording belong to `0x:pricing-monetization`.
3. Notify in advance. Many consumer jurisdictions and card-network rules require advance notice
   of a price increase with the right to cancel; check the notice period for the markets served.
4. Migrate at each subscription's renewal with proration off, so nobody gets a mid-cycle charge.
   Use scheduled changes at the provider, or a batch job that updates the subscription item.
5. Run the batch idempotently and slowly: a migration table with one row per subscription
   (pending, done, failed), provider rate limits respected, resumable. Dry-run on a test clock.
6. Verify afterwards: count of subscriptions per price, and the next upcoming invoice for a
   sample from each cohort.

Traps: annual subscribers must not be changed mid-term; subscriptions with coupons, add-ons or
custom prices need their own cohorts; currency cannot change on an existing subscription.

## Ask the user

- **Trial with or without a card?** It trades sign-up volume for conversion and dispute risk.
  Default: no card for self-serve products, with a provider subscription created at conversion.
- **What happens to access when a renewal fails?** Default: full access for the retry period
  with a banner, then free tier with data kept.
- **Do downgrades and cancellations take effect now or at period end, and is anything refunded?**
  Default: period end, no prorated refund.
- **What counts as a billable seat?** Default: active members; invites are free until accepted.
- **When prices change, are existing customers grandfathered?** Default: grandfather until a
  dated, announced migration at renewal.
- **How long is data kept after a subscription ends?** Default: a stated period such as 90 days,
  then deletion per the retention policy.
