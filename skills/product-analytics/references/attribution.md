# Attribution

Read this when: working out which channels and campaigns produce signups and paying customers,
setting UTM conventions, adding a "how did you hear about us" question, sending conversions
back to ad platforms, explaining a large "direct" bucket, or deciding whether a channel's
reported conversions are real.

## What attribution can and cannot do

Attribution assigns credit for a conversion to touchpoints that were observed. It measures
which channels **captured** demand through a trackable click; it does not measure which
channels **created** the demand, and it does not measure what would have happened without the
spend. Podcasts, word of mouth, communities, private chat links and AI assistants mostly end
as "direct" or "branded search". Treat tracked attribution as one of three imperfect
instruments, alongside self-reported source and incrementality tests, and decide from the
picture where they overlap.

Stage: at Prototype, ask every signup personally. At Launch, first-touch capture plus a
self-report question is enough. Multi-touch models and incrementality tests are for Scale and
for meaningful ad spend.

## First-touch capture and UTM conventions

Conventions (write them in the repository and use a link builder or a short script, never
hand-typed URLs):

| Parameter | Meaning | Rule |
|---|---|---|
| `utm_source` | where the click came from | the platform or publisher: `google`, `linkedin`, `newsletter_name`, `partner_name` |
| `utm_medium` | type of traffic | closed list: `cpc`, `paid_social`, `email`, `social`, `referral`, `affiliate`, `display` |
| `utm_campaign` | the initiative | stable slug: `2026q4_launch`; same value across sources for one campaign |
| `utm_content` | creative or placement | optional: `hero_video_a` |
| `utm_term` | keyword or audience | optional, paid search |

- **Lowercase, snake_case, no spaces.** Values are case-sensitive in most tools, so `LinkedIn`,
  `linkedin` and `linked-in` become three channels. Normalize to lowercase at ingestion as well.
- **Never put UTMs on internal links.** A UTM on a link inside the site or product overwrites
  the real source and starts a new session in some tools.
- Tag every link that is controlled: ads, email, social profiles, partner listings, QR codes,
  app-store and directory entries. Untagged email and app clicks arrive with no referrer and
  count as direct.
- No personal data in UTM values.
- Keep platform click IDs (`gclid`, `fbclid`, `msclkid` and others) when present; they are
  what ad platforms need for conversion upload.

Capture on the first landing, persist until signup, and store on the user and account rows:

```ts
const KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
  "gclid", "gbraid", "wbraid", "fbclid", "msclkid"];

export function captureFirstTouch() {
  if (/(?:^|; )first_touch=/.test(document.cookie)) return; // first touch is written once
  const q = new URLSearchParams(location.search);
  const ft: Record<string, string> = {
    landing_path: location.pathname.slice(0, 200),
    referrer: document.referrer.slice(0, 300), // a cookie over about 4 KB is silently dropped
    ts: new Date().toISOString(),
  };
  for (const k of KEYS) {
    const v = q.get(k);
    if (v) ft[k] = k.startsWith("utm_") ? v.slice(0, 100).toLowerCase() : v.slice(0, 300);
  }
  document.cookie = `first_touch=${encodeURIComponent(JSON.stringify(ft))}` +
    "; Max-Age=7776000; Path=/; Domain=.example.com; SameSite=Lax; Secure";
}
```

Click IDs are case-sensitive tokens: store them verbatim, and lowercase only the UTM values.
Further rules:

- Set the cookie on the registrable domain so it survives the hop from `www` to `app`. A
  marketing site and app on different registrable domains need the values passed in the signup
  link.
- At signup, the server reads the cookie and writes `first_touch_*` columns once. The database
  row is the durable record: cookies expire and analytics tools get replaced. The cookie is
  input anyone can forge: parse it with a schema, cap lengths, use it for attribution only.
