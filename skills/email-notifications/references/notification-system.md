# Notification system design

Read this when: notifications span several types and channels and need preferences, an in-app
inbox, batching or digests, throttling, quiet hours, measurement, or a build-versus-buy decision.

## One entry point

Feature code never calls an email, push or SMS client. It calls one function and states what
happened; the notification layer decides whether, where and when.

```ts
await notify({
  type: "comment.created",
  recipientId,
  actorId,                       // never notify the actor about their own action
  data: { commentId, threadId },
  dedupeKey: `comment:${commentId}:${recipientId}`,
});
```

Inside `notify`, in this order: load the type definition; drop if recipient equals actor or
lacks access to the object; deduplicate; resolve channels from type defaults and user
preferences; apply throttles, batching and quiet hours; write the in-app row; enqueue per-channel
deliveries. Authorization is checked here and again at render time: permissions change between
event and digest.

Introduce this function at Prototype even when it only sends one email. Retrofitting it across
forty call sites is the expensive version.

## Model: types, channels, preferences

| Piece | Lives in | Holds |
|---|---|---|
| Type registry | Code (a typed object) | key, category, default channels, `required`, batch window, urgency, template per channel |
| Category | Code | The 4 to 8 groups users see in settings: Security, Billing, Mentions and replies, Activity, Product updates |
| Preference | Database, sparse | `(user_id, category, channel, enabled)`; only rows where the user changed something |
| Notification | Database | One row per recipient per event: the inbox record |
| Delivery | Database | One row per notification per channel: status, provider ID, timestamps |

Rules:

- Store overrides, not a full matrix. With sparse rows, changing a default or adding a type
  takes effect for everyone who never touched the setting, with no backfill.
- Resolution: `required` types ignore preferences; otherwise the user's row for (category,
  channel) wins; otherwise the type's default. Keep this in one pure function with tests.
- Show categories in settings, not types. A matrix of categories by channels (Email, Push,
  In-app) with 5 to 8 rows is usable; forty toggles are not, and users answer them by turning
  everything off.
- Channel availability is separate from preference: no verified email, no push token, a
  suppressed address. Show "unavailable" with the reason instead of a toggle that does nothing.
- Multi-tenant products need per-workspace preferences (muted in workspace A, not B) and often
  per-object mutes ("unfollow this thread"). Object-level mute removes more noise than any global toggle.
- Every non-required email carries a link that changes the preference for that category
  without logging in (a signed token), plus a path to the full settings page.
- Defaults: in-app on for everything; email on for what the user must not miss or asked for;
  push on only for direct, timely items; SMS off unless explicitly chosen.

## Required messages and opt-out messages

| Class | Examples | Opt-out | Stream |
|---|---|---|---|
| Required transactional | Verification, password reset, security alerts, receipts, payment failure, legal and policy notices, data export ready | None; suppress only on hard bounce | Transactional |
| Product activity | Mentions, replies, assignments, shares, digests of activity | Per category and channel, default on | Transactional stream is acceptable; keep volume honest |
| Marketing and lifecycle | Newsletters, feature announcements, upgrade offers, re-engagement, onboarding tips | Always, one click; consent required first in many jurisdictions | Marketing stream, separate subdomain |

- The test for "required": the user triggered it, or cannot safely use the account without it,
  and it promotes nothing. "We think they would want to know" is not required.
- Adding an upsell block to a receipt can turn it into a marketing message for legal and
  filtering purposes. The legal test differs by jurisdiction (United States law looks at the
  primary purpose of the message; UK and EU-style rules tend to treat any promotional content
  as marketing), so the design that is safe everywhere is required mail with no promotion.
- Mark `required` in the type registry and get the user's explicit sign-off on any addition; the
  flag bypasses user choice, so it attracts misuse ("make the launch announcement required").
- A global "unsubscribe from everything" must leave required mail working and say so on the page.
- Onboarding sequences and upgrade nudges are lifecycle mail: opt-out applies. A notice that a
  trial is about to convert to a paid charge, or that a subscription renews, is different:
  auto-renewal rules in several jurisdictions require it, so send it as required billing mail
  with no promotion and do not let a marketing unsubscribe silence it. Lifecycle strategy is
  `0x:growth-marketing`; renewal and payment-failure sequences are `0x:payments-billing`; the
  legal definitions and consent rules are `0x:privacy-compliance`.

## In-app inbox

