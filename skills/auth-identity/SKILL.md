---
name: auth-identity
description: "Builds sign-in and access control that resist account takeover: auth provider or library choice, sessions, passwords, MFA, passkeys, OAuth and OIDC login, SAML SSO and SCIM, roles and permissions, account recovery and abuse defense. Use when adding login or signup, Sign in with Google, organizations and invitations, password reset, fixing an IDOR, or fighting fake signups and credential stuffing."
---

# Authentication, authorization and account abuse

## Stance

Accounts are taken over through the weakest door: a recovery flow, an unverified email match, a
support request, an endpoint that forgot to check. Expert work here is deciding what not to build
(the cryptographic mechanisms) and then being exhaustive about every path around them.

1. **Borrow the mechanism, own the policy.** Hashing, tokens, OAuth, WebAuthn and SAML come from
   a maintained library or provider, because their bugs do not show in tests. The account model,
   authorization and recovery rules are the project's own, because no library knows the business.
2. **The weakest path sets the strength.** Every sign-in method, fallback, recovery flow and
   support procedure is a way in. A new method lowers security unless its recovery is as strong
   as the rest.
3. **Identity is a subject ID, never an email.** Emails change, get recycled and are asserted by
   providers with varying honesty. Matching on an unverified email is takeover.
4. **Keep state the server can revoke.** Opaque sessions in `HttpOnly` cookies by default.
   Anything that cannot be revoked (a JWT, a signed URL) lives for minutes.
5. **Authorize where data is touched, on every object, deny by default.** Hidden buttons,
   middleware and layouts are presentation. Each server function, job and channel is an entry
   point of its own.
6. **One pattern for every secret:** random, single-use, short-lived, bound to a purpose, stored
   hashed. Reset links, codes, invitations, sessions and recovery codes all follow it.
7. **Tell anonymous callers nothing.** The same response and timing whether or not the account
   exists; the detail goes to the mailbox.
8. **Friction follows risk.** Step-up, challenges and verification appear when the action or the
   signals justify them. Hard lockouts and walls hurt honest users and teach attackers.
9. **Log and notify every security-relevant change.** The audit trail with old values makes a
   hijack reversible, and the notice is how the owner finds out.

## Route

