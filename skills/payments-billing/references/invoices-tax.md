# Invoices and sales tax

Read this when: deciding how tax is handled, issuing invoices and receipts, selling to
businesses or to other countries, correcting an invoice, accepting bank transfers or purchase
orders, or pricing in more than one currency.

Tax rules here are mechanisms and common practice, not advice for a jurisdiction. Thresholds,
rates and deadlines change; confirm current values with the tax authority or an accountant
before registering or filing. Filing and bookkeeping are `0x:startup-finance`.

## Merchant of record, or handle tax yourself

Indirect tax on digital sales is generally owed where the *customer* is, not where the seller
is. A seller of record therefore acquires obligations in every place with customers, sometimes
from the first sale.

| Option | What it is | Takes on | Cost and limits |
|---|---|---|---|
| Merchant of record (Paddle, Lemon Squeezy, Polar and similar) | The provider is the legal seller and resells the product | Tax registration, collection, remittance and invoices worldwide; much of fraud and dispute handling | Higher percentage fee; their checkout, invoice format, payout schedule and acceptable-use rules; customers see their name on statements; weaker fit for sales-led B2B and marketplaces |
| Processor + tax engine (Stripe + Stripe Tax, or a tax API) | The business is the seller; software computes tax and tracks thresholds | Calculation and reports only. Registration and filing remain the business's job (add a filing service or accountant) | Lower fee, full control, real ongoing obligations |
| Processor, no tax handling | Ignore tax | Nothing | Accrues liability with penalties and interest; acceptable only at Prototype with no real revenue |

Decision rule: one founder selling low-priced software to consumers and small businesses in
many countries → merchant of record, and revisit when the fee difference exceeds the cost of an
accountant plus filings. Selling mostly B2B in a few countries, needing custom invoicing,
contracts or a marketplace → processor plus tax engine plus an accountant. Switching later
means migrating subscriptions and cards, so decide before Launch, not after.

A merchant of record does not remove the business's own income tax or its obligations in its
home country for the payouts it receives; it removes the customer-facing indirect tax.

## Registering, collecting, remitting

The mechanics by region, as background for the conversation with an accountant:

- **EU**: B2C digital services are taxed at the customer's country's VAT rate. A seller
  established in the EU has a small EU-wide annual threshold for cross-border B2C sales below
  which home-country VAT applies; sellers outside the EU have no threshold. The One Stop Shop
  (OSS) lets a seller register once and file one quarterly return for all member states
  instead of registering in each. B2B sales to a customer with a valid VAT ID in another
  member state are reverse-charged: no VAT charged, a note on the invoice, the buyer accounts
  for it.
- **UK, Norway, Switzerland, Australia, New Zealand, India, Canada, Japan and many others**:
  their own rules for foreign sellers of digital services, with thresholds from zero to
  substantial. Each is a separate registration.
- **United States**: no federal sales tax. Each state sets whether software or SaaS is taxable
  at all (it varies, and so does the treatment of B2B vs personal use) and its own economic
  nexus threshold, typically a sales amount per year and sometimes a transaction count; rates
  vary down to city and district level, so the full address or at least the postal code is
  needed. A few states have no state-level sales tax.
- **Evidence of customer location**: tax authorities expect proof of where the customer is.
  Store the billing country, the IP-derived country and the card's issuing country with each
  sale; EU rules ask for two non-conflicting pieces of evidence above a small-seller threshold.
  When they conflict, block or ask rather than guess.

Sequence when handling it in-house:

1. Turn on the tax engine in monitoring mode from the first sale, so it tracks where sales
   accumulate. Give every product the right tax code; the default code is often wrong for SaaS
   versus downloadable software versus services.
2. Register *before* charging tax in a jurisdiction. Collecting tax without a registration is
   itself an offense in many places.
3. Add the registration to the engine; it then charges tax there. Decide per market whether
   existing prices absorb the tax (inclusive) or it is added on top (exclusive).
4. File and remit on the jurisdiction's schedule even when the amount is zero. Missed zero
   returns produce penalties.
5. Keep the tax collected out of spendable cash: it is not revenue.

## Tracking thresholds

- Thresholds are measured variously on trailing twelve months, calendar year, or current and
  previous year, and on gross sales, taxable sales or transaction counts. Let the tax engine
  track them; a spreadsheet built from provider exports by customer location is the fallback.
