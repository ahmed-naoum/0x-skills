# Usage-based and credit billing

Read this when: price depends on consumption: metering API calls, tokens, storage, messages or
minutes; prepaid credits and top-ups; quotas and overages; seats-plus-usage plans; or showing
customers their usage and spend.

## The architecture that holds up

Four parts, and the app's database is the system of record for usage. The billing provider is
the invoicing engine, not the meter.

```
product action → usage event (append-only, own DB)
                    ├→ live counter per account and period   (quota checks, usage page)
                    ├→ provider meter or period-end invoice line   (billing)
                    └→ reconciliation: events vs counters vs provider   (before each billing run)
```

Reasons: provider usage APIs are asynchronous and rate limited, so they cannot answer "may this
request proceed" in the request path; they aggregate without giving back per-event detail a
customer dispute needs; and a meter that only exists at the provider cannot be re-rated when a
pricing bug is found.

Skip all of this at Prototype. A flat plan with a generous fair-use limit is the right first
version unless cost per customer varies by orders of magnitude (LLM tokens, video minutes).
Choosing the value metric and price points is `0x:pricing-monetization`.

## Metering events

One row per billable occurrence, written by the server at the point the work is done.

| Field | Rule |
|---|---|
| `id` / idempotency key | Deterministic from the thing measured (request ID, job ID, message ID), unique-constrained. A random UUID generated at send time dedupes nothing on retry |
| `account_id` | The billed entity, resolved server-side |
| `meter` | Stable name: `tokens_out`, `api_request`, `storage_gb_hour` |
| `quantity` | Integer in the smallest unit ever priced (tokens, bytes, seconds); never floats |
| `occurred_at` | When the work happened; decides the billing period |
| `recorded_at` | When it was stored; needed to reason about late arrivals |
| `properties` | Dimensions that price may depend on later (model, region, tier) |

- **Record the raw quantity, price later.** Events store "1,532 output tokens on model X", not
  "$0.02". Rating at read time lets a price change, a discount or a bug fix be applied without
  rewriting history.
- **Write the event in the same transaction as the work's result** when both are in Postgres,
  or through an outbox when the work is elsewhere. Fire-and-forget metering calls under-bill
  silently; that loss never shows up as an error.
- **Meter what was delivered.** A failed request, a retried job or a stream cut by a server
  error must not bill twice or bill for nothing. Decide whether partial work is billed, and
  write the event when the outcome is known.
- **Late events**: accept events whose `occurred_at` falls in a closed period for a short grace
  window before the invoice finalizes; after that, bill them in the next period as an
  adjustment line. Never drop them silently and never edit a finalized invoice.
- **Gauges** (storage, seats over time) are sampled: a scheduled job writes one event per
  account per interval. Pick the aggregation explicitly (peak, average, last) because customers
  will ask.
- High volume: buffer and pre-aggregate per account per minute before the durable write, keyed
  so that a replayed batch overwrites instead of adding. Keep raw events as long as invoices
  can be disputed (see `0x:data-stores` for retention).

When forwarding to a provider meter (Stripe Billing Meters and equivalents), send the same
deterministic identifier so the provider dedupes too, send from a job with retries, and respect
its limits on how old an event's timestamp may be. Providers reject events older than their
backfill window, so a multi-day outage of the forwarder needs manual invoice adjustments.

## Enforcing quotas without calling the provider

The check runs on every request and must cost about a millisecond and survive a billing outage.

| Need | Mechanism |
|---|---|
| Hard limit that must not be exceeded (prepaid credits, free tier on costly resources) | Atomic conditional decrement in the store that holds the balance |
| Soft limit (plan allowance with overage) | Local counter incremented per event; compare to allowance for alerts only |
| Very high request rates | Redis counter per account and period, reconciled to Postgres; or a leased budget per process |

```sql
-- Hard limit: succeeds only if enough remains. Zero rows updated means deny.
update usage_balance
   set remaining = remaining - $2
 where account_id = $1 and remaining >= $2;
```

- **Unknown cost up front** (LLM output length, job duration): reserve an upper bound before
  the work, then settle to the actual amount afterwards and release the difference. Without a
  reservation, concurrent requests all pass the check and overshoot together.
