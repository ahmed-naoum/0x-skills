# Sending transactional email

Read this when: adding or restructuring email sending in the app (provider choice, templates,
the sending path, previews and tests, send logs), or wiring inbound mail and replies.

## Provider and streams

| Situation | Choose | Why |
|---|---|---|
| Default, any stage | Postmark or Resend | Fast delivery, good shared pools, usable logs, minutes to set up |
| Already on AWS, cost matters, volume is high | Amazon SES | Cheapest per message; you build logs, suppression views and dashboards yourself |
| The project already has a working provider | Keep it | A switch moves the stream to new IPs and a new signing setup, so receivers re-evaluate it and volume has to be ramped again; move only for a concrete failure |
| "Just use Gmail/Workspace SMTP" | No, beyond a Prototype | Per-day sending caps, no bounce webhooks, and bulk app mail endangers the founders' own mailboxes |

Rules that hold for every provider:

- **Send through the HTTP API, not SMTP**, unless a framework forces SMTP. The API returns a
  message ID and structured errors, and supports tags, metadata and (where offered) idempotency keys.
- **Two streams from day one of Launch**: transactional (receipts, verification, resets, security
  alerts) and broadcast or marketing (newsletters, announcements, lifecycle). Separate them at
  least by provider stream and subdomain (`notify.example.com` and `news.example.com`), and by IP
  pool where the provider allows. A complaint spike on a newsletter must not delay a password reset.
  Postmark enforces this with message streams; on Resend and SES create it with separate domains
  or configuration sets.
- **One provider, not two with failover**, until Scale. A second provider means a second warm
  domain reputation, second suppression list and second webhook integration. Handle provider
  outages by queueing and retrying.
- New SES accounts start in a sandbox that delivers only to verified addresses under a small
  daily quota. Request production access days before launch, not on launch day.
- Create separate API keys per environment and restrict them to sending only where the provider
  offers scoped keys.

## The sending path

The request that causes an email does not send it. It records the intent in the same database
transaction as the state change; a worker sends it.

```sql
create table email_outbox (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null unique,      -- e.g. 'receipt:inv_123'
  template text not null,
  template_version int not null,
  to_address text not null,
  user_id uuid,
  payload jsonb not null,
  status text not null default 'queued',     -- queued | sent | delivered | bounced | complained | failed | skipped
  provider_message_id text,
  expires_at timestamptz,                    -- drop instead of sending late
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  last_error text
);
```

Sequence, and why each step is there:

1. In the business transaction, `insert ... on conflict (idempotency_key) do nothing`. If the
   transaction rolls back, no email exists. If the handler runs twice, one row exists.
2. Derive the key from the business event, never from a random value or a timestamp:
   `welcome:{userId}`, `receipt:{invoiceId}`, `reset:{resetTokenId}`. A random key deduplicates nothing.
3. The worker claims a row, checks the suppression list and `expires_at`, renders, calls the
   provider, then stores `provider_message_id` and `status = 'sent'`.
4. A crash between the provider call and the status update causes a resend on retry. Close that
   window by passing the same key as the provider's idempotency key where one exists; otherwise
   accept the rare duplicate for low-stakes mail. Resend accepts one per request and remembers
   it for about 24 hours (check the current window), which covers retries but not a replay days
   later: the outbox's unique key stays the real guard. The same key with a different payload
   is rejected with a 409; treat that as a bug, not as something to retry.
5. Retry on network errors, HTTP 429 and 5xx with exponential backoff. Do not retry 4xx
   validation errors or "recipient inactive/suppressed" responses: mark `failed` or `skipped`.

```ts
const { data, error } = await resend.emails.send(
  { from: "Acme <notify@notify.example.com>", to, subject, html, text, tags },
  { idempotencyKey: row.idempotencyKey },
);
if (error) throw new SendError(error); // this SDK returns errors instead of throwing
```

Traps:

- Sending inside a database transaction: the transaction rolls back, the email is already gone,
  and it describes something that never happened.
- Time-critical mail (login codes, resets, verification) sits behind a backlog of digest mail.
  Give it its own queue or priority, and set `expires_at` to the token lifetime so a code is
  never delivered after it stopped working.
- Rendering in the web request and storing HTML in the queue: stores personal data twice and
  freezes a template bug into queued rows. Store the payload and template version; render in the worker.
- At Prototype, sending inline with `await` is acceptable. Keep the single `sendEmail()` entry
  point so moving it behind a queue later touches one file.

Queue choice and retry machinery belong to `0x:backend-architecture`.

## Templates

Keep templates in the repository, rendered by the app, and send finished HTML and text to the
provider. Provider-hosted templates drift from the code that fills them, cannot be code-reviewed
and tie the product to the vendor. Flip this only when a non-engineer must edit copy weekly.

