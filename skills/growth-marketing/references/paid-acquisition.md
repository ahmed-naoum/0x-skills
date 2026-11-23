# Channel selection and paid acquisition

Read this when: nobody is signing up and the question is where to find customers, choosing which
channel to focus on, running search or social ads, buying newsletter, podcast or creator
sponsorships, deciding whether to stop or scale a channel, hiring an agency, or setting up
retargeting.

## Test a few channels, then master one

Young companies that grow usually get most of their customers from one channel for a long time.
Spreading a solo founder's effort over six channels produces six mediocre efforts and no
learning.

1. **List candidates** where the target customer already looks for a solution or gathers:
   search, communities, marketplaces and integrations, content, outbound, partners, sponsorships,
   social ads, events. Include the unglamorous ones.
2. **Shortlist three** by fit with the product (table below) and by the founder's unfair
   advantage: an existing audience, a network, a skill.
3. **Test the three in parallel, cheaply.** Each gets a fixed budget of time or money, a fixed
   duration of a few weeks, a success metric set in advance (cost per activated signup or per
   qualified conversation, never clicks) and a written stop rule.
4. **Pick the one with the best economics and the most room to grow**, and give it most of the
   effort (rule of thumb: well over half) until its results plateau.
5. **Add a second channel** when the first one's marginal returns fall, or when depending on it
   becomes a risk (`community-partnerships.md`).

| Product and buyer | Channels to test first |
|---|---|
| Developer tool | Docs and content, Show HN and developer communities, open source, integrations |
| SMB SaaS, self-serve | Search (content plus ads on high-intent terms), marketplaces and integrations, comparison pages |
| B2B, high price | Outbound and the founder's network (`0x:sales-support`), LinkedIn content, partners, events |
| Consumer app | Short-video creators, social ads with strong creative, app store optimization, referral loops |
| Product used by teams | Invite and collaboration loops (`referral-loops.md`), templates, integrations |
| Niche professional audience | Niche newsletters and podcasts, professional communities and associations |

Search ads capture demand that already exists; social ads and sponsorships create it. When
nobody searches for the problem, search ads fail however well they are run.

## The CAC ceiling, computed before spending

Every paid channel needs a maximum customer acquisition cost derived from the economics and set
before the first dollar. Work backward from it to a maximum cost per click to learn whether a
channel can work at all:

| Step | Example (illustrative numbers) |
|---|---|
| Average monthly revenue per customer | 40 |
| Gross margin | 80%, so 32 of margin per month |
| Target payback period | 6 months |
| CAC ceiling = margin per month × payback months | 192 |
| Paid conversion from signup | 10%, so at most 19.20 per signup |
| Signup rate from ad click | 5%, so at most 0.96 per click |

