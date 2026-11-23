# Landing pages and conversion

Read this when: building the marketing site or a landing page, deciding which pages the site
needs, recording a demo video, or finding out why visitors arrive and leave without signing up.

## One page, one promise, one action

A landing page moves one kind of visitor to one next step. Every element either supports the
promise, removes a doubt, or is cut. The default skeleton, top to bottom:

| Section | Job | Notes |
|---|---|---|
| Hero | Headline, subhead, primary CTA, product visual | Headline method in `positioning-messaging.md`. CTA and product visual visible without scrolling on a phone |
| Proof strip | "People like me use it" | Permitted logos, a usage number, or one short quote |
| Problem and alternative | The current way and what it costs | In the customer's words |
| How it works | Three steps from signup to outcome | State time to value when it is short |
| Value pillars | Two to four outcomes, each with its proof | A screenshot or short clip per pillar |
| Demo | Video or interactive demo | See the demo section |
| Objections | FAQ answering real objections | Taken from sales calls and support, not invented |
| Pricing teaser | Starting price or "free plan", link to pricing | Hidden prices raise doubt on self-serve products |
| Final CTA | The primary action again | Same wording as the hero |

CTA by product type:

| Product | Primary CTA | Secondary |
|---|---|---|
| Self-serve with free plan or trial | "Start free", with the removed friction stated ("no card") | Demo video |
| High price, sales-assisted | "Book a demo", calendar on the next screen | Short recorded tour |
| Developer tool | "Get started" into a quickstart, or the install command inline | Docs, repository |
| Not launched yet | "Join the waitlist", saying what and when | None |

Signup asks only for what the first session needs: email plus OAuth (Google; GitHub for
developer tools) by default. Company, role and team size move to onboarding, where the answers
personalize the product; on the signup form each extra field costs completions. Whether a trial
requires a card is a pricing decision (`0x:pricing-monetization`); a free plan never does.

## The marketing site

| Page | Job | Add at |
|---|---|---|
| Home | Promise, proof, one action for the main segment | Prototype |
| Pricing | Plans, what each includes, billing FAQ | Launch, or as soon as charging |
| Feature pages | One per value pillar, with deeper proof | Launch |
| Use-case or role pages | The same product framed for one segment's job | When a second segment converts |
| Comparison and alternative pages | "Product vs X", "X alternatives", honest | When prospects ask how it differs from X |
| Customers | Case studies, proof in depth | With the first case study |
| Docs | Quickstart, guides, reference | Launch for developer tools, where it is the most visited page |
| Changelog | Proof the product is alive; feeds launches | Launch |
| Blog or resources | The content program (`content-marketing.md`) | When content is a chosen channel |
| Security and trust | Data location, subprocessors, posture, contact | When the first B2B prospect asks |
| About | Who is behind it, with a real name and face | Launch |
| Legal | Terms, privacy policy, cookie choices | Before collecting personal data (`0x:privacy-compliance`) |

Serve marketing pages statically from a CDN, either inside the product's Next.js app or as a
separate site when a non-developer edits through a CMS (where content lives: `0x:react-nextjs`).
A slow page loses visitors before the message is read: keep landing pages within the Core Web
Vitals "good" thresholds on a mid-range phone (`0x:web-performance`). Third-party scripts (chat
widgets, session recorders, ad pixels) are the usual cause; load them late or not on the hero.

## Finding why visitors leave

Quantify first, then watch. Rewriting copy without knowing where people drop wastes weeks.

1. **Funnel by source and device.** Visitors, CTA clicks, signup started, signup completed,
   activated. Launch, search and paid traffic behave differently; a blended rate hides the
   problem. Building the funnel: `0x:product-analytics`.
2. **Work only on the largest drop.**
3. **Scroll depth.** If most visitors never reach the proof or the pricing teaser, move proof
   up. If they reach the bottom and still do not click, the offer or an unanswered doubt is the
   problem, not the layout.
4. **Session recordings** of non-converters from the source that matters: watch 20 to 30. Look
   for hesitation on a section, clicks on elements that are not links (they expected one), rage
   clicks, loops between pricing and home, and the form field where people stop. Mask every
   input; record only after consent wherever consent is required (`0x:privacy-compliance`).
