# Writing application SQL

Read this when: writing or reviewing the queries an application runs (joins, aggregates, upserts,
pagination, ORM output), or changing production data by hand or with a one-off fix script.

## Traps that produce wrong results

| Symptom | Cause | Fix |
|---|---|---|
| Sums and counts too high | Two one-to-many joins multiply each other before `GROUP BY` | Aggregate each child in its own subquery, then join the totals |
| `LEFT JOIN` drops parents without children | A `WHERE` condition on the right table removes the NULL rows | Move the condition into `ON` |
| `NOT IN (subquery)` returns nothing | One NULL in the subquery makes every comparison unknown | `NOT EXISTS (...)` |
| Rows at the period boundary counted twice or lost | `BETWEEN` is inclusive on both ends | Half-open: `ts >= $start AND ts < $end` |
| Daily totals off by hours | `date_trunc('day', ts)` uses the session zone | `date_trunc('day', ts, 'America/New_York')` with the business zone |
| A changed column still equals the old one in a diff | `a <> b` is unknown when either is NULL | `a IS DISTINCT FROM b` |
| Page two repeats or skips rows | `ORDER BY` on a non-unique column | Add the primary key as the last sort column |
| Deploy breaks after a column is added or dropped | `SELECT *` in application code | Name the columns |

```sql
SELECT o.id, i.items_minor, p.paid_minor
FROM orders o
LEFT JOIN (SELECT order_id, sum(amount_minor) AS items_minor FROM order_items GROUP BY order_id) i
       ON i.order_id = o.id
LEFT JOIN (SELECT order_id, sum(amount_minor) AS paid_minor  FROM payments    GROUP BY order_id) p
       ON p.order_id = o.id
WHERE o.id = $1;
```

## Shapes worth knowing by hand

```sql
-- Several conditional aggregates in one pass
SELECT tenant_id,
       count(*)                                         AS orders,
       count(*) FILTER (WHERE status = 'paid')          AS paid_orders,
       sum(total_minor) FILTER (WHERE status = 'paid')  AS paid_minor
FROM orders
WHERE created_at >= $1 AND created_at < $2
GROUP BY tenant_id;

-- Latest row per group
SELECT DISTINCT ON (customer_id) customer_id, id, created_at
FROM orders
WHERE tenant_id = $1
ORDER BY customer_id, created_at DESC, id DESC;

-- Top N per group, ranks, running totals
SELECT *
FROM (
  SELECT id, customer_id, total_minor,
         row_number() OVER (PARTITION BY customer_id ORDER BY total_minor DESC, id) AS rn
  FROM orders
  WHERE tenant_id = $1
) ranked
WHERE rn <= 3;
```

