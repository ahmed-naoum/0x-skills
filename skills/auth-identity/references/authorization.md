# Authorization models

Read this when: deciding who may do what: a user can reach another user's data by changing an
ID, the product needs organizations, invitations and roles, a choice between role, attribute and
relationship models is due, sharing links are being built, or it is unclear where checks belong.

## Object-level checks (IDOR)

Authentication says who is calling. It says nothing about whether row 4812 is theirs. Every
handler that receives an identifier from a client resolves it through the caller's scope.

```ts
// wrong: any signed-in user reads any invoice
const [invoice] = await db.select().from(invoices).where(eq(invoices.id, id));

// right: the tenant boundary is in the query, and the action check is explicit
const [invoice] = await db
  .select()
  .from(invoices)
  .where(and(eq(invoices.id, id), eq(invoices.orgId, actor.orgId)));
if (!invoice) throw new NotFoundError();
authorize(actor, "invoice:read", invoice);
```

- `actor.orgId` comes from the session plus a membership lookup made on this request. An
  organization ID in the path, a header or the body is a request for a context, not proof.
- Outside the caller's tenant answer 404, not 403, so the object's existence is not confirmed.
  Inside the tenant without permission answer 403.
- Random IDs reduce guessing and fix nothing. IDs leak through logs, referrers, exports, shared
  links and screenshots.

Where the flaw hides after the obvious read endpoint is fixed:

| Place | The miss |
|---|---|
| Update and delete | The read was checked; the mutation takes the same ID unchecked |
| Nested routes | `/orgs/A/projects/123`: membership in A is checked, but project 123 belongs to B |
| References in the body | `projectId`, `assigneeId` or `parentId` on create or move point into another tenant |
| Mass assignment | A body spread into the update sets `orgId`, `ownerId` or `role`; validate with an allowlist schema |
| Bulk endpoints | An array of IDs checked for the first element only, or not at all |
| Files and exports | Guessable or long-lived storage and export URLs; mint short-lived signed URLs after the check (`0x:data-stores`) |
| Search, autocomplete, counts | Aggregate and index queries without the tenant filter |
| Secondary lookups | "Get by slug", "get by email", a GraphQL node fetched by global ID |
| Response bodies | Whole rows serialized, including fields this role may not see; map to an explicit output shape |
| Admin functions | An endpoint hidden in the UI but callable by any member |

Structural fix: data-access functions take the actor as a required argument and add the tenant
filter themselves, so an unscoped query cannot be written by accident. Row-level security as a
second layer, and tenant isolation design in general: `0x:backend-architecture`.

## Enforce at every entry point

Put the check next to the data access so that every way in inherits it. Then verify each entry
point, because each fails differently.

| Entry point | How it fails | Rule |
|---|---|---|
| Next.js middleware (named proxy in recent versions) | Treated as the gate; matcher gaps and past bypass bugs skip it | Coarse redirects only, never the sole check |
| Layouts and pages | A layout's check does not rerun on client navigation between its child pages | Authorize in the data layer each page calls |
| Server Functions (Server Actions) | Each is a public POST endpoint, callable with any arguments whether or not the UI renders its button | Authenticate, validate input and authorize inside every one |
| Route handlers, APIs, GraphQL resolvers | A check at the root only; nested resolvers and sub-resources unchecked | The same policy function at the data layer |
| Background and scheduled jobs | Payload trusted blindly; permission revoked between enqueue and run | The payload carries actor and organization IDs; work on a user's behalf re-checks permission at run time; system jobs run as an explicit, narrow system actor |
| Inbound webhooks | Tenant taken from a field the sender controls | Verify the signature, then map to a tenant through an identifier stored at connection time |
| Realtime channels | Subscribe is authorized once and the connection outlives the permission; broadcasts carry fields some subscribers may not see | Authorize at subscribe on the server; disconnect or re-check on membership change; check `Origin` on the WebSocket upgrade; send IDs and let clients refetch where visibility differs |
| Caches | A per-user response stored under a shared key | Keys include the tenant and, where output differs, the user or role |
| Search and LLM retrieval | The index query is not filtered by tenant and access list | Filter at query time with the actor's scope (`0x:ai-features`) |
| Emails and notifications | Sent to someone who has since lost access | Re-check recipients at send time |
| Support and impersonation tools | Bypass paths that leave no trace | A separate guard, a required reason and an audit entry |

## Organizations, invitations and roles

