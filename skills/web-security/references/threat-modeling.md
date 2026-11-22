# Threat modeling and security priorities

Read this when: starting a product or feature and deciding what could go wrong, what to protect first and what to accept; before launch, to run the baseline; or when deciding which vendors, scripts and security help to trust.

## How a small product actually gets breached

Rule of thumb for a small SaaS, ordered by how often each is the entry path. Spend effort in this order unless the product's data argues otherwise.

| # | Path | First control | Details |
|---|---|---|---|
| 1 | Founder or staff account takeover: phish, reused password, stolen session cookie | Phishing-resistant MFA on email, registrar, repository, cloud, payments | `accounts-admin-hardening.md` |
| 2 | Leaked secret: repository, CI log, client bundle, laptop | Secret scanning, scoped and short-lived credentials | `secrets.md` |
| 3 | Missing authorization check: a signed-in user changes an ID and reads another tenant's data | Check ownership at the data-access layer, test with two accounts | `0x:auth-identity`, `security-testing.md` |
| 4 | Exposed surface: public bucket, open database port, debug route, forgotten staging host | Pre-launch exposure sweep | `accounts-admin-hardening.md` |
| 5 | Customer account takeover at volume (credential stuffing) | Rate limits, breached-password check, MFA | `0x:auth-identity` |
| 6 | Vulnerable or malicious dependency, unpatched framework CVE | Lockfile, release cooldown, patch deadlines | `supply-chain.md` |
| 7 | Injection, XSS or SSRF in the product's own code | Safe-by-construction APIs | `vulnerability-classes.md` |

Realistic attackers: indiscriminate bots and scanners (constant), a curious or hostile customer holding a valid account, a phisher targeting the founder, a compromised vendor or package, a former contractor with leftover access. A targeted state-level adversary is out of scope for nearly every small product; write that down as an accepted risk instead of designing for it.

## Map the system in 30 minutes

Produce three lists from the code, not from memory. A text table in `docs/security/threat-model.md` is enough; diagram tools add nothing at this size.

1. **Entry points**: every place outside input arrives. Route handlers, server actions, pages with parameters, webhooks, OAuth callbacks, file uploads, inbound email, queue consumers, cron endpoints, admin tools, websocket channels, API keys. In Next.js every server action and route handler is a public HTTP endpoint whether or not any UI links to it.
2. **Stores and copies**: database, object storage, cache, search index, queue payloads, logs, error tracker, analytics, warehouse, backups, staging refreshes, exports on laptops.
3. **Outbound**: every third-party API, webhook delivery, URL fetch, email and LLM call, with the data that leaves.

Then mark the trust boundaries, the lines where the level of trust changes, and what must happen at each crossing:

| Boundary | What crosses | Required at the crossing |
|---|---|---|
| Browser → server | Everything the client sends, including hidden fields, headers, cookies and IDs | Authenticate, authorize per object, schema-validate. Client code and TypeScript types are not controls |
| Tenant ↔ tenant | Shared tables, caches, search indexes, buckets, job queues | Tenant filter enforced below the handler (query layer or row-level security); cache and storage keys include the tenant |
| Customer ↔ staff | Admin panel, impersonation, support tools | Separate authentication; audit log of reads and writes |
| Server → third party | Customer data, secrets, URLs to fetch | Minimum data, egress rules, timeouts; the response is untrusted input |
| Third party → server | Webhooks, OAuth callbacks, inbound email | Verify the signature or state before parsing; handle replays |
| Server → browser | Props serialized to client components, API responses | Select fields explicitly; a whole database row passed to a client component ships every column |
| Stored content → renderer | User HTML, markdown, filenames, SVG, LLM output | Encode or sanitize at output |
| CI → production | Deploy credentials, build scripts, dependencies | Short-lived scoped credentials, protected branches |
| Enqueue → execute | Job and cron payloads written earlier by less-trusted code | Re-validate and re-authorize at execution time, not only at enqueue |

