# Revenue model and value metric

Read this when: deciding how the product charges at all (subscription, usage, transaction fee or
take rate), what unit the price scales with, how a stranger gets in (trial, freemium, reverse
trial, paid only), whether a human sells it, how to charge for AI features, or whether to sell a
one-time or lifetime deal.

## Decide in this order

Each choice constrains the next. Founders usually start at the end (a number) with none of the
first four settled, then cannot explain why the number is what it is.

1. **Where value accrues**: continuously (a tool used every week), per event (a document
   processed, a payment taken), or once (a template, a report). This picks the model.
2. **The value metric**: the unit the bill grows with. This decides whether revenue grows when
   the customer succeeds.
3. **The entry point**: how a stranger becomes a paying customer.
4. **The sales motion**: whether a human is involved, decided by expected annual contract value.
5. Only then the price points (`price-setting.md`) and the plans (`packaging-tiers.md`).

## Choosing the revenue model

| Model | Fits when | Breaks when | Default for |
|---|---|---|---|
| Subscription, flat per tier | Value is continuous and similar within a segment; cost to serve is low and flat | Heavy users cost ten times the median or more (AI, video, compute); flat plans then subsidize them | Most B2B and prosumer SaaS |
| Subscription per seat | Each named user gets value individually and value grows with team size | The product automates work so customers need fewer people; logins get shared; collaboration needs people who will not pay | Collaboration tools with distinct creators |
| Usage (pay as you go) | Value and cost both scale with one measurable unit; buyers are developers | Buyers need a fixed budget; usage is spiky; you need forecastable revenue | APIs, infrastructure, inference |
| Hybrid: platform fee plus usage | Most products with real variable cost | Rarely; it is the usual end state | AI and API products past Launch |
| Transaction fee (% of money moved) | The product sits in the flow of the customer's revenue: payments, bookings, invoicing | Large customers see the percentage as a tax and negotiate or leave; the processor's fee sits inside yours | Payment-adjacent and booking products |
| Marketplace take rate | The platform keeps adding value after the match: payment, escrow, trust, scheduling, insurance | Value is only the introduction; repeat business moves off-platform | Two-sided marketplaces |
| One-time purchase | A delivered artifact with low ongoing cost: desktop app, plugin, template, course | Ongoing hosting, inference or support cost per buyer | Downloads and digital goods |

Rules that settle most cases:

- **Revenue must follow cost when cost per customer varies by an order of magnitude.** Otherwise
  the most active customers are the least profitable. Measure the cost distribution per account
  before committing to flat pricing (`unit-economics.md`).
- **Predictability is part of what is sold.** Business buyers approve a known budget faster than
  an open meter. Usage pricing for them needs a committed minimum, a prepaid balance or a spend
  cap they control.
- **A take rate is bounded by leakage, not by what the market will bear.** The higher the share,
  the more pairs that met once transact off-platform afterwards. Hold it where the ongoing
  services (payment protection, dispute handling, records, rebooking) are worth more to both
  sides than the fee, and add those services before raising it.
- **A percentage fee must clear the processor's cost on small transactions.** Processors charge a
  percentage plus a fixed amount per charge, so a pure percentage loses money below some ticket
  size. Add a fixed component or a minimum fee.

## Picking the value metric

The value metric is what the price is "per". A wrong metric cannot be fixed by any price point;
a wrong price point is fixed in one review. A good metric passes five tests:

| Test | Question | Failure looks like |
|---|---|---|
| Value-aligned | Do customers who get more value consume more of it? | A customer who doubled their revenue through the product pays the same |
| Predictable | Can a buyer estimate next month's bill in one sentence? | "Compute units" nobody can estimate before using them |
| Cost-correlated | Does cost to serve grow with it? | A flat per-seat price on a product whose cost is tokens |
| Measurable | Can it be counted reliably and shown to the customer? | Disputed counts, gaming, outcomes nobody can attribute |
| Not punishing | Does charging for it leave the sticky behavior unpenalized? | Charging per collaborator in a product whose retention comes from sharing |

Procedure: list 10 to 20 real or likely customers and rank them by value received. Rank them
again by each candidate metric. The metric whose ranking matches the value ranking wins. If no
metric matches, the customers are several segments, and plans must split by segment
(`packaging-tiers.md`) rather than by a cleverer metric.

