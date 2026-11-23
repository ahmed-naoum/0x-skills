# Unit economics

Read this when: checking whether the business works per customer, plan or channel: break-even,
CAC, payback, LTV, gross margin and cost to serve per plan including AI inference, whether a
segment or channel is worth pursuing, or which customers and plans lose money.

By stage: at Prototype, log cost per account and know the break-even count; skip the rest. At
Launch, keep the one-sheet model with a blended column and margin per plan. At Scale, add a column
per channel and segment, and decide on marginal CAC.

## Definitions that get used wrong

Work monthly unless stated, and on gross margin, never on revenue alone.

| Term | Formula | Common mistake |
|---|---|---|
| ARPA | Recurring revenue ÷ paying accounts | Including one-time fees; counting annual contracts at the annual amount instead of the monthly equivalent |
| Gross margin (GM) | (Revenue − cost of revenue) ÷ revenue | Leaving out support, payment fees or inference (`price-setting.md` lists what belongs) |
| Contribution per account | ARPA × GM | Using ARPA instead |
| CAC | Sales and marketing spend in a period ÷ new paying accounts it produced | Counting only ad spend; dividing by sign-ups; ignoring the founder's selling time |
| Blended versus paid CAC | Blended divides by all new accounts; paid by those from paid channels only | Using blended CAC to justify paid spend: organic customers make the number look good |
| Payback, months | CAC ÷ contribution per account | Dividing by revenue instead of contribution |
| Logo churn | Accounts lost ÷ accounts at period start | Counting downgrades as retained |
| Revenue churn | Revenue lost to churn and downgrades ÷ revenue at period start | Netting expansion into it without saying so |
| LTV | Contribution per account ÷ monthly gross revenue churn (expansion excluded), capped | No cap: low early churn implies decades of revenue; netting expansion can push churn to zero or below and LTV to infinity |
| LTV:CAC | LTV ÷ CAC | Treating it as precise; it inherits every error above |

Conventions:

- **Cap lifetime at 3 to 5 years in LTV**, whatever churn implies. Young cohorts and tiny churn
  rates produce absurd lifetimes.
- **Below about 50 customers, churn is noise** (rule of thumb). Use a range (worst, expected, best) and look at
  cohorts, not one rate.
- **Lag CAC.** Spend in one month produces customers later; match spend to conversions using the
  typical time from first touch to first payment.
- **Cash payback and margin payback differ.** An annual prepayment larger than CAC recovers it in
  cash on day one while margin payback is unchanged. Track both: cash for runway, margin for whether the channel
  works.

## Break-even

```text
break-even accounts  = monthly fixed costs ÷ (ARPA × GM)
new accounts / month = accounts × monthly logo churn + growth target
```

Example: fixed costs $9,000 a month (tools, base infrastructure, a contractor, the founder's pay
target), ARPA $60, GM 80 percent, so contribution is $48 and break-even is about 188 paying
accounts. At 3 percent monthly logo churn, holding 188 accounts takes about 6 new paying accounts
every month before any growth.

- **Run it twice**: founder unpaid, and founder at a market salary. They describe different
  businesses, and the second is the one that lasts.
- **Then ask the realistic question**: at current traffic and conversion, how many months until
  that count? If the answer is years, the price, the segment or the cost base has to change.
  That is a pricing decision, not only a marketing one.
- **Fixed costs grow in steps** (a support hire, a larger database tier). Recompute at each step,
  not only when revenue changes.

Runway and cash forecasts → `0x:startup-finance`.

## The one-sheet model

One spreadsheet: inputs on top, outputs below, one column per channel or segment and a blended
column. Small enough to refresh monthly in minutes.

| Row | Type | Source |
|---|---|---|
| Spend: ads, tools, content, sales time at an hourly cost | Input | Accounting, ad platforms, time log |
| New paying accounts | Input | Billing provider, attributed by channel |
| ARPA, first year, monthly equivalent | Input | Billing provider |
| Gross margin for the plans this channel sells | Input | Cost per plan (below) |
| Monthly revenue churn | Input | Cohort data |
| Net expansion | Input, optional | Billing provider |
| CAC | Output | Spend ÷ new accounts |
| Contribution per account | Output | ARPA × GM |
| Payback, months | Output | CAC ÷ contribution |
| LTV, capped | Output | Contribution ÷ churn, capped at the lifetime cap |
| LTV:CAC | Output | LTV ÷ CAC |

Reading it, with widely used rules of thumb rather than laws:

- **LTV:CAC of about 3 or more and payback under about 12 months** for self-serve and
  small-business products. Enterprise products often accept longer payback, around 18 to 24
  months, because contracts are annual and retention is higher.
- **Payback is the more robust number** at small scale; it rests on fewer uncertain inputs than
  LTV, which multiplies every churn error.
- **Show sensitivity**: churn and CAC each at plus and minus 50 percent. A model that only works at
  the optimistic corner does not work.
