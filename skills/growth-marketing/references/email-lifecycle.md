# Email list and lifecycle messaging

Read this when: adding email capture or a newsletter, writing welcome, activation, trial,
re-engagement or win-back messages, adding in-app nudges, segmenting users, or judging whether
lifecycle messages work.

## Three kinds of messages, kept apart

| Kind | Examples | Permission | Sent by |
|---|---|---|---|
| Transactional | Receipts, password resets, security alerts, invitations | Needed to deliver the service; carries no marketing | The transactional provider (`0x:email-notifications`) |
| Lifecycle | Welcome, activation nudges, trial ending, milestones, re-engagement | How-to and account mail to the user is usually treated as service mail; anything promoting an upgrade, offer or other product is marketing in the EU and UK and may be "commercial" under US CAN-SPAM. Give every lifecycle email an unsubscribe and honor it. If a trial converts to a paid charge automatically, the pre-charge notice (price, date, how to cancel) is required billing mail sent through the transactional stream regardless of unsubscribe (`0x:email-notifications`, `0x:privacy-compliance`) | A product-email tool fed by product events |
| Marketing | Newsletter, announcements, offers | Marketing consent or another lawful basis per country; unsubscribe in every message | The same tool or a newsletter tool |

Keep them apart so newsletter complaints never damage the reputation that delivers password
resets, and so a newsletter unsubscribe never silences security alerts. Separate sending
streams or subdomains, SPF, DKIM, DMARC and one-click unsubscribe headers:
`0x:email-notifications`.

By stage: at Prototype, plain emails sent by the founder by hand are enough. At Launch: capture
forms, the welcome and activation sequence, trial messages. At Scale: segments, in-app
messages, holdout measurement, a sunset policy.

Tooling: a tool that receives product events through an API and triggers messages on them (the
Loops or Customer.io class) for lifecycle; at small scale it can send the newsletter too. Tools
that only know a list and a schedule cannot react to behavior, and time-based drips are where
lifecycle email goes wrong.

## Capture with a reason at high-intent moments

People subscribe to a specific promise, not to "our newsletter".

| Moment | Offer | Form |
|---|---|---|
| Before launch | Early access, saying what and roughly when | Email plus one qualifying question |
| End of a useful article | The next piece on the topic, or a related template | One field, inline |
| After using a free tool | Save or email the result; monitor it over time | Email to receive the output |
| Pricing page, not ready to buy | A comparison guide, a case study | Low-key inline form |
| Docs and changelog | Updates for this tool or API | One field |
| Webinar or event | The registration itself | Name, email, one question |

- Say what they get and how often: "One email every two weeks about [topic]."
- Capture is consent capture: store the source, timestamp, the wording shown and the IP for
  every subscriber, so consent can be proven later.
- **Permission rules differ by jurisdiction** and follow where the recipient is, not where the
  company is. Never pre-tick a marketing box. Summary below; detail and current law:
  `0x:privacy-compliance`.

| Market | Marketing email | Marketing SMS |
|---|---|---|
| EU (ePrivacy Directive, national laws) | Prior consent for individuals. "Soft opt-in" exception: existing customers, about the company's own similar products, with an opt-out offered at collection and in every message. Email to business addresses varies by country: Germany requires consent; France allows opt-out email relevant to the recipient's job | Same as email |
| UK (PECR) | Consent or soft opt-in for individuals, sole traders and most partnerships; staff at companies (corporate subscribers) may be emailed without consent if the sender is identified and an opt-out offered | Same as email |
| US (CAN-SPAM; TCPA for texts) | Opt-out model, B2C and B2B alike: accurate sender and subject, identified as an ad, a valid postal address, a working unsubscribe honored within 10 business days | Prior express written consent for marketing texts, naming the sender and not a condition of purchase; statutory damages of $500 per message, up to triple if willful; some states add quiet hours and more; carriers require sender registration (10DLC or toll-free verification) |
| Canada (CASL) | Express or implied consent, B2B included; implied consent lasts two years from a purchase and six months from an inquiry; identification and an unsubscribe in every message | Same as email |
| Australia (Spam Act 2003) | Express or inferred consent, identification and a working unsubscribe | Same as email |

