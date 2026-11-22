# Email deliverability

Read this when: configuring a sending domain, mail lands in spam or does not arrive, bounce or
complaint rates rise, or a DMARC policy, dedicated IP or blocklist question comes up.

## What decides inbox placement

In order of weight for a small sender: (1) authentication that passes and aligns, (2) complaint
rate, (3) bounce rate and spam-trap hits, (4) engagement (opens, replies, "not spam" versus
deletes), (5) content and links. Founders usually start at (5) and rewrite subject lines. Start
at (1) and work down; content is rarely the cause when authentication or list quality is wrong.

## Authenticate: SPF, DKIM, DMARC

DMARC passes when **either** SPF **or** DKIM passes **and** the passing domain aligns with the
domain in the visible From header. Alignment is the part people miss.

| Mechanism | Checks | Domain it authenticates | Aligns when |
|---|---|---|---|
| SPF | Sending IP is listed by the envelope sender's domain | Return-Path (MAIL FROM), not the From header | Return-Path domain shares the organizational domain with From |
| DKIM | Signature verifies against a public key in DNS | The `d=` domain of the signature | `d=` shares the organizational domain with From |
| DMARC | SPF or DKIM passed with alignment | The From header domain | n/a; publishes policy and report address |

Setup sequence for a sending subdomain `notify.example.com`:

1. Add the domain at the provider and publish the DKIM records it gives (usually CNAMEs, so the
   provider can rotate keys). This makes `d=notify.example.com`. Without it the provider signs
   with its own domain: DKIM passes but does not align.
2. Configure the custom Return-Path or MAIL FROM domain (for example `bounce.notify.example.com`
   as a CNAME, or MX plus TXT on SES). Without it the Return-Path is the provider's domain: SPF
   passes for the provider and does not align.
3. Publish DMARC on the organizational domain:

```text
_dmarc.example.com.  TXT  "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
```

4. Send a message to a Gmail account, open "Show original" and require all three lines:
   `spf=pass`, `dkim=pass header.d=notify.example.com`, `dmarc=pass`.

```bash
dig +short TXT example.com | grep spf1
dig +short TXT _dmarc.example.com
dig +short CNAME s1._domainkey.notify.example.com   # selector name comes from the provider
```

Traps:

- **Two SPF records on one name** make SPF a permanent error. Merge into one `v=spf1` record.
- **SPF's limit of 10 DNS lookups**: each `include`, `a`, `mx` and `redirect` counts, nested
  ones too. Exceeding it fails SPF for everything. Putting each sender on its own subdomain
  avoids the pile-up on the root.
- The root domain's SPF record only needs the services that use the root as envelope sender
  (typically the company mailbox provider). The app provider's `include` belongs where its
  Return-Path lives.
