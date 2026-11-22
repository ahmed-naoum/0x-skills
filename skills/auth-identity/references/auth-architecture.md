# Auth architecture and signup

Read this when: starting authentication in a product or replacing it: choosing a provider or a
library, picking sign-in methods, designing the user tables and the signup and verification flow,
testing auth flows, or moving users from another auth system.

## Provider or library

Buy or borrow the mechanism, own the policy. Password hashing, token generation and comparison,
JWT verification, OAuth and OIDC flows, WebAuthn verification, TOTP and SAML parsing come from a
maintained library or a provider: hand-written versions fail in ways tests do not show (timing
leaks, algorithm confusion, signature wrapping). The project's own code holds the account model,
authorization, invitations, recovery policy and UI.

| Situation | Choose | Why |
|---|---|---|
| Greenfield on Postgres and TypeScript, no enterprise deal in sight | A library writing to the project's own database: Better Auth for new work; keep whatever the project already runs (Auth.js is in security-only maintenance: leave it where it works, start nothing new on it) | Users join to domain tables in one transaction, no per-user fee, no third party on the login path |
| Data already on Supabase or Firebase | That platform's auth | Its row-level security and SDKs assume it; a second identity source doubles the work |
| B2B with SSO, SCIM and org management due within a year, or nobody wants to own auth | Managed provider (Clerk, WorkOS, Auth0, Stytch, Kinde) | Organizations and enterprise SSO are months of work; the fee is small against contract size |
| Consumer product with a large free base | Library | Per-active-user pricing grows with users who pay nothing |
| Self-hosted or on-prem product | Library, or an embeddable identity server (Keycloak, Ory, Zitadel) | Customers cannot depend on a vendor's cloud |
| Contractual data residency | Library, or a provider that commits to the region in the contract | User records are personal data |

Check before committing to a managed provider:

- **Exit.** Will it export password hashes, and in which algorithm? Some do so only through a
  support request on paid tiers, and some user pools never export them. No hash export means a
  forced reset for every password user on the way out.
- **Price shape.** Per monthly active user, per SSO connection, per add-on (MFA, organizations).
  Model the bill at ten times the current user count from the provider's current price list.
- **Where the session is verified.** If every request calls the provider, its latency and downtime
  become the app's. Prefer local verification of a short-lived token.
- **User sync.** The app still needs its own `users` row to join against. Upsert it on the first
  authenticated request by the provider's user ID, and also process the provider's webhooks.
  Webhooks alone arrive late or out of order, and a user who just signed up hits a missing row.
- **Portability of identities.** Use the project's own domain for hosted pages and passkeys and its
  own OAuth client IDs from the first real user. Passkeys registered to a vendor domain and social
  identities created through a vendor's shared credentials cannot be moved.

A self-hosted identity server is a second production system to patch, back up and monitor. Skip it
unless the product itself ships to customer infrastructure.

## Sign-in methods

Every enabled method is another attack surface and another recovery path, and the account is as
strong as the weakest of them. Start with two methods and add on evidence.

| Audience | Start with | Add later |
|---|---|---|
| B2B SaaS | Google and Microsoft sign-in, plus email (one-time code, or password) | Per-customer SSO, passkeys |
| Consumer web | Google, email code; Apple when there is an iOS app | Passkeys as an upgrade prompt |
| Developers | GitHub, Google, email | Passkeys |
| High-value accounts (money, admin, health) | Password with mandatory MFA, or passkeys | SSO |

- **Passwords** bring reset flows, breach checks and credential stuffing. Passwordless email
  removes those and makes login depend on email delivery: a delayed message is a locked-out user.
  Offer passwords when the audience expects them or their corporate mail is slow or filtered.
- **Email code versus magic link:** send both in one message. The code works when the email is
  opened on another device and survives corporate link scanners; the link is one click on the
  same device.
- **Passkeys:** offer as an added method after another sign-in, and through autofill on the login
  field. Passkey-only at Launch strands users who change phone ecosystem. See
  `passwords-mfa-passkeys.md`.
- **Social login:** only providers the audience already has; each needs the linking rules in
  `oauth-oidc.md`. An iOS app that offers third-party sign-in must also offer an equivalent
  privacy-focused option under App Store review rules; in practice that is Sign in with Apple.
- **SMS as a sign-in method:** skip. It costs per message, attracts toll fraud and falls to SIM
  swap.

## Schema

