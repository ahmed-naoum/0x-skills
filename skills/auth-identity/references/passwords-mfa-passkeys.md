# Passwords, MFA and passkeys

Read this when: implementing a first or second authentication factor: password storage and
policy, email magic links and one-time codes, WebAuthn passkeys, TOTP, recovery codes, MFA
enforcement, or upgrading old password hashes.

## Password storage

Use the auth library's hasher when it meets the parameters below, otherwise a maintained Argon2
binding plugged into the library's custom hash and verify hooks. Read the library's default
before trusting it: Better Auth, for one, ships scrypt with its own parameters. Switching the
hasher on a live system needs the rehash-at-login path at the end of this file, or existing
users cannot sign in. The figures are the OWASP minimums; go higher when the hardware allows.

| Algorithm | Minimum parameters | Use when |
|---|---|---|
| Argon2id | 19 MiB memory, 2 iterations, parallelism 1 (or 46 MiB, 1 iteration) | Default |
| scrypt | N=2^17, r=8, p=1 (about 128 MiB per hash; OWASP lists equivalents with less memory and a higher p) | Argon2 is unavailable in the runtime; `node:crypto` ships scrypt but rejects these parameters until `maxmem` is raised above its 32 MiB default |
| bcrypt | Cost 10 or higher; input limited to 72 bytes | The project already has bcrypt hashes: keep verifying them and rehash at login |
| PBKDF2-HMAC-SHA256 | 600,000 iterations | FIPS-validated cryptography is required |

```ts
import { hash, verify } from "@node-rs/argon2";

const params = { memoryCost: 19456, timeCost: 2, parallelism: 1 }; // memoryCost in KiB
const stored = await hash(password, params); // PHC string: algorithm, parameters, salt, digest
const ok = await verify(stored, password);
```

- Tune upward until one hash takes roughly 100 to 250 ms on production hardware (a rule of
  thumb), then check memory: concurrent logins times memory cost must fit in the instance. A
  login burst at 64 MiB per hash on a 512 MB container is an out-of-memory crash. Cap hashing
  concurrency with a small semaphore.
- The stored string carries its parameters. After every successful login, rehash when they are
  below the current target. That is the entire parameter-upgrade mechanism.
- Accept at least 64 characters and cap the input (for example at 256) before hashing; unbounded
  input is a CPU denial of service.
- Normalize Unicode (NFKC) before hashing so the same password typed on two keyboards matches.
- A pepper (a secret mixed in through HMAC and held outside the database) helps only against a
  database-only leak and complicates rotation. Skip it until a secrets manager and a rotation
  procedure exist.
- Newer Node.js releases expose Argon2 in `node:crypto`. Use it in place of the binding only
  when the installed version documents it as stable.

## Password policy

- Minimum length 12 for password-only accounts (a house rule of thumb), 8 when MFA is mandatory.
  NIST SP 800-63B-4 requires 15 for password-only accounts and 8 as the floor with MFA; adopt
  its numbers where compliance drives the product.
- No composition rules, no periodic rotation, no hints, no security questions. Force a change only
  on evidence of compromise.
- Reject known-breached passwords at signup, change and reset with the Pwned Passwords range API:
  SHA-1 the password, send the first 5 hex characters to
  `https://api.pwnedpasswords.com/range/<prefix>` with the header `Add-Padding: true`, and search
  the response for the remaining 35 characters (the response is uppercase hex, so compare
  case-insensitively). Neither the password nor its full hash leaves the server. Use a timeout
  near one second and fail open; an outage must not block signups.
- Reject passwords that equal the email, its local part or the product name.
- When a password that just verified at login is in the breach set, treat the sign-in as risky:
  email-code challenge, then a forced change (`abuse-defense.md`).
- UI: allow paste and password managers, offer a show toggle, set `autocomplete` to
  `current-password` or `new-password`, never truncate and never restrict the character set.
- Passwords never appear in logs (failed attempts included) or in email, and no staff tool can
  read or set one.

## Magic links and one-time codes

