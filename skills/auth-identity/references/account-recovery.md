# Account recovery and lifecycle

Read this when: designing password reset, email change, lost-device or lost-passkey recovery,
account deletion or deactivation, organization ownership transfer or support procedures for
account changes, or when a hijacked account must be recovered.

Recovery is authentication by another route. An account is exactly as strong as its weakest
recovery path, and attackers prefer "forgot password" and the support inbox to the login form.

## Password reset

1. **Request.** Take an email address and always answer "If an account exists, a reset link is on
   its way", with the same timing. Limit per account and per IP (`abuse-defense.md`). Change
   nothing on the account yet: no lock and no invalidated password, or anyone can deny service
   to any user.
2. **Token.** Issue by the token rules below, valid 15 to 60 minutes (30 is a sound default). A
   new request invalidates earlier unused reset tokens.
3. **Link.** Build the URL from the configured base URL, never from the request's `Host` header.
   A forged host puts the attacker's domain into a genuine email (reset poisoning).
4. **Landing.** GET renders the form and consumes nothing, because mail scanners fetch links.
   Send `Referrer-Policy: no-referrer` and load no third-party scripts.
5. **Submit.** In one transaction consume the token, store the new hash after the breach check,
   and revoke every session, refresh token and remembered device. Then send "your password was
   changed" to the account's address.
6. **Afterwards.** Send the user to the normal sign-in, which runs MFA when enrolled. A reset
   proves mailbox control and nothing else; it never removes, skips or resets MFA.

Variants: an account without a password (social or passkey only) gets an email naming its
sign-in method, while the screen shows the same generic sentence. An SSO-enforced member gets a
pointer to the organization's sign-in. An unknown address can be sent "no account uses this
address", which helps people with several addresses and tells the screen nothing. A completed
reset may mark the email verified, since it proved inbox control.

Traps: a token logged by a proxy or analytics tool because it sits in the URL (scrub those
routes); a user ID in the URL trusted separately from the token; a reset token accepted by the
email-change or verification endpoint; long-lived tokens waiting in mailboxes; reset by security
question, or by SMS to a number that can be ported.

## Email change

Changing the email and then resetting the password is how a hijacker makes a takeover permanent.

1. Require step-up with the strongest enrolled factor.
2. Store the new address as pending. The login email does not change yet.
3. Send a confirmation code or link to the new address and, at the same time, a notice to the
   current address: "A change to this account's email was requested. If this was not you, secure
   the account."
4. On confirmation, inside the signed-in session where possible, re-check uniqueness and swap.
5. Send "your email was changed" to the old address with a revert link valid for days to weeks.
   Reverting restores the old address, revokes all sessions and forces a password reset.
6. Revoke other sessions and invalidate outstanding reset tokens and magic links.
7. For accounts holding money or sensitive data, block payout changes, ownership transfer and
   deletion for 24 to 72 hours after the change.

If the new address already belongs to another account, the requester still sees "confirmation
sent" and that address receives a notice instead. Linked social identities are not affected by
an email change; say so in the UI. A phone number that serves as a factor gets the same sequence.

## One-time tokens

The same rules serve reset, verification, magic link, email change and invitation.

```ts
import { createHash, randomBytes } from "node:crypto";

const token = randomBytes(32).toString("base64url");            // goes into the email
const tokenHash = createHash("sha256").update(token).digest();  // goes into the database
```

```sql
update auth_tokens set used_at = now()
where token_hash = $1 and purpose = 'password_reset'
  and used_at is null and expires_at > now()
returning user_id;
```

- The single `update ... returning` is the consume step. Two parallel requests cannot both
  receive a row.
- SHA-256 is the right hash here. The input is 256 random bits, so slow hashing buys nothing.
- Look the token up by its hash. No secret is compared in application code, so timing is moot.
- Each row has a purpose, a user, an expiry and `used_at`. Consume checks the purpose.
- A scheduled job deletes expired rows.

| Purpose | Lifetime |
|---|---|
| Sign-in code | 5 to 10 minutes |
| Magic link | 10 to 15 minutes |
| Password reset | 15 to 60 minutes |
| Email-change confirmation | 1 to 24 hours |
| Email verification at signup | 24 hours |
| Invitation | 7 days |

Stateless signed tokens (JWT or HMAC) cannot be single-use without state. Where a library uses
them, the signature must cover something that changes on use, such as the current password hash.
Prefer database tokens.

## Deletion, deactivation and reactivation

| State | Set by | At sign-in | Data | Ends by |
|---|---|---|---|---|
| Deactivated | The user | Offers reactivation | Kept, hidden from others | The user confirming |
| Suspended | Staff or automation | Shows a notice and an appeal route | Kept; public content unpublished | Staff only |
| Pending deletion | The user | Offers to cancel | Kept until the grace period ends | Cancel link or sign-in |
| Deleted | The deletion job | Impossible | Erased or anonymized | Never |

