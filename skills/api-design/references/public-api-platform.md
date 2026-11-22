# Public API and developer platform

Read this when: opening the product to outside developers or to AI agents: deciding whether to
have a public API at all, issuing API keys, publishing docs and SDKs, offering a sandbox, adding
OAuth apps, or building an MCP server.

## Whether and when to commit

A public API is a promise with no end date. Every published field becomes something that cannot
be renamed, every quirk becomes a dependency, and each integrator adds support load, abuse
surface and a constraint on refactoring. It also raises switching costs, unlocks integrations
the team will never build, and is increasingly how customers' agents reach the product.

| Stage | Default |
|---|---|
| Prototype | No public API. The data model is still changing weekly; anything published now is wrong |
| Launch | Still no by default. Offer exports, an import, and one or two integrations the team owns (a Zapier-style connector, a webhook). Open a clearly labeled beta API to named design partners if deals depend on it |
| Scale | Public, documented, versioned API when the signals below are present |

Signals that it is time: customers script against the private endpoints or scrape the UI; deals
stall on "does it have an API"; the same integration request arrives from several customers;
the product's value depends on data flowing in or out. One loud prospect is not a signal; a
bespoke export or a design-partner beta answers that.

Before committing, confirm these exist or are planned, because each is hard to retrofit:
tenant-scoped authorization in the domain layer (not in the UI), the conventions in
`api-style.md` and `requests-responses.md`, idempotency and rate limits per key, a versioning
and deprecation policy, per-key usage logging, and an abuse and terms-of-use position
(`0x:privacy-compliance`, `terms-policies.md`).

Do not publish the internal API as is. Private endpoints are shaped for one UI's screens. Design
a smaller public surface over the same domain layer, covering the top integration tasks, and
grow it on request. Shipping less is reversible; shipping more is not.

## API keys

Keys are the default credential for server-to-server access. Use OAuth only for the case in the
last section.

```ts
import { randomBytes, createHash } from "node:crypto";

const secret = `sk_live_${randomBytes(32).toString("base64url")}`;  // shown to the user once
const keyHash = createHash("sha256").update(secret).digest("hex");  // stored, unique-indexed
```

- **Format**: a recognizable prefix that encodes type and environment (`sk_live_`, `sk_test_`),
  then at least 128 bits from a CSPRNG. The prefix lets secret scanners, log redaction and
  support identify a leaked key, and stops test keys being used against live by mistake.
  A distinctive prefix is also what makes enrollment in code hosts' secret-scanning programs possible.
- **Store only a hash.** A plain SHA-256 is correct here: the key is high-entropy, so a slow
  password hash adds latency to every request and no security, and a deterministic hash allows
  lookup by index. Keep the first few characters and last four separately for display.
- **Show the full key once** at creation. Afterward the UI shows name, prefix, last four, scopes,
  created by, created at, last used and expiry.
- **Keys belong to the organization or workspace**, with the creating user recorded. A key tied
  to a person breaks production integrations when that person leaves.
- **Scopes**: at minimum read-only versus read-write; add resource-level scopes
  (`invoices:read`) when customers ask. Default new keys to the least privilege the UI flow allows.
- **Rotation without downtime** requires several active keys per account: create new, deploy,
  revoke old. A "roll" action that issues a replacement and expires the old key after a chosen
  overlap is the same thing made convenient.
- **Expiry**: offer it at creation; whether keys expire by default is a product choice. An
  expiring key needs warning emails before it lapses, or the expiry is an outage generator.
- **Revocation is immediate.** If key lookups are cached, the cache TTL is the revocation delay:
  keep it at seconds, or invalidate on revoke.
- **Record `last_used_at`** (updated at most once a minute per key, not per request) so
  customers can find and delete dead keys, and record key ID on every request log line.
- **Transport**: `Authorization: Bearer <key>` over HTTPS only. Never accept keys in query
  strings, which end up in access logs, browser history and referrers. Reject plain HTTP rather
  than redirecting, since the key has already been sent in clear by then.
- **Never log the key**, and strip `Authorization` from error-tracker payloads.
- **Browser-exposed keys** are a different kind: a publishable key that only identifies the
  account and can do nothing sensitive. A secret key in frontend code is public.

Authentication failures return 401 in the standard problem shape, with the same response for
"unknown key" and "revoked key". Hashing choices and secret storage are detailed in
`0x:web-security`, `secrets.md`; who may create keys is an authorization question for `0x:auth-identity`.

## Reference docs and the first call

Generate the reference from the OpenAPI document; write the guides by hand. A reference written
separately from the spec is wrong within a release.

- **Renderer**: any maintained OpenAPI renderer or docs platform (Scalar, Redoc, Mintlify and
  similar). Choose on whether it shows request examples per language, a try-it console and search.