Email sign-in makes the mailbox the only factor. That suits most products and is wrong for
high-value accounts unless MFA follows.

| | Link | Code |
|---|---|---|
| Secret | 32 random bytes, base64url | 6 digits, or 8 alphanumeric, from a CSPRNG |
| Lifetime | 10 to 15 minutes | 5 to 10 minutes |
| Use | Single use | Invalidate after 3 to 5 wrong tries |
| Storage | SHA-256 of the token | Hash plus attempt counter |
| Issuance | Limited per address and per IP | The same, plus a cap on codes per account per hour, since each new code is a fresh set of guesses |

- Put both in one message. The code typed into the tab that asked covers "mail opened on the
  phone, sign-in on the laptop".
- Bind the request to the browser that made it: set a short-lived `HttpOnly` cookie holding a
  nonce and store its hash with the token. Link opened in that browser: sign in. Opened anywhere
  else: sign nobody in; show "enter the code in the window where sign-in started" or offer to
  restart here.
- Do not build "click the link to approve the sign-in waiting on another device" unless the
  approver sees what is being approved (browser, device, approximate location) and presses a
  button. Otherwise an attacker starts a login for the victim's address and the victim, trained
  to click, signs the attacker in.
- Mail scanners and client previews fetch URLs. A GET must not consume the token: consume on a
  POST from a button on the landing page, or on GET only when the binding cookie is present.
- A new request invalidates earlier unused tokens of the same purpose.
- Landing page: `Referrer-Policy: no-referrer`, no third-party scripts, redirect to a clean URL
  after consuming. Keep token URLs out of analytics and error-tracker breadcrumbs.
- Code input: `autocomplete="one-time-code"` and `inputmode="numeric"`.
- The response is the same whether or not the address has an account.
- A code can be phished in real time by a fake page. Only passkeys resist that.
- Lifetimes under 5 minutes fail on slow mail. Delivery itself: `0x:email-notifications`.

## Passkeys (WebAuthn)

Use the auth library's passkey support or SimpleWebAuthn (`@simplewebauthn/server` with
`@simplewebauthn/browser`). Never parse attestation objects or verify signatures by hand.

| Option | Value | Reason |
|---|---|---|
| RP ID | The registrable domain (`example.com`), not `app.example.com` | Passkeys work on every subdomain; changing the RP ID later orphans every passkey. Any subdomain can then start a ceremony, so the server's expected-origin list names only the app's own origins |
| `residentKey` | `"required"` | A discoverable credential: sign-in without typing a username, and autofill works |
| `userVerification` | `"preferred"`; `"required"` where the passkey replaces password plus MFA | With user verification a passkey is two factors (device plus biometric or PIN); when relying on that, check the flag in the response on the server |
| `attestation` | `"none"` | Attestation adds prompts and privacy cost; only customers restricting authenticator models need it |
| `excludeCredentials` | The user's existing credential IDs | Prevents a second passkey on the same authenticator |
| `user.id` | Random bytes, at most 64, nothing personal | It is stored on the authenticator and comes back as `userHandle` |

Store per credential: credential ID, public key, signature counter, transports, the
backup-eligible and backup-state flags, AAGUID, a user-editable name, created and last-used times.
Challenges are random, single-use, held on the server and expire in about 5 minutes.

- **Autofill sign-in:** `autocomplete="username webauthn"` on the email field and
  `navigator.credentials.get` with `mediation: "conditional"`, after checking
  `PublicKeyCredential.isConditionalMediationAvailable()`. Passkey users get one tap; everyone
  else types as before. Keep an explicit "Sign in with a passkey" button as well.
- **Creation prompt:** right after a successful sign-in by another method and in security
  settings, never as a wall during signup.
- A passkey sign-in with user verification satisfies MFA. Do not ask for TOTP after it.
- **The fallback is the real security level.** If every passkey account can also sign in by email
  code, the account is as phishable as an email code. At Launch keep one other path (email code,
  or password with MFA) and block deletion of the last sign-in method. For high-value accounts
  let users opt into "passkeys and recovery codes only" and route lost access through
  `account-recovery.md`.
