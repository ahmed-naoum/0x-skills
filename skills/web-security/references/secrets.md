# Secrets, key management and cryptographic primitives

Read this when: deciding where a credential lives, sharing or rotating one, responding to a secret that was committed or leaked, turning on encryption at rest, arranging emergency access, or choosing between a random token, a hash, an HMAC, encryption and a signature.

## Where secrets live

| Stage | Runtime secrets | Human-held credentials |
|---|---|---|
| Prototype | The host's encrypted environment variables; a git-ignored `.env.local` holding development-only keys | A password manager |
| Launch | Host environment store or a secrets manager (Doppler, Infisical, 1Password, AWS Secrets Manager or Parameter Store, Google Secret Manager) as the single source, synced to hosts and CI; separate values per environment; no production secrets on laptops | Team password manager with role vaults |
| Scale | Secrets manager with per-service identity, an access audit log and automated rotation; short-lived credentials wherever the provider supports them | SSO everywhere; a tested break-glass procedure |

Rules for every stage: one source of truth instead of five dashboards edited by hand; a different credential per environment and per service, so that revoking one has a small blast radius and logs show which service acted; development and staging never hold production keys; presence and shape validated at startup (`0x:ci-cd-release`, `environments-config.md`).

## Where secrets leak

| Place | Mechanism | Prevention |
|---|---|---|
| Client bundle | Any variable with the public prefix (`NEXT_PUBLIC_`, `VITE_`) is inlined into JavaScript at build time; a server module imported by a client component drags its values along | `import "server-only"` in every module that reads a secret; the bundle check below |
| Repository | `.env` committed, real values in `.env.example`, keys in fixtures, notebooks and scripts | `.gitignore` covers `.env*` except the example; secret scanning |
| Container image | `ARG`, `ENV` and `COPY .env` persist in layers and in `docker history` | BuildKit secret mounts (below); `.dockerignore` lists `.env*` and `.git` |
| CI | Shell tracing, debug output, a secret echoed after an encoding that defeats masking, artifacts containing environment dumps | Secrets scoped to the job and step that needs them; OIDC instead of stored cloud keys |
| Logs and error tracker | Logged request objects, headers, connection strings, full URLs with tokens | A redaction list at the logger and the tracker: `authorization`, `cookie`, `set-cookie`, `password`, `token`, `secret`, `api_key` |
| URLs | Query-string tokens land in access logs, `Referer` headers, browser history and analytics | Tokens in headers or POST bodies; single-use and short-lived when a link must carry one |
| Infrastructure state | Terraform state stores resource secrets in plain text | Encrypted remote backend with restricted access: `0x:cloud-infrastructure` |
| Chat, tickets, documents | Pasted keys persist in search and exports | Share through the password manager only |
| Coding agents and LLM tools | An agent that can read `.env` can send its contents wherever its tools reach | Deny rules for secret files: `0x:ai-coding-agents` (`permissions-governance.md`) |
| Anything shipped to users | Mobile and desktop apps, browser extensions, public source maps | A secret in a distributed artifact is public; proxy through the server |

"Publishable" and "anon" keys are designed to be public. Their safety rests entirely on the server-side rules behind them (row-level security, allowed origins, restricted scopes), so confirm those rules before treating such a key as harmless.

