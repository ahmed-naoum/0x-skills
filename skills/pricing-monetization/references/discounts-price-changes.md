# Discounts and price changes

Read this when: a customer asks for a discount; setting the annual-plan incentive; planning a
promotion or coupon; raising prices; announcing any pricing change; running the periodic pricing
review; or moving customers off old plans and retiring prices.

## Discount policy

Write the policy before the first request. Without it the founder decides under pressure on a
call, every customer ends up on a different price, and each of those prices becomes the renewal
baseline.

A discount is a trade. Give price only for something worth money:

| The customer gives | Typical discount (rule of thumb) |
|---|---|
| Annual prepayment instead of monthly | About 15 to 20 percent ("two months free" is 16.7 percent) |
| Multi-year commitment | A price lock for the term, or a few extra points per added year |
| Larger volume (seats, usage) | Built into graduated tiers, not negotiated ad hoc |
| Case study, logo use, reference calls | Small and time-limited, with the deliverable written into the order |
| Signature by a date | Small, and only when the date matters to you too (a launch, a quarter end) |
| Nonprofit, education, early-stage startup | A fixed published percentage with proof of eligibility |

- **Never discount for nothing.** A discount without a trade tells the buyer the list price was a
  bluff, and they will ask again at renewal.
- **Cap it and own it.** Write the maximum and who may approve it. For a solo founder: anything
  beyond the table needs a written reason recorded with the deal.
- **Give discounts an end date.** "First-year discount" or "until renewal" on the order; renewal
  reverts to list or to an agreed price. An open-ended discount becomes the price.
- **Record list price and discount separately**, in the billing provider (as a coupon or discount
  object) and with the deal record, so reports show real price realization and the renewal knows
  what was granted.
- **Prefer giving more over charging less**: extra seats, a longer trial, onboarding help, a higher
  plan at the lower price for a period. These protect the list price.
- **Know what a discount costs.** At 75 percent gross margin, a 20 percent discount needs about 36
  percent more customers for the same gross profit (margin per customer falls from 0.75 to 0.55
  of list). The lower the margin, the worse it gets.

Negotiating a specific deal → `0x:sales-support`.

## Annual plans

- **Offer annual on every paid self-serve plan from Launch.** Annual customers mostly leave only
  at renewal (subject to your refund terms and consumer cancellation rights), pay a year of cash
  upfront, and incur one fixed per-charge fee instead of twelve.
- **Incentive: about two months free.** Larger annual discounts make the monthly price look like a
  penalty and give away revenue from customers who would have paid annually anyway.
- **Default toggle position**: annual for B2B (buyers budget per year), monthly for consumer
  products (the monthly number is what they compare). Either way, the amount billed and the
  period must be unmistakable.
- **Prompt annual at the right moments**: after activation, after the second or third monthly
  renewal, at upgrade, and before a price increase (to lock in the current price).
- **Decide refund and cancellation terms for annual plans before selling them**: no refund after a
  short window, prorated refund, or account credit. Consumer rules on refunds and cancellation
  differ by jurisdiction (`0x:privacy-compliance`).
- **Cash is not revenue.** Annual prepayment is recognized over the year; plan cash accordingly
  (`0x:startup-finance`).

## Promotions and coupons

Promotions are acquisition spend. They must not teach customers to wait for the next sale.

- **Few, with a reason, and dated**: launch, a major release, or a seasonal event the market
  already expects (consumer and prosumer). No recurring site-wide sales in B2B.
- **New customers only, first period only**: "40 percent off the first three months" or "launch
  price for the first year", never a permanent discount.
- **Prefer promoting annual plans**: the discount buys a year of retention.
- **Restrict codes**: limited redemptions, an expiry date, first-time customers only, specific
  plans. Public codes end up on coupon sites. Give each partner or campaign its own code so
  attribution works.
- **Existing customers will see it.** Decide in advance: extend it to them as a credit, or keep it
  new-customer-only and state that rule on the offer.
- **Measure promotion cohorts separately**: retention after the discount ends, and how many would
  have bought anyway. Heuristic: if most new sales carry a coupon, the list price is fiction;
  change the price instead.

## Raising prices

The most common pricing mistake is never raising them: a product that improved for two years at
the same price has given the improvement away.

**Break-even churn.** With a price rise of x, revenue holds if at most x ÷ (1 + x) of affected
customers leave. A 20 percent increase breaks even on revenue at about 17 percent of them lost.
Because departing customers also stop costing money, gross profit holds up to x ÷ (GM + x) lost:
about 21 percent at 75 percent gross margin. Judge the measured churn against these numbers, not
against zero.

Sequence:

1. **Justify it.** List what improved since the customer's price was set: features, performance,
   support, and cost increases. If nothing did, reconsider.
2. **Pick the scope.** New customers only (lowest risk; start here), new and existing at their
   next renewal, or a plan restructure (`packaging-tiers.md`).
3. **Pick the grandfathering policy for existing customers:**