- Alert at a fraction of each threshold (for example 80%), because registration takes days to
  weeks and the obligation typically starts at or shortly after crossing.
- Review monthly at Launch. One large annual contract can cross a state threshold alone.
- Marketplaces and merchants of record that already collect on a sale usually take that sale
  out of the seller's own count; rules differ, so confirm before assuming.
- If a threshold was crossed in the past unnoticed, stop and get professional help: voluntary
  disclosure programs exist and are much cheaper than being found.

## Invoices and receipts

A receipt confirms payment. A tax invoice is a legal document businesses need to deduct tax,
and its required content is set by law. Commonly required fields:

| Field | Notes |
|---|---|
| Unique sequential number | Gapless per series in many countries; never reuse or delete. Use a database sequence per legal entity and series, assigned at finalization, not at draft |
| Issue date, and supply date if different | |
| Seller legal name, address, tax registration number | The legal entity, not the brand |
| Customer name and address; customer tax ID for B2B | |
| Description, quantity, unit price, service period | |
| Net amount, tax rate, tax amount per rate, gross total, currency | Some countries require the tax amount also in local currency at an official rate |
| Reason when no tax is charged | Reverse charge, export, exemption: the specific wording matters locally |

- Generate the invoice from an immutable snapshot of the order at finalization: customer
  details, line items, tax rates as charged. Regenerating from current data rewrites history
  when a customer edits their address.
- Store the rendered PDF and the structured data. Retention periods for invoices are long
  (commonly six to ten years); they are exempt from deletion requests for that reason, see
  `0x:privacy-compliance`.
- Give customers a self-serve invoice history. B2B customers ask for invoices monthly.
- Let customers add billing details *before* purchase; after finalization, changes go through
  a credit note (below), with a narrow exception for provider-supported address edits on
  not-yet-paid invoices.
- Provider-generated invoices are sufficient for most small businesses if the entity details,
  tax IDs and numbering prefix are configured. Check them once against local requirements.

## Tax IDs and billing addresses from business customers

- Ask "Are you buying as a business?" and reveal the tax ID field with the country-specific
  format hint. Hosted checkouts have a tax-ID collection option; use it.
- **Validate, do not just format-check.** For EU VAT numbers, validate against the VIES service
  and store the result, timestamp and consultation reference; the zero-rating is defensible
  only with proof of validation at the time of sale. Other countries have their own registries.
- Validation services go down. On failure, either charge tax and refund it when validation
  later succeeds, or accept provisionally and re-validate in a job; never block the sale
  indefinitely and never zero-rate on an unvalidated number without a recheck.
- A valid ID changes tax treatment only in the cases the law defines (cross-border B2B in the
  EU). A domestic business customer is still charged VAT, with the ID printed on the invoice.
- The ID's country must match the billing country. Mismatches are either mistakes or evasion.
- US exempt buyers (resellers, nonprofits) provide exemption certificates per state; store them
  and mark the customer exempt in the tax engine.
- Re-validate stored IDs periodically for subscriptions; companies deregister.

## Credit notes, not edits

A finalized invoice is immutable. Changing it destroys the audit trail and, in jurisdictions
with sequential numbering, is illegal.

| Situation | Action |
|---|---|
| Wrong amount, wrong tax, refund, cancellation | Credit note referencing the original invoice, for the full or partial amount; its own number series; then a new correct invoice if needed |
| Wrong customer name, address or tax ID | Full credit note + new invoice with the right details |
| Invoice will never be paid | Void (if never sent or the jurisdiction allows) or mark uncollectible; a credit note where voiding is not permitted |
| Typo noticed before finalization | Edit the draft |

A credit note either refunds money, credits the customer's balance for the next invoice, or
simply reduces an unpaid invoice; record which. Tax reported on the original is reversed by
the credit note in the period the note is issued. Refund without a credit note and the tax
return over-reports.

## E-invoicing mandates

A growing number of countries require invoices to be issued as structured data, often through a
government platform or a certified network, rather than as a PDF. Models differ: clearance
(the tax authority approves each invoice before it is valid, as in Italy and much of Latin
America), and network exchange with reporting (Peppol-based systems in several European and
Asia-Pacific countries). The EU has adopted a move toward mandatory structured e-invoicing for
cross-border B2B, with member states phasing in domestic mandates on their own timelines.