Two traps in the default stack. Middleware, or an edge proxy in front of the app, is a routing convenience and not the authorization layer: a framework bug or a path its matcher misses bypasses it, so every handler and data-access function resolves the session and checks again. And a route under `/admin` or `/internal` is reachable by anyone who guesses the URL.

## Crown jewels and the shortest path to them

| Tier | Examples | Why it ranks here |
|---|---|---|
| Control plane | Registrar and DNS, primary email, cloud root, source hosting, CI, password manager | Controls everything below: DNS redirects mail, mail resets passwords, CI holds deploy credentials |
| Credentials held for others | Password hashes, session and API tokens, customers' OAuth tokens and API keys for third-party systems, signing keys | A leak extends the breach into customers' other systems |
| Money movement | Payment-provider secret key, payout settings, refund and credit functions | Direct loss, fast |
| Customer content | The data customers pay to keep in the product | Contractual and reputational core |
| Personal data | Emails, names, addresses, IPs; special categories such as health, finance, children, biometrics | Legal notification duties: `0x:privacy-compliance` |

For each top item answer "who or what can read this today?" and count the paths: the application's database
role, read replicas, backups and where dumps go, the analytics warehouse copy, logs and error-tracker payloads,
support and admin tools, staff laptops, every subprocessor, LLM prompts. The shortest path is usually a copy,
not the primary: a backup bucket, a staging database refreshed from production, a CSV in a shared drive.

Reduce before defending, in this order: do not collect it; let a vendor hold it (cards stay with the payment provider, passwords with the identity provider); keep it out of copies (no production data in staging, redaction in logs); shorten retention; only then add controls such as field-level encryption (`secrets.md`).

## Threat-model a feature

When: any feature that adds an entry point, a new data class, an outbound call, money movement or sharing between users. Budget 20 to 30 minutes; skip it for pure UI changes. Record five things in the spec or pull request: assets touched, new entry points, abuse cases, mitigations, accepted risks.

Generate abuse cases by rewriting each user story with an attacker as the subject:

- "...to someone else's object": change the ID, the tenant, the email.
- "...a million times": cost, spam, enumeration, storage.
- "...with hostile values": negative, huge, zero, wrong type, markup, a URL to an internal host.
- "...out of order or twice at once": skip the payment step, replay, race two requests.
- "...after access ended": removed member, expired trial, revoked key, old share link.
- "...for free, or for profit": trial farming, referral loops, refunds, reselling the product's resources.
- "...to hit a third person through the product": phishing sent from the product's domain, malware hosting, harassment.

For a systematic pass, ask the six STRIDE questions at each boundary the feature crosses: can someone pretend to be another identity, alter data, deny having acted (is it logged?), read what they should not, exhaust a resource, or gain a privilege?

| Feature | Abuse cases that are usually missed |
|---|---|
| Invitations, sharing by email | Mail-bombing a victim address; user enumeration through differing responses; an invite that grants access to whoever opens it; an invite still valid after the inviter was removed |
| Share links | Token short or sequential; never expires; leaks through `Referer` and chat link previews; still works after unsharing |
| File upload | Stored XSS through HTML or SVG served from the app origin; malware hosting; storage cost; decompression bombs |
| Export, reports, search | Bulk exfiltration after a single account takeover; cross-tenant rows; expensive queries as denial of service |
| "Fetch this URL", outbound webhooks, link previews | SSRF to internal hosts and cloud metadata |
| Free tier, trials, credits, referrals | Farming with disposable accounts; self-referral; reselling compute or LLM usage |
| User-triggered email or SMS | Spam relay on the product's sending reputation; SMS toll fraud |
| API keys, integrations | Full-account scope; no expiry; shown again after creation; logged in plain text |
| Support impersonation | Staff, or a compromised staff account, browsing customer data without trace |
| LLM features | Prompt injection through retrieved content: `0x:ai-features` |

## Rank risks and decide

Three levels each for likelihood and impact; finer scales add false precision.