1. Step-up, then show what will be erased, what is kept and why, and when the subscription ends.
2. Resolve blockers: sole ownership of an organization with other members (transfer or delete it
   first), an active subscription (`0x:payments-billing`), an outstanding balance or payout.
3. Mark `deletion_requested_at`, revoke all sessions and tokens, and email a confirmation with a
   cancel link. Grace period 7 to 30 days (14 is a reasonable default). The delay turns deletion
   by a hijacker into a recoverable event.
4. The job erases or anonymizes profile, credentials, identities, sessions and the personal
   workspace, propagates to the auth provider, payment customer record, mailing lists, analytics,
   search indexes and object storage, and lets backups age out (`0x:data-stores`).
5. Keep what law or safety requires and nothing more: invoices and tax records for their
   statutory period (it varies by country; ask an accountant), a minimal hashed identifier for
   bans, audit entries with the actor replaced by a tombstone. Erasure duties and deadlines:
   `0x:privacy-compliance`.

- Content created inside a shared organization belongs to the organization. Keep it and show the
  author as "Deleted user".
- Do not cascade-delete the user row. Null the personal fields, keep the ID as a tombstone, and
  free the email so the person can register again as a new account.
- Revoke provider grants on deletion. Apps on the App Store must offer deletion inside the app,
  and apps using Sign in with Apple are expected to revoke the Apple token.
- Deactivation and deletion are not exits from a ban. A suspended account stays suspended and
  its ban identifier survives deletion (`abuse-defense.md`).
- Deletion must be easy to find in settings. A hidden or support-only path draws complaints to
  regulators and app stores.

## Security notifications

Send to the address that was on file before the change; for an email change, to both.

| Event | Notify |
|---|---|
| Password changed or reset; email change requested or completed | The user, always |
| MFA enabled or disabled; a factor, passkey or recovery-code set added, removed, regenerated or used | The user, always |
| Sign-in from a new device | The user, when the browser has no prior device cookie for the account |
| Provider identity linked or unlinked; API key or personal token created; app or agent authorized | The user, always |
| Deletion requested; ownership transferred; role raised to admin or owner | The user, plus all owners for organization events |
| SSO or domain settings changed; payout or bank details changed; full data export | All owners |
| Any change made by support staff | The user, stating that support made it |

- These are not marketing and cannot be switched off in preferences. Send them on the
  transactional stream through a queue with retries (`0x:email-notifications`).
- Content: what happened, when, from which device and approximate location, and one "this was
  not me" action that leads into a signed-in or recovery flow. Nothing happens on GET, and the
  message contains no secret.
- Too many new-device emails train users to ignore them. Rely on a device cookie, not IP changes.
- Write every event to an audit table as well: actor, action, target, old and new value where
  safe, IP, user agent, time. The user's security-activity page reads from it, and hijack
  recovery depends on it. Keep at least 90 days.

## Lost passkeys and MFA devices

Recovery routes, strongest first:

1. Another enrolled factor: a second passkey, a synced passkey on a new device, TOTP elsewhere.
   Prompt users to enroll two at setup.
2. Recovery codes.
3. For organization members, an organization admin resets the member's factors (the admin has
   MFA, the action is audited, the member is notified). The member re-enrolls at the next
   sign-in after an email code.
4. Delayed self-service reset. The user proves password and mailbox control and requests an MFA
   reset. A waiting period starts (24 to 72 hours as a floor, longer for valuable accounts).
   Notices go to the email and to every signed-in session, and repeat. Any successful MFA
   sign-in, or a click on "cancel", aborts it. At the end the factors are removed, all sessions
   are revoked and sensitive actions stay blocked for a further period.
5. Support, with the verification procedure below.

Backdoors that are not offered: an emailed link that removes MFA at once (it reduces MFA to
mailbox control); SMS fallback on an account protected by passkey or TOTP; security questions; a
support agent disabling MFA on a plausible message; remembered-device cookies that never expire.

- Passkey-only accounts recover through an email code plus, where MFA policy applies, the delay.
  The first passkey created after recovery triggers a notice and the same cooldown.
- A recovery request never reveals to an unauthenticated visitor which factors exist.
- Some accounts are unrecoverable, and saying so at enrollment is honest design: "Save the
  recovery codes. Without a factor or a code, access cannot be restored."
- Accounts without MFA recover by email reset alone. The delay applies to users who chose, or
  are required to have, a second factor.

## Support identity verification

The easiest takeover is a persuasive message to the founder's inbox: "I lost access to my email,
please change it to this one." Write the policy before the first such request arrives.

- Email, ownership and MFA never change on request alone, never under time pressure (urgency is
  a red flag) and never through a direct database edit. An audited admin action makes the change
  and the account's existing contacts are notified.
- Staff cannot read or set passwords and cannot act as the user without an audit trail.

Require more than one kind of evidence for a change of email or owner:

| Evidence | Strength | Notes |
|---|---|---|
| The request comes from a signed-in session | Strong | An in-app channel whose user identity is signed by the server, not a typed email address |
| Control of the registered email | Strong | With it, self-service already works |
| Control of the organization's verified or custom domain, shown by a DNS TXT record | Strong for organizations | |
| Confirmation by another owner or admin | Strong for organizations | |
| Payment proof through the payment provider: access to the billing email, or a code placed in a small charge's statement descriptor | Medium | Last four digits and a charge date are not secret enough |
| Knowledge of account details: creation date, project names, recent activity | Weak | A supplement only; a partial breach reveals these |
| Government ID | Avoid | Forgeable, nothing on file to match it against, and a liability to store |

Then apply a waiting period (24 to 72 hours) with notices to every existing contact, make the
change through the admin tool, revoke sessions, force a reset and record the ticket.

Ownership disputes (co-founders splitting, agency against client, an employee who registered
with a personal address): follow the records, namely who pays, who controls the domain and who
signed the contract, and ask for a written request from an authorized signatory. When the claim
is contested and the records do not settle it, freeze changes and let the parties resolve it
legally. Terms of service should state that an organization account belongs to the entity
(`0x:privacy-compliance`). Staff tooling and its access control: `0x:web-security`.

## Organization ownership transfer

- Allow several owners and nudge organizations with one owner and many members to add a second.
  That removes most transfer emergencies.
- Voluntary transfer: the owner starts it with step-up and picks an existing member with a
  verified email, and MFA where policy requires. The recipient accepts within 7 days. Roles swap
  in one transaction, and all owners and admins are notified.
- Billing is separate from ownership. Prompt for a new payment method and billing contact when
  the card belonged to the departing owner (`0x:payments-billing`).
- A sole owner cannot leave or delete their account before transferring or deleting the
  organization.
- Unreachable owner (left the company, died, locked out), in order of preference: another owner
  acts; the organization's verified domain plus a signatory's written request; proof from the
  billing contact. Each passes the support verification above, with a waiting period and
  notices to the old owner's address. With none of these there is no transfer.
- SCIM deactivating the sole owner must not orphan the organization. Keep the membership
  suspended, alert the organization's admins and flag it for support; promote a successor only
  by the rules above.
- Integrations, API keys and webhooks belong to the organization, not to the user who created
  them, or they break when that person leaves.

## Hijacked account recovery

In place beforehand, at Launch: the audit table with old values, a lock switch per account,
revoke-all, and soft delete on user content.

1. **Contain.** Lock the account. Revoke sessions, refresh tokens, API keys, OAuth and agent
   grants and remembered devices. Pause outgoing effects: scheduled sends, payouts, webhooks.
2. **Identify the owner.** Use contact details from before the first suspicious change, taken
   from the audit log. Recovery goes to the original email, not the current one.
3. **Reconstruct.** From the first anomalous sign-in onward list every change: email, password,
   factors, passkeys, recovery codes, linked identities, tokens, invited members, roles, sharing
   links, webhook and forwarding targets, billing, exports, deletions, content sent.
4. **Undo.** Restore the email. Remove attacker-added factors, identities, members, invitations,
   links, webhooks and keys. Restore deleted data from soft delete or backup
   (`0x:postgres-database`). Reverse fraudulent charges or payouts (`0x:payments-billing`).
5. **Re-secure.** The owner sets a new password, re-enrolls MFA and receives new recovery codes.
   Advise securing the email account first; it is the usual root cause.
6. **Find the entry.** Credential stuffing (look for other accounts hit from the same sources,
   `abuse-defense.md`), phishing, session cookies stolen by malware (a reset does not help while
   the device is infected), support social engineering, or a product vulnerability, which makes
   this a security incident (`0x:web-security`).
7. **Notify.** The owner gets a summary of what was accessed and changed. If other people's
   personal data was exposed, breach-notification duties may apply (`0x:privacy-compliance`).

For many accounts at once: invalidate the affected password hashes so those users pass through
reset, revoke their sessions, notify them and prompt MFA enrollment at the next sign-in.

## Ask the user

- **What is an account worth to an attacker: money, data, reach?** It sets the delays and how
  strict support must be. Default: email reset for ordinary accounts; delays and cooldowns once
  accounts hold money or sensitive data.
- **If someone loses every factor and cannot be verified, is losing the account acceptable?** The
  alternative is a backdoor for attackers. Default: yes, and the enrollment screen says so.
- **How long is the deletion grace period, and what must be retained?** Retention is a legal and
  tax question. Default: 14 days, then erase all but invoices and a hashed ban marker.
- **Who decides a contested organization ownership?** Default: the paying entity and domain
  controller per the records; freeze when they conflict.
- **May support change an email or reset MFA at all?** Default: only with two kinds of evidence,
  a waiting period, notices to existing contacts and an audit entry.
