# Consent, cookies, tracking and marketing permission

Read this when: adding analytics, ad pixels, session replay, embeds or chat widgets; building or
auditing a cookie banner; wiring consent into tags; collecting marketing-email permission; or
planning cold email, SMS or calls.

## Two separate rules, often confused

1. **Device access (EU and UK e-privacy rules).** Storing or reading anything on a user's
   device needs prior consent unless it is strictly necessary for a service the user explicitly
   asked for. It covers cookies, `localStorage`, IndexedDB, pixels, device fingerprinting and
   SDK identifiers, and it applies whether or not the data is personal.
2. **Use of personal data (GDPR, US state laws).** What happens with the data afterwards needs
   its own lawful basis in the EU, or an opt-out for sale and sharing in the US.

A tool can pass one and fail the other. "We only use first-party cookies" and "the data is
anonymized" do not answer rule 1.

| Region | Non-essential trackers | What that means in code |
|---|---|---|
| EU, EEA | Opt-in before anything loads | Banner, blocked by default |
| UK | Opt-in, except analytics used only by the site operator for aggregate statistics, which since 5 February 2026 may run with clear notice and an easy opt-out | Banner for ads, pixels and third-party tracking; first-party statistics may run with a working opt-out |
| Switzerland | Clear notice and an easy way to refuse is generally enough; consent for high-risk profiling | Most sites reuse the EU banner for simplicity |
| US | Opt-out of sale, sharing and targeted ads; honor Global Privacy Control | "Your Privacy Choices" link; no banner required, though wiretap-style lawsuits over pixels and session replay make disclosure prudent |
| Elsewhere (Brazil, Canada, others) | Mixed; mostly consent-leaning | Treat like the EU unless advised otherwise |

Default: geo-target the opt-in banner to EU, EEA, UK and Switzerland; apply GPC and an opt-out
link everywhere. If geo-detection is not available, show the opt-in banner to everyone.

## What counts as strictly necessary

| No consent needed | Consent needed |
|---|---|
| Session and auth cookies, CSRF tokens | Analytics that set identifiers (GA4, default PostHog, Mixpanel) |
| Cart, checkout state, language or theme the user set | Ad and conversion pixels (Meta, Google Ads, LinkedIn, TikTok) |
| Load balancing, bot and fraud defense needed to deliver the service | Session replay and heatmaps |
| The cookie storing the consent choice itself | A/B testing tools that set identifiers, in most countries |
| A chat widget or video loaded after the user clicks to open it | Chat widgets, video and map embeds that load and set cookies on page load |

"Necessary" is judged from the user's side, not the business's: revenue attribution is not
necessary to deliver a page. A few regulators exempt narrowly configured audience measurement
(first-party, no cross-site tracking, aggregate use only), as France's regulator does; the UK
exemption above is similar but requires notice and an opt-out and never covers advertising. EU
proposals (the 2025 Digital Omnibus) to move cookie rules into the GDPR and widen exemptions
were still being negotiated in late 2026. Treat all of these as country-specific and confirm
before relying on them.

## Avoid needing a banner

The best banner is none. With only strictly necessary storage there is nothing to ask, and no
banner is required; a privacy policy line is enough.