- Window functions run after `WHERE` and `GROUP BY`, so filter on their result in an outer query.
- With `ORDER BY` in a window, the default frame ends at the current row and includes its peers:
  `last_value()` and running sums over ties surprise. State the frame:
  `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
- A CTE referenced once is inlined into the main query. Write `AS MATERIALIZED` only to force
  separate evaluation, which is occasionally a useful fix for a bad plan.
- `count(*)` on a large table scans it. For "about how many" use `reltuples` from `pg_class` or cap
  the count (`SELECT count(*) FROM (SELECT 1 FROM t WHERE ... LIMIT 10001) s`).

## RETURNING, LATERAL and recursive CTEs

`RETURNING` removes the read-after-write round trip and the race inside it: get generated ids and
defaults from `INSERT`, the new state from `UPDATE`, the removed rows from `DELETE`. PostgreSQL 18
adds `RETURNING old.col, new.col`. A data-modifying CTE moves rows atomically:

```sql
WITH moved AS (
  DELETE FROM orders WHERE status = 'void' AND created_at < $1 RETURNING *
)
INSERT INTO orders_archive SELECT * FROM moved;
```

All parts of such a statement see the same snapshot; later parts see earlier changes only through
`RETURNING`.

`LATERAL` runs a subquery per outer row and may use `ORDER BY ... LIMIT` inside it. With an index
on `(customer_id, created_at DESC)` it does one short index scan per parent, which beats ranking
every child row when parents are few and children many:

```sql
SELECT c.id, c.name, r.id AS order_id, r.created_at
FROM customers c
LEFT JOIN LATERAL (
  SELECT o.id, o.created_at
  FROM orders o
  WHERE o.customer_id = c.id
  ORDER BY o.created_at DESC
  LIMIT 3
) r ON true
WHERE c.tenant_id = $1;
```

Recursive CTE for a tree stored as `parent_id`. Always bound the depth and guard against cycles
(the `CYCLE` clause, PostgreSQL 14+), or one bad row hangs the request:

```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id, name, 1 AS depth FROM categories WHERE id = $1
  UNION ALL
  SELECT c.id, c.parent_id, c.name, t.depth + 1
  FROM categories c JOIN tree t ON c.parent_id = t.id
  WHERE t.depth < 50
) CYCLE id SET is_cycle USING path
SELECT id, name, depth FROM tree WHERE NOT is_cycle;
```

## N+1 queries

One query for a list and then one more per row. Each is fast, so no slow-query log shows it; the
request is slow because of round trips.

Find it: log query count per request in development and fail a test when a list endpoint exceeds
a fixed number; in production look in `pg_stat_statements` for a trivial `WHERE id = $1` statement
with a call count orders of magnitude above the rest.

| Cause | Fix |
|---|---|
| Loop that queries per item | One query with `WHERE parent_id = ANY($1)`, grouped in memory |
| Lazy relation access in an ORM | Eager load: Drizzle `with: { ... }`, Prisma `include` or `select` |
| GraphQL resolver per field | Batch per request with a DataLoader |
| Each React server component fetching its own row | Fetch the list's data once in the parent, or batch behind a per-request cache (`0x:react-nextjs`) |
| Count or sum per row | A grouped subquery or `LATERAL` join in the list query |

An ORM that loads a relation with one extra query for all parents is fine; one query per parent is
the bug. Pass id lists as a single array parameter (`= ANY($1::uuid[])`): the wire protocol allows
at most 65,535 parameters per statement, and an `IN` list with one placeholder per id hits that
and creates a different statement shape for every list length.

## Reading and overriding ORM SQL

Turn on query logging in development (Drizzle `logger: true`, Prisma `log: ['query']`), or print one
statement (Drizzle `.toSQL()`). Paste the statement with real parameters into `psql` under
`EXPLAIN (ANALYZE, BUFFERS)` (`indexes-query-plans.md`).

Override with hand-written SQL when the ORM selects every column of wide tables on a hot path,
issues a query per row, joins in application memory, or cannot express the statement: window
functions, `DISTINCT ON`, `LATERAL`, recursive CTEs, `ON CONFLICT ... WHERE`,
`FOR UPDATE SKIP LOCKED`, multi-row updates from `VALUES`.

Use the parameterized escape hatch (Drizzle's `sql` template tag, Prisma's `$queryRaw` tagged
template). The `Unsafe` and `raw` variants concatenate strings; injection rules are in
`0x:web-security`. Raw results are typed by assertion only, so parse them with a schema at the
boundary. A query used in several places can live in a view that the ORM maps like a table.

## Upserts and bulk writes

```sql
INSERT INTO usage_daily AS u (tenant_id, day, events)
VALUES ($1, $2, $3)
ON CONFLICT (tenant_id, day) DO UPDATE SET events = u.events + EXCLUDED.events
RETURNING events;
```

- The conflict target must match a unique index exactly. For a partial unique index repeat its
  predicate: `ON CONFLICT (slug) WHERE deleted_at IS NULL`.
- `DO NOTHING ... RETURNING` returns no row when the row already existed. For get-or-create, follow
  with a SELECT, or use `DO UPDATE` and accept the write.
- Two rows with the same key in one statement fail with "cannot affect row a second time".
  Deduplicate the batch first.
- Skip no-op updates so they do not create dead rows, WAL and trigger runs:
  `DO UPDATE SET name = EXCLUDED.name WHERE t.name IS DISTINCT FROM EXCLUDED.name`.
- Every attempted insert consumes a sequence value even when it conflicts. Upsert-heavy tables
  need `bigint` identities.
- Prefer `ON CONFLICT` to `MERGE` for upserts: `MERGE` can still raise a unique violation when two
  sessions insert the same key.

| Rows | Method |
|---|---|
| Up to a few thousand | One multi-row `INSERT`, or arrays through `unnest` (below), in one transaction |
| Tens of thousands | Batches of 1,000 to 5,000 rows, one transaction per batch |
| Hundreds of thousands and up | `COPY` into a staging table, then `INSERT ... SELECT ... ON CONFLICT` |

```sql
INSERT INTO contacts (email, name)
SELECT * FROM unnest($1::text[], $2::text[])
ON CONFLICT (email) DO NOTHING;
```

`unnest` keeps the statement at a fixed number of parameters whatever the row count. Sort each
batch by key so concurrent batches lock rows in the same order and cannot deadlock. Large deletes
and updates follow the same rule: batches of a few thousand rows by key range, each committed, never
one statement over millions of rows (it holds every row lock, floods replicas and bloats the table).

## Keyset pagination

`OFFSET n` reads and discards n rows, so cost grows with depth and concurrent inserts shift rows
between pages. Use it only for small, bounded admin lists. For feeds, APIs and exports:

```sql
-- index: (tenant_id, created_at DESC, id DESC)
SELECT id, created_at, total_minor
FROM orders
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)     -- last row of the previous page; omit for the first page
ORDER BY created_at DESC, id DESC
LIMIT 21;                             -- page size + 1 tells whether another page exists
```

- The sort must end in a unique column, and the index must match the filter prefix and the sort.
  The row comparison `(a, b) < ($2, $3)` becomes a single index range; it needs every sort column
  in the same direction and NOT NULL.
- JavaScript dates hold milliseconds, `timestamptz` holds microseconds. A cursor that passes
  through a `Date` rounds, and rows are skipped. Carry the timestamp as text
  (`created_at::text`) or page on a time-ordered id alone (`WHERE id < $2 ORDER BY id DESC`).
- Keyset gives next and previous, not "jump to page 40", and no total count. The opaque cursor
  format the API exposes is specified in `0x:api-design`.

## Manual SQL against production

Claude writes the change and its count and before-image queries as a file in the repository; a
person (or a reviewed pipeline job) runs it against production. Claude holds no production
credentials (`0x:ai-coding-agents`, `permissions-governance.md`), so it never executes this itself
and never pulls production rows into the conversation; the steps are for whoever runs it. At
Prototype, with no real user data, the before-image is optional; the review, `BEGIN` and the row
count are not.

1. Write the change as a file in the repository; it is the record of what was done.
2. Run the predicate as a `SELECT count(*)` and look at a sample. Record the count.
3. Execute inside a transaction, with timeouts, taking a before-image:

```sql
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';
CREATE TABLE ops.fix_20261122_orders AS
  SELECT * FROM orders WHERE tenant_id = 42 AND status = 'open' AND created_at < '2026-07-01';
