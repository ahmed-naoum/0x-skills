# Exit and due diligence

Read this when: an acquirer or investor asks to look inside the company, someone offers to buy
it, the founder wants to sell or step back, a product is being shut down, or the company is
running out of money and must wind down.

## Make the business run without the founder

Owner dependence is the first thing a buyer prices, and the same work protects the company
against illness and burnout.

- Every account in the company's name with a company email: domain registrar, DNS, cloud,
  payment processor, app stores, email provider, analytics, social handles. An account tied to a
  personal email is a transfer problem in every deal.
- Credentials in a company password manager with a second administrator; recovery codes stored
  there, not on one phone.
- Written procedures for every recurring task: support, billing operations and refunds, deploys,
  incident response, the monthly close, renewals. Automate whatever is done by hand monthly.
- Contracts in the company's name and assignable; no key vendor paid on a personal card.
- Test: the founder goes fully offline for two weeks. Whatever broke or waited is the next
  procedure to write.

## Valuing and selling a small software business

| Business | Common basis | Notes |
|---|---|---|
| Owner-operated, profitable, one or two people | Multiple of seller's discretionary earnings (SDE) | SDE = net profit + owner's salary and benefits + one-time and discretionary costs + depreciation, amortization and interest |
| Larger, with a team that runs it | Multiple of EBITDA, after a market-rate salary for the manager | Every add-back must survive the buyer's review |
| Growing SaaS sold to a strategic or venture-backed buyer | Multiple of ARR | Growth and net retention drive the multiple more than profit |

Multiples move with growth, churn and net retention, the age and stability of the revenue
history (buyers want two to three years), owner hours per week, customer concentration,
platform dependence (one app store, one API, one ad channel), the recurring share of revenue,
code and infrastructure quality, and clean legal records. As a rule of thumb, small profitable
SaaS often sells for a low-to-mid single-digit multiple of annual SDE; check current marketplace
and broker reports, because the range moves with interest rates and buyer demand.

| Route | Fits | Cost |
|---|---|---|
| Listing marketplace (Acquire.com, Flippa and similar) | Smaller deals the founder runs personally | Listing or success fees; the founder does the selling |
| Broker (FE International, Quiet Light, Empire Flippers and similar) | Mid-sized profitable businesses | A success fee as a percentage of price, declining with size; vetted buyers and a managed process |
| M&A advisor or banker | Larger deals with strategic buyers | Retainer plus success fee; a competitive process (below) |

Small-deal mechanics: an NDA before revealing metrics; proof of revenue through read-only access
to the processor and analytics; an asset purchase agreement; an escrow service holding the money
until the assets (domain, code, accounts) transfer; a defined transition period of founder
support with capped hours.

## The standing data room

Keep it current every quarter, so diligence for an investor or acquirer takes days, not months.
Number the folders and keep an index.

| Folder | Contents |
|---|---|
| 1 Corporate | Charter, bylaws, all board and stockholder consents, good-standing certificates, subsidiaries |
| 2 Equity | Cap table reconciled to the ledger; SAFEs, notes, option plan, grants, 409A reports, 83(b) copies, repurchases |
| 3 Financials | Monthly statements, tax returns, the model, deferred revenue schedule, debt |
| 4 Revenue and customers | MRR bridge, cohort retention, top customer contracts, concentration, churn reasons |
| 5 Contracts | Vendors, partners, leases; change-of-control and assignment clauses flagged |
| 6 IP and technology | IP assignments from every founder, employee and contractor; trademarks; domains; open-source license inventory; architecture overview |
| 7 People | Employee list with role, compensation and location; contractor agreements; policies |
| 8 Legal and compliance | Privacy policy, terms, DPAs and subprocessors, disputes and claims |
| 9 Security | Policies, latest penetration test or security review, incident history |
| 10 Tax | Returns, sales tax and VAT registrations and filings, R&D claims |

The gaps that most often kill or reprice deals: a missing IP assignment from a founder or an
early contractor; unfiled 83(b) elections; option grants without board approval or below fair
market value; sales tax never collected where there was an obligation; contractors who are
employees in substance; customer contracts that need consent to assign; open-source license
conflicts (`0x:privacy-compliance`). Fix them before a buyer finds them, while they are cheap.
Technical diligence on the codebase is `0x:engineering-leadership`.

## Quality-of-earnings-ready financials

A quality-of-earnings review (by the buyer's accountants, or commissioned by the seller in
larger deals) tests whether reported earnings are real and repeatable. Prepare for it:

