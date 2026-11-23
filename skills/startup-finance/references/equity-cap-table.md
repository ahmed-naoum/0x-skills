# Equity and the cap table

Read this when: splitting equity between co-founders, setting up founder vesting, granting
options to hires or advisors, explaining an equity offer to a candidate, modeling dilution from
SAFEs and rounds, creating an option pool and its valuation, or handling equity when someone leaves.

## Founder split and vesting

Vesting matters more than the split. Default to an equal split between co-founders who start
together full-time in comparable roles; deviate only for explicit, durable reasons (one founder
worked a year alone, put in significant cash, or will stay part-time). Weeks spent negotiating
52/48 are wasted; a split one founder resents is a time bomb. The founder agreement and IP
assignment are `0x:company-building`.

- **Vesting**: four years with a one-year cliff, monthly after. Founders who already worked on
  the company get credit, for example a quarter vested at the start for a year of prior work.
- **Mechanics** in a US corporation: founders buy restricted stock at a nominal price (paid in
  cash or by assigning their technology), and the company holds a right to repurchase unvested
  shares at cost if the founder leaves. The shares are owned from day one; vesting is the lapse
  of the repurchase right. In the UK and much of Europe the same effect comes from leaver
  provisions in the articles or shareholders' agreement (unvested shares transfer back at
  nominal value), with different tax treatment (below).
- **Acceleration**: double-trigger (a sale, then termination without cause within a set period)
  is the norm; single-trigger acceleration on any sale worries acquirers and investors.
- **No vesting at all**: a co-founder who leaves after three months keeps the full stake, and
  investors will make fixing it a condition of investing.

## The 83(b) election (US): the deadline that cannot be fixed

On receiving stock subject to vesting, a US taxpayer can elect under section 83(b) to be taxed
now on its value at issuance, which for founder stock bought at nominal value is close to zero.
Without the election, each vesting date is a taxable event on the shares' value that day; after
a funding round that can mean a large tax bill on shares that cannot be sold.

- Deadline: **30 days from the date the stock is issued**. No extension, no late filing, no
  repair afterwards short of restructuring the grant.
- File with the IRS by certified mail with return receipt, or online with Form 15620 through an
  IRS online account (available since mid-2025; use one method, never both). Give a copy to the
  company and keep the proof permanently. Form 15620 is optional on paper; a signed statement
  with the required content also works.
- Applies to restricted stock and to early-exercised options; not to ordinary option grants,
  which are not stock yet.
- Non-US founders receiving stock in a US company check with an accountant at issuance: the
  election can still matter for US tax, and home-country rules differ.
- UK: shares with leaver or vesting restrictions are usually restricted securities; employer
  and employee sign a joint section 431 election within 14 days of acquisition and keep it (it
  is not sent to HMRC). Without it, value released as restrictions lift can be taxed as
  employment income. Other countries have their own regimes; ask a local accountant at
  issuance, not at vesting.

## Maintaining the cap table

The legal record is the board and stockholder approvals plus the stock ledger; the cap table must
agree with them.

| Stage | Tool |
|---|---|
| Prototype, founders only | A spreadsheet: holder, class, shares, price, issue date, vesting schedule, 83(b) filing date, certificate or ledger number |
| First option grant, SAFE or priced round | An equity management platform; it also produces option paperwork and 409A valuations |

- Track authorized, issued and reserved shares separately, plus a list of SAFEs and notes with
  amount, cap and discount.
- **Fully diluted** = issued shares + all options granted + the unissued pool + shares reserved
  for warrants, with SAFEs and notes added as an estimate of conversion. Ownership percentages in
  offers and investor documents are quoted on this basis.
- After every grant, round, repurchase or exercise, update the table the same day and file the
  signed approval with it.

## Modeling dilution

