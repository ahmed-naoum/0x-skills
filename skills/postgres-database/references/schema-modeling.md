# Relational modeling

Read this when: designing or reviewing tables, keys, constraints and column types for a feature or
a new product, or deciding ORM versus raw SQL and UUID versus integer keys.

## Order of work

1. List entities and relationships with cardinality, and for each relationship decide what happens
   to the child when the parent is deleted.
2. Write every invariant as a sentence ("an account has at most one active subscription", "a paid
   invoice has a payment time") and turn each into a constraint. An invariant that lives only in
   application code will be violated by the second code path, a script or a race.
3. List the queries the feature runs (filter plus sort) and derive indexes from them
   (`indexes-query-plans.md`). Ship the result as a migration (`migrations.md`).

Keys, constraints, time and money types are the same at Prototype as at Scale, because changing
them later is a data migration. Audit history and trash windows can wait for Launch;
denormalization waits for a measured slow query.

## Baseline table

```sql
CREATE TABLE invoices (
  id            uuid PRIMARY KEY DEFAULT uuidv7(),   -- PostgreSQL 18+; otherwise generate in the app
  account_id    uuid NOT NULL REFERENCES accounts (id) ON DELETE RESTRICT,
  status        text NOT NULL DEFAULT 'draft'
                CONSTRAINT invoices_status_check CHECK (status IN ('draft', 'open', 'paid', 'void')),
  amount_minor  bigint NOT NULL CHECK (amount_minor >= 0),
  currency      text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
  paid_at       timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT invoices_paid_has_time CHECK ((status = 'paid') = (paid_at IS NOT NULL))
);
CREATE INDEX invoices_account_id_idx ON invoices (account_id);
```

- `NOT NULL` is the default; allow NULL only when "unknown" or "not applicable" is a real state.
  Every nullable column doubles the states the code must handle; a nullable boolean has three.
- Postgres indexes the referenced side of a foreign key (it must be unique) but not the referencing
  column. Index it yourself: joins need it, and without it every parent delete scans the child.
- Name the constraints that users can hit. The driver error carries `code` (`23505` unique, `23503`
  foreign key, `23514` check) and `constraint`; map the name to a field-level message instead of
  pre-checking with a SELECT, which races.
- `updated_at` does not maintain itself. Set it in one place (the ORM's on-update hook or one
  trigger function), not both.
- `snake_case` identifiers, never quoted mixed case. Follow the project's singular or plural habit.

| Child relationship | `ON DELETE` | Why |
|---|---|---|
| Part of the parent, meaningless alone (order items, memberships) | `CASCADE` | One delete removes the aggregate |
| Independent record that must survive or block (invoices, payments, audit rows) | `RESTRICT` | A stray parent delete fails instead of erasing money history |
| Optional pointer (assignee, last editor) | `SET NULL` | The row stays, the pointer clears |

A cascade from a large parent runs in one transaction and can delete millions of rows; for
tenant-sized deletes, delete children in batches first.

## Constraints that make invalid states impossible

| Rule | Mechanism |
|---|---|
| Value from a fixed set, numeric range, cross-column rule | `CHECK`, including multi-column checks such as the paid/paid_at pair above |
| Case-insensitive unique email | `CREATE UNIQUE INDEX ... ON accounts (lower(email))` and query with `lower(email) = lower($1)` |
| "At most one active/default/primary per parent" | Partial unique index: `CREATE UNIQUE INDEX ... ON subscriptions (account_id) WHERE status = 'active'` |
| Unique among non-deleted rows | Partial unique index `WHERE deleted_at IS NULL` |
| Unique where NULLs should collide | `UNIQUE NULLS NOT DISTINCT (a, b)` (15+); by default NULLs never conflict |
| No overlapping bookings, price periods, shifts | Exclusion constraint on a range |
| Exactly one of several columns set | `CHECK (num_nonnulls(a_id, b_id) = 1)` |

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE bookings (
  id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  room_id  bigint NOT NULL REFERENCES rooms (id),
  during   tstzrange NOT NULL,
  EXCLUDE USING gist (room_id WITH =, during WITH &&)
);
```

Use half-open ranges `[start, end)` so back-to-back bookings do not collide. From PostgreSQL 18
`PRIMARY KEY (room_id, during WITHOUT OVERLAPS)` states the same rule (it also needs `btree_gist`).
A check-then-insert in application code cannot replace this: two concurrent requests both pass
the check.

A CHECK cannot look at other rows or tables. Rules such as "sum of allocations is at most the
budget" need a lock on the parent row or a serializable transaction (`transactions-concurrency.md`).

## Column types

| Data | Use | Avoid, and why |
|---|---|---|
| A moment in time | `timestamptz` | `timestamp` drops the offset and silently reinterprets values when a session time zone differs |
| A future local event (appointment, recurring schedule) | Local `timestamp` plus an IANA zone column | A precomputed UTC instant goes wrong when zone rules change |
| A calendar day (birthday, billing date) | `date` | A midnight timestamp shifts across zones |
| Strings | `text`, with `CHECK (char_length(x) <= n)` when a limit is a business rule | `char(n)` pads; `varchar(n)` adds nothing over a named check |
| Identifiers and counters | `bigint` | `integer` runs out at 2.1 billion and widening it later is a multi-deploy migration |
| Exact decimals (quantities, rates, unit prices below a minor unit) | `numeric(p, s)` | `real`/`double precision` cannot represent 0.1 |
| Measurements where tiny error is fine | `double precision` | |
| UUIDs | `uuid` (16 bytes) | `text` is more than twice the size and compares slower |
| Fixed set of states | `text` plus `CHECK` | See below |
| Variable or opaque structure | `jsonb` | `json` keeps raw text and cannot be indexed usefully |
| Files and large blobs | Object storage key in a column | `bytea` bloats backups and the cache; see `0x:data-stores` |

Enumerations, three options. `text` plus a named `CHECK` is the default: changing the set is an
online constraint swap (`NOT VALID` then `VALIDATE`). A native `ENUM` is compact and what some ORMs
generate; adding a value is cheap but a value can never be removed or reordered without recreating
the type, so use it only for sets that are stable. A lookup table with a foreign key fits when the
values carry attributes (label, sort order) or are edited at runtime.

When a boolean will prompt the question "since when?", store a nullable timestamp instead
(`archived_at`, `verified_at`).

## Money

Store an integer count of the currency's minor unit in `bigint` next to an explicit ISO 4217
currency code, as in the baseline table. Reasons: integer arithmetic is exact, the payment provider
speaks the same format, and the amount is meaningless without its currency.

- The number of minor-unit digits is per currency (JPY 0, USD 2, KWD 3). Convert for display with
  a currency library or `Intl.NumberFormat`, never by dividing by 100.
- Never add amounts of different currencies; aggregate `GROUP BY currency`. Store a converted
  reporting amount as a separate column pair with the rate and its timestamp.
- Unit prices finer than a minor unit (per-token, per-request pricing) and tax or FX rates are
  `numeric`. Round once, at the invoice-line or invoice level, with a rule written down, and store
  the rounded result.
- Snapshot what was charged. Copy unit price, tax rate and totals onto the order or invoice line at
  purchase time; recomputing from today's catalog rewrites history.
- Do not use the `money` type (its formatting and parsing depend on a server locale setting) or
  floats. Ledger design belongs to `0x:payments-billing`.

## Primary keys

| Option | Choose when | Costs |
|---|---|---|
| UUIDv7 in a `uuid` column | Default for entities whose ids leave the database (URLs, APIs, clients, other systems) | 16 bytes; embeds creation time to the millisecond |
| `bigint GENERATED ALWAYS AS IDENTITY` | Internal, high-volume or join-heavy tables (events, line items, logs) | Enumerable and reveals volume if exposed; assigned only by the database |
| UUIDv4 | Only if the project already uses it | Random inserts scatter across the index: more page splits, WAL and cache misses on large tables |
| Natural key | Truly immutable external codes (ISO country or currency) | Emails, usernames, SKUs and slugs change: give them `UNIQUE`, not the primary key |

UUIDv7 is time-ordered, so inserts land at the right edge of the index like a sequence, and it can
be generated in the application before the insert (`uuidv7()` in SQL from PostgreSQL 18, a library
before that). No UUID version is a secret: authorization still applies, and tokens need a separate
random value. Use `IDENTITY` rather than `serial`, and `ALWAYS` so a stray explicit id cannot
desynchronize the sequence. Pick one scheme per project and keep it.

Join tables take a composite key in the lookup order, `PRIMARY KEY (team_id, user_id)`, plus an
index on the reverse `(user_id, team_id)`.

## ORM or raw SQL

| Situation | Choice |
|---|---|
| Greenfield TypeScript | A typed SQL-first layer (Drizzle): schema in code, queries shaped like SQL, migrations emitted as SQL files |
| Project already on Prisma or another ORM | Keep it; drop to its raw-SQL escape hatch where needed |
| Reports, window functions, recursive queries, bulk writes, locking clauses | Raw parameterized SQL, even inside an ORM project |
| No ORM wanted | A query builder (Kysely) or a driver with tagged templates, plus generated types |

Rules that hold for any of them:

- The migration files are SQL that gets read and reviewed; the ORM is a generator, not the author.
- Schema-sync commands (`drizzle-kit push`, `prisma db push`, `synchronize: true`) are for
  Prototype databases only. They diff and apply with no review and will drop a column to "fix" a
  rename.
- What the schema DSL cannot express (some ORMs lack CHECK, partial or expression indexes,
  exclusion constraints) goes into a hand-written SQL migration. Then confirm the next generated
  migration does not try to drop it.
- Types follow the database: infer or generate them from the schema and fail CI on drift
  (`0x:code-quality`).

## JSONB without losing integrity

Use it for attributes that vary per row (per-category product fields, user-defined custom fields),
provider payloads kept verbatim, and settings bags. Do not use it for anything filtered, joined,
summed or constrained on most requests; that is a column.

- Validate at the boundary with a schema (Zod) and store a `schema_version` key so old shapes can
  be migrated. Add `CHECK (jsonb_typeof(attrs) = 'object')`.
- Promote a hot key to a real column or a stored generated column, which can be indexed, checked
  and made NOT NULL: `sku text GENERATED ALWAYS AS (attrs ->> 'sku') STORED`. Write `STORED`:
  from PostgreSQL 18 the default is `VIRTUAL`, and that version cannot index a virtual column.
- Index by query shape: `USING gin (attrs jsonb_path_ops)` for containment (`attrs @> '{"color":"red"}'`),
  a B-tree expression index `((attrs ->> 'color'))` for equality or range on one key.
- No foreign keys reach inside JSON, and the planner keeps no statistics on keys, so filters on
  them are misestimated unless an expression index exists.
- Every update rewrites the whole value. Counters, append-only arrays and anything written often
  belong in columns or child rows.

## Soft delete, audit history and temporal data

| Need | Model |
|---|---|
| Nothing special | Hard delete. The default |
| User-facing trash or undo | `deleted_at timestamptz`, partial unique indexes `WHERE deleted_at IS NULL`, a purge job after the grace period |
| "Who changed what, when" | Append-only history table written in the same transaction |
| Values valid for a period (prices, plans, tax rates) | Rows with a validity range and a no-overlap exclusion constraint |
| What was true when it happened | Snapshot columns on the event row (see Money) |

Soft delete has a standing cost: every query must exclude deleted rows (one missed filter leaks
them), unique constraints must be partial, child rows stay behind, and where privacy law gives
people a right to deletion, that request still needs a real delete (`0x:privacy-compliance`;
`0x:data-stores` owns deletion across stores). Enforce the filter in one place, such as a view or
the data-access layer's base query.

History table: `(id, table_name, row_id, action, actor_id, at, old jsonb, new jsonb)`. Written by
application code it carries context but can be bypassed; written by a trigger it cannot be
bypassed but needs the actor passed in, with `SELECT set_config('app.user_id', $1, true)` inside
the transaction and `current_setting('app.user_id', true)` in the trigger. Revoke UPDATE and DELETE
on it from the application role (`backup-recovery.md`). Security audit logging requirements are in
`0x:web-security`.

## Hierarchies, many-to-many and polymorphic relations

- **Trees**: `parent_id` referencing the same table plus a recursive CTE (`sql-queries.md`) is the
  default and is fine for trees of thousands of nodes. Add `CHECK (parent_id <> id)` and reject
  cycles on write. Switch to the `ltree` extension or a closure table only when subtree reads
  dominate and are measurably slow. Skip nested sets: every insert renumbers the tree.
- **Many-to-many**: a join table with both foreign keys `ON DELETE CASCADE` and the composite key
  above. Facts about the relationship (role, joined_at, invited_by) live on the join row.
- **Polymorphic** ("a comment belongs to a post or a photo"):

| Pattern | Use |
|---|---|
| One nullable foreign key per target plus `CHECK (num_nonnulls(post_id, photo_id) = 1)` | Default for up to about five targets: real foreign keys, real cascades |
| One join table per target type | Many targets or different relationship attributes |
| `target_type` plus `target_id` with no foreign key | Only for append-only logs and feeds where orphans are acceptable |

- **Subtypes**: one table with nullable subtype columns and a CHECK per type while the subtypes
  differ by a few columns; a table per subtype sharing the parent's primary key when they diverge.
  Do not use Postgres table inheritance for this.

## Denormalizing

Normalize first: one fact in one place. Denormalize only with a measured slow query in hand, and
try these in order: an index or covering index; a generated column; a summary column updated in
the same transaction as its source; a materialized view (`REFRESH MATERIALIZED VIEW CONCURRENTLY`
needs a unique index and recomputes everything); a table rebuilt asynchronously by a job.

Every copy needs three things written down: the single code path (or trigger) that writes it, a
reconciliation query that finds drift (`WHERE stored_count <> (SELECT count(*) ...)`), and a
rebuild script. A counter on a popular parent row turns every child insert into a lock on that
row; when that contends, aggregate periodically instead of per write.

## Ask the user

- **Will amounts ever be in more than one currency?** It decides whether currency is a column on
  every money row. Assume yes: the column costs nothing and retrofitting is painful.
- **When a user deletes something, must it be recoverable, and for how long?** Decides hard delete
  versus a trash window. Default: hard delete for minor records, a 30-day trash for
  customer-created top-level objects (projects, workspaces).
- **Do you need a record of who changed what?** For which entities, and is it for support, for
  customers or for an auditor? Default: history on money, permissions and account settings only.
- **Are ids shown to customers or competitors (URLs, invoices, API)?** Sequential ids reveal volume
  and invite enumeration. Default: UUIDv7 for anything exposed.
- **Do events happen in the user's local time (bookings, schedules, reminders)?** Then the zone
  must be stored. Default: store the IANA zone on the user or the event.
