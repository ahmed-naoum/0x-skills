# Community, partnerships and market expansion

Read this when: growing through existing communities, starting the product's own community,
reducing dependence on one channel or platform, shipping integrations and marketplace listings,
co-marketing with other products, setting up affiliate or reseller programs, or entering a new
country.

## Member first in existing communities

Communities are where a solo founder reaches customers without a budget, and where promotion
without standing is removed fastest.

- **Find where the customer already talks**: subreddits, Slack and Discord groups, forums,
  Stack Overflow tags, GitHub issues of adjacent tools, LinkedIn groups, professional
  associations, local meetups. List each with its rules on promotion.
- **Contribute for weeks before mentioning the product**: answer questions fully, share what was
  learned, give the right answer even when it is a competitor's product. A common rule of thumb
  keeps self-promotion to about a tenth of what an account posts.
- **The profile carries the link.** Helpful answers send curious people to it without any
  promotion in the post.
- **Mention the product only when it directly answers the question**, with disclosure: "I build
  X, which does this; Y and Z are alternatives." Disclosure turns a promotion into an honest
  recommendation.
- **Never astroturf**: no fake accounts praising the product, no undisclosed paid posts, no
  coordinated upvotes. Communities detect it, ban the account and remember the name; undisclosed
  paid endorsements also break advertising law in the US (FTC), the EU (Unfair Commercial
  Practices Directive) and the UK (DMCC Act 2024).
- **Time-box it**: a fixed daily slot (for example 30 minutes) across two or three communities,
  with a simple log of threads and outcomes.

## Avoid depending on one channel or platform

A business whose customers arrive through one platform lives at that platform's mercy: an
algorithm change, a policy change, an API price rise, a marketplace delisting or a suspended
account can cut acquisition overnight.

| Risk | Mitigation |
|---|---|
| One channel brings most signups (rule of thumb: more than half) | Start testing a second channel before the first plateaus (`paid-acquisition.md`) |
| The audience lives on one social network | Move followers to the email list, which the company owns |
| A marketplace is the main source of customers | Know its policies in detail; offer direct signup and billing where its rules allow; keep customer contact data where the terms permit |
| One integration partner or API underpins the product | Follow the partner's roadmap and terms; avoid features that compete with theirs |
| Ad account suspension | Follow ad policies strictly; never let one ad account carry all acquisition |
| Search traffic | Spread across content types and channels; avoid tactics that risk penalties (`seo-aeo-geo-ultimate`) |

Review the share of signups by source every month; concentration rises quietly.

## Building and moderating an own community

Start one when users already help each other or ask for a place to meet, usually at Launch with
a few hundred engaged users. Earlier, an empty room signals an unused product.

| Platform | Strengths | Weaknesses |
|---|---|---|
| Discord | Real-time, free, familiar to developers and consumers | Not indexed by search; answers sink in chat; noisy |
| Slack | Familiar to B2B professionals | The free plan shows only recent history (90 days as of 2026) and deletes content older than a year; members juggle many workspaces |
| Forum (Discourse or similar) | Searchable and indexable; answers accumulate | Slower; needs seeding to feel alive |
| GitHub Discussions | Natural for open-source and developer tools | Developers only |
| Hosted community platform | Courses, events and paid memberships in one place | Cost and lock-in; check data export before committing |

Default: a forum or GitHub Discussions when answers should accumulate and be found by search;
Discord or Slack when real-time conversation is the point.

- **Seeding**: invite 20 to 50 hand-picked users first. The founder posts and answers daily;
  recurring rituals (weekly show-and-tell, monthly office hours, a changelog thread) give people
  a reason to come back.
- **Recognize contributors**: roles, thanks in the changelog, early access. Members who answer
  other members are what makes a community worth joining.
- **Moderation from day one**: a short published code of conduct; an enforcement ladder (warn,
  time out, ban) applied consistently; verification or a waiting period before new members can
  post links; automated spam filtering; a private log of moderation actions. Recruit moderators
  from trusted members as it grows.