| Metric | Trap |
|---|---|
| Seats | Seat compression when AI reduces headcount; shared logins. Charge for creators or editors, make viewers free |
| Active users | The bill moves every month; define "active" precisely and show the count in the product |
| Contacts, records, items stored | Customers delete data to stay under a threshold; leave headroom above each tier |
| API calls, requests | Penalizes chatty integrations the product itself caused; price the business action, not raw requests |
| Volume processed (revenue, documents, GMV) | Strong alignment; large customers negotiate the rate down; measurement must be trusted by both sides |
| Outcomes (resolved tickets, booked meetings) | Best alignment, worst measurability; attribution disputes. Only when the product itself records an unambiguous outcome |

Start with **one** metered dimension. Each extra dimension doubles the explanation on the pricing
page and the cases in billing code. Serve secondary needs with tier fences and add-ons.

## Entry point: trial, freemium, reverse trial or paid only

| Entry | Use when | Main risk |
|---|---|---|
| Free trial, no card | Value shows within days; product is self-explanatory; sign-ups are the bottleneck | Many unqualified trials, low trial-to-paid rate |
| Free trial, card required | Traffic is high-intent or sales-assisted; payment conversion matters more than sign-up volume | Fewer trials; needs a pre-charge reminder and easy cancel, or disputes and legal exposure follow |
| Freemium | A free user costs almost nothing; large market; free users spread the product (sharing, invites, public pages, badges); a limit that succeeding users reach naturally | Most free users never pay; the free plan becomes the product; cost and support grow with no revenue |
| Reverse trial | Premium features are what make users stick, and a free floor is wanted for retention | Users who lose features at trial end feel downgraded; say upfront what happens |
| Paid only, with a refund guarantee | High-intent B2B, high per-user cost (inference, human service), small market | Fewer sign-ups; needs strong proof on the landing page and a demo path |

Decision rules:

- **Trial length is time to first real value plus one usage cycle.** Rule of thumb: 14 days for
  most self-serve tools, 7 when value shows in one session, 30 when setup, data import or team
  rollout is needed. A longer trial mostly delays the decision; extend individual trials on
  request instead.
- **Freemium is a distribution strategy, not a pricing tier.** Choose it only if free users bring
  in other users or content. Otherwise a trial costs less and converts better.
- **Freemium conversion is small**: low single-digit percentages of free accounts paying is a
  common rule of thumb. Budget the free plan's cost against that rate; free-user cost is
  acquisition spend (`unit-economics.md`).
- **Compare entry options on paying customers per 100 visitors**, not on trial-to-paid rate.
  Card-required trials always win on conversion rate and often lose on paying customers.
- **AI products: every free user costs real money.** Cap free usage hard, require verified
  sign-in, and expect multiple accounts per person.

Trial and card mechanics → `0x:payments-billing`; reminder and cancellation duties →
`0x:privacy-compliance`.

## Sales motion from the price point

Who sells is decided by what a deal is worth, because selling cost must be recovered from it.
Bands of annual contract value (ACV), as a rule of thumb:

| ACV | Motion | What the product must have |
|---|---|---|
| Under about $1k | Pure self-serve; no human time per deal | Sign-up, trial, card checkout, docs, in-app onboarding |
| About $1k to $10k | Self-serve with assist: demo on request, chat, founder answers questions | Above, plus a "talk to us" path, invoices, annual plans |
| About $10k to $50k | Inside sales: discovery call, demo, guided trial, order form | Quotes, contracts, security questionnaire answers, admin features |
| Above about $50k | Enterprise: several stakeholders, procurement, legal review, a cycle of months | SSO, audit logs, SLA, DPA, custom terms, and someone whose job is selling |

- **The trap is the middle**: a product that needs a call to adopt (complex setup, several
  stakeholders, data migration) priced like self-serve. Either remove the reasons for the call
  or raise the price to pay for it.
- **Founder-led sales comes first whatever the target motion.** Selling the first 10 to 20
  customers personally reveals objections, the buyer, and the real value metric. Do not hire
  sales before the founder closes repeatably.
- **Moving upmarket is a product change**: enterprise buyers need features and process that
  self-serve buyers never ask for (`packaging-tiers.md`, and `0x:sales-support` for deals).

