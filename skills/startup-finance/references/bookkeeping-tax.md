# Bookkeeping and tax

Read this when: opening the company's bank accounts, setting up or catching up the books,
reading the financial statements, working out which taxes are due and who files them, claiming
R&D credits, or making billing-system revenue agree with the books.

## By stage

| Stage | Minimum |
|---|---|
| Prototype (company formed) | Business bank account and card; every company transaction on them; accounting software with bank feeds; receipts captured; a calendar of filing dates; an accountant for the annual returns |
| Launch | Accrual books closed monthly; processor clearing account; payroll through a provider; sales tax or VAT decision made; bookkeeper monthly, accountant for tax and year end |
| Scale | Close within about ten business days; revenue recognition schedule; audit-ready records; controller or fractional CFO (`runway-forecasting.md`) |

Before incorporation there are no company books: keep receipts for pre-formation costs so the
company can reimburse or record them once it exists. Forming the entity is `0x:company-building`.

## Separate the money

Open the company's bank account in the company's name, with its tax ID, the week the entity
exists. From then on every company transaction runs through it and the company card, and
nothing personal does.

- **Why it matters**: commingled accounts make the books unreconcilable, turn personal spending
  into taxable distributions or disallowed deductions, can weaken limited liability (US courts
  weigh commingling when deciding whether to disregard the entity; other countries set the bar
  differently), and surface in every diligence.
- **Accounts**: one operating account; a second account at a different bank
  (`runway-forecasting.md`); optionally a sub-account that holds collected sales tax and payroll
  tax until paid. Separate company cards per category (cloud, ads, software) make
  categorization automatic, and a compromised card stops only one thing.
- **Founder paid with a personal card**: reimburse through an expense report with receipts (in
  the US, an accountable plan keeps reimbursements non-taxable), then stop doing it. Ad hoc
  transfers with no record are what gets recharacterized as income or distributions.
- **Founder puts money in**: record it as a loan with a signed note, or as equity (a share
  purchase or a SAFE). An unrecorded transfer becomes a guess at year end and a question in
  diligence.
- **Founder takes money out**: salary through payroll for a corporation; draws or distributions
  for pass-through entities. The right method depends on the entity's tax classification and
  country; ask the accountant before the first payment.
- **Processor payouts** go to the operating account. Money sitting at the processor is a company
  asset and belongs on the balance sheet.

## Accounting software and the monthly books

| Choice | Default | Flips when |
|---|---|---|
| Software | QuickBooks Online in the US; Xero (or QuickBooks) in the UK, Australia and New Zealand | In most EU countries, and whenever the accountant works in a local system (DATEV in Germany, for example): use theirs. UK VAT-registered companies need software that files under Making Tax Digital |
| Basis | Accrual from Launch | Prototype with no revenue: cash basis is fine. The tax return may still use cash basis where the law allows; the accountant handles the difference |
| Ownership | The company's own subscription; bookkeeper and accountant invited as users | Never books kept only inside a bookkeeping firm's proprietary system: when that firm closes or is dropped, the history goes with it |
| Processor revenue | Summary journal per payout through a clearing account, via a maintained connector | The ledger lives in the app → custom export (`0x:payments-billing`) |

Chart of accounts for a software company, built so gross margin and spend by function come out
of the books without a spreadsheet:

- **Revenue** split into subscription, usage, and services or setup. Investors and buyers value
  them differently.
- **Cost of revenue (COGS)**: production hosting, third-party APIs and model tokens consumed by
  customers, payment processing fees, support and onboarding staff, tools used to serve
  customers. Development and staging infrastructure is R&D, not COGS.
- **Operating expenses** by function: R&D, sales and marketing, general and administrative.
  Salaries are split by function, not lumped into one payroll line.
- **Balance sheet**: processor clearing, prepaid expenses, deferred revenue, sales tax payable by
  jurisdiction, accrued expenses, payroll liabilities.

Bank feeds with categorization rules handle most lines; the bookkeeper handles the rest; the
founder reviews the result monthly, not daily.

## Reading the three statements

Read them in this order, asking one question of each.

| Statement | Question | Look at | Red flags |
|---|---|---|---|
| Profit and loss | Does each unit of revenue make money, and where does spend go? | Revenue by type; gross margin (revenue minus COGS, over revenue); opex by function, month over month | Gross margin moving with no pricing or infrastructure change (usually misclassified costs); revenue spiking in months with annual renewals (deferred revenue missing); "uncategorized" lines |
| Balance sheet | What does the company have and owe right now? | Cash (ties to bank statements); receivables and their age; deferred revenue; sales tax payable; accrued and payroll liabilities; equity | Cash that does not match the bank; sales tax payable that only grows; negative asset balances; a suspense account with a balance; founder loans without paperwork |
| Cash-flow statement | Why did cash change, and is the company funded by customers or investors? | Operating cash flow vs net income; financing inflows | Operating cash flow persistently below net income (customers paying late, or revenue booked early) |