```bash
# after a production build: must print nothing
rg -l -e '[sr]k_live_' -e 'AKIA[0-9A-Z]{16}' -e 'PRIVATE KEY' -e 'sb_secret_' .next/static
# prefixes catch known formats only; the complete check is each server secret's real value (bash)
for v in DATABASE_URL STRIPE_SECRET_KEY SESSION_SECRET; do
  [ -n "${!v}" ] && rg -q -F -- "${!v}" .next/static && echo "LEAKED: $v"
done
```

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN="$(cat /run/secrets/npm_token)" pnpm install --frozen-lockfile
```

```bash
docker build --secret id=npm_token,env=NPM_TOKEN .
```

## Secret scanning and push protection

- Turn on the source host's secret scanning with push protection for every repository, at the organization level so that new repositories inherit it. Push protection rejects the push before the secret reaches the remote, the only point at which a leak costs nothing to fix. On GitHub this is free for public repositories and a paid feature for private ones; check the current packaging.
- Add an open-source scanner (gitleaks or TruffleHog) as a pre-commit hook and a CI job regardless. It covers private repositories without the paid feature and catches the secret before the commit. Run it once over the full history when adopting it.
- Scanners match known formats. Generic passwords and home-made tokens pass unseen, so give tokens the product issues a recognizable prefix (`acme_live_...`) and register the pattern as a custom rule.
- Cloud and payment providers scan public repositories for their own keys and may restrict a leaked key automatically. Treat that as an alarm, not as remediation; the key still has to be rotated.
- A decoy credential (canary token) placed in the repository, the CI variables and a laptop's config raises an alert when someone uses it. Minutes to set up and almost no false positives; worth having from Launch.

## A secret leaked: the sequence

Order matters. The usual mistake is cleaning the history first.

1. **Treat it as compromised from the moment of exposure.** Public repositories are harvested by bots within minutes. A private repository, a CI log or a chat message counts too when more identities can read it than should hold the key.
2. **Revoke or rotate now.** Issue a new credential, deploy it, verify traffic on it, revoke the old one. If the exposure was public, abuse is in progress or deployment is slow, revoke immediately and accept the outage.
3. **Rotate the neighbors.** Everything in the same file, commit, CI environment or machine was readable in the same act.
4. **Audit use during the exposure window** in the provider's logs, filtered by the credential's ID: cloud audit trail, payment-provider request log, source-host audit log, database connection log, LLM and email provider usage. Look for new users, keys, roles and tokens (persistence), resources created in any region, data reads and exports, changed webhooks or payout details, and usage spikes.
5. **Remove what the attacker added**: credentials, OAuth apps, deploy keys, forwarding rules, webhooks.
6. **Decide whether it is an incident.** If the credential could read personal data and use cannot be ruled out, follow `logging-breach-response.md`.
7. **Purge the history last, as hygiene** (commands below). It mitigates nothing: clones, forks, caches and scrapers already hold the value.
8. **Close the cause**: push protection, the pre-commit hook, moving the value into the secrets manager.

```bash
# in a fresh clone; filter-repo removes the origin remote, so re-add it before pushing
git filter-repo --invert-paths --path .env          # drop a file from all history
git filter-repo --replace-text replacements.txt     # each line: LITERAL_SECRET==>REMOVED
git push --force --all && git push --force --tags
```

After the force-push the old commits stay reachable by hash on the host, and in pull-request refs, until the host garbage-collects them: ask the host's support to purge, and have collaborators re-clone. Forks are not rewritten.

## Rotation without downtime

The pattern is dual validity. Rotating in place causes an outage as long as the deploy.

| Secret kind | Sequence |
|---|---|
| Issued by a provider: API key, database password, OAuth client secret | Create a second credential → deploy it everywhere → confirm the old one is unused (the provider's last-used data, or logs) → revoke the old one |
| Verified by the application: session or JWT signing key, webhook signing secret, API keys the product issues | Accept new and old for verification → deploy → sign with new → after the longest token lifetime, drop old. Tag tokens with a key ID so the verifier picks the right key |
| Encryption key for stored data | Store a key ID with each ciphertext; write with the new key and read with either; re-encrypt in the background; retire the old key when no row references it. With envelope encryption only the wrapped data keys are re-encrypted |
| Database password where the provider offers no overlap | Create a second role with the same grants, switch the application, then drop or re-password the first |

Schedule: calendar rotation of long-lived secrets is worth less than three other things, in this order.
Eliminate static secrets where short-lived credentials exist. Rotate on events: a person with access leaves, a
laptop is lost, a vendor reports a breach, a leak is suspected. Rehearse: rotate each critical secret at least
once a year (a rule of thumb; a compliance framework may set its own interval) so that the procedure is known to
work. A secret that has never been rotated cannot be rotated quickly during an incident.

Keep an inventory, names only, in the repository: secret, issuer, where it is used, owner, rotation procedure, last rotated. It doubles as the checklist for offboarding and breach response.

## Short-lived, scoped credentials

| Path | Use instead of a static key |
|---|---|
| CI → cloud | OIDC federation: the workflow exchanges its identity token for a role session. The trust policy pins the repository and the branch or environment, never a wildcard over the organization (`0x:ci-cd-release`, `pipeline-security.md`) |
| Workload → cloud | The platform's attached identity (instance, task or service-account role); no access keys in environment variables |
| Human → cloud | SSO sessions that expire in hours; no personal long-lived access keys (`0x:cloud-infrastructure`, `iam-accounts.md`) |
| Automation → source host | App installation tokens, or fine-grained tokens with an expiry scoped to named repositories; not classic full-scope tokens |
| Package publishing | Registry trusted publishing from CI over OIDC, which leaves no publish token to steal |
| Application → third-party API | Restricted keys limited to the resources and actions used; one key per service and environment |
| Browser or customer → object storage | Presigned URLs valid for minutes, for one object and one method |
| Human → database | Personal roles, read-only by default, time-boxed elevation (`accounts-admin-hardening.md`) |

Scope along five axes: which actions, which resources, which identity, for how long, from where. When a provider offers only all-powerful static keys, keep the key in one server-side service and have everything else call that service.

## Team password manager

- Adopt one at the first shared credential (1Password or Bitwarden, business tiers). Vaults follow roles, not people: for example founders and break-glass, engineering production, engineering development, marketing, finance. Grant access to groups.
- Nothing is shared through chat, email or documents. A one-off share uses the manager's expiring link.
- Shared logins exist only where the service has no multi-user support. Everywhere else each person has an account, behind SSO where available.
- For a shared login, store its TOTP seed in the manager so that MFA does not depend on one phone. That puts both factors in one place, acceptable only because the manager itself is protected by a hardware key or passkey.
- The manager needs two administrators or a documented recovery path. One person who alone can recover it is a single point of failure for the company.
- Offboarding: remove the person, then rotate what they could read; business tiers report which items a member accessed.
- Developers load secrets through the manager's CLI so that `.env` files hold references, not values: `op run --env-file=.env -- pnpm dev`, with entries such as `DATABASE_URL=op://Engineering/app-db/url`.

