# Sessions, cookies and tokens

Read this when: deciding how signed-in state is stored, carried, refreshed and revoked: session
cookies, JWTs, refresh tokens, CSRF defense, cookie scope across subdomains and environments,
mobile clients, the active-sessions page, or re-authentication before sensitive actions.

## Which mechanism

| Client and topology | Use | Not |
|---|---|---|
| Browser, app and API on one origin (Next.js) | Opaque session ID in a cookie, session row in Postgres | JWT in `localStorage` |
| Browser SPA, API on a sibling subdomain | The same cookie session; better, proxy the API under the app origin | Bearer tokens handled by page script |
| Browser SPA, API on another site or a third-party token issuer | Backend-for-frontend: a small server holds the tokens, the browser holds only a session cookie | Tokens in browser storage |
| Native mobile app | Authorization code with PKCE in the system browser; short access token plus rotating refresh token in the OS keystore | Embedded WebView login, long-lived static token |
| Several backend services that verify identity without a shared store | Short-lived JWT access token minted from the server-side session | A long-lived JWT as the session |

## Cookie attributes

```http
Set-Cookie: __Host-session=<opaque>; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=2592000
```

- **Value:** at least 128 bits from a CSPRNG (`crypto.randomBytes(32).toString("base64url")`).
  The database stores its SHA-256, so a leaked table or backup holds no usable sessions.
- **`HttpOnly`:** script cannot read the cookie. XSS can still act inside the open page, but it
  cannot carry the session away. A token in `localStorage` or `sessionStorage` is readable by
  every script on the origin, including a compromised dependency or analytics tag, and stays
  valid elsewhere until it expires.
- **`__Host-` prefix:** browsers accept the cookie only with `Secure`, `Path=/` and no `Domain`.
  It is host-only, and a sibling subdomain cannot overwrite it (cookie tossing).
- **`SameSite=Lax`, set explicitly:** browsers differ in what they assume when it is absent.
  `Strict` makes users arriving from an email or another site look signed out on the first page.
  `None` is only for real cross-site embeds and then meets third-party-cookie blocking.
- **Size:** browsers cap a cookie near 4 KB. Session data belongs in the row, not the cookie.
- **Caching:** a shared cache must never store a response that sets or depends on the cookie.
  Send `Cache-Control: private, no-store` on authenticated pages (`0x:web-networking`).

## Session lifecycle

| Event | Action |
|---|---|
| Login, MFA completion, privilege change | Issue a new session ID (prevents fixation); never accept an ID from a URL |
| Each request | Look up by token hash; reject if expired, revoked or the user is not active |
| Activity | Slide the expiry only after half the idle window has passed; write `last_seen_at` at most every few minutes |
| Logout | Revoke the row on the server, then clear the cookie with identical `Path` and `Domain`; POST only |
| Password change or reset, email change, MFA change | Revoke every other session and refresh token of the user |
| Suspension, deletion, removal from an organization | Revoke all; membership is re-checked per request in any case |

Lifetimes are rules of thumb to settle with the user:

| Product | Idle timeout | Absolute timeout |
|---|---|---|
| Consumer and typical SaaS | 14 to 30 days | 60 to 90 days |
| Admin consoles, finance, health data | 15 to 60 minutes | 8 to 12 hours |
| Enterprise SSO sessions | 8 to 24 hours | The same, so deactivation at the identity provider takes effect |

Traps: a logout that only clears the cookie leaves a stolen copy valid. Checking the session only
in middleware and not where data is read leaves every route the matcher misses unauthenticated
(`authorization.md`).

## CSRF

CSRF applies to every state-changing request authenticated by a cookie. It does not apply to
requests authenticated by an `Authorization` header that script must attach. Layer the defenses,
because each covers a gap in the others:

1. No state change on GET. `SameSite=Lax` still sends cookies on top-level GET navigation.
2. `SameSite=Lax` blocks cross-site POSTs. It does not block same-site ones: any sibling
   subdomain (marketing site, customer subdomain, forgotten staging host) is same-site.
3. Verify the origin on every non-GET request: `Origin` equals the app's own origin, or
   `Sec-Fetch-Site` is `same-origin`. Reject when present and wrong. When both are absent, reject
   on cookie-authenticated routes unless a known client needs otherwise.
4. Add a token (synchronizer token, or a double-submit value signed with a server secret and
   bound to the session) when defense in depth matters. A plain double-submit cookie is defeated
   by a subdomain that can set cookies.

Framework facts: Next.js Server Actions accept only POST and compare `Origin` with the host.
Behind a proxy that changes the host, list the public origin in `serverActions.allowedOrigins`
in `next.config` (nested under `experimental` in the docs checked; follow the installed
version) and keep that list narrow. Route Handlers have no CSRF protection, so add the origin
check in shared code. Auth libraries protect their own endpoints only.