- Forwarding breaks SPF (the forwarder's IP is not listed) while DKIM survives. Aligned DKIM is
  therefore the mechanism to rely on; treat SPF alignment as the backup.
- Use 2048-bit DKIM keys. If the DNS host rejects the long TXT value, split it into quoted
  strings or use the provider's CNAME form.
- Relaxed alignment (the default) accepts any subdomain of the same organizational domain. Do
  not set strict alignment (`aspf=s`, `adkim=s`) without a reason.
- A DMARC record on a subdomain overrides the organizational one for that subdomain; `sp=` on
  the organizational record sets the policy for subdomains without their own.

Mailbox providers publish sender requirements (Google and Yahoo since 2024, Microsoft's consumer
mail since 2025): every sender needs SPF or DKIM; senders of roughly 5,000 or more messages a
day to their users need SPF, DKIM and a DMARC record with alignment, one-click unsubscribe on
marketing mail, and a low complaint rate. Meet the bulk rules from Launch regardless of volume;
the threshold is counted per receiving provider and crossing it is not announced.

DNS record mechanics beyond these mail records are in `0x:web-networking`.

## Subdomains and warm-up

- Send application mail from a subdomain (`notify.example.com`), marketing from another
  (`news.example.com`), and keep people's mailboxes on the root. Reputation is tracked per
  domain and per subdomain, so a newsletter complaint spike is partly contained and the
  founders' own email keeps working.
- Stay under the brand's registered domain. A lookalike (`example-mail.com`) trains users to
  trust lookalikes and starts with no reputation. Separate cold-outreach domains are a sales
  tactic with its own risks, outside this file.
- Visible addresses, link domains and image hosts all carry reputation. Do not use public URL
  shorteners in email.

Warm-up applies to a new domain, new subdomain or new dedicated IP: receivers throttle or junk
volume from senders with no history.

- On a provider's shared pool the IPs are warm, but the domain is not. Domain warm-up still applies.
- Transactional mail that grows with signups warms itself. The danger is a step change: a
  launch announcement to an imported list, or a migration that moves all volume in one day.
- For a step change, ramp: start with a few hundred messages a day to the most recently engaged
  recipients, roughly double every few days while bounces, deferrals (4xx) and complaints stay
  flat, and hold or step back when they rise. Expect two to six weeks to reach six-figure daily
  volume (a rule of thumb; follow the provider's schedule for a dedicated IP).
- Migrating providers: move streams one at a time, lowest-risk first, over days, and keep the
  old provider's DNS records until the old volume is zero.

## Keep the list clean at the source

- **Confirm every address before sending anything else to it.** Until the user clicks the
  verification link, the only mail that address receives is the verification message, with a
  cap on resends. This single rule prevents typo bounces, spam-trap hits and most signup abuse.
- At the form: syntax validation, an MX lookup on the domain, and a "did you mean gmail.com?"
  hint for common typos. Do not reject on strict regexes; valid addresses are stranger than expected.
- Signup forms get abused to bomb third parties with confirmation mail (the victim then reports
  the sender as spam). Rate-limit signups per IP and per address, add bot protection when abuse
  appears, and keep the confirmation email free of any attacker-supplied text.
- Never import a purchased, scraped or years-old list. For a legitimately old list, run it
  through a verification service and re-confirm in small batches before any normal send.
- Paid address-verification APIs earn their cost for imports and for high-value signups, not for
  every form submission when confirmation mail already exists.
- Invitations ("add teammates by email") are sends to unverified addresses supplied by a user.
  Rate-limit them per account, stricter for new and free accounts, and count their bounces.

## Bounces, complaints and suppression

| Event | Meaning | Action |
|---|---|---|
| Hard bounce (5xx, unknown user or domain) | Address is permanently bad | Suppress immediately for all streams; flag the account in the product |
| Soft bounce (4xx, mailbox full, temporary) | May work later | Provider retries; suppress after repeated soft bounces over several days |
| Block bounce (policy, reputation, content) | The receiver rejected the sender, not the address | Do not suppress the address; investigate the sender problem |
| Complaint (user pressed "spam") | Recipient does not want this | Stop all non-essential mail to them at once; treat as an unsubscribe |
| Unsubscribe | Opt-out of a category | Record in preferences; effective immediately |

- Providers keep their own suppression list and refuse sends to it. Mirror the events into the
  app database through webhooks so the product knows, and check suppression before enqueueing.
- Suppression is keyed by address, not user ID, and survives account deletion as a hash where
  privacy rules require minimization.
- Gmail does not send per-recipient complaint notifications; complaints from Gmail users show
  only as an aggregate rate in Google Postmaster Tools. A webhook complaint count of zero is not
  evidence of a clean stream.
- Password resets and security alerts to an address that complained: still send (the user asked
  for them), unless the address hard-bounced.
- Thresholds: keep hard bounces under about 2% of sends (rule of thumb) and complaints under
  0.1%; mailbox providers treat 0.3% as the line where placement degrades. Sending providers
  suspend accounts at their own published thresholds; check them and alert well below.
- Alert on rate per stream per day, with a minimum volume so three sends and one bounce do not page.

## One-click unsubscribe

Required on marketing and subscribed mail by the bulk-sender rules; not required on strictly
transactional mail. Add both headers and make sure they are covered by the DKIM signature:

```text
List-Unsubscribe: <https://example.com/unsubscribe/TOKEN>, <mailto:unsubscribe@example.com?subject=TOKEN>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

- The URL must accept a `POST` (body `List-Unsubscribe=One-Click`) and unsubscribe with no login,
  no cookie, no confirmation step and no redirect. The token identifies recipient and category.
- A `GET` on the same URL shows a page with a confirm button. Do not unsubscribe on GET: link
  scanners would unsubscribe everyone.
- Also show a visible unsubscribe link in the body. Hiding it converts unsubscribes into spam
  complaints, which cost far more.
- Honor the request immediately in the app; the outer limit providers state is two days.
- Most providers add these headers on broadcast streams. Verify in a received message's source
  rather than assuming.

Consent and anti-spam law for marketing mail is `0x:privacy-compliance`.

## Monitor and diagnose

Set up at Launch: Google Postmaster Tools for the sending domain (spam rate, authentication and
compliance status), the provider's bounce and complaint dashboards with alerts, and a mailbox for
DMARC aggregate reports (or a report-parsing service; raw XML is not readable at any volume).
At Scale add Microsoft SNDS (for dedicated IPs) and periodic seed-list placement tests.

| Symptom | Likely cause | Check, then fix |
|---|---|---|
| Not in inbox or spam, provider says delivered | Corporate gateway quarantine, or a recipient-side rule | Ask the recipient's IT; add aligned DKIM; ask to be allowlisted |
| Provider shows bounce with 550 5.7.x and "policy" or "authentication" | DMARC or SPF failure, or blocklisting | Read the diagnostic text; verify the three passes in message source |
| Spam at Gmail only | Domain reputation or complaint rate at Gmail | Postmaster Tools spam rate; cut volume to engaged recipients |
| Spam at Microsoft only | IP or domain reputation there, often on a new sender | Provider support for shared IPs; Microsoft's sender support form |
| Spam everywhere, new domain | No reputation and a volume jump | Warm up; send only confirmed addresses |
| Fine yesterday, spam today | A burst (bug loop, big campaign), a compromised form, or a DNS change | Send log volume by hour; diff DNS; check blocklists |
| Deferred (4xx) and slow | Receiver throttling a sender it does not know yet | Reduce rate; let the provider retry; do not resend manually |
| Gmail Promotions tab | Marketing-looking content; it is still the inbox | Usually leave it; for transactional mail remove promotional blocks and heavy imagery |

Diagnosis order: read the raw headers of a received copy (`Authentication-Results`), then the
provider's event for a failed message, then reputation dashboards, and content last. A
mail-tester style score is a lint, not evidence of placement.

## DMARC from none to reject

`p=none` only monitors; anyone can still spoof the domain. Moving to `reject` protects customers
from phishing in the brand's name and is increasingly expected by enterprise buyers.

1. Publish `p=none` with `rua`. Collect two to four weeks of aggregate reports.
2. Inventory every source sending as the domain: app provider, marketing tool, company
   mailboxes, helpdesk, CRM, invoicing, calendar and form tools. Each legitimate one needs
   aligned DKIM (preferred) or aligned SPF. The forgotten ones are the helpdesk and the billing tool.
3. When legitimate sources pass at close to 100%, set `p=quarantine`, optionally with `pct=25`
   as a ramp, watch reports for a week or two, then raise.
4. Set `p=reject`. Keep `rua` forever; a new tool added next year shows up there first.
5. For domains that never send mail (parked domains, old brands) publish `v=spf1 -all` and
   `v=DMARC1; p=reject` at once.

Traps: indirect flows (forwarding, mailing lists that modify the message) fail DMARC through no
fault of the sender and will never reach 100%; judge by the sources under the company's control.
Reports sent to an address on another domain need that domain to publish an authorization record,
which report services provide. Skip BIMI until Scale: it requires enforcement policy first and,
for most mailbox providers, a paid mark certificate.

## Shared or dedicated IPs

Default: the provider's shared pool. A dedicated IP has no reputation until the sender builds
it and loses it when volume dips, so low or bursty volume performs worse on a dedicated IP than
on a well-run pool.

Move to dedicated IPs only when all hold: volume is steady and on the order of 100,000 or more
messages a month to consumer mailboxes (rule of thumb; follow the provider's own threshold),
someone will run a warm-up and watch reputation, and there is a reason (a noisy shared pool
proven by evidence, a customer contract, or separation of high-volume streams). When moving,
take at least two IPs or keep transactional and marketing on separate ones, and warm each.

## Recovering from a blocklisting or reputation collapse

1. **Stop the cause before asking for anything.** Pause the stream that triggered it (usually
   marketing or invitations); keep verification and reset mail flowing if they still deliver.
2. Identify the list from the bounce text, then check the major ones (Spamhaus, Barracuda,
   SpamCop, and the mailbox providers' own internal blocks, which no public lookup shows).
3. Determine IP or domain. A shared IP is the provider's to delist: open a ticket with a sample
   bounce. A domain listing or a dedicated IP is the sender's.
4. Find the root cause in the send log: an abused signup or invite form, an old list, a bug
   loop, a compromised API key. Rotate keys if sending volume is unexplained.
5. Fix it, then file the delisting request stating what happened and what changed. Requests
   without a fix get one chance; repeat listings escalate in duration.
6. Resume as a warm-up: engaged recipients first, low volume, ramp over weeks. Domain reputation
   at the large mailbox providers recovers in weeks of clean sending, not on request.

Do not switch to a fresh domain or IP to escape. Filters link the new identity to the old
content and links, and the behavior matches how spammers operate.

## Ask the user

- **Which subdomains may be used for sending, and who controls DNS?** Records must be published
  before anything works. Default: `notify.` for application mail, `news.` for marketing.
- **Which other tools send mail as the domain?** Each must be aligned before DMARC enforcement
  or its mail will be rejected. Default: assume the company mailbox, helpdesk and billing tool
  do, and confirm from DMARC reports.
- **Is there an existing list, and where did it come from?** An unverified import is the usual
  cause of a reputation collapse. Default: do not send to it until verified and re-confirmed in batches.
- **How fast should DMARC reach reject?** Faster protects the brand sooner but risks dropping
  mail from a forgotten tool. Default: none at Launch, reject within two to three months.
- **Is a dedicated IP wanted?** It costs money and attention. Default: no, until steady high volume.
