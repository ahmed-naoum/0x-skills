# SMS, push and chat channels

Read this when: adding SMS, web push, mobile push or chat-app messaging, choosing which channel
a message goes to, or when SMS cost, push opt-in or delivery goes wrong.

## Which channel for which message

Choose by how soon the person must act and how much interruption the message has earned.

| Channel | Use for | Cost and limits | Do not use for |
|---|---|---|---|
| In-app (inbox, badge, toast) | Everything the user might want to find later; the system of record | Free; only seen when in the product | Anything that must reach an absent user alone |
| Email | Receipts, records, anything with detail or that must be searchable later; digests | Near free; minutes of latency are normal; arrives beside everything else | Second-level urgency |
| Push (web or mobile) | Timely, short, personal: a reply, a mention, "your export is ready", a delivery | Free; needs permission; no delivery guarantee; revoked in one tap | Marketing by default, long content, anything that needs a record |
| SMS | Login codes where no better factor exists, and operational alerts with money or safety attached (appointment in an hour, fraud alert, on-call page) | Paid per segment, per country; registration; fraud exposure | Anything email or push can do; marketing without explicit consent |
| Chat (WhatsApp, Slack, Teams) | Markets or products where the conversation already lives there | Template approval or app install; per-message fees on WhatsApp | A default channel in a market that does not use it |

Decision rules:

- Start at Launch with email plus in-app. Add push when there are events a user wants within
  minutes and a reason to believe they will grant permission. Add SMS last and only for a
  named message type.
- Every push and SMS has an in-app or email counterpart, because neither is durable.
- The more interruptive the channel, the fewer message types it carries. A rule of thumb: if the
  user would not thank the product for waking their phone, it is not a push.
- For B2B tools, a Slack or Teams integration often replaces push entirely and gets a team-wide audience.
- For authentication, passkeys and authenticator apps beat SMS on cost and security; factor
  choice is `0x:auth-identity`.

## Push permission

A denied prompt is close to permanent: browsers and iOS do not let the product ask again, and the
user must dig through settings. The prompt is spent once, so spend it well.

- Never prompt on page load or first launch. Browsers penalize it (quiet UI, automatic blocking
  for sites with low acceptance) and users refuse by reflex.
