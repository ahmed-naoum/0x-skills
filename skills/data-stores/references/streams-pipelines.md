# Warehouse, pipelines and event streams

Read this when: moving data between systems: deciding whether a warehouse is needed, loading
product, billing and marketing data into one, building trusted metric tables, monitoring
pipelines, syncing segments back to tools, change data capture, or designing an event stream.
Writing the analytical SQL and dashboards on top is the `data` skill; event tracking design is
`0x:product-analytics`.

## Warehouse or read replica

| Situation | Use |
|---|---|
| Prototype; questions about user behavior | The product analytics tool. No warehouse, no replica. |
| Questions answerable from the product database alone | A read replica with a BI tool or SQL client pointed at it |
| A weekly report that is slow on the replica | Rollup tables built by a scheduled job; or a nightly export to Parquet queried with DuckDB |
| Questions that join product data with billing, marketing spend or support data | Warehouse |
| History is needed that the product database overwrites (plan changes, status over time) | Warehouse with snapshots |
| Several people or tools need the same metric definitions | Warehouse plus versioned transformations |
| Customer-facing analytics inside the product | Not the warehouse; see columnar engines in `choosing-datastores.md` |

Never run analytical queries on the primary. A long-running query holds back vacuum for every
table and competes for memory and I/O with user requests. On a replica, long queries either get
cancelled by replication conflicts ("canceling statement due to conflict with recovery") or,
with `hot_standby_feedback` on, cause bloat on the primary; give analytics a dedicated replica
whose lag nobody depends on, and set a statement timeout for the reporting role.

Warehouse choice for a solo founder: a serverless one with no idle cost (BigQuery is the usual
answer; Snowflake with auto-suspend set to its minimum also works; a separate Postgres instance
is acceptable up to tens of gigabytes). Cost traps: on scan-priced warehouses, partition large
tables by date, require a partition filter, and set a per-query and per-day byte limit; on
compute-priced ones, confirm auto-suspend is on. Set a budget alert on day one.

## Loading: one warehouse, three kinds of source

Extract and load raw data first; transform inside the warehouse (ELT). Keep three layers:

| Layer | Contents | Rule |
|---|---|---|
| `raw` | Tables as loaded, one schema per source | Never edited by hand; reloadable |
| `staging` | One model per raw table: renamed, typed, deduplicated, time zones normalized | No joins, no business logic |
| `marts` | Facts and dimensions, metric tables | The only layer dashboards and syncs read |

Sources and their traps:

- **Product database.** Load from a replica or by change data capture, not from the primary
  under load. Incremental loads by `updated_at` miss hard deletes and any row changed without
  bumping the column (bulk SQL, triggers). Fully reload small tables daily; use soft deletes or
  CDC for large ones. Extract by column allowlist: password hashes, tokens, secrets and free-text
  fields with personal data do not belong in the warehouse.
- **Billing.** Revenue numbers come from the payment provider's invoices, charges, refunds and
  disputes, not from the application's `subscriptions` table, which drifts from what was
  actually collected. Handle currency, tax, refunds and proration explicitly. Metric definitions
  are in `0x:payments-billing`.
- **Marketing.** Ad spend and campaign data by day from each platform, plus the attribution
  captured by the product: store UTM parameters and referrer on the user row at signup, because
  no connector can recover them later.
- **Product events.** Batch export from the analytics tool into the warehouse.

What makes the sources joinable is decided in the application, not the warehouse: the product
database stores the payment provider's customer ID, the CRM ID and the analytics distinct ID
against the account. Add those columns before building any pipeline.

Loads must be idempotent: running the same day twice gives the same tables. Use a merge keyed
on the primary key, or replace whole date partitions. Use a cursor with a lookback overlap
(reload the last few hours or days) to catch late-arriving and corrected rows. Store all
timestamps in UTC and define the reporting time zone once, in staging.

## Managed connector or custom script