If the going cost per click for the target keywords (shown in the platform's planning tools)
is above the last number, search ads cannot work at today's conversion rates: improve
conversion or choose another channel before spending.

- Payback target by funding: a bootstrapped company needs payback within a few months because
  cash is the constraint; a funded company may accept a year or more. Unit economics and
  churn-adjusted lifetime value: `0x:pricing-monetization`.
- Replace the assumptions with the channel's own cohort numbers as soon as they exist: paid
  users often convert and retain differently from organic ones.
- Set hard daily and monthly budget caps in the ad account. Platforms spend what they are
  allowed to.

## Conversion tracking before the first campaign

Without accurate conversion data, ad platforms optimize toward whatever is cheapest to get,
which is usually the wrong user.

- **Server-side conversions**: send signups, activations and purchases from the backend to the
  platforms (Meta's Conversions API, Google Ads enhanced and offline conversions). Browser
  pixels alone lose a large share of events to ad blockers, tracking protection and declined
  consent.
- **Deduplicate** browser and server events with a shared event ID.
- **Keep the click ID** (`gclid`, `fbclid` and the like) and UTM parameters on the account at
  signup, so a payment weeks later can be sent back as an offline conversion.
- **Optimize toward the deepest event with enough volume.** Purchases are the truth but may be
  too rare for the platform to learn from; activation is usually the best proxy; optimizing for
  raw signups invites junk signups.
- **Consent**: in the EEA and UK, tags must follow the visitor's consent, and Google requires
  consent signals for measurement and audience features with users there; in US states with
  privacy laws, honor opt-outs of "sharing" for targeted ads, including browser signals such as
  Global Privacy Control where the law requires it (`0x:privacy-compliance`).
- **Check**: complete a signup and a test purchase, then confirm each appears exactly once in
  every platform's event view before any campaign goes live.

## Running search ads without waste

Ad platform defaults favor spend. Settings to change in Google Ads (they move and get renamed;
confirm them in the current interface):

- **Networks**: search only. Untick the Display Network on search campaigns; leave search
  partners off at first and test them later.
- **Location**: target people in or regularly in the locations ("Presence"), not people who are
  merely interested in them.
- **Auto-applied recommendations**: off; review recommendations by hand.
- **Keywords**: start narrow, with exact and phrase match on high-intent terms (the job plus
  "software", "tool" or "app"; "alternative to [competitor]"). Use broad match only with
  conversion-based bidding and plenty of conversion data.
- **Negative keywords** from day one: jobs, salary, free (unless there is a free plan), course,
  tutorial, definitions, competitors' login and support searches. Read the search-terms report
  weekly and keep adding.
- **Bidding**: manual or click-maximizing with a bid cap until conversions flow steadily, then a
  target cost per acquisition set from the CAC ceiling.
- **Brand campaign**: cheap protection for the product's own name. Test whether it is
  incremental by pausing it; many of those clicks would arrive organically.
- **Competitor terms**: bidding on a competitor's name is generally allowed; using their
  trademark in the ad text often is not. Send those clicks to an honest alternative page.

## Testing creative and audiences

On social platforms, creative does most of the targeting: broad audiences with strong, varied
creative usually beat narrow interest stacks, and the platforms' automated audiences depend on
clean conversion data.

Test in this order, because each level outweighs the ones below it:

1. **Angle**: the pain, the outcome, the alternative, social proof, the product demo itself.
2. **Hook**: the first seconds of video, or the headline.
3. **Format**: short video, static image, carousel, founder speaking to camera.
4. **Details**: wording, colors, call to action.

- One variable per test, equal budgets, enough spend per variant to reach a meaningful number of
  conversions rather than clicks. A click-through winner often loses on cost per activated user.
- Platforms need a minimum number of optimization events per ad set each week to leave their
  learning phase; check the current figure. Consolidate ad sets instead of splitting a small
  budget many ways, and avoid edits during learning, which restart it.
- **Fatigue**: rising frequency with falling click-through means the audience has seen the ad
  too often. Rotate in new angles before performance collapses.
- Keep a test log: hypothesis, variants, spend, result, decision. Winning angles feed the
  landing page and the messaging hierarchy (`positioning-messaging.md`).
- LinkedIn ads cost far more per click than the other platforms; they fit high-price B2B, where
  job-title and company targeting justifies the price.

## Sponsoring newsletters, podcasts and creators

- **Selection**: ask for audience composition (roles, company sizes, countries), click rates on
  past sponsorships, and whether sponsors rebook; rebooking is the most honest signal. Read
  several past issues or episodes first.
- **Price**: usually per placement, often quoted per thousand subscribers or listeners.
  Negotiate a test placement, then a package.
- **Judge after two or three placements**, not one: recognition builds with repetition.
- **Creative**: written in the publication's voice. For podcasts and creators, give talking
  points rather than a script; a host's own words convert better. One CTA, a memorable URL.
- **Tracking**: a landing page per publication, an offer code, UTM parameters, and the "how did
  you hear about us" field. Tracked conversions badly undercount sponsorships; estimate the true
  total from the self-reported answers.
- **Disclosure**: paid placements must be identifiable as advertising in the US, the EU and most
  markets; put the requirement in the agreement. Agree on usage rights if creator content will
  be reused in ads.

## Deciding when to stop or scale a channel

Keep a monthly table per channel by signup cohort: spend, signups, activation rate, paid
conversions, CAC, months to payback, retention at a fixed age (for example 90 days).

Stop or rework a channel when:

- CAC stays above the ceiling after the test budget and at least two rounds of optimization
  (landing page, creative, targeting).
- Its cohorts churn faster, so payback on retained revenue fails even though first-month CAC
  looks fine.
- An incrementality test shows little lift: pause the channel for a few weeks (or only in some
  regions) and check whether total signups fall. Retargeting and brand search often fail this.

Scale a channel by raising the budget in steps while watching marginal CAC, the cost of the
additional customers rather than the average. Returns diminish as spend grows; the channel's
useful size ends where marginal CAC crosses the ceiling.

## Judging an agency or freelancer

- **Hire after the founder has proven the channel at small scale**, or when the founder lacks
  the skill and can fund several months of testing.
- **Ownership**: the company owns the ad accounts, pixels, analytics, domains and creative
  files; the agency gets user access. An agency running ads from its own account leaves with
  the history.
- **Terms**: a trial period of two to three months with written targets, then month to month. A
  fee as a percentage of spend rewards spending; prefer a fixed fee plus a bonus tied to CAC or
  pipeline.
- **Reporting**: weekly spend, CAC, cost per activated signup, pipeline or revenue by cohort.
  Reports built on impressions, reach and clicks describe activity, not results.
- **Red flags**: guaranteed results, refusal to grant account access, long lock-in, no testing
  plan, success shown only as platform-attributed conversions.

## Retargeting within consent and frequency limits

- **Consent first**: in the EU and UK the retargeting pixel needs consent; in US states with
  privacy laws, cross-context behavioral advertising must honor opt-outs
  (`0x:privacy-compliance`). Platforms also restrict retargeting in sensitive categories such
  as health and finance.
- **Audiences**: high-intent visitors only (pricing page, signup started, docs readers) over a
  short window, typically one to four weeks.
- **Exclusions**: current customers and recent signups, synced from the product or excluded via
  the conversion event. Ads to people who already bought waste money and annoy them.
- **Frequency cap**: a few impressions per person per week. Being followed around the web by
  one ad damages the brand.
- **Creative**: answer the objection they likely had (proof, pricing, a case study); do not
  repeat the ad they already ignored.
- **Measurement**: retargeting claims credit for conversions that would have happened anyway.
  Test incrementality with a holdout before scaling it, and keep it a small share of spend.

## Ask the user

- **How much can be spent on testing per month, and for how long?** Default: a fixed test budget
  for four to six weeks across at most three channels, stop rules written first.
- **What payback period can the company afford?** Default: a few months if bootstrapped, up to a
  year if funded.
- **What are revenue per customer and gross margin?** The CAC ceiling depends on them. Default:
  estimate conservatively and replace with cohort data after the first months.
- **Which markets are targeted?** Consent rules and ad prices depend on them. Default: the
  markets where today's customers are.
- **Is an agency or freelancer being considered?** Default: not until the founder has run the
  channel at small scale.
