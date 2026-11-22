# Bot and abuse defense

Read this when: login, signup, reset, trials, invitations or sharing features are attacked or
exploited (fake signups, credential stuffing, free-tier farming, spam sent through the product),
or a host, registrar, email provider or browser blocklist has flagged the product for abuse.

Abuse is economics. The aim is not to stop every attempt but to make an attempt cost more than
it returns, so the attacker moves on. Honest users pay for friction too: add it where signals or
the action justify it, and measure the effect.

## Rate limits on auth endpoints

Starting values, all rules of thumb to tune from logs:

| Endpoint | Key | Limit | On exceed |
|---|---|---|---|
| Login | Account identifier as submitted, normalized | 5 failures, then growing delay; about 10 per 15 minutes | Throttle and require a challenge; no hard lockout |
| Login | IP (IPv6 aggregated to /64) | 20 to 50 attempts per 15 minutes | 429, then a challenge |
| Login | Global failure ratio | Several times the normal baseline | Turn challenges on for all logins |
| Signup | IP and device token | 3 to 5 per hour | Challenge, then block |
| Reset, magic link, verification email | Target address | 3 per hour, 10 per day | Drop silently with the usual response |
| Reset, magic link, verification email | IP | 10 per hour | 429 |
| Code verification (email, TOTP, recovery) | Account | 5 per code, 10 per hour | Invalidate the code and back off |
| SMS send | Number, prefix, country, global budget | Tight, with a country allowlist | Stop sending and alert |

- **Hard lockout is a weapon for the attacker.** Anyone can lock any account by failing on
  purpose. Throttle, delay and challenge instead.
- **Key on the submitted identifier whether or not it exists.** Limiting only real accounts
  reveals which are real and leaves the rest unprotected.
- **IP limits stay loose.** Offices, campuses, mobile carriers and VPN exits put thousands of
  honest users behind one address. An IPv6 user controls at least a /64, so count per /64.
- **Take the client IP from the hop the infrastructure controls**: the platform's own header or
  the entry appended by the trusted proxy. The leftmost `X-Forwarded-For` value is whatever the
  client typed, and trusting it defeats every per-IP limit (`0x:web-networking`).
- **Count in a shared store.** In-memory counters reset per serverless instance. Use Redis, a
  Postgres table at low volume, or the edge provider's rate limiting for the per-IP layer.
  Per-account limits stay in the app, where the account is known.
- **Cover every door:** mobile and legacy login APIs, the OAuth token endpoint, MFA and
  recovery-code verification, and GraphQL, where one request can batch hundreds of login
  mutations through aliases (count operations, not requests).
- Email and SMS sends are limited for a second reason: attackers use them to bomb a victim's
  inbox, or to pump paid SMS to numbers they profit from, on the product's bill and reputation.
- Answer 429 with `Retry-After` and wording that does not say which limit tripped. If the
  limiter's store is down, auth endpoints fall back to a conservative in-process limit.

General API rate limiting: `0x:api-design`.

## Signup throttling by reputation

Collect signals at signup and store them in a row per signup. They also feed clustering later.

| Signal | Cheap source | Reading |
|---|---|---|
| IP type and velocity | ASN lookup, the edge provider's bot score | Datacenter and proxy ranges raise risk but prove nothing: privacy VPNs and corporate egress look the same |
| Device | A signed first-party cookie set before signup; a commercial fingerprint at Scale | Many accounts from one device |
| Email domain | Disposable-domain lists (stale quickly, so a signal only), no MX record, a domain registered days ago, many signups on one unfamiliar domain within an hour | Throwaway identities |
| Canonical email | For Gmail, drop dots and anything after `+` before counting | One mailbox posing as many. Count on it; never use it as the login identifier |
| Shape | Random-looking local parts, sequential names, identical time from form load to submit | Automation |

Device cookies and fingerprinting carry consent implications in some jurisdictions
(`0x:privacy-compliance`).

Respond in steps rather than with a wall:

1. Allow.
2. Allow with limits: nothing costly or outbound until the email is verified, and lower quotas.
3. Challenge: CAPTCHA, phone verification or a card on file.
4. Block, with a generic error.

