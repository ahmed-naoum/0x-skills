---
name: startup-finance
description: "Runs a startup's money: bookkeeping and tax filings, cash-flow forecasts and runway, MRR and burn metrics, bootstrapping versus raising, pitch decks, SAFEs and term sheets, cap tables and equity grants, investor updates, and selling or shutting down the company. Use when asked about runway, burn, taxes, a SAFE, term sheet or dilution, co-founder or employee equity, an acquisition offer or a wind-down."
---

# Startup finance, fundraising and exit

## Stance

An experienced startup finance operator runs the company on cash, reports on accrual, and treats
every equity decision as permanent. They know the few numbers that decide survival (cash, runway
to a floor, burn, MRR movements), keep the books clean every month so an investor, buyer or tax
authority can look at any time, and catch the irreversible decisions (a missed election, a
stacked SAFE, a participating preference, a personal guarantee) before they are made.

- **Cash decides survival; accrual decides value.** Runway comes from a cash forecast down to a
  floor, not cash divided by burn; the books are accrual so revenue, margin and value are real.
- **Close the books every month.** Numbers more than a month old steer nothing, and catch-up
  bookkeeping during a raise or a sale stalls the deal.
- **Some deadlines cannot be repaired.** The US 83(b) window (30 days), the UK section 431
  election (14 days), R&D credit elections and claim notifications, repurchase rights when a
  founder leaves: calendar them the day they start.
- **Choose the path before taking money.** Venture money mostly closes the bootstrapped path;
  raise only when the venture outcome is wanted and money buys a specific milestone.
- **Model dilution before signing anything.** Stacked SAFEs, pool top-ups and preferences cost
  founders more than headline valuations do.
- **Clean terms beat a high price.** Standard documents and a 1× non-participating preference at
  a fair valuation beat a bigger number with structure attached, in rounds and in sales.
- **Act with runway left.** Cut, raise or sell with nine to twelve months of runway, while
  alternatives exist; at three months every option is a bad one.
- **Stay diligence-ready.** A standing data room, signed IP assignments and a reconciled cap
  table turn diligence into days and remove what buyers use to cut the price.
- **Give the mechanism, then name the professional.** Tax, securities and employment rules
  differ by jurisdiction; explain how they work and the common practice, state which
  jurisdiction is assumed, and say where an accountant or counsel must decide.

Follow the company's existing setup first: its accounting software, accountant, equity platform
and documents. The defaults below are for new decisions.

## Route

