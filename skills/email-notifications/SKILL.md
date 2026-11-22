---
name: email-notifications
description: Sends transactional email, SMS, push and in-app notifications that arrive, render and are wanted, covering provider setup, SPF, DKIM and DMARC, sender reputation, templates, channel choice and user preferences. Use when emails go to spam or do not arrive, when adding receipt, verification or reset emails, SMS codes, web or mobile push, a notification inbox or preferences, or when an SMS bill explodes.
---

# Email, SMS and push notifications

## Stance

A notification is a message someone else's system agrees to deliver and a person agrees to keep
receiving. Both agreements are revocable: mailbox providers junk senders they do not trust, and
users mute products that interrupt them. Expert work in this area is mostly protecting those two
permissions, and only then writing the send call.

1. **Reputation is an asset that is slow to build and fast to lose.** Authentication, confirmed
   addresses and low complaint rates come before any content work, because filters judge the
   sender before the message.
2. **Separate what must arrive from what may be refused.** Transactional and marketing mail use
   different streams and subdomains so a newsletter complaint never delays a password reset.
3. **Every send goes through one entry point and a durable record.** Feature code states what
   happened; a notification layer decides channel and timing, deduplicates, and logs. Otherwise
   retries double-send and support cannot answer "did they get it?".
4. **Send from a job, keyed by the business event.** The request records intent in its own
   transaction; a worker sends with an idempotency key derived from the event, so a retry or a
   rollback never produces a wrong or duplicate message.
5. **The channel must match the urgency.** In-app and email by default; push for timely personal
   items; SMS only where money, safety or login requires it. Each step up interrupts more and
   is revoked faster.
6. **Any endpoint that sends on request is an abuse target.** Signup, invite, resend and SMS code
   endpoints get rate limits, country allowlists and spend caps before they are public, because
   the product pays for the fraud and the reputation damage.
7. **Fewer notifications win.** Batch, digest, honor quiet hours, and delete types nobody acts
   on. A disabled push permission or a spam complaint is close to permanent.
8. **Measure action and opt-out, not opens.** Open tracking is distorted by privacy features and
   scanners; the product action and the mute rate tell whether a notification earns its place.
9. **Non-production never reaches a real recipient.** A recipient guard in the send function,
   tested, prevents the staging-emails-all-customers incident.

## Route

| If the task is | Read |
|---|---|
| Choosing an email provider, sending a receipt, verification or reset email, structuring the send path, building or fixing templates, Outlook or dark mode rendering, previewing and testing email, a send log for support, receiving replies | `references/transactional-email.md` |
| Setting up SPF, DKIM and DMARC, mail going to spam or not arriving, bounces and complaints, unsubscribe headers, choosing a sending subdomain, warm-up, dedicated IPs, moving DMARC to reject, a blocklisting | `references/deliverability.md` |
| Deciding between email, push, SMS and in-app, adding SMS codes or alerts, an exploding SMS bill or fake signups, the push permission prompt, web push, APNs and FCM, delivery receipts and fallback, WhatsApp or Slack messages | `references/sms-push.md` |
| Notification preferences and settings, an in-app inbox with unread counts, users complaining about too many notifications, digests and batching, duplicate notifications, quiet hours and time zones, notification metrics, Knock or Novu versus building it | `references/notification-system.md` |

Tasks often span two files: a new notification type usually needs `notification-system.md` for
the model and `transactional-email.md` for the template and send path; "emails are not arriving"
starts in `deliverability.md` and often ends in the send log section of `transactional-email.md`.

## Defaults at a glance

Follow what the project already uses first; these apply to greenfield choices.

