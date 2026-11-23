# Cash, runway and financial planning

Read this when: asked how much runway is left, building or updating a cash forecast or financial
model, computing MRR and churn from billing data, preparing the monthly finance numbers, deciding
whether and how to cut burn, moving cash between banks, or worrying about one customer or processor.

## Runway: compute it from a forecast

| Term | Definition |
|---|---|
| Gross burn | All cash out in a month |
| Net burn | Cash out minus cash in from customers in a month; excludes equity, loans and other financing |
| Simple runway | Cash ÷ average net burn of the last three months. A sanity check only |
| Real runway | Months until the forecast cash balance falls below the cash floor |
| Cash floor | The balance that pays final payroll, accrued obligations and an orderly wind-down; rule of thumb, two to three months of gross burn |

Simple runway is wrong whenever burn is changing, which is most months: committed hires, annual
renewals, tax payments and seasonal collections all move it. Report real runway.

- Forecast monthly for 18 months. When real runway drops under six months, forecast the next 13
  weeks weekly, because payroll dates and large payments then decide survival.
- Rows: opening cash; receipts by type (subscriptions, annual prepayments, invoices collected on
  terms, tax refunds and credits); payments by type (payroll with employer costs, contractors,
  cloud, software, marketing, rent, taxes, debt service); closing cash.
- Receipts are cash collections, not MRR: annual plans arrive in renewal months, invoices on
  terms arrive weeks after issue, processor payouts lag sales by days.
- Include everything already committed: signed offers, annual contracts, vendor price
  increases, the next tax installment.
- Each month, replace the forecast month with actuals and record the variance. A forecast that
  is persistently optimistic is a finding about the assumptions, not bad luck.

## Personal runway and the kill date

For a founder not drawing a full salary, personal runway is the real deadline: the company ends
when the founder has to take a job.

- Personal runway = savings the founder is willing to spend ÷ monthly personal costs, after
  setting aside taxes owed, health cover and an emergency reserve that is never touched.
- Decide in advance the total personal money that goes into the company. Funding payroll with
  personal credit cards or personally guaranteed loans is a decision to make explicitly, with a
  partner if there is one, not a drift.
- Write the kill date while calm: a date, the evidence that must exist by then (a number of
  paying customers, an MRR level, a retention level), and what happens otherwise (one pivot,
  shut down, or return to employment). Review it in the monthly pack.
- Leave enough company cash for the wind-down (`exit-due-diligence.md`); running to zero turns an
  orderly shutdown into unpaid creditors.
- Founder salary once funded: enough that money worries do not distort decisions, well below
  market. Investors look at it, and it is the first lever in a burn cut.

## MRR, expansion and churn from billing data

Decide the definitions once, write them down, apply them identically every month. Investors and
acquirers recompute MRR from the billing export; a number that does not survive that costs
credibility for every other number.

| Case | Rule |
|---|---|
| Annual or quarterly plan | Normalize: annual ÷ 12, quarterly ÷ 3 |
| Discounts | Net of recurring discounts. A time-limited discount ending shows as expansion unless tracked as its own discount roll-off line; pick one and keep it |
| One-time fees, setup, services | Excluded |
| Usage and overage | Excluded unless contractually committed; report usage revenue beside MRR |
| Taxes | Excluded |
| Trials | Excluded until the first paid period |
| Past due, in dunning | Counted until the subscription is canceled; churn dated at cancellation |
| Canceled at period end | Counted until the period ends; shown as scheduled churn |
| Paused | Excluded while paused; resumption is reactivation |
| Multiple currencies | Converted at fixed planning rates; currency effects reported separately |

The bridge must close exactly every month:
`opening + new + expansion + reactivation − contraction − churned = closing`.

Compute it from one row per customer per month end, dense (a zero row when inactive), starting
at the first billing month so the first opening balance is right:

```sql
with m as (
  select customer_id, month, mrr,
         lag(mrr, 1, 0) over w as prev,
         bool_or(mrr > 0) over (partition by customer_id order by month
           rows between unbounded preceding and 1 preceding) as active_before
  from customer_mrr
  window w as (partition by customer_id order by month)
)
select month,
  sum(mrr) as closing_mrr,
  sum(case when prev = 0 and mrr > 0 and not coalesce(active_before, false) then mrr else 0 end) as new_mrr,
  sum(case when prev = 0 and mrr > 0 and active_before then mrr else 0 end) as reactivation_mrr,
  sum(case when prev > 0 and mrr > prev then mrr - prev else 0 end) as expansion_mrr,
  sum(case when prev > 0 and mrr > 0 and mrr < prev then prev - mrr else 0 end) as contraction_mrr,
  sum(case when prev > 0 and mrr = 0 then prev else 0 end) as churned_mrr
from m
group by month
order by month;
```