```sql
create table memberships (
  org_id uuid not null references organizations(id),
  user_id uuid not null references users(id),
  role text not null,                      -- owner | admin | member
  status text not null default 'active',   -- active | suspended
  primary key (org_id, user_id)
);
create table invitations (
  id uuid primary key,
  org_id uuid not null references organizations(id),
  email citext not null,
  role text not null,
  token_hash bytea not null unique,
  invited_by uuid not null references users(id),
  expires_at timestamptz not null,
  accepted_at timestamptz,
  revoked_at timestamptz
);
```

- Users are global and the role lives on the membership. Every tenant-owned table carries
  `org_id`.
- Give every user a personal organization instead of supporting both user-owned and
  organization-owned resources. One ownership model halves the authorization code and makes
  "upgrade to a team" a rename.
- Put the active organization in the URL (`/o/<slug>/...`), not in the session. Several tabs
  work, links are shareable, and the server verifies membership for the organization named in
  each request.
- Read membership and role from the database on each request, cached for a minute at most. A
  role baked into a long-lived token keeps working after removal.
- Starter roles: owner, admin, member. Owner-only: billing, deleting the organization,
  transferring ownership, SSO settings. Invariants enforced in the transaction that makes the
  change: there is always at least one owner, nobody grants a role above their own, and admins
  cannot change owners.
- Removing a member takes effect on their next request, revokes their organization-scoped
  tokens, closes their realtime connections and leaves their work with the organization.

Invitations:

- The token is 32 random bytes, stored hashed, single-use, valid 7 days and revocable. Resending
  rotates it.
- The invitation is bound to the invited address. Accepting requires being signed in as that
  verified address or signing up with it. A click on the emailed link, confirmed by a POST, may
  count as verifying that address. A forwarded or leaked link must not admit a different person;
  if "accept with another account" is wanted, the inviter or an admin confirms the new address.
- The invited role is capped at the inviter's own. Seat limits are checked at invite and again
  at accept (seat billing: `0x:payments-billing`).
- The inviter sees the same result whether or not the address already has an account.
- Joining automatically by email domain needs a verified domain (`enterprise-sso.md`).
  Invitation spam: `abuse-defense.md`.

## One policy layer

Handlers call one function and never compare role names inline. Scattered `role === "admin"`
checks cannot be audited, tested or changed when a role is added.

```ts
const grants = {
  owner: ["project:read", "project:write", "member:manage", "billing:manage", "org:delete"],
  admin: ["project:read", "project:write", "member:manage"],
  member: ["project:read", "project:write"],
} as const satisfies Record<string, readonly string[]>;

type Role = keyof typeof grants;
type Permission = (typeof grants)[Role][number];

export function can(actor: { role: Role }, permission: Permission): boolean {
  const allowed: readonly Permission[] = grants[actor.role];
  return allowed.includes(permission);
}
```

- Conditions that depend on the resource (ownership, status, amount) live in the same module as
  functions that take the resource, for example `canEditDocument(actor, doc)`.
- Two layers, both mandatory: the tenant scope in every query, then the permission check for the
  action.
- Deny by default. An unknown permission or role is a denial. A test enumerates every route
  handler and server function and fails when one neither calls the guard nor appears on an
  explicit public allowlist.
- The UI imports the same grants to hide controls. That is presentation; the server call is the
  control.
- Tests: a table-driven matrix of role by permission generated from `grants`, and a cross-tenant
  suite that creates two organizations and asserts, for every endpoint taking an ID, that a
  member of A gets 404 on B's objects. Every authorization bug found gets a regression test.
- Log denials with actor, permission and resource. A burst of them is an attack signal
  (`0x:web-security`).

## Choosing a model

| Model | Decides on | Fits | Breaks down when |
|---|---|---|---|
| RBAC | The caller's role in the organization | Most SaaS: "what kind of member is this" | Access differs per resource (this project, not that one) |
| ABAC | Attributes of caller, resource and context: owner, status, amount, time | Conditional rules: "members edit their own drafts", "approvals above a limit need an admin" | Rules multiply until nobody can say who sees a given object |
| ReBAC | Relationships: member of a team that owns a folder that contains the document | Products where sharing and hierarchy are the product (documents, files, design tools) | Flat role checks do not need it; listing queries get expensive |

Default: RBAC per organization, a few attribute conditions written as code in the policy module,
and a grants table for per-resource sharing. That combination carries most products to Scale.
Whether an organization's subscription includes a feature is a separate question from whether
this member may use it. Check both and keep them in separate modules (`0x:payments-billing`).

## Roles customers can administer

