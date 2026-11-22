# Webhooks, inbound and outbound

Read this when: receiving events from another service (a payment provider, a source host, an
email provider), or delivering events from the product to customers' endpoints.

A webhook is an unauthenticated public POST endpoint (inbound) or a server that makes requests
to URLs chosen by strangers (outbound). Both are security boundaries first and integration
features second. Delivery is at-least-once, unordered and sometimes late in both directions;
every design choice below follows from that.

## Inbound: the receiver

The handler does four things and nothing else: verify, deduplicate and store, acknowledge, and
hand off. Business logic runs in a worker.

```ts
import { createHmac, timingSafeEqual } from "node:crypto";

export async function POST(req: Request) {
  const raw = await req.text();                       // exact bytes; never re-serialize parsed JSON
  const ts = req.headers.get("x-provider-timestamp") ?? "";
  const given = Buffer.from(req.headers.get("x-provider-signature") ?? "", "hex");
  const expected = createHmac("sha256", process.env.PROVIDER_WEBHOOK_SECRET!)
    .update(`${ts}.${raw}`).digest();
  const fresh = Math.abs(Date.now() / 1000 - Number(ts)) <= 300;
  if (!fresh || given.length !== expected.length || !timingSafeEqual(given, expected)) {
    return new Response("invalid signature", { status: 401 });
  }
  const event = JSON.parse(raw);
  await storeEventAndEnqueue(event.id, event.type, raw); // unique on (provider, event id)
  return new Response(null, { status: 204 });
}
```

The header names and the signed string differ per provider; the structure does not.

### Verify signatures and reject replays

- **Use the provider's SDK verification function when one exists.** It encodes their exact
  scheme (signed string, encoding, multiple signatures during rotation). Hand-roll only from
  their documentation, as above.
- **Verify over the raw body bytes.** The most common failure is a framework or middleware that
  parses JSON first; re-serializing changes whitespace and key order and the signature never
  matches. In a Next.js route handler read `await req.text()`; in Express mount a raw-body
  parser on that route only.
- **Compare in constant time** with `timingSafeEqual`. It throws when lengths differ, so check
  length first.
