# Catalog, cart, inventory and fulfillment

Read this when: selling physical goods, digital goods, tickets or bookable units: choosing a
commerce platform or building one, modeling products and prices, carts, discounts and shipping,
stock and seat reservation, fulfillment, returns, license keys, or syncing with marketplaces
and warehouses.

## Platform, headless backend or custom

Commerce has a very long tail of solved problems (tax, shipping rates, returns, fraud, payment
methods, marketplace feeds). Building them is rarely where a small team's advantage lies.

| Situation | Choose | Why |
|---|---|---|
| Standard store: physical or simple digital goods, storefront is not the differentiator | Hosted platform (Shopify or similar) with its theme system | Live in days; payments, tax, shipping, admin, apps included |
| Custom storefront or app experience, standard commerce underneath | Headless: the platform's storefront API, or an open-source commerce backend (Medusa and similar) behind a Next.js front end | Own the UX; rent the order, payment and admin machinery |
| Commerce is a feature inside a product (SaaS plans, credits, a few digital items) | Payment provider's products, prices and checkout; no commerce platform | A catalog of ten items does not need a platform |
| The unit sold is unusual: time slots, seats, rentals, quotes, configurable builds, multi-vendor | Custom domain model, with provider checkout for payment | Platforms model SKUs and quantities; bending them costs more than building the core |
| Scale with complex B2B pricing, many regions, ERP integration | Enterprise headless platforms or custom services | Only with a team to run it |

Before choosing custom, list what will have to be built that a platform includes: admin UI for
non-developers, tax and shipping calculation, refunds and returns, order emails, inventory
adjustments, fraud screening, reporting. If the list is longer than the differentiating
feature, choose the platform. Platform lock-in is mostly in the admin workflows and app
ecosystem; keep product data exportable and own the domain and customer list.

## Catalog model

| Entity | Holds |
|---|---|
| `product` | Title, description, media, category, options definition (Size: S/M/L; Color: red/blue), status |
| `variant` | The sellable unit: one combination of option values, SKU (unique), barcode, weight and dimensions, tax category |
| `price` | variant_id, currency, amount (integer minor units), optional price list (region, customer group), validity window |
| `inventory_item` / `stock_level` | Per variant, per location: on hand, reserved |

- **Everything sellable is a variant**, including products with no options (one default
  variant). Carts, orders, stock and prices reference variants only; code that handles
  "product or variant" doubles every path.
- **Options generate variants; variants are rows, not JSON.** Stock, price and SKU hang off them.
- **Prices are rows per currency**, set deliberately, not computed from a base currency at
  render time. A missing price for a currency means "not sold in that currency", not zero.
  State on the price list whether amounts include tax.
- **Order lines snapshot** the title, SKU, unit price, tax rate and discount at purchase. An
  order must render identically after the product is renamed, repriced or deleted. Archive
  products; do not hard-delete ones that have orders.
- SKUs are stable identifiers shared with warehouses and channels; never reuse or encode
  mutable facts into them.
- Free-form attributes (material, specs) go in a JSON column or attribute table for filtering
  and search; search itself is `0x:data-stores`.
- Bundles and kits: model as a variant with component rows that decrement component stock;
  decide whether the bundle or the components appear on the packing slip.

## Cart

- **Server-side cart** keyed by an opaque cart ID in an HTTP-only cookie for guests and by
  account for signed-in users. A cart only in browser storage cannot be recovered, shared
  across devices or used for reminders.
- **Merge on sign-in**: combine the guest cart into the account cart, summing quantities up to
  stock and purchase limits, then drop the guest cart. Decide and test the conflict rule.
- **Lines store variant ID and quantity only.** Prices are looked up and totals computed on
  every read by the pricing engine. A price stored in the cart is either stale or tamperable.