| If the task is | Read |
|---|---|
| Adding login or signup from scratch, choosing Clerk, Auth0, Supabase Auth or a library, designing user tables, email verification, hiding which emails have accounts, testing auth flows, or migrating users between auth systems | `references/auth-architecture.md` |
| "Sessions or JWTs?", where to store a token, cookie flags, CSRF, cookies across subdomains or environments, refresh tokens, a sessions-and-devices page, mobile app sign-in, re-authentication before sensitive actions | `references/sessions-tokens.md` |
| Hashing passwords, password rules, magic links or email codes, passkeys, two-factor with TOTP, recovery codes, requiring MFA, upgrading old password hashes | `references/passwords-mfa-passkeys.md` |
| Adding Sign in with Google, GitHub, Apple or Microsoft, a `redirect_uri_mismatch` or state error, duplicate accounts from social login, ID token validation, scopes, credentials for AI agents or MCP | `references/oauth-oidc.md` |
| An enterprise customer wants SAML, SSO, SCIM, directory sync, domain verification, group-to-role mapping or enforced SSO | `references/enterprise-sso.md` |
| A user can see another user's data by changing an ID, adding roles, permissions, organizations, team invitations or sharing links, or choosing RBAC, ABAC, ReBAC or a policy engine | `references/authorization.md` |
| Password reset, email change, a lost phone or passkey, deleting or deactivating accounts, security emails, a support request to change an owner or email, a hacked account | `references/account-recovery.md` |
| Fake signups, credential stuffing, rate limits on login, CAPTCHA, free-tier or trial abuse, invite spam, an abuse notice from a host or registrar, a browser "deceptive site" warning, ban evasion | `references/abuse-defense.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Who runs auth | A maintained library writing to the project's Postgres (Better Auth for new TypeScript work); never hand-rolled | SSO, SCIM and organization features are due soon, or data already lives on Supabase or Firebase: use a managed provider |
| Sign-in methods | Google plus email code; passkeys offered after sign-in | The audience expects passwords; developers want GitHub; an iOS app needs Apple |
| Session | Opaque ID in a `__Host-` cookie with `HttpOnly; Secure; SameSite=Lax`, row in Postgres, 30 days idle and 90 absolute | Services must verify without the store: a 5 to 15 minute JWT minted from the session |
| CSRF | No mutation on GET, `SameSite=Lax`, origin check on every non-GET request | Never |
| Passwords | Argon2id at 19 MiB, 2 iterations, parallelism 1 or stronger; breach check; no composition rules | The runtime lacks Argon2: scrypt |
| MFA | TOTP and passkeys with recovery codes; required for owners and admins; no SMS | The audience cannot use an authenticator app |
| One-time tokens | 32 random bytes, SHA-256 stored, single-use, purpose-bound; reset 30 minutes, codes 10 | Never |
| Tenancy and roles | Organizations with memberships; owner, admin, member; one `can()` module; 404 across tenants | A sharing graph or several services at Scale: evaluate a policy engine |
| Social account linking | Keyed by issuer and subject; automatic only for a verified email from an authoritative provider | Never |
| Enterprise SSO | Buy or bridge; email-first routing on verified domains; SCIM for deprovisioning | Per-connection fees dominate |
| Abuse | Per-account and per-IP limits, throttling instead of lockout, challenges behind a flag | Under attack: enable challenges and new-device email codes |

By stage:

- **Prototype:** library or provider defaults, one or two sign-in methods, the tenant scope in
  every query, rate limits on auth endpoints. Skip MFA, SSO, custom roles and the sessions page.
- **Launch:** verified email before costly or outbound actions, breach check, MFA for admins,
  session revocation on password change, security notifications with an audit table, cross-tenant
  tests, a deletion flow, an account lock switch and a monitored `abuse@` mailbox.
- **Scale:** enterprise SSO and SCIM, organization-wide MFA policy, sessions and devices page,
  risk-based challenges, an abuse review queue with bulk suspension, custom roles when a deal
  needs them.

## Before you call it done

1. No hashing, token signing, OAuth, WebAuthn or SAML logic is written by hand, and the libraries
   that provide them are current.
2. The session cookie carries `HttpOnly`, `Secure` and `SameSite`, has no `Domain` unless
   justified, and no token sits in `localStorage`.
3. Logout, password change and reset revoke sessions on the server: a test replays the old
   cookie and gets 401.
4. Every server function, route handler, job and realtime subscription that touches tenant data
   calls the policy layer, and a cross-tenant test gets 404 on another organization's IDs.
5. Every cookie-authenticated non-GET endpoint checks the origin, and nothing mutates on GET.
6. Login, reset, magic-link and signup responses match for existing and unknown emails in
   status, body and timing.
7. One-time tokens are stored hashed, consumed by one atomic update, expire, and are bound to a
   purpose. A GET never consumes one.
8. Social identities are keyed by provider subject, automatic linking needs a verified email on
   both sides, and the connect flow checks `state`.
9. MFA cannot be skipped: a pre-MFA cookie reaches nothing, and password reset does not bypass
   it.
10. Changing email, password or MFA requires step-up and notifies the previous address.
11. Login, signup, reset and code verification are rate-limited per account and per IP, using
    the real client IP.
12. ID tokens are verified for signature, issuer, audience, expiry and nonce with a pinned
    algorithm.
13. Invitations are bound to the invited address, expire, and cap the role at the inviter's.
14. For SSO, an assertion is accepted only for its own connection and that organization's
    verified domains, and enforcement has a break-glass path.
15. No password, token or secret appears in logs, analytics URLs or error-tracker payloads.

## Not this skill

- XSS, injection, CSP, CORS and other vulnerability classes → `0x:web-security`
- Tenant data isolation and row-level security design → `0x:backend-architecture`
- API keys and OAuth for third-party developers → `0x:api-design`
- Sending the verification, reset and security emails or SMS → `0x:email-notifications`
- WAF rules and DDoS protection at the edge → `0x:web-networking`
- Staff SSO, device security and internal access control → `0x:web-security`