Rules that change decisions:

- Profit is not cash. Annual prepayments arrive as cash months before they become revenue;
  invoices on payment terms are revenue before they are cash. Run the company on cash
  (`runway-forecasting.md`) and report on accrual.
- Pure software gross margin commonly sits well above 70% as a rule of thumb; heavy model,
  data or services costs pull it lower. The trend and its explanation matter more than the level.
- How a SAFE appears on the balance sheet (liability or equity) is an accounting judgment that
  depends on the standard and the instrument's terms; the accountant classifies it.

## Taxes: what is due and when

Four families: **income tax** on profit, due annually even with no revenue (filing is what
preserves losses to carry forward); **employment taxes**, withheld and contributed on each
payroll (a payroll provider files and pays, but the company stays liable); **indirect taxes**
(sales tax, VAT, GST) collected from customers, where whether to collect is
`0x:payments-billing` and filing and paying on schedule belongs here; and **entity fees**
(annual reports, franchise taxes, registered agent).

| Jurisdiction | Obligation | Timing | Trap |
|---|---|---|---|
| US, Delaware C corporation | Federal corporate return (Form 1120) | April 15 for a calendar-year company; six-month extension available | An extension moves the filing date, not the payment date; a profitable company also pays estimated tax quarterly |
| | Delaware franchise tax and annual report | March 1 each year (corporations; a Delaware LLC instead pays a flat annual tax due June 1) | The state's default notice uses the authorized-shares method and can show tens of thousands of dollars for a startup with millions of authorized shares; recompute with the assumed par value capital method (it needs total gross assets and issued shares; minimum 400 USD at the time of writing), which for a typical early startup gives a small amount. Unpaid tax blocks a certificate of good standing |
| | State income and franchise taxes | Varies by state | An employee working from a new state creates payroll registration and often income-tax nexus there |
| | Contractor information returns (1099-NEC) | January 31 | Collect a W-9 at onboarding. The reporting threshold rose from 600 to 2,000 USD for payments made from 2026 (indexed from 2027). Foreign individuals working outside the US give a W-8BEN and get no 1099; foreign contractors working inside the US raise withholding questions for the accountant |
| | Foreign-owned companies (corporations 25% or more foreign-owned; foreign-owned single-member LLCs): Form 5472 | With the corporate return (for an LLC, a pro forma 1120) | A 25,000 USD penalty per missing form per year under current law, even when no tax is due; foreign founders need an accountant who files these every year |
| UK private limited company | Corporation tax payment | 9 months and 1 day after the period end (companies below the large-company threshold) | Register for corporation tax within 3 months of starting to trade |
| | Company tax return (CT600) | 12 months after the period end | |
| | Annual accounts to Companies House | 9 months after year end; first accounts 21 months after incorporation | Late-filing penalties are automatic |
| | Confirmation statement | Annually | |
| | PAYE | Report on or before each payday through payroll software; pay HMRC by the 22nd of the following month when paying electronically | A director on salary is on payroll too |
| | VAT return, if registered | Usually quarterly; return and payment one month and seven days after the period end | Filed through Making Tax Digital software |
| | Companies House identity verification | Directors and people with significant control, since November 2025 | The confirmation statement cannot be filed until every director is verified |
| EU, Canada, Australia and elsewhere | Annual accounts, corporate return, payroll and periodic VAT or GST returns | Country-specific | In several countries a licensed tax adviser is effectively required; get the full filing calendar from a local accountant in the first month |

US beneficial-ownership (BOI) reporting to FinCEN no longer applies to US-formed companies or US
persons (an interim rule in March 2025, made final in August 2026); foreign companies registered
to do business in a US state still report. Older guidance saying every startup must file is out
of date. Banks still collect ownership details when an account is opened.

- Put every date in a shared calendar with reminders a month and a week ahead, owned by the
  founder and the accountant.
- Hold collected sales tax and payroll withholding in reserve; it is other people's money.
  Unpaid payroll withholding can be collected personally from the people responsible (in the US
  through the trust fund recovery penalty, with equivalents in many countries).
- A dormant or pre-revenue company still files. Penalties on companies that "had nothing to
  report" are the most common and most avoidable tax cost of a startup.

## Who does what