- **Price or stock changed since adding**: show it explicitly at cart and checkout ("price
  changed from X to Y", "only 2 left") and require the customer to proceed again. Silent
  changes at the payment step cause abandonment and complaints.
- **Freeze at order placement**: creating the order copies lines and computed totals, and that
  frozen total is what is charged. If the cart changes after a payment session was created,
  expire that session and create a new one; a payment for a stale total must not fulfil a
  changed order.
- Validate on every mutation: variant exists and is purchasable, quantity within limits,
  currency consistent across lines.
- Expire abandoned guest carts on a schedule (weeks, not hours) and keep account carts longer.
- Carts do not reserve stock by default (see reservations).

## One pricing engine, on the server

A single pure function computes totals for cart display, checkout, the payment amount, the
order and the invoice. Several implementations will disagree by a cent, and the customer will
see it.

```
price(cart lines, customer, shipping address, shipping method, codes, now)
  → lines[{unit_price, quantity, line_discount, tax_rate, tax, total}],
    subtotal, discount_total, shipping, tax_total, grand_total, applied[], rejected[{code, reason}]
```

- **Order of operations, fixed and documented**: unit prices → line-level promotions →
  order-level discounts (allocated back to lines proportionally) → shipping → tax → total.
  Whether tax is computed on the discounted price and whether shipping is taxed depend on
  jurisdiction; the tax engine decides, given line-level discounted amounts.
- **Rounding**: round per line at the tax step in the currency's minor unit, sum the rounded
  lines, and allocate order-level discounts with a largest-remainder method so the parts sum
  exactly to the whole. Refunds per line rely on this.
- **Coupons**: validate on the server (existence, validity window, minimum spend, eligible
  items, per-customer and global redemption limits). Enforce redemption limits atomically at
  order placement (conditional increment of the redemption counter), not at apply time, or a
  limited code is redeemed many times in parallel. Rate-limit code attempts; codes are guessable.
- **Stacking rules** explicit: which promotions combine, and which wins when they do not.
  Totals never go below zero; a 100% discount still creates an order, with no payment step.
- **Shipping**: rates from rules (flat, by weight or subtotal bands, free above a threshold) or
  a carrier-rate API with a cached fallback when the API is down. Needs the destination before
  the total is final.
- The client may show an optimistic estimate; the server result replaces it. The payment amount
  comes only from the server computation (see `checkout-integration.md`).
- Test the engine with table-driven cases and property tests: the total equals the sum of the
  lines, is never negative, and is stable under recomputation.

## Reserving stock and seats

Overselling comes from read-then-write races. The decrement must be a single conditional write.

```sql
-- Returns a row only if enough stock was available. No row = sold out.
update stock_levels
   set reserved = reserved + $2
 where variant_id = $1 and location_id = $3
   and on_hand - reserved >= $2
returning variant_id;
```

| Decision | Default | Flip when |
|---|---|---|
| When to reserve | At checkout start (payment session creation), with an expiry | Reserve at add-to-cart only for scarce, high-demand items (tickets, drops), with a short visible timer |
| Reservation lifetime | Slightly longer than the payment session lifetime | Async payment methods: keep until the payment resolves |
| On payment success | Convert the reservation: `on_hand -= qty`, `reserved -= qty`, in the fulfilment transaction | |
| On expiry, failure or cancel | Release: `reserved -= qty`, by a job scanning expired reservations and by the session-expired webhook | |
| Payment succeeds after the reservation expired and stock is gone | Refund automatically and apologize, or backorder if the business allows | Rare if lifetimes are aligned; it must still be handled |

- Keep a `reservations` table (order or cart, variant, quantity, expires_at, status) so
  releases are idempotent and auditable; the counter alone cannot say whose hold it is.
- Multi-line orders: reserve all lines in one transaction, in a fixed order (sorted by variant
  ID) to avoid deadlocks; fail the whole reservation if any line fails.
- **Unique units** (seats, license slots): one row per unit; claim with
  `select ... for update skip locked` for "any available", or a conditional update on the
  specific seat's status for "this seat".
- **Time-range bookings**: a Postgres exclusion constraint makes overlapping bookings of one
  resource impossible: `exclude using gist (resource_id with =, during with &&)` on a range
  column (needs the `btree_gist` extension). Locking details: `0x:postgres-database`.
- Flash sales: the conditional update holds, but protect the database with a queue or waiting
  room in front and rate limits; hot-row contention is the bottleneck, not correctness.
- Inventory changes are an append-only movement log (received, sold, returned, adjusted,
  damaged) with the counters derived from it; stock disputes are otherwise unanswerable.

## Fulfillment

An order has three independent state machines; one combined status column cannot express
"paid, partly shipped, one item refunded".

| Machine | States |
|---|---|
| Payment | pending → authorized → paid → partially refunded → refunded; disputed |
| Fulfillment (per shipment) | unfulfilled → picking → packed → shipped → delivered; failed, returned |
| Order | open → completed → canceled |

- An order has one or more **shipments** (fulfillments), each with its lines, location, carrier,
  tracking number and status. Split shipments and partial fulfillment then need no special case.
- Each step is a job triggered by the previous state change, idempotent, with retries and a
  dead-letter state a human sees: label purchase, warehouse or 3PL submission, tracking
  ingestion from carrier webhooks or polling, customer notifications. Job mechanics:
  `0x:backend-architecture`.
- **Failure handling to design up front**: address fails validation (validate at checkout, hold
  the order for correction after); item out of stock at pick (partial ship plus refund of the
  missing line, or wait, by policy); label API down (retry, then queue for manual); shipment
  lost or returned to sender (reship or refund); warehouse never acknowledges (alert on orders
  unfulfilled past a time limit).
- **Cancellation window**: customer cancel is allowed until the order is sent to the warehouse;
  after that it becomes a return. Enforce with a guarded state transition.
- **Notifications**: order confirmed, shipped with tracking link, out for delivery or delivered,
  delayed. One message per event, sent from the state transition exactly once
  (`0x:email-notifications`).
- If capture happens at shipment, capture per shipment and watch authorization expiry.
- Operational alert: count and age of orders by state. "Paid, unfulfilled for more than N
  hours" is the metric that catches a stuck pipeline.

## Returns, exchanges and restocking

- A **return** (RMA) is its own object: order lines and quantities, reason, status (requested →
  approved → in transit → received → inspected → resolved), resolution (refund, exchange,
  store credit, rejected).
- **Refund trigger**: default to refunding when the item is received and inspected; refund on
  carrier scan for trusted customers or low-value items. Refunding at request invites abuse.
- **Refund amount** is computed per line from the order snapshot: the line's paid amount after
  allocated discounts plus its tax; original shipping only where policy or law requires;
  minus a restocking fee if policy has one. Execute per `refunds-disputes-fraud.md`, capped at
  what was paid, with a credit note.
- **Restock** is a separate decision after inspection: sellable stock goes back via an
  inventory movement; damaged goods go to a non-sellable location. Never restock automatically
  on refund.
- **Exchange** = return + new order linked to it, with the price difference charged or
  refunded. Reserve the replacement at approval so it is still available when the return lands.
- Promotions that depended on the returned item (bundle price, spend threshold, free gift)
  need a rule: recompute what the kept items would have cost, or let it stand.
- Consumer law in many markets grants distance-selling withdrawal rights with specific refund
  deadlines, with exceptions for some digital and custom goods; `0x:privacy-compliance` covers
  the rules. Publish the policy and link it at checkout.

## Digital goods and license keys

- **Deliver from the paid transition**, not from the success page: the same idempotent
  fulfilment function creates a `grant` row (order line, customer, product, status) and sends
  the email. A replayed redirect or webhook produces no second grant.
- **Downloads**: files in private object storage; the download route checks the grant, then
  issues a short-lived signed URL (minutes) per request. Never email a permanent file URL.
  Count downloads and cap them generously; log IP and time as delivery evidence for disputes.
- **License keys**: generate from a CSPRNG with enough entropy that guessing is infeasible
  (at least 128 bits), formatted for typing. For keys from a pre-supplied pool, claim one with
  `for update skip locked` inside the fulfilment transaction. Activation is server-side: an
  endpoint binds the key to a device or account and enforces the seat limit, with a
  self-service deactivation path.
- **Offline-verifiable licenses**: a signed payload (product, expiry, limits) with an asymmetric
  signature (Ed25519), the public key embedded in the app. They cannot be revoked without an
  online check, so give them an expiry and refresh.
- **Revoke on refund and on dispute**: mark the grant revoked, invalidate keys, stop downloads.
- Show keys and downloads in the account area as well as by email; mail gets lost.
- Rate-limit activation and download endpoints; key-guessing and link-sharing are the abuse.

## Syncing with channels and warehouses

- **One system is the master for each fact**, written down: usually the warehouse or 3PL for
  physical on-hand counts, the commerce backend for sellable availability and prices, each
  channel for its own orders until imported. Two-way sync of the same field without a master
  loops and oversells.
- **Availability pushed to channels = on hand − reserved − a safety buffer** per channel. The
  buffer absorbs sync latency; widen it for fast-moving items.
- **Push deltas from events, and reconcile with a periodic full sync.** Events get lost; a
  nightly comparison of the full stock list per channel repairs drift. Alert on large deltas.
- **Order import is idempotent** on the channel's order ID (unique constraint), maps external
  SKUs through a mapping table, and stores unknown SKUs in a holding state for a human instead
  of failing the batch.
- Respect channel API rate limits with a queue per channel, and handle their outages by
  replaying from a stored cursor (last synced timestamp or ID).
- Warehouse messages (shipment confirmations, receipts, adjustments) arrive late, duplicated
  and out of order: process them as inventory movements keyed on the warehouse's message ID.
- Expect physical counts to diverge from the system; schedule cycle counts and post the
  differences as adjustment movements with a reason.
- Skip multi-channel sync until a second channel exists; then prefer the platform's connector
  or an integration service over custom code.

## Ask the user

- **What is being sold: shippable goods, digital files, time slots, seats?** It decides
  platform versus custom. Default: a hosted commerce platform for physical goods; provider
  checkout plus a small custom model for digital goods.
- **If stock runs out between cart and payment, cancel and refund, or backorder?** Default:
  reserve at checkout start so it rarely happens; refund automatically when it does.
- **What is the return policy: window, who pays return shipping, restocking fee?** Default: the
  legal minimum for the markets served, refund on receipt, customer pays return shipping
  unless the item is faulty.
- **Can discount codes be combined, and with sale prices?** Default: one code per order, not
  combinable with other codes.
- **Who ships: the founder, a warehouse or 3PL, or dropshipping?** It decides the fulfillment
  integration. Default: manual fulfillment from the admin at Launch, integration when order
  volume makes it painful.
- **Charge at order or at shipment?** Default: at order, except preorders with long lead times.