- Ask right after an action that makes the value concrete: the user posts a question ("Notify
  me when someone answers?"), places an order, or starts a long job.
- Use a soft ask first: an in-product explanation with "Enable" and "Not now". Only "Enable"
  triggers the system prompt, from that click (a user gesture is required in Safari and Firefox,
  and is good practice everywhere). "Not now" costs nothing and can be offered again later.
- Say which notifications will come and that they can be tuned. Then send only those.
- Read the current state before showing any UI: `Notification.permission` is `default`,
  `granted` or `denied`. For `denied`, show instructions to re-enable only where the user asks.
- iOS: provisional authorization delivers quietly to the notification center without a prompt
  and lets the user keep or turn off; use it for low-urgency products. Android 13 and later
  require a runtime permission like iOS, so the same timing rules apply.
- Track prompt shown, accepted and denied per placement; an acceptance rate that is low at one
  placement means the ask is in the wrong moment.

## SMS through a provider

Default: Twilio, or the SMS product of a provider already in the stack. For login codes prefer a
managed verification API (Twilio Verify or equivalent) over raw SMS plus hand-written code logic:
it brings templates pre-approved in many countries, routing and fraud controls, and in some
countries its own registered senders (confirm per target country before skipping registration).

Sender types and registration (the part that delays launches by weeks):

| Destination | Sender | Registration |
|---|---|---|
| United States | 10-digit long code (10DLC) | Brand and campaign registration is mandatory; unregistered traffic is blocked. Days to weeks |
| United States, Canada | Toll-free number | Verification must be approved before anything is delivered; unverified numbers are blocked. Days to weeks, with business identity details |
| United States | Short code | Lease and carrier approval; weeks and expensive. Only for high volume |
| UK, much of Europe and Asia-Pacific | Alphanumeric sender ID (the brand name) | Varies and is tightening: some countries need nothing or a letter of authorization through the provider; a growing number (Ireland, Spain, Australia and Singapore among them) run mandatory registries and block or relabel unregistered IDs. Recipients cannot reply |
| India and several other countries | Registered sender and registered message templates | Local entity or paperwork; plan well ahead or use WhatsApp |

Rules:

- Start registration the day SMS is decided; build while waiting. The registration asks for the
  opt-in flow, sample messages and a privacy policy URL, and is rejected when these are vague.
- Check the provider's per-country guidelines before enabling a country: sender type, required
  wording, quiet hours and whether the content type is allowed at all.
- Store numbers in E.164 (`+14155550123`). Parse and validate with libphonenumber using the
  user's selected country; do not write a regex.
- In the United States and Canada, STOP and HELP replies must work. Providers handle the
  keywords by default; mirror the opt-out into the app (webhook) so the product stops trying,
  and expect a "recipient unsubscribed" error if it does not.
- Marketing SMS needs explicit prior consent and has legally defined sending hours in several
  jurisdictions; consent law is `0x:privacy-compliance`.
- Cost is per segment: 160 characters in the GSM-7 alphabet, 153 per segment once concatenated.
  One character outside GSM-7 (an emoji, a curly quote, some accented letters) switches the
  whole message to UCS-2 at 70 characters, 67 when concatenated. A few GSM-7 characters (square
  and curly brackets, pipe, caret, tilde, backslash, the euro sign) count as two. Keep codes and
  alerts in one GSM-7 segment and strip smart punctuation from templates.
- Carriers filter public link shorteners and messages that look like phishing. Use the product's
  own domain in full, name the brand at the start, and keep one link at most.
- For web login codes, add the origin-bound last line so browsers and iOS can autofill safely:

```text
123456 is your Acme code. Do not share it.

@app.example.com #123456
```

## SMS pumping and OTP abuse

Fraudsters trigger code messages to numbers they profit from (premium ranges, colluding
carriers). The product pays per message. Any unauthenticated endpoint that sends SMS is a target
from the day it is public.

Symptoms: a jump in sends to countries with no customers, consecutive or similar numbers,
verification completion rate collapsing, and a bill.

Controls, cheapest and most effective first:

1. **Country allowlist** in the provider console (geo permissions): enable only countries with
   real customers. Disabled by default for everything else. This alone removes most exposure.
2. **Rate limits on several keys at once**: per phone number (for example one code per minute,
   five per hour), per IP, per device or session, per account, and per number prefix so
   sequential numbers in one range trip a limit. Increase the resend delay on each attempt.
3. **Require proof of a real client before sending**: a session that already verified email, a
   bot check on the form, and no SMS-sending endpoint callable without a CSRF-protected session.
4. **Line-type lookup** before first send to reject landlines and, where policy allows,
   disposable VoIP numbers.
5. **Conversion monitoring**: track codes sent versus codes verified per country and per hour;
   alert and auto-disable a country when the ratio collapses.
6. **A hard spend ceiling**: provider usage alerts plus an application-level daily cap that
   fails closed to "try another method". An alert at 3 a.m. does not stop the spend; a cap does.
7. Turn on the provider's fraud protection for verification traffic where offered.

Rate-limit design generally is in `0x:api-design`; signup abuse defense in `0x:auth-identity`.

## Web push

Pieces: a service worker, a VAPID key pair (public key in the client, private on the server), a
subscription per browser, and a push library on the server (`web-push` for Node).

1. Register the service worker; after the soft ask, call
   `registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey })`.
2. Send the subscription (`endpoint`, `keys.p256dh`, `keys.auth`) to the server; store it per
   user with a unique constraint on `endpoint`, plus user agent and `last_seen_at`.
3. On every app load, read `pushManager.getSubscription()` and upsert it. Subscriptions change
   and expire silently, and the `pushsubscriptionchange` event is not reliable across browsers.
4. In the worker, every push must show a notification:

```js
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data?.json() ?? {}; } catch { /* not JSON: still show something */ }
  event.waitUntil(
    self.registration.showNotification(data.title ?? "Acme", {
      body: data.body, tag: data.tag, data: { url: data.url ?? "/" },
    }),
  );
});
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url));
});
```

5. On the server, delete dead subscriptions when the push service says so:

```ts
try {
  await webpush.sendNotification(sub, JSON.stringify(payload), { TTL: 3600 });
} catch (err: any) {
  if (err.statusCode === 404 || err.statusCode === 410) await deleteSubscription(sub.endpoint);
  else throw err;
}
```

Traps:

- A push that shows nothing is treated as abuse: Chrome shows a generic "site updated in the
  background" notification, and Safari revokes the subscription after a few silent pushes. A
  handler that throws before `showNotification` counts as silent.
- On iOS and iPadOS, web push works only for a site added to the Home Screen as a web app, and
  there is no install prompt: the user must find Share, Add to Home Screen, and the permission
  request works only inside the installed app. For a consumer product whose users are mostly on
  iPhone, web push reaches few of them; plan email or a native app.
- Payloads are limited to about 4 KB and are visible on lock screens. Send a title, a short body
  and a URL; fetch detail after the click.
- Set `TTL` to how long the message stays useful (0 means "now or never"), and use `tag` so a
  newer notification replaces an older one about the same thing instead of stacking.
- Delete the subscription on logout, and unsubscribe in the browser. Otherwise the next person
  on that browser receives the previous user's notifications.
- Rotating VAPID keys invalidates every subscription. Store the private key as a long-lived secret.

## Mobile push: APNs and FCM

| Topic | APNs (iOS) | FCM (Android, optionally iOS) |
|---|---|---|
| Server auth | Token-based with a `.p8` key (does not expire, can be revoked). Certificates expire yearly and take push down when forgotten | Service account with the HTTP v1 API; the legacy server-key API is shut down |
| Environments | Sandbox and production are separate hosts with separate device tokens; mixing them returns `BadDeviceToken` | One environment; separate Firebase projects for staging |
| Dead token signal | HTTP 410 `Unregistered`; 400 `BadDeviceToken` for a malformed or wrong-environment token | HTTP 404 `UNREGISTERED`; 400 `INVALID_ARGUMENT` can mean a bad token or a bad payload, so delete on it only when the payload is known good |
| Collapse | `apns-collapse-id` header | `collapse_key` |
| Expiry | `apns-expiration` | `ttl` |
| Priority | `apns-priority` 10 immediate, 5 power-saving | `high` wakes a dozing device, `normal` waits; overuse of `high` gets deprioritized |

Decision: send through FCM for both platforms (one API, it relays to APNs) or through a push
service (Expo for React Native apps, OneSignal) unless there is a reason to speak APNs directly.
Direct APNs is worth it when iOS-specific features or delivery debugging matter. When speaking
APNs directly, cache the signed provider token: Apple rejects one older than an hour
(`ExpiredProviderToken`) and throttles a sender that mints a new one more often than about
every 20 minutes (`TooManyProviderTokenUpdates`), which is what a token-per-request
implementation hits in production. Send `apns-topic` and `apns-push-type` on every request.

Token hygiene, which decides whether push works in month six:

- A token identifies an app install, not a user. Store `(user_id, token, platform, app_version,
  last_seen_at)` with the token unique; a user has many, and a token moves between users.
- Send the token to the server on every app start and whenever the SDK reports a refresh; update
  `last_seen_at`. On login, reassign the token to the new user. On logout, delete it server-side.
- Delete on the dead-token responses above, immediately. Additionally prune tokens not seen for
  a staleness window of a month or two (rule of thumb): FCM tokens of inactive devices keep
  accepting messages that go nowhere until FCM expires them, which its documentation puts at
  about nine months of inactivity on Android.
- Do not retry permanent errors. Retry 429 and 5xx with backoff and honor `Retry-After`.
- "Accepted by APNs or FCM" means queued for the device. There is no delivery receipt to rely
  on; devices offline, in battery saver, or with notifications disabled produce no error.
- Silent or background pushes are throttled by the operating system. Never build correctness on
  them; the app must fetch state when it opens.
- Android 8 and later group notifications into channels the user controls individually. Map
  channels to the product's notification categories so users mute one kind instead of all.
- Keep sensitive content out of the payload; show "New message from Ana" and load the rest in the app.

## Receipts, failures and fallback

| Channel | Signal available | Reliability |
|---|---|---|
| Email | Delivered, bounced, complained webhooks | Good for delivery to the server; says nothing about inbox versus spam |
| SMS | Status callback: queued, sent, delivered, undelivered, failed, with an error code | Carrier-reported; missing or optimistic in some countries |
| Push | Accepted or token error only | No delivery or display signal |
| In-app | Seen and read, recorded by the product | Exact |

- Record one delivery row per notification per channel with provider ID, status and error code;
  update it from status webhooks (signature verified, deduplicated, status only moves forward).
- Classify SMS failures: unreachable or unknown handset (retry later once), landline or invalid
  number (mark the number bad and ask the user), carrier filtered (a content or registration
  problem on the sender side; retrying makes it worse), recipient opted out (stop).
- **Escalate on "not acted", not on "not delivered"**, because delivery signals are weak. Pattern:
  write in-app and send push at once; if the item is still unread after a delay that fits its
  urgency (minutes for a mention, an hour for a task), send the email; SMS only for types the
  user opted into as urgent.
- The fallback step re-checks state before sending. Reading the item anywhere cancels the rest.
- Fallback sends share the notification's ID so they deduplicate and so analytics count one
  notification delivered through two channels, not two.
- For login codes, do not auto-fallback to a second channel: offer "Send by email instead" or a
  voice call after a visible timeout, so one request never fans out into several paid messages.

## WhatsApp and other chat channels

Use WhatsApp when a meaningful share of customers live in markets where it is the default
messenger (much of Latin America, India, Southern Europe, the Middle East, Africa, Southeast
Asia) and they ask for it, or when SMS to those countries is costly and unreliable.

- Access is through the WhatsApp Business Platform: Meta's Cloud API directly, or a provider
  (Twilio and others) that adds a unified API at a markup. It needs a verified business and a
  dedicated number.
- Business-initiated messages must use pre-approved templates in a category (marketing, utility,
  authentication) and require the user's opt-in to WhatsApp messages specifically. Free-form
  messages are allowed only inside the 24-hour window after the user's last message.
- Meta charges per delivered template message, by category and recipient country, and revises
  the rules often: which messages inside the service window are free, volume tiers, and
  restrictions on marketing templates in particular countries. Read the current rate card
  before promising a cost; authentication and utility templates are cheaper than SMS in many
  countries, not all.
- Meta rates sender quality from blocks and reports. Low quality pauses templates and lowers the
  daily limit, so the fatigue rules for push apply with real penalties.
- Inbound replies arrive by webhook and open a conversation someone must answer; decide who
  before enabling. Support tooling is `0x:sales-support`.

Other channels: Slack and Microsoft Teams apps for B2B products (post to a channel the customer
chooses, respect workspace admin install flows); Telegram bots for technical and crypto
audiences. RCS business messaging exists and is growing; skip it until Scale and treat SMS as
its fallback. Each new channel is an integration to monitor; add one when customers ask twice.

## Ask the user

- **Which countries must SMS reach?** It sets registration work, cost and the fraud allowlist.
  Default: only the countries with current paying customers.
- **What daily SMS spend is the ceiling?** A cap that fails closed is the last defense against
  pumping. Default: a small multiple of the normal day, with an alert at half.
- **Which events are worth a push or an SMS?** Each added type raises opt-out risk for all of
  them. Default: push for direct replies, mentions and completed long-running work; SMS for
  login codes only when no better factor is available.
- **Is a native app planned, or web only?** Web push barely reaches iPhone users. Default: web
  only with email as the reliable channel.
- **Do customers expect WhatsApp or Slack?** It depends on market and audience. Default: no chat
  channel until customers ask for it.
