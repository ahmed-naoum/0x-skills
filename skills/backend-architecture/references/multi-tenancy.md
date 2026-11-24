# Multi-tenancy

Read this when: one deployment serves many customer organizations and their data and load must be
kept apart, or a tenant needs its own settings, its own domain, its data in a chosen region, or
its own infrastructure.

## Isolation model

| Model | Choose when | Cost |
|---|---|---|
| Shared tables with a tenant column (pooled) | Default for every stage | Isolation depends on every query being scoped: enforce it with a scoped data layer plus row-level security |
| Schema per tenant | Almost never | Every migration runs once per tenant, the catalog bloats, pooling by `search_path` is fragile; painful from hundreds of tenants (rule of thumb) |
| Database per tenant | A contract or regulator demands physical separation, per-tenant restore or per-tenant keys, and the price covers it; tens to low hundreds of tenants | Per-tenant provisioning, migrations, monitoring, backups and connection pools |
| Pooled by default, dedicated for a few | Scale, with a handful of enterprise customers | A routing layer from tenant to database, and the migration procedure at the end of this file |

Start pooled. Two cheap choices keep the other models reachable: a tenant ID on every
tenant-owned row, and one function that hands out the database handle for a tenant
(`db_for(org_id)`), even while it always returns the same pool.

## Accounts, organizations and users

```text
users(id, email UNIQUE, ...)                        a person, global
organizations(id, slug UNIQUE, plan, region, ...)   the tenant; billing attaches here
memberships(org_id, user_id, role, UNIQUE (org_id, user_id))
invitations(org_id, email, role, token_hash, expires_at, accepted_at)
```

- A user belongs to many organizations through memberships. A `users.org_id` column is the
  mistake that later forces duplicate accounts for consultants and agency staff.
- Subscription, plan, usage and invoices belong to the organization, never to the user.
- Create a personal organization at signup even for a single-player product. Adding teams later
  becomes an invitation feature instead of a data migration.
- The active tenant comes from the URL (`/o/{slug}/...` or a subdomain), not from a "current
  organization" stored only in the session: two tabs on two organizations must both work.
- Resolve per request: URL to organization, then verify the membership, then build the tenant
  context. Never take a tenant ID from a request body or a client-set header.
- Every tenant-owned table carries `org_id NOT NULL`, including child tables. Composite foreign
  keys (`FOREIGN KEY (org_id, project_id) REFERENCES projects (org_id, id)`) make a row that
  points across tenants impossible; the parent table needs `UNIQUE (org_id, id)` for it.
- Uniqueness becomes per tenant (`UNIQUE (org_id, slug)`), and indexes lead with `org_id`.

Roles and permission checks are in `0x:auth-identity` (`authorization.md`); tenant-specific
identities and SSO in `enterprise-sso.md`.

## Scope everything, not only queries

| Surface | Rule |
|---|---|
| Queries | Data-layer functions take a tenant handle that only a verified membership can create (below), so an unscoped call does not compile; raw pool access is reserved for a named, reviewed set of admin and migration code |
| Cache keys | Prefix with the tenant: `t:{org_id}:projects:list`. A shared key is a cross-tenant leak served fast |
| Jobs | `org_id` in the arguments; the handler rebuilds the tenant context (and the RLS setting) before touching data |
| Object storage | Server-generated keys under `tenants/{org_id}/...`; authorize before signing a URL; never build a key from a client-supplied path |
| Search and vector indexes | Tenant filter applied on the server on every query; never a filter the client can drop |
| Realtime channels | Channel names include the tenant; authorize each subscription on the server |
| Logs, traces, error reports | Attach `org_id` so one tenant's incident can be isolated, and so support does not read other tenants' data to debug |
| Rate limits and quotas | Keyed by tenant as well as by user and IP |
| Exports, reports, emails, webhooks out | Built from the scoped data layer, not from ad hoc SQL |
| LLM context | Retrieval filtered by tenant before ranking; no cross-tenant examples in prompts or caches |

Unguessable IDs are not isolation. Staff access goes through explicit, time-limited, audited
impersonation, never through a flag that turns scoping off (`0x:web-security`,
`accounts-admin-hardening.md`).

## Row-level security

RLS makes the database refuse cross-tenant rows even when application code forgets the filter.
Treat it as the net under the scoped data layer, not a replacement. Skip at Prototype; adopt at
Launch for B2B or any sensitive data.

```sql
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
  USING      (org_id = nullif(current_setting('app.org_id', true), '')::uuid)
  WITH CHECK (org_id = nullif(current_setting('app.org_id', true), '')::uuid);
```

The tenant handle carries the setting, so code holding one cannot forget it:

```rust
use sqlx::{PgConnection, PgPool, Postgres, Transaction};
use uuid::Uuid;

/// Only `verify_membership` builds this, so holding one proves the check ran.
pub struct Membership { org_id: Uuid, user_id: Uuid }

pub async fn verify_membership(pool: &PgPool, org_id: Uuid, user_id: Uuid) -> sqlx::Result<Option<Membership>> {
    let found: Option<Uuid> =
        sqlx::query_scalar("SELECT org_id FROM memberships WHERE org_id = $1 AND user_id = $2")
            .bind(org_id)
            .bind(user_id)
            .fetch_optional(pool)
            .await?;
    Ok(found.map(|org_id| Membership { org_id, user_id }))
}

/// A transaction with the RLS setting applied; tenant data functions take this, never a pool.
pub struct TenantTx { tx: Transaction<'static, Postgres>, org_id: Uuid }

impl TenantTx {
    pub async fn begin(pool: &PgPool, m: &Membership) -> sqlx::Result<Self> {
        let mut tx = pool.begin().await?;
        sqlx::query("SELECT set_config('app.org_id', $1, true)") // true: this transaction only
            .bind(m.org_id.to_string())
            .execute(&mut *tx)
            .await?;
        Ok(Self { tx, org_id: m.org_id })
    }
    pub fn org_id(&self) -> Uuid { self.org_id }
    pub fn conn(&mut self) -> &mut PgConnection { &mut self.tx }
    pub async fn commit(self) -> sqlx::Result<()> { self.tx.commit().await }
}
```

| Trap | Consequence | Fix |
|---|---|---|
| The application connects as the table owner or a superuser | Policies are skipped silently | A dedicated application role that owns nothing and lacks `BYPASSRLS`; `FORCE` covers the owner, nothing covers a superuser |
| Session-level `SET` behind a transaction-mode pooler | The setting leaks to the next client on that connection | Only `set_config(..., true)` or `SET LOCAL`, inside a transaction |
| Setting never set | With the policy above the comparison is NULL: zero rows | This is the intended fail-closed behavior; test it |
| Views | A view runs with its owner's rights and bypasses the caller's policies | `WITH (security_invoker = true)` on PostgreSQL 15 or later |
| Unique and foreign-key checks | They see all rows, so an error can reveal that a value exists in another tenant | Per-tenant unique constraints and composite foreign keys |
| No index starting with `org_id` | Every query scans all tenants' rows before filtering | Lead composite indexes with `org_id` |
| Migrations and back-office jobs | Blocked by policies, or bypassing them by accident | A separate role with `BYPASSRLS`, used deliberately and only there |

## Tests that prove isolation

Seed two organizations, A and B, with the same shape of data, and for every resource:

- As a member of A, fetch B's object by ID: expect 404 (a 403 confirms the object exists).
- As A, update and delete B's object: expect failure, then assert B's row is unchanged.
- As A, create or update with `org_id` of B in the body: the field is ignored or rejected.
- As A, list and search: no B rows, including through filters, sorting and pagination cursors.
- As A, request B's file URL, export, realtime channel and job result.

Make it systematic: one test walks the route table and calls every route that takes an ID with a
foreign tenant's ID, so a new endpoint is covered the day it is added. For RLS, connect as the
application role without setting the tenant and assert zero rows, and fail CI when this query
returns any tenant table where row-level security is not both enabled and forced:

```sql
SELECT c.relname
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'org_id' AND NOT a.attisdropped
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
  AND NOT (c.relrowsecurity AND c.relforcerowsecurity);
```

Tests must run as the application role, not as the migration owner, or every RLS test passes
while proving nothing. `#[sqlx::test]` connects with the credentials in `DATABASE_URL`, usually a
role that can create databases and owns the tables: begin each isolation test with `SET ROLE` to
the application role.

## Per-tenant settings and overrides

Resolve in layers: code defaults, then plan, then organization override, then user preference.
One typed struct (serde with `#[serde(default)]`, checked with garde) defines every setting with
its default; overrides are stored sparsely
(a JSONB column or an `org_settings` table) and read through one resolver.

- Code asks for capabilities and limits (`limits.sso`, `limits.seats`), never
  `plan == Plan::Pro`. Plans change and enterprise deals need exceptions; only the mapping should
  move (`0x:payments-billing`, `subscriptions.md`).
- `if org.id == ACME_ID` in code is a fork with one customer. Turn it into a named setting that
  any organization could have.
- Customer-defined fields go in a JSONB column validated against per-tenant field definitions,
  not in per-tenant columns or tables.
- Ladder for customization requests: setting, then feature flag, then webhook or API
  extensibility. A branch or separate deployment per customer is off the ladder.
- Cache resolved settings briefly and invalidate on change; they are read on every request.

## Noisy tenants

One tenant can exhaust request capacity, the job queue, database time, connection slots or a
shared third-party quota. Skip most of this until Launch; add fairness as soon as one customer is
visibly larger than the rest.

- **Requests**: token bucket per tenant in addition to per user and per IP, shared across
  instances (an in-process limiter such as tower_governor counts per instance).
- **Jobs**: FIFO lets one tenant's 500,000-row import delay every other tenant's email. Cap
  concurrency per tenant (with a jobs table, rank ready jobs per tenant in a subquery and claim
  the first few of each), or dispatch at most N
  jobs per tenant per tick, and keep bulk work on its own queue with its own workers.
- **Database**: `statement_timeout` on the application role, pagination limits, and bulk
  endpoints that enqueue instead of running inline.