| Decision | Default | Flips when |
|---|---|---|
| Email provider | Postmark or Resend over the HTTP API | SES when already on AWS and volume makes price matter |
| Streams | Transactional and marketing separated by stream and subdomain (`notify.`, `news.`) | Never merged from Launch on |
| Templates | In the repository (React Email), typed props, HTML plus plain text | Provider-hosted only if non-engineers edit copy often |
| Send path | Outbox row in the business transaction, worker sends, idempotency key from the event | Inline send is acceptable at Prototype behind the same function |
| Tracking | Click and open tracking off on transactional mail | On for the marketing stream if wanted |
| Authentication | Aligned DKIM, custom Return-Path, DMARC record | DMARC `p=none` at Launch, `reject` within months |
| IPs | Provider's shared pool | Dedicated only at steady high volume with someone to manage it |
| Address quality | Confirm email before any other mail; suppress hard bounces and complaints at once | n/a |
| Channels | Email plus in-app | Push for timely personal events; SMS for login codes or money and safety alerts |
| SMS | Managed verification API, country allowlist, per-number and per-IP limits, daily spend cap | n/a |
| Mobile push | Through FCM or a push service for both platforms | Direct APNs for iOS-specific needs |
| Preferences | Categories by channels, stored as sparse overrides; required types cannot be muted | Per-workspace and per-thread mutes for collaborative products |
| Activity email | Batched by a short window; daily digest offered | Instant only for direct, low-volume types |
| Quiet hours | Push and SMS held about 22:00 to 08:00 recipient local time; urgent types bypass | User-configurable at Scale |
| Notification layer | In-house `notify()` plus tables | A notification service at three or more channels with digests and a preference center |

By stage:

- **Prototype**: one provider, one `sendEmail()` or `notify()` function, DKIM set up, a local mail
  sink, the non-production recipient guard. Skip preferences, digests, push and SMS.
- **Launch**: outbox and send log with webhooks, suppression handling, full SPF, DKIM and DMARC
  alignment, separate streams, verified addresses, one-click unsubscribe on marketing mail,
  bounce and complaint alerts, category preferences, abuse limits on every sending endpoint.
- **Scale**: DMARC at reject, reputation monitoring across mailbox providers, batching and
  digests tuned from data, per-type measurement and pruning, a circuit breaker on volume, and a
  review of dedicated IPs and a notification service.

## Before you call it done

1. A test message received in Gmail shows `spf=pass`, `dkim=pass` with the sending domain in
   `header.d`, and `dmarc=pass` in its original source.
2. Transactional and marketing mail leave through different streams and subdomains.
3. Each email has a plain-text part, a specific subject, a preheader, one primary action and a
   Reply-To that someone reads.
4. The send is enqueued in the same transaction as the state change, with an idempotency key
   derived from the business event; running the handler twice sends one message.
5. Time-critical messages have their own priority and an expiry, so a stale code is never sent.
6. Non-production environments cannot reach real recipients, and a test proves the guard.
7. Templates render from fixtures in CI, and were viewed in Gmail, Apple Mail and Outlook on
   Windows in light and dark mode after any layout change.
8. Bounce and complaint webhooks are signature-verified, update the send log, and suppress the
   address; a suppressed user sees that in the product.
9. Marketing and subscribed mail carries `List-Unsubscribe` and `List-Unsubscribe-Post`, the POST
   works without login, and GET does not unsubscribe.
10. No link in any message performs an action on GET.
11. Every endpoint that triggers a send (signup, resend, invite, SMS code) is rate-limited; SMS
    has a country allowlist and a spend cap that fails closed.
12. Push is requested after a soft ask at a moment of value, dead tokens and subscriptions are
    deleted on the provider's error, and tokens are removed on logout.
13. Required notification types are flagged in one registry; everything else respects
    per-category preferences and has a no-login opt-out.
14. Bursts are batched or capped, the actor is not notified of their own action, and reading an
    item in one channel cancels pending sends in the others.
15. Times and language in messages use the recipient's time zone and locale.

## Not this skill

- Lifecycle, newsletter and marketing email strategy and copy → `0x:growth-marketing`
- Dunning emails and failed-payment recovery logic → `0x:payments-billing`
- Magic links, OTP login and reset-flow security → `0x:auth-identity`
- DNS record mechanics beyond the mail records → `0x:web-networking`
- Anti-spam and consent law for marketing and cold email → `0x:privacy-compliance`
- The queue and retry machinery that sends in the background → `0x:backend-architecture`
