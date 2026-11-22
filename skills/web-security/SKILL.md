---
name: web-security
description: Makes a web product and its company resist attack. Covers threat models, injection, XSS and SSRF, CSP, CORS and security headers, secrets and crypto primitives, dependency supply chain, account and admin hardening, audit logs, breach response and pentests. Use when asked if a feature is secure, to fix a CORS or CSP error, or to handle a leaked key, a compromised package or a suspected breach.
---

# Web application and company security

## Stance

Security for a small company is a prioritization problem. A few paths account for most real breaches, and
the work is to close those in order, make the safe way the default way in the code, and be able to see and
respond when something still gets through. Think as the attacker first (what is worth taking, and what is
the cheapest way to it), then as the engineer.

1. **Start from what an attacker wants and the cheapest path to it.** For a small product that is a staff
   account, a leaked secret, a missing authorization check or an exposed admin surface far more often than
   a clever exploit. Order the work by that, not by a generic checklist.
2. **Everything crossing a trust boundary is hostile until parsed, and every check lives on the server.**
   Client code, TypeScript types, hidden fields and middleware are conveniences; the handler and the
   data-access layer decide.
3. **Remove before defending.** Data not collected, features not exposed and URLs not fetched cannot be
   breached. Deletion is the only control with no maintenance cost.
4. **Make the safe path the only easy one.** Parameterized queries, auto-escaping, schema allow-lists and
   maintained libraries; ban the unsafe APIs by lint, so that safety does not depend on vigilance.
5. **Assume one layer fails.** Pair each control with a cheap second one (CSP behind escaping, a limited
   database role behind query checks) and shrink what any single credential or account can reach.
6. **The company's accounts are part of the product.** Phishing-resistant MFA on email, registrar,
   repository, cloud and payments outranks most code hardening.
7. **Nothing can be investigated that was not logged.** Decide audit events and retention before the
   incident, and keep the logs where an attacker cannot delete them.
8. **In an incident, rotate and contain first, preserve evidence, clean up last.** The reverse order is
   the usual mistake.
9. **Proportion by stage.** Spend where likelihood times impact is highest, write down what is accepted,
   and skip tooling nobody will operate.

## Route

| If the task is... | Read |
|---|---|
| "Is this feature secure?"; planning a feature or a launch; ranking risks; vetting a vendor or third-party script; deciding whether to bring in security help | `references/threat-modeling.md` |
| Writing or reviewing code that handles input: SQL, HTML output, file paths, shell calls, URL fetches, redirects, money logic; rendering user HTML, markdown or SVG; running user code; custom domains | `references/vulnerability-classes.md` |
| A CORS error; a CSP to add or fix; security headers; iframes and embedding; third-party script tags; `postMessage`; cross-origin isolation | `references/browser-security.md` |
| A key was committed or leaked; where secrets live; rotation; password manager; encryption at rest; "token, hash, HMAC, encryption or signature?" | `references/secrets.md` |
| Adding or updating a dependency; a vulnerability alert; a compromised or abandoned package; runtime end of life; SBOM | `references/supply-chain.md` |
| Locking down registrar, email, repository, cloud and SaaS accounts; offboarding; the admin panel; internal tools; staff laptops; who may read production data | `references/accounts-admin-hardening.md` |
| What to audit-log; building the audit log; alerts on suspicious activity; "we think we were breached"; writing the incident plan | `references/logging-breach-response.md` |
| Testing the product's own endpoints; checking headers and TLS from outside; CI scanners; buying a penetration test; fixing findings; `security.txt`; a breach rehearsal | `references/security-testing.md` |

## Defaults at a glance

| Area | Default | From |
|---|---|---|
| Company accounts | Passkey or hardware-key MFA on email, registrar, repository, cloud, payments and password manager; company-owned; recoverable by a second person | Prototype |
| Secrets | Host environment store; nothing in the repository, image or client bundle; secret scanning with push protection. Secrets manager and short-lived CI credentials at Launch | Prototype |
| Dependencies | Committed lockfile, frozen installs, alerts on. At Launch add a 7-day release cooldown, install scripts off and patch deadlines | Prototype |
| Input | A Zod schema at every entry point, with size bounds; a per-operation allow-list of writable fields | Prototype |
| Queries and output | Parameterized queries only; framework escaping; an allow-list sanitizer at render for any user HTML | Prototype |
| Authorization | Session and ownership checked in every handler and server action, and again at the data layer. At Launch add the two-account test suite | Prototype |
| Browser | Baseline headers on every response; same-origin API, so no CORS; nonce-based CSP on app pages, rolled out report-only first | Launch |
| Server-side fetch of user URLs | Avoid; otherwise resolve, block private ranges, connect to the checked address, no redirects | Launch |
| Crypto | 32 random bytes for tokens; SHA-256 to store issued tokens; HMAC-SHA-256 for webhooks; AES-256-GCM or libsodium to encrypt; Ed25519 to sign; passwords through the auth library | Any |
| Admin and internal tools | Separate hostname, staff SSO, behind an identity-aware proxy, every action logged | Launch |
| Logging | Append-only audit table for auth, permission, export, money and admin events; 12 months; cloud audit trail archived outside the production account | Launch |
| Response | One-page incident plan with phone numbers; `security.txt`; disclosure policy without rewards | Launch |
| Outside testing and heavy tooling | Penetration test when a customer or framework asks; bug bounty, SIEM, SBOM and Trusted Types wait | Scale |

## Before you call it done

1. Every new route handler and server action resolves the session and checks ownership of each ID it
   receives, including IDs in the body.
2. A test shows that an account in another tenant gets 404 or 403 on every new endpoint, with none of the
   first tenant's data in the body.
3. Input is parsed by a schema with length and range bounds; no request body reaches a create or update
   unfiltered.
4. `rg -n 'queryRawUnsafe|executeRawUnsafe|sql\.raw\(|dangerouslySetInnerHTML|innerHTML|child_process' src app`
   shows no unreviewed hit.
5. User-supplied HTML, markdown, SVG and URLs pass a sanitizer or a scheme allow-list at render; uploads
   are served from a separate domain.
6. Any server-side fetch of a user-influenced URL goes through the filtered fetch path.
7. Limits on money, coupons, quotas and single-use tokens are enforced by an atomic database statement and
   tested with parallel requests.
8. No secret is in the diff, the client bundle or the image; new secrets are in the inventory with a
   rotation procedure.
9. `curl -sI` on a page, an API route and an error page shows the baseline headers, and the end-to-end run
   reports no CSP violation.
10. CORS, if present at all, echoes only exact allow-listed origins and sends `Vary: Origin`.
11. New dependencies were verified to exist under the intended name, are in the lockfile, and CI installs
    in frozen mode.
12. Security-relevant actions added by the change write audit events, and no log line contains a secret,
    token or password.
13. No debug route, seeded credential or test bypass ships; new internal endpoints require a secret or sit
    behind the access proxy.
14. Risks accepted in the change are written in the risk list with an owner and a revisit trigger.

## Not this skill

- Reviewing the current diff or pending changes for vulnerabilities → `security-review`
- Login, sessions, MFA, permission checks and signup abuse → `0x:auth-identity`
- TLS configuration, HSTS, WAF and DDoS protection → `0x:web-networking`
- SOC 2, ISO 27001, PCI scope and breach-notification law → `0x:privacy-compliance`
- Hardening a single Linux host and SSH → `0x:linux-server`
- Prompt injection and LLM-specific guardrails → `0x:ai-features`
