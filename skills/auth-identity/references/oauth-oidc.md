# OAuth and OpenID Connect login

Read this when: adding Sign in with Google, GitHub, Apple or Microsoft, debugging a login flow
that fails on redirect, state or cookies, linking provider logins to accounts, validating ID
tokens, or letting AI agents and other clients act for a user.

## The flow and the OAuth 2.1 baseline

Use the auth library's provider integration. To read or debug it, know the flow: authorization
code with PKCE.

1. **Start.** Generate `state`, `nonce` and a random PKCE `code_verifier` (43 to 128 characters).
   Keep them on the server or in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie that lives about
   10 minutes. Redirect to the provider with `response_type=code`, `client_id`, `redirect_uri`,
   `scope`, `state`, `nonce`, `code_challenge` (base64url of the verifier's SHA-256) and
   `code_challenge_method=S256`.
2. **Callback.** If `error` is present, return to the login page with a neutral message
   (`access_denied` is the user pressing cancel). Compare `state` with the stored value. Exchange
   the code at the token endpoint from the server, sending `code_verifier` and the client secret.
3. **Finish.** Validate the ID token, find or create the identity by issuer and subject, apply the
   linking rules, create the session, delete the temporary cookie, redirect to a validated local
   path.

OAuth 2.1 (an IETF draft, not yet an RFC when this was checked) consolidates the security
practice of RFC 9700: PKCE for every client including confidential ones, no implicit grant, no
password grant, exact string matching of redirect URIs, no tokens in query strings, and refresh
tokens for public clients rotated or sender-constrained. Configure to that baseline and refuse
anything older.

Redirect rules:

- Register each redirect URI exactly, per environment, with no wildcards. A difference in scheme,
  host, port, path or trailing slash fails.
- Compute the redirect URI from a configured base URL, not from request headers. Behind a proxy
  the app sees `http://` or an internal host name.
- The post-login return target (`returnTo`, `callbackUrl`) accepts only a relative path that
  starts with a single `/` not followed by `/` or `\`. An open redirect here sends authorization
  codes and users to an attacker.
- Preview deployments have unpredictable hosts that cannot be registered. Either a stable auth
  host completes the flow and hands the result to the preview (auth libraries ship a
  redirect-proxy feature for this), or previews get a test-only sign-in and no social login.

## Provider facts

| Provider | Stable user key | Email trust | Traps |
|---|---|---|---|
| Google | `sub` | `email_verified` claim; authoritative for `gmail.com` and for Workspace domains (an `hd` claim is present) | A consent screen left in "Testing" admits only listed test users and expires refresh tokens within days. `hd` as a request parameter is only a hint: check the `hd` claim on the server when restricting to a domain. A refresh token comes only with `access_type=offline`, on first consent |
| GitHub | Numeric `id` from `GET /user`; login names change and are reused | `GET /user/emails` with scope `user:email`: take the entry with `primary` and `verified` both true. The profile `email` field may be null and is the wrong source | Plain OAuth, not OIDC, so no ID token. An OAuth App has one callback URL: one app per environment |
| Apple | `sub`, scoped to the developer team | Verified; may be a private relay address | The client secret is an ES256 JWT signed with a key file and valid at most 6 months: generate it at runtime or schedule rotation. The user's name arrives only on the first authorization, in the callback form body: store it then. Requesting name or email forces `response_mode=form_post`, a cross-site POST on which `SameSite=Lax` cookies are not sent. No `localhost` redirect URIs. Mail to relay addresses needs the sending domain registered with Apple |
| Microsoft | `oid` together with `tid`; `sub` differs per application | The `email` claim is not proof of ownership, since a tenant admin can set it freely. Never link accounts on it | With the `common` or `organizations` endpoint the issuer contains the user's tenant ID: validate it against the `tid` claim, not a fixed string. Client secrets expire: put the date in a calendar |

## Debugging a failing flow

Reproduce with the browser's network log preserved across navigations. Inspect the authorization
URL parameters, the `Set-Cookie` on the start response, the `Cookie` header on the callback
request, and the token endpoint's error body (`error`, `error_description`) in server logs. Never
log codes, tokens or secrets.

| Symptom | Cause | Fix |
|---|---|---|
| `redirect_uri_mismatch` | The URI sent is not identical to a registered one: `http` versus `https`, `www`, port, trailing slash, or built from an internal host | Copy `redirect_uri` out of the authorization URL, register exactly that, set the app's base URL |
| "State mismatch", "invalid state" or a missing PKCE verifier on callback | The temporary cookie did not come back: the flow started on one host and returned on another (`www` versus apex, preview versus production); `Secure` cookie over HTTP; `SameSite=Strict`; Apple's form POST; a start inside an iframe or in-app browser that finished elsewhere; a second flow overwrote the first; the cookie expired on a slow consent screen | Redirect to one canonical host before starting; `SameSite=Lax` (`None; Secure` for the Apple callback); key the cookie by state value; break out of iframes first |
| `invalid_grant` at the code exchange | The code was used twice (the callback ran twice: a client-side effect firing twice in development, a prefetch, a refresh), the code expired, `redirect_uri` differs between the two requests, or the verifier is wrong | Handle the callback on the server exactly once and redirect away; send the identical `redirect_uri` |
| `invalid_client` | Wrong or expired secret; for Apple an expired or mis-claimed client-secret JWT, or server clock skew | Rotate the secret; check the JWT claims and the clock |
| The callback succeeds but the app shows signed out, or loops | The session cookie was never stored: `Set-Cookie` stripped from a redirect response by a proxy or cache, a `Domain` mismatch, a cookie over 4 KB (provider tokens packed into it), or a `SameSite=Strict` session cookie, which is not sent on the redirect that ends a cross-site flow | Inspect `Set-Cookie` on the callback response; use `SameSite=Lax`; keep provider tokens out of the cookie |
| Works locally, fails in production | The other environment's client ID or secret, the production URI not registered, forwarded headers not trusted | Compare environment variables; register the URI; set the base URL |
| Google refuses with `disallowed_useragent` | The login opened in an embedded WebView, typically a social app's in-app browser | Open the system browser; show an "open in browser" hint |
| Only some Google users can sign in | Consent screen still in "Testing", or the user type set to "Internal" (one Workspace organization only) | Publish the app; set the user type to "External" |
| ID token rejected on `iss` (Microsoft) or on `exp` and `iat` | Tenant-specific issuer; clock skew | Check the issuer by `tid`; allow at most 60 seconds of tolerance and fix the clock |
| A second account appears for the same person | Another provider with the same email and no linking | The linking rules below |

## Account linking without takeover

The identity key is issuer plus subject. Email is an attribute the provider reports, with varying
honesty. Three takeover routes must be closed:

1. **Unverified email match.** A provider that does not prove email ownership, or a claim an
   admin can set, lets an attacker assert the victim's address and be linked into the victim's
   account.
2. **Pre-registration.** The attacker first creates a local, unverified account on the victim's
   address. The victim's later Google sign-in merges into it and the attacker's password still
   works.
3. **Linking CSRF.** A "connect provider" flow whose `state` is not bound to the session attaches
   the attacker's provider identity to the victim's signed-in account.

Rules:

- Link automatically at sign-in only when both hold. First, the provider asserts the email as
  verified and is authoritative for it: Google for Gmail and Workspace domains, and Apple; not
  Microsoft's `email` claim and not GitHub's profile email. Second, the local account's email is
  verified, or its unverified credentials and sessions are deleted in the same transaction.
- Otherwise neither link nor create a duplicate. Stop with: "An account with this email already
  exists. Sign in with the existing method, then connect the provider in settings."
- Connecting from settings needs the signed-in session, a recent step-up and the full `state` and
  PKCE checks. The callback attaches the identity to the session's user and to nobody else.
- An identity already attached to another user is refused, never merged silently. Merging two
  accounts is a support operation with verification.
- Do not overwrite the local email from the provider's claim at each sign-in. An attacker who
  changes the address at the provider would otherwise gain password reset here.
- Disconnecting needs another remaining sign-in method and step-up. Email the user whenever an
  identity is added or removed.
- Check the library's linking switch and trusted-provider list instead of assuming. In Auth.js
  the email-linking option is named `allowDangerousEmailAccountLinking` for a reason.

## ID token validation

A library performs the checks (`jose`, `openid-client`, or the auth library). The task is to make
sure every one of them is switched on.

```ts
import { createRemoteJWKSet, jwtVerify } from "jose";

const clientId = process.env.GOOGLE_CLIENT_ID;
if (!clientId) throw new Error("GOOGLE_CLIENT_ID missing"); // an undefined audience skips the check
const jwks = createRemoteJWKSet(new URL("https://www.googleapis.com/oauth2/v3/certs"));
const { payload } = await jwtVerify(idToken, jwks, {
  issuer: ["https://accounts.google.com", "accounts.google.com"],
  audience: clientId,
  algorithms: ["RS256"],
  clockTolerance: 60,
});
if (payload.nonce !== expectedNonce) throw new Error("nonce mismatch");
```

| Check | Expected value | What skipping it allows |
|---|---|---|
| Signature | Provider keys from the `jwks_uri` named in its discovery document (`/.well-known/openid-configuration`), cached, refetched on an unknown `kid` | Forged tokens |
| Algorithm | A fixed list in code | Downgrade and key-confusion attacks |
| `iss` | The exact issuer from discovery | Tokens from another issuer |
| `aud` | This app's client ID (and `azp` when there are several audiences) | A token issued to another app signing in here |
| `exp`, `iat` | Within tolerance | Replay of old tokens |
| `nonce` | The value sent from this browser | Replay or injection of a token from another session |
| `email_verified`, `hd`, `tid` | As the linking and tenant rules require | Unverified or out-of-tenant users |

Native apps and one-tap widgets hand an ID token to the client, which posts it to the backend.
The backend runs every check with the client ID of that platform as the audience. Accepting any
token the provider signed, whatever its audience, lets a token minted for someone else's app sign
in here. For the same reason an access token is never proof of login. With OAuth-only providers
such as GitHub, identity comes from the code exchange the server performed itself, followed by the
user endpoint.

## Scopes and provider tokens

- Sign-in needs `openid email profile` (GitHub: `read:user user:email`). Each further scope
  lengthens the consent screen and lowers conversion, and Google's sensitive and restricted
  scopes trigger verification and possibly a paid security assessment.
- Ask for data scopes (calendar, files, repositories) when the feature is first used, as a
  separate "connect" step, not at login.
- After sign-in the provider's access and refresh tokens are not needed, so do not store them.
  Many libraries persist them in the accounts table by default: switch that off or null the
  columns. A leaked database then gives no access to users' Google or GitHub data.
- Discard the ID token after validation. Nothing from the provider goes into the session cookie.
- When an integration does need stored tokens: encrypt them at rest with a key outside the
  database, keep refresh tokens on the server only, treat `invalid_grant` on refresh as "connection
  broken, ask the user to reconnect", and revoke at the provider on disconnect and on account
  deletion.

## Credentials for AI agents acting for users

An agent (an MCP client, a coding or browsing agent, an automation) never receives the user's
password, session cookie, or a long-lived full-access key pasted into a prompt or config file.
Anything in a model's context can be exfiltrated through prompt injection. Build none of this
before an agent or MCP integration is actually planned; apply all of it to the first one.

- Treat the agent as an OAuth client. The user grants access through authorization code with
  PKCE and a consent screen that names the agent and the scopes.
- Tokens are short-lived (minutes to an hour), bound to this API as audience (resource
  indicators, RFC 8707), and carry both the user and the client identity, so every audit entry
  reads "agent X for user Y".
- Scopes are narrow and split read from write, with per-resource grants (this project, not all
  projects) where the data model allows. Destructive, financial and permission-changing actions
  are excluded by default, or create a pending approval that the user confirms in the product UI.
- Effective permission is the intersection of the token's scopes and the user's current
  permissions, evaluated on every request. Removing the user's access removes the agent's.
- Refresh tokens rotate with reuse detection (`sessions-tokens.md`). Users see and revoke agent
  grants on the same page as their sessions.
- Per-token rate limits and spending caps bound the damage of a looping or hijacked agent.
- For an MCP server, read the current revision of the MCP authorization specification before
  building: it is revised often, and client registration in particular has changed between
  revisions. The stable core builds on OAuth 2.1: the server is a resource server that publishes
  protected-resource metadata (RFC 9728) and validates the token audience. It never forwards the
  client's token to an upstream API; to call downstream for the user it obtains a separate token
  (token exchange, RFC 8693).
- First-party agent features that run on the server act with the requesting user's authority.
  Pass the user's actor context into every tool call and run the normal policy checks. A tool
  that queries with a service role is privilege escalation waiting for a prompt injection
  (`0x:ai-features`).

Acting as an OAuth provider for third-party developers, and API keys: `0x:api-design`.

## Ask the user

- **Which providers do the users already have?** Each one adds setup, a consent screen and linking
  rules. Default: Google; add Microsoft for business users, GitHub for developers, Apple when
  there is an iOS app.
- **Is an iOS app planned?** It brings the Sign in with Apple obligation and a paid developer
  account. Default: add Apple when the app is built, not before.
- **Is only identity needed, or also the user's data at the provider?** Data scopes mean
  verification work, stored tokens and a bigger breach impact. Default: identity only; data
  access as a separate connect step.
- **Should accounts with the same email merge across providers?** Convenience against takeover
  risk. Default: merge only for verified emails from authoritative providers; otherwise ask the
  user to sign in first and connect in settings.
- **Will agents or third-party apps act for users, and which actions need a human approval?**
  Default: read scopes freely grantable, writes scoped per resource, destructive and financial
  actions confirmed in the UI.