- Safari caps script-set cookies at about a week, and at about a day when the visit arrives
  with a decorated URL (query string or click ID) from a domain it classifies as a tracker,
  which is the paid-click case; the 90 days will not hold there. On a server-rendered stack,
  set the same cookie from the server response instead (middleware reading the query string
  and `Referer`): cookies set over HTTP by the site's own server are outside those caps,
  unless the responding host is a third party behind a CNAME or on an IP range unrelated to
  the main site's. Check WebKit's current tracking-prevention rules before relying on either.
- Also record **last touch before signup** (same fields, overwritten on each new external
  landing). First touch says what created awareness; last touch says what closed.
- Derive a `channel` from source, medium and referrer with one function in code (`paid_search`,
  `organic_search`, `paid_social`, `organic_social`, `email`, `referral`, `ai_assistant`,
  `direct`, `partner`), so every report groups the same way.
- Exclude own domains, the payment provider, OAuth providers and email-verification clicks
  from referrers, or signups get attributed to `accounts.google.com` or the checkout host.
- This cookie is non-essential storage. Where consent is required, write it only after
  opt-in (`0x:privacy-compliance`); without consent, attribution falls back to what the
  landing request itself shows, and the self-report question.
- Product suites capture initial referrer and UTMs as person properties automatically; still
  copy them to the database at signup, because that is where revenue is joined.

## Ask "how did you hear about us?"

Self-reported attribution sees what tracking cannot: podcasts, word of mouth, communities,
events, AI assistants, a colleague's recommendation.

- Place it **right after signup**, on the first onboarding screen, as one optional question.
  On the signup form itself it can cost conversions; weeks later nobody remembers.
- Use a **free-text field** at Launch volume, and categorize answers by hand or with a model
  weekly. Free text returns names ("the X podcast", "my coworker", "asked ChatGPT") that a
  dropdown cannot. At Scale switch to a short option list in random order with "Other" plus
  text, since ordered lists inflate the first options.
- Store the raw answer and the assigned category on the user row.
- For sales-assisted deals, ask on the first call and record it in the CRM in the same
  categories.

Reconcile with tracked data in a cross-table: tracked channel in rows, self-reported category
in columns, signups and paying customers in cells.

| Pattern | Reading |
|---|---|
| Tracked `direct` or `organic_search` (brand terms), self-report "podcast", "friend", "community" | the self-reported channel created the demand; search only captured it |
| Tracked `paid_search` on brand keywords, self-report something else | the ad took credit for a visit that would have happened; candidate for an incrementality test |
| Tracked `paid_social`, self-report agrees | credible paid acquisition |
| Self-report "Google" | uninformative; people name the last step. Keep the category but do not act on it |

Use self-report for where demand comes from and tracked data for which specific campaign,
creative and keyword converts. Expect them to disagree; the disagreement is the information.
Self-report has its own bias: response rate differs by segment, and memory favors the most
recent or most memorable touch.

## Connect source to revenue and retention

Signups by channel is the metric that channels are easiest to flatter. Judge channels on what
the signups become:

| Per channel (first touch), by signup cohort | Why |
|---|---|
| Signups, and cost | volume and CAC inputs |
| Activation rate | intent and fit of the traffic |
| Paid conversion and time to pay | a channel with slow conversion looks bad in a short window |
| Revenue per signup at 3, 6, 12 months | value, including expansion |
| Retention or logo churn of its customers | cheap customers who churn are expensive |
| Payback period: acquisition cost ÷ monthly gross margin per customer | what the channel can afford |

