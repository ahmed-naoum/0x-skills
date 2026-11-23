---
name: growth-marketing
description: "Gets the product found and tried: positioning and homepage copy, landing pages that convert, launches on Product Hunt, Hacker News and communities, content that brings signups, welcome and win-back email sequences, ads with a CAC ceiling, referral and invite loops, communities, integrations and partners. Use when nobody signs up, choosing a first marketing channel, planning a launch or writing marketing copy."
---

# Growth and marketing

## Stance

A solo founder's product rarely fails for lack of features; it fails because the right people
never hear of it, or hear of it in words that do not land. An experienced growth operator treats
distribution as part of the product: decides who it is for and against what before writing a
word, puts the scarce hours into one channel at a time, and judges every effort by activated
and paying users. Most of the work is unglamorous repetition done consistently for months.

- **Positioning before copy.** Who it is for, what it replaces, why it wins and the proof come
  first, in the customers' own words. Copy written before those decisions argues with itself
  across every page.
- **Retention before amplification.** Launches, ads and loops multiply what the product already
  is. On a product people abandon in a week, they buy faster churn.
- **One channel at a time.** Test a few cheaply with stop rules written in advance, then master
  the one with the best economics. Six half-run channels teach nothing.
- **Measure customers, not attention.** Signups, activation and revenue per channel cohort.
  Pageviews, opens, votes and impressions are activity; optimizing them misleads.
- **Set the economics before spending.** A CAC ceiling from margin and payback, budget caps and
  a kill rule come before the first ad dollar, sponsorship or agency contract.
- **Earn standing before asking.** Communities, journalists and partners reward people who gave
  first. Borrowed audiences punish promotion; the email list is the audience the company owns.
- **Specific proof beats adjectives.** Named customers with numbers and time frames persuade.
  Invented testimonials, fake scarcity and unsubstantiated claims break consumer law in the US,
  EU and UK, and destroy trust when found.
- **Behavior triggers messages.** Lifecycle email and in-app nudges fire on what users did or
  did not do, and stop the moment the goal is reached.
- **Sustainable beats spectacular.** A cadence the founder can keep for a year (posts, issues,
  launches) outperforms a burst that stops.

Follow the project first: if a marketing site, email tool, analytics setup or ad account already
exists, work within it. The defaults below are for new decisions.

## Route

