# Positioning and messaging

Read this when: describing the product for the first time, writing or rewriting the homepage,
choosing or changing a name, collecting testimonials and case studies, or when visitors "do not
get it" and the words are the suspect.

## Decide the positioning before writing copy

Positioning is a set of decisions; copy only expresses them. Headlines written first produce
clever sentences about an undefined product, and every page then tells a different story. Make
the decisions in this order, because each depends on the one before (the sequence follows April
Dunford's method):

| # | Decision | The question | The usual mistake |
|---|---|---|---|
| 1 | Competitive alternatives | What would the best customers do if this product disappeared tomorrow? | Listing only look-alike startups. The real alternative is usually a spreadsheet, an agency, a hire, a generic tool stretched to fit, or doing nothing |
| 2 | Differentiated capabilities | What can this do that those alternatives cannot? | Listing features every alternative also has |
| 3 | Value | What does each capability produce for the customer, in their terms? | Stopping at the feature ("AI summaries") instead of the outcome ("month-end close in one day") |
| 4 | Target customer | Who cares most about that value, by observable traits and a trigger? | Demographics ("SMBs", "creators") instead of a situation ("agencies invoicing a dozen retainer clients a month") |
| 5 | Market category | Which frame makes the value obvious at a glance? | Inventing a category before anyone looks for it |

Work from evidence. The inputs are the customers who reached value fastest and stayed, and their
own words: interview notes, support tickets, sales-call transcripts, reviews they wrote of the
alternatives. Positioning built from the founder's vision instead describes a product nobody in
particular buys. At Prototype, with no customers, positioning is a hypothesis: write it anyway,
so the landing page, outreach and launch posts test one coherent story instead of five
(interview method: `0x:product-discovery`).

Record the result as an internal statement. It is a decision record, not copy:

```text
For [target customer + trigger situation]
who today [competitive alternative and what it costs them],
[product] is a [market category]
that [primary value, stated as an outcome].
Unlike [the alternative], it [differentiated capability],
shown by [the strongest proof available].
```

A slot that cannot be filled with something specific is the next piece of work. Do not paper
over it with adjectives in the copy.

## Proof, strongest first

| Proof | Form | Notes |
|---|---|---|
| Named customer, quantified result, time frame | "[Name, role, company]: errors went from A to B per month within a quarter" | The target for every value pillar |
| Recognizable customer logo | Logo row | Needs written permission; many enterprise contracts forbid logo use |
| Usage numbers | "[N] teams", "[N] documents processed" | True, current, defined consistently; a stale counter erodes trust |
| Demonstration | Interactive demo, video, free tool, open-source code | Strongest when the visitor can try it without signing up |
| Mechanism | How it works and why that is faster or safer | Persuades technical buyers; weak alone for others |
| Third party | Marketplace ratings, review sites, press | Only real ones; buyers check |
| Unnamed praise | "Great tool! (J., founder)" | Close to no value; often reads as invented |

## The homepage headline: five seconds for a stranger

A stranger must be able to answer three questions within about five seconds: what is it, is it
for me, what do I do next. Headline, subhead, product visual and call to action share that job.

| Element | Job | Rule |
|---|---|---|
| Headline | The outcome or the thing, and for whom | Concrete nouns and verbs the target customer uses; roughly ten words or fewer |
| Subhead | How it works, or what it replaces | One sentence naming the mechanism or the alternative |
| Visual | Proof it is real | The actual product producing the result, not an abstract illustration |
| CTA | The next step and its cost | "Start free, no card" beats "Get started" |

Headline patterns and when each fits:

- **Outcome for an audience**: "Payroll for restaurants that runs itself". The default.
- **Known category, narrow segment**: "The CRM for recruiting agencies". When the category is
  well understood and the segment is the point.
- **Replace the alternative**: "Stop reconciling bank exports in spreadsheets". When the
  alternative is painful and instantly recognized.
- **Analogy ("Stripe for X")**: only for an audience that knows the reference; it fails with
  everyone else and dates quickly.

Cut abstract benefit words (empower, unlock, seamless, next-generation, all-in-one), questions as
headlines, puns, and anything that would fit a competitor's page unchanged. The swap test: if a
competitor's name could replace this one and the sentence stays true, the headline says nothing.

Check with people, not opinions. Show the above-the-fold area for five seconds to five people
who match the target customer (a remote five-second-test tool works), then ask what the product
does and who it is for. If fewer than four of five come close to the intended meaning, rewrite;
do not argue with the result.

## Messaging hierarchy

One document that every page, ad, email and launch post draws from, so the story stays the same
when written by different people, or different sessions, months apart.

| Level | Content | Used on |
|---|---|---|
| Core promise | One sentence: the value for the target customer | Headline, meta description, social bios, launch posts |
| Value pillars | Three, rarely four; each a distinct outcome tied to a differentiated capability | Homepage sections, feature pages, ad angles |
| Proof points | Two or three per pillar, from the proof table | Next to the pillar they support |
| Objections | Each reason a qualified visitor does not act, with its answer | FAQ, pricing page, next to CTAs, sales calls |
| Segment variants | Pillars reordered and reworded per segment or use case | Use-case pages, campaign pages, outreach |

The recurring objections and what answers them:

| Objection | Answer with |
|---|---|
| "Will it work for my case?" | A use-case page or template for that case; a named customer like them |
| "Switching is painful" | Import tool, migration done for them, setup time stated in minutes |
| "Is my data safe?" | Security page, where data is stored, export at any time |
| "Too expensive" | The cost of the current alternative; a case-study number; free tier or guarantee |
| "Will this company still exist next year?" | A visible founder, a changelog showing steady shipping, data export |
| "No time to set it up" | Time to first value, stated and true; setup help |

Keep the hierarchy in the repository (for example `docs/messaging.md`) so that code generating
pages, emails and ads can follow it, and so changes to it are reviewed like code.

## Category and honest alternatives

Choose the category by where buyers already look and budget:

| Situation | Choice |
|---|---|
| Buyers search and budget for an existing category, and the product is strongest in one segment of it | Existing category, narrowed: "the X for Y". Default for a small team |
| The obvious category frames the product badly (it gets compared on features it lacks) | An adjacent category whose buyers value what it does best |
| No category fits and a visible trend is creating demand | A new category, only with the money and years to educate a market; rarely right for a solo founder |

Name the alternatives honestly on the site, including the non-product ones (spreadsheets, an
agency, a hire). Say when an alternative is the better choice ("If you need on-premise
deployment, X fits better"). This qualifies traffic, reduces churn from bad-fit customers, and
makes the rest of the page believable. Comparative claims must be true and verifiable when
published and kept current: date comparison tables, never imply the competitor endorses
anything, and expect stricter rules on comparative advertising in the EU than in the US.
Drafting comparison and alternative pages for search: `seo-aeo-geo-ultimate`.

## Naming

A name gets expensive to change after Launch: domain, trademark, links, integrations, store
listings and customer memory attach to it. Screen in this order, because the early checks are
fast and eliminate most candidates:

1. **Shortlist 10 to 20.** Prefer invented words, unrelated real words and suggestive names;
   avoid descriptive names ("Fast Invoice"), which are hard or impossible to register and that
   anyone may use.
2. **Say it aloud.** Someone who hears it once can spell it; it has no unfortunate meaning in
   the languages of the target markets.
3. **Domain.** A `.com` is ideal, not required; a prefixed `.com` (get-, use-, try-) or a
   fitting TLD (`.dev`, `.io`, `.ai` for technical buyers) is acceptable. Avoid hyphens and
   digits. Check the domain's history in the Wayback Machine and on spam blocklists: a domain
   once used for spam can carry email-reputation damage.
4. **Trademark knockout search.** Search identical and similar names in the classes covering
   the product (Nice class 9 for downloadable software, 42 for SaaS, 35 for some business
   services) in each target market: the USPTO trademark search, EUIPO's TMview, the WIPO Global
   Brand Database, and national offices of other key markets. A similar-sounding mark in the
   same class for related goods is a conflict even when spelled differently.
5. **Handles and listings.** X, LinkedIn, GitHub organization, YouTube and whichever social
   networks the customers use, the package-registry name for developer tools, app store names.
6. **Secure on the same day**: the domain (and the obvious misspelling) and every handle.
7. **Before spending on brand (Launch)**: a trademark attorney's clearance and a filing in the
   main market. Ownership and filing: `0x:company-building`.

A forced rename after a trademark dispute costs months; the knockout search costs an afternoon.

## Testimonials and case studies

Ask at moments of felt value: right after an activation milestone, after support fixed a
problem, at an upgrade or renewal, or when a customer praises the product unprompted in email,
chat or a public post. A quarterly survey collects little.

Questions that produce specific answers:

- What did you use before, and what was wrong with it?
- What made you try this, and why then?
- What changed afterwards? Which number moved, by how much, over what period?
- What would you tell someone in your position who is considering it?

Draft the quote from their words, send it for approval, and record written permission for name,
photo, title, company and logo, with the date. The legal floor in the US and EU: testimonials
are genuine and reflect the customer's real experience; incentives for reviews or testimonials
are disclosed and never conditional on a positive opinion; invented testimonials, including
AI-generated "customers", are unlawful; a quote featuring an exceptional result must not imply
it is typical.

Case study, one page:

| Section | Content |
|---|---|
| Headline | The result with its number: "How [company] cut [metric] from A to B in [period]" |
| Customer | Size, industry, the champion's role; one line |
| Before | The alternative they used and what it cost them in hours, money, errors or risk |
| Trigger | Why they looked for something new, at that moment |
| Choice | Why this product over the alternatives, in their words |
| Rollout | Time to first value, who was involved |
| Results | Before and after with numbers and period; absolute figures beside percentages |
| Quote | One sentence a reader remembers |

Numbers come from the customer's records or from product data they agree to publish, never from
the founder's estimate. Larger customers route approval through marketing or legal: allow weeks,
and offer something back (early access, a link, co-promotion). Publish a one-line version of
each result for the homepage and pricing page.

## Test messaging before scaling spend

Ads, redesigns and launches multiply whatever the message is. Test the message first, cheaply:

1. **Explain-back**: show the homepage or a one-paragraph pitch to five to ten target prospects
   and ask them to describe the product as they would to a colleague. Adopt the words they use.
2. **Live calls**: in sales or support conversations, try alternative one-sentence pitches and
   note which one makes people ask a follow-up question.
3. **Headline ad test**: three to five headlines, one audience, small equal budgets, the same
   landing page. Click-through rate measures resonance only; confirm with signups.
4. **Subject lines and outbound angles**: differences in replies between pain angles show which
   pain is sharper (outreach itself: `0x:sales-support`).
5. **Paid message-testing panels** of respondents in the target role exist for B2B when
   prospects are hard to reach.

Do not A/B test homepage headlines at low traffic: without several hundred conversions per
variant the result is noise (sample size: `0x:product-analytics`). Make one bold change, check it
with explain-back, and keep the version prospects repeat correctly.

## Ask the user

- **Who are the three to five best customers today, and what did they use before?** Positioning
  is derived from them. Default: with none yet, position for the narrowest segment the founder
  can name and reach this month.
- **Which customer names, logos and numbers may be published?** Default: nothing public without
  written approval.
- **Which claims can be substantiated with a source?** Default: drop every claim without one.
- **Which markets matter for the name, and is there budget for trademark counsel?** Default:
  knockout search before choosing; attorney clearance and a filing before Launch spending.
- **If two segments compete for the headline, which comes first?** Default: the one with the
  shortest path to paying; the other gets its own use-case page.