5. **Five-second test** of the hero with people who match the target customer.
6. **Ask.** A one-question on-page or exit poll ("What is stopping you from signing up
   today?"), and an email to recent signups asking what nearly stopped them. A dozen answers
   usually name the problem.

| Symptom | Likely cause | Fix |
|---|---|---|
| High bounce, seconds on page | Headline unclear or not matching the link or ad | Message match, five-second test, rewrite |
| Scroll to the bottom, no CTA click | Doubt unanswered or offer unattractive | Proof and objection answers; lower-commitment CTA |
| CTA clicked, signup abandoned | Form friction, unexpected card request, OAuth error | Fewer fields, requirements stated up front, test on a phone |
| Pricing page visit, then exit | Price shock or unclear plan fit | Plan recommendation, value proof next to the price |
| Good signup rate, poor activation | The page promises what the first session does not deliver | Align the promise and onboarding (`email-lifecycle.md`) |
| Mobile far below desktop | Layout, speed or form problems on phones | Test on a real mid-range phone over a slow connection |

At low traffic, A/B tests cannot detect realistic differences. Below several hundred
conversions per variant, make large changes based on the evidence above and compare periods
carefully, watching source mix and seasonality. Experiment design: `0x:product-analytics`.

## Social proof where doubt occurs

A testimonial block at the bottom of the page answers nobody's question. Put each piece of proof
where its doubt arises:

| Where | The doubt | Proof that answers it |
|---|---|---|
| Hero | "Is this real, and do others use it?" | Logos, a usage number, a rating from a known review site |
| Each feature claim | "Does it really do that?" | Screenshot of the result, a metric, a quote about that feature |
| Pricing | "Is it worth it?" | Case-study number, a return-on-cost quote, refund policy or guarantee |
| Signup form | "Will I regret this?" | "No card required", "cancel anytime", a one-line privacy note |
| Enterprise section | "Is it safe and compliant?" | Security page, compliance status that is true today, DPA, SSO |
| Final CTA | "Will anyone help me?" | Support response time, founder contact, community |

A quote with full name, role, company and photo carries weight; an anonymous quote carries
almost none. Use only real, current, permitted proof. Fake counters, invented scarcity ("3 spots
left"), fake "someone just bought" pop-ups and pre-checked add-ons are dark patterns that US and
EU consumer regulators act against, and that experienced buyers recognize immediately.

## The demo video

It sells the outcome, not a tour of the interface.

- **Script before recording.** The first five seconds show the result (the finished report, the
  workflow running by itself). Then the problem in one sentence, then three moments of the
  product producing the outcome on realistic data, then the CTA.
- **Length**: 60 to 120 seconds for the homepage. A longer walkthrough for evaluators lives on
  its own page.
- **Recording**: a seeded demo account with realistic fictional data; no real customer data,
  notification badges or personal tabs; high resolution, zoomed on the area of action, slow and
  deliberate cursor. Screen recorders with automatic zoom save most of the editing.
- **Works without sound**: autoplaying video is muted. Burn in captions or ship a caption track;
  a short silent loop in the hero works as a moving screenshot.
- **Performance**: never load a video player with the page. Show a poster image and load the
  player on click, or self-host a compressed MP4 with `preload="none"` and a poster
  (`0x:web-performance`).
- **Maintenance**: re-record when the interface changes visibly; an old interface in the video
  signals a neglected product. Keep the script in the repository so re-recording is cheap.

## Dedicated pages per campaign and intent

Send each distinct intent to a page that continues the conversation the visitor came from. The
homepage serves the average visitor, and therefore no particular one.

| Traffic | Page | Message match |
|---|---|---|
| Search ad on a competitor's name | "[Competitor] alternative" | Names the competitor and states honestly how this differs |
| Search ad on a job to be done | Use-case page | Headline repeats the searched job |
| Newsletter or podcast sponsorship | Page naming the publication, with its offer | "For [publication] readers" |
| Integration or marketplace listing | Integration page | Shows the combined workflow |
| Community launch post | Page with the post's angle and any community offer | The same words as the post |

- The headline repeats the promise of the ad or link. A mismatch is the most common reason a
  paid page converts worse than the homepage.
- Remove the main navigation from paid-campaign pages; keep the footer and legal links.
- Paid-only variants that duplicate an indexable page get `noindex`; pages meant to rank are
  built for search (`seo-aeo-geo-ultimate`).
- Tag every inbound link with one UTM scheme (lowercase, one spelling per source) and store the
  first-touch parameters on the account at signup, so channels can later be compared by
  activation and revenue rather than visits (`0x:product-analytics`).
- Build pages from shared section components so a new campaign page takes an hour. When it
  takes a day, campaigns get sent to the homepage.

## Ask the user

- **What single action should a visitor take?** Free signup, trial, demo or waitlist changes the
  whole page. Default: free signup for self-serve products priced for individuals and small
  teams; demo for sales-assisted, higher-priced products.
- **May the price be shown publicly?** Default: yes for self-serve; hidden pricing only for
  sales-led products.
- **Which proof may be used: logos, names, numbers?** Default: only what is approved in writing.
- **Is session recording acceptable for the product's privacy stance and markets?** Default:
  inputs masked, recording only after consent where consent is required.
- **Who will edit the marketing site after launch?** Default: the founder, in code; a CMS only
  when a non-developer edits it every week.