- Verification checks the expected origin and RP ID from configuration. Passing through whatever
  origin the request claims removes the phishing resistance.
- Synced passkeys report a signature counter of 0 forever. Flag a clone only when a stored nonzero
  counter goes backwards.
- `localhost` is a valid RP ID for development; passkeys made there do not exist on the real
  domain.

## Synced passkeys, multiple devices, cross-device sign-in

- Most passkeys sync through a provider (iCloud Keychain, Google Password Manager, password
  managers). The backup-eligible flag says the credential can sync and the backup-state flag says
  it currently is. Hardware security keys are device-bound: both flags are off.
- Use the flags for nudges, not gates. A user whose only credential is device-bound is prompted
  to add a second passkey or save recovery codes; a synced one survives a lost phone.
- Allow several passkeys per account, because people live in more than one ecosystem. List them
  with a name (derive the provider from the AAGUID where known), created and last-used times;
  rename and delete need step-up.
- Cross-device sign-in (a QR code scanned by the phone, with a Bluetooth proximity check) is
  offered by the browser when no local passkey matches. After one, offer "create a passkey on
  this device" so the next sign-in is local.
- A passkey deleted in the password manager leaves a dead row on the server, and the reverse
  leaves a dead entry in the manager. Where the browser supports the WebAuthn Signal API
  (`PublicKeyCredential.signalUnknownCredential`, `signalAllAcceptedCredentials`), call it to keep
  both sides in step; feature-detect first.
- Several domains for one product (a country domain, a rebrand): Related Origin Requests lets
  other origins use one RP ID through a `/.well-known/webauthn` file on the RP ID's domain.
  Check current browser support before depending on it.
- A synced passkey is as safe as the sync account's own recovery. Requiring device-bound keys
  needs attestation and an authenticator allowlist; skip that unless a contract demands it.

## MFA: factors and TOTP

| Factor | Resists phishing | Offer |
|---|---|---|
| Passkey or security key | Yes | Always, as the preferred second factor |
| TOTP app | No, a code can be relayed | Always, as the universal option |
| Email code | No, it equals mailbox control | Only as a new-device challenge for accounts without MFA |
| SMS or voice | No: SIM swap, number recycling, interception, per-message cost, toll fraud | Only when the audience cannot use the others; never the only option, never the recovery path for a stronger factor |

- TOTP parameters every authenticator app honors: SHA-1, 6 digits, 30-second period, a 160-bit
  secret in base32. Some popular apps silently ignore other values and the codes never match.
- Enrollment: show a QR code of `otpauth://totp/<Issuer>:<account>?secret=<base32>&issuer=<Issuer>`
  and the secret as text. The factor becomes active only after the user enters a valid code.
- Verification: accept the current time step and one on either side. Record the last accepted
  step and reject it and anything older, because a code is single-use. Back off after 5 failures.
- The secret must be recoverable, so encrypt it at rest with a key held outside the database.
- **Pending state, not a session.** After the first factor issue only a pending-login state valid
  for the MFA step (5 to 10 minutes). A session cookie issued before the second factor, with the
  UI merely redirecting to the code page, is the classic bypass. Test it by calling an
  authenticated endpoint with the pre-MFA cookie.
- Every path enforces MFA: password, magic link, social login, mobile, and the sign-in after a
  password reset. A reset proves mailbox control and nothing more; it never removes or skips MFA.
  Enterprise SSO sessions are the exception, because the customer's identity provider owns MFA.
- "Remember this device for 30 days" is a separate random token in its own `HttpOnly` cookie,
  stored hashed per user and device, listed with sessions, revoked on password or MFA change.

Sending SMS codes when the audience requires them: `0x:email-notifications`.

## Recovery codes

- Generate 10 codes at MFA enrollment, each about 80 bits from a CSPRNG: 16 characters from a
  32-symbol alphabet without look-alikes, displayed as `xxxx-xxxx-xxxx-xxxx`.