Mechanics: the join key is the user or account ID. First-touch fields live on the account row;
revenue comes from the billing system keyed by the same account (store the account ID on the
payment provider's customer and pass it into checkout, for example as the checkout session's
client reference or metadata). Report by **signup cohort** with a fixed observation window so
old and new cohorts are comparable, and include all costs of a channel (tools, content,
people's time), not only media spend. With few customers per channel, show counts and customer
names rather than rates. Unit economics are defined in `0x:pricing-monetization`; channel
strategy in `0x:growth-marketing`.

## Attribution models

| Model | Credit goes to | Good for | Blind spot |
|---|---|---|---|
| First touch | first observed touch | which channels create awareness; default for a small team | ignores what closed; "first" is first on this device within cookie life |
| Last touch | last touch before conversion | which campaigns and pages close | overcredits brand search, retargeting, email, direct |
| Position-based, linear, time-decay | several touches by a fixed rule | long B2B journeys with many tracked touches | the weights are arbitrary; needs complete journeys that cookie loss prevents |
| Data-driven (platform models) | modeled by the vendor | optimizing inside one ad platform | opaque; each platform credits itself, and the platforms' totals sum to more than actual conversions |
| Self-reported | what the customer says | untracked channels | recall bias |
| Incrementality test | the causal difference | deciding budget | costly; needs volume |

Rules: default to first touch and last touch side by side, plus self-report. Do not build
multi-touch attribution before Scale: it needs volume, an identity graph and maintenance, and
its output is no more causal than last touch. No rule-based or modeled attribution answers
"what happens if this budget is cut"; only an experiment does. Ad platforms' own dashboards
use their own attribution windows and often count view-through conversions; compare platforms
using the product's own numbers, and record the windows used.

## Server-side conversions to ad platforms

Ad platforms optimize toward the conversions they are told about. Browser pixels lose events
to blockers, browser privacy limits and consent refusals, and can only see what happens in the
browser. Sending conversions from the server (Meta's Conversions API, Google's conversion
upload, and equivalents) recovers part of that and lets the platform optimize for the event
that matters. These APIs are renamed and replaced often: Google now directs offline and
enhanced-conversion uploads to its Data Manager API and in 2026 closed the older Google Ads
API upload path to new adopters, so many examples found online target an API a new project
cannot use. Write the integration from the platform's current documentation, not from memory.

- **Send the business event, not the pixel event.** Report `subscription_started` (with
  value) or a qualified signup, from the same server code that records it. Optimizing ads
  toward raw signups buys cheap signups.
- If the valuable event is rare, platforms cannot learn from it. Use the deepest event that
  still occurs often enough for the platform's learning requirement (check the platform's
  current guidance); typically activation rather than payment for early-stage products.
- **Match keys**: the click ID captured at landing and stored on the user row, and hashed
  identifiers in the format the platform specifies (normalized, lowercased email hashed with
  SHA-256).
- **Deduplicate** when both pixel and server send the same conversion: send the same event
  name and the same event ID on both (Meta matches on that pair within a limited window, 48
  hours at the time of writing, so a late retry or backfill counts again). Without it each
  conversion counts twice and the platform optimizes on inflated numbers.
- **Consent applies to the server path exactly as to the pixel.** Sending hashed emails to an
  ad platform is sharing personal data for advertising. Store the user's advertising consent
  at the time of the click or signup and send only for users who granted it; pass the
  platform's consent signals where it requires them (Google requires them for users in the
  EEA and any other region its consent policy covers; check the current list). Under several
  US state privacy laws this sharing can count as "sale" or "sharing" and require an opt-out,
  where the law applies to the business at all; thresholds and definitions differ by state.
  The rules are in `0x:privacy-compliance`.
- Send within the platform's upload window and with the original conversion time. Check the
  platform's event-quality or match-rate diagnostic after launch.
- Send from a job with retries, keyed on the conversion's ID so a retry cannot double-count.

## Cookie loss, dark traffic and AI referrals

Reasons tracked attribution undercounts or mislabels, and what to do about each:

| Cause | Effect | Mitigation |
|---|---|---|
| Browser limits on script-set cookies and storage (Safari caps their lifetime to days; other browsers restrict in private modes) | first touch forgotten when signup comes later | write first touch server-side at the earliest identified moment; keep the gap short (email capture, signup early) |
| Cross-device journeys | phone click, desktop signup: desktop looks direct | self-report; logged-in identity; accept the loss |
| Consent refused, ad blockers | no client record at all | server-side landing log of referrer and query string within consent limits; self-report |
| Link shared in private chat, email clients, mobile apps | no referrer: "direct" | UTMs on everything shared deliberately; share buttons that add them |
| Referrer stripped by policy or redirect chains | source lost | avoid redirect hops that drop the query string; test each ad URL end to end |
| Click IDs or UTMs stripped by browsers or extensions | paid click looks organic or direct | rely on more than one key (UTM plus click ID plus landing page built per campaign) |
| AI assistants and AI search | see below | referrer classification plus self-report |

AI-referral traffic: assistants send visits in three ways. Some clicks carry a referrer from
the assistant's domain or a `utm_source` the assistant appends (ChatGPT has used
`utm_source=chatgpt.com`); classify those domains and
values into an `ai_assistant` channel in the channel function, and maintain the list, since
the products and domains change. Many clicks, especially from native apps, carry no referrer
and land as direct. And the largest effect leaves no click at all: the user reads a
recommendation, then types the brand into a browser or search engine later. So measure AI
influence with the self-report question (add the category), with direct landings on deep
pages that nobody types by hand, and with the trend in branded search, and do not expect
click attribution to size it. Clicks from AI answers inside a search engine's results page
arrive as ordinary organic search, or with no referrer, and click data cannot separate them.
Assistants have added and dropped these parameters without notice: treat a sudden change in
this channel as an instrument change first.

Read the `direct` bucket as "unknown", never as "typed the URL". A rising share of direct
alongside growing signups usually means untracked channels are working.

## Incrementality

Incrementality asks how many conversions would not have happened without the channel. It is
the only measurement that justifies a budget, and the only way to expose channels that harvest
existing demand (brand search, retargeting, coupon and affiliate sites).

| Method | How | Fits |
|---|---|---|
| On/off (switchback) | pause the channel or campaign for 2–4 weeks, compare total signups and paying customers to the expected trend, then turn it back on and confirm recovery | small budgets; crude, confounded by seasonality, but often decisive for brand search and retargeting |
| Geo holdout | choose matched regions; run the channel in some, withhold it in others; compare total conversions per region against the pre-period relationship | Scale; needs many conversions per region and geo-targetable media |
| Platform lift study | the ad platform randomizes users into exposed and holdout groups | when spend meets the platform's minimum; measures within that platform only |
| Audience holdout | withhold email or retargeting from a random 10% | lifecycle and retargeting programs (`references/experiments.md`) |

Rules: measure **total** business outcomes from the product's own database, not the channel's
attributed conversions, since the point is to test the attribution. Define regions, duration
and metric before starting; match regions on pre-period trend, not on size alone; run at least
two full weeks plus the typical conversion lag. A result of "no detectable drop" when the
channel is off is a finding worth acting on. At Launch-level spend, the practical version is:
pause brand-keyword ads for two weeks and see whether organic and direct absorb the signups.
Media-mix modeling needs a long history of varied spend and is not a small-team tool.

## Ask the user

- **Which channels are active, and how much is spent on each per month?** Decides how much
  attribution machinery is worth building. Default: first touch, last touch and a self-report
  question; nothing more below meaningful ad spend.
- **Is advertising to EU or other consent-regulated users in scope?** Determines consent
  gating for the first-touch cookie and for conversion uploads. Default: yes, gate on consent.
- **What counts as a conversion worth paying for: signup, activated account, or paying
  customer?** This is the event sent to ad platforms and used to judge channels. Default:
  activated account for optimization, paying customer for evaluation.
- **How long is the typical gap from first visit to payment?** Sets the evaluation window and
  explains cookie loss. Default: evaluate cohorts at 30 and 90 days.
- **Is pausing a channel for two to four weeks acceptable to learn whether it works?** The
  cheapest incrementality test costs short-term signups. Default: yes for brand search and
  retargeting, no for the main acquisition channel without a geo split.
