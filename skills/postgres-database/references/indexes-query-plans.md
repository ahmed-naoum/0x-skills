# Indexes and query plans

Read this when: a query or endpoint is slow, database CPU or I/O is high, or deciding which indexes
to add, change or drop.

## Method

1. Find the statement that matters. Rank by total time, not by the slowest single run
   (`pg_stat_statements`, below). Guessing from the code is wrong more often than right.
2. Get real parameter values: a large tenant, a common status, a deep page. A plan for a tiny
   tenant proves nothing.
3. Run `EXPLAIN (ANALYZE, BUFFERS)` against production-sized data: a replica, a restored copy or a
   database branch. A development database with 500 rows always chooses a sequential scan and
   always looks fast.
4. Change one thing: the query, an index or the statistics. Rerun and compare buffers and time.
5. Ship the index with `CREATE INDEX CONCURRENTLY` (`migrations.md`) and confirm in
   `pg_stat_statements` that the statement's mean time fell.

`EXPLAIN ANALYZE` executes the statement. Wrap writes in `BEGIN; EXPLAIN (ANALYZE) ...; ROLLBACK;`.

By stage: at Prototype index foreign keys and the filter behind each list page, nothing more. From
Launch keep `pg_stat_statements` on and use this method when something is slow. At Scale review the
top statements and the unused-index list on a schedule (monthly is a workable start).

## Reading a plan

```text
Limit  (cost=0.42..55.12 rows=20 width=140) (actual time=0.012..0.026 rows=20 loops=1)
  Buffers: shared hit=8
  ->  Index Scan using orders_tenant_created_idx on orders  (cost=0.42..35976.18 rows=13154 width=140)
                                                            (actual time=0.011..0.024 rows=20 loops=1)
        Index Cond: (tenant_id = 1)
        Filter: (status = 'open'::text)
        Rows Removed by Filter: 40
```

Read from the innermost node outward. Look at these, in order:

| Look at | Meaning | Act when |
|---|---|---|
| Estimated `rows` versus actual `rows` on each node | Whether the planner understood the data | Off by 10x or more: fix statistics first (last section); a new index will not cure a bad estimate |
| `actual time` and `loops` | Time is per loop; total is time x loops | An inner node with thousands of loops is a nested loop over too many rows |
| `Rows Removed by Filter` | Rows fetched, then thrown away | Much larger than rows returned: the index does not cover the filter |
| `Buffers: shared hit / read` | 8 kB pages touched; `read` came from outside Postgres's cache | Thousands of buffers for a few rows: missing index, wrong index or bloat |
| `Sort Method: external merge  Disk:` and `Batches:` above 1 on a hash | The operation spilled to disk | Provide the order from an index, fetch fewer rows, or raise `work_mem` for that role |
| `Heap Fetches` on an Index Only Scan | Table visits the index could not avoid | High: the table needs vacuum (covering section) |
| `Planning Time` close to execution time | Too many partitions or indexes, or a very large join | Simplify, or use prepared statements |

`cost` is in planner units and only comparable within one plan. A plan that shows `JIT` with
compile time near the execution time is paying for compilation it does not need: set `jit = off`
for transactional workloads.

## When a sequential scan is the problem

It is correct on small tables and when the query returns a large share of the table (roughly
above 5 to 10 percent). Otherwise:

| Cause | Fix |
|---|---|
| No index on the filter columns | Add one that matches filter and sort (next section) |
| Function or cast on the column: `lower(email) = $1`, `created_at::date = $1` | Expression index on the same expression, or rewrite as a range on the bare column |
| Parameter type forces a cast of the column (a `numeric` parameter against an integer column, `id::text = $1` from an ORM) | Cast the parameter, not the column: `WHERE id = $1::bigint` |
| `LIKE '%term%'` or `ILIKE` | Trigram index: `USING gin (name gin_trgm_ops)` with the `pg_trgm` extension |
| `LIKE 'prefix%'` under a non-C collation | `text_pattern_ops` index, or a trigram index |
| Composite index exists, but the query does not filter on its first column | Reorder or add an index led by a column the query does filter on |
| `OR` across different columns | One index per branch (bitmap OR), or rewrite as `UNION` |
| Estimate says most rows match when few do | Statistics (last section) |
| `ORDER BY x LIMIT n` walks an index on `x` and filters for a long time | Composite index: filter columns first, then `x` |

## Matching an index to filter and sort