Also protect the login form (login CSRF signs the victim into the attacker's account and captures
what they then enter), the logout endpoint, and OAuth callbacks through `state` (`oauth-oidc.md`).
A CORS policy that reflects any origin together with `Access-Control-Allow-Credentials: true`
cancels all of this; CORS configuration belongs to `0x:web-security`.

## Server sessions or JWTs

| | Opaque session (default) | JWT as the session |
|---|---|---|
| Revocation | Immediate: revoke the row | Not until expiry, unless each request checks a denylist, which is a session store again |
| Per request | One indexed read, cacheable for seconds | Signature check, no I/O |
| Stale data | None | Roles, membership and suspension frozen until reissue |
| Failure modes | Store outage | Key leakage, algorithm confusion, oversized cookies, a logout that does nothing |
| Sessions page, sign out everywhere | Built in | Needs server-side records anyway |

Choose JWTs only when something must verify identity without reaching the session store (other
services, edge functions). Then keep the lifetime at 5 to 15 minutes, mint the token from a
server-side session that remains the thing being revoked, and state plainly that revocation lags
by the token lifetime. Destructive and financial actions check the server-side session directly.

JWT verification, through `jose` or the provider SDK: pin the accepted algorithm in code and
never read it from the token; verify `iss`, `aud` and `exp`; never fetch keys from a URL named
inside the token; treat the payload as public. Managed providers generally run this hybrid: a
very short-lived JWT refreshed from a session they can revoke.

## Cookie scope across subdomains and environments

- Default to host-only cookies (no `Domain`). `Domain=example.com` sends the session to every
  subdomain, including vendor-hosted ones reached by CNAME (docs, status, support) and dangling
  DNS records that a stranger can claim.
- App on `app.example.com` with the API on `api.example.com`: the two are same-site, so
  `SameSite=Lax` cookies flow, but the API needs credentialed CORS and the cookie is either
  host-only on the API host (server rendering on the app host then never sees it) or widened
  with `Domain=example.com`. Serving the API under the app origin through a rewrite avoids both
  and keeps `__Host-`.
- User-controlled content and customer subdomains that can run script must live on a different
  registrable domain (`example-usercontent.com`). On the same one, tenant script is same-site for
  CSRF purposes and can set cookies for the parent domain.
- Customer custom domains cannot share a cookie with the main app. Sign in per domain: redirect
  to the central login and back with a single-use code (30 to 60 seconds) exchanged on the
  server. Never pass a session token in a URL.
- Staging on `staging.example.com` receives every `Domain=example.com` production cookie, so a
  staging XSS steals production sessions. Put non-production on a separate registrable domain, or
  at least use host-only cookies with a different name per environment.
- Preview deployments under a shared platform suffix (for example `*.vercel.app`) are separate
  sites from each other because the suffix is on the Public Suffix List. Cookies and OAuth
  redirect URIs do not carry over (`oauth-oidc.md`).
- Local development: some browsers refuse `Secure` and `__Host-` cookies over plain HTTP even on
  `localhost`. Run local HTTPS (mkcert), or switch cookie name and flags by environment in one
  place.
- Browsers that apply schemeful same-site treat `http://` and `https://` as different sites.
  Redirect to HTTPS before anything sets a cookie.

## Refresh token rotation and reuse detection

Needed for native apps, third-party clients and the JWT hybrid. A browser app on cookie sessions
needs no refresh tokens.

```sql
create table refresh_tokens (
  id uuid primary key,
  family_id uuid not null,          -- one family per login
  user_id uuid not null,
  token_hash bytea not null unique,
  used_at timestamptz,
  expires_at timestamptz not null,
  revoked_at timestamptz
);
```

- Each refresh returns a new refresh token and marks the presented one used.
- A token presented a second time means two parties hold it. Revoke the whole family, end the
  session, log a security event and notify the user. Do not guess which party is legitimate.
- False positives come from the client: two tabs or threads refreshing at once, or a response
  lost on a bad network followed by a retry with the old token. The client serializes refresh
  behind one in-flight promise; the server answers a repeat of the just-used token within a short
  grace window (about 10 to 30 seconds) with the same successor instead of revoking.
- The family has an absolute lifetime (30 to 90 days, longer for mobile) that rotation does not
  extend, plus an idle expiry. Access tokens live 5 to 15 minutes. Refresh tokens are stored
  hashed. In a browser a refresh token lives only in an `HttpOnly` cookie scoped to the refresh
  path.

## Active sessions and devices

This needs server-side session rows. Skip the page at Prototype. Build it at Launch when accounts
hold money, customer data or admin power; otherwise it can wait for Scale. Revoking every session
on password change is due at Launch either way.

