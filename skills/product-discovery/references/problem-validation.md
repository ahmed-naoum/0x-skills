# Problem and demand validation

Read this when: deciding whether an idea or a large feature is worth building, choosing between
ideas, defining who the customer is, or designing a test of whether people want it and will pay.

## The sequence

Validate in this order and stop at the first step that fails:

1. Problem statement: one sentence, specific enough to be wrong.
2. Ideal customer profile (ICP): narrow enough to list 100 named prospects.
3. Existing alternatives: what they do today, including nothing.
4. Interviews: evidence the problem is frequent or costly (`customer-interviews.md`).
5. Score the idea against at least two others.
6. Demand test with a threshold written in advance.
7. Commitment: pre-orders, letters of intent, design partners.

Jumping to step 6 with a polished landing page is the common mistake: without steps 1–3 the page
targets nobody in particular and its result cannot be interpreted.

## Write the problem statement

```text
<Specific who> who <situation or trigger> struggle to <job> because <obstacle>.
It costs them <time, money or risk> <how often>. Today they <current workaround>.
```

| Weak | Why it fails | Stronger (illustrative) |
|---|---|---|
| "Small businesses struggle with marketing" | No findable who, no frequency, no cost | "Owners of single-location dental practices lose hours every week chasing unconfirmed appointments by phone; the front desk works from a printed schedule" |
| "Developers need better observability" | A category, not a problem | "Solo SaaS founders learn about failed background jobs from customers days later, because nothing alerts on job failures" |
| "People want an AI assistant for X" | A solution, not a problem | Describe the job and the obstacle; AI is one possible answer |

Check that the who can be searched for, the cost and frequency carry units, and the workaround
is named. Daily-and-annoying and rare-and-expensive problems both sell; rare-and-mild does not,
however many people have it.

## Define an ICP narrow enough to name 100 prospects

| Attribute | Example (illustrative) |
|---|---|
| Organization | Independent accounting firms, 5–30 staff, one country |
| User | Senior bookkeeper doing month-end close |
| Buyer | Managing partner (user and buyer differ) |
| Trigger | Taking on more clients than the team can close on time |
| Current tools | Spreadsheets plus a general ledger product |
| Findable signal | Listed in a professional directory; hiring bookkeepers |
| Excluded | Firms over 100 staff (procurement cycles), sole practitioners (no budget) |

The 100-names test: in one or two days of desk research, list 100 named organizations or people
who fit, each with a contact route. If that is impossible, the ICP is too vague (no searchable
attribute) or unreachable (no channel exists); either is fatal for a solo founder without a sales
team. If the whole profile holds only a few hundred organizations, run the revenue math below
before going further.

Narrow is the starting point, not the ceiling: choose the first segment where pain is highest and
reach is cheapest, and expand only after it works there.

## Map the existing alternatives

Every real problem already has a solution, usually a bad one. List all of them:

| Type | Examples | Record |
|---|---|---|
| Direct competitors | Products built for this job | Price, segment, what reviews praise and hate |
| Adjacent tools | A product that does this as a side feature | Whether it is good enough for the ICP |
| General-purpose tools | Spreadsheets, docs, email, a no-code database | How elaborate the setup is |
| People | An assistant, agency, contractor or internal team | Cost per month |
| Doing nothing | Living with the problem | What that costs, and why it has been acceptable |

- Doing nothing is the most common winner. If the pain does not beat the effort of switching,
  nothing sells, however good the product.
- An elaborate spreadsheet is the best evidence there is: it proves the job, the frequency and the
  willingness to invest effort, and it hands over the data model. Ask to see it.
- Paying people to do the job proves budget exists and sets a price anchor.
- "No competitors" usually means no demand, or a search in the founder's words instead of the
  customer's. Search again with the phrases heard in interviews.
- Record switching cost for each alternative (data migration, retraining, contracts,
  integrations); it sets how much better the new product has to be.

## Score ideas before choosing one

Score each candidate 1–5 on four criteria, with the evidence written next to each score.

| Criterion | 1 | 5 | Evidence that counts |
|---|---|---|---|
| Pain | Mentioned only when asked | Frequent or costly; paying for a workaround | Interview cards at the higher pain rungs |
| Payer clarity | Unclear who pays; user has no budget | A named role with budget for this today | Current spend on alternatives |
| Reachability | No list, no channel | 100 names in a day; a channel that reaches many | The prospect list exists |
| Founder advantage | None | Domain insider, existing audience, rare skill or access | What a funded competitor could not copy quickly |