- **Fail open or closed on counter outage**: fail open (allow, meter later) for paid plans with
  overage, where a blocked customer costs more than some unbilled usage; fail closed for free
  tiers and prepaid balances on expensive resources, where open means unbounded loss.
- Return a specific error (HTTP 402 or 429 with a machine-readable code and the reset time or
  top-up link), not a generic failure. Rate-limit design is `0x:api-design`.
- Entitlement limits come from the local plan map (see `subscriptions.md`), never from a
  provider call in the request path.
- Abuse: a free tier on a costly resource is a target. Require a verified email or a card
  before the expensive meter opens, and cap per-account daily spend regardless of plan.

## Showing usage: page, alerts, caps

Bill shock produces disputes and churn; a usage page is part of the billing system.

- **Usage page**: current-period quantity per meter, the included allowance, overage so far in
  money, the projected period total, and a daily breakdown. Read from the app's own counters,
  seconds to minutes fresh, and label the freshness. Make it exportable.
- **Alerts** at thresholds of the allowance or of a customer-set budget (50%, 80%, 100% is the
  common set), by email to billing admins and in-app. Send each threshold once per period: store
  the last threshold notified.
- **Caps**: a customer-set hard cap that stops usage at a spend amount. Default new self-serve
  accounts to a conservative cap they can raise; enterprise accounts to alert-only. When the
  cap hits, the API returns the specific quota error and the admins get an email with the raise
  link.
- **Provider-side spend alerts** are a second line, not the mechanism: they lag.
- New accounts with no payment history get a low ceiling on postpaid usage until the first
  invoice is paid; postpaid usage is credit extended to a stranger.

## Billing in arrears from metered totals

| Approach | Use when |
|---|---|
| Provider meters: send events, provider aggregates and invoices at period end | Default with Stripe Billing; simple per-unit or tiered prices |
| Own rating: compute the amount at period end, add invoice lines to the draft invoice | Pricing the provider cannot express, or re-rating needs |
| Threshold billing: invoice whenever accrued usage reaches an amount | New or risky accounts; limits exposure |

Period-end sequence, whichever approach:

1. Period closes at the subscription's boundary, in UTC. Define which side an event exactly on
   the boundary falls on (period is `[start, end)`).
2. Grace window for late events and for the forwarder to drain.
3. Reconcile (below). Only then let the invoice finalize. With Stripe, invoices stay in draft
   for about an hour before finalizing, and that window is when corrections are possible.
4. Finalize, charge, and store on the app side the per-meter totals the invoice was built from.

Tiered pricing traps: state whether tiers are graduated (each unit priced by its own tier) or
volume (all units at the tier reached); the two differ sharply near boundaries. Round once, at
the invoice line, not per event. Mid-period plan changes need a rule for the allowance:
prorate it, or apply the new allowance to the whole period.

## Prepaid credits

Credits are a liability ledger, not a number column. An `update balance = balance + x` design
cannot explain to a customer where their credits went, and cannot expire anything correctly.

| Table | Rows |
|---|---|
| `credit_grant` | One per top-up, promo or plan allowance: account, amount, remaining, source (paid, promo, included), `expires_at`, payment reference |
| `credit_entry` | Append-only: grant ID, signed amount, reason (grant, consume, expire, refund, adjust), reference to the usage event or payment, created time |

- Balance = sum of `remaining` over unexpired grants. Keep `remaining` consistent with the
  entries in the same transaction; the entries are the audit trail and are never updated.
- **Consumption order**: earliest-expiring first, and promotional before paid within the same
  expiry, so customers lose the least. Lock the account's grants (`select ... for update`) while
  consuming across several.
- **Grant on webhook**, idempotently, keyed on the payment ID: a top-up granted from the
  redirect is free credits for anyone who replays the URL.
- **Expiry**: a scheduled job writes an `expire` entry and zeroes `remaining`. Warn before
  expiry. Whether paid credits may expire at all, and how unredeemed balances are treated, is
  regulated in some jurisdictions (gift-card and stored-value rules); ask before promising or
  imposing expiry on paid balances.
