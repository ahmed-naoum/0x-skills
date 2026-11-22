# Versioning and evolving an API

Read this when: changing an endpoint, payload or event that has consumers not deployed together
with the server (third parties, mobile apps, other teams, long-open browser tabs), or planning a
deprecation or a new API version.

## The working model

The best versioning strategy is to almost never need a new version. Nearly every change can be
made additively; a breaking change is a project with a customer-communication plan, and a new
major version is a second product to run. Order of preference:

1. Add alongside (new field, new endpoint, new event type, new optional parameter).
2. Add alongside and deprecate the old thing, removing it only when usage is measured at zero
   or the published notice period has passed.
3. Gate the new behavior per consumer (a pinned version or an opt-in flag) while the default stays.
4. Break everyone at once. Acceptable only for a security fix, or when there are no outside consumers.

Who the consumers are decides how much of this applies:

| Consumers | Compatibility window | Mechanism |
|---|---|---|
| Own web UI, same deploy | Minutes to days (open tabs, cached bundles, rolling deploys) | Expand and contract across two deploys; no version numbers |
| Own mobile apps | Months to years; old versions never fully disappear | Additive only; minimum-supported-version check with a forced-upgrade path |
| Named partners | Whatever is agreed | Additive; direct notice before any removal |
| Public developers | The published policy | Versioning scheme and deprecation policy below |

Even the "same deploy" case breaks: a server function whose arguments change shape fails for
every tab loaded before the deploy. Ship the server accepting both shapes, then the client, then
remove the old shape (`0x:ci-cd-release`, `deploy-rollback.md`, covers the deploy side).

## Additive change and tolerant readers

Compatibility is a deal with two halves, and the client's half must be written down on day one,
because it cannot be imposed later:

**Clients must** ignore unknown response fields; treat unknown enum values as a generic
"other" case rather than crashing; not depend on field order, on array order where none is
documented, or on the text of error messages; follow cursors and links as given rather than
constructing them; and treat IDs as opaque strings of unbounded reasonable length.

**The server must** keep every existing field, type, meaning and default; keep accepting every
request that was valid before; and add only things an old client can ignore.

Put the client rules in the docs and bake them into any SDK shipped (open enums, permissive
decoding). Then exercise them: add a harmless new field early and often, so no client ever gets
to assume the response shape is closed. First-party clients should parse responses with schemas
that strip unknown keys, not strict ones; a strict response parser in the client turns every
additive server change into an outage.

Techniques that keep changes additive:

- **Changing a field's type or meaning**: add a new field with a new name, populate both, and
  deprecate the old. Never reuse the name.
- **Splitting or restructuring a resource**: add the new endpoint or representation; keep the
  old one as a view computed from the new model.
- **Making validation stricter**: apply it to new resources or new API versions only, or roll it
  out as a warning (a response header or dashboard notice) with a date before enforcing.
- **New required input**: give it a server-side default that reproduces the old behavior.
- **Scalar that should have been an object**: design for this up front by returning objects
  rather than bare scalars or arrays at the top level and for anything likely to gain attributes.

## Recognizing a breaking change

Review every API diff against this table before merging. The third column is where experienced
teams still get caught.

| Change | Breaking? | Notes |
|---|---|---|
| Add optional request field or query parameter | No | |
| Add response field | No, for tolerant readers | Breaks strict-schema clients; that is their contract violation only if the docs said so |
| Add endpoint, method or event type | No | Event type: only if subscriptions are explicit |
| Remove or rename a field, endpoint or parameter | Yes | A rename is a remove plus an add |
| Change a type (number to string, object to array, nullable to non-null in requests) | Yes | |
| Make a response field nullable or omit it sometimes | Yes | Clients dereference it |
| Add a required request field, or make an optional one required | Yes | |
| Tighten validation (shorter max length, new format rule) | Yes | Previously valid requests now fail |
| Loosen validation | Usually no | Unless clients relied on the server to reject |
| Add an enum value to a response | In practice often yes | Exhaustive switches and generated strict enums throw. Safe only if enums were documented as open |
| Remove an enum value accepted in requests | Yes | |
| Change a default (page size, sort order, default filter) | Yes | Silent behavior change is worse than an error |
| Change a status code or error `code` for an existing case | Yes | Clients branch on both |
| Change ID format or length | Often yes | Customers store IDs in fixed-width columns and validate them with regexes |
| Change the unit, precision or time zone of a value | Yes | Silent data corruption on the client |
| Lower a rate limit or quota, shorten a timeout | Yes, operationally | Treat as a deprecation with notice |
| Change pagination semantics or cursor validity | Yes | |
| Change when a webhook fires or its ordering relative to another | Yes | Consumers build state machines on it |
| Make a synchronous operation asynchronous | Yes | |
| Change required scopes or permissions for an endpoint | Yes | |
| Fix a bug that clients depend on | Treat as breaking | Check usage first |

