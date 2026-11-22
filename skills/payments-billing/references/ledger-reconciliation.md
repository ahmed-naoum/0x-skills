# Ledger and reconciliation

Read this when: modeling money in the database, a customer says they were charged twice or
paid without getting access, the provider's numbers and the database disagree, matching payouts
to the bank and to sales, exporting to accounting software, or holding and paying out money for
third parties in a marketplace.

## How much ledger, at which stage

| Stage | Build |
|---|---|
| Prototype | Provider is the record. Store provider IDs on the user or order. Nothing else |
| Launch | Orders, payment attempts, payments, refunds, disputes as tables mirroring provider objects; a webhook event log; daily reconciliation. This is enough for most SaaS |
| Launch, if the app itself holds balances (credits, wallets, marketplace earnings, gift cards) | An immutable double-entry ledger for those balances, from day one |
| Scale | Double-entry ledger for all money movement; automated payout matching; accounting integration |

The trigger for double entry is the app owing or tracking money that the provider does not
track for it. A subscription SaaS whose provider holds all balances does not need one.

## Schema for orders and payments

| Table | Key columns | Notes |
|---|---|---|
| `orders` | id, account_id, status, currency, subtotal, discount, tax, total (all integer minor units), pricing snapshot | Totals frozen at placement; never recomputed from the live catalog |
| `payment_attempts` | id, order_id, idempotency key (unique), provider object ID, status, decline code, created_at | One row per try, written before the provider call |
| `payments` | id, order_id, provider payment ID (unique), amount, currency, status, captured_at, provider balance-transaction ID, fee, net, settlement currency | One row per successful money movement in |
| `refunds` | id, payment_id, provider refund ID (unique), amount, status, reason, actor | |
| `disputes` | id, payment_id, provider dispute ID (unique), amount, reason, status, due_by | |
| `provider_events` | provider event ID (unique), type, payload, received_at, processed_at, error | The webhook inbox; also the audit log |

Rules for every money column:

- Integer minor units (`bigint`) plus an ISO currency code in the same table. No floats; no
  `numeric` dollars mixed with cents. Never add amounts of different currencies.
- A provider ID column for every mirrored object, with a unique constraint. It is the join key
  for reconciliation and what makes webhook upserts idempotent.
- Status changes go through guarded transitions, and the history is kept: either an append-only
  `order_events` table or the ledger. "Who changed this and why" must be answerable.
- Timestamps in UTC with time zone; reporting periods are converted at read time.

## Making double charges impossible

Layered guards; the database constraint is the one that cannot be bypassed by a bug elsewhere.

```sql
-- At most one live payment per order. A second provider payment for the same order is
-- stored with status 'duplicate' (outside this index) and then refunded.
create unique index one_live_payment_per_order
  on payments (order_id)
  where status in ('processing', 'succeeded');

-- Guarded transition: only a pending order can become paid.
update orders set status = 'paid', paid_at = now()
 where id = $1 and status = 'pending';
-- 0 rows updated = someone else already did it: skip the side effects.
```

| Layer | Guard |
|---|---|
| Request | One open attempt per order: take `select ... for update` on the order row, refuse or return the existing attempt when one is in flight |
| Provider call | Idempotency key = attempt ID, persisted first (see `checkout-integration.md`) |
| Webhook | Event ID unique in `provider_events`; fulfillment through the guarded transition |
| Database | Unique provider payment ID; the partial unique index above; `check (amount > 0)`; refunds sum ≤ payment amount enforced under a lock |
| Subscriptions | One active subscription per account: partial unique index on `account_id` where status is live; reuse the existing provider customer instead of creating another |
| After the fact | Reconciliation finds two succeeded provider payments carrying the same order ID in metadata, refunds the later one, alerts |

Recurring jobs that charge (usage top-ups, renewals run in-house) need a unique key on
`(account_id, billing_period)` so a job that runs twice inserts one charge row.

## Answering "I was charged twice"

Most reports are not double charges. Establish facts before refunding anything.

1. **Provider dashboard, by customer email and by card last four**: list payments in the window.
   Note status, amount, the provider payment IDs and the order ID in metadata.
2. **Classify**:

| What the provider shows | What it is | Response |
|---|---|---|
| One succeeded payment, plus one failed or canceled attempt | A pending authorization from the failed attempt showing on the statement | Explain; it drops off within days. No refund exists to issue |
| One succeeded payment | Bank app showing pending and posted lines for the same charge, or a second card on the account | Explain with the charge date and amount |
| Two succeeded payments, same order ID | True duplicate | Refund the later one now; find the missing guard |
| Two succeeded payments, different orders | Customer submitted twice (two tabs, back button), or two accounts | Refund if unwanted; add the guard from `checkout-integration.md` |
| Two subscription invoices | Two subscriptions on one customer, or upgrade proration plus renewal | Cancel the duplicate and refund; or explain the proration |
| A charge the database does not know about | Missed webhook, or a payment created outside the app | Reconcile, fulfill or refund |