- **Hard quotas**: rows, storage, seats, API calls per plan, checked at write time and answered
  with a clear error that names the limit and the upgrade path.
- **Visibility**: a top-tenants view by requests, job seconds and database time. Do not add a
  metric label per tenant at Scale; record top-K or put the tenant on logs and traces instead.

## Customer custom domains

1. The customer enters a hostname. Normalize it (lowercase, punycode) and store it with status
   `pending`, unique across all tenants.
2. Show two DNS records: a `CNAME` from their hostname to a stable target you control
   (`customers.example-app.com`), and a `TXT` record with a per-tenant verification token.
   An apex domain cannot be a CNAME: it needs the provider's ALIAS or flattening feature, or
   static IP addresses that then can never change.
3. Verify the TXT record before activating. A CNAME alone proves nothing: a hostname already
   pointing at the platform could be claimed by any tenant, and a dangling CNAME left after a
   customer leaves is a takeover waiting for the next claimant.
4. Issue the certificate on demand at the first TLS handshake, or through the platform's
   custom-hostname feature (CDN "for SaaS" products and PaaS domain APIs do this). With on-demand
   issuance the proxy must ask the application whether the hostname is known and verified;
   without that check anyone can point domains at the server and burn certificate rate limits.
5. Route by `Host` header through a cached hostname-to-tenant lookup. Unknown hosts get a 404.
6. Re-check DNS periodically; deactivate hostnames that no longer point at the platform.

```text
{
  on_demand_tls {
    ask http://localhost:3000/internal/domain-check
  }
}

https:// {
  tls {
    on_demand
  }
  reverse_proxy localhost:3000
}
```

The `ask` endpoint receives `?domain=<hostname>` and allows issuance only by answering 200.

Traps: session cookies do not cross to a custom domain, and OAuth redirect URIs cannot be
registered per customer, so authenticate on the main domain and hand off with a one-time code.
A `CAA` record at the customer can forbid the issuing CA; say so in the setup instructions.
Tenant subdomains are same-site with the main domain and receive any cookie scoped to it, so
tenant-authored pages or scripts call for a separate registrable domain. Keep a reserved list
(`www`, `api`, `admin`, `mail`, `app`, `status`). DNS and certificates: `0x:web-networking`.

## Home region per tenant

Do this when a signed customer or regulator requires data to stay in a region, not before. It
multiplies infrastructure and operations by the number of regions.

- Each region is a complete, independent stack: application, database, queue, object storage,
  cache and secrets. No cross-region queries or joins.
- `organizations.region` is set at creation and treated as immutable; moving it is the migration
  below.
- A small global control plane holds only the directory needed for routing: hostname or slug to
  region, and login identifier to organizations. That directory is itself personal data; keep it
  minimal and confirm it is acceptable.
- Routing: a region in the hostname (`eu.example-app.com`) is the simplest and most transparent.
  A global router that looks up the tenant and proxies is smoother for users and adds a hop and
  a shared failure point.
- The same build deploys to every region; migrations run per region; a region can be down alone.
- Residency covers vendors too: email, logs, error tracker, analytics, LLM provider and backups
  must be region-pinned or excluded for those tenants. What the law requires is in
  `0x:privacy-compliance`.

Cheap preparation now: the `region` column, tenant-prefixed storage keys, `db_for(org_id)`, and no
code that assumes a globally unique sequence.

## Moving a tenant to dedicated infrastructure

Prerequisites: `org_id` on every table, routing through `db_for(org_id)`, IDs that do not collide
across databases (UUIDs).

1. Provision the target at the same schema version and freeze schema migrations for the move.
2. Copy while live: logical replication with a row filter on the tenant (PostgreSQL 15 or
   later; for updates and deletes the filter column must be part of the replica identity, so
   check before relying on it), or a table-by-table backfill in foreign-key order plus change
   capture. Copy the object-storage prefix in parallel.
3. Verify: row counts and per-table checksums, then a read-only smoke test against the target.
4. Cut over: drain that tenant's jobs, set the tenant read-only, wait for replication to catch
   up, flip the routing entry, clear its caches, lift read-only.
5. Keep the source rows read-only for a rollback window, then delete them and rebuild that
   tenant's search index and derived data.

"No downtime" here means a write pause of seconds to a few minutes for that one tenant. Say so
to the customer and schedule it. Rehearse on a copy of the tenant first; the rehearsal gives the
real duration.

## Ask the user

- **Is the customer a company with several users, or an individual?** It decides whether
  organizations are visible in the product. Assume organizations exist in the data model either
  way, with a hidden personal one for individuals.
- **Has any customer or regulator asked for physical data separation or a specific region?**
  Only a concrete requirement justifies dedicated databases or regional stacks. Assume pooled, in
  one region.
- **What do plans limit: seats, projects, storage, API calls?** Quotas and fairness are built
  around these. Assume seats and one usage dimension.
- **Should customers be able to use their own domain, and on which plan?** It adds DNS
  verification, certificate issuance and support load. Assume not until a customer asks.
- **May staff see customer data for support, and must customers be told?** It defines
  impersonation, audit logging and contract terms. Assume audited impersonation with a visible
  banner and a log entry the customer can request.