A hard block tells the attacker in one request which signal caught them; degraded service wastes
their time. At Launch a small additive score with two thresholds in code is enough; buy risk
scoring at Scale. Track signup-to-activation by segment: abusive cohorts never activate, or go
straight to the one costly feature. Requiring a work email for B2B trials trades conversion for
quality and is the user's decision.

## Credential stuffing

Signature: many accounts tried with one or two passwords each, from thousands of IPs that each
send a handful of requests (residential proxies), so per-IP limits see nothing. The login
failure ratio rises, and a small share succeeds because people reuse passwords.

Defenses, most effective first:

1. MFA and passkeys: the only complete fix. Require them for high-value roles, promote them to
   everyone.
2. New-device challenge: a correct password from a browser with no prior device cookie for that
   account gets an email code before a session is issued. Stuffing supplies correct passwords
   and rarely the mailbox.
3. Breach check at login: when the password that just verified is in the breach corpus, require
   the email code and then a password change (`passwords-mfa-passkeys.md`).
4. A switchable invisible challenge on the login form, enabled by the failure-ratio trigger.
5. No user enumeration, so lists cannot be validated cheaply (`auth-architecture.md`).
6. At Scale: TLS and device fingerprint velocity from the edge provider, or a bot-management
   product.

After an attack, find every account with a successful login from the attacking sources (IPs,
ASNs, user agents, fingerprints, time window), revoke their sessions, force resets, notify the
users and review what changed (`account-recovery.md`). Regulators often treat successful
stuffing as a personal-data breach, so check notification duties (`0x:privacy-compliance`).

## Alerts and anomalous sign-ins

Emit counters for login success and failure (with reason), signup, reset request, MFA failure,
challenge shown and passed, throttle hits, and auth email and SMS sends by type.

| Alert | Starting condition |
|---|---|
| Stuffing or brute force | Login failures above 3 to 5 times the trailing baseline for 5 to 10 minutes, or a failure ratio near half when normal is far lower |
| Signup attack | Signups per hour several times baseline, or the verification rate collapsing |
| Email or SMS bombing | Reset or code sends spiking; SMS spend above the daily budget |
| Takeover wave | Many accounts with successful logins from a new network or country, or a spike in new-device notices |
| Staff account | Every new-device sign-in to an admin or staff account |

Page a person only for sustained spikes and send the rest to a daily digest
(`0x:site-reliability`).

Per-user anomalies: a new device together with a new country or network triggers the email
challenge and a notice. "Impossible travel" (two sign-ins too far apart for the elapsed time) is
a weak signal alone: VPNs, mobile carriers and corporate egress produce it daily, and IP
geolocation is rough. Weight it; do not block on it.

Log per auth event: time, user ID if known, a hash of the submitted identifier, IP, ASN,
country, user agent, device ID, method, result and reason. Never the password, not even on
failure: failed attempts are full of real passwords typed into the wrong field or site.

## CAPTCHA and challenges

A CAPTCHA costs conversion, excludes some people with disabilities (`0x:accessibility`), ships a
third party's script and data flow, and is solved by farms and models for a fraction of a cent.
It raises the attacker's cost and is not a wall.

| Where | Default |
|---|---|
| Signup | An invisible or managed challenge (Cloudflare Turnstile, hCaptcha, reCAPTCHA) once signups cost money or send email; otherwise only when an attack starts |
| Login | Off; on per account or IP after failures, or globally on the failure-ratio trigger |
| Reset and magic-link request | Invisible challenge, since each request sends an email |
| Card entry | Card-testing defense: `0x:payments-billing` |
| Invite and contact forms | When spam appears |

- Verify the token on the server in the same request that performs the action, check the
  hostname and action it reports, and treat it as single-use with a lifetime of minutes. A form
  left open needs a fresh token.
- Decide the failure policy: when the challenge provider is down, proceed with tighter limits.
- Keep every challenge behind a feature flag so it can be enabled per endpoint within minutes.
- Cheaper layers come first: email verification, a honeypot field with a minimum time-to-submit
  (stops only naive bots, costs nothing), rate limits, proof-of-work widgets. Native apps use
  platform attestation instead of CAPTCHA.