3. **Database**: attempts and payments for the order; do the provider IDs match the dashboard?
4. **Logs and `provider_events`**, filtered by the order and payment IDs: were two create calls
   made, with which idempotency keys, from which request IDs? Two calls with different keys for
   one order identifies the code path.
5. **Reply with specifics**: dates, amounts, last four, what each line is, and when a refund
   will appear. Log the provider request IDs on every provider call so this takes minutes.
6. **If it was a real duplicate, search for others**: the same query across all orders for the
   period, then the correction procedure in `refunds-disputes-fraud.md`.

"Paid but no access" is the mirror case: find the payment at the provider, check
`provider_events` for the event and its processing error, replay the handler, then fix why it
failed.

## Daily reconciliation

Webhooks get lost, handlers have bugs, humans act in the dashboard. A scheduled job compares
both sides and repairs or alerts.

- **Window**: list provider payments, refunds, disputes and subscriptions created or updated
  since the last successful run minus an overlap (for example the last 48 hours every day), so a
  failed run is covered by the next.
- **Provider → database**: every provider object has a matching row with the same status and
  amount. Missing or stale rows are repaired by running the same sync function the webhook uses.
- **Database → provider**: every local row in a non-terminal state older than a threshold
  (pending order for an hour, processing payment for a week) is looked up; every local "paid"
  has a provider payment that is in fact succeeded and not refunded.
- **Entitlements**: every account with paid access has a live subscription or a valid override;
  every live subscription has an account with access.
- **Output**: counts checked, repaired and unresolved, stored per run. Alert on any unresolved
  item and on the job not finishing. An always-green job that silently stopped running is the
  usual failure.
- Auto-repair only toward the provider's truth, and only through idempotent sync functions.
  Anything involving a refund above a small amount goes to a human.

## Matching payouts, fees and refunds

The bank statement shows one deposit per payout; it is the net of many payments, minus fees,
refunds, disputes and adjustments, and it does not line up with calendar-day sales.

- The provider records every movement of the balance as a balance transaction with a type
  (charge, refund, dispute, fee, payout, adjustment), gross amount, fee and net. Each payout
  can be expanded into the balance transactions it contains (Stripe: list balance transactions
  filtered by payout, which works for automatic payouts only, or the payout reconciliation
  report).
- For each payout: `sum(net of its balance transactions) = payout amount = bank deposit`. Store
  the payout ID on each payment, refund and dispute row once known. Three-way match: bank
  deposit ↔ payout ↔ ledger rows.
- Things that break naive matching: fees deducted per transaction versus billed monthly;
  refunds and disputes netted against later sales; reserves held and released; currency
  conversion (match on settlement-currency amounts); a negative payout debited from the bank;
  payouts on a delay, so month-end sales arrive next month.
- The balance still at the provider at period end is an asset ("funds in transit"), which is
  why revenue for a month never equals deposits for a month.
- Launch: reconcile payouts monthly from the provider's report. Scale: per payout, automated.

## Export to accounting

- Post summaries, not every transaction: one journal per payout or per day with gross sales,
  refunds, fees, tax collected, disputes and the net to the bank, each to its own account.
  Thousands of individual rows make the books unusable; keep detail in the app and provider.
- Tax collected goes to a liability account, split by jurisdiction. Processor fees are an
  expense. Refunds reduce revenue; they are not expenses. Prepayments (annual plans, credits)
  are deferred revenue; the recognition schedule is `0x:startup-finance`.
- Stable identifiers in every exported line (payout ID, invoice number) and an idempotent
  export: re-running a period replaces or skips, never duplicates.
- Lock exported periods: a correction after export is a new adjusting entry dated now, not an
  edit to the past.
- Use a maintained connector between the provider and the accounting package before writing
  one; custom export is justified when the ledger lives in the app.

## An immutable double-entry ledger

Every movement is a transaction with two or more entries that sum to zero per currency.
Balances are derived, never stored as the only copy.

```sql
create table ledger_accounts (
  id bigint generated always as identity primary key,
  owner_type text not null,           -- 'platform', 'customer', 'seller', 'provider'
  owner_id text not null default '',  -- '' for platform accounts: null would defeat the unique key
  kind text not null,                 -- 'cash_at_provider', 'customer_credit', 'seller_payable', 'revenue', 'fees'
  currency char(3) not null,
  unique (owner_type, owner_id, kind, currency)
);

create table ledger_transactions (
  id bigint generated always as identity primary key,
  idempotency_key text not null unique,   -- provider event or business operation ID
  kind text not null,
  reference text,
  created_at timestamptz not null default now()
);

create table ledger_entries (
  id bigint generated always as identity primary key,
  transaction_id bigint not null references ledger_transactions (id),
  account_id bigint not null references ledger_accounts (id),
  amount bigint not null check (amount <> 0)  -- signed minor units: debit > 0, credit < 0
);
```