```sql
create table notifications (
  id uuid primary key default uuidv7(),      -- PostgreSQL 18+; otherwise generate in the app
  user_id uuid not null references users(id) on delete cascade,
  type text not null,
  group_key text,                -- e.g. 'thread:123' for collapsing
  dedupe_key text,
  payload jsonb not null,        -- ids and minimal display data, not rendered text
  created_at timestamptz not null default now(),
  seen_at timestamptz,           -- appeared in the opened list; clears the badge
  read_at timestamptz,           -- opened or acted on
  unique (user_id, dedupe_key)
);
create index notifications_unread on notifications (user_id, created_at desc)
  where read_at is null;
```

- Two states, not one: `seen` clears the badge when the panel opens; `read` marks the item
  handled. With only `read`, either the badge never clears or everything is marked read on open.
- Badge count comes from the partial index, capped in the query (`limit 100`, display "99+").
  Do not maintain a counter column until the count query shows up in profiling.
- "Mark all read" takes the timestamp of the newest item the client has shown:
  `update ... set read_at = now() where user_id = $1 and read_at is null and created_at <= $2`.
  Without the bound it marks items that arrived a second ago and were never displayed.
- Store IDs and render at read time in the viewer's current locale, checking the object still
  exists and is still visible to them. Deleted target: show the item as unavailable, do not 404.
- Collapse by `group_key` at read time ("Ana and 3 others replied"); keep the rows separate so
  each has its own read state and so email digests can use the same rows.
- Pagination is by cursor on `(created_at, id)`. Retain a bounded history (for example 90 days
  or the last few hundred per user) with a scheduled delete; inboxes grow without limit otherwise.
- Freshness: at Launch, refetch on window focus and poll every 30 to 60 seconds while visible.
  Add server-sent events or WebSockets only when the product already has a realtime channel;
  realtime transport is `0x:backend-architecture`.
- State is shared across channels: following the link in the email or tapping the push marks the
  inbox item read (carry the notification ID in the URL), and reading in-app cancels pending
  email or push for that item.
- The inbox panel needs focus management and live-region announcements; see `0x:accessibility`.

## Batching and digests

Without batching, an active thread sends one email per comment and the user turns email off for
good. Batch per `(recipient, type, group_key)`.

- **Window batching**: the first event opens a window and schedules one job at its end; later
  events in the window only add rows. The job collects all unsent rows for the key and sends one
  message ("5 new comments on Q3 plan"). Typical windows: a few minutes for conversation
  activity, an hour for low-urgency activity. Use a fixed window from the first event, or cap a
  sliding window with a maximum wait, so a busy thread cannot delay the message forever.
- **Presence check**: at send time, skip items already read and skip the email entirely if the
  user has been active in the product within the window. This removes the most resented
  duplicate, the email about something seen ten seconds ago.
- **Scheduled digests**: daily or weekly, sent at a fixed local hour in the user's time zone
  (morning works for work tools). Offer "instantly, daily, weekly, off" per category where
  volume is high. Never send an empty digest, and cap its length with a link to the rest.
- Push batches differently: use the collapse identifier or `tag` so the device replaces "1 new
  reply" with "3 new replies" instead of stacking three alerts.
- Do not batch required or time-critical types (codes, security alerts, payment failures).
- The scheduled job must be idempotent on `(recipient, key, window_start)`: a retried job that
  finds its rows already marked sent does nothing.

## Deduplication and throttling

| Problem | Mechanism |
|---|---|
| The same event processed twice (retry, double webhook) | Deterministic `dedupe_key` with a unique constraint; insert with `on conflict do nothing` and stop if no row was inserted |
| One action generates several notifications to one person (mentioned, also assignee, also watcher) | Resolve to one notification per recipient per event, keeping the most specific reason |
| A burst of legitimate events (bulk import, 200 tasks reassigned) | Per-recipient, per-type cap in a time window; overflow is summarized ("and 187 more") or moved to the digest |
| A bug or loop sending to everyone | Global circuit breaker: when a type's hourly volume exceeds a multiple of its normal level, or one job tries to enqueue more than a set number, pause that type and alert a human |
| One user spamming others (mention bombing, invite abuse) | Per-actor limits on notification-generating actions, stricter for new accounts |
| A chatty integration | Per-source caps, and coalesce updates to the same object |

- Per-user budgets by channel are a useful backstop: a small number of pushes per hour and of
  non-required emails per day (rule-of-thumb values; tune from opt-out data), with overflow
  falling to in-app only. Required types bypass budgets.
- Bulk operations should pass a flag to `notify` that forces summarization instead of relying
  on caps to clean up afterwards.
- Fan-out to a large audience (announcement to all users) runs as chunked jobs with a rate
  limit, resumable by cursor, with a dry-run count shown before it starts.
- Test the breaker. The incident it prevents (a loop mailing every customer hundreds of times)
  is the one that gets a sending domain blocklisted in an hour.