- Code checks permissions (`resource:action`) and roles are named bundles of them, so custom
  roles later are a data change and not a rewrite.
- Ship three or four fixed roles named for jobs, with a visible matrix of what each can do. The
  additions customers request first, in the usual order: a read-only viewer, a billing-only role,
  an external guest limited to specific resources.
- Custom roles wait until enterprise customers ask (Scale). Then: per-organization role rows
  holding a permission set, immutable system roles, an editor who can grant only permissions
  they hold, and "manage roles" as a guarded permission of its own.
- Avoid deny rules, per-user permission overrides and roles that mirror UI screens. Each makes
  "why can this person do that" unanswerable.
- New members receive the least privileged role.
- Admins get an audit log of membership and role changes and a way to see what a given member
  can access. Enterprise buyers ask for both.

## Sharing by link and invitation

```sql
create table grants (
  id uuid primary key,
  org_id uuid not null,
  resource_type text not null,
  resource_id uuid not null,
  grantee_type text not null,        -- user | email | link
  grantee_id text,                   -- user id or email; null for a link
  token_hash bytea unique,           -- link grants only
  permission text not null,          -- view | comment | edit
  created_by uuid not null,
  expires_at timestamptz,
  revoked_at timestamptz
);
```

- A link token carries 128 bits or more of randomness and is unrelated to the resource ID. The
  default permission is view. The default expiry is set (7 to 30 days), with "never" as an
  explicit choice.
- Revocable means checked on every access: rotating or revoking the link kills the old URL at
  once. Files behind the link are served through signed URLs minted after the grant check and
  valid for minutes.
- The token is a credential inside a URL. Send `Referrer-Policy: no-referrer` and
  `X-Robots-Tag: noindex` on shared pages, load no third-party script that records URLs, and
  scrub the token from logs and analytics.
- A visitor arriving through a link is never promoted to a member. Edits made through a link are
  attributed to "anyone with the link".
- Sharing with an email address creates a pending grant bound to that address, claimed after a
  verified sign-in with it.
- Re-sharing is its own permission and is off for recipients by default.
- Organization admins can list and revoke every public link and can restrict sharing to members
  or to the verified domain. Enterprises ask for that switch.
- Links created by a member who leaves remain the organization's and stay listed for admins.
- Public pages on the product's domain attract phishing and spam: `abuse-defense.md`.

## Policy engines and Zanzibar-style services

Signals that checks have outgrown code:

1. Several services in different languages must reach the same decision.
2. Deep hierarchies and sharing make "list everything this user can see" slow or wrong in SQL.
3. Customers need custom policies as data, or auditors want policy reviewable outside the code.

| Kind | Examples | Answers | Addresses |
|---|---|---|---|
| Policy engine | OPA, Cedar, Cerbos, Oso | "Given these attributes and this policy, allow or deny" | Signals 1 and 3 |
| Relationship store | SpiceDB, OpenFGA and hosted equivalents | "Does this user have this relation to this object", plus reverse lookups | Signal 2 |

Costs to weigh before adopting one:

- **Dual writes.** Relationships live in the authorization store and in Postgres, and every
  drift between them is an authorization bug. Use a transactional outbox and reconcile.
- **Staleness.** A check served from an old snapshot honors a permission that was just revoked.
  Use the store's consistency tokens on writes that remove access.
- **Availability and latency.** Every request depends on one more service. Fail closed and budget
  the extra hop.
- **Listing.** Filtering ten thousand rows by permission needs the store's lookup API with
  pagination or a pre-filter in SQL. Evaluate this query first.
- **Development and tests** need the service running with fixture data.

A grants table with a recursive CTE for folder inheritance, or a materialized table of effective
access, handles more depth than expected and should be tried first. Keep handlers calling `can()`
so the backend behind it can change. Tenant isolation stays in the queries either way; an engine
does not replace it.

## Ask the user

- **Do customers work alone or in teams, and can one person belong to several organizations?**
  It fixes the ownership model, which is expensive to change. Default: organizations from the
  start, a personal one per user, multiple memberships allowed.
- **Which roles are needed at launch?** Each role is a column in the test matrix and a support
  topic. Default: owner, admin, member.
- **Is sharing outside the organization a feature?** Public links are a data-leak and abuse
  surface. Default: off, or view-only links that expire.
- **Which actions belong to owners only?** Default: billing, deleting the organization,
  ownership transfer, SSO settings and full data export.
- **Has any prospect asked for custom roles or an audit log?** Default: fixed roles and an
  internal audit trail now; customer-facing audit log and custom roles when a deal needs them.