- **Auto top-up**: when the balance crosses a threshold, charge the saved method off-session
  for a fixed amount. Guard with one in-flight top-up per account, a daily maximum, and a clear
  off switch. A failed auto top-up notifies and falls back to the hard limit.
- **Refunds**: refund only unused paid credits, by writing a negative entry against the grant
  and refunding the payment proportionally. Promo credits have no cash value; say so in terms.
- **Negative balance**: allow a small overdraft to finish in-flight work, then block. Decide
  whether the overdraft is collected from the next top-up.
- Unused prepaid balances are deferred revenue until consumed or expired; accounting treatment
  is `0x:startup-finance`.

Provider credit features (billing credit grants applied to metered invoices) can replace the
own ledger when usage is already billed through provider meters and real-time blocking is not
needed. Real-time enforcement still requires the local balance.

## Hybrid: seats plus usage

Typical shape: a base subscription (flat or per seat) that includes an allowance, plus metered
overage, on one subscription with one invoice.

- Base fee is billed in advance, usage in arrears. The first invoice has only the base; each
  later invoice has the next period's base and the previous period's overage. Explain this on
  the invoice or support will.
- Allowance = per-plan constant or per-seat amount × seats. With seat changes mid-period,
  the default is to compute the allowance from seats at period end or from the peak; prorating
  by seat-days is the fairest and the hardest to explain.
- Allowances reset each period by default. Rollover needs the credit ledger above, with the
  allowance as an expiring grant.
- Annual base with monthly overage is normal: two cadences on one customer. Confirm the provider
  supports mixed intervals on one subscription, otherwise use two subscriptions and treat that
  as the one sanctioned exception to "one subscription per account".
- Overage price should be visible before the customer crosses the allowance, with the option
  to upgrade instead; an upgrade that would have been cheaper than the overage is a support
  ticket waiting to happen.
- Committed-use contracts (prepaid annual commitment drawn down by usage) are the credit ledger
  with one large grant and an invoice-based top-up.

## Reconcile before each billing run

Run daily and as a gate before finalization. For every account and meter in the period:

| Comparison | Mismatch means |
|---|---|
| Sum of raw events vs live counter | Counter drift: lost increments or double counting |
| Sum of raw events vs provider meter total | Forwarder lag, rejected events, or duplicate sends |
| Rated amount from own events vs draft invoice line | Wrong price, tier mode or period boundary |
| Usage events vs independent evidence (request logs, upstream vendor bill) | Metering gaps: code paths that do work without emitting an event |
| Credit entries sum vs grant `remaining` | Ledger bug |

- Set a tolerance (for example a fraction of a percent or a small absolute amount) and hold the
  invoice in draft above it, with an alert. Under-billing discovered later is mostly
  unrecoverable; over-billing is a refund plus an apology.
- Sanity rules catch what sums cannot: an account whose usage rose by an order of magnitude over
  its trailing average, a negative quantity, usage on a canceled account, zero usage on an
  active API key.
- Keep the reconciliation result per invoice. It is the evidence when a customer disputes a
  bill and the audit trail when an upstream cost bill does not match revenue.
- After a metering bug: re-rate from raw events, issue credit notes or adjustment lines per
  `invoices-tax.md`, and follow the correction procedure in `refunds-disputes-fraud.md`.

## Ask the user

- **Is usage billed after the fact, or prepaid with credits?** Postpaid extends credit to
  customers and needs caps; prepaid needs a ledger and top-up flow. Default: prepaid credits for
  self-serve products with real marginal cost, postpaid in arrears for established B2B.
- **What happens when a customer hits their limit: block, or continue and charge overage?**
  Default: block on free and prepaid, overage with alerts on paid plans.
- **Do paid credits expire, and are unused credits refundable?** Legal limits vary by country.
  Default: promo credits expire, paid credits do not expire within at least a year, unused paid
  credits refundable on request.
- **Is partial or failed work billed?** Default: bill only successfully delivered work.
- **Should new accounts have a default spend cap?** Default: yes, a low one the customer can
  raise after the first paid invoice.