| Source | Default | Reason |
|---|---|---|
| SaaS APIs with wide, changing schemas (payment provider, ad platforms, CRM, support desk) | Managed connector (Fivetran, Airbyte Cloud, Stitch, or the vendor's own warehouse export) | Their APIs change, paginate and rate-limit in ways that eat days; the connector vendor absorbs it |
| The product's own Postgres | Managed connector if the price fits; otherwise a small script or an open-source loader such as dlt | The schema is known and under control |
| High-volume event or log tables | Custom batch export, or the analytics tool's export | Row-based connector pricing multiplies on high-churn tables |
| A niche API no connector covers | Custom script | No choice |

Rule of thumb: if a connector costs less per month than two hours of the founder's time, buy
it. Before committing, estimate the bill from the row counts that change monthly, since that is
the usual pricing unit.

A custom loader is production code and needs: a stored cursor, idempotent writes, pagination
and rate-limit handling, retries with backoff, a backfill mode for a date range, detection of
new or changed columns, a failure alert, and a scheduler. A scheduled CI workflow is enough at
Launch; an orchestrator (Dagster, Airflow) is a Scale purchase, when dependencies between jobs
become the problem.

## Transformations into trusted metric tables

Transformations are code: SQL `SELECT` models in git, built by a tool that understands their
dependencies (dbt is the default; SQLMesh is an alternative), reviewed in pull requests, and
run by the scheduler after loads.

- **One definition per metric.** Active user, MRR, churn and conversion each exist in exactly
  one model, with a written definition and a stated grain ("one row per account per day").
  Dashboards never recompute them. Two dashboards disagreeing about revenue costs more trust
  than any pipeline bug.
- **Test the keys.** Every model declares its primary key with `unique` and `not_null` tests,
  foreign keys with `relationships`, and enumerations with `accepted_values`. These four catch
  most breakage.
- **Guard against fan-out.** A join to a table with several rows per key silently multiplies
  sums. Aggregate to the join grain before joining, and assert that row counts do not change
  across the join.
- **Reconcile against the source.** A test compares monthly revenue in the mart with the payment
  provider's own report within a tolerance. A metric nobody has reconciled is a guess.
- **Prefer full rebuilds.** Incremental models are faster and add failure modes: late data,
  changed logic that applies only to new rows, schema changes needing a full refresh. Use them
  when the full build is too slow or too expensive, not before.
- **Snapshot mutable dimensions** (plan, account owner, status) so that "which plan was this
  customer on in March" has an answer. The product database only knows today.
- **CI builds changed models and runs tests** in a scratch schema on every pull request.
  `dbt build` runs models and their tests together in dependency order, so a failing test stops
  downstream models from being built on bad data.

## Monitoring

The default failure of a pipeline is silence: the job stops, the dashboard keeps showing last
week's number, and decisions get made on it.

| Check | How | Alert when |
|---|---|---|
| Freshness | Latest loaded timestamp per source table; dbt source freshness | Older than twice the load interval |
| Volume | Rows loaded per run against the trailing average | Zero, or outside an expected band |
| Schema | Column added, removed or retyped at the source | Any change to a column a model uses |
| Quality | The key and enumeration tests above | Any failure |
| Reconciliation | Mart totals against source totals | Beyond tolerance |
| Scheduler heartbeat | A dead-man check pinged at the end of each run | No ping within the expected window |
| Cost | Warehouse and connector spend | Above budget |

Send alerts where application alerts already go. Put "data as of <timestamp>" on every
dashboard so staleness is visible to the reader. Keep the alert list short; a pipeline alert
that fires weekly and is ignored protects nothing.

## Syncing segments back to tools

Reverse ETL pushes warehouse-defined audiences and attributes into CRM, email and ad tools
("trial accounts with three or more active users", lead scores, plan and usage fields). Skip it
until Scale; at Launch, send the handful of needed properties straight from the application to
the email tool or CRM.

When it is built (Hightouch, Census, or a script):

- The segment is a mart model with tests; the sync tool only moves it.
- Upsert by a stable external ID, never by email address, which changes and duplicates.
- Sync differences, not the full table, and respect destination rate limits.
- Carry consent in the model and filter on it: marketing email and ad audiences need a
  permission the user actually gave (`0x:privacy-compliance`).
- Every destination is another copy of personal data and joins the deletion path
  (`data-lifecycle.md`).
- Do not create loops (CRM → warehouse → CRM) without a declared owner per field.
- Nothing the product needs to function may depend on the warehouse. It is hours behind and has
  no uptime commitment; product logic reads the product database.

## Change data capture

CDC reads the database's replication log and emits every row change. It earns its complexity
when several derived stores need the same changes, when bulk SQL and migrations bypass
application hooks, when deletes must be captured, or when the warehouse needs to be minutes
behind instead of a day.

Choose the mechanism:

| | Transactional outbox | Log-based CDC |
|---|---|---|
| What is emitted | Events the application chooses to write, in a designed schema | Every insert, update and delete, in table shape |
| Coupling | Consumers depend on the event contract | Consumers depend on table structure; a migration is a breaking change |
| Captures bulk SQL and manual fixes | No | Yes |
| Effort | A table, a relay job | Replication configuration plus a CDC service |

Default: outbox for events other systems act on; log-based CDC for replicating tables to the
warehouse or a search index, through a managed service. Running Debezium with Kafka Connect is
a team's job.

Postgres logical replication traps:

- **A replication slot retains WAL until its consumer confirms it.** A stopped or forgotten
  consumer fills the primary's disk and takes the database down. Monitor, alert, and cap with
  `max_slot_wal_keep_size`. Drop slots that are no longer used.

```sql
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;
```

- Requires `wal_level = logical` (a restart) and a direct connection, not a transaction-mode
  pooler. Confirm the managed provider supports it and what happens to slots on failover.
- Updates and deletes carry only the primary key of the old row by default. A table without a
  primary key cannot replicate updates or deletes at all. Set `REPLICA IDENTITY FULL` on a
  table only when consumers need the previous values, at a WAL-volume cost.
- Large unchanged column values (TOAST) are omitted from update events; consumers must not
  treat absence as null.
- Schema changes are not replicated as events. Coordinate migrations with consumers: add
  columns first, deploy consumers, then use them.
- Delivery is at-least-once. Consumers upsert by primary key and ignore a change older than
  the one already applied (compare log position or a row version).

## Designing an event stream

Applies to a Kafka-style log, a managed stream, and equally to an outbox with several
consumers. Skip until Scale unless the product itself is event-driven.

- **Events are facts in the past tense** (`invoice.paid`), not commands. The producer does not
  know who consumes.
- **Envelope:** unique event ID, type, schema version, time it occurred, producer, tenant ID,
  entity ID, payload.
- **Schemas are contracts.** Define them in a schema format (JSON Schema, Avro or Protobuf),
  check compatibility in CI, and evolve only by adding optional fields. Renaming, removing or
  retyping a field is a new event version published alongside the old until consumers move.
  Consumers ignore fields they do not know.
- **Partition key = the entity whose events must stay in order** (order ID, account ID).
  Ordering exists only within a partition; there is no global order. A key with few distinct
  values or one giant tenant creates a hot partition. Changing the partition count remaps keys
  and breaks ordering during the change, so choose a count with headroom at creation.
- **Publish through an outbox.** Writing to the database and then to the stream in request code
  loses or invents events when either call fails.
- **Consumers are idempotent.** Delivery is at-least-once; record processed event IDs in the
  same transaction as the effect, or make the effect an upsert by version. "Exactly once" in
  stream platforms covers reads and writes inside the platform, not an email sent or a card
  charged.
- **Replay is the reason to own a log, so design for it.** Retention must exceed the longest
  consumer outage plus rebuild time. A replay must not repeat external side effects: keep
  projection consumers (rebuildable, replay-safe) separate from side-effect consumers
  (notifications, charges), which replay only with effect-level idempotency keys.
- **Poison events:** after bounded retries, park the event in a dead-letter destination and
  alert. Decide per consumer whether to continue past it (loses ordering for that key) or halt.
- **Keep personal data out of long-lived events.** An immutable log cannot honor a deletion
  request. Carry IDs and let consumers look up current data, or encrypt per subject and destroy
  the key (`data-lifecycle.md`).
- **Monitor consumer lag as time**, not message count, with an alert per consumer group.

## Ask the user

- **Which decisions will this data inform, and who looks at it?** Three named questions justify
  a warehouse; "we should have our data in one place" does not. Default: replica plus the
  analytics tool until a cross-source question is blocked.
- **How fresh must the numbers be?** Daily is cheap, hourly moderate, minutes means CDC or
  streaming. Default: daily.
- **What is the budget for warehouse and connectors together?** Default: serverless warehouse,
  managed connectors only for the billing and ad sources.
- **Which metric definitions are official?** How MRR, active and churned are defined is a
  business decision that must be made once, by the founder.
- **May personal data go into the warehouse and on to ad or email tools?** Default: IDs and
  pseudonymous attributes only; no free text; syncs filtered by consent.