| Need | Consent-free route (verify the vendor's current mode) |
|---|---|
| Traffic and page analytics | Cookieless tools (Plausible, Fathom and similar) or server-side log analytics: no device storage, no persistent identifier |
| Product analytics for logged-in users | Server-side events keyed by user ID, covered by the privacy policy under legitimate interests with an opt-out; or the analytics SDK in a memory-only, cookieless mode |
| Conversion measurement | Aggregate server-side counts; UTM parameters read from the landing URL and stored with the signup |
| Fonts, icons, scripts | Self-host; third-party font and CDN requests send the visitor's IP to another company |
| Video | Click-to-load facade, privacy-enhanced embed domain |

The moment an ad pixel, GA4 or session replay is added, a real consent mechanism is required for
EU and UK visitors. Decide whether the data is worth the banner and the consent rate: a rule of
thumb is that a fair banner loses a large share of EU visitors from the analytics.

## Banner design that survives review

- "Reject all" on the first layer, same size, color weight and click count as "Accept all". A
  "Manage options" link as the only alternative to "Accept" is the most enforced-against pattern.
- No pre-ticked boxes or toggles defaulted on. Scrolling, continuing to browse or closing the
  banner is not consent; treat a dismissed banner as rejection.
- Granular by purpose (analytics, marketing, functional), each with a one-line plain description
  and the vendors named or linked.
- No cookie wall: do not block content until the user accepts. "Pay or consent" models need
  legal advice.
- Withdrawal as easy as giving: a persistent "Cookie settings" link in the footer that reopens
  the same dialog. On withdrawal, stop the tags and delete their cookies.
- Do not re-ask on every visit after a rejection. Remember a refusal as long as an acceptance;
  re-prompting after six months (the French regulator's suggestion) to twelve months is common
  practice.
- The banner must be keyboard-operable and screen-reader-labeled, must not trap focus badly on
  mobile, and must not shift layout (reserve space or overlay).
- No guilt wording ("No, I don't care about my experience"), no hidden reject in gray text.

## Actually blocking: the implementation rule

A banner that records a choice while the tags have already fired is the most common failure.
Nothing non-essential may load, set storage or send a request before an opt-in.

- Gate loading, not just behavior. Do not put vendor snippets in the document head; inject them
  from one consent module after the choice is read.
- Keep a single source of truth: `consent = { analytics, marketing, functional, version, ts }`,
  readable on the server (first-party cookie) so server-rendered pages do not emit tags either.
- In a tag manager, every tag needs a consent condition; the default container state is denied.
- Server-side tagging and conversion APIs are not a way around consent: forwarding an EU
  visitor's events to an ad platform server-to-server needs the same opt-in.

Google tags (required to keep EEA ad measurement and audiences working) read Consent Mode
signals. Set defaults before any Google tag loads, then update on choice:

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('consent', 'default', {
    ad_storage: 'denied', analytics_storage: 'denied',
    ad_user_data: 'denied', ad_personalization: 'denied',
    wait_for_update: 500
  });
</script>
```

```js
gtag('consent', 'update', { analytics_storage: 'granted' }); // only the purposes accepted
```

"Basic" mode does not load Google tags until consent; "advanced" mode loads them and sends
cookieless pings while denied. Default to basic for EU traffic: whether the pings need consent
is disputed, and basic is the defensible position.

For a PostHog-style SDK, start opted out and without device storage, and enable both on
consent. Opting out of capture alone can still leave the SDK's identifier cookie, so set
persistence too:

```ts
const ok = consent.analytics === true; // read from the consent module on every page load
posthog.init(key, {
  api_host: host,
  persistence: ok ? "localStorage+cookie" : "memory", // no cookie or storage before consent
  opt_out_capturing_by_default: !ok,                   // no events before consent
});
// after the user accepts analytics
posthog.set_config({ persistence: "localStorage+cookie" });
posthog.opt_in_capturing();
// on withdrawal: stop capture, then delete the SDK's ph_* cookies and storage keys
posthog.opt_out_capturing();
```

SDK option names change between versions; confirm in devtools that nothing is written before
acceptance.

Build or buy: a hand-built banner is fine for a handful of first-party-controlled tags. Use a
consent management platform when running programmatic ads (the IAB TCF string and Google's
certified-CMP requirement for publishers apply), when many tags are managed by marketers, or
when per-country rules must be maintained by someone else.

## Recording and honoring consent

Consent must be provable: the burden is on the site.

| Field | Why |
|---|---|
| Subject: user ID if logged in, else a random consent ID in a first-party cookie | Links the record to a choice without creating a tracking identifier |
| Timestamp, region applied | Shows which rules were used |
| Banner text version and vendor-list version | Shows what was agreed to |
| Choice per purpose, and the action (accept all, reject all, custom, GPC) | The content of the consent |

Rules: store choices server-side for logged-in users and apply them at login on a new device,
taking the more restrictive of the device and account choice until the user decides. Bump the
version and re-ask when a purpose or a materially new vendor is added; never re-ask merely to
get a different answer. Consent logs are personal data: keep them for the consent lifetime plus
the limitation period, not forever. A GPC signal is recorded as an opt-out and overrides an
earlier acceptance of sale or sharing.

## Auditing tags and pixels

Run this before launch and after any marketing change.

1. Fresh browser profile, EU location (or the geo override). Load the page and touch nothing.
   In devtools, the Network tab filtered to third-party domains must show only essential
   requests; Application storage must show only essential cookies and keys.
2. Click "Reject all", navigate three pages, repeat the check.
3. Click "Accept" for one purpose only; confirm only that purpose's tags load.
4. Withdraw; confirm tags stop and their cookies are gone.
5. Repeat with GPC enabled from a US location.

Automate steps 1 and 2 as a Playwright test that fails on any request to a non-allowlisted host
before consent.

Leaks to look for in the request payloads, even after consent:

| Leak | Fix |
|---|---|
| Emails, names, tokens or search terms in URLs sent as page location or referrer | Keep personal data out of paths and query strings; strip before `page_view`; `Referrer-Policy: strict-origin-when-cross-origin` |
| Pixels with "automatic advanced matching" or autocapture reading form fields | Turn the feature off; never run ad pixels on authenticated, checkout or account pages |
| Session replay capturing inputs, messages or on-screen personal data | Mask all inputs and text by default; allowlist what is recorded |
| Health, finance or other sensitive context revealed by the page URL to an ad network | No ad or social tags on such pages at all; this has drawn regulator action and class suits in the US |
| Tags injected by other tags (piggybacking) | Content Security Policy allowlist; see `0x:web-security` |
| Third-party fonts, maps, captcha, video loaded on every page | Self-host or click-to-load |

## Marketing email permission

| Situation | EU and UK | US (CAN-SPAM) | Canada (CASL) |
|---|---|---|---|
| Newsletter signup by a non-customer | Opt-in consent | Allowed; opt-out | Express consent |
| Existing customer, own similar products | "Soft opt-in": allowed if the address came from a sale, an opt-out was offered at collection and in every message | Allowed | Implied consent, time-limited after the purchase |
| Checkbox at signup | Unticked, separate from terms acceptance, not a condition of the account | Not required | Unticked |
| Every message | Unsubscribe link, sender identity | Unsubscribe honored within 10 business days, physical postal address, truthful headers and subject | Unsubscribe, sender identity and contact details |

- Use double opt-in (confirmation link) for any list built from a public form: it is the proof
  of consent regulators expect in some countries, and it keeps typos and bots off the list.
- Keep consent evidence per subscriber: timestamp, source form, the wording shown, IP.
- One-click unsubscribe: send `List-Unsubscribe` and `List-Unsubscribe-Post:
  List-Unsubscribe=One-Click` headers on marketing mail; large mailbox providers require it of
  bulk senders and expect removal within two days. No login, no survey before the opt-out works.
- Suppression list: an unsubscribed or complained address goes on a permanent do-not-send list
  that every send checks, including after a re-import or a new tool. The suppression entry
  survives an account deletion request, because it is what honors the objection.
- Transactional mail (receipts, password resets, security alerts) needs no marketing consent
  and must not carry promotion beyond a footer line; "we miss you" and feature announcements
  are marketing. Separate streams in the provider; see `0x:email-notifications`.
- Purchased lists have no valid consent anywhere that requires it and wreck sender reputation.

## Cold outreach

Check the recipient's country, not the sender's.

| Country | Cold B2B email | Trap |
|---|---|---|
| US | Allowed under CAN-SPAM with opt-out, address and honest headers | State laws and platform terms on scraped addresses |
| UK | Allowed to corporate bodies with opt-out; sole traders and partnerships are treated as individuals and need consent | A `name@company` address is still personal data: a legitimate-interests note and a privacy notice are needed |
| Germany | Prior consent required even B2B, in practice | Competitors and associations send paid cease-and-desist letters |
| France | Allowed if relevant to the recipient's professional role, with opt-out and source disclosure | Generic relevance does not count |
| Other EU states | Varies between the UK and German positions | Check each before a campaign |
| Canada | Consent, with narrow exceptions such as a conspicuously published business address and a role-relevant message | High statutory penalties |
| Australia | Consent, which may be inferred from conspicuous publication in a relevant role | Functional unsubscribe required |

Where it is allowed: message the role, keep it relevant to their job, identify the sender and
the source of the address in the first message, offer a one-step opt-out, and suppress forever.
Send from a separate domain so complaints do not hurt product mail.

Texts and calls are stricter than email everywhere. In the US, marketing texts and autodialed
calls need prior express written consent, with statutory damages per message and an active
plaintiffs' bar; get the consent wording reviewed before the first campaign.

## Ask the user

- **Are ad platforms or retargeting in the plan, or is analytics enough?** Ads force a consent
  banner in the EU and an opt-out link in the US. Default: cookieless analytics only, no banner.
- **Which countries will see the site?** Decides geo-targeting of the banner. Default: opt-in
  for EU, EEA, UK and Switzerland; opt-out plus GPC elsewhere.
- **Will existing customers get product marketing email?** Decides whether soft opt-in wording
  is needed at signup. Default: yes, with an unticked marketing checkbox for EU signups.
- **Is cold outreach planned, and to which countries?** Some require prior consent. Default:
  cold email only to US and UK corporate recipients until others are checked.
- **Is session replay wanted?** It is the highest-risk tag for leakage and US wiretap claims.
  Default: off; if on, consent-gated, masked by default and excluded from authenticated pages
  with sensitive data.