- Gross MRR churn = (churned + contraction) ÷ opening MRR.
- Net MRR retention for a month = (opening + expansion − contraction − churned) ÷ opening.
- Annual net revenue retention = MRR today from customers active 12 months ago ÷ their MRR then.
  Compute it on that cohort; compounding a monthly figure misleads.
- Logo churn = customers lost ÷ customers at the start of the month; the month's new customers
  are not in the denominator.

Traps: annual plans churn only at renewal, so monthly churn looks excellent for eleven months
(report renewal rates for annual cohorts separately). ARR is closing MRR × 12; annualizing a month
inflated by usage or one-time fees is the overstatement investors catch first. The billing
provider's dashboard MRR follows its own rules: use it as a cross-check, or adopt its rules
explicitly. Booked subscription revenue and MRR track each other; a widening gap is a definition
or data error (`bookkeeping-tax.md`).

## The monthly finance pack

One page, same layout every month, produced right after the close, for the founders and board,
summarized for investors (`funding-strategy.md`).

| Line | Definition |
|---|---|
| Cash at month end | Reconciled bank and money-market balances |
| Net burn | The month and the trailing three-month average |
| Real runway | Months to the cash floor from the forecast, base and downside |
| MRR and its bridge | As above |
| Revenue and gross margin | From the books, accrual basis |
| Opex by function vs plan | With one sentence on each variance above a set threshold (10% is common) |
| Burn multiple | Net burn ÷ net new ARR, trailing quarter |
| CAC payback | Sales and marketing spend ÷ (new MRR × gross margin), in months; per-channel analysis is `0x:pricing-monetization` |
| Concentration | Largest customer and top five as shares of MRR |
| Receivables | Amount more than 30 days overdue |
| Headcount | Actual vs plan |
| Milestones | Status against the kill date or the next round's milestones |

A pack that only reports is half done: end it with the two or three decisions the numbers call for.

## The 18-month model with scenarios

Eighteen months covers the runway a round is meant to buy plus the time to raise the next one.

- **Structure**: one assumptions sheet holding every input; calculation sheets for revenue,
  headcount and other costs; monthly P&L and cash flow; a summary. No number typed into a formula.
- **Revenue from drivers** matching the sales motion. Self-serve: visitors × signup rate × paid
  conversion × average revenue per account. Sales-led: pipeline × win rate × contract value,
  shifted by the sales cycle. Churn and expansion from actual cohorts. Never revenue as a share
  of the total market.
- **Headcount**: role, start month, salary, a fully loaded multiplier for employer taxes,
  benefits, equipment and software (roughly 1.2 to 1.4 times salary in the US as a rule of
  thumb; different elsewhere), recruiting lag, ramp time for sales hires.
- **Cost of revenue** per unit of usage (hosting, model tokens, processing fees, support), so
  gross margin moves with growth instead of staying a fixed percentage.
- **Cash timing**: annual-prepay mix, payment terms, payout delays, tax payments, credit refunds.
- **Scenarios**: base (recent trends continue); downside (growth at half of base, higher churn,
  the next round six months late or absent); upside. The plan is acceptable only if the downside
  never breaches the cash floor before a pre-agreed cut triggers. Write the triggers: "if MRR is
  below X by month Y, cut Z".
- **Sanity checks**: implied growth against the last six months; hiring pace against the
  ability to recruit; revenue per employee; gross margin; burn multiple by quarter.

## Burn multiple and default alive

**Burn multiple** = net burn ÷ net new ARR over the same period: how much cash buys each new
dollar of recurring revenue. The scale its author (David Sacks) proposed: under 1 excellent, 1
to 1.5 great, 1.5 to 2 good, 2 to 3 suspect, above 3 bad. It applies to venture-funded
companies past early revenue; before that it is noise.