Column order in a B-tree: equality columns first, then the sort column(s) of an `ORDER BY ... LIMIT`
query, or else the one range column. A range column placed before the sort columns breaks the
index order and forces a sort. For

```sql
SELECT id, total_minor FROM orders
WHERE tenant_id = $1 AND status = 'open'
ORDER BY created_at DESC LIMIT 20;
```

the index is `(tenant_id, status, created_at DESC)`: Postgres descends to the tenant and status,
reads 20 entries already in order and stops. With `(tenant_id, created_at)` it filters status row
by row; with `(created_at)` alone it may walk the whole index.

- An index serves queries that constrain a leading prefix of its columns. `(a, b)` makes a
  separate index on `(a)` redundant, and does little for a filter on `b` alone. PostgreSQL 18 can
  skip over a low-cardinality leading column; do not design around that.
- Direction matters only for mixed sorts (`a ASC, b DESC`); a B-tree is read in either direction.
- In a multi-tenant schema, nearly every index starts with `tenant_id`.
- Index every foreign-key column that is joined on or whose parent rows get deleted.

**Partial indexes** cover a hot subset and cost almost nothing to maintain:
`CREATE INDEX ... ON jobs (run_at) WHERE status = 'queued'`. The query must repeat the predicate
with a literal written into the SQL text, not bound: a parameter (`status = $1`) cannot be proven
to match once a generic plan is used, and SQLx's statement cache makes generic plans likely.
Good targets: unprocessed rows, non-deleted rows, the rare value of a skewed status.

**Expression indexes** must match the query's expression exactly: `ON accounts (lower(email))`
serves `WHERE lower(email) = lower($1)` and nothing else.

Derive indexes from the queries that exist, not from the columns that exist. An index for a query
nobody runs is pure write cost.

## Index types

| Type | Use for | Notes |
|---|---|---|
| B-tree | Equality, ranges, sorting, `IS NULL`, uniqueness | The default; the only type worth trying first |
| GIN | Many values per row: `jsonb` containment, arrays, full-text `tsvector`, trigrams | Slower writes; cannot sort; `jsonb_path_ops` is smaller when only `@>` is needed |
| GiST | Ranges and overlap, exclusion constraints, geometry, nearest-neighbor ordering | Needed for no-overlap constraints (`btree_gist` for the scalar part) |
| BRIN | Very large append-only tables filtered on a column that follows insertion order (`created_at`) | Tiny; useless once rows are updated or arrive out of order |
| Hash | Equality on very long values | No uniqueness, no ranges, no multi-column; a B-tree is nearly always as good |

Vector indexes (HNSW) and full-text search design are in `0x:data-stores`.

## Finding the costliest queries

Enable `pg_stat_statements` (managed providers preload it or offer a switch; then `CREATE EXTENSION
pg_stat_statements`). It aggregates statements with constants replaced by `$n`.

```sql
SELECT round(total_exec_time::numeric)                                            AS total_ms,
       calls,
       round(mean_exec_time::numeric, 2)                                          AS mean_ms,
       round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 1)  AS pct,
       rows / greatest(calls, 1)                                                  AS rows_per_call,
       shared_blks_read, temp_blks_written,
       left(query, 100)                                                           AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 15;
```

| Pattern | Diagnosis | Usual fix |
|---|---|---|
| Huge `calls`, tiny `mean_ms`, large `pct` | N+1 or chatty polling | Batch or eager-load (`sql-queries.md`), or cache |
| Few `calls`, large `mean_ms` | Report, export or missing index | Index, or move it off the primary (`replication-scaling.md`) |
| Large `rows_per_call` | Over-fetching | `LIMIT`, pagination, fewer columns |
| Large `shared_blks_read` | Reads beyond the cache | Better index, or more memory |
| `temp_blks_written` above zero | Sorts or hashes spilling to disk | Index that provides the order; `work_mem` for that role |

The top five statements usually account for most of the load; fix those and stop. Run
`SELECT pg_stat_statements_reset();` after a fix so the next reading is clean. To see real
parameters and plans of slow statements, set `log_min_duration_statement = '500ms'` or load
`auto_explain` with `auto_explain.log_min_duration`.

## Unused and duplicate indexes

Every index is written on each insert and on each update that changes an indexed column, adds
WAL, lengthens vacuum and competes for cache. An update that touches no indexed column can stay
within its page (a HOT update) and skip index maintenance entirely, so an index on a frequently
updated column such as `updated_at` or a counter is the most expensive kind.

