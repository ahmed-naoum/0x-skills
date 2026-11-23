# Referral and product-led loops

Read this when: making the product bring in its own users through invites, sharing, public
pages, templates, badges or a referral program, scoring product-qualified leads for sales, or
measuring whether a loop works.

## Loops come after retention

A loop exists when using the product exposes it to new people, some of whom become users and
repeat the cycle. A loop multiplies what the product already is: on a product people abandon
after a week, it spreads disappointment faster. Check retention first (`0x:product-analytics`);
build loops once cohort usage flattens instead of falling toward zero.

| Loop | Mechanism | Fits | Pattern |
|---|---|---|---|
| Collaboration invite | The work needs another person | Team tools, approvals, client portals, shared documents | Share a document, assign a task, request a review |
| Public artifact | The output is seen by non-users | Booking pages, forms, reports, portfolios, status pages | "Create your own" on every public page |
| Template and gallery | Users publish reusable starting points | Configurable products: workflows, designs, dashboards | Template page with "Use this template" |
| Badge or attribution | The output carries the product's mark | Embeds, emails, widgets, sites built with the product | "Made with X" on free plans |
| Incentivized referral | A reward for bringing a new customer | Products already recommended by word of mouth | Credit for both sides |
| Integration | The product appears inside another tool | Products that send data or actions elsewhere | Marketplace listing, attribution inside the other tool |

Choose the loop that falls out of the core workflow. A referral program bolted onto a product
nobody talks about produces a dashboard full of zeros.

## Invite loops in the core workflow

The strongest loop is a product that works better with another person in it.

- **Invite at the moment of need**, where the work is: a share button on the document, an
  assignee field, "request approval", "send to client". An "invite your team" onboarding step
  fits only products that are useless alone.
- **The invitee sees value before signing up**: the shared item opens without an account;
  signup is required only to edit, comment or reply. A signup wall in front of the shared item
  kills most of the loop.
- **Context in the invitation**: from the inviter's name ("Ana shared 'Q3 plan' with you"),
  showing what was shared and why, sent through the transactional channel
  (`0x:email-notifications`). One reminder after a few days if unopened, then stop.
- **The invitee's onboarding starts at the shared item**, not at an empty dashboard: their first
  session is the collaboration.
- **Abuse**: invitation emails are a spam and phishing vector. Require a verified email before
  sending invites, rate-limit invites per account per day, keep sender-written free text and
  links out of emails to strangers, and watch bounces and complaints on invitation mail
  (abuse defense: `0x:auth-identity`).
- **Instrument** invites sent per active user, acceptance rate, and invitee activation rate.

## Public pages and sharing

Every public page the product generates is a landing page shown to exactly the right audience:
the people the user works with.

- A visible but quiet product mark and a "Create your own" link on each public page, leading to
  a signup that starts with the same kind of page.
- Generated Open Graph images and titles, so shared links preview well in chat apps and feeds.
- **Privacy defaults**: decide per artifact whether sharing is on or off by default and make the
  state obvious. "Anyone with the link" uses long unguessable URLs and is still not a security
  boundary for sensitive data.
- **Indexing**: let search engines index public pages only when they are useful to strangers and
  the user opted in; noindex pages from new or unverified accounts.
- **Abuse**: public user-generated pages attract spam, phishing and malware. Add a report link,
  rate limits on publishing, link checks, review for new accounts and a fast takedown path. One
  phishing page can get the whole domain blocklisted by browsers and mail filters; host user
  content on a separate domain where that risk is real.

## Templates, galleries and badges

- **Template gallery**: each template is an indexable page showing the result, explaining the
  use case and offering "Use this template", which signs the visitor up with the template already
  loaded, so activation happens in the first minute. Seed the gallery with the founder's own
  best templates before opening it to users, and review submissions before listing them.
- **Creator incentives**: credit, profile pages and visibility for template authors work better
  than cash at small scale.
- **Badges**: "Made with X" on outputs of the free plan, removable on paid plans, turns usage
  into exposure and gives a reason to upgrade. Keep it small and tasteful, and link it with a
  referral parameter so it can be measured.
- **Embeds and widgets** carry the same mark and link.
- **Measure** visits, signups and activation from each surface; prune templates nobody uses.

## Referral incentives that resist fraud

| Decision | Default | Why |
|---|---|---|
| Who is rewarded | Both sides | The referrer is motivated and the friend has a reason to accept |
| Reward type | Product credit or plan extension; cash or gift cards only for B2B referrers who cannot use credit | Credit costs less than its face value and keeps the referrer a customer |
| When it is granted | After the referred customer pays and the refund window has passed | Removes most fake-account fraud |
| Size | Affordable within the CAC ceiling (`paid-acquisition.md`) | A reward above the ceiling loses money on every success |
| Caps | A maximum number of rewards per referrer per period | Limits the damage when a code leaks to coupon sites |
| Placement | After a success moment or a high satisfaction score, and on the account page | Asking at signup gets nothing; the user has no story to tell yet |

Fraud patterns and their controls:

| Pattern | Control |
|---|---|
| Self-referral with a second email | Reward only on payment; compare payment-method fingerprints, devices and IP addresses; reject plus-addressed and disposable domains |
| Fake accounts farming signup rewards | Never reward a signup alone |
| Codes posted on coupon and deal sites | Caps per referrer; terms forbid public posting |
| Refund or chargeback after the reward | Delay the reward; claw back credit when the payment reverses |
| Organized rings | Manual review above a reward threshold; alerts on unusual referral volume |

Publish short terms: eligibility, reward, timing, limits, the right to withhold for abuse. Cash
rewards can create tax reporting duties (in the US, an information return once one person's
payments in a year pass the IRS threshold; other countries differ: `0x:startup-finance`), and
referrers who promote the program publicly must disclose the reward (FTC Endorsement Guides in
the US, CMA and ASA rules in the UK, the Unfair Commercial Practices Directive in the EU).
Store the referral code or link on the
account at signup, next to the UTM data. Partners who are not customers (affiliates):
`community-partnerships.md`.

## Product-qualified leads

For products with self-serve signup plus a sales motion for larger accounts, usage shows who is
ready for a conversation better than any form. Skip this until someone, often the founder, has
time to talk to accounts and the price justifies a conversation.

Combine two kinds of signal:

| Fit (who they are) | Usage (what they do) |
|---|---|
| Company email domain, not a free mailbox | Activation reached |
| Company size and industry from enrichment | Several active users in the workspace, growing |
| Role of the person (admin, team lead, buyer) | Usage near a plan limit |
| Country and market served | Visits to pricing or enterprise features (SSO, audit log, security page) |
| | Integrations connected, invites sent, repeated weekly use |

- **Start with a points model a person can read**: a few points per signal and a threshold.
  Validate it against history: accounts above the threshold should have become paying customers
  several times as often as accounts below it. If not, change the signals.
- **Set the threshold by sales capacity**: route the number of accounts the team can contact
  well each week, highest score first.
- **Routing**: write the score and the reasons (what the account did) to the CRM, alert the
  owner, contact within a business day. Outreach refers to the usage helpfully ("your team is
  close to the seat limit; want help planning?") rather than revealing surveillance.
- **Close the loop**: record the outcome of every routed account and recalibrate each quarter.
- Using product usage for sales outreach must be covered by the privacy policy
  (`0x:privacy-compliance`). Prospecting and the conversation itself: `0x:sales-support`.

## Measuring a loop: viral coefficient and cycle time

The viral coefficient K is the number of new activated users each new user brings in:

```text
K = invites (or exposures) per new user × share of invites that become new activated users
```

- K above 1 means self-sustaining growth, which very few products reach. A K below 1 still
  multiplies every user acquired by other means: each one brings K, who bring K², and so on, for
  1 / (1 − K) users in total. At K = 0.3 that is about 1.43, which lowers effective CAC by about
  30%.
- **Cycle time** is the median time from a user's signup to their invitees' signups. Shorter
  cycles compound faster: the same K with a cycle of days instead of months produces a very
  different curve. Inviting at the moment of need shortens it.
- Measure per loop and per weekly signup cohort, with a fixed window:

```sql
-- K for users who signed up in one week: activated new users they brought in within 30 days.
-- Assumes invites(inviter_user_id, invitee_user_id, created_at), invitee_user_id set on
-- acceptance, and users(id, created_at, activated_at).
with cohort as (
  select id, created_at from users
  where created_at >= date '2026-10-05' and created_at < date '2026-10-12'
),
sent as (
  select i.created_at, i.invitee_user_id
  from invites i
  join cohort c on c.id = i.inviter_user_id
  where i.created_at < c.created_at + interval '30 days'
),
won as (
  select distinct s.invitee_user_id
  from sent s
  join users u on u.id = s.invitee_user_id
  where u.created_at >= s.created_at   -- new accounts only, not existing users
    and u.activated_at is not null
)
select
  (select count(*) from cohort) as new_users,
  (select count(*) from sent)   as invites,
  (select count(*) from won)    as activated_invitees,
  round((select count(*) from won)::numeric
        / nullif((select count(*) from cohort), 0), 3) as k;
```

Pitfalls that inflate K: counting invites to people who already had accounts; counting seats an
admin added after a team purchase (that is expansion, not virality); counting signups instead of
activated users; reading a cohort before its window has closed. Run it only for cohorts older
than the window plus the time invitees need to activate.

## Ask the user

- **Is the product more useful with other people in it?** That decides between an invite loop
  and a referral program. Default: an invite loop where collaboration exists in the workflow;
  otherwise a referral program only once word of mouth is visible.
- **What reward can the business afford per referred customer?** Default: product credit worth
  well under the CAC ceiling, double-sided, granted after the first paid period clears.
- **Should user-created pages be public or indexable by default?** Default: private, public on
  an explicit toggle, noindex unless the user opts in.
- **Is anyone available to follow up on product-qualified leads?** Default: no scoring until
  there is; meanwhile the founder reviews the top accounts by usage each week.
- **May the free plan carry a "Made with" badge?** Default: yes, small, removable on paid plans.