| Role | Does | When |
|---|---|---|
| Founder | Owns bank and accounting admin access, approves payments, reviews the monthly pack, knows the cash balance at all times | Always; never delegated |
| Bookkeeper (person or firm) | Categorization, reconciliations, payables, the monthly close | Launch, earlier if the founder is behind |
| Accountant (CPA, chartered accountant, Steuerberater) | Annual returns, year-end adjustments, tax planning, credits, entity and founder-pay advice | From incorporation |
| Payroll provider | Payslips, withholding, filings, year-end forms | First employee, including a founder on salary |
| R&D credit specialist | Credit study and claim | Once qualifying spend is material |
| Fractional CFO | Model, board pack, fundraising and audit support | `runway-forecasting.md` |

Choosing an accountant:

- Works with software startups in the company's jurisdiction and can explain, unprompted,
  deferred revenue, R&D credits and the local traps in the table above.
- For a founder living in one country with a company in another, cross-border experience in both
  is mandatory: treaty positions, controlled-foreign-company rules and information returns are
  where the large penalties sit.
- Works in the company's accounting software, charges a fixed monthly fee with a stated close
  date, and answers within an agreed time.
- Gets references from two founders at a similar stage. Red flags: no close calendar, wants the
  books in their own system, or offers credits on contingency without asking for documentation.

## Monthly close checklist

Target: closed by business day 10 to 15 at Launch, faster at Scale (a rule of thumb; numbers more
than a month old cannot steer anything).

1. Bank, card and loan accounts reconciled to statements, to the cent.
2. Processor clearing account: payouts matched; clearing balance equals the processor's reported
   balance at month end (payout matching is in `0x:payments-billing`).
3. Revenue: billing-system invoices agree with booked revenue; deferred revenue roll-forward
   balances (below).
4. Payroll journal from the provider, including employer taxes and benefits, split by function.
5. Accruals for services received but not yet billed (usage-based cloud, contractors, legal);
   prepaid expenses (annual software, insurance) amortized.
6. Equipment above the accountant's capitalization threshold recorded and depreciated.
7. Sales tax and VAT payable agree with the tax engine report or the filed returns.
8. Uncategorized, suspense and "ask my accountant" accounts at zero.
9. P&L compared with last month and the plan; every line off by more than a set threshold
   explained in one sentence.
10. Period locked in the software, so later edits need a deliberate unlock.
11. Finance pack produced (`runway-forecasting.md`).

## R&D credits and startup reliefs

The pattern everywhere: governments refund or offset part of qualifying research spend, often in
cash for loss-making startups, if the claim is made on time and backed by records made during
the work. Most of the money is in engineering salaries.

| Jurisdiction | Mechanism | What to know |
|---|---|---|
| US federal | Research credit (IRC section 41) on qualified US wages, supplies and part of contract research | A qualified small business (gross receipts under 5 million USD in the year and none more than five years earlier) can elect to apply up to 500,000 USD a year of the credit against employer payroll taxes, so a pre-revenue company gets cash. The election is made on Form 6765 with a timely filed income tax return (extensions count), then claimed on Form 8974 against payroll tax from the quarter after the return is filed; a late return forfeits it for that year. Many states add their own credits |
| US federal | Deducting research costs (sections 174 and 174A) | For 2022 to 2024, domestic research costs had to be capitalized over five years, creating taxable income for near-profitable startups. The July 2025 legislation made domestic research costs deductible again from tax years beginning in 2025; foreign research is still amortized over 15 years, so development by offshore contractors stays capitalized. Unamortized 2022 to 2024 costs can be deducted over one or two years; the small-business option to amend those returns closed on July 6, 2026. Have the accountant confirm which elections were made |
| US federal | Qualified small business stock (section 1202) | Benefits US taxpayers holding stock of a US C corporation issued while its gross assets were under the threshold (75 million USD for stock issued after July 4, 2025; 50 million before). For the newer stock, 50% of the gain is excluded from federal tax after three years, 75% after four and 100% after five, up to the greater of 15 million USD or 10 times basis per company; older stock needs five years and caps at 10 million. Some states, California among them, do not follow it, and some service businesses do not qualify. Keep issuance dates and gross-asset records; LLC interests do not qualify until converted |
| UK | R&D relief: for accounting periods from April 2024, the merged expenditure credit, or enhanced support (ERIS) for loss-making SMEs whose R&D is a large share of total spend | A company that has not claimed in the previous three years (first-time claimants included) must submit a claim notification within 6 months of the end of the period of account, or the claim is lost; every claim needs the additional information form. Payments to overseas contractors and externally provided workers are largely excluded. HMRC scrutiny of claims is high |
| UK | SEIS and EIS | Investor reliefs that make raising from UK angels easier; investors expect HMRC advance assurance before they invest (optional but standard), and the company files compliance statements after (`funding-strategy.md`) |
| EU | National schemes, for example France's research tax credit and young innovative company status, the Netherlands' WBSO payroll reduction, Germany's research allowance | Rules and rates differ by country; a local adviser files |
| Canada | SR&ED: refundable credits for Canadian-controlled private corporations | The claim is due 18 months after the year end; control by non-residents (a US parent, foreign investors) can remove the enhanced refundable rate |
| Australia | R&D Tax Incentive: a refundable offset for smaller companies | Register the activities with the government within 10 months of the year end, before claiming |