## Pricing AI features against inference cost

Inference makes cost per customer variable and skewed: the heaviest accounts often cost many times
the median. Price on the measured distribution, never on the average.

1. **Measure first.** Log tokens or compute per account per action from day one. Compute cost per
   active account per month at p50, p90 and p99. Every option below is a guess without this.
2. **Choose the structure:**

| Structure | Fits when | Watch |
|---|---|---|
| Bundled in the plan with a fair-use cap | AI is one feature of a broader product; most users are light | The cap must keep a capped user profitable; publish the cap |
| Allowance plus overage or top-up | Usage varies widely and buyers accept metering | Spend alerts and caps, or surprise bills cause churn and disputes |
| Credits (prepaid units) | Several actions or models with different costs; re-rating later must be possible | Map credits to actions users understand; expiry and refund rules |
| Model tiering | Cheaper model on lower plans, strongest model on higher plans | The lower tier must still do the job, or it is a crippled trial |
| Bring your own key | Developer tools, power users, open-source products | No inference margin; support for key and quota errors |
| Usage pass-through with markup | API products sold to developers | Price competition against the model provider itself |

3. **Derive the allowance from the margin target:**

```text
allowance per period = plan price × (1 − target gross margin − other cost share) ÷ cost per unit
```

   Example: a $20 plan, 70 percent target gross margin, other cost of revenue 10 percent of price
   leaves $4 for inference; at $0.02 per action that is 200 actions a month. Recompute whenever
   model prices, the model choice or prompt size change.
4. **Never sell "unlimited" AI without a fair-use limit enforced in code.** Unlimited attracts the
   heaviest users and scripted abuse (adverse selection). Past the fair-use level, slow down or
   switch to a cheaper model rather than cutting the user off.
5. **Credits decouple price from model cost.** When a cheaper model arrives, keep the credit price
   and either lower credits per action or keep the margin; when a costlier model is better,
   charge more credits for it. Do not expose raw tokens to non-developer buyers.
6. **Prepaid balances carry legal and accounting consequences** (expiry, refund of unused value,
   revenue recognition) that differ by jurisdiction; check `0x:privacy-compliance` and
   `0x:startup-finance` before setting expiry rules.

Lowering the cost per call → `0x:ai-features`; metering and credit ledgers → `0x:payments-billing`.

## One-time and lifetime deals

| Offer | Use when | Avoid when |
|---|---|---|
| One-time purchase with a period of updates ("perpetual license, one year of updates") | Desktop or self-hosted software, plugins, templates, courses | The product is hosted and costs money per buyer every month |
| Lifetime deal (pay once, use the hosted product indefinitely) | Early cash and feedback matter more than recurring revenue, marginal cost is near zero, quantity is capped | Any per-use variable cost (AI, storage growth, SMS), or a product still changing shape |

If a lifetime deal is sold anyway:

- Cap the number sold and the plan's limits (seats, projects, usage). Exclude variable-cost
  features, or give them a monthly allowance with paid top-ups.
- Sell a named plan with a defined feature set, not "all future features", and define "lifetime"
  as the life of the product in the terms.
- Expect a heavier support load per buyer than subscribers, and deal-seeking buyers who rarely
  move to recurring plans. Deal marketplaces keep a large share of the price; compare net cash
  per buyer against several years of their cost to serve before agreeing.
- Lifetime buyers keep their terms forever. They constrain every later pricing change and are
  the loudest voices when one happens.

## Ask the user

- **Who pays, and from which budget?** An individual's card, a team lead's tool budget, or
  procurement: this decides model, metric and motion. Default: a team lead paying by card,
  self-serve B2B.
- **What do the heaviest customers cost compared with a typical one?** Decides flat versus usage.
  Default if unknown: flat tiers with a published fair-use cap, and log cost per account now.
- **Is growth limited by sign-ups or by conversion?** Decides freemium versus trial. Default:
  14-day free trial without a card.
- **Will you sell by talking to people?** Decides whether an ACV above about $10k is realistic.
  Default: self-serve, with founder-run demos on request.
- **Is cash now worth more than recurring revenue later?** The only good reason for a lifetime
  deal. Default: no lifetime deal.