- **Likelihood**: high if reachable from the internet without an account or by any self-registered user, or if tooling automates it; medium if it needs a specific customer role or a victim's interaction; low if it needs insider access or another compromise first.
- **Impact**: high if it touches all tenants, credentials, money or the control plane; medium for one tenant or a recoverable integrity loss; low for one user's non-sensitive data or brief unavailability.

| | Impact low | Impact medium | Impact high |
|---|---|---|---|
| **Likelihood high** | Fix this quarter | Fix before launch | Fix before the feature ships |
| **Likelihood medium** | Backlog or accept | Fix this quarter | Fix before launch |
| **Likelihood low** | Accept | Accept with a revisit trigger | Mitigate, or document with an owner |

Each risk gets one of four decisions: remove (drop the feature or the data), mitigate, transfer (a vendor holds
it, or insurance covers it), accept. Acceptance is legitimate only when written down: the risk, why it is
tolerable now, the owner, and the trigger that reopens it (a stage change, the first enterprise customer, a new
data class, an incident). Keep the list in `docs/security/risks.md`; ten lines is a healthy size at Launch.

Not subject to ranking: any path by which a self-registered user reaches another tenant's data, and any unauthenticated path to the control plane or to money, is fixed before shipping.

Deliberately skip until Scale: a SIEM, custom WAF rule sets, a paid bug bounty, red-team exercises, threat-modeling software, hardware security modules. Each needs someone to operate it.

## Launch baseline

Run before real users arrive. Each line is checkable; the named file has the procedure.

| Area | Must be true at Launch |
|---|---|
| Accounts | Passkey or hardware-key MFA on email, registrar, source hosting, cloud, payments and password manager; all owned by the company; a second person can recover them (`accounts-admin-hardening.md`, `secrets.md`) |
| Authentication | A maintained auth library or provider; session cookies `Secure`, `HttpOnly`, `SameSite=Lax`; rate limits on sign-in and reset (`0x:auth-identity`) |
| Authorization | Every handler and server action resolves the session and checks object ownership; a two-account test covers every endpoint that takes an ID (`security-testing.md`) |
| Input and output | Schema validation at every entry point; no string-built SQL; no unsanitized HTML sinks (`vulnerability-classes.md`) |
| Browser | Security headers present; CSP at least in report-only; no reflected or wildcard CORS with credentials (`browser-security.md`) |
| Secrets | None in the repository, client bundle or image; secret scanning with push protection on; production values differ from development (`secrets.md`) |
| Dependencies | Lockfile committed, frozen installs, vulnerability alerts on, framework and runtime on supported versions (`supply-chain.md`) |
| Exposure | No debug routes, default credentials, public buckets or reachable database ports; staging is gated and holds no production data (`accounts-admin-hardening.md`) |
| Transport | HTTPS everywhere with HSTS (`0x:web-networking`) |
| Data | Encryption at rest on; backups exist and one restore has been performed (`0x:postgres-database`) |
| Detection | Audit log for authentication, permission, export and admin events; cloud audit trail on; alerts reach a phone (`logging-breach-response.md`) |
| Response | One-page incident plan with contacts; `security.txt` published (`logging-breach-response.md`, `security-testing.md`) |

At Prototype only the Accounts, Secrets and Dependencies rows apply, plus keeping real customer data out of the product.

## Third-party scripts and vendors

A script loaded from a vendor runs with the full authority of the page: it reads the DOM, form fields and any token in `localStorage`, and makes authenticated requests as the user. A vendor that holds data or credentials extends the perimeter to its own security. List both in the threat model as components of the system.

Scripts:

- No third-party scripts on sign-in, password reset, payment and admin pages. Analytics, chat widgets and session replay there capture credentials and card data when the vendor is compromised.
- A tag manager is a code-deploy channel controlled by whoever holds the marketing login. Protect it like the repository: MFA, few publishers, no custom-HTML tags without review.
- Session replay and analytics mask inputs by default; verify in a recorded session that password, token and personal fields are blank.
- Prefer self-hosted bundles to remote script tags, and pin what cannot be self-hosted (`browser-security.md`).