Hyrum's law is the operating assumption: with enough consumers, every observable behavior is
depended on by someone, documented or not. Usage data decides how careful to be, not the docs.

## Versioning scheme and deprecation policy

Skip version machinery entirely until there are consumers outside the team's deploys. When the
API becomes public, choose once:

| Scheme | How it works | Choose when |
|---|---|---|
| Major version in the path (`/v1/...`) | One long-lived version evolved additively; `/v2` only for a redesign | Default. Visible in logs and docs, trivial to route, easy for integrators to understand |
| Date-based version pinned per account or key (header such as `Api-Version: 2026-06-01`) | Each breaking change gets a dated version; a consumer stays on the version it started with until it opts up; a request header can override for testing | Many integrators and a real need to make breaking changes regularly without a `/v2`. Requires the transformation layer below |
| Version in a media type or query parameter | | Avoid: harder to see, cache and debug, with no advantage over the two above |

A workable combination: put `/v1` in the path from the start, never plan a `/v2`, and add
date-pinned versions under it only when the first unavoidable breaking change arrives. Do not
version individual endpoints independently (`/v1/users`, `/v3/orders`); integrators cannot keep
the matrix in their heads. Versions do not apply to security fixes.

A published deprecation policy is what lets customers build on the API and lets the team remove
things. Write it before the first deprecation. It states:

- What counts as a breaking change (the table above, condensed) and what clients must tolerate.
- Stability labels: beta surfaces may change with short notice; generally available surfaces
  follow the policy. Mark beta in the path, header or docs so nobody ships on it unknowingly.
- The minimum notice before removal. Common practice is 6 to 12 months for a public API and
  longer for enterprise contracts; pick a number that can actually be honored.
- Where notice appears: changelog, email to the technical contact of affected accounts, response headers.
- The exception: security and legal issues may be fixed immediately.

Collect a technical contact email per API account at key creation; without it, there is no way
to give the notice the policy promises.

## Detect breaking changes in CI

With the OpenAPI document committed (`api-style.md`), diff it against the main branch on every
pull request and fail on breaking changes:

```bash
git show origin/main:openapi.yaml > /tmp/openapi.base.yaml
oasdiff breaking /tmp/openapi.base.yaml openapi.yaml --fail-on ERR
```

- First fail CI if regenerating the document from code changes the committed file; otherwise the
  diff compares stale artifacts.
- An intentional breaking change is merged through an explicit override (a label or an
  allowlist entry with a reason), so it is a decision in review rather than an accident.
- Run `oasdiff changelog` (or an equivalent) to draft the public changelog entry from the same diff.
- Protobuf: `buf breaking --against '.git#branch=main'`. GraphQL: a schema diff tool such as
  GraphQL Inspector, plus field-usage data before removals.
- For typed RPC with first-party clients only, the type checker across the monorepo is the
  check; the unprotected gap is clients built from an older commit, which the expand-and-contract
  sequence covers.

A structural diff cannot see behavioral changes: defaults, ordering, validation rules expressed
in code, timing, error cases, side effects. Cover the important ones with contract or snapshot
tests of real responses per version (`0x:code-quality`, `e2e-contract-visual.md`), and keep the
table above in the review checklist for anything touching handlers.

## Sunsetting an endpoint or field

Sequence, each step gated on the one before:

1. **Measure.** Log, for every request: route template, API version, key or account ID, and for
   field-level removals whether the deprecated parameter was sent. Without per-consumer usage,
   a sunset is a guess. Build the list of affected accounts and their volume.
