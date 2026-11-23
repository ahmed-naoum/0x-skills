# Setting the price

Read this when: choosing the actual numbers: a first price, whether the current price is too low,
competitor and status-quo anchors, the margin floor, willingness-to-pay research, testing a price,
publishing or hiding enterprise prices, or prices by region and currency.

## The three numbers that bound a price

| Bound | What it is | Role |
|---|---|---|
| Floor | Cost to serve a heavy (p90) customer ÷ (1 − target gross margin), with enough contribution left to recover acquisition cost within the payback target | Below it, growth loses money. Never the price itself |
| Reference | What the customer pays today for the next best alternative: a competitor, a contractor, an employee's hours, a spreadsheet plus the errors it causes | Where the buyer's mind starts |
| Ceiling | The economic value the product creates for the customer per period | Never reachable; the customer must keep most of the value |

Price between reference and ceiling. A common heuristic is to capture roughly 10 to 20 percent of
the value created; treat it as a starting point to test, not a rule.

Cost-plus pricing underprices software because the marginal cost of a customer is small compared
with the value delivered. Cost sets the floor and shapes the structure (`revenue-model.md`); it
does not set the number.

## Setting the first price from value

1. **Name the segment.** One price logic per segment; a freelancer and a 50-person agency are
   different markets for the same feature set.
2. **Quantify value for a typical customer of that segment**, in money per month:
   - Time saved: hours per month × loaded hourly cost of the person whose hours they are.
   - Revenue gained: extra conversions, faster collection, fewer lost deals, with a conservative
     share attributed to the product.
   - Cost avoided: tools replaced, contractor or hire not needed, errors and penalties avoided.
   - Risk reduced: count it only when the customer already budgets for it (compliance, security).
3. **Find the next best alternative and its full cost**, including the cost of switching to the
   product: migration, retraining, lost history.
4. **Set the price** at the reference, plus the value of the differentiation, minus switching
   cost. Check it sits well under the quantified value (about a fifth or less).
5. **Round to a price point the market expects**: charm endings ($29, $49) for consumer and
   prosumer; round numbers ($50, $500 a month, $12,000 a year) for business buyers.
6. **Check against the floor.** If the price is below it, change the segment, the value metric or
   the cost to serve. Shipping below the floor in the hope of scale does not fix it.

Start higher than feels comfortable. Lowering a price for new customers is easy and welcomed;
raising it for existing ones costs a notice period, an email and some churn.

Signs the price is too low (heuristics, not laws):

- Almost nobody pushes back on price on calls or in trial exit surveys.
- Close rate on qualified prospects is very high and sales cycles are short.
- Buyers take the top plan without questions, or say it seems cheap for what it does.
- Usage is heavy, yet the cheapest plan carries most of the revenue.

Signs it is too high or packaged wrong: prospects agree on value but stall at the number; most
deals need a discount; trials activate but do not convert; early churn reasons name price. First
separate a price problem from a value-communication problem: if prospects cannot say what the
product does for them, the fix is positioning (`0x:growth-marketing`), not price.

## Anchoring against competitors and the status quo

- **Normalize competitor prices to the customer's real size.** Compute what each competitor
  charges a typical customer (for example 8 editors and 20,000 contacts), not the entry price on
  their page. Entry prices hide limits, add-ons and required tiers.
- **Choose a position explicitly**: premium (above, justified by a differentiator the buyer can
  see), parity (match, win on fit or service), or discount (below, only with a structural cost
  advantage or a deliberately narrower product). A discount position without a cost advantage is
  a margin race that the larger company wins.