- **Legal**: hosting user content on the company's own forum brings duties that a Discord or
  Slack server mostly leaves with the platform. EU: the Digital Services Act requires hosting
  services to run notice-and-action for illegal content and give reasons for removals (lighter
  duties for micro and small companies). UK: the Online Safety Act covers user-to-user services
  with UK users whatever their size, with a written illegal-content risk assessment kept up to
  date and reporting and complaints routes; Ofcom enforces it. US: Section 230 shields hosts
  from most liability for users' posts, but the copyright safe harbor requires a DMCA agent
  registered with the Copyright Office. Community terms: `0x:privacy-compliance`.
- **Measure**: share of questions answered by members rather than staff, weekly active members,
  and retention of community members against other customers.
- **Cost**: founder time. If support moves into the community, set response expectations so
  paying customers are not left waiting in a public channel (`0x:sales-support`).

## Integrations and marketplace listings

Integrations put the product where customers already work, and marketplace listings bring buyers
who are searching inside that platform.

- **Choose by the customers' stack**: ask which tools they use every day, and build where the
  integration makes the core job easier, not where the partner's logo looks impressive.
- **Marketplaces with buyer traffic**: app stores of e-commerce platforms, team chat, project
  management, CRM and design tools; workflow-automation directories; browser and code-editor
  extension stores; cloud marketplaces, which also ease enterprise procurement.
- **Know the rules before building**: review and security assessments, permitted OAuth scopes,
  privacy and data-handling requirements, review times, and whether the marketplace requires
  billing through its own system and takes a revenue share. These differ widely and change; read
  the current partner terms.
- **Listing**: a name and short description containing the job, screenshots of the outcome, a
  setup video, and early reviews from happy users asked personally. Ratings and review counts
  drive ranking inside most marketplaces.
- **Automation platforms first**: a connector for a workflow-automation platform covers the long
  tail of tools before native integrations are built one by one.
- **Treat each integration as a launch** (`launches.md`): an integration page, a post, an email
  to users of that tool, and a request that the partner feature it in their own channels.
- **Engineering**: OAuth, webhooks and retries (`0x:backend-architecture`); the public API that
  partners build on (`0x:api-design`).

## Co-marketing with complementary products

- **Partner selection**: the same customer, no competing product, an audience of comparable size
  or a clear reason the asymmetry works for both. A working integration between the two products
  is the strongest basis.
- **Formats**: a joint webinar or workshop, an integration announced by both, guest posts or
  newsletter swaps, perks for each other's customers, a joint case study, templates in each
  other's galleries.
- **A one-page agreement**: deliverables, dates, what each side promotes and where (list sizes,
  number of posts), how leads are handled, which metrics are shared.
- **Leads**: share registrant data only when the registration form names both companies and the
  purpose; otherwise each side keeps its own (`0x:privacy-compliance`).
- **Give first**: offering to promote the partner first is the fastest way to a yes.
- **Measure** with partner-specific UTM parameters and offer codes.

## Affiliate and reseller programs

| Program | Who | Paid for | Fits |
|---|---|---|---|
| Customer referral | Existing users | Referred customers, usually in credit | Products with word of mouth (`referral-loops.md`) |
| Affiliate | Creators, bloggers, consultants | Referred customers, in cash | Products whose buyers follow reviewers and educators |
| Agency or solution partner | Agencies that implement the product for clients | Commission or discount, plus leads | Products that need setup or services |
| Reseller | Firms that sell to and bill the customer themselves | A discount on list price | Markets where buyers need a local vendor, language or procurement route |

Affiliate setup:

- **Tracking**: an affiliate tool integrated with the billing provider, attributing through a
  link with a cookie window (commonly 30 to 90 days) and a coupon code as fallback. Store the
  affiliate on the account at signup.
- **Commission**: a percentage of net revenue (after refunds, discounts and taxes), recurring
  for a limited period; a common rule of thumb in SaaS is 20 to 30% for the first year. Keep it
  within the CAC ceiling (`paid-acquisition.md`).
- **Payout**: monthly, only after the refund window has passed, above a minimum threshold.
  Collect tax forms and payout details through the affiliate tool; paying individuals can
  create tax reporting obligations that differ by country (`0x:startup-finance`).