**Default alive** (Paul Graham's term): with expenses held where they are, plus hires already
committed, and revenue growing at its recent rate, does revenue cover expenses before cash
reaches the floor?

```ts
// Monthly amounts; growth as a fraction (0.08 = 8% month over month).
function defaultAlive(cash: number, floor: number, revenue: number,
                      expenses: number, growth: number, horizon = 60) {
  for (let month = 1; month <= horizon; month++) {
    revenue *= 1 + growth;
    cash += revenue - expenses;
    if (cash < floor) return { alive: false, month };
    if (revenue >= expenses) return { alive: true, month };
  }
  return { alive: false, month: horizon };
}
```

- Use the trailing three-month growth rate, then rerun at half of it. Alive only at the
  optimistic rate means dead.
- Default dead leaves two honest options: cut now until default alive, or raise with evidence
  that investors will fund it (term sheets, not enthusiasm). Decide with nine to twelve months of
  runway left; at three months only bad options remain.

## Banks, processors and reserves

The 2023 failure of Silicon Valley Bank left companies holding all their cash there unable to
reach it for payroll until regulators stepped in. Plan as if nobody steps in next time.

- **Two banks**, both open, funded and connected to payroll and card issuers before they are
  needed. The operating bank holds about two to three months of burn.
- **Above deposit-insurance limits** (a fixed amount per depositor per bank: FDIC in the US,
  national schemes in the UK and EU; check the current figure), hold the excess in an insured
  cash sweep program that spreads deposits across many banks, or in short-term government
  securities or a government money market fund held in custody.
- **Treasury policy**, a few lines approved by the board when there is one: allowed instruments
  (insured deposits, short-term government debt, government money market funds), maximum per
  institution, maturities laddered within 12 months. Runway money is not for equities, crypto or
  yield-chasing.
- **Processor risk**: processors can delay payouts, impose a rolling reserve or close an account,
  usually after a dispute spike, a sudden volume jump or a category review. Keep payouts automatic
  and frequent so funds do not pile up there; warn the processor before a launch or big sale;
  keep a second processor account approved and tested; hold cash outside the processor covering
  at least a month of expected payouts. Dispute control is `0x:payments-billing`.
- **Access**: at least two people can operate each bank account, with strong second factors and
  documented recovery (`0x:web-security` for account hardening).

## Customer concentration

- Measure the largest customer and the top five as shares of MRR every month. Investors and
  acquirers start discounting when one customer passes roughly 10 to 20% of revenue (a rule of
  thumb; US public companies must disclose customers above 10%).
- Model "largest customer leaves" and know the runway that remains.
- Reduce it on every side: in the contract (longer terms, notice periods, auto-renewal); in the
  relationship (several champions, not one); in the business (grow other segments deliberately,
  decline custom work only that customer will use, since it builds dependency into the code as
  well as the revenue).
- The same reasoning applies to a single channel or platform (one app store, one marketplace,
  one ad network) supplying most new revenue.

## Cutting burn

Cut once, deep enough to reach default alive or at least 18 to 24 months of real runway on the
downside case, rather than in several rounds. Repeated small cuts destroy morale faster than one
clear one.

1. Spend with no measurable return: unused seats, duplicated tools, events, paid channels
   without acceptable payback.
2. Renegotiate: list every contract with renewal date and notice period; ask vendors for
   downgrades, payment plans or startup programs; switch annual prepayments to monthly when cash
   matters more than the discount. Cloud cost work is `0x:cloud-infrastructure`.
3. Contractors and agencies.
4. People, if the above does not close the gap. Founder salaries move first and visibly.

Reprioritize before cutting people: choose the few projects that drive revenue or retention,
stop the rest, then size the team for those. Across-the-board percentage cuts keep every project
alive and understaffed. Involve employment counsel before announcing any reduction.

| Jurisdiction | Main obligations |
|---|---|
| US | Final-pay timing set by state law (some states require payment on the last day) and state rules on accrued vacation; federal WARN notice applies to larger employers, and some states set lower thresholds; benefits-continuation notices; severance in exchange for a release, where employees aged 40 or over must get time to consider (21 days, or 45 in a group program with required disclosures) and 7 days to revoke |
| UK | Fair selection and consultation; notice; statutory redundancy pay after two years' service; collective consultation and government notification when 20 or more redundancies at one establishment fall within 90 days |
| EU | Consultation with employee representatives or works councils where they exist; long statutory notice periods in several countries |

Execution: selection criteria decided and written first; affected people told individually
first, the rest of the team the same day with the new plan and runway, investors before or on
that day. Pay severance where cash allows and consider extending option exercise windows
(`equity-cap-table.md`); how departures are treated decides future hiring.

## When to bring in a fractional CFO

Ladder: founder with a bookkeeper → accounting firm with a controller reviewing the close →
fractional CFO (part-time, on retainer) → full-time CFO at Scale.

Bring one in when any of these appears: a priced round where investors will diligence the model;
a first audit required by investors, a lender or a large customer; contracts mixing subscription,
usage and services; more than one entity or country; a debt facility with covenants; quarterly
board reporting; an acquisition approach. Choose someone who has done the next step (raised that
round, run that audit), scope the work in hours and deliverables, and keep bookkeeping separate:
a CFO doing categorization is expensive bookkeeping.

## Ask the user

- **How much personal money goes into the company in total, and what date and evidence end the
  attempt?** It sets the real deadline. Default: write one now from current savings and costs.
- **What cash floor is acceptable?** It decides when runway "ends". Default: two to three
  months of gross burn.
- **Is a raise planned, and when?** Default: the base case assumes no new money.
- **How are past-due subscriptions treated in MRR?** It changes churn timing. Default: counted
  until canceled.
- **What risk is acceptable for cash reserves?** Default: insured deposits and short-term
  government securities only.
- **Is reducing headcount on the table if the downside case arrives?** Default: plan the
  non-people cuts first and name the trigger at which people cuts begin.