```sql
-- Never scanned since statistics were last reset; constraint-backing indexes excluded
SELECT s.relname AS table_name, s.indexrelname AS index_name,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size, s.idx_scan
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0 AND NOT i.indisunique AND NOT i.indisprimary
ORDER BY pg_relation_size(s.indexrelid) DESC;

-- Exact duplicates: same table, columns, operator classes, expressions and predicate
SELECT indrelid::regclass AS table_name, array_agg(indexrelid::regclass) AS duplicates
FROM pg_index
GROUP BY indrelid, indkey::text, indclass::text, indoption::text,
         coalesce(pg_get_expr(indexprs, indrelid), ''), coalesce(pg_get_expr(indpred, indrelid), '')
HAVING count(*) > 1;
```

Before dropping: confirm the statistics cover at least a full business cycle including month-end
jobs (`SELECT stats_reset FROM pg_stat_database WHERE datname = current_database()`), check the
same counters on every replica (they are per server), and look for prefix duplicates by hand
(`(a)` next to `(a, b)`). Of a duplicate pair keep the one that backs a constraint. Save
`pg_get_indexdef()` output so the index can be recreated, then `DROP INDEX CONCURRENTLY`.

## Covering indexes and index-only scans

An index-only scan answers from the index without visiting the table. Add the selected columns
that are not part of the search key with `INCLUDE`:

```sql
CREATE INDEX CONCURRENTLY orders_customer_cover_idx
  ON orders (customer_id) INCLUDE (status, total_minor);
```

- Worth it for hot, narrow reads: a lookup run thousands of times a minute, existence checks,
  counts over a range. Not worth it for wide rows or `SELECT *`.
- It works only for pages that vacuum has marked all-visible. On a heavily updated table
  `Heap Fetches` stays high and the benefit disappears; lower that table's autovacuum threshold
  (`postgres-operations.md`).
- Keep included columns few and small. Each one enlarges the index and, if updated, defeats HOT
  updates for that column.

## Bad plans from statistics

The signature: a node estimated at a handful of rows returns thousands (or the reverse), and above
it sits a nested loop or a sort that only made sense for the estimate.

| Cause | Fix |
|---|---|
| Table changed a lot since the last analyze: bulk load, restore, large backfill, new partition | `ANALYZE table_name;` as the last step of any bulk operation |
| Major-version upgrade before PostgreSQL 18 | Statistics are not carried over: `ANALYZE` the whole database |
| Big table where 10 percent churn (the default trigger) is days of data; "today's rows" estimated near zero | `ALTER TABLE t SET (autovacuum_analyze_scale_factor = 0.01);` |
| Skewed column with many distinct values | `ALTER TABLE t ALTER COLUMN c SET STATISTICS 1000;` then `ANALYZE t;` |
| Correlated columns (`tenant_id` and `project_id`, city and postcode) multiplied as if independent | `CREATE STATISTICS s (dependencies, ndistinct, mcv) ON a, b FROM t;` then `ANALYZE t;` |
| Filter on an expression or a JSONB key | Expression index (it collects statistics), or `CREATE STATISTICS` on the expression |
| Prepared statement switched to a generic plan that is bad for a skewed parameter. SQLx prepares and caches every statement per connection, so from the sixth run Postgres may pick a generic plan | `ALTER ROLE ... SET plan_cache_mode = force_custom_plan`, or `SET LOCAL` in that transaction |
| Planner avoids index scans on SSD storage | `random_page_cost = 1.1` (`postgres-operations.md`) |

Postgres has no query hints in core. When statistics are right and the plan is still wrong, change
the query's shape (a materialized CTE, a `LATERAL` join, splitting an `OR`) rather than forcing
planner switches globally; `SET LOCAL enable_nestloop = off` is a diagnostic, not a fix.

## Ask the user

- **Which screens or endpoints feel slow, and for which customers?** Aggregate statistics hide a
  large tenant's pain. Default: start from the top of `pg_stat_statements`.
- **Is there a copy of production-sized data to test against?** Plans from small data mislead.
  Default: use a provider branch or a restored backup; never tune against a seed database.
- **May unused indexes be dropped now, or is there seasonal work (month-end, annual reports) that
  the statistics window missed?** Default: keep anything whose purpose is unclear until a full
  cycle has passed.
- **Is slightly stale data acceptable on this page?** If so, caching or a replica may be cheaper
  than tuning. Default: tune first, cache second.