```sql
create table users (
  id uuid primary key,
  email citext unique,                     -- needs: create extension citext; null only when deleted
  email_verified_at timestamptz,
  status text not null default 'active',   -- active | deactivated | suspended | deleted
  created_at timestamptz not null default now()
);
create table identities (                  -- one row per linked provider login
  provider text not null,                  -- 'google', 'github', 'sso:<connection id>'
  provider_subject text not null,          -- the provider's stable user id, never the email
  user_id uuid not null references users(id),
  primary key (provider, provider_subject)
);
create table password_credentials (
  user_id uuid primary key references users(id),
  hash text not null,
  updated_at timestamptz not null
);
create table sessions (
  id uuid primary key,
  user_id uuid not null references users(id),
  token_hash bytea not null unique,
  created_at timestamptz not null,
  last_seen_at timestamptz not null,
  expires_at timestamptz not null,
  mfa_verified_at timestamptz
);
```

What the shape encodes:

- The internal `id` is opaque and permanent. Email is a mutable attribute and is not a key
  anywhere: not in foreign keys, not for provider links, not as an analytics ID.
- `(provider, provider_subject)` identifies a social or SSO login. Matching on email instead is how
  takeover through a recycled or unverified address happens.
- Password hashes sit in their own table, so `select *`, an ORM include or a logged user object
  cannot leak them. The same applies to MFA secrets, passkeys and recovery codes.
- Timestamps instead of booleans (`email_verified_at`, `mfa_verified_at`): investigations need to
  know when.
- Sessions store a hash of the token (`sessions-tokens.md`). One-time tokens for verification,
  reset, magic link and invitation share one table with a `purpose` column (`account-recovery.md`).
- Roles and organization membership never go on the user row (`authorization.md`).
- Compare emails case-insensitively and keep what the user typed for display. Do not strip dots or
  plus-tags for uniqueness; that is wrong outside Gmail. A canonical form for abuse counting is a
  separate column (`abuse-defense.md`).
- A deleted user must release the unique email, or the same person cannot sign up again. The
  deletion job nulls it (a unique column accepts many nulls); a check constraint such as
  `check (email is not null or status = 'deleted')` keeps it mandatory for everyone else.

When a library or provider owns these tables, keep its schema untouched and put app fields in a
profile table keyed by its user ID, so library upgrades do not collide with local migrations.

## Signup and email verification

1. Form: email, plus password if used, and nothing else. No "confirm email" field: verification
   catches typos and a second field does not. Use `autocomplete="username"` and
   `autocomplete="new-password"`, and allow paste.
2. Before sending: reject domains that cannot receive mail (no MX and no address record, or a
   null MX), suggest a fix for near-miss domains (`gmial.com`), and show the address on the
   "check your inbox" screen with an edit link.
3. Create the user unverified and send a code (6 digits, 10 to 15 minutes) or a single-use link
   (up to 24 hours). Throttle resends: one per 60 seconds and a handful per hour per address.
4. Verify inside the session that started signup: the code typed there, or a link whose landing
   page needs a button press that sends a POST. A GET that verifies lets a mail security scanner
   "verify" an address whose owner never saw the message.
5. Until verified, let the user explore but block anything that emails other people, publishes
   content, joins an organization by email domain, accepts an invitation or consumes costly
   resources.

Traps:

- **Pre-registration hijack.** An attacker signs up with the victim's email and a password and
  never verifies. Later the victim signs in with Google or verifies, and the attacker's password
  still works. When an email becomes verified by any route, delete credentials and sessions created
  while it was unverified, or use email-first signup where no credential exists before
  verification.
- **Squatting.** An unverified account must not block the real owner. A new signup for the same
  unverified email replaces the stale unverified account.
- A verification link that also signs the user in is a magic link and needs magic-link rules
  (`passwords-mfa-passkeys.md`).
- Fixing a typo must be possible before verification and restarts verification.

Bots, disposable domains and signup velocity: `abuse-defense.md`. Sending and deliverability:
`0x:email-notifications`.

## Enumeration and timing

Decide whether the existence of an account is sensitive. Health, dating, adult, political and
financial products: yes, and every row below is mandatory. Ordinary B2B: hide existence on login
and reset; the signup leak can be accepted with rate limits.

| Endpoint | Leak | Uniform behavior |
|---|---|---|
| Login | "No such user" versus "wrong password"; a faster answer for unknown users | One message ("Invalid email or password"); for unknown users verify against a fixed dummy hash with the same parameters |
| Reset, magic link, resend verification | "Email not found" | Always "If an account exists, an email is on its way"; enqueue the send so response time does not depend on existence |
| Signup | "Email already registered" | Email-first: always "Check your inbox"; an existing account receives a "sign in or reset" email instead |
| Passkey login | A username-first flow returns credential IDs only for real users | Discoverable credentials with an empty `allowCredentials` |
| Invitations, sharing by email | The inviter learns who has an account | The same visible result for members and strangers |
| Rate limiting | Limits applied only to real accounts | Key limits on the submitted identifier whether or not it exists |