- The obligation usually depends on where the *seller* is established and sometimes on the
  buyer (public-sector buyers often require e-invoices first). A foreign seller with no local
  establishment is frequently out of scope; confirm per country.
- Formats to recognize: the European standard EN 16931 and its syntaxes (UBL, CII), Peppol BIS,
  and hybrid PDF-with-embedded-XML formats (Factur-X, ZUGFeRD), plus national formats.
- Do not build this. Use the billing provider's e-invoicing support or a certified access-point
  partner; the work on the app side is supplying complete structured data: tax IDs, addresses,
  unit codes, tax categories per line.
- Skip until the entity's own country mandates it or a customer's procurement requires it; then
  it is mandatory, with dates set by law.

## Bank transfers, purchase orders and net terms

Larger B2B customers will not put a card on file. Offer invoice payment above a minimum
contract size (rule of thumb: annual contracts in the thousands, not monthly plans), because
each such customer costs manual work.

- **Flow**: quote or order form → invoice with due date (net 30 is the common default) →
  payment by bank transfer → matched to the invoice → paid. Provider invoicing supports this
  with a send-invoice collection mode and a hosted payment page offering transfer and card.
- **Matching**: give each customer a dedicated virtual bank account number or a unique payment
  reference so incoming transfers reconcile automatically. Without that, expect payments with
  missing references, short payments (bank fees deducted, or tax withheld) and two invoices
  paid in one transfer; define handling for under- and over-payment.
- **Access before payment**: with net terms the customer uses the product before paying. Grant
  entitlements on signed order or finalized invoice, set by a human decision, not on `paid`.
  Overdue handling is a manual escalation (reminders at due date, +7, +14, then a conversation),
  not automatic cutoff.
- **Purchase orders**: store the PO number and print it on the invoice; many accounts-payable
  departments reject invoices without it. Procurement portals and vendor forms are
  `0x:sales-support`.
- ACH and SEPA debit are the middle path: automated like cards, cheaper for large amounts, with
  delayed confirmation and return risk (see `checkout-integration.md`).
- Chasing unpaid invoices is a real cost. Annual upfront only; avoid monthly invoicing on terms.

## Multiple currencies

Three different currencies are in play: presentment (what the customer is charged), settlement
(what the processor pays out) and reporting (the company's books).

- **Pricing**: set explicit prices per currency for the main markets (round, locally sensible
  numbers) rather than converting live; live conversion makes prices drift and look arbitrary.
  Provider-side automatic local-currency conversion at checkout is the low-effort alternative,
  with the customer usually bearing a conversion markup.
- **Lock currency per customer.** A subscription cannot change currency; a customer who
  relocates gets a new subscription. Choose the currency from billing country, not IP alone.
- **Settlement**: when presentment and settlement currencies differ, the processor converts at
  its rate plus a fee. Above meaningful volume in a currency, open a bank account in it and
  settle like-for-like.
- **Refunds** are made in the presentment currency for the original amount. The settlement-
  currency cost differs from what was received when the rate has moved; the business absorbs
  the difference. The same applies to disputes.
- **Records**: store the presentment amount and currency on the order, and the settled amount,
  currency and fee from the provider's balance transaction on the payment. Never store a
  converted amount without the rate and its date. Reporting in one currency converts using
  the settled amounts, not a re-derived rate.
- **Regional price differences** invite arbitrage via VPN; tie the price to the billing
  country and payment-method country, and accept some leakage.
- Realized exchange gains and losses, and the rate to use for tax reporting in local currency,
  are accounting questions for `0x:startup-finance`.

## Ask the user

- **Do you want to be responsible for registering and filing tax in other countries, or pay a
  higher fee to have a merchant of record do it?** Default: merchant of record for a solo
  founder selling internationally to consumers; processor plus tax engine for B2B-led products.
- **Where is the company established, and where is it already registered for tax?** Everything
  else depends on it. Default: assume registered at home only, and collect tax only there until
  the engine shows a threshold approaching.
- **Are customers mostly consumers or businesses?** It decides inclusive vs exclusive pricing
  and whether tax-ID collection is needed at Launch. Default: collect tax IDs optionally.
- **Will you accept payment by invoice and bank transfer, and above what contract size?**
  Default: cards only until a customer with an annual contract asks.
- **Do you have an accountant who handles indirect tax?** If not and tax is handled in-house,
  recommend engaging one before the first foreign registration.