- Keep evidence as the work happens: project descriptions, the technical uncertainty addressed,
  approaches tried, time by person per project. Ticket and sprint history is a good base;
  reconstruction a year later is what fails an inquiry.
- Routine work (cosmetic UI, standard integrations, post-release bug fixing) usually does not
  qualify; work resolving genuine technical uncertainty usually does. The line is set per country.
- Be wary of contingency-fee firms that maximize claims: the company carries the penalty and
  interest when a claim is cut.

## Revenue recognition and billing-to-books

Under accrual accounting (ASC 606 in the US; IFRS 15, or a local standard with similar
principles such as FRS 102 in the UK, elsewhere) revenue is recognized as the service is
delivered, not when invoiced or paid.

| Billing event | Booked as |
|---|---|
| Monthly subscription paid | Revenue that month |
| Annual plan, 1,200 paid in January | Cash 1,200; deferred revenue 1,200, released at 100 per month |
| Setup or onboarding fee | Usually not a separate deliverable: deferred and recognized over the contract term or expected customer life |
| Usage billed in arrears | Revenue in the month of use; accrued if invoiced later |
| Prepaid credits | Deferred until consumed; expired credits recognized under a policy the accountant sets |
| Refund or credit note | Reduces revenue; not an expense |
| Processor fees | Expense in COGS; revenue is booked gross, not net of fees |
| Sales through a merchant of record (Paddle-style) | The merchant of record sells to the end customer; whether the company books gross sales or net payouts as revenue is a principal-or-agent judgment the accountant makes once and applies consistently |
| Sales tax or VAT collected | A liability, never revenue |
| Multi-year prepayment | Deferred; the part beyond 12 months is long-term |

Monthly reconciliation:

- Deferred revenue roll-forward: opening + invoiced in the month − recognized = closing. The
  closing balance equals the unearned portion of open invoices.
- Recognized subscription revenue in the books matches the billing system's revenue schedule;
  each difference is explained (usage accruals, refunds, currency) or it is a bug.
- Cash collected = invoiced − increase in receivables. A widening gap means a collection problem.
- MRR is an operating metric, not revenue, and differs from recognized revenue every month
  (`runway-forecasting.md`).

A spreadsheet schedule for annual plans is enough at Launch. Move to the billing provider's
revenue recognition module or a dedicated tool when contracts mix subscription, usage and
services, or when an audit is coming.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Revenue spikes in January, P&L swings with renewals | Annual plans booked as revenue on invoice | Deferred revenue schedule |
| Books and processor never agree | Net payouts booked as revenue | Clearing account: gross sales, fees, refunds and payouts as separate lines |
| Weeks of catch-up bookkeeping before a raise or sale | No monthly close | Close monthly; the first catch-up is a fixed-scope project |
| Penalty notices at a company with no revenue | Assumed nothing needed filing | File every return; calendar every date |
| Startling Delaware franchise tax notice | Authorized-shares method on a company with many authorized shares | Recompute with the assumed par value capital method |

## Ask the user

- **Where is the company incorporated, and where do founders, employees and contractors live?**
  Filing obligations follow both. Default: assume nothing; list the jurisdictions before
  advising.
- **How is the entity taxed (C corporation, LLC, S corporation, UK limited company)?** It decides
  how founders get paid and which returns exist. Default: treat as a C corporation if it is a
  Delaware startup planning to raise.
- **What is the fiscal year end?** Default: the calendar year.
- **Are there annual plans, prepaid credits or setup fees?** They create deferred revenue.
  Default: yes if annual plans exist; set up the schedule.
- **Are engineers on payroll doing new technical work?** A credit may be worth more than most
  other financing at this stage. Default: ask the accountant to assess it at year end.
- **What budget exists for outside help?** Default at Launch: monthly bookkeeper plus an
  accountant for year end and tax.