- Accrual-basis monthly statements for 24 to 36 months, closed and reconciled, with revenue
  recognized consistently (`bookkeeping-tax.md`).
- Proof of cash: revenue ties to bank deposits through processor payouts, month by month.
- MRR bridge reconciled to booked subscription revenue, and cohort tables (revenue retained by
  signup month or year) built from the same billing data (`runway-forecasting.md`).
- An adjusted EBITDA or SDE bridge with every add-back documented (one-time legal costs, owner
  pay normalized to market). Aggressive add-backs are the first thing buyers reject, and the
  rest of the numbers lose credibility with them.
- Normalized working capital (deferred revenue, receivables, payables): buyers set a target and
  adjust the price at closing.
- Gross margin with costs correctly split between COGS and opex; customer concentration; a sales
  tax exposure analysis.

## Sell, merge, raise or keep running

Compare personal outcomes, not headline numbers.

1. **Proceeds to the founder** = price − debt − transaction fees − liquidation preferences ahead
   of common (waterfall in `fundraising-process.md`) − escrow and earn-out at a discount −
   taxes (asset or stock sale; qualified small business stock or local equivalents). This
   number, not the headline, is the offer.
2. **Keeping it**: expected profit or distributions over the next several years, plus the value
   of selling later, weighed against the risks (competition, platform dependence, burnout).
3. **Raising**: dilution and higher expectations in exchange for growth; only if the venture path
   is wanted (`funding-strategy.md`).
4. **Merging**: shares in a combined company are worth what its next exit is worth; value them
   with the same skepticism as buyer stock.
5. **Non-financial**: what the founder wants to do for the next three to five years, and what
   happens to the team, customers and product under the buyer.

- Set the walk-away number before talking to any buyer.
- With investors, a sale usually needs board and preferred approval, and their incentives (fund
  life, target multiple) can differ from the founders'. Bring them in early.
- An unsolicited offer is information, not a deal: thank them, share nothing before an NDA, and
  if selling is attractive, use the approach to start a process with other buyers. A single
  bidder sets the price.

## A competitive sale process

| Phase | Work |
|---|---|
| Prepare | Choose an advisor; clean financials and the data room; a QoE for larger deals; a list of strategic and financial buyers |
| Outreach | Anonymous teaser, NDA, then a confidential information memorandum to interested buyers |
| First round | Indications of interest with a price range; select a short list |
| Management meetings | Presentations, early diligence, data room opened in stages |
| Letters of intent | Price, structure, cash and stock mix, escrow, earn-out, exclusivity period, key conditions |
| Exclusivity and confirmatory diligence | The buyer's full financial, legal, technical and tax diligence; definitive agreement negotiated |
| Signing and closing | Approvals, third-party consents, closing deliverables, funds flow |

- Advisor fees are a success percentage, plus a retainer for bankers. Watch the tail clause that
  pays them for a sale to any buyer they contacted, for a period after the engagement ends.
- Settle everything that matters in the letter of intent: once exclusivity starts, leverage
  passes to the buyer, and re-trading the price after diligence is common.
- Keep the business performing; a missed month during exclusivity becomes a price cut.
- Keep the circle small until signing; tell key employees when the retention plan requires it.

## Deal terms

| Term | What it means | Position |
|---|---|---|
| Price and form | Cash, buyer stock, or a mix | Cash at close is worth most; private buyer stock is illiquid and valued at the buyer's word |
| Structure | Asset purchase, stock purchase or merger | Buyers prefer assets (liabilities stay behind, better tax basis); for a C corporation an asset sale can be taxed twice. Model both with a tax adviser |
| Working capital adjustment | The price moves if working capital at closing differs from a target | Agree target and method in the letter of intent |
| Escrow or holdback | Part of the price held back to cover claims | Negotiate amount and release date; representations and warranties insurance can shrink it |
| Earn-out | Further payment if targets are met after closing | Value it heavily discounted; earn-outs cause most post-closing disputes. Require objective metrics, buyer obligations to support the business, and acceleration if the founder is let go |
| Representations and warranties | Statements about the business the buyer can claim on | Knowledge and materiality qualifiers; the disclosure schedule lists every exception |
| Indemnification | What the sellers pay for breaches | A basket (deductible), a cap tied to the escrow, a survival period; fundamental representations (title, capitalization, taxes) carry higher caps |
| Non-compete and employment | The founder's commitments after closing | Duration, scope, and whether employment pay is really part of the price |
| Retention pool | Equity or cash for the team | Whether it comes out of the price paid to shareholders or on top of it |