| If the task is … | Read |
|---|---|
| "Write the positioning", homepage headline and copy, "people don't get what it does", choosing a name, collecting testimonials, writing a case study, testing messages | `references/positioning-messaging.md` |
| "Build a landing page that converts", which pages the marketing site needs, visitors leave without signing up, where to put social proof, recording a demo video, campaign-specific pages | `references/landing-conversion.md` |
| Planning a launch: waitlist, beta, Product Hunt, Show HN, Reddit and community posts, press and newsletter pitches, launch-day checklist, after-launch follow-up, announcing a feature | `references/launches.md` |
| A content strategy that brings signups, editing AI-written articles, building in public, docs or free tools as acquisition, repurposing, measuring content | `references/content-marketing.md` |
| Email capture, welcome and activation sequences, trial emails, in-app nudges, segments, a newsletter, win-back and list cleanup, whether emails work | `references/email-lifecycle.md` |
| "Nobody is signing up, where are the customers?", which channel first, running Google or Meta ads, CAC limits, sponsorships, stopping a channel, hiring an agency, retargeting | `references/paid-acquisition.md` |
| Referral program, invite loop, share and public pages, template gallery, "Made with" badge, referral fraud, product-qualified leads, viral coefficient | `references/referral-loops.md` |
| Promoting in communities, starting a Discord or forum, depending on one platform, integrations and marketplace listings, co-marketing, affiliates and resellers, entering a new country | `references/community-partnerships.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| First channel | Three cheap tests with stop rules, then focus on one | The founder already has an audience or network in the market: start there |
| Positioning | Narrow segment of an existing category, "the X for Y" | The category frames the product badly: adjacent category |
| Homepage CTA | Free signup, no card, OAuth plus email | Higher-price, sales-assisted product: book a demo |
| Headline | Outcome for an audience, checked with a five-second test | |
| Launch | Beta, waitlist drip, own channels, then one borrowed channel per day | Small feature: changelog, segment email, in-app |
| Content | Decision- and solution-intent pieces first, drafted from the founder's own explanation, every week or two | No search or discussion of the problem: content is a second channel |
| Lifecycle email | Event-triggered activation sequence with exit conditions, signed by the founder | |
| Marketing consent | Explicit email opt-in everywhere; double opt-in for EU signups; marketing SMS only with express written consent | Counsel confirms a market-specific basis (US opt-out email, UK corporate B2B, EU soft opt-in) |
| Paid ads | None at Prototype; at Launch only with server-side conversions and a CAC ceiling | |
| Search vs social ads | Search when people search for the problem; social or sponsorships when they do not | |
| Loops | Invite at the moment of need, before any incentive program | No collaboration in the workflow: double-sided referral credit |
| Referral reward | Double-sided product credit after the first paid period clears | B2B referrer cannot use credit: cash or gift card |
| Community | Participate in existing ones; own community only when users ask | |
| New market | Payment methods and local prices before translation | |
| Attribution | First-touch UTM, click ID, referral code and self-reported source on the account | |

By stage:

- **Prototype**: positioning statement, one page with a waitlist and a qualifying question, a
  personal launch list, steady participation in two or three communities, founder emails sent by
  hand. Skip ads, referral programs, an own community and designed newsletters.
- **Launch**: staged launch; home, pricing, feature, about and legal pages; the activation
  sequence; a content program on one platform; testimonials and a first case study; channel
  tests with written stop rules; attribution stored at signup.
- **Scale**: paid channels with incrementality tests, holdouts on lifecycle messages, in-app
  messaging, product-qualified lead routing, affiliates, marketplace listings, localization.

## Before you call it done

1. The positioning statement has every slot filled specifically, and at least four of five
   target-like people describe the homepage correctly after five seconds.
2. Every claim, number, logo and testimonial on the site is real, sourced, current and
   permitted in writing; any incentive behind a testimonial is disclosed beside it, and
   public-review requests go to all customers in a group, not only happy ones.
3. Each landing page has one primary CTA visible without scrolling on a phone, and its headline
   repeats the promise of the ad or link that sends traffic to it.
4. Signup stores first-touch UTM parameters, ad click IDs, referral or affiliate code and a
   free-text "how did you hear about us" answer on the account.
5. Before any ad spend, each conversion event reaches every ad platform exactly once, sent from
   the server and deduplicated against the pixel, verified with a test signup and purchase.
6. Every paid channel has a CAC ceiling, a budget cap in the ad account and a stop rule written
   before it started.
7. Lifecycle messages trigger on events with exit conditions; a test account that activates
   receives no further activation nudges, and no user gets more than one lifecycle email a day.
8. Marketing email and SMS have stored consent records per recipient (source, time, wording,
   country), an unsubscribe in every message, and are sent separately from transactional mail.
9. Launch posts are written per community and follow each community's rules; nothing anywhere
   asks for upvotes.
10. Public launch gates passed: drip cohorts activate unaided, marketing pages cached, alerts
    on, billing live, payment provider warned of the spike, support staffed.
11. AI-drafted content was checked against primary sources, contains first-hand material, and
    carries a real author's byline.
12. Referral and affiliate rewards are paid only after payment clears the refund window, with
    caps and fraud checks in place.
13. Public user-generated pages have a report and takedown path and are noindexed by default.
14. Results are reported as activated and paying users per channel cohort, not as visits,
    opens, votes or impressions.

## Not this skill

- SEO, keyword research, technical SEO and AI-search visibility → `seo-aeo-geo-ultimate`
- Email deliverability, SPF, DKIM, DMARC and sending infrastructure → `0x:email-notifications`
- Attribution models, funnel analysis and experiment statistics → `0x:product-analytics`
- Outbound sales, demos and closing deals → `0x:sales-support`
- Price points, plan packaging and discount policy → `0x:pricing-monetization`
- Validating the problem before there is a product → `0x:product-discovery`
- Consent banners, cookie rules and marketing-permission law → `0x:privacy-compliance`
- Review-site profiles, complaints and reputation → `0x:sales-support`