- **Anchor on the status quo when competitors are not the real alternative.** If the customer
  currently uses a spreadsheet plus two hours a week of someone's time, the anchor is the cost of
  those hours. Say it on the pricing page or in the deck ("less than one hour of a contractor a
  month").
- **Anchor within the page**: a visible higher plan or enterprise tier makes the recommended plan
  look reasonable (`packaging-tiers.md`).
- **Do not copy a competitor's price without their cost structure and segment.** A funded
  competitor may price for growth at a loss; a larger one may have costs you cannot match.

## The margin floor

Gross margin = (revenue − cost of revenue) ÷ revenue. Cost of revenue is everything that grows with
customers:

| In cost of revenue | Out of it (operating expense) |
|---|---|
| Production hosting, databases, CDN | Engineering on new features |
| Per-customer services: email, SMS, maps, search, AI inference | Marketing, ads, sales pay (these are CAC) |
| Payment processing fees | Admin, legal, accounting |
| Support and onboarding time | Office and general tools |
| Licences paid per customer or per seat | |

- **Set a target gross margin explicitly.** Software businesses commonly aim for roughly 70 to 80
  percent or more; products heavy in inference or human service run lower and must price for it.
  Buyers of a company value revenue partly by its gross margin, so a low-margin product needs a
  higher price or a different structure, not just more customers.
- **The price must also recover acquisition.** Monthly contribution (price × gross margin) times
  the payback target in months must exceed CAC (`unit-economics.md`).
- **Check margin at the plan's limits, not on average.** A plan whose average user is profitable
  but whose capped user is not drifts unprofitable as power users choose it.
- **Low prices break on fixed fees.** A processor's fixed fee per charge is a large share of a $5
  monthly payment. Rule of thumb: below roughly $10 a month, push annual billing or raise the price.

## Researching willingness to pay

"What would you pay?" produces low, unreliable answers. In order of cost:

**Interviews (from Prototype).** Ask about behavior, not hypotheticals:

- What do you use today, and what does it cost in money and time?
- Who approved the last tool like this, how, and what did it cost?
- What happens if this problem is not solved this quarter?
- At the end, state the planned price and watch: an instant "fine" means it is low.

Interview method → `0x:product-discovery`.

**Van Westendorp price sensitivity (Launch; dozens of responses from one segment).** After a
concrete description of the product, ask:

1. At what price would it be so expensive you would not consider it?
2. At what price would it start to seem expensive, though you would still consider it?
3. At what price would it be a bargain?
4. At what price would it be so cheap you would doubt its quality?

Plot cumulative curves; the crossings give an acceptable range, not a point. Use it to rule prices
out, not to pick one. Mixing segments in one survey produces a meaningless range.

**Gabor-Granger (Launch).** Ask whether the respondent would buy at a price, then step up or down.
It gives a rough demand curve. Stated intent overstates purchases, so compare relative revenue
across price points rather than trusting the absolute rates.

**Conjoint analysis**: skip until Scale; it needs large samples and specialist tooling.

## Testing with real offers

Stated willingness to pay is a hypothesis; a payment is the test.

| Method | Stage | How |
|---|---|---|
| Pre-sale or deposit | Prototype | Ask design partners to pay, or put down a deposit, at the intended price before launch |
| Sequential quotes | Launch, sales-led | Quote a higher price to the next N qualified prospects; compare close rate and deal size with the previous N |
| Time-based change | Launch, self-serve | Change the public price for new customers for a fixed period; compare revenue per visitor with the period before, by traffic source; avoid launch weeks, holidays and seasonal peaks, which swamp the effect |
| New-segment launch | Launch or Scale | Open a new region, segment or plan at a higher price |
| Concurrent A/B on the public price | Scale only, with care | Different visitors see different prices; risks screenshots and fairness complaints. Prices personalized from personal data or profiling carry disclosure duties in the EU (Consumer Rights Directive) and New York, with more rules pending; check `0x:privacy-compliance` first |

- **Judge by revenue per visitor or per qualified lead**, not conversion rate. A 30 percent higher
  price with 15 percent lower conversion is a win.
- **Test big steps.** At small volume a 5 percent change is undetectable; test 25 to 50 percent
  steps, then refine.
- **Honor what was shown.** Whoever paid a test price keeps it; whoever saw a lower price and paid
  more gets the difference as credit if they ask.
- Experiment design and statistics → `0x:product-analytics`.

## Publish enterprise prices or sell by quote

| Situation | Do |
|---|---|
| Self-serve tiers | Always publish; hidden self-serve prices lose every buyer who will not book a call |
| Enterprise price varies with scope (seats, compliance, support, deployment) | "Contact us" plus a "starting at" figure or minimum annual commitment, to filter out small budgets |
| Enterprise package is stable | Publish it; procurement can budget without a call and cycles shorten |
| Competitors would use the number to undercut deals | Quote, with an internal price book so quotes stay consistent |

As soon as anything is quoted, keep a written price book: list prices, discount limits, who
approves what. Otherwise every customer has a different price and each renewal reopens the
negotiation (`discounts-price-changes.md`).

## Regional prices, currencies and purchasing-power discounts

- **Decide by who pays.** Individuals and very small businesses paying personally are sensitive to
  local income; companies, especially buying from abroad, usually pay list price in USD or EUR.
  Purchasing-power discounts fit consumer, prosumer, developer and education products, rarely B2B.
- **Use a few bands, not per-country prices**: full price, a moderate discount band, a deeper
  discount band. Fewer bands mean fewer prices to maintain and less arbitrage.
- **Bind the regional price to the payment method's country** (card issuing country or billing
  address), not the visitor's IP; a VPN defeats IP-based pricing in a minute. Showing the band by
  IP on the pricing page is fine if checkout re-checks it against the card.
- **The EU is one band.** For electronically supplied services such as SaaS (services whose main
  feature is copyrighted content, such as e-books, music or games, are carved out), the EU
  Geo-blocking Regulation bars treating customers (consumers, and businesses buying for their own
  use) differently by residence or by where in the EU their card was issued. Different prices per
  country storefront are allowed only if anyone in the EU may buy at them, which defeats
  purchasing-power bands inside the EU. Keep one EU price and apply bands to countries outside it,
  or get legal advice first. The UK is not covered by this regulation.
- **Charge in local currency in the large markets** (commonly USD, EUR, GBP, plus any market that
  is a large share of revenue) at **rounded local price points** (€49, £45), not converted
  amounts like €45.37. Revisit when exchange rates drift a lot, not on every move.
- **Show tax as the market expects.** Prices shown to consumers in the EU, the UK and several
  other markets (Australia, for example) must include VAT or GST; US prices and prices for business
  buyers are usually shown before tax. One tax-inclusive price across the EU means net revenue
  varies with each country's VAT rate (standard rates differ by about ten points); either absorb
  that, or fix the net price and let the inclusive price vary by country. Display rules →
  `0x:privacy-compliance`; tax collection and registration → `0x:payments-billing`.
- **A merchant of record or the provider's localized-pricing feature** can handle currency
  presentation and conversion; check current features and fees before building it.
- **Stop B2B arbitrage**: limit regional discounts to individual plans, or require the billing
  entity's address in the region.

## Ask the user

- **What does the customer use today, and what does it cost them?** The anchor for everything.
  Default if unknown: five interviews before fixing a price; meanwhile parity with the closest
  competitor, normalized to a typical customer.
- **What gross margin are you aiming for?** Sets the floor and AI allowances. Default: 75 percent
  for software, 60 percent for inference-heavy products.
- **Premium, parity or cheaper?** Decides anchoring and page messaging. Default: parity with a
  visible differentiator; never cheaper without a cost advantage.
- **Will you show different prices to different visitors?** Decides the test method. Default: no;
  sequential tests on new customers only.
- **Do buyers pay personally or through a company?** Decides regional pricing. Default: no regional
  discounts for B2B; three bands for consumer and developer products.