- Show per session: browser and OS parsed from the user agent, approximate location from the IP
  (labeled approximate), sign-in method, created and last-active times, and a "this device" mark.
- Actions: revoke one, revoke all others, effective on the next request. Offer "sign out other
  devices" inside the password-change flow.
- Revoking a session also ends what hangs off it: refresh token families, remembered-device MFA
  tokens, and open WebSocket or SSE connections (close them, or re-validate on a timer). Mobile
  app tokens appear in the same list.
- Personal API tokens and OAuth grants to other apps are listed on the same page but separately.
  They are not sessions and do not die at logout.
- A new-device sign-in email links here (`account-recovery.md`). Stored IPs and user agents are
  personal data and need a retention period (`0x:privacy-compliance`).

## Native and mobile clients

- Sign in through the system browser (`ASWebAuthenticationSession` on iOS, Custom Tabs on
  Android) with authorization code and PKCE. An embedded WebView exposes credentials to the app,
  lacks the user's existing sessions and passkeys, and is refused by some providers (Google
  answers `disallowed_useragent`).
- Return to the app through a claimed HTTPS link (Universal Links, App Links) where possible; any
  app can register the same custom URL scheme. PKCE makes an intercepted code useless.
- A mobile app is a public client. Nothing shipped in the binary is secret, so no client secret.
- Storage: iOS Keychain with a `ThisDeviceOnly` accessibility class so tokens are not restored
  onto another device; Android Keystore-backed encrypted storage. In React Native or Expo use
  `expo-secure-store` or `react-native-keychain`, never AsyncStorage, preferences or a file.
- iOS Keychain items survive app deletion. On first launch after install, detected by a flag in
  ordinary app storage, wipe stored tokens; otherwise a reinstalled app opens signed in.
- Requests carry `Authorization: Bearer`, so CSRF does not apply. On a 401: one serialized
  refresh, one retry, otherwise sign out. Mobile users expect to stay signed in for months, so
  use a long family lifetime with reuse detection rather than short sessions.
- Biometric unlock gates local access to the stored token. It is not server-side authentication
  unless a key or passkey ceremony is involved; sensitive actions need a real step-up.
- Logout revokes the refresh family on the server, then deletes local storage. App attestation
  (App Attest, Play Integrity) is a Scale-stage abuse control, not an auth mechanism.

## Step-up authentication

The session records how and when the user last proved identity (`authenticated_at`,
`mfa_verified_at`, method). Sensitive actions require that proof to be recent, checked on the
server inside the action.

```ts
const STEP_UP_WINDOW_MS = 10 * 60_000;
if (Date.now() - session.lastStrongAuthAt.getTime() > STEP_UP_WINDOW_MS) {
  throw new StepUpRequiredError(); // the client opens a re-auth dialog, then retries the action
}
```

- Gate: changing email or password, adding or removing MFA factors and passkeys, viewing recovery
  codes, creating API keys, changing payout or bank details, exporting all data, deleting the
  account or organization, transferring ownership, editing SSO configuration, impersonation.
  Skip step-up at Prototype; from Launch every item on this list that exists is gated.
- Window: 5 to 15 minutes. A "sudo mode" that lasts hours protects nothing against a stolen
  session. The most destructive actions require proof per action.
- The factor is at least as strong as the account's strongest. An account with MFA steps up with
  MFA, not with the password alone. A passkey with user verification is the lowest-friction
  strong option.
- Users without a password re-authenticate through their provider with `prompt=login` or
  `max_age=0`, and the server verifies a fresh `auth_time` in the returned ID token. Not every
  provider honors these: Google's documented `prompt` values have not included `login`. A token
  without a recent `auth_time` means no step-up happened, however the redirect looked. Those
  users step up with a passkey, or with an email code, treated as weak.
- Step-up updates a timestamp on the existing session. It does not extend the session lifetime.
- The UI prompt is a convenience and the server check is the control. Test it by calling the
  action directly with a session whose strong-auth time is old.

## Ask the user

- **How long should people stay signed in?** Convenience against exposure on shared or stolen
  devices. Default: 30 days idle and 90 days absolute; 30 minutes idle for admin or financial
  surfaces.
- **Is there, or will there be, a mobile app or another non-browser client?** It adds refresh
  tokens and a token endpoint. Default: shape the session table to hold them and build them when
  the client exists.
- **Do customers get subdomains or custom domains, or host their own content?** It decides cookie
  scope and whether a separate content domain is needed now. Default: user content on a separate
  domain from the first day, because moving it later is expensive.
- **Must access end the moment an account is disabled?** Enterprise and regulated buyers ask for
  it. Default: yes, with opaque sessions checked per request.
- **Which actions would hurt most from a stolen session?** They define the step-up list. Default:
  the list above.