- **Every operation has a realistic example request and response**, and CI validates each
  example against its schema. Wrong examples are the most copied text in the docs.
- **Runnable**: a copyable curl for every operation; when signed in, prefill the reader's own
  test key. A console that calls the sandbox from the page removes the setup step entirely.
- **Hand-written guides** that the spec cannot express: authentication, errors and the `code`
  catalog, pagination, idempotency and retries, rate limits, webhooks and signature
  verification, versioning policy, and a quickstart per main use case.
- **Changelog** with dates, linked from the reference; it is where deprecation notices live.
- **Publish the OpenAPI file itself** at a stable URL, and offer the docs as plain Markdown
  (an `llms.txt` index is a common convention). Much integration code is now written by coding
  agents, and they read these, not the rendered site.

Time to first successful call is the metric for a developer platform. A capable developer who
cannot make one call work in about five minutes (a rule of thumb) often does not return.

1. Self-serve signup and a test key with no sales call, no approval queue and no card.
2. The quickstart is one screen: the key, one curl command that works when pasted, the expected
   response. The first call is a harmless read or a create in test mode.
3. Errors teach: a 401 says which header was expected; a 422 names the field; every problem
   `type` links to its page.
4. Instrument the funnel: signup, key created, first 2xx, first write, first live-mode call.
   The largest drop is the next thing to fix.
5. Run the quickstart from a clean machine before every launch and after any auth change.

## An MCP server for AI agents

The Model Context Protocol lets customers' AI assistants and agents use the product through
tools. Treat it as another surface over the domain layer with a very different consumer: a model
that reads descriptions, pays for every token returned, and may be steered by hostile content.

| Decision | Rule |
|---|---|
| Transport | Remote server over the Streamable HTTP transport for a hosted product; stdio only for tools run on the user's machine. The protocol is versioned by date and revisions break things: the 2026-07-28 revision removed protocol-level sessions and the initialize handshake so each request is self-contained, while deployed clients may still speak earlier revisions. Keep the server stateless (anything a later call needs is in its arguments or the database), build on the official SDK at a version covering the revisions the target clients use, and read the current specification changelog and deprecation list before implementing (the same revision deprecated Roots, Sampling and Logging, so do not build on them) |
| Auth | OAuth as the protocol specifies for remote servers, with the MCP server as a resource server that accepts only tokens issued for itself (check the audience) and never forwards a client's token to another API. The server publishes OAuth Protected Resource Metadata so clients can find the authorization server. How clients register changes between revisions (2026-07-28 prefers Client ID Metadata Documents and deprecates dynamic client registration), so choose an auth provider that documents support for the revisions the target clients speak. A scoped API key in a header is acceptable where clients support it. Never a shared credential |
| Tool granularity | Tools are tasks, not endpoints. A handful of well-chosen tools (`search_invoices`, `create_invoice`, `get_account_summary`) outperforms a generated mirror of 80 operations, which floods the model's context and makes it pick wrongly |
| Descriptions | Written as instructions to a model: what the tool does, when to use it and when not, what each parameter means, with constrained types and enums. The description is the documentation |
| Results | Small and structured: names alongside IDs, only fields useful for the next step, small default page sizes with a cursor, and an explicit note when output was truncated |
| Errors | Say what to do next ("no customer matches; call search_customers first") rather than returning a bare code; the model will act on the text |
| Safety | Read-only scope by default; write and destructive tools behind explicit scopes and marked with the protocol's tool annotations; irreversible operations either absent or two-step (prepare, then confirm with a token) |

- **Authorization is enforced server-side per call, as the end user**, exactly as in the API.
  Tool descriptions and annotations are hints to the client, not controls.
- **Content returned by tools is untrusted input to the model.** Anything users can write
  (names, comments, ticket text) can carry instructions. Do not combine, in one session's reach,
  private data, attacker-writable content and a tool that can send data out, without a human
  approval step. `0x:ai-features`, `guardrails.md`, covers prompt injection.
- **Rate-limit and meter per token**, with tighter budgets than for human-driven clients: an
  agent in a loop issues calls faster than any integration.
- **Mark agent-originated actions in the audit log**, so "who did this" has an answer.
- Build with the official SDK for the server's language, and test with a real client: watch a
  model attempt the top five tasks and rewrite descriptions wherever it picks the wrong tool
  or passes wrong arguments. Evaluate, do not guess.

Designing agents that call tools is `0x:ai-features` (`agents-tools.md`); Claude API tool-use
syntax is `claude-api`.

## SDKs

Skip until Scale, or until Launch if customers are asking for one. A correct OpenAPI file, good curl examples and published types
let developers and their coding agents generate what they need. Ship SDKs when integrators
repeatedly get the same things wrong (retries, pagination, signature verification), or when the
main audience expects `npm install`.