## Recovery codes and break-glass access

The solo founder is the single point of failure: a lost phone during an incident, or an unreachable founder when the domain renewal fails.

1. List the root-of-trust accounts: primary email or identity provider, registrar and DNS, cloud root, source-host organization owner, password manager, payment provider, bank, app-store accounts.
2. For each: two owners where the service allows it; two hardware keys or passkeys registered, one stored off-site; recovery codes printed.
3. Store recovery material where a second person can reach it without the first person's devices: a sealed envelope in a safe or deposit box, plus the manager's emergency-access feature or a second administrator. At the solo stage the second person is a lawyer, a family member or a trusted advisor, holding written instructions.
4. Never keep an account's recovery codes only inside that account: the manager's recovery kit inside the manager, mailbox recovery codes in that mailbox's drive.
5. A break-glass identity does not depend on SSO, is used for nothing else, and any use of it alerts everyone. The cloud root user fits: hardware MFA, no access keys, an alarm on sign-in.
6. Test twice a year (rule of thumb) by having the second person actually recover one account. An untested path is assumed broken.

## Encryption at rest

Turn on provider-managed encryption for every store, and verify instead of assuming: database, disks and volumes, object storage, snapshots, backups, log archives, laptops. Some stores can be encrypted only at creation, and converting an existing one means snapshot, encrypted copy, restore; choose it on day one. The usual hole is the copy made by hand: a `pg_dump` in a bucket or on a laptop.

```bash
aws ec2 enable-ebs-encryption-by-default   # per region; affects new volumes only
```

What it covers: stolen or decommissioned media, a mis-shared raw snapshot, the compliance question. What it does not: anyone holding database credentials, and any injection, still reads plaintext. It is necessary and nearly free, not sufficient.

| Level | Use when | Cost |
|---|---|---|
| Provider-managed keys | Default for everything | None |
| Customer-managed KMS key | A contract or framework demands it, key-use audit logs are needed, or deleting the key must destroy the data | Fees per key and per call; a deleted or mis-permissioned key is unrecoverable data loss |
| Application-level field encryption | A few fields whose leak is disproportionate: customers' third-party tokens and API keys, government IDs, bank details, TOTP seeds, health notes | The field cannot be indexed or searched (add a keyed-hash column for equality lookup); key management and rotation become application code |

For field encryption: authenticated encryption with the row's identity as associated data, so that a ciphertext cannot be moved to another row; a key ID stored beside the ciphertext; the key held in the secrets manager or wrapped by KMS (envelope encryption). Passwords are hashed, not encrypted: `0x:auth-identity` (`passwords-mfa-passkeys.md`).

## Choosing a primitive