Vendors:

| Tier | Definition | Before adopting | Ongoing |
|---|---|---|---|
| 1 | Can deploy code, mint credentials or read crown-jewel data: cloud, database host, auth provider, source hosting, CI, payments, email sending, password manager, admin-tool builders | SSO or enforced MFA, its own audit log, an independent security report (SOC 2 or ISO 27001), a breach-notification clause | Subscribe to its security advisories; know how to rotate every credential it holds; review access quarterly |
| 2 | Holds personal data: analytics, support desk, CRM, error tracker, LLM provider | Signed DPA; data minimized and scrubbed before sending; processing region known | Remove unused ones; review what is sent |
| 3 | No customer data | Unique password, MFA | None |

OAuth grants are vendor access too: an integration holding repository-write or mailbox-read scope is a standing
credential in a third party's hands. Review connected apps on the identity provider and the source host
quarterly and revoke the unused. When a vendor announces a breach, assume every credential and token it held is
exposed: rotate first, read the report second. Contract and DPA mechanics: `0x:privacy-compliance`
(`vendors-dpas.md`); whether to buy at all: `0x:engineering-leadership` (`build-vs-buy.md`).

## Who owns security: fractional CISO, hire or managed service

| Situation | Choice | Why, and the limit |
|---|---|---|
| Prototype and Launch, no regulated data, no enterprise buyers | Founder owns it; buy managed components (auth provider, PaaS, managed database); commission one penetration test when a customer asks | The controls are engineering decisions; there is nothing to delegate yet |
| Enterprise deals stall on security questionnaires or SOC 2; regulated data; aftermath of an incident; nobody able to sign risk decisions | Fractional CISO, a few days per month | Delivers the risk register, policies, audit preparation and customer answers. Does not do the engineering; without an internal owner for the fixes, the output is documents |
| Engineering team in the tens, or the product itself is security-, finance- or health-critical | First security hire: an engineer who ships code (application or cloud security), not a compliance manager | Paperwork can be outsourced; secure design inside the codebase cannot |
| A contract or regulator requires round-the-clock monitoring and nobody answers alerts at night | Managed detection and response | Buys the night shift. Worthless unless someone internal can act on an escalation within the hour and the provider receives the right logs |
| An audit certificate is needed | Compliance automation platform plus auditor: `0x:privacy-compliance` (`pci-soc2-iso.md`) | Collects evidence; does not make the product secure |

Traps: a CISO title before there is a team to lead; a SIEM or monitoring contract with nobody to respond; forty policy documents nobody follows; believing any of these transfers accountability. The founder still signs risk acceptances and is the one called at night. Readiness test for any option: name who receives the alert, who can shut a system off, and who decides to notify customers.

## Ask the user

- **What data would hurt most if it leaked, and is any of it regulated (health, financial, children's, government IDs)?** It sets the crown-jewel ranking and the legal duties. Default: customer content and credentials are the crown jewels; no special-category data.
- **Who are the customers: consumers, small businesses, or enterprises with security reviews?** Enterprise buyers turn audit logs, SSO, penetration tests and written policies into sales requirements. Default: small businesses; build the Launch baseline and defer formal compliance.
- **Who besides you has access to anything today: a cofounder, contractors, an agency, former collaborators?** Leftover access is a top breach path that the code cannot reveal. Default: assume some exists and run the account inventory.
- **Which outcome could the company not survive: a data leak, a long outage, a fraud loss, or losing the domain or cloud account?** It decides where the first day of hardening goes. Default: loss of the control-plane accounts.
- **Are there security promises already made: a signed DPA, an answered questionnaire, an SLA?** Accepted risks must not contradict them. Default: none, but check signed customer agreements before accepting a risk.
- **Is a known gap acceptable for now, and until when?** Accepting risk is a business decision. Default: accept only low-impact items, each with a revisit trigger at the next stage.