- **Expansion changes everything**: with net revenue retention above 100 percent, a cohort grows
  without new sales. Include it only from measured cohorts, never from hope.

## Cost to serve and gross margin per plan

An average gross margin hides losing plans. Compute it per plan, and per account wherever cost is
variable.

| Cost component, most often forgotten first | How to measure |
|---|---|
| AI inference | Input, output and cached tokens (or compute) per account from request logs × current price per unit, per model |
| Support and onboarding | Tickets or minutes per account per plan × loaded hourly cost |
| Payment processing | The provider's percentage plus its fixed fee per charge; the fixed part dominates small monthly charges |
| Per-account third-party services | Email and SMS volume, maps, search, storage, per-seat licences paid to vendors |
| Shared infrastructure | Allocated by a driver: requests, storage or compute share per plan |
| Free accounts | Their total cost, treated as acquisition cost and divided by the conversions they produce |

AI inference:

```text
inference cost per account per month =
  sum over actions (actions per month × tokens per action × price per token)
```

- **Measure from logs per account, not from estimates.** Tokens per action vary several-fold with
  input size, retrieved context, tool calls, retries and conversation length.
- **Report the distribution per plan**: p50, p90 and p99 cost per account against the plan price.
  The p50 says whether the price is right; the p99 says whether a cap is needed.
- **Count invisible spend**: retries, failed calls, background jobs, evaluation and test traffic.
  No customer action shows them, but the invoice does.
- **Recompute when model prices or the model choice change**, and whenever a feature starts
  calling the model more often.
- Lowering cost per call (caching, smaller models, batching) → `0x:ai-features`; lowering the
  hosting bill → `0x:cloud-infrastructure`.

## Is a segment or channel worth pursuing?

Fill one sheet column per segment or channel, then:

| Result | Decision |
|---|---|
| Payback within target, retention at or above average, room to grow | Invest; raise spend in steps and re-measure CAC at each step |
| Payback within target, volume capped (one community, one partner) | Keep it, but do not plan growth on it |
| Payback beyond target, retention clearly better than average | Possibly worth it if cash allows; confirm with LTV and the cash plan |
| Payback beyond target, retention average or worse | Stop, or change the offer for that segment: price, plan, onboarding |
| Customers cannot be attributed to it | Do not scale spend; fix attribution first (`0x:product-analytics`) |

- **Marginal CAC rises.** The next dollar in a paid channel buys customers at a higher cost than
  the average so far. Decide on the cost of the last increment, not the channel average.
- **Channels bring different customers.** Customers from deal sites, coupons or broad paid
  campaigns often retain worse than those from referrals or search. Use per-channel churn in the
  per-channel LTV, not blended churn.
- **Segments differ in cost to serve.** A small-customer segment with heavy support needs can show
  a fine CAC and a poor margin; check both before choosing it.
- Channel choice and campaigns → `0x:growth-marketing`.

## Finding and fixing customers or plans that lose money

1. **Instrument cost per account**: inference, support time, storage, messaging. Without it this
   procedure cannot start.
2. **Rank accounts by contribution** (revenue minus direct cost). List those below zero and those
   below target margin, and sum them by plan.
3. **Classify the cause and apply the matching fix:**

| Cause | Fix |
|---|---|
| Heavy user on a flat plan | Fair-use cap with notice, a usage tier or add-on, or a plan with a fitting allowance |
| Legacy price or an old discount | Migrate at renewal (`discounts-price-changes.md`) |
| Small account with heavy support needs | Self-serve help, support levels by plan, paid onboarding |
| Abuse: shared logins, scripting, many free accounts per person | Enforce terms, rate limits, verification (`0x:auth-identity` for abuse defense) |
| A whole plan below target margin | Reprice or restructure it for new customers, then migrate existing ones |
| An expensive feature used by few | Move it to an add-on or a higher plan |

4. **Talk to the top loss-makers before changing their terms.** Heavy users are often the most
   engaged customers and the best candidates for a higher plan or a custom deal; a cap imposed
   without warning turns them into public critics.
5. **Change terms for new customers first**, then for existing ones with notice.
6. **Re-check margin per plan monthly** until it is stable, then at each pricing review.

Ending a customer relationship is a legitimate last step for persistent abuse or an account that
stays margin-negative and refuses every change: give notice, help them export their data, and end
at a period boundary.

## Ask the user

- **What are the monthly fixed costs, and what should the founder be paid?** Needed for
  break-even. Default: model both unpaid and market salary.
- **What counts as acquisition spend?** Decides CAC. Default: all sales and marketing spend plus
  the founder's sales and marketing hours at an hourly cost.
- **What payback can the cash position support?** Decides which channels to fund. Default: 12
  months for self-serve, longer only with cash or annual prepayment to cover it.
- **Would you change terms for the heaviest users?** Decides how losing accounts are fixed.
  Default: talk first; caps for new customers at once, for existing ones with notice.
- **How long may a customer lifetime be assumed?** Caps LTV. Default: 3 years.