## Free tiers and trials

Ask what a free account lets someone extract: compute (mining on build and hosting products),
model tokens, outbound email or SMS, storage and bandwidth, the domain's reputation (phishing
pages, redirects), referral or signup credit, or an endless trial. Abuse stops when making an
account costs more than one account yields.

| Lever | How |
|---|---|
| Raise the cost of an account | Gate costly or outbound features behind stronger identity in steps: verified email, phone, a card on file, payment history or account age |
| Lower the yield | Hard daily quotas on free use; a global daily budget for free usage with an alert and a kill switch |
| Delay the yield | Credits and limits that unlock with account age and normal behavior |
| One grant per person | Tie credits to a card fingerprint, phone number or device, not to an email address |
| Sandbox outbound | New accounts send only to their own verified addresses until reviewed or paying |
| Pay referrals late | Reward only after the referred account pays or stays active for weeks, capped per referrer (`0x:growth-marketing`) |
| Remove the motive | `rel="nofollow ugc"` on user links, `noindex` on new accounts' public pages, custom domains for paying or aged accounts only |

From the first day: quotas, and spend alerts on cloud and model providers; both are cheap. Add
verification gates when the first abuse appears, not before. Review the cost of the top 1
percent of free accounts weekly. Requiring a card for trials trades signups for quality and is
the user's call. Token budgets for LLM features: `0x:ai-features`.

## Spam and phishing through invites and sharing

Any feature where user-supplied text and a recipient address make the product send a message is
a relay that carries the product's reputation. The classic: an organization named "Your account
is locked, visit evil.example" invites ten thousand strangers.

- No free-text message in invitations from new or free accounts; ideally none at all.
- Names that appear in email (organization, project, display name) are length-limited, rejected
  when they contain URLs or domain-like text, and rendered as plain text.
- Invitations per account per day scale with trust: a handful for a new free account, more with
  age and payment. Cap pending invitations. The inviter's own email must be verified.
- The message shows the inviter's address and a report link. Recipients get per-recipient limits
  across all senders and a global "never email me again" that every sender honors.
- Suspend sending automatically for accounts whose invitations bounce, draw complaints or are
  never accepted; a spammer's acceptance rate is near zero.
- Public pages and files get the same care: user content on a separate registrable domain so a
  blocklisting does not take the app down, no custom HTML or scripts on free tiers, outbound
  links checked against a URL-reputation service, a visible "report abuse" link, and uploads
  scanned and served as attachments (`0x:backend-architecture`).
- Redirect and link-shortening endpoints validate destinations. An open redirect on a trusted
  domain is a phishing tool.

Effects on sender reputation: `0x:email-notifications`.

## Abuse notices from hosts, registrars and blocklists

Senders: the hosting or cloud provider, the domain registrar or registry, the email provider,
the CDN, the payment processor, browser blocklists (Google Safe Browsing, Microsoft SmartScreen),
spam and phishing lists, researchers and brand-protection firms. Deadlines are short, commonly
24 to 48 hours and less for phishing or malware. Silence ends in a suspended server, a blocked
sending account, or a domain placed on hold, which stops the site and all email at once.

Prepare at Launch:

- `abuse@` and `security@` mailboxes that reach a person, a public report form and
  `/.well-known/security.txt`.
- Current contact addresses on the registrar, host and email-provider accounts, exempt from spam
  filtering, and not an old personal inbox.
- The domains verified in Google Search Console and Bing Webmaster Tools, which show security
  flags and carry the review request.
- User content and user-triggered email on domains separate from the app and corporate mail.

Respond:

1. Acknowledge within hours, quoting the case ID. Reach the provider through its console, not
   through links in the message: fake abuse notices are a phishing genre.
2. Verify and remove: suspend the account, take the content down so the URL returns 404 or 410,
   and purge the CDN cache.
3. Sweep for siblings by device, IP range, payment card, content hash and link target.
4. Reply with facts: what was found, what was removed and when (UTC), the cause, and the control
   added to prevent a repeat. Ask for confirmation that the case is closed.
5. Request delisting where flagged: the security-issues review in Search Console for Safe
   Browsing, and each list's removal form. Reviews take hours to days.