- Any 1 disqualifies; averages hide fatal flaws. A product nobody can reach dies with perfect pain
  scores.
- Compare at least three ideas side by side. One idea scored alone always looks fine.
- An unknown scores 2 until evidence arrives, which makes the next step obvious: gather it.
- Two more gates once the four pass: the revenue math below works for the founder's goal, and an
  MVP that tests the riskiest assumption fits in weeks (`mvp-scoping.md`).

## Test demand: landing page, fake door, concierge

Commitment ladder, weakest to strongest: page visit → email signup → answered a qualifying
question → booked a call → signed letter of intent → paid deposit or pre-order → paid and uses it.
Design each test to reach as high a rung as possible; an email costs the visitor nothing and
predicts little.

| Test | Use when | Setup | Read |
|---|---|---|---|
| Landing page (smoke test) | No product yet; testing a promise to a segment | One segment, one problem, one promise, one call to action; targeted traffic | Share of targeted visitors reaching the highest rung offered |
| Fake door | Existing product with users; testing a new feature | A button or menu entry leading to "not built yet; want early access?" | Click rate among exposed users, then signups |
| Concierge | Testing whether the outcome is valuable and what the workflow really is | Deliver the result by hand to a few named customers who know a person does it | Do they use it, come back, and pay |
| Pre-sale | Testing willingness to pay | Payment link or deposit with clear refund terms | Paid count against the threshold |

Landing page rules:

- Traffic must come from the ICP: targeted ads, community posts, direct outreach. Friends and
  general launch sites measure the curiosity of the wrong people.
- Wait for a few hundred targeted visitors before reading a rate. At 100 visitors, 5 signups is
  consistent with anything from about 2% to 11% at 95% confidence.
- Ask one qualifying question after signup (role, team size, current tool) and offer a call to
  the qualified; it separates the ICP from the curious.
- Vary one thing at a time (segment, problem framing, or price). Copy and conversion mechanics
  belong to `0x:growth-marketing`.

Fake door rules: tell the truth on the next screen, never take money for it, limit exposure to a
slice of users behind a flag (`0x:ci-cd-release`), and remove it when the window closes.
Measuring it properly is `0x:product-analytics`.

Prefer concierge over Wizard of Oz (customers believe it is automated while a person does it).
Wizard of Oz teaches less about the workflow, and it creates a disclosure problem when people the
customer does not know about handle their data, or when automation or AI is claimed that does
not exist.

## Set a falsifiable threshold, then decide

Write the threshold, the time box and the decision for each result before the test starts.
Otherwise every result reads as encouraging.

```text
Hypothesis: Agencies with 10-50 staff will pre-pay for automated month-end reconciliation.
Test:       Outreach to 100 named ICP prospects, calls with responders, pre-sale at the planned price.
Time box:   4 weeks, ending 2026-12-21.
Persevere:  >= 5 paid pre-orders AND >= 8 calls where the prospect pays for a workaround today.
Kill:       <= 1 pre-order AND fewer than 4 calls show current spend.
Otherwise:  change one variable (segment, problem framing or price) and rerun once.
```

| Result | Decision |
|---|---|
| Threshold met | Persevere: build the MVP for exactly this segment and promise |
| Strong signal in an adjacent segment or problem | Pivot one element (segment, problem, solution, channel, revenue model) and rerun |
| No signal after two or three honest iterations | Kill; record what was learned and which assumption failed |
| Ambiguous | The threshold or sample was wrong; fix the test, do not round up |

- Change one variable per iteration, or the next result cannot be attributed to anything.
- Kill early; time and money already spent do not count toward the next decision.
- Derive thresholds from the founder's economics: customers needed (sizing below) and the share
  of reachable prospects a channel can plausibly convert.

## Collect pre-orders or letters of intent

Money is the only proof of willingness to pay. Ask for it before building.

Pre-orders (self-serve or small B2B):

- Use the payment provider's hosted payment link (`0x:payments-billing`); write no billing code.
- State the delivery date, what is included, and "full refund on request until delivery". Rules on
  pre-orders and delayed delivery vary by jurisdiction (`0x:privacy-compliance`), and processors
  restrict long gaps between charge and delivery; check both before charging.