- **Double opt-in** (confirm by clicking a link) costs some signups and buys a cleaner list plus
  proof of consent. German courts put the burden of proving consent on the sender, which is
  why it is standard there; it is a sound default for all EU audiences.
- Use inline forms before pop-ups. Full-screen interstitials annoy visitors, and Google's
  Search guidance discourages intrusive interstitials, especially on mobile.

## Welcome and activation sequence, triggered by behavior

Define the activation event first: the action that predicts retention (`0x:product-analytics`).
Each message exists to move one user one step toward it and stops the moment they take it. A
time-based drip that keeps teaching a step the user already completed is the most common
lifecycle failure.

| Message | Trigger | Content | Exit when |
|---|---|---|---|
| Welcome | Signup, immediately | One action: the shortest path to first value, deep-linked; from a named person | Single message |
| Nudge 1 | Not activated a day after signup | The most common blocker (from data) and how to get past it | Activation event |
| Nudge 2 | Not activated after about three days | Proof: how a customer like them does it, or a ready template | Activation event |
| Founder check-in | Not activated after about a week | Plain text: "What were you hoping to do? Reply and I'll help." | Activation or a reply |
| Activated | Activation event | Brief congratulations; the next step toward a habit (second key action, invite a teammate, connect an integration) | Next milestone |
| Trial ending | A few days before the trial ends | What they did, what they would lose, how to keep it. An optional nudge, separate from the required pre-charge notice of a card-on-file trial (see above) | Converted |
| Trial ended | Trial over without conversion | An extension or downgrade path, and a question why | Converted or replied |

- **One email, one action**, with a button deep-linked to the exact screen.
- **Branch on the onboarding answer** (role or use case) where the path to value differs.
- **Send from a person**, with a reply-to a person reads. Replies are the best feedback channel a
  small company has.
- **Cap frequency across all sequences**: at most one lifecycle message per user per day, fewer
  once activated. Overlapping sequences are how a user receives three emails in one morning.
- **Suppress** users who already converted or have an open support conversation on the topic.
- **Send in the user's time zone** where the tool allows.
- Treat the delays as starting points; tune them to how quickly real users activate.

## In-app messages and habit nudges

In-app messages work while the user is present and the action is one click away; email brings
them back when they are not.

| Pattern | When | Rule |
|---|---|---|
| Onboarding checklist | First sessions | Three to five steps toward activation; the first already ticked; gone when done |
| Empty state | Any screen with no data yet | Explain the value and offer the action or sample data; never a bare empty table |
| Contextual tip | First visit to a feature | One tip, dismissible, never shown again once dismissed |
| Feature announcement | After a tier 1 or tier 2 release (`launches.md`) | Small banner or badge, only for users who can use it |
| Habit nudge | After the user repeats a manual action | "You've done this three times; automate it?", tied to real behavior |
| Milestone | A meaningful result reached | Show the value created: time saved, items processed |

- One message at a time: a queue, not a pile.
- Never interrupt a task. A modal on login or in the middle of a flow is the worst placement.
- Store dismissals and completions on the server so they hold across devices.
- Match the product's natural frequency: a weekly-use product nudged daily teaches users to
  ignore it.
- Build the first few in the app behind feature flags; adopt a dedicated in-app messaging tool
  at Scale. Flow and screen-state design: `0x:ui-ux-design`; channel preferences:
  `0x:email-notifications`.

## Segmenting by behavior, plan and stage

Every message goes to a segment for a stated reason. Sync the data from the product; never
maintain it by hand.

Attributes to send to the email tool for each user: lifecycle stage, plan, signup source, role
or use case from onboarding, key events with timestamps, last active date, team size, country
and language.

