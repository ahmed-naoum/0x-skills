# Hardening company accounts, staff access and admin tools

Read this when: locking down the company's own accounts before launch, moving accounts out of personal names, onboarding or offboarding a person, exposing an internal tool or admin panel, setting a device baseline, or deciding who may read production data.

## The account chain

For a small company the likeliest breach is the takeover of an account that controls the product, not an exploit. The accounts form a chain, and hardening follows it from the top.

| Account | What its takeover gives | Minimum hardening |
|---|---|---|
| Primary email and identity provider | Password resets for everything else | Passkey or hardware key; no SMS or phone recovery; two super admins, one of them break-glass; OAuth grants and forwarding rules reviewed |
| Registrar and DNS | Mail redirection (so resets again), site redirection, certificate issuance | Hardware-key MFA; transfer lock; auto-renew with a working card and a multi-year term on the main domain; account contact address not on the domain it protects |
| Password manager | Everything stored in it | Hardware key; two administrators or a recovery path (`secrets.md`) |
| Source hosting | Code, CI secrets, a deploy path to production | 2FA required for the organization; two owners, everyone else members; rulesets on the default branch; app installs need owner approval |
| Cloud and hosting | Data and infrastructure | Root with hardware MFA and no access keys; people through SSO roles (`0x:cloud-infrastructure`, `iam-accounts.md`) |
| Payments and bank | Payout destination, refunds | Individual logins with MFA, least role, restricted API keys, alerts on payout-detail changes; dual approval on bank transfers once two people exist |
| Email sending, auth provider, error tracker, support desk, analytics | Sending as the company; customer data; material for social engineering | MFA, least role, unique password, stale users removed |

## MFA and least privilege

| Method | Resists phishing | Use |
|---|---|---|
| Passkey or FIDO2 hardware key | Yes: bound to the site's origin | Required on every account in the table above; two per person |
| TOTP app, push with number matching | No: a real-time proxy page relays the code | Acceptable on lower-tier tools |
| SMS or voice | No, and exposed to SIM swap | Remove as a method and as a recovery fallback wherever possible |

The weakest enabled method defines the account's strength: adding a passkey while SMS recovery stays on changes nothing. Theft of a session cookie by malware on the laptop bypasses every MFA method, which is why device hygiene and short admin sessions belong to the same control.

Least privilege:

- One named account per person; no shared logins where the service supports users.
- Owner or admin role for at most two people. Everyone else gets the least role that does the job, granted to a group and not to a person.
- On the source host: base permission for members is none or read; teams grant repository access; tokens are fine-grained with an expiry; no outside collaborator without an end date.
- API tokens, deploy keys, webhooks, installed apps and OAuth grants count as users. Inventory them per service.
- Quarterly access review: export the user list of each top-tier system, remove stale entries, record that it was done.

## Company-owned identities

Typical faults: the domain registered in a founder's personal account or by the agency that built the first version; the cloud root on a personal mailbox; repositories under a personal profile; an app-store account opened as an individual; the payment account opened by an individual with a personal bank account; analytics and ads under someone's personal login.

Rule: the legal entity owns every account. The login is a role address on the company domain (`ops@`, `domains@`, `cloud-root@`) delivered to at least two people, or to the founder plus an archive; never a personal mailbox and never one named employee's. Billing runs on a company card. The domain's registrant organization is the company's legal name, since that is what counts in a dispute.

Why it matters beyond tidiness: offboarding works; providers demand proof matching the account holder during recovery; acquirers and investors verify ownership of domain, code and accounts in due diligence (`0x:startup-finance`, `exit-due-diligence.md`); a founder dispute or death does not strand the company.

Migration order when accounts sit in personal names:

| Step | Account | Note |
|---|---|---|
| 1 | Email and identity provider | Everything else will point here |
| 2 | Registrar | Move the domain into a company registrar account. A registrant change or transfer can start a lock period during which the domain cannot move again; do it well clear of a launch |
| 3 | Source hosting | Transfer repositories into an organization. Old URLs redirect, but CI secrets, deploy keys and webhooks must be re-created |
| 4 | Cloud and hosting | Change the root or owner email to the role address, or move workloads into a company organization |
| 5 | Payments | A change of legal entity usually means a new account and a migration handled with the provider's support: `0x:payments-billing` |
| 6 | App stores, analytics, ads, social handles | Organization accounts take verification time; start early |

Contractors and agencies get member access to company-owned accounts, with an end date. They never hold the owner role and never register anything in their own name on the company's behalf.

## Pre-launch exposure sweep

Classify every route first: list all pages, route handlers and server actions and label each one public, authenticated, admin or machine-only. Anything unlabeled is a finding. Then remove or gate:

| Class | Examples | Fix |
|---|---|---|
| Default and seeded credentials | Seed admin users; demo accounts with known passwords; vendor defaults on self-hosted dashboards, queues, object stores and databases; placeholder secrets copied from an example file | Delete the accounts; fail startup in production when a secret is missing, short or equal to a known placeholder |
| Debug and development routes | `/api/debug`, `/api/seed`, `/api/test`, reset endpoints, health checks that print the environment, a GraphQL playground, interactive API docs listing internal endpoints, framework debug modes, error pages with stack traces | Remove from the production build instead of hiding: a condition on an environment variable is one misconfiguration away from open |
| Test bypasses | Fixed OTP codes, auth mocks behind a flag, query parameters that toggle features, webhook handlers that skip signature checks outside production | Compile out, or guard with a check that cannot be true in production |
| Machine endpoints | Cron and queue triggers, internal webhooks, metrics | Require a secret or signature; cron routes verify the scheduler's authorization header |
| Files served by accident | `/.env`, `/.git/`, database dumps and archives in the web root, directory listings, public source maps when the source is meant to stay private | 404 from outside |
| Forgotten hosts | Staging and preview deployments with real data or production keys, old API versions, admin UIs for queues and databases, dangling DNS records | Gate behind access control or delete; staging that holds production data is production |
| Network exposure | Database, cache and search ports reachable from the internet; a container port published on all interfaces, which bypasses the host firewall | Private networking or an allow-list; publish as `127.0.0.1:5432:5432` (`0x:linux-server`) |
| Storage | Public buckets, listable prefixes, long-lived public URLs to private files | Block public access at the account level; presigned URLs |

Checks from outside:

```bash
for p in .env .git/config api/debug api/seed graphql server-status metrics; do
  printf '%s  /%s\n' "$(curl -s -o /dev/null -w '%{http_code}' "https://example.com/$p")" "$p"
done
nmap -Pn -p- app.example.com   # expect 80 and 443 only
```

Every path should return 404 or 401; inspect the body of any 200. Search certificate-transparency logs for the domain to list every hostname that ever received a certificate: each must map to a live, owned, gated resource. Search the code for leftovers with `rg -n -i 'debug|seed|bypass|skipAuth|TODO.*auth' app src`.

## Staff: SSO, phishing-resistant MFA, offboarding

- From the first hire or contractor, the mailbox provider is the identity provider. Use "sign in with" that provider on every tool that offers it, even without paid SAML: no separate password exists, MFA is inherited, and suspending one account cuts new sign-ins everywhere.
- Paid SAML and SCIM: buy them on top-tier tools when a compliance framework requires it or when headcount (roughly ten or more) makes manual offboarding unreliable. Elsewhere social sign-in is enough.
- Identity-provider settings: 2-step verification enforced for everyone; security keys or passkeys only for admins; app passwords and legacy protocols off; third-party apps requesting mail or drive scopes need approval; alerts on a new admin, a new forwarding rule and a suspicious sign-in.
- Integrations run as service accounts or apps, never under a person's identity. Otherwise they break, or keep running with stale privileges, when that person leaves.