## After the deal: integration

- Before signing: retention agreements with the people the buyer needs (often a closing
  condition); the founder's role, reporting line and authority agreed in writing, especially when
  an earn-out depends on them.
- Day one: team first, then customers, then the public. Customers want to know what changes and
  when, what does not, who supports them, and whether prices hold. Changes to data processing or
  subprocessors may require notice under privacy terms (`0x:privacy-compliance`).
- A transition services agreement when the buyer needs the seller's systems or people for a time.
- Migrations (billing, accounts, infrastructure) planned with dates; a rushed billing migration
  causes churn the earn-out then pays for.
- No early price rises or product cuts that drive churn while earn-out metrics are running.

## Sunsetting a product

1. Check obligations: customer contracts (notice periods, SLAs, prepaid terms, data-return
   clauses), DPAs, app store and marketplace rules.
2. Stop new signups and disable upgrades.
3. Announce the end date, what customers must do and how to export: at least 30 days ahead for
   self-serve products, commonly 90 or more for business customers and API users (rules of
   thumb; contracts override).
4. Turn off renewals and cancel subscriptions in the billing provider through its API, not just
   in the app; refund unused prepaid time pro rata.
5. Self-serve bulk export in open formats (CSV, JSON, original files); keep the API readable for
   integrators until the end date.
6. Reminders at intervals, for example 30, 7 and 1 days before.
7. Shut down; leave a static page explaining what happened and where data went.
8. Delete customer data after a short, stated grace period, as the privacy policy and DPAs
   require, including at subprocessors; confirm deletion on request.
9. Keep the domain registered for years: a lapsed domain can be bought and used to phish former
   customers or receive their password-reset emails.

## Winding down the company

Decide while there is cash to pay everyone. A solvent wind-down is administrative; an insolvent
one is a legal process with duties to creditors, and directors who keep trading while insolvent
can become personally liable in many jurisdictions.

1. Tell the board and investors early; they may find an acqui-hire or asset sale that returns
   more than a shutdown.
2. Board and stockholder approval of dissolution and a plan of distribution.
3. Stop new commitments; sunset the product (above); try to sell assets (code, domain, customer
   list where privacy terms allow) through a small-acquisition marketplace.
4. Employees: final pay on time under local law, accrued vacation where required, benefits
   continuation notices, notice or WARN-type obligations where they apply.
5. Creditors: notify and pay in legal priority (secured creditors, then employee wages and
   taxes, before general unsecured). Unpaid payroll withholding can become the directors' debt.
6. Taxes: final payroll filings and year-end forms, a final income tax return marked final,
   final sales tax and VAT returns, registrations canceled.
7. Distribute what remains by the liquidation waterfall: debts first, then preferred and SAFE
   holders (a post-money SAFE returns its purchase amount ahead of common in a dissolution),
   then common.
8. File the dissolution. Delaware requires franchise taxes and annual reports to be current;
   withdraw registrations in other states. Close bank accounts after the last payments clear.
9. Keep corporate, tax and employment records for the periods the accountant gives (years, not
   months), and keep tail coverage on directors' insurance where it exists.

| Jurisdiction | Solvent | Insolvent |
|---|---|---|
| US (Delaware) | Dissolution under state law with notice to creditors | Assignment for the benefit of creditors under state law, or bankruptcy; insolvency counsel |
| UK | Strike-off application when there are no debts and no recent trading, or a members' voluntary liquidation with a declaration of solvency | Creditors' voluntary liquidation through a licensed insolvency practitioner |
| EU | National liquidation procedure with a liquidator and creditor notice | National insolvency filing duties with short deadlines; local counsel |

## Ask the user

- **What does the founder want personally: cash now, keep running, stay on after a sale?**
  Default: compute proceeds to the founder for each path before discussing price.
- **What is the walk-away number?** Default: set it before any buyer conversation, after taxes
  and preferences.
- **Do investors and the board know, and what approvals do the documents require?** Default:
  assume board and preferred approval are needed; read the charter and investor agreements.
- **How much of the price is acceptable as earn-out or escrow?** Default: value earn-outs at a
  heavy discount and push for cash at close.
- **For a wind-down: is the company solvent today, including all employee and tax obligations?**
  Default: if unsure, get insolvency counsel before paying anyone other than employees and taxes.
- **What notice and refunds do customers get when a product ends?** Default: at least 30 days
  for self-serve, 90 for business customers, pro rata refunds, full data export.