## Quiet hours, time zones and locale

- Store an IANA time zone name per user (`Europe/Berlin`), captured from the browser with
  `Intl.DateTimeFormat().resolvedOptions().timeZone` and refreshed on login; let the user
  override it. Never store a UTC offset: it is wrong twice a year.
- Default quiet hours for push and SMS of non-urgent types: about 22:00 to 08:00 local.
  Email is not held for quiet hours except scheduled digests. In-app is never held.
- Defer, do not drop: schedule the delivery for the end of the quiet period, re-check
  read state and relevance then, and give each type a maximum age after which it is discarded
  ("meeting starts in 10 minutes" is worthless at 08:00).
- Urgent and required types bypass quiet hours: security alerts, login codes, and whatever the
  user explicitly marked as "always notify" (on-call pages).
- Compute the next send time with a time-zone library at scheduling time. Local times that do
  not exist or occur twice on clock-change days must not crash or double-send the daily digest;
  key the digest on the local date.
- Unknown time zone: fall back to the workspace's zone, then to a guess from the last request,
  then hold non-urgent push to the conservative overlap of plausible daytime hours.
- Render in the **recipient's** locale and time zone, not the actor's and not the server's. Dates
  inside messages state the zone or use relative wording. Store a locale per user, fall back
  language-then-default (`pt-BR`, `pt`, `en`), and render at send time, not at event time.
- Marketing SMS and calls have legally defined hours in some jurisdictions; see `0x:privacy-compliance`.

## Measurement

Record per notification and channel: created, sent, delivered (where the channel reports it),
opened or seen, clicked, and **acted**: the product action the notification existed to cause
(replied, paid, viewed the report), attributed within a window.

| Metric | Trust | Use |
|---|---|---|
| Delivery rate, bounce rate | High | Channel health; alert on change |
| Email open rate | Low: privacy features preload tracking pixels and image blocking hides real opens | Trend only, never a decision |
| Click rate | Medium: security scanners click links | Compare types against each other |
| Action rate | High | The measure of whether a type earns its interruption |
| Opt-out, mute, push-disable and complaint rate after a send | High | The cost side; the guardrail for every change |

- Tag every provider message with its type key so provider dashboards and webhooks can be split by type.
- Review per type on a schedule: high volume with low action rate and rising opt-outs means
  move it to digest, lower its default, or delete it. Deleting a notification type is a feature.
- A notification can look effective only because active users get more of them. To know whether
  a type causes the action, hold out a small random group; experiment design is `0x:product-analytics`.
- Watch the share of users with push disabled at OS level and email globally unsubscribed over
  time. These are irreversible for practical purposes, and their trend is the fatigue metric.
- Skip dashboards at Prototype. At Launch, the delivery table plus two queries (rates per type,
  opt-outs per type) is enough.

## Notification service or in-house routing

| Situation | Choice |
|---|---|
| One or two channels, under about ten types, no digests | In-house: `notify()`, the tables above, the email provider. A few days of work |
| Three or more channels, digests and batching, a preference center, an inbox component, and no wish to build them | A notification service (Knock, Courier, or Novu which can be self-hosted) |
| Mobile push is the main channel and marketing wants segments and campaigns | A push-focused service (OneSignal or similar) for that channel |
| Non-engineers must edit workflows and copy | A service with a workflow editor |

The vendors named are examples; confirm their current features, pricing and hosting options.
Consider before buying: the vendor sits in the delivery path of every message (keep
authentication mail going directly to the email provider so login survives a vendor outage); it
is another processor of user data and message content; pricing usually scales with messages or
active users; and the preference and inbox data model becomes theirs. Keep `notify()` as the only
interface either way, so the choice can be reversed in one module. Vendor evaluation in general
is `0x:engineering-leadership`.

## Ask the user

- **Which notifications must nobody be able to turn off?** The flag overrides user choice and has
  legal weight. Default: security, account access, receipts and payment failures, legal notices.
- **Which categories should users see in settings, and what is on by default?** It defines the
  product's tone toward attention. Default: 5 to 8 categories, in-app on, email on for direct
  items, push only for direct and timely items.
- **Should activity email be instant, batched or a daily digest by default?** It trades
  immediacy against fatigue. Default: batched by a short window, with a daily option.
- **Are there events urgent enough to break quiet hours?** Wrong either way hurts: a missed
  alert or a 3 a.m. buzz. Default: only security alerts and login codes.
- **Build or buy the notification layer?** It is a recurring cost against a few weeks of
  engineering. Default: in-house until three channels or digest and preference needs appear together.