- A founding-customer price with a stated end date is fine. Free is not a pre-order.
- Deliver on the date or refund proactively. A missed date without contact turns supporters into
  chargebacks.

Letters of intent (B2B):

- Non-binding, one page: buyer organization, the problem in their words, intended scope, price or
  budget range, intended start date, conditions to purchase, and the signature of someone who
  controls budget.
- An LOI from a user without budget authority is a compliment on letterhead. Ask who signs
  purchase orders and get that person.
- A paid pilot beats an LOI, and an LOI beats verbal enthusiasm. Pilot and contract terms belong
  to `0x:sales-support`; the price to `0x:pricing-monetization`.

## Sign design partners

Three to five ICP organizations that commit time and access before launch, in exchange for
influence and a discount.

| They commit | They get |
|---|---|
| A named champion and a 30-minute session every one or two weeks | Direct influence on what gets built |
| Real data and workflow access, under a confidentiality agreement | Early access and a direct line to the founder |
| Feedback within a few days of each release | A founding price, fixed for a stated period |
| To pay at launch at a pre-agreed price, or a reduced fee now | Optional credit as a launch reference |

- Put it in a one-page agreement: duration (often about three months), cadence, data handling and
  conversion terms. Without written conversion terms, partners become free users who never pay.
- Build what at least two partners need or what clearly fits the ICP. One partner steering the
  roadmap turns the product into their custom software.
- A partner who misses two sessions in a row is telling the truth about their pain; replace them.
- Choose partners who resemble the ICP over the biggest names available. An enterprise logo
  brings enterprise requirements that drag the product upmarket before it works anywhere.

## Size the market bottom-up

Count customers; never take a percentage of a published market figure.

```text
Reachable ICP organizations (counted from registers, directories, marketplaces)   N
x realistic annual price per customer                                           P
= revenue if every one bought                                                   N x P
Customers needed for the founder's goal = goal ARR / P
Required share of the ICP               = customers needed / N
```

Example: $1M ARR at $100 per month needs about 834 customers. If the counted ICP is 5,000
organizations, that is about 17% of the segment, a lot for one channel; at 50,000 it is under 2%,
which is plausible.

- Use what the ICP pays for alternatives today as the realistic price, not the hoped-for one.
- Cross-check the count from two independent sources.
- The goal sets the bar: a business supporting one founder needs far fewer customers than one
  meant to justify venture funding (`0x:startup-finance`).
- A small count is not fatal by itself; a small, reachable, high-pain segment is a good beachhead
  when an adjacent segment exists to expand into.

## Tear down competitors

Spend a day on the top two or three alternatives, using them as a normal customer would.

| Look at | Record |
|---|---|
| Sign-up and onboarding | Steps and time to first value, data required up front, where the card is asked for, emails over the first two weeks |
| Pricing page | Value metric, tiers, what is gated where, annual discount, "contact sales" threshold |
| Reviews (marketplaces, app stores, forums) | Sort to 1–3 stars; tally recurring complaints and "I wish it…" lines; note each reviewer's segment |
| Docs and changelog | Complexity hidden behind the marketing; release cadence |
| Job postings | Where they are investing next |
| Status page history | Reliability as a possible wedge |

Turn it into a gap table: complaint, how often it recurs, which segment raises it, whether the ICP
cares, and whether the new product can credibly do better. Attack where complaints come from the
ICP and the incumbent cannot follow for structural reasons (its pricing model, its move upmarket,
its architecture), not where it is merely behind on a feature it will ship next quarter.

Use public information and normal sign-up flows. Do not misrepresent identity to get sales calls
or internal material, and read the terms of service before any automated scraping.

## Ask the user

- **What is this business meant to become?** A one-founder income and a venture-scale company need
  very different market sizes. Default: profitable with one founder, so a few hundred to a few
  thousand customers is enough.
- **How long and how much to spend validating before building?** Default: four weeks, with only a
  small test budget for ads.
- **What is the founder's unfair advantage?** It changes the scores and the first segment. Default:
  assume none and score honestly.
- **Is taking money before the product exists acceptable?** Default: yes, with a delivery date and
  refund on request.
- **Which ideas or segments are on the table?** Default: score at least three before committing.