| Stage | Definition (adapt to the product) | Typical messages |
|---|---|---|
| Subscriber | On the list, no account | Newsletter, launches, content |
| Signed up, not activated | Account without the activation event | Activation sequence |
| Activated | Activation reached, free or trial | Habit building, upgrade path |
| Paying | Active subscription | Feature adoption, expansion, announcements |
| At risk | Paying, usage well below its own baseline | Help and re-engagement (success work: `0x:sales-support`) |
| Dormant | No activity for longer than the natural usage cycle | Re-engagement |
| Churned | Canceled or lapsed | Win-back |

Keep segments few: each one needs messages, and unmaintained messages rot. Emit stage changes
as events from the backend, or sync from the database on a schedule, so the email tool always
reflects the product's truth.

## Newsletter: a format that can be sustained

| Format | Fits | Effort |
|---|---|---|
| Founder essay | Expertise and opinions; B2B and developer audiences | High per issue |
| Curated links with commentary | A fast-moving domain, readers short of time | Medium, steady |
| Product updates with tips | Products that ship often | Low; doubles as release communication |
| Data or insight digest | Products with aggregate data worth sharing | Medium; the most differentiated |

- **Cadence**: the one that will still be kept a year from now. Every two weeks or monthly is
  fine; irregular gaps lose more readers than a slow, steady rhythm.
- **Plain, personal format** from a named person gets more replies than a designed template.
- **End with a question** worth answering. Replies are the clearest sign of a live audience.
- **Measure per issue**: replies, clicks into the product, attributed signups, unsubscribes and
  spam complaints. Opens are inflated by mail-privacy features that preload images (Apple Mail
  Privacy Protection above all); treat open rates as directional only.

## Re-engaging dormant users and sunsetting the list

Dormancy is relative to the product's natural rhythm: a few weeks for a daily tool, a couple of
months for a monthly one. That is a rule of thumb; derive the threshold from usage data.

Re-engagement for dormant accounts, in order:

1. What changed since they left, chosen for the likely reason they stopped.
2. An offer of help: a short call, a template, a migration.
3. One click to say why they stopped: a few fixed reasons plus free text.
4. An incentive only where pricing rules allow (`0x:pricing-monetization`), never first.

Win-back for churned paying customers: a few messages spread over months (for example about a
week, a month and three months after churn), each with a real reason to return. Cancellation
flows and save offers belong to `0x:sales-support`.

Sunset the marketing list: subscribers with no clicks, replies or product activity for roughly
three to six months get one re-permission message ("Still want these?"); remove those who do
not respond. Inactive addresses drag down engagement, which hurts delivery for everyone else,
and some become spam traps. Since opens are unreliable, base engagement on clicks, replies and
product activity.

## Measuring by activation and revenue

| Measure | How |
|---|---|
| Goal conversion | Share of recipients who reach the sequence's goal event within a set window |
| Incremental lift | A random holdout (around a tenth of eligible users) gets nothing; compare goal conversion |
| Revenue per recipient | Paid conversions and revenue within the window, per sequence |
| Health | Unsubscribes, spam complaints and replies per message |
| Leading signal | Clicks per message; opens only as a weak signal |

- Without a holdout, a sequence takes credit for users who would have activated anyway. Add
  holdouts once volume allows, usually at Scale; before that, compare cohorts before and after a
  change with care.
- A message with many clicks and no change in goal conversion entertains; it does not work.
- Holdout and test statistics: `0x:product-analytics`.

## Ask the user

- **What is the activation event?** Every sequence aims at it. Default: the first action that
  produces the product's core result for the user.
- **Which countries make up the audience?** Consent rules follow them. Default: run the list as
  if EU rules apply: explicit opt-in, double opt-in for EU signups, unsubscribe everywhere; no
  marketing SMS without express written consent.
- **Who signs the emails and reads the replies?** Default: the founder, by name.
- **Is a newsletter wanted, and how often can it really be written?** Default: monthly, product
  updates plus one useful insight.
- **May win-back messages offer a discount?** Default: never in the first message; the pricing
  policy decides about later ones.