- Default tooling: React Email (components compile to table-based HTML with inline styles). MJML
  is the alternative outside React. Hand-written HTML email is a maintenance trap.
- One typed function per template: `renderReceipt(props): { subject, html, text }`. Validate
  props with a schema; a missing variable must fail the job, not send "Hi undefined".
- `template_version` in the outbox row lets support see exactly what a user received after the
  template changed. Bump it on any visible change.
- One shared layout (header, footer, legal address where required, preference link for
  non-essential mail). Never copy the layout into each template.
- Escape every interpolated value. User-controlled names in a subject or body are an injection
  path for phishing content ("Your account is locked, visit evil.example"). Strip CR and LF from
  anything that goes into a header, and cap the length of user-supplied names.

## Writing the message

- **Subject** states the specific event with its identifier: "Receipt for your May invoice
  (#1042)", "Confirm your email for Acme". No "Important update". Keep the meaning in roughly
  the first 40 characters; mobile clients truncate.
- **Preheader**: set the hidden preview text deliberately; otherwise clients show "View in
  browser" or the logo alt text.
- **One action** per email: one primary button, repeated as a plain URL under it. A receipt's
  action is "view invoice"; a reset's action is "choose a new password". Secondary links go in the footer.
- **Plain-text part always** (`multipart/alternative`). Write it or generate it from the same
  component and read the result once. HTML-only mail is a negative signal to some filters and is
  unreadable in some clients and for some assistive setups.
- **From**: a human-readable name and a stable address on the sending subdomain. Changing the
  From address resets recipient-side trust and filters.
- **Reply-To** points at a monitored inbox. `no-reply@` discards the cheapest support and
  deliverability signal available (a reply tells the mailbox provider the mail is wanted).
- **Turn off click and open tracking on the transactional stream**, and always on
  authentication mail. Rewritten links point at a tracking domain (looks like phishing, breaks
  universal links), and the pixel adds a third-party image to a security message.
- Corporate link scanners open every URL in a message. Any link that performs an action on GET
  (verify, unsubscribe, approve) will be triggered by a robot. Links land on a page; a button
  press performs the action. Token design is `0x:auth-identity`.
- Do not put secrets, full card numbers or passwords in email. State what happened, when, and
  what to do if the reader did not do it.

## Rendering across clients and dark mode

Design for the worst engines, test in three: Gmail (web and mobile app), Apple Mail (iOS), and
Outlook on Windows.

| Constraint | Consequence |
|---|---|
| Classic Outlook for Windows renders with Word's engine | Layout with tables; no flexbox, grid, `position`, background images without VML, unreliable `margin` and `max-width` on divs |
| Gmail removes the whole `style` block when it contains CSS it rejects or is too large, and its mobile apps ignore it for non-Google accounts | Inline every style that affects layout; treat the `style` block as progressive enhancement |
| Gmail clips messages whose HTML exceeds about 102 KB | Keep markup lean; the clipped part includes the footer and unsubscribe link |
| Images are blocked by default in some clients | Meaningful `alt` text, explicit `width` and `height`, no text baked into images, buttons built from HTML not images |
| Web fonts load in few clients | Choose a system font stack that looks right as the fallback |
| No JavaScript, forms are unreliable | Every interaction is a link to the app |
| Much mail is read on a phone | Single column, about 600 px maximum width, body text 16 px, tap targets at least 44 px high |

Dark mode has three behaviors and the template cannot choose which one it gets:

1. No change (the client keeps the light design).
2. Partial inversion: light backgrounds become dark, dark text becomes light.
3. Full inversion, including already-dark designs (the Gmail app on iOS, classic Outlook on
   Windows), which media queries cannot override.

What works across all three:

- Declare support so clients that honor it apply the template's own colors:

```html
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
```

- Add `@media (prefers-color-scheme: dark)` overrides for clients that support it (Apple Mail
  does; Gmail does not). Client support shifts; caniemail.com is the current matrix.
- Logos and icons: transparent PNG with a light outline or padding plate so a dark logo survives
  on a dark background. Avoid SVG; support is poor.
- Avoid pure `#ffffff` and `#000000` pairs; mid-tones invert less harshly. Never convey state by
  background color alone.
- Check that the button remains readable when the client inverts the text but not the background.

## Preview and test without mailing real users

| Layer | Tool | What it proves |
|---|---|---|
| Local preview | React Email dev server or equivalent | Layout and copy while editing |
| Local capture | Mailpit as the SMTP or API sink in development | The full flow sends the right message; nothing leaves the machine |
| Unit and CI | Render each template with fixture props; assert subject, key link, text part present; snapshot the HTML | A refactor did not break a template or drop a variable |
| End-to-end | Playwright reads the captured message from the sink's API and follows the link | Signup, verification and reset actually work |
| Client rendering | A rendering service (Litmus, Email on Acid) or real accounts in Gmail, Apple Mail, Outlook | Looks right; run on layout changes, not every commit |
| Provider path | The provider's simulator addresses (Resend `delivered@`, `bounced@` and `complained@resend.dev`; SES `success@`, `bounce@` and `complaint@simulator.amazonses.com`) or its sandbox mode | Webhook handling for delivered, bounced and complained events, without real bounces counting against the account |

Guards that prevent the classic incident (staging loaded with production data emails every customer):

- The mail transport is chosen by environment, and production credentials exist only in production.
- In every non-production environment, a recipient guard in `sendEmail()` either rewrites all
  recipients to a team catch-all or drops any address outside an allowlist of domains. Test this guard.
- Scrub or fake email addresses when copying production data.
- Use reserved domains (`example.com`, `.test`) in fixtures and seeds, never plausible real ones:
  bounces from invented addresses damage reputation.

## Send log and delivery status

The outbox table is the send log. At Prototype the provider's dashboard is enough; from Launch
the app owns the record, extended with provider webhooks:

- Subscribe to delivered, bounced, complained and (for inbound) received events. Authenticate
  every call, deduplicate on the provider's event ID, look up by `provider_message_id`, and only
  move status forward (a late `delivered` must not overwrite `bounced`).
- Authentication depends on the provider. Where it signs, verify the signature over the raw
  request body (Resend sends Svix-style signature headers; SES delivers through SNS, whose
  message signature must be checked and whose subscription must be confirmed). Where it does
  not sign (Postmark has offered basic-auth credentials in the webhook URL plus published IP
  ranges; check its current documentation), use a long random credential compared in constant
  time. An unauthenticated bounce endpoint lets anyone suppress any customer's address.
- Store the bounce type and the receiving server's diagnostic text. "550 5.1.1 user unknown" is
  the answer to half of all "I never got the email" tickets.
- Give support an admin view: search by address, see each message with template, time, status
  and reason, plus a resend action that creates a new outbox row with a new key.
- When an address is suppressed, show it in the product ("We could not deliver to this address")
  and let the user correct it. Silent suppression produces lockouts.
- Provider logs have limited retention and are per-vendor; the app's log is the durable record.
  Keep metadata long enough for support and disputes, and keep bodies only if there is a reason;
  retention policy is `0x:privacy-compliance`.
- Never log full tokens or reset links; log the template and the token ID.

## Inbound email and replies

Skip until a feature needs it (reply-by-email to comments or tickets, email-to-create). When it does:

1. Use a separate subdomain (`reply.example.com`) with MX records pointing at the provider's
   inbound service. Never repoint the root domain's MX: that is the company's own mail.
2. Set `Reply-To: reply+{token}@reply.example.com`, where the token is a signed, unguessable
   reference to the thread and recipient. Route on the token, not on the subject or From.
3. The provider posts parsed JSON to a webhook. Authenticate the webhook, respond 200 quickly,
   and process in a job, deduplicating on `Message-ID`.

Traps:

- The From header is forgeable. The token proves "someone who received this notification";
  treat the content as coming from that user only at the trust level of a comment, never for
  privileged actions. Expire tokens.
- Mail loops: ignore messages with `Auto-Submitted` other than `no`, with `Precedence: bulk`,
  `junk`, `list` or `auto_reply`, or with an empty envelope sender (bounce notifications). Set
  `Auto-Submitted: auto-generated` on outgoing notifications, plus `X-Auto-Response-Suppress: All`,
  which Exchange and Outlook honor for out-of-office replies. Never auto-respond to an auto-response.
- Quoted history and signatures: use the provider's stripped-reply field when offered, and keep
  the raw body for when the parser cut too much.
- Attachments: enforce size and type limits and scan them like any upload. HTML bodies are
  untrusted input; sanitize before display.

## Ask the user

- **Which provider, if none is set?** It decides cost, logs and setup effort. Default: Postmark
  or Resend; SES when already on AWS and volume makes price matter.
- **What address and name should mail come from, and who reads replies?** It becomes a
  recognized sender and changing it later costs trust. Default: `Product <notify@notify.domain>`
  with Reply-To set to the support inbox.
- **Will anyone besides engineers edit email copy?** It decides repository templates against
  provider-hosted ones. Default: templates in the repository.
- **How long should sent-message records be kept?** Support wants history, privacy wants less.
  Default: metadata for about a year, no stored bodies.
- **Is reply-by-email needed?** It adds an inbound pipeline and abuse surface. Default: no;
  replies go to the support inbox.