- Store only hashes; SHA-256 is enough at that entropy. Show the codes once with copy, download
  and print, and require confirmation that they were saved. Never email them.
- Consume atomically so two parallel requests cannot both succeed:

```sql
update recovery_codes set used_at = now()
where user_id = $1 and code_hash = $2 and used_at is null
returning id;
```

- A recovery code replaces the second factor only, never the first.
- After use: email notice, show the remaining count, prompt to regenerate at 2 or fewer left.
- Regenerating needs step-up and invalidates the whole previous set. Disabling MFA deletes them.
- Attempts share the failure counter and backoff of TOTP attempts.

## MFA policy

| Level | Decided by | When |
|---|---|---|
| Optional per user | The user | Launch |
| Required for owner and admin roles | The product | Launch, for anything holding customer data |
| Required for all members of an organization | The organization's admin, as a setting | When business customers ask; standard at Scale |
| Required for everyone | The product | Finance, health and infrastructure products |

- Enforce in the session guard, not in the UI. When policy applies and the session has no
  `mfa_verified_at`, only enrollment and verification routes respond. With several organizations,
  evaluate at access time: one session may enter organization B and be stopped at A.
- Rolling out to existing users: announce, show a banner with a deadline (7 to 14 days), then
  enforce at the next sign-in.
- Forced enrollment is an attack window: whoever knows the password at the next login enrolls
  their own device. Require an email code before a first enrollment and send an enrollment notice.
- SSO users are exempt from app MFA. Do not double-prompt them.
- Organization admins see who has MFA and can reset a member's factors (audited, member notified,
  re-enrollment needs email proof). They cannot read secrets.
- Policy can restrict methods (for example passkeys only for admins). Changing policy needs
  step-up and an audit entry.
- The company's own staff and admin tools need phishing-resistant MFA: `0x:web-security`.

## Upgrading legacy hashes

1. Tag every stored hash with its scheme: the PHC prefix, or an `algorithm` column.
2. On a successful login against an old scheme, hash the password just supplied with current
   Argon2id parameters and replace the stored value in the same request.
3. When the old scheme is fast (MD5, SHA-1, unsalted or single-round SHA-256), do not wait for
   logins. In a batch job compute Argon2id over each old hash (as hex text) and store it tagged,
   for example `argon2id+md5`. Login computes the old hash of the input, verifies the wrapper,
   and on success replaces it with a direct Argon2id hash. Nothing crackable at GPU speed remains
   in the database.
4. Set an end date (6 to 12 months). Wrapped hashes of users who never returned are deleted and
   those users go through reset.

Traps:

- A wrapped unsalted hash can be attacked with hashes from other breaches as candidates, without
  cracking them first. Wrapping is a stopgap; the direct rehash at login is the fix.
- Feed the inner digest to the outer hash as hex or base64 text. Raw bytes can contain NUL, which
  truncates the input in bcrypt and some bindings.
- Reproduce the old system's quirks exactly when verifying: lowercasing, trimming, truncation,
  character encoding, static salt or pepper.
- Verify only the scheme recorded on the user's row; never try several schemes in turn.
- Before cutover, test with real fixture hashes from the old system for every scheme.

## Ask the user

- **Passwords, or passwordless?** Passwordless removes storage, reset and stuffing work but ties
  sign-in to email delivery. Default: email code and social sign-in, passkeys as an upgrade,
  passwords only when the audience asks.
- **Who must use MFA?** Friction against takeover risk. Default: optional for users, required for
  owners and admins, an organization-wide switch for business customers.
- **Is SMS needed for this audience?** It costs per message and invites fraud. Default: no SMS;
  TOTP and passkeys only.
- **What is an account worth to an attacker?** It sets how strong the passkey fallback and
  recovery must be. Default: email-code fallback for ordinary accounts, recovery codes and delay
  for accounts that hold money or sensitive data.
- **Does a compliance framework or customer questionnaire dictate password and MFA rules?**
  Default: the rules above; the frameworks themselves are in `0x:privacy-compliance`.