6. Record the case. Providers tolerate platforms that are abused and act fast; they terminate
   those that show a pattern of ignoring reports.

A wrong or malicious notice is answered with evidence inside the deadline, never ignored.
Copyright takedowns, counter-notices and platform notice-and-action duties:
`0x:privacy-compliance`. Child sexual abuse material carries legal reporting and handling duties
that vary by country: stop, preserve as required and get legal advice at once. If the product
itself was compromised, it is a breach: `0x:web-security`.

## Signals, review queue and bulk suspension

| Part | Rule |
|---|---|
| Cases | Scheduled queries turn signals (signup rows, auth events, use of abusable features, user reports, bounces and complaints, disputes) into rows in an `abuse_cases` table: account, rule, score, evidence, status |
| Three bands | Automatic action only for rules with proven precision (a banned card fingerprint, a link flagged by a reputation service, complaint counts); a human queue for the middle; logging only for the rest |
| Review screen | Cases sorted by score and impact; per account the signup signals, linked accounts, recent activity and content samples; actions: clear, limit, suspend, ban with cluster |
| States | Active; limited (quotas down, outbound off); suspended (sign-in shows a notice and appeal route, public content unpublished, API keys off, queued sends canceled, payouts held); banned |
| Bulk action | Select by query or cluster, dry-run for a count and a sample, apply with a reason and batch ID, undo by batch ID; rate-limited and audited |
| Shadow mode | A new rule logs what it would have done for a week before it acts; precision per rule is tracked from appeal outcomes |

- Suspension is reversible and deletes nothing. Purge after a retention period.
- Do not teach: generic errors, enforcement in delayed batches and silent limits keep attackers
  from learning which signal caught them.
- Paying customers above a revenue threshold are never suspended automatically; a person looks
  first.
- Suspended users get a reason and a way to appeal; some jurisdictions require it
  (`0x:privacy-compliance`).

Build the suspend switch and its cascade at Launch. The queue and bulk tools come with the first
real wave.

## Multi-accounting and ban evasion

Link accounts by shared identifiers, strongest first: payment card fingerprint (Stripe exposes
one per card), verified phone number, device token or app attestation, commercial browser
fingerprint, canonical email, then IP range close in time, and behavior (same content, naming
pattern, sequence of actions). Accounts joined by strong links form clusters, found with a
recursive query over the link table.

- A shared IP alone is not a link: households, offices, campuses and carrier NAT share addresses.
- A ban writes the account's identifiers, hashed, to a blocklist that signup and payment check.
  A match routes to review or silent limits, not to an error that explains itself.
- Ban identifiers outlive account deletion, minimal and hashed, with the purpose documented
  (`0x:privacy-compliance`).
- Pool free allowances across a cluster: five linked accounts share one free quota, which
  removes the motive without banning anyone.
- Ask for a scarce identifier (phone, card) only from signups that resemble banned clusters. For
  phone verification, reject virtual and VoIP numbers with a line-type lookup.
- Legitimate multiple accounts exist (work and personal, agencies managing clients). Act on the
  purpose, multiplying free allowances or returning after a ban, not on a second account's
  existence.
- Expect anti-detect browsers, residential proxies, virtual cards and rented numbers. A
  determined abuser returns; the aim is that each return costs more and yields less.

## Ask the user

- **What can be extracted from a free account, and how much free usage per month is tolerable?**
  It sets quotas and the kill-switch budget. Default: quotas sized so one account's daily yield
  is negligible, plus a global daily cap with an alert.
- **How much signup friction is acceptable?** A card or phone step stops farming and costs
  conversions. Default: email verification and quotas; escalate only on evidence.
- **Is user content public on the product's domain?** A blocklisting then hits the whole
  product. Default: move it to a separate domain before Launch.
- **Who reads `abuse@` and provider notices, and how fast?** Missed deadlines end in suspension.
  Default: the founder, the same day, with forwarding to a phone.
- **What happens to a paying customer who is banned?** Refund and appeal policy is a business
  and legal choice. Default: human review before any ban, a stated reason, an appeal address,
  and a refund of the unused period unless fraud is clear.