| Policy | Use when | Cost |
|---|---|---|
| Full grandfathering, old price indefinitely | Small early base that carried the product; the increase targets new customers | Legacy price debt that grows; many price versions to maintain |
| Time-limited, old price for 6 to 12 months | The default | A second announcement when it ends |
| At next renewal, after notice | Modest increase and clearly added value | Highest churn risk; needs the strongest justification |
| Choice: stay on the legacy plan as is, or move to the new plan | Restructures where new plans add value | Two plan sets until migration |

4. **Offer a lock-in**: switch to annual at the current price before the change date.
5. **Announce** (next section), then change prices in the billing provider on the stated date.
   Moving the date after announcing it teaches customers that complaints work.
6. **Measure for two to three billing cycles**: cancellations and downgrades in affected cohorts
   against the same months before; tickets mentioning price; revenue per affected customer before
   and after; uptake of the annual lock-in. Compare with break-even churn.

Changing prices on live subscriptions → `0x:payments-billing`.

## Announcing a change

- **Notice**: 30 days for monthly customers by default, longer for large business accounts;
  annual customers get notice well before their renewal. Consumer rules differ by jurisdiction,
  and some set a window rather than a minimum: California's automatic-renewal law requires the
  fee-change notice between 7 and 30 days before the change, so an earlier announcement needs a
  second notice inside that window. Many consumer-law regimes also require the terms to reserve
  the right to change prices and to let the customer cancel. App stores require subscribers to
  opt in to increases above their thresholds or where local law demands consent. Check
  `0x:privacy-compliance` before announcing.
- **Email from a named founder, plus an in-app notice.** State what changes, from when, why
  (concrete improvements and costs), what this customer will pay in their currency and period,
  their options (lock in annual, change plan, cancel), and who to reply to.
- **One number per customer.** Compute and include each customer's new price; "prices are
  changing" without their number produces anxiety and tickets.
- **No surprise invoices.** The first charge at the new price comes after the notice period and
  after the normal renewal reminder.
- **Never bury it** in a terms update; that damages trust more than the increase and is risky
  under consumer law.
- **Prepare support**: an internal FAQ, an exception policy (who may stay on the old price and for
  how long), and a log of replies.

## Reviewing pricing on a schedule

A light review quarterly from Launch; a deep review yearly, and whenever costs or the market move
(a model price change, a competitor repricing).

| Signal | Source | Likely meaning | Move |
|---|---|---|---|
| Price named in many lost deals | Win/loss notes, trial exit survey | Value not perceived, or wrong segment | Positioning first, then packaging, then price |
| Price rarely named, high close rate | Win/loss notes | Too cheap | Raise for new customers |
| Most customers on the cheapest plan | Plan mix | Weak fences, or too big a jump to the next plan | Move a fence or narrow the gap |
| Few customers near any limit | Usage against limits | Limits too generous; no upgrade trigger | Tighten for new customers |
| Many far above typical usage on a flat plan | Usage distribution | Heavy users underpriced | Usage tier or add-on |
| Discounts on most deals | Billing and deal records | List price is fiction | Lower list or enforce the policy |
| A plan below target gross margin | Cost per plan (`unit-economics.md`) | Cost to serve grew or was ignored | Cap, re-rate credits or reprice |

The output is one decision with its expected effect and a date to check it, or an explicit "no
change". Change one thing at a time so the effect can be attributed.

## Migrating legacy plans and retiring prices

Each old plan means entitlement branches, support confusion and prices nobody remembers selling.
Keep a versioned price book of every price ever sold, and aim for few live plan versions.

1. **Inventory** every price and plan version: active subscriptions on each, revenue, and the
   entitlements each grants.
2. **Map each legacy plan to a current plan** granting at least the same entitlements. Where
   nothing matches, carry the difference as a per-account override or add-on, not a new plan.
3. **Compute each customer's price change** and group: decrease or no change (migrate now and tell
   them), small increase (at renewal with notice), large increase (phase in over several
   renewals, or a set period at the old price).
4. **Stop selling the old price first**: archive it in the billing provider so no new subscription
   can use it; existing subscriptions keep billing until moved.
5. **Migrate each customer at their renewal**, announced like a price increase.
6. **Delete dead entitlement code** once no subscription references the old plan.

Traps: migrating mid-period creates prorations nobody understands; mapping by plan name instead
of by each account's actual entitlements breaks workflows; and customers on signed contracts or
lifetime deals cannot be moved without their agreement.

## Ask the user

- **What is the most you will discount, and for what?** Sets the policy table. Default: annual
  about 17 percent, nonprofit and education 25 percent, nothing else without a trade.
- **Will existing customers keep their price, and for how long?** Decides grandfathering. Default:
  time-limited; 6 months for monthly customers, next renewal after notice for annual.
- **How much churn would you accept from an increase?** Frames it against break-even churn.
  Default: proceed when expected loss is well under break-even.
- **Do you run promotions, and do existing customers get them?** Decides coupon rules. Default: one
  launch or yearly promotion, new customers and annual plans only.
- **Are any customers on contracts or lifetime deals that fix their price?** Limits what can be
  migrated. Default: assume any signed order form fixes the price until its term ends.