- **Generate from the OpenAPI document**, with a hosted generator (Fern, Speakeasy and similar)
  or an open-source one (OpenAPI Generator). This market changes hands: Stainless shut down its
  hosted generator after being acquired in 2026, and Fern became part of Postman the same year.
  Before committing, check the vendor's current ownership, license and pricing, and confirm the
  generated code is yours and builds without their service. Hand-written SDKs fall behind the
  API within months; a solo team cannot maintain several by hand.
- **Start with the languages the customers use**, usually TypeScript and Python. Each language
  is a permanent maintenance and support line.
- **What an SDK must add beyond typed calls**: automatic retries with backoff and jitter that
  honor `Retry-After`; an idempotency key generated once per logical call and reused on retry;
  auto-paginating iterators; typed errors exposing `code` and `request_id`; configurable
  timeouts; webhook signature verification; a `User-Agent` carrying SDK name and version; open
  enums and tolerant decoding.
- **Version the SDK with semantic versioning, independently of the API version.** State which
  API version each SDK release targets. A regenerated SDK that renames a method is a breaking
  SDK release even when the HTTP API did not change, which is why `operationId` and schema
  names must stay stable.
- **Release from CI** when the spec changes: generate, run tests against the sandbox, publish,
  append to the changelog. Read the generated diff before publishing a major version.

## Sandbox and test mode

Developers need a place to make mistakes. Without one they test in production with real
customers' data, or do not integrate.

| Design | How | Trade-off |
|---|---|---|
| Test mode in the same system | Keys carry a mode; every row has a mode column; every query is scoped by it | One deploy, identical behavior, easy switch. A scoping bug mixes test and live data, so enforce it in the data layer exactly like tenant isolation |
| Sandbox as a separate tenant | Each account can create a sandbox workspace: an ordinary tenant flagged as test | Reuses existing tenant isolation with almost no new machinery. Default for a small team |
| Separate sandbox deployment | A second environment with its own database and hostname | Strongest isolation; drifts from production, doubles operations, separate accounts and keys |

Whatever the design: test keys are visibly different (`sk_test_`) and are rejected by live
resources and the reverse; no real-world side effects occur (no real charges, emails or SMS to
arbitrary recipients, no third-party calls that cost money), but webhooks do fire so integrations
can be tested end to end; documented magic inputs trigger each important error and slow path;
data can be reset; limits are lower than live; and sandbox usage is excluded from billing and
business metrics.

## OAuth for third-party apps

Add OAuth only when third parties build apps that act on behalf of the product's users: a
marketplace, integrations built by other vendors, or remote MCP clients. For a customer calling
their own account from their own server, API keys are simpler and sufficient.

- **Do not write the authorization server.** Use the auth provider's or a maintained library's
  implementation, configured to the OAuth 2.1 profile (still an IETF draft: OAuth 2.0 plus the
  security best current practice, RFC 9700); the protocol's failure modes are subtle
  (`0x:auth-identity`, `oauth-oidc.md`).
- **Flows**: authorization code with PKCE for every client type. No implicit flow, no password
  grant. Client credentials only for app-level access with no user.
- **Redirect URIs** are pre-registered and matched exactly, with no wildcards or prefix matching.
- **Tokens**: short-lived access tokens (minutes to an hour), refresh tokens that rotate on use
  with reuse detection, bound to the app, the user and the tenant. Store them hashed, like keys.
- **Scopes and consent**: the consent screen names the app, its publisher and each requested
  permission in plain words; scopes are the same vocabulary as API-key scopes.
- **The granted access never exceeds the granting user's own permissions**, evaluated at request
  time, so a user who loses access takes the app's access with them.
- **Users and admins can see and revoke** authorized apps; revocation kills refresh tokens at once.
- **App registration**: a developer console issuing client IDs and secrets, with secret rotation.
  A public listing or marketplace needs a review step, which is a staffing commitment.

## Ask the user

- **Which customers or deals need an API, and for what tasks?** Decides whether to commit and
  what the first surface covers. Default: do not publish until at least a few independent
  customers name concrete integrations; start with those tasks only.
- **Is API access part of every plan, or a paid feature?** Affects key issuance, limits and
  support load. Default: available on paid plans with per-plan rate limits (`0x:pricing-monetization`).
- **What may agents do without a human confirming?** A risk decision for the MCP server.
  Default: read-only by default, writes opt-in per scope, nothing irreversible.
- **Should API keys expire by default?** Security posture versus integration breakage.
  Default: no forced expiry, optional expiry at creation, prominent last-used data and easy rotation.
- **Will third parties build apps for the product's users?** Only then build OAuth and an app
  console. Default: not yet; API keys only.
- **How much support will API users get?** Sets expectations in docs and terms. Default:
  documentation and email, no guaranteed response time below the top plan.