| Need | Use | Not |
|---|---|---|
| Unguessable token: session ID, reset link, invite, API key | 32 bytes from the CSPRNG: `randomBytes(32).toString("base64url")` | `Math.random()`, timestamps, sequential or time-ordered IDs, a hash of user data |
| Store a token the product issued | SHA-256 of the token, looked up by hash; show the plaintext once | Plaintext; a slow password hash (pointless for high-entropy input, and it prevents indexed lookup) |
| Store a user's password | Argon2id through the auth library (scrypt where the runtime lacks Argon2; bcrypt only for hashes that already exist); parameters in `0x:auth-identity` (`passwords-mfa-passkeys.md`) | Any fast hash; encryption |
| Integrity or deduplication of non-secret data | SHA-256 | MD5 or SHA-1 where an attacker chooses the input |
| Prove a message came from a holder of a shared secret: webhooks, signed URLs, unsubscribe links | HMAC-SHA-256 over the raw bytes plus a timestamp; constant-time comparison | `sha256(secret + message)`; `===` on signatures; signing re-serialized JSON |
| Keep data confidential under a key the product holds | Authenticated encryption: AES-256-GCM, or XChaCha20-Poly1305 through libsodium | AES-CBC or CTR without a MAC, ECB, anything unauthenticated |
| Let others verify without being able to forge: tokens across organizations, license files, release artifacts | A signature: Ed25519, or ECDSA P-256 or RSA where interoperability requires | HMAC, since every verifier could forge |
| Encrypt to someone's public key | libsodium sealed boxes, `age`, HPKE | Raw RSA encryption |
| Key from a password | Argon2id or scrypt as a KDF | A single hash |
| Several keys from one master key | HKDF-SHA-256 with a distinct `info` per purpose | One key reused for two purposes |
| Protect data in transit | TLS | Anything custom |

```ts
import { createCipheriv, createDecipheriv, createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export function seal(key: Buffer, plaintext: Buffer, aad: Buffer): Buffer {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  cipher.setAAD(aad);
  const ct = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  return Buffer.concat([iv, cipher.getAuthTag(), ct]); // 12-byte IV, 16-byte tag, ciphertext
}

export function open(key: Buffer, blob: Buffer, aad: Buffer): Buffer {
  const decipher = createDecipheriv("aes-256-gcm", key, blob.subarray(0, 12), { authTagLength: 16 });
  decipher.setAAD(aad);
  decipher.setAuthTag(blob.subarray(12, 28));
  return Buffer.concat([decipher.update(blob.subarray(28)), decipher.final()]); // throws if altered
}

export function verifyHmac(secret: string, rawBody: Buffer, signatureHex: string): boolean {
  const expected = createHmac("sha256", secret).update(rawBody).digest();
  const given = Buffer.from(signatureHex, "hex");
  return given.length === expected.length && timingSafeEqual(given, expected);
}
```

Traps:

- GCM fails catastrophically when an IV repeats under one key: confidentiality and forgery resistance are both lost. Use a fresh random 12-byte IV per message and rotate the key well before 2^32 (about four billion) messages, the limit usually quoted for random IVs; XChaCha20-Poly1305's 24-byte nonce removes the concern.
- `timingSafeEqual` throws on unequal lengths; compare lengths first.
- Base64, hex and JWT payloads are encodings, readable by anyone. A JWT is signed, not encrypted; pin the accepted algorithm on verification (`0x:auth-identity`, `sessions-tokens.md`).
- A version 4 UUID from `crypto.randomUUID()` (122 random bits from the CSPRNG) is acceptable as an unguessable token; v4 UUIDs from other generators carry no such guarantee, and time-ordered UUIDs (v1, v7) are identifiers, not secrets.
- Never design a protocol, a padding scheme or a comparison. If the need is not in the table, the answer is a maintained library (libsodium) or a provider feature.

## Ask the user

- **Who can recover the company's critical accounts if you are unreachable for a week?** Break-glass needs a named second person. Default: nobody yet; set up sealed recovery codes and a trusted contact now.
- **Was the leaked secret in a public repository, and since when?** It sets the exposure window for the audit. Default: assume public and fully harvested.
- **Is there budget for a team password manager and a secrets manager?** Both are small monthly costs against the most common breach path. Default: password manager now, the host's environment store until Launch.
- **Do contracts or frameworks require customer-managed keys or fixed rotation intervals?** Otherwise provider-managed keys and event-driven rotation are right. Default: no such requirement.
- **Which stored fields would be disproportionately damaging if the database leaked?** Those get field-level encryption. Default: third-party tokens and API keys held for customers, and MFA seeds.