- **Append-only**: the application role has `insert` and `select` only on these tables (revoke
  `update` and `delete`), or a trigger raises on change. A mistake is corrected by a reversing
  transaction that references the original.
- **Balanced**: all entries of a transaction are inserted in one database transaction through a
  single function that checks `sum(amount) = 0` per currency before commit. A deferred
  constraint trigger (`create constraint trigger ... after insert on ledger_entries deferrable
  initially deferred`) that raises when a transaction's entries do not sum to zero enforces
  it against direct writes.
- **Idempotent**: the unique key on `ledger_transactions` makes a replayed webhook a no-op.
- **Balances**: `sum(amount)` per account. With this sign convention, liability and revenue
  accounts (customer credit, seller payable) carry negative sums: negate for display, and
  write overdraft checks with the sign in mind. When summing gets slow, keep a balance row
  updated in the same transaction, and verify it against the sum in reconciliation.
- **No overdraft**: lock the account row (`for update`) before checking and spending, or put a
  check constraint on the cached balance, so two concurrent spends cannot both pass.
- **Cross-currency** movements go through explicit FX accounts with both legs recorded; a
  single entry never changes currency.
- Global invariant to test in CI and in the daily job: the sum of all entries per currency is
  zero, and the `cash_at_provider` account equals the provider's reported balance.

Example, customer buys 100.00 of credits, fee 3.20: debit cash_at_provider 96.80, debit fees
3.20, credit customer_credit 100.00. Spending 10.00 of credits: debit customer_credit 10.00,
credit revenue 10.00.

## Marketplace funds and connected accounts

Receiving money on behalf of sellers and paying it out is regulated activity (money
transmission or payment services) in most jurisdictions. Do not route third-party funds through
the company's own bank account. Use the provider's marketplace product (Stripe Connect, Adyen
for Platforms, PayPal's equivalent), where the provider holds the funds, onboards and verifies
each seller, and performs payouts.

| Decision | Options | Default |
|---|---|---|
| Charge type | Direct charge on the seller's account; destination charge on the platform with automatic transfer; separate charge and later transfers | Destination charges for a typical marketplace; separate charges and transfers when one payment is split among several sellers or released later; direct when sellers are the merchants (SaaS platforms) |
| Seller onboarding | Provider-hosted onboarding vs custom-built | Hosted. Identity verification requirements change and the provider keeps the hosted flow current |
| Who is liable for refunds, disputes, negative balances | Platform or seller, depending on charge type and account configuration | Know it before launch: with platform-owned charges the platform is debited when a seller cannot cover a dispute |
| Payout timing | Immediate, scheduled, or held until delivery | Hold until the service is delivered or the return window closes, within the provider's maximum holding period |

- Collect the platform fee as an application fee on the charge, not by invoicing sellers later.
- Mirror every balance-affecting event into the double-entry ledger with a `seller_payable`
  account per seller; the ledger explains each payout to the seller and catches transfer bugs.
- Refunds and disputes after payout: reverse the transfer, and decide what happens when the
  seller's balance is empty (debit their bank, net against future sales, or platform absorbs).
  A reserve or delayed payout for new sellers limits this.
- Sellers need tax documents and reporting in many countries, and platforms increasingly have
  their own reporting duties about seller income (US Form 1099-K and the EU's DAC7 are the
  best-known examples); the provider's tooling covers part. Ask an accountant which apply.
- Payouts are blocked until the seller completes verification; surface the provider's
  requirements status in the seller dashboard and by email, or support will hear about it.

## Ask the user

- **Does the app hold balances for customers or pay money out to third parties?** It decides
  whether a double-entry ledger and a marketplace product are needed now. Default: no ledger
  beyond mirrored provider objects unless credits, wallets or seller payouts exist.
- **In a marketplace, who bears a chargeback when the seller has been paid already?** Default:
  the seller, enforced by delayed payouts for new sellers, with the platform as backstop.
- **When should sellers be paid: at purchase, at delivery, or after a return window?** Default:
  after delivery confirmation.
- **Which accounting system is used, and who closes the books?** Default: a maintained
  connector posting daily summaries, reviewed monthly.
- **How large a discrepancy can be auto-corrected without a person?** Default: repairs toward
  provider truth automatically; any refund above a small fixed amount needs approval.