A single form that takes email and password for signup cannot hide existence: accept the leak or
switch to email-first. Status code, body, headers and redirect target must match between the two
branches. Prove it with a diff of both responses and a latency comparison over a few hundred
requests.

## Testing auth flows

| Level | Scope |
|---|---|
| Integration (Vitest against a real database) | Session lifecycle, token consumption, every negative path below |
| End to end (Playwright) | One happy path per sign-in method, signup through verification, logout |
| Not end to end | A provider's own login pages: run a mock OIDC issuer, or call the callback with a token signed by a test key |

Negative paths that need a test from Launch on (at Prototype the happy paths suffice), each a
recurring incident class:

- Expired and already-used tokens are rejected (verification, reset, magic link, invitation).
- A token issued for one user or purpose does nothing for another user or purpose.
- After logout, replaying the old cookie returns 401; after a password change, other sessions die.
- A suspended or deleted user's existing session fails on the next request.
- An unverified account cannot perform the gated actions.
- An OAuth callback with a missing or wrong `state` is rejected.
- Responses for existing and unknown emails are identical; the rate limit triggers at its count.

Technique: inject a clock and advance it for expiry tests instead of sleeping. Capture mail with
a local SMTP catcher such as Mailpit and extract the link or code. Compute TOTP codes in the test
from a seeded secret. Drive passkey ceremonies with Chromium's virtual authenticator through a
Playwright CDP session (`WebAuthn.enable`, then `WebAuthn.addVirtualAuthenticator`). Create users
through a seed helper and reuse a saved `storageState`; only the auth specs go through the login
UI. General test structure: `0x:code-quality`.

## Migrating between auth systems

| Strategy | When | Cost |
|---|---|---|
| Bulk import with hashes | The old system exports hashes and the new one can verify that algorithm | One cutover; users notice nothing but a re-login |
| Lazy migration | No hash export, but the old system can still check a password | The old system runs for weeks; on each login verify there, then create the user and store a new hash |
| Forced reset | Neither is possible | A reset email to every password user, a support spike and some churn |

1. Inventory: hash algorithms with parameters, salt layout and any pepper; social identities with
   their provider subject IDs; MFA secrets; passkeys; email verification state.
2. Keep user IDs stable: reuse the old primary keys or store them as `legacy_id`. Foreign keys,
   analytics and billing records depend on them.
3. Check that provider subjects survive. Google's `sub` is the same across OAuth clients; Apple's
   is scoped to the developer team; Microsoft's `sub` differs per application (use `oid` with
   `tid`); Facebook IDs are per app. Identities created through the old vendor's shared OAuth
   credentials can only be re-matched by verified email.
4. MFA: TOTP secrets move only if exportable; otherwise re-enroll at next login after password
   and email-code proof. Passkeys are bound to the RP ID, which is a domain, not to the vendor:
   they move if credential IDs and public keys are exportable and the RP ID stays the same.
5. Sessions do not migrate. Cut over at a quiet hour; everyone signs in once.
6. Run lazy migration for 60 to 90 days (rule of thumb: most active users have signed in by
   then), then switch the remainder to reset-on-next-login.
7. Verify: user counts match, one test login per hash format and per provider passes, MFA is still
   enforced, and the old system stays read-only through a rollback window.

Weak legacy hashes (MD5, SHA-1) should be wrapped at once rather than waiting for logins; see
`passwords-mfa-passkeys.md`.

## Ask the user

- **Who signs in, and on what?** Consumers, business teams or developers; web only or also a
  native app. This decides the methods and whether Apple sign-in is needed. Default: Google plus
  email code on the web.
- **Will a customer ask for SSO or SCIM within a year?** It is the main reason to pay for a managed
  provider. Default: no; pick a library that can add SSO or sit behind an SSO bridge later.
- **Is it harmful if a stranger can tell that an email has an account?** It decides whether signup
  must be email-first. Default: hide on login and reset, accept the signup leak for ordinary B2B.
- **How many free users are expected against revenue per user?** Per-user auth pricing can exceed
  what a free user is worth. Default: a library when the free base is large.
- **Is a password wanted at all?** Passwordless removes reset and stuffing work but ties login to
  email delivery. Default: email code plus social sign-in; add passwords when users ask.
- **For a migration: is one forced re-login acceptable, and when?** Default: lazy migration at a
  quiet hour, one re-login, no password resets.
