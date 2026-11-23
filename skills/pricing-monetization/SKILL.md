---
name: pricing-monetization
description: "Decides how a product makes money: revenue model, value metric, trial or freemium, price points, plans and the pricing page, AI pricing against inference cost, discounts, price increases, legacy plans and unit economics. Use when asking what to charge, subscription vs usage vs per seat, designing tiers or a pricing page, pricing AI features, raising prices, a discount request, or CAC, LTV and payback."
---

# Pricing, packaging and unit economics

## Stance

Pricing is the highest-leverage decision a founder revisits least. Most small products are
underpriced, have too many plans, and charge per a unit chosen by accident. An experienced pricer
treats pricing as part of the product: set from the customer's value, packaged by segment, tested
with real payments, checked against margin per plan, and changed on a schedule with notice.

- **Value sets the price; cost sets the floor.** Cost-plus underprices software because a
  customer's marginal cost is tiny next to the value. Cost decides the minimum and the structure.
- **The value metric matters more than the number.** A wrong number is fixed in one review; a
  metric that does not grow with customer value caps revenue no matter the price.
- **Start higher than comfortable.** Lowering a price for new customers is free; raising it for
  existing ones costs notice, an email and some churn.
- **One plan per segment, each with a success-driven upgrade trigger.** Customers should move up
  because they grew, not because a core feature was withheld.
- **Price variable cost on its distribution, not its average.** Inference cost per account is
  skewed; plans are judged at p90 and p99, and nothing variable-cost is sold as unlimited
  without a fair-use limit enforced in code.
- **Every discount is a trade with an end date.** A discount for nothing becomes the price and
  the renewal baseline.
- **Price changes are announced, never discovered.** Notice, each customer's new number,
  time-limited grandfathering, and churn measured against the break-even churn of the increase.
- **Unit economics run on gross margin, per plan and per channel, from measured cost.** Averages
  hide losing plans; blended CAC hides losing channels.
- **Review on a schedule and change one thing at a time**, so each effect can be attributed.

Follow the project first: if prices, plans and a billing setup already exist, start from them and
from the data they produce. The defaults below are for new decisions.

## Route

| If the task is … | Read |
|---|---|
| "Subscription, usage, per seat or one-time?", choosing what the price is per, free trial vs freemium vs reverse trial vs paid only, whether sales calls are needed, how to charge for AI features without losing money on heavy users, lifetime deals | `references/revenue-model.md` |
| "How much should I charge?", is the price too low, competitor comparison, margin floor, willingness-to-pay interviews and surveys, testing a price, publishing enterprise prices or "contact us", regional pricing, currencies, purchasing-power discounts | `references/price-setting.md` |
| How many plans, what goes in each, where limits sit, free plan limits, seats and add-ons, usage tiers, an enterprise tier with SSO and SLA, designing or reviewing the pricing page | `references/packaging-tiers.md` |
| A customer wants a discount, annual plan incentive, coupons and promotions, raising prices, grandfathering, announcing a change, the periodic pricing review, moving customers off old plans | `references/discounts-price-changes.md` |
| "Do our unit economics work?", break-even customer count, CAC, LTV, payback, gross margin per plan including inference, whether a channel or segment pays off, customers or plans that lose money | `references/unit-economics.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Revenue model | Subscription with flat tiers | Cost per account varies by 10x or more → platform fee plus usage or credits; money flows through the product → transaction fee |
| Value metric | One metric; paid editors with free viewers for collaboration tools; a business action for API and AI products | No metric ranks customers like their value → split plans by segment |
| Entry | 14-day free trial, no card | Free users spread the product and cost almost nothing → freemium; inference-heavy → hard-capped trial or paid only |
| Sales motion | Self-serve, founder demos on request | Expected ACV above about $10k → sales-assisted |
| Plans | Up to three paid plans plus enterprise "contact us"; middle one recommended; 2 to 3 times apart | Prototype: one paid plan |
| AI features | Bundled with a published fair-use cap derived from the margin target | Several models or actions → credits; developer buyers → usage or bring your own key |
| Gross margin target | About 75 percent; about 60 percent for inference-heavy products | |
| Annual plan | Offered from Launch at about two months free | |
| Discounts | Only for a trade, capped, with an end date | |
| Price increase | New customers first; existing customers time-limited grandfathering, at least 30 days notice | Contract or lifetime terms fix the price |
| Regional pricing | None for B2B; a few bands bound to card country for consumer and developer products | |
| Enterprise price | "Contact us" with a starting figure or minimum annual commitment | Stable package → publish it |
| Lifetime deal | No | Cash is urgent, marginal cost near zero, quantity capped |

By stage:

- **Prototype**: one paid plan priced from value, pre-sales or deposits from design partners,
  cost logged per account from the first request. Skip surveys, regional pricing and tiers.
- **Launch**: two or three plans, annual option, written discount policy, break-even count and the
  one-sheet model, quarterly pricing review, first price increase for new customers when the
  signals say so.
- **Scale**: per-channel and per-segment economics, enterprise tier, structured price tests,
  regional pricing where individuals pay, legacy plan migration.

## Before you call it done

1. The value metric passes the five tests and ranks real customers the way their value does.
2. The price is derived from the next best alternative and quantified customer value, with the
   reasoning written down, and sits above the floor at p90 cost to serve.
3. Gross margin is computed per plan with inference, support and payment fees included, and a
   customer at each plan's limits still meets the target margin.
4. Every variable-cost feature has a published limit enforced in code; nothing variable-cost is
   unlimited.
5. Each plan names its segment, adjacent plans have a success-driven upgrade trigger, and one plan
   is marked recommended.
6. The free plan or trial reaches activation and ends below a typical paying customer's usage.
7. Prices, currency, billing period, tax treatment and trial terms on the pricing page match
   checkout exactly; annual prices show the amount billed.
8. The discount policy states the trade, the maximum and the end date; list price and discount
   are recorded separately.
9. Every price change has each customer's new price, a notice period checked against the rules
   that apply, a grandfathering policy, and a measurement plan against break-even churn.
10. CAC is fully loaded including the founder's selling time, payback uses contribution not
    revenue, LTV is capped, and small samples are shown as ranges.
11. The break-even account count and the new accounts needed per month are known.
12. Accounts and plans with negative or below-target contribution are listed with a cause and a fix.
13. A price book lists every live and legacy price with its customers; retired prices are archived
    so no new sale can use them.
14. The next pricing review has a date, and its output will be a decision or an explicit "no change".

## Not this skill

- Implementing checkout, subscriptions, metering and invoices → `0x:payments-billing`
- Cash-flow forecasts, runway, bookkeeping and fundraising → `0x:startup-finance`
- A/B test design and statistics for a pricing experiment → `0x:product-analytics`
- Negotiating a specific enterprise deal → `0x:sales-support`
- Legal rules on price display, auto-renewal and cancellation → `0x:privacy-compliance`
- Reducing the cloud bill itself → `0x:cloud-infrastructure`