| If the task is … | Read |
|---|---|
| Opening a business bank account, setting up or catching up the books, "which taxes do I file", Delaware franchise tax, reading the P&L or balance sheet, choosing an accountant, month-end close, R&D credits, deferred revenue | `references/bookkeeping-tax.md` |
| "How much runway do I have", a cash-flow forecast, calculating MRR and churn, the monthly finance pack, an 18-month model, default alive or burn multiple, too much cash in one bank, one dominant customer, "we are burning too fast", layoffs, a fractional CFO | `references/runway-forecasting.md` |
| "Should I bootstrap or raise?", angels vs VC vs revenue-based financing, grants and cloud credits, what to reach before a seed or Series A, a two-minute pitch, the monthly investor update | `references/funding-strategy.md` |
| A pitch deck, the data room for a round, SAFE vs priced round, explaining a term sheet, checking out an investor, running the investor pipeline, negotiating and closing a round | `references/fundraising-process.md` |
| Co-founder split, founder vesting and 83(b), equity for a hire or advisor, explaining an offer to a candidate, dilution through future rounds, option pool and 409A, someone leaving with equity | `references/equity-cap-table.md` |
| "Someone wants to buy the company", valuing or selling the business, due diligence and the data room, earn-out and escrow, integration after a sale, shutting down a product, winding the company down | `references/exit-due-diligence.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Banking | Business account in the company's name from day one; second bank at Launch | Cash above deposit-insurance limits → insured sweep or short-term government securities |
| Books | Company-owned accounting software, bank feeds, accrual basis, monthly close | Prototype with no revenue: cash basis is fine |
| Outside help | Accountant from incorporation; bookkeeper at Launch; fractional CFO at a priced round or first audit | |
| Runway | Forecast to a cash floor of two to three months of gross burn | Under six months left → weekly 13-week forecast |
| MRR | Normalized recurring, net of discounts; one-time fees, usage and tax excluded; counted until cancellation | Committed usage minimums are included |
| Funding | Bootstrap with customer funding until venture-scale evidence exists | Founder wants the venture path and money buys a specific milestone |
| Instrument | US: standard post-money SAFE at pre-seed and seed | Larger round or a lead wanting governance → priced round on model documents; UK angels relying on SEIS/EIS → advance subscription agreement; elsewhere → the local standard (convertible loan, BSA AIR) |
| Round size | 18 to 24 months of runway to the next round's milestones | |
| Founder equity | Equal or near-equal split with a written tie-break (`0x:company-building`); four-year vesting, one-year cliff, credit for time served; double-trigger acceleration; the tax election on vesting stock (US 83(b) within 30 days; UK section 431 within 14 days; elsewhere ask a local accountant at issuance) | Clear, durable differences in contribution |
| Employee equity | Options at a defensible current value (US: 409A appraisal; UK: EMI options, value usually agreed with HMRC); four-year vesting, one-year cliff; pool sized from the hiring plan | Other countries: the local scheme or a phantom plan, set up with local counsel |
| Exit | A process with several buyers; cash at close over earn-outs | |

By stage:

- **Prototype**: entity, bank account, accounting software with feeds, a filing calendar,
  founder vesting and 83(b), personal runway and a written kill date. Skip models, packs and
  data rooms.
- **Launch**: monthly close on accrual, MRR bridge, cash forecast, monthly finance pack,
  investor updates if funded, second bank, concentration tracking, a standing data room started.
- **Scale**: 18-month model with scenarios reviewed monthly, fractional or full-time CFO, audit
  readiness, a treasury policy, QoE-ready financials, regular option valuations (409A in the US).

## Before you call it done

1. Company and personal money are separate; no unexplained founder transfers sit in the books.
2. The last month is closed: bank, card and processor reconciled, deferred revenue rolled
   forward, suspense accounts at zero.
3. Every tax and entity filing has a date in a shared calendar and an owner.
4. Runway is quoted from a cash forecast to a stated floor, with the downside case beside it.
5. The MRR bridge closes exactly, its definitions are written down, and ARR is closing MRR × 12.
6. Cash above insurance limits is spread or in government securities, and a second bank and a
   second processor account are ready.
7. The largest customer's share of revenue is known and its loss is modeled.
8. Every SAFE, note and round was modeled in the cap table through the next two rounds, pool
   top-ups included, before signing.
9. Term sheet terms were compared with the standard-terms table and every deviation was listed
   for the founder.
10. Every US holder of vesting stock has a filed 83(b) with proof of mailing or online
    confirmation (or a recorded decision not to file); non-US holders have the local election
    (UK section 431) or written advice on file.
11. Every option grant has board approval, a strike at or above a current valuation (US 409A,
    UK HMRC-agreed EMI value, or the local rule), any required notification filed, and a
    matching cap-table entry.
12. IP assignments are signed by every founder, employee and contractor.
13. Advice touching tax, securities or employment law names the jurisdiction it assumes and the
    point where a professional must decide; no US-only mechanism (83(b), 409A, QSBS, Delaware,
    the SAFE, Form D) was offered to a company or person outside the US as if it applied there.

## Not this skill

- Prices, plans, CAC, LTV and margin per customer → `0x:pricing-monetization`
- Sales tax and VAT collection, invoices and payment reconciliation → `0x:payments-billing`
- Incorporation, founder agreements, the board, hiring and payroll setup → `0x:company-building`
- Cloud bills and infrastructure cost reduction → `0x:cloud-infrastructure`
- Technical due diligence on the codebase → `0x:engineering-leadership`
- Analyzing financial data with SQL or statistics → `data`
