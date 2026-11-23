# Layer 5: Trust

Read this when: the user asks what there is to know about trust, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

Who is this, what may they do, and what keeps attackers and regulators away?

Competencies: 194 (61 ● / 93 ◐ / 40 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## auth-identity

Build sign-in and access control that resist takeover: auth architecture, sessions and tokens, passwords, MFA and passkeys, OAuth and OIDC, enterprise SSO, authorization models, account recovery and abuse defense.

**Auth architecture and signup** (`references/auth-architecture.md`)

- ● Decide between a managed auth provider and a vetted library; never hand-roll crypto
- ● Choose sign-in methods for the audience: passkeys, social, magic links, passwords
- ● Model users, linked identities, credentials and sessions in the schema
- ● Design signup and email verification that resist typos and abuse
- ◐ Prevent user enumeration and timing leaks on auth endpoints
- ◐ Test auth flows end to end, including expiry and revocation paths
- ○ Migrate users between auth systems without forcing password resets

**Sessions, cookies and tokens** (`references/sessions-tokens.md`)

- ● Keep sessions in HttpOnly, Secure, SameSite cookies, not tokens in localStorage
- ● Implement sessions with rotation, expiry and revocation
- ● Protect state-changing requests against CSRF
- ● Choose server-side sessions or JWTs and accept the revocation trade-off
- ◐ Scope cookies correctly across subdomains and environments
- ◐ Rotate refresh tokens and detect reuse
- ◐ Let users view and revoke active sessions and devices
- ◐ Authenticate native and mobile clients with tokens in secure storage
- ○ Require step-up authentication for sensitive actions

**Passwords, MFA and passkeys** (`references/passwords-mfa-passkeys.md`)

- ● Hash passwords with Argon2id and reject known-breached passwords
- ● Implement email magic links and one-time codes that resist interception and replay
- ◐ Offer passkeys via WebAuthn as primary sign-in with a safe fallback
- ◐ Offer TOTP or passkey MFA and never rely on SMS alone
- ◐ Generate, store and consume MFA recovery codes safely
- ◐ Enforce MFA by policy for admins and organizations
- ○ Handle synced passkeys, multiple devices and cross-device sign-in
- ○ Upgrade legacy password hashes transparently at login

**OAuth and OpenID Connect login** (`references/oauth-oidc.md`)

- ● Add social login with Google, GitHub, Apple or Microsoft
- ● Debug an OAuth flow failing on redirect, state or cookie errors
- ● Link a provider login to an existing account without enabling takeover
- ◐ Implement OAuth 2.1 with PKCE and strict redirect URI validation
- ◐ Validate ID tokens: issuer, audience, nonce, signature and expiry
- ◐ Request minimal scopes at login and discard provider tokens you do not need
- ○ Issue scoped, short-lived credentials to AI agents acting for users

**Enterprise SSO and provisioning** (`references/enterprise-sso.md`)

- ◐ Decide build versus buy for enterprise single sign-on
- ◐ Add SAML or OIDC single sign-on for enterprise customers
- ○ Route users to their identity provider by verified email domain
- ○ Provision and deprovision users with SCIM
- ○ Map identity-provider groups to roles with just-in-time provisioning
- ○ Enforce SSO per organization while keeping a break-glass admin
- ○ Test SSO against Okta, Entra ID and Google Workspace

**Authorization models** (`references/authorization.md`)

- ● Check authorization on every object access to prevent IDOR
- ● Enforce authorization in server functions, APIs, jobs and realtime channels alike
- ● Implement organizations, invitations and role-based access for teams
- ● Centralize permission checks in one policy layer and test them
- ◐ Choose role-based, attribute-based or relationship-based authorization
- ◐ Design roles and permissions customers can understand and administer
- ◐ Share resources by link or invitation with expiring, revocable grants
- ○ Adopt a policy engine or Zanzibar-style service when checks outgrow code

**Account recovery and lifecycle** (`references/account-recovery.md`)

- ● Design password-reset and email-change flows that resist hijacking
- ● Issue reset tokens that are single-use, short-lived and stored hashed
- ● Build account deletion, deactivation and reactivation flows
- ◐ Notify users of every security-relevant account change
- ◐ Design recovery for lost passkeys and MFA devices without a backdoor
- ◐ Verify identity before support changes account ownership or MFA
- ◐ Transfer organization ownership when the owner leaves
- ◐ Recover hijacked accounts: force resets, restore ownership, undo attacker changes

**Bot and abuse defense** (`references/abuse-defense.md`)

- ● Rate-limit login, signup and reset endpoints per IP and per account
- ● Throttle signups by IP, device and email-domain reputation
- ◐ Stop credential stuffing with breach checks, device signals and MFA prompts
- ◐ Alert on failed-login spikes and anomalous-location sign-ins
- ◐ Add CAPTCHA or invisible challenges only where risk justifies the friction
- ◐ Design free tiers and trials so abuse is unprofitable
- ◐ Stop invites and sharing features being used to send spam or phishing
- ◐ Answer host, registrar and browser-blocklist abuse notices before they suspend you
- ○ Build abuse signals, a review queue and bulk-suspension tooling
- ○ Detect multi-accounting and ban evasion

## web-security

Build and run the product so it resists attack: threat modeling, vulnerability classes, browser security headers, secrets and cryptographic choices, the software supply chain, hardening of company accounts and admin tools, security logging and breach response, and security testing.

**Threat modeling and security priorities** (`references/threat-modeling.md`)

- ● Draw trust boundaries and data flows for the system
- ● Identify the crown-jewel data and the shortest paths to it
- ● Apply a security baseline checklist before a product launches
- ◐ Threat-model a feature and list abuse cases before building it
- ◐ Rank risks by likelihood and impact and decide what to accept
- ◐ Treat third-party scripts and vendors as part of the attack surface
- ○ Decide between a fractional CISO, a security hire and a managed service

**Vulnerability classes and safe input and output handling** (`references/vulnerability-classes.md`)

- ● Use parameterized queries everywhere and ban string-built SQL
- ● Escape output by context to prevent cross-site scripting
- ● Prevent path traversal, command injection and unsafe deserialization
- ● Reject mass assignment by allow-listing writable fields
- ● Sanitize untrusted HTML, markdown and SVG before rendering
- ◐ Block SSRF by allow-listing outbound destinations and guarding metadata endpoints
- ◐ Prevent open redirects and unsafe URL handling
- ◐ Close business-logic flaws: coupon reuse, negative amounts, race-condition double spends
- ◐ Bound attacker-sized inputs to prevent ReDoS and resource exhaustion
- ○ Sandbox user-supplied code, HTML and custom domains

**CSP, CORS and browser security headers** (`references/browser-security.md`)

- ● Configure CORS precisely, without wildcard origins on credentialed requests
- ● Block clickjacking with frame-ancestors
- ● Set Referrer-Policy, Permissions-Policy and nosniff headers
- ◐ Deploy a strict nonce-based Content Security Policy
- ◐ Roll out CSP in report-only mode and fix violations before enforcing
- ◐ Inventory third-party scripts and pin them with Subresource Integrity
- ◐ Validate postMessage origins and sandbox embedded iframes
- ○ Enforce Trusted Types to remove DOM XSS sinks
- ○ Apply cross-origin isolation headers (COOP, COEP, CORP) where needed

**Secrets, key management and cryptographic primitives** (`references/secrets.md`)

- ● Keep secrets in a secrets manager, never in repositories, images or client bundles
- ● Enable secret scanning with push protection on all repositories
- ● Rotate a leaked key, audit its use and purge it from history
- ● Share credentials through a team password manager with role-based access
- ● Turn on provider-managed encryption at rest for databases, disks, buckets and backups
- ● Pick the right primitive: random tokens, hashes, HMAC, authenticated encryption or signatures
- ◐ Issue short-lived, scoped credentials instead of static keys
- ◐ Rotate secrets on a schedule without downtime
- ◐ Store recovery codes and break-glass credentials where a second person can reach them

**Dependencies and software supply chain** (`references/supply-chain.md`)

- ● Commit lockfiles and install in frozen mode everywhere
- ● Evaluate a library's maintenance, license and bus factor before depending on it
- ● Scan dependencies and images in CI and patch within a deadline
- ◐ Automate dependency updates with a release cooldown window
- ◐ Disable install scripts and vet packages against typosquatting and slopsquatting
- ◐ Upgrade dependencies and runtimes on a cadence, ahead of end-of-life dates
- ○ Generate an SBOM for each release
- ○ Establish a compromised package's blast radius and rotate everything exposed
- ○ Fork, vendor or replace an abandoned dependency

**Hardening company accounts, staff access and admin tools** (`references/accounts-admin-hardening.md`)

- ● Enforce MFA and least privilege on registrar, repository, payment and SaaS accounts
- ● Hold domains, cloud, code and payment accounts in company-owned identities
- ● Remove default credentials, debug routes and forgotten internal endpoints before launch
- ◐ Enforce SSO, phishing-resistant MFA and same-day offboarding for staff
- ◐ Put internal tools behind zero-trust access instead of a VPN
- ◐ Harden admin panels with separate authentication, access restrictions and audit
- ◐ Secure staff devices with disk encryption, updates and screen locks
- ◐ Limit who can read production data and log every access

**Security logging, detection and breach response** (`references/logging-breach-response.md`)

- ● Decide which security events to log and how long to keep them
- ◐ Record security-relevant actions in an append-only audit log
- ◐ Log every internal admin action and customer impersonation
- ◐ Ship audit logs off-host and alert on anomalous cloud API calls
- ◐ Write a security incident plan before you need it: roles, contacts, decisions
- ◐ Contain an intrusion: isolate hosts, revoke sessions, rotate credentials, preserve evidence
- ○ Give customers exportable audit logs of account activity
- ○ Reconstruct from logs what an attacker accessed and when
- ○ Detect anomalies: export spikes, privilege changes and new credentials

**Security testing and disclosure** (`references/security-testing.md`)

- ● Test endpoints for broken access control using two accounts
- ● Verify security headers, TLS and cookie flags with external scanners
- ◐ Probe your own app against the OWASP Top 10 with an intercepting proxy
- ◐ Run automated security scanners in CI and triage their findings
- ◐ Commission a penetration test and triage findings by exploitability
- ◐ Fix findings by severity with deadlines and regression tests
- ◐ Publish a security.txt and run a vulnerability disclosure program
- ○ Run a tabletop exercise for a breach scenario

## privacy-compliance

Keep the product lawful and sellable: GDPR and US privacy law, consent and cookies, data-subject requests and retention, DPAs and vendors, PCI, SOC 2 and ISO 27001, sector and consumer rules, terms and policies, and software licenses.

**GDPR, CCPA and privacy fundamentals** (`references/privacy-law.md`)

- ● Map what personal data you hold, why, where and for how long
- ● Collect only the personal data a feature needs
- ◐ Choose a lawful basis for each processing purpose
- ◐ Decide whether you are controller or processor for each data flow
- ◐ Meet CCPA and US state privacy duties, including Global Privacy Control
- ◐ Notify regulators and affected users of a breach within legal deadlines
- ○ Handle cross-border transfers and EU data-residency requests
- ○ Run a data-protection impact assessment for high-risk processing
- ○ Appoint an EU or UK representative or DPO when required

**Consent, cookies, tracking and marketing permission** (`references/consent-cookies.md`)

- ● Implement cookie consent that actually blocks non-essential trackers
- ● Design a consent banner with equal accept and reject and no dark patterns
- ● Obtain marketing-email consent and honor unsubscribe and suppression
- ◐ Record, version and honor consent across devices and sessions
- ◐ Choose analytics that need no consent where the law allows
- ◐ Audit third-party tags and pixels for personal-data leakage
- ◐ Wire consent state into ad and analytics tags
- ◐ Check anti-spam rules before sending cold outreach in each country

**Data-subject requests and retention policy** (`references/data-subject-requests.md`)

- ● Fulfill access, deletion and export requests on deadline
- ◐ Verify a requester's identity without collecting more data
- ◐ Write a request runbook covering every system and subprocessor
- ◐ Set retention periods with a legal basis and legal-hold exceptions
- ◐ Keep a request log proving timely responses
- ○ Decide how deletion applies to backups, logs and analytics
- ○ Respond to objection, rectification and restriction requests

**Vendors, DPAs and subprocessors** (`references/vendors-dpas.md`)

- ◐ Sign DPAs with processors and maintain a subprocessor list
- ◐ Offer customers a DPA and notify them of subprocessor changes
- ◐ Assess a vendor's privacy and security before sending it customer data
- ◐ Keep a vendor inventory with owners, data categories and renewal dates
- ◐ Publish the subprocessor list and data locations on a trust page
- ○ Put transfer mechanisms in place for vendors outside the EU

**PCI DSS, SOC 2 and ISO 27001** (`references/pci-soc2-iso.md`)

- ● Decide when buyers actually require SOC 2 or ISO 27001
- ◐ Determine PCI DSS scope and complete the correct self-assessment questionnaire
- ◐ Write the minimal security policy set and actually follow it
- ○ Choose a compliance automation platform and auditor
- ○ Achieve SOC 2 Type II or ISO 27001 with automated evidence collection
- ○ Run access reviews, vendor reviews and risk assessments on a cadence
- ○ Inventory and monitor payment-page scripts per PCI DSS 6.4.3 and 11.6.1

**Other rules that may apply: sector, consumer, accessibility, AI and trade regulation** (`references/sector-consumer-rules.md`)

- ● Determine whether HIPAA, COPPA, financial or other sector rules apply
- ◐ Meet consumer-law rules on auto-renewal, cancellation and price display
- ◐ Remove dark patterns from consent, pricing and cancellation flows
- ◐ Meet accessibility law (EAA, ADA) with audits and a public statement
- ◐ Disclose AI-generated content and chatbots where transparency rules require
- ◐ Block sanctioned countries and parties and check export-control rules before selling abroad
- ○ Classify AI features under the EU AI Act and meet the resulting duties
- ○ Decide whether the EU Cyber Resilience Act covers software you distribute and meet it
- ○ Triage and remediate an accessibility complaint or demand letter

**Terms, privacy policy and platform duties** (`references/terms-policies.md`)

- ● Publish terms of service and a privacy policy matching actual data flows
- ● Write terms with liability caps and record versioned acceptance
- ● Decide what to template yourself and when to pay a lawyer
- ◐ Publish an acceptable use policy and enforce it
- ◐ Change terms with notice and re-acceptance when the change is material
- ◐ Process takedown notices (DMCA, DSA) within required timelines
- ○ Meet DSA and online-safety duties for user-generated content
- ○ Respond to a legal demand, subpoena or regulator letter with counsel

**Open-source licenses and third-party IP** (`references/licenses-ip.md`)

- ● License the fonts, images, icons and data you ship
- ● Check dependency licenses and avoid copyleft conflicts
- ◐ Generate a license inventory and attribution notices for a release
- ◐ Choose a license for your own code: open-source, source-available or proprietary
- ◐ Check license and IP exposure of AI-generated code and assets
- ◐ Respect the API terms, scraping limits and data licenses of your sources
- ○ Accept outside contributions with a CLA or DCO