UPDATE orders SET status = 'void', updated_at = now()
  WHERE tenant_id = 42 AND status = 'open' AND created_at < '2026-07-01';
-- the reported row count must equal the count from step 2; spot-check, then:
COMMIT;   -- or ROLLBACK
```

4. Undo, if needed, from the before-image:
   `UPDATE orders o SET status = b.status, updated_at = b.updated_at FROM ops.fix_20261122_orders b WHERE o.id = b.id;`

Start with `BEGIN` before typing anything else; psql autocommits, and an `UPDATE` whose `WHERE`
was lost in editing is otherwise permanent. Do not leave the transaction open while thinking: its
row locks block the application and it holds back vacuum. Roll back and return. Schema changes are
transactional too, so the same wrapper protects a manual `ALTER`. Connect as a read-only role by
default and switch to a writing role only for the change (`postgres-operations.md`). Create the
`ops` schema once and grant it to no application role: before-images are copies of customer data.

## Fixing bad records with a backfill

1. Stop the source first. If the bug that wrote bad rows still runs, the fix chases a moving target.
2. Define the bad set as a `SELECT` whose predicate stops matching once a row is repaired. That
   makes the fix idempotent and safe to rerun after an interruption.
3. Count, sample 20 rows, and compute the corrected value in the same `SELECT` next to the current
   one. Review that output; it is the dry run for correctness.
4. Save the before-image (primary key plus the columns to change) into an `ops` table.
5. Dry-run for mechanics: run the real statement inside `BEGIN ... ROLLBACK` on a restored copy or
   a database branch, and compare the affected count with step 3.
6. Execute. Under roughly 10,000 rows, one transaction as above. More than that, keyed batches
   with a commit per batch (the loop is in `migrations.md`).
7. Verify: the bad-set query returns zero, and sums or counts that should be unchanged are.
8. Handle what the rows fed: search index, caches, counters, exports, anything already sent to a
   customer or a payment provider. Keep the before-image for a fixed period, then drop it.

Decide deliberately whether the fix bumps `updated_at` and fires triggers: sync jobs and webhooks
keyed on them will re-run.

## Ask the user

- **Who runs this fix against production, and have they seen the statement, the count and a
  sample?** Default without an answer: it is not run; Claude never runs it.
- **Should customers affected by the bad data be told, or the correction be silent?** It changes
  whether notifications and `updated_at` fire. Default: silent fix, list of affected accounts kept.
- **Do list screens need exact totals and page numbers?** Exact counts on large tables are slow and
  rule out keyset pagination. Default: next/previous with a capped count ("10,000+").
- **How long should before-image tables be kept?** They can contain personal data. Default: 30 days.