Each round, existing holders are multiplied by roughly (1 − new investors' share − pool top-up),
since the pool top-up created inside the pre-money falls on existing holders.

Illustrative path for two equal founders (simplified: a post-money SAFE holding a fixed share of
the capitalization before the seed round; pool targets set post-money):

| Holder | After pre-seed SAFE (as converted) | After seed: 25% sold, pool to 10% | After Series A: 20% sold, pool to about 12% |
|---|---|---|---|
| Founders together | 90% | 58.5% | about 44% |
| Pre-seed SAFE, 750k at a 7.5M post-money cap | 10% | 6.5% | about 5% |
| Seed investors | | 25% | 19% |
| Option pool, granted and unissued | | 10% | about 12% |
| Series A investors | | | 20% |

- Build the model before signing any SAFE or term sheet, and run it through the next two rounds,
  not only this one. Founders are surprised by stacked SAFEs and pool top-ups, not by the
  headline round.
- The exact conversion depends on each SAFE's definition of capitalization and how the pool
  top-up is counted; the equity platform or counsel produces the binding numbers.
- Model a sale in the same sheet: ownership percentages say nothing about proceeds until the
  liquidation preferences are applied (`fundraising-process.md`).

## Sizing grants for hires and advisors

Size grants as a percentage band by role and hiring order, convert to a share count on the fully
diluted basis, and record the reasoning so later grants stay consistent. Use the benchmark data
equity platforms and compensation surveys publish for the current market; the bands below are
rules of thumb for a seed-stage company and shrink as the company de-risks.

| Role | Rule-of-thumb band at seed |
|---|---|
| First few engineers and key early hires | about 0.5 to 1.5% |
| Senior leader hired early (head of engineering, of sales) | about 1 to 3% |
| Later employees | about 0.1 to 0.5% |
| Advisors | about 0.1 to 1%, vesting monthly over one to two years, little or no cliff |

- Employee vesting: four years, one-year cliff, monthly after.
- Offer a choice of cash and equity mixes; it shows what the candidate values and avoids
  overpaying in both.
- Advisors: tie the grant to a defined commitment (hours per month, introductions, a specific
  expertise). Advisor value is front-loaded and most advisor grants are too large; paying cash
  for a specific piece of work is often cleaner.
- In the US, contractors and advisors get non-qualified options (NSOs) or restricted stock;
  incentive stock options (ISOs) are for employees only.
- Size the pool from the hiring plan: sum the planned grants until the next round. That number,
  not a convention, is the pool to ask for.
- Refresh grants for strong performers once most of their initial grant has vested; a
  four-year cliff in motivation is otherwise built in.

## Explaining an equity offer honestly

A candidate deciding on an offer needs these facts, in writing:

- Number of options, the fully diluted share count, and the resulting percentage.
- Strike price (US: fair market value from the 409A valuation; UK: the HMRC-agreed EMI value)
  and the cost to exercise everything.
- The last preferred price and why common is worth less: preferred shares get their liquidation
  preference first, so the preferred price is not the value of an option.
- Vesting schedule, cliff, and what happens in a sale (acceleration or not).
- The exercise window after leaving, and the options' tax type with its consequence in a
  sentence (US ISO: no regular tax at exercise, but possible alternative minimum tax; US NSO:
  ordinary income on the spread at exercise; UK EMI: usually no income tax at exercise if the
  strike was at least market value at grant; elsewhere the local rule). Suggest a tax adviser.
- Expected dilution from future rounds.
- Liquidity: no market for the shares until a sale or IPO, which may never come.

Show outcomes at a few exit values, including zero, after expected dilution and preferences.
Never say "your options are worth X" using the preferred price or a hoped-for valuation: it is
misleading, and it is what disappointed employees remember and repeat.

## Option pool and fair market value

Setting up in the US:

1. The board adopts an equity incentive plan reserving the pool; stockholders approve it (needed
   for ISOs, within 12 months of board adoption).
2. An independent 409A valuation before the first grant. An appraisal by a qualified independent
   firm gives the safe-harbor presumption that the strike price is fair market value.
3. Grants approved by the board or a delegated committee, with the strike at or above fair
   market value on the grant date. The grant date is the approval date, not the offer letter
   date; batch grants into regular approvals.
4. Refresh the 409A at least every 12 months and after any material event: a priced round, a big
   change in revenue, an acquisition offer. Do not grant between signing a term sheet and the new
   valuation.

Options granted below fair market value can fail section 409A, and the employee, not the
company, then faces income inclusion as the options vest, an additional 20% federal tax and
interest, with some states adding their own.

Other rules that bite:

- ISO limits: only ISOs first exercisable in a calendar year up to 100,000 USD of grant-date value
  keep ISO treatment; holders of more than 10% need a strike of 110% of fair market value and a
  term of at most five years.
- US private-company grants rely on Rule 701; when more than 10 million USD of securities is
  sold under it in 12 months, financial statements and risk disclosure must go to holders. The
  equity platform or counsel tracks it.
- UK: EMI options are the standard tax-advantaged scheme for qualifying companies (size and
  activity limits, raised in April 2026; check current ones). Agree the share value with HMRC
  before granting (optional, but it removes the main dispute), and notify each grant to HMRC by
  6 July after the end of the tax year of grant (the rule for grants since April 2024): a
  missed notification loses the tax advantage unless HMRC accepts a reasonable excuse. A leaver
  keeps EMI treatment only by exercising within 90 days of leaving.
- EU: rules differ widely by country; many startups use virtual (phantom) share plans where real
  options are taxed badly.
- Employees in other countries: a grant under a US plan can create local tax and securities
  obligations; use the platform's international support or local counsel before the first
  non-US grant.

## Departures

| Situation | Default outcome | Decide |
|---|---|---|
| Founder leaves | Company repurchases unvested shares at original cost under the repurchase right; vested shares stay | Exercise the repurchase in writing within the window in the stock purchase agreement; a missed window can leave the shares with the founder |
| Founder without vesting leaves | Keeps everything | Negotiate a buyback or voluntary reverse vesting; investors will require it |
| Employee leaves | Unvested options return to the pool; vested options exercisable within the post-termination window (90 days is the common US default, matching the ISO rule; UK EMI also needs exercise within 90 days for the tax advantage) | Whether to extend the window |
| Extended exercise window | Gives departing employees time to afford exercise | US: ISOs exercised more than three months after employment ends are taxed as NSOs, and extending the window on existing options is a modification that usually turns ISOs into NSOs; keep any extension within the option's original term to stay clear of 409A problems |
| Termination for cause | Usually as above; some plans allow forfeiture | Read the plan wording before relying on it |
| Sale of the company | The plan decides: options assumed by the buyer, cashed out, or accelerated | Single or double trigger, set at grant |
| UK or EU good leaver and bad leaver | Bad leavers may lose vested shares or sell at nominal value | Enforceability varies; draft with counsel |

For any departure: board approval of the repurchase or window change; a written notice with the
exact exercise deadline and cost; payment for repurchased shares; cap table and platform
updated; IP assignment confirmed and company property returned (`0x:company-building`).

Extending the exercise window to several years costs the company mostly dilution and overhang
(in the US the employee loses ISO treatment, and the company withholds tax at exercise), and is
the cheapest generosity available in a layoff. Decide it as a policy, not case by case, so
treatment is consistent and defensible.

## Ask the user

- **How do the founders want to split equity, and why?** Default: equal, with four-year vesting,
  a one-year cliff and credit for time already served.
- **Has every founder made the tax election on vesting stock (US 83(b) within 30 days; UK
  section 431 within 14 days)?** If not, stop and involve counsel now. Default: assume not made
  until proof of filing or the signed election is seen.
- **What equity philosophy for hires: more cash or more equity?** Default: market cash where
  affordable, equity from the rule-of-thumb bands, and a choice of mixes offered.
- **What exercise window should leavers get?** Default: 90 days, with extension decided as a
  written policy.
- **Single- or double-trigger acceleration for founders and executives?** Default: double trigger.
- **In which countries are the people receiving equity?** Default: US plan rules only for US
  residents; check local rules before any other grant.