- **Reject stale timestamps** (5 minutes is a common tolerance; use the provider's value) when the
  timestamp is part of the signed content; an unsigned timestamp protects nothing. This blocks
  replay of a captured request later.
- **Deduplicate on the provider's event ID** with a unique constraint. The timestamp window
  limits replays; the ID makes them harmless.
- **One secret per endpoint and per environment**, stored as a secret, never shared between
  test and live. Signature failures right after a deploy are usually the wrong environment's secret.
- **The route is public**: exempt it from session auth and CSRF middleware, and nothing else.
  Do not rely on source-IP allowlists as the only check; ranges change. Asymmetric schemes
  (a provider's public key or JWKS) follow the same structure with a verify call.
- **Never act on an unverified payload**, including "just logging it" into a table that other
  code later trusts.

### Acknowledge fast, process asynchronously

Sequence: verify, insert the raw event into an inbox table (unique on provider and event ID,
`ON CONFLICT DO NOTHING`), enqueue or let a worker poll the inbox, return 2xx. Target well under
a second.

Providers time out after seconds (the exact figure varies) and treat a timeout as failure. Slow
handlers cause retries, retries arrive while the first attempt is still running, and after
enough failures many providers disable the endpoint. Responding before doing the work removes
that whole class.

| Situation | Respond |
|---|---|
| Verified and stored (or already stored: duplicate) | 2xx |
| Event type not handled | 2xx. A non-2xx makes the provider retry forever something that will never succeed |
| Bad signature or stale timestamp | 400 or 401, and count it in metrics |
| Could not store (database down) | 5xx, so the provider retries. The only case for 5xx |
| Processing fails later in the worker | Not the provider's concern: retry from the inbox, alert on dead letters |

On serverless, work started after the response is returned may be frozen or killed. Either
enqueue before responding or use the platform's explicit post-response hook (`waitUntil`, or
`after` in Next.js); a bare un-awaited promise is lost work. Keep the raw payload in the inbox:
it allows reprocessing after a bug fix without asking the provider to resend. Set a retention
for it, since payloads often contain personal data.

### Process idempotently, out of order, after delays

Assume every event may arrive twice, in the wrong order, hours or days late, or interleaved with
a newer one being processed by another worker.

- **Treat the event as a signal, not as the data**, whenever correctness matters: on
  `subscription.updated`, fetch the subscription from the provider's API and write that state.
  The fetch returns current truth, so order and duplication stop mattering. This costs one API
  call per event and is the default for billing and entitlement state.
- **If using the payload directly**, guard against going backward: store the object's version
  or the event's creation time with the row and ignore events older than what is stored
  (`UPDATE ... WHERE last_event_at < $1`). Timestamps with one-second resolution tie; prefer a
  provider sequence or version when offered.
- **Write handlers as upserts and guarded state transitions**: `updated` may arrive before
  `created`, so the handler for either creates the row if missing; a transition that does not
  apply to the current state is ignored, not an error.
- **Serialize per object**: two events for the same object processed concurrently can interleave
  writes. Take a row lock or a per-object advisory lock, or key the queue by object ID.
- **Side effects need their own idempotency**: "send the receipt email" is guarded by a unique
  record per (event or object, effect), not by the inbox dedup alone, because a worker can crash
  after the send and before marking the event done.
- **Late events**: an event about a deleted or long-finished object must be a no-op.

Payment-provider specifics (which events drive entitlements, checkout completion) are in
`0x:payments-billing`, `checkout-integration.md` and `subscriptions.md`.

### Reconcile by polling

Webhooks get lost: an outage longer than the provider's retry window, a disabled endpoint, a
bad deploy that returned 2xx without storing, a provider incident. A system whose state depends
on webhooks alone drifts and nobody notices until a customer does. Mandatory at Launch for
anything involving money or access.

- **Scheduled reconciliation**: every few minutes to hourly, list objects changed since the last
  successful run (with an overlap of several minutes, relying on idempotent upserts) and apply
  the same handler logic. Where the provider has an events listing endpoint, page through it
  from the last seen event; retention there is limited, so run it more often than that window.
- **On-demand reconciliation** at decision points: before granting or revoking something
  valuable based on stale local state, re-fetch.
- **A full sweep** (daily or weekly) over open or active objects catches what incremental runs miss.
- **Alert on silence**: no events from a normally chatty provider for N hours is an incident,
  as is a rising signature-failure rate or a growing inbox backlog.
- After any receiver outage, use the provider's dashboard replay or run reconciliation before
  declaring recovery.

## Outbound: sending webhooks to customers

Decide build versus buy first. A correct sender is a queue, a retry scheduler, signing, an SSRF
boundary, a delivery log, an endpoint-management UI and customer support for all of it. A
hosted or self-hostable delivery service (Svix, Hookdeck Outpost, Convoy and similar; check the
current license and pricing, since some are source-available, not open source) is a reasonable
default at Launch if webhooks are a feature customers pay for; build in-house when volume is
small and the job queue already exists. Skip outbound webhooks entirely at Prototype.

### Signing, retries and delivery logs

- **Emit through an outbox.** Insert the event row in the same transaction as the state change,
  and let a worker deliver from the table. Sending inline from the request loses events on a
  crash and sends events for transactions that later roll back.
- **Sign every delivery with HMAC-SHA256 over an ID, a timestamp and the exact body**, with a
  per-endpoint secret. Follow the Standard Webhooks conventions rather than inventing a scheme:
  headers `webhook-id`, `webhook-timestamp`, `webhook-signature`; signed content
  `{id}.{timestamp}.{body}` with the timestamp in Unix seconds; signatures prefixed with a scheme
  version (`v1,<base64>`), and several space-separated signatures allowed in the header to
  support rotation. Customers then get ready-made verification libraries. Generate each secret
  from a CSPRNG: 24 to 64 random bytes, shown base64-encoded with the `whsec_` prefix those
  libraries expect (they strip the prefix and decode the rest to get the HMAC key).
- **The `webhook-id` is the event's stable ID and stays the same across retries**; it is the
  consumer's deduplication key. Document that delivery is at-least-once and unordered.
- **Retry on any non-2xx, timeout or connection error** with exponential backoff and jitter over
  a long window: a handful of attempts in the first hour, then spaced out to cover one to three
  days in total. Publish the schedule. Honor `Retry-After` on 429 and 503 within reason.
- **Per attempt**: timeout of 10 to 15 s, success is any 2xx, do not follow redirects, cap the
  response bytes read, send a descriptive `User-Agent`.
- **Isolate endpoints from each other.** One slow or dead customer endpoint must not delay the
  rest: limit concurrency per endpoint and keep retries in a delayed queue, not blocking a
  worker with sleeps.
- **Disable an endpoint after sustained failure** (for example, every attempt failing for
  several days), notify the owner by email and in the dashboard, and let them re-enable and replay.
- **Delivery log per attempt**: event ID, endpoint, attempt number, request timestamp, response
  status, duration, truncated response body, next retry time. Retain 7 to 30 days. Expose it
  to the customer with a manual resend; this is the difference between self-service debugging
  and a support ticket for every missed event.
- **Payload size cap** (tens to low hundreds of kilobytes); link to large data instead of embedding it.

### Customer URLs must not reach internal networks

The sender makes requests to arbitrary URLs from inside the infrastructure: this is server-side
request forgery by design unless constrained. The targets are cloud metadata services, internal
admin ports, databases and localhost services.

1. Require `https://`; reject URLs with credentials, and non-default ports unless there is a reason to allow them.
2. Resolve the hostname and reject the delivery if **any** resolved address is not public:
   loopback (`127.0.0.0/8`, `::1`), RFC 1918 private ranges, link-local (`169.254.0.0/16`, which
   contains the metadata address `169.254.169.254`, and `fe80::/10`), carrier-grade NAT
   (`100.64.0.0/10`), unique-local IPv6 (`fc00::/7`), unspecified (`0.0.0.0/8`, `::`), multicast
   and reserved addresses, and the IPv4-mapped (`::ffff:0:0/96`) and NAT64 (`64:ff9b::/96`) forms
   of all of these. A hand-kept blocklist goes stale: classify each address with a maintained IP
   library and deliver only to what it reports as global unicast.
3. **Connect to the address that was validated.** Validating the name and then letting the HTTP
   client resolve again allows DNS rebinding: the second lookup returns an internal address. Pin
   the resolved IP for the connection (keeping the hostname for TLS and `Host`), or do the check
   in a custom lookup or agent used by the request itself.
4. Do not follow redirects; a public URL can redirect to an internal one.
5. Validate at registration and again at every delivery; DNS changes after registration.
6. Truncate and sanitize what the delivery log shows of the response, so the log cannot be used
   to read from a target.

Defense in depth, which becomes the primary control at Scale: send from workers in a network
segment with no route to internal services, or through an egress proxy that enforces the address
rules. Parsing tricks (decimal or octal IP forms, mixed encodings) defeat string checks, which is
why the check must be on resolved addresses, not on the URL text. The general SSRF class is in
`0x:web-security`, `vulnerability-classes.md`.

### Endpoint management for customers

What a customer needs to run an integration without contacting support:

- Create, edit, disable and delete endpoints; several endpoints per account.
- Subscribe each endpoint to chosen event types. Default new endpoints to an explicit selection,
  not "all events", or every event type added later lands on consumers that never asked for it.
- A signing secret per endpoint, generated server-side and retrievable or shown once.
  **Rotation with overlap**: on rotate, sign each delivery with both old and new secrets for a
  fixed period (24 hours is typical) so the customer can deploy the new one without dropped
  deliveries; then expire the old one.
- A "send test event" button, the delivery log with payloads and responses, resend for one
  delivery, and replay for a time range after their outage.
- An event catalog in the docs: every type, its payload schema and an example.
- Endpoint changes are sensitive: restrict them to admins and record them in the audit log. An
  attacker who adds an endpoint receives a copy of the account's data stream.

### Payload design and versioning

| Style | Payload | Strengths | Costs |
|---|---|---|---|
| Fat (snapshot) | The full resource as of the event | No callback needed; works for no-code tools and consumers without API access | Stale by the time it is processed; order matters; payload shape is a versioned contract; sensitive data sits in customers' logs |
| Thin (notification) | Event type plus resource ID | Always-current data via the API; no ordering problem; small; authorization enforced at fetch time | One API call per event; requires API credentials; a burst of events becomes a burst of API load |

Default: fat events whose `data` is the same representation the API returns for that resource,
since most consumers want the data and many use tools that cannot call back. Choose thin when
payloads are sensitive or large, or when consumers must always act on current state. Either way,
give events a constant envelope:

```json
{ "id": "evt_01JD4...", "type": "invoice.paid", "created_at": "2026-11-22T09:30:00Z",
  "api_version": "2026-06-01", "data": { "id": "inv_123", "status": "paid" } }
```

- **Name types `resource.past_tense_verb`** (`invoice.paid`, `member.removed`). Never change what
  an existing type means or when it fires; add a new type instead.
- **Payloads follow the same evolution rules as API responses**: additive only. Consumers must
  ignore unknown fields and unknown event types; say so in the docs from day one.
- **Pin the payload version per endpoint** (recorded when the endpoint is created, upgradable
  by the customer), and render the payload through the same version layer as the API
  (`versioning-evolution.md`). The version is a property of the endpoint, not of the event.
- A new event type is a non-breaking addition only if endpoints subscribe explicitly.

## Ask the user

- **Which providers' events change money or access in the product?** Those need the fetch-on-event
  pattern and reconciliation before Launch. Default: treat payment and identity providers this way.
- **Do customers need webhooks now, or would polling an `updated_since` listing do?** Outbound
  webhooks are an operational commitment. Default: defer until a customer integration needs them.
- **Build the sender or use a delivery service?** Money versus maintenance. Default: a service if
  webhooks are a selling point; in-house on the existing job queue if they are a minor feature.
- **How long should failed deliveries be retried and logs kept?** Affects storage and what support
  can promise. Default: retry for about 3 days, keep logs 30 days.
- **May payloads contain personal or sensitive data?** A fat event copies that data onto servers
  the customer runs and into their logs. Whether that is allowed depends on the contracts with
  customers and on the data-protection rules covering the product's users, which differ by
  jurisdiction (`0x:privacy-compliance`). If it is not, send thin events. Default: fat events
  without secrets, payment details, or health and similarly sensitive data.