2. **Provide the replacement first** and a migration guide with before-and-after requests.
3. **Announce**: changelog, docs banner on the old operation (`deprecated: true` in OpenAPI, which
   also marks SDK methods), and email to affected accounts naming their own usage and the date.
4. **Signal in-band** on every response from the deprecated surface:

```http
Deprecation: @1782864000
Sunset: Thu, 31 Dec 2026 23:59:59 GMT
Link: <https://docs.example.com/migrations/invoices-v2>; rel="deprecation"
```

   `Deprecation` (RFC 9745) carries the date the deprecation took effect as a Unix timestamp
   prefixed with `@`; `Sunset` (RFC 8594) carries the removal date as an HTTP date. Few clients
   read them automatically, so treat them as support for the emails, not a replacement.
5. **Chase the tail.** Usage follows a power law: most consumers migrate after the first notice,
   a few never read email. Contact the remaining large accounts personally. Re-send notices at
   decreasing intervals (90, 30, 7 days).
6. **Brownouts.** In the final weeks, fail the deprecated surface on purpose for short, announced
   windows (minutes, then hours), returning the final error. This reaches integrations whose
   owners ignore email, while the failure is still reversible.
7. **Remove**: return **410 Gone** with a problem body that links the migration guide, and keep
   that response for a long time rather than letting the route fall through to a generic 404.
   Delete the code only after the 410 has been quiet.

If meaningful revenue still depends on the old surface at the sunset date, extending the date is
normally cheaper than the churn. That is a business decision; present the usage list and ask.

## Two versions, one implementation

Never fork the handlers into `v1/` and `v2/` directories: every bug fix and feature then has to
be made twice, and the copies diverge within a month. Keep one implementation that speaks only
the latest shape, and translate at the edge.

```ts
type VersionChange = {
  version: string;                                   // the version that introduced the change
  description: string;
  upgradeRequest?: (route: string, body: unknown) => unknown;      // older request -> newer
  downgradeResponse?: (route: string, body: unknown) => unknown;   // newer response -> older
};

const changes: VersionChange[] = [/* ordered oldest to newest */];

export function toClientVersion(route: string, body: unknown, clientVersion: string) {
  return changes
    .filter((c) => c.version > clientVersion && c.downgradeResponse)
    .reverse()
    .reduce((b, c) => c.downgradeResponse!(route, b), body);
}
```

- Each breaking change is one small, named module holding its request upgrade and response
  downgrade. A request from an old client is upgraded step by step to the latest shape, handled
  once, and the response is downgraded step by step to the client's version. ISO-dated version
  strings compare correctly as plain strings.
- The list of changes doubles as the changelog and as documentation of exactly how versions differ.
- **Behavioral differences that a payload transform cannot express** (a different default,
  different side effects) are gated in the domain code on a named change flag derived from the
  client's version (`if (version.has("invoices_default_sort_desc"))`), never on a raw
  version comparison scattered through handlers.
- Resolve the client's version once per request: explicit header, else the version pinned on the
  key or account at creation, else the oldest supported. New accounts pin to the latest.
- Render webhook payloads through the same chain, using the endpoint's pinned version.
- Test with stored request and response fixtures per supported version, run against the single
  implementation in CI. A transform nobody tests breaks silently on the next refactor.
- Cap the cost: each live version lengthens the chain. Retire old versions through the sunset
  process, and let usage data, not tidiness, choose which.

For a `/v1` to `/v2` redesign, apply the same idea: implement `/v1` as an adapter over the `/v2`
domain model for the length of the deprecation window.

## Ask the user

- **Who calls this API today that the team does not deploy?** Decides whether a change is a
  refactor or a breaking change. Default: if unknown, check request logs by client before assuming nobody.
- **How much notice will be promised before removing something?** A commercial commitment that
  sales contracts may already contain. Default: 6 months for general availability, none for beta.
- **Is forcing mobile users to upgrade acceptable, and below which app version?** Default: keep
  supporting versions with meaningful active use; add the minimum-version check now so the option exists.
- **At the sunset date, what usage level is acceptable to cut off?** A revenue and relationship
  call. Default: no paying account cut off without personal contact first.
- **Is the upcoming change worth a pinned-version system?** It is permanent machinery.
  Default: no; find the additive route unless breaking changes will be regular.