- **Terms that prevent abuse**: no bidding on the product's brand name in search ads, no
  coupon-site listings, no spam, no cookie stuffing, no self-purchases; mandatory disclosure of
  the affiliate relationship (required by the FTC in the US, the CMA and ASA in the UK and
  consumer law in the EU); the right to withhold commission for violations.
- **Fraud checks**: purchases made with the affiliate's own payment details, refund and
  chargeback rates per affiliate, traffic sources that do not match the affiliate's audience.
- **Activation**: most affiliates never send anyone. Recruit a few who already write about the
  category, give them assets and early access, and talk to them monthly.

Resellers: decide who bills, who supports, who owns the customer relationship and the data, and
what happens when the relationship ends. For a small company an agency partner program is
usually more realistic; reseller deals fit specific markets or procurement routes. Contracts:
`0x:sales-support`; payouts and balances owed to partners: `0x:payments-billing`.

## Localizing for a new market

Choose the market from evidence: visitors and signups by country, conversion by country, inbound
requests, competitors that serve it poorly, payment methods customers ask for. Then localize in
this order, cheapest and most decisive first:

| Step | What | Why in this position |
|---|---|---|
| 1 | Local payment methods: SEPA Direct Debit (euro payments across the SEPA area), iDEAL (Netherlands, being replaced by Wero through 2026 and 2027), Bancontact (Belgium), BLIK (Poland), Pix (Brazil), UPI (India), convenience-store payment (Japan), others by country | Buyers abandon checkout when their usual method is missing; payment providers and merchants of record enable many by configuration. Many are one-off methods: for subscriptions, check that the provider supports recurring charges with each one (some turn the first payment into a SEPA Direct Debit mandate) (`0x:payments-billing`) |
| 2 | Prices in local currency at rounded local price points, tax-inclusive for consumers where the law requires it | A converted price like 17.63 looks foreign. Consumer prices must include VAT or GST in the EU (Price Indication Directive), the UK and Australia; US prices are normally shown before sales tax; prices offered only to businesses may exclude VAT if they say so |
| 3 | Purchasing-power adjustment where the market is price-sensitive | Price levels: `0x:pricing-monetization`. Tie regional prices to billing and card country to limit VPN abuse |
| 4 | Tax, invoicing and consumer law: VAT or GST registration or a merchant of record, invoice rules, consumer withdrawal and cancellation rights | Selling before this is settled creates liabilities. EU consumers buying online have a 14-day right of withdrawal: for digital content it ends once delivery starts with their express consent and acknowledgment; for a service such as SaaS they pay pro rata if they asked to start at once; since June 19, 2026 an online withdrawal function is required wherever the right applies (Directive 2023/2673, as transposed nationally). Germany also requires a cancellation button for online subscriptions (`0x:payments-billing`, `0x:privacy-compliance`) |
| 5 | Landing pages in the language, with local proof such as a customer from that country | Machine translation edited by a native speaker; never unreviewed machine output for marketing copy |
| 6 | Product interface in the language | Engineering: `0x:frontend-foundations` |
| 7 | Support in the language and time zone; local channels, communities and partners | The market's own platforms and communities may differ from the home market's |

- Do steps 1 to 3 first and measure conversion by country before translating everything; many
  markets convert well in English once payment and price fit.
- Data residency and procurement questions differ by market; answer them before selling to
  regulated buyers there (`0x:privacy-compliance`).
- International search setup (hreflang, local domains): `seo-aeo-geo-ultimate`.
- Enter the market as a launch of its own (`launches.md`), with local communities and
  newsletters, timed around local holidays.

## Ask the user

- **Which communities does the founder already belong to, and under which name?** Default: start
  there, contributing for weeks before mentioning the product.
- **Is there time to run a community every day?** Default: no own community until users ask for
  one and the founder can be present daily for months.
- **Which tools do customers use every day?** They pick the first integrations. Default: a
  workflow-automation connector first, then the most-requested native integration.
- **What commission or margin can partners receive?** Default: affiliate commission of at most a
  quarter of first-year net revenue, within the CAC ceiling, paid after the refund window.
- **Which country is next, and why?** Default: the one already sending the most signups, with
  payment methods and pricing before translation.