Offboarding happens the same day, within the hour for an involuntary departure, in this order:

1. Suspend the identity-provider account (suspend, not delete, so data and mail stay recoverable) and revoke its sessions, app passwords and OAuth grants. Suspension does not end sessions and tokens already issued by other tools.
2. Remove the person from every system not behind SSO: source host (including their deploy keys, personal tokens and apps), cloud, hosting, database roles, password manager, payments, registrar, support desk, analytics, chat, package registry, app stores.
3. Rotate what they could read: shared logins, production secrets held locally, SSH keys in `authorized_keys`, API keys in their `.env`.
4. Devices: returned, or remotely locked and wiped.
5. Transfer what they owned: documents, scheduled jobs, API tokens, anything opened in their name.
6. Record completion against the access matrix.

The access matrix (person × system × role) makes this mechanical; the systems outside SSO are where access survives. Contractor accounts are created with an expiry date.

## Internal tools: zero-trust access instead of a VPN

A VPN authenticates once and then exposes a network, its appliance is itself an internet-facing target, and someone has to run it. An identity-aware proxy authenticates every request to each tool against the identity provider, applies per-tool rules and logs per request, with nothing listening publicly.

| Need | Default |
|---|---|
| HTTP tools: admin panel, dashboards, queue UIs, staging | An identity-aware proxy (Cloudflare Access, Google IAP or a self-hosted equivalent) in front, with an outbound tunnel from the origin so that no inbound port is open |
| Non-HTTP: database, SSH, cache | An identity-based overlay network (Tailscale-style) with default-deny rules per person and host, or the cloud's session tooling, which needs no open SSH port |
| Extra layer only | IP allow-lists: weak alone because addresses are shared, change, and carry no identity |

Traps:

- The origin stays reachable around the proxy. Bind it to localhost or the tunnel, or firewall it to the proxy, and have the application verify the proxy's signed assertion: a JWT header checked against the provider's keys and the application's audience. A plain header such as `X-Forwarded-User` is forgeable by anyone who reaches the origin directly.
- The gate replaces nothing inside. The tool keeps its own authentication and role checks.
- Overlay networks ship with allow-all rules; write the default-deny policy on day one.
- Preview and staging environments belong behind the same gate.

## Admin panel

| Property | Requirement |
|---|---|
| Separate surface | Its own hostname and, when feasible, its own deployment, behind the zero-trust gate. An `/admin` path guarded only by a role check inside the customer app is one missed check from exposure |
| Separate authentication | Staff sign in through the company identity provider with phishing-resistant MFA. No `is_admin` flag on customer accounts: customer-side flows (password reset, email change, a session bug, mass assignment) then escalate into admin |
| Sessions | Short: an absolute lifetime of one working day and an idle timeout of 15 to 30 minutes (rule of thumb); re-authentication before refunds, exports, deletions, role changes and impersonation |
| Roles | Support, billing, engineer, super admin; every handler checks the role on the server; two-person approval for bulk or destructive operations at Scale |
| Page hygiene | Strict CSP; no analytics, session replay or chat widgets; customer-supplied strings escaped, because stored XSS aims here |
| Data display | Sensitive fields masked by default; revealing one is a logged action; secrets are never displayed |
| Audit | Every read of customer data and every write recorded with actor, target and reason (`logging-breach-response.md`) |

Features that need extra design:

- Impersonation: time-boxed, a reason required, a visible banner, credential and payment changes blocked while active.
- Bulk export: rate limit and alert.
- Changing a customer's email or resetting their MFA on request. This is the social-engineering target and needs an identity-verification procedure (`0x:auth-identity`, `account-recovery.md`).
- A raw SQL console: avoid; otherwise read-only against a replica, and logged.
- Admin-tool builders that connect to the database hold its credentials. Give them a scoped role and treat the vendor as top-tier.

## Staff devices

Baseline for every device that touches code, production or customer data, founders' and contractors' included:

| Control | Requirement | Verify |
|---|---|---|
| Disk encryption | On, with the recovery key escrowed off the device | macOS `fdesetup status`; Windows `manage-bde -status`; Linux `lsblk -f` shows `crypto_LUKS` |
| Updates | OS and browser automatic; critical patches within two weeks, within days for flaws under active exploitation (rule of thumb) | OS settings |
| Screen lock | Idle lock at five minutes or less; password or biometric to resume | OS settings |
| Accounts | No shared OS logins; password manager in use; no passwords saved in the browser | Spot check |
| Remote lock and wipe | Enabled through the OS vendor's service or MDM | Test once |
| Malware protection | The built-in one enabled; EDR when compliance or headcount asks | Settings |
| Data | No production dumps on laptops; if unavoidable, encrypted and deleted after use | Spot check |

- Enforcement: a self-attested checklist under about ten people; MDM or a compliance agent once an audit requires evidence or the team grows.
- Unmanaged or contractor devices: browser-only access to SSO-gated tools, no production credentials.
- Infostealers are the current laptop threat: malware from fake installers, malicious packages or "coding test"
  repositories copies browser session cookies, saved passwords, SSH keys and cloud credentials. Countermeasures:
  short-lived cloud sessions through SSO, hardware-backed SSH keys (`ed25519-sk`), a separate browser profile for
  admin consoles, unknown code run in a container or VM, restricted permissions for coding agents
  (`0x:ai-coding-agents`).
- Lost or stolen device: remote lock and wipe, revoke sessions at the identity provider, rotate secrets that were on disk, review logs for their use. Encrypted and powered off is low risk; unlocked and signed in is an incident.

## Production data access

Default: people do not read production data; the application does. Access is by role, through tools that log, and for a stated reason.

| Level | Who | How |
|---|---|---|
| Support views | Support role | Admin tool with scoped screens and audit |
| Read-only SQL | Named engineers | A personal read-only role against a replica, with sensitive tables and columns excluded or exposed through views; time-boxed |
| Write access | One or two people, as break-glass | A logged session with a stated reason; routine changes go through reviewed migrations and scripts |

- People never use the application's database credentials: there is no attribution, and rotating them breaks the app.
- Log at the database, because direct access bypasses the application's audit log: connection logging plus statement auditing for human roles (pgAudit where the host offers it; `0x:postgres-database`, `postgres-operations.md`). Object-level read logging on buckets is typically off by default; turn it on for the sensitive ones.
- Copies are access too: warehouse, BI tool, staging refreshes, local dumps, CSV exports in chat and drives, error tracker, LLM tools. Inventory them. Staging uses synthetic or anonymized data.
- For sensitive products, let the customer grant support access for a limited time instead of staff holding standing access.
- Solo founder: still use a personal read-only role by default and elevate deliberately. It prevents accidents now, and the structure is ready when the first contractor arrives.

## Ask the user

- **Whose name and email are on the registrar, cloud, source-host, payment and app-store accounts?** Personal ownership blocks recovery, offboarding and due diligence. Default: assume at least one is personal and verify each.
- **Who has had access since the project began: cofounders, contractors, agencies?** Leftover access cannot be seen from the code. Default: export user lists from every top-tier account and remove anyone not currently working on the product.
- **Which provider hosts company email?** It becomes the identity provider for everything. Default: the existing mailbox provider; do not add a separate identity product before Scale.
- **Is there budget for two hardware keys per person and for SSO tiers on the critical tools?** Keys are a one-time cost; SSO tiers recur. Default: keys now, paid SSO only where a framework or customer requires it.
- **Does support need to see customer content, or only account metadata?** It sets the admin tool's scopes. Default: metadata only, with content access through time-boxed, logged impersonation.
- **Where does the admin panel live today and how do staff sign in?** A role flag on customer accounts needs a migration plan. Default: move it behind the identity-aware proxy first, then separate authentication.
