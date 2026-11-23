# Data lifecycle, retention and deletion

Read this when: deciding how long data lives, building user export or account deletion, purging
expired data, offboarding a customer, checking vendor lock-in, archiving cold data, or
encrypting sensitive fields. This file covers the engineering. The legal duties, deadlines and
lawful bases behind it are `0x:privacy-compliance`; nothing here is legal advice.

## Classify data and map where it lives

Deletion, export, retention and breach response all start from the same artifact: a data map
that says which class of data sits in which store. Keep it as a file in the repository so it
changes in the same pull request as the schema or the new vendor. By stage: the map and
collecting less start at Prototype; user export and deletion, the retention configuration and
purge jobs are Launch work; tenant deletion with proof, yearly exit tests, archiving and
per-tenant keys wait for Scale unless a contract demands them sooner.

| Class | Examples | Handling |
|---|---|---|
| Secrets and credentials | Password hashes, session tokens, API keys, OAuth refresh tokens, webhook secrets, TOTP seeds | Never logged, never in analytics, warehouse or search. Third-party credentials encrypted at field level. |
| Payment card data | Card numbers, CVC | Never stored or logged; provider tokens only |
| Sensitive personal data | Health, biometric, precise location, government IDs, bank details, data about children | Collect only if the product needs it; field-level encryption; shortest retention; excluded from every derived store by default |
| Personal data | Name, email, phone, IP address, device and cookie IDs, free text typed by users | Pseudonymize outside the primary database; covered by export and deletion |
| Customer content | What a tenant uploads or enters; often contains other people's personal data | The tenant owns it; delete on tenant instruction and at contract end |
| Internal and public | Plans, feature configuration, published content | No special handling |

The stores to list, including the ones that are always forgotten: primary database and
replicas; backups; cache; search and vector indexes (embeddings derived from personal text are
personal data); object storage including old versions; warehouse raw and modeled layers; event
streams; application logs; the error tracker (request bodies and user context); product
analytics and session replay; the email provider's send logs; support desk; CRM; payment
provider; LLM provider logs; exports sitting in shared drives; and staging or developer copies
of production data.

Make it enforceable rather than aspirational:

- Each map row: store, data classes, purpose, retention period, deletion mechanism.
- Mark personal and sensitive columns in the schema (a column comment or a naming convention)
  and have CI fail when a new column on a user-related table is unclassified.
- Logs use an allowlist of fields; request bodies are not logged by default.
- Production data is not copied to staging or laptops without anonymization. A staging database
  with real customers is an unprotected second production.

## Export and deletion that reach every store

Build both as code paths with tests, not as a runbook. Structure: a registry of handlers, one
per store or vendor, each implementing `export(subject)` and `delete(subject)`; a job runs
every handler, records the outcome per handler, and retries failures. Adding a store means
adding a handler, and the registry is what the review checklist points to.

Decisions to make before coding:

- **Delete or anonymize.** Records the business must keep (invoices, ledger entries, security
  audit logs) stay, detached from the person: the user reference points to a tombstone, and
  name and email are removed. Everything else is deleted. Which records may be kept and for how
  long is a legal question.
- **Content in shared spaces.** A departing member's comments and documents in a team workspace
  normally stay with the tenant, attributed to "Deleted user". Confirm this with the user; it
  is a product and legal choice.
- **Per foreign key, on purpose:** `CASCADE` for data owned by the user, `SET NULL` for
  attribution, `RESTRICT` for financial records. An accidental cascade deletes what must be
  kept; a missing one blocks deletion in production.
- **Soft delete is not deletion.** A `deleted_at` row is still personal data. Soft delete is
  the grace period; a purge job must follow it.

Deletion sequence:

1. Authenticate the request; re-confirm for destructive actions.
2. Immediately: disable the account, revoke sessions, tokens and API keys, cancel subscriptions.
3. Grace period (commonly 7 to 30 days) during which the account can be restored. Where a law
   or contract sets a deadline for completing deletion, the grace period, the batch schedules
   and the vendor deletions all have to fit inside it.
4. Hard-delete job, idempotent and resumable: primary database → object storage (every version)
   → search and vector indexes → cache → warehouse and analytics → each vendor through its
   deletion API (analytics, email, support, CRM, error tracker).
5. Record completion in a deletion log holding the internal ID, timestamps and per-handler
   status, and no personal data.

**Backups** cannot be edited row by row. The common engineering practice: deleted data ages out
of backups within the backup retention period, that period is stated in the privacy
documentation, and after any restore the deletion log is replayed so deleted users do not come
back. Without the replay step, a restore silently resurrects every account deleted since the
backup. Whether this satisfies a particular law or contract is a `0x:privacy-compliance`
question; a short backup retention makes the answer easier.

**Re-import** is the other resurrection path: a connector or sync job that reloads history
brings the person back into the warehouse or CRM. Delete at the source first, then downstream.

Export: generate asynchronously into a machine-readable archive (JSON or CSV plus files),
deliver through an authenticated download that expires within days, and include what the user
provided and what was recorded about them. Exclude other people's data, internal notes about
security or fraud, and secrets.

Check: an integration test creates a user with data in every store, runs the deletion job, and
then searches each store for the user's ID and email (for the database, across all text columns
or a dump). The test fails when a new table or store is added without a handler, which is its
purpose.

## Retention schedule and automatic purge

Define retention in one configuration file that the purge jobs read and the privacy policy
quotes. Starting points below are common engineering practice, not legal requirements; statutory
periods for financial and tax records vary by jurisdiction and need professional confirmation.

| Data | Typical retention |
|---|---|
| Expired sessions, used or expired reset and verification tokens | Days |
| Webhook payload and delivery logs, job history | 14 to 30 days |
| Application logs | 30 to 90 days |
| Soft-deleted records, abandoned uploads, unverified signups | 30 days |
| Search query logs | 90 days |
| Raw analytics events | 12 to 24 months, then aggregates only |
| Security audit log | 1 to 2 years, or the contract term |
| Invoices and accounting records | Statutory; several years; ask an accountant |

Mechanics by store:

- **Large time-based Postgres tables:** partition by time and drop old partitions, which is
  near-instant and leaves no bloat. On a busy table detach first with `ALTER TABLE ... DETACH
  PARTITION ... CONCURRENTLY` (PostgreSQL 14 and later), so the parent is not locked
  exclusively, then drop.
- **Unpartitioned tables:** delete in batches in a loop until no rows remain, with an index on
  the timestamp. One giant `DELETE` is a long transaction that bloats the table, lags replicas
  and can block migrations.

```sql
DELETE FROM webhook_deliveries
WHERE id IN (
  SELECT id FROM webhook_deliveries
  WHERE created_at < now() - interval '30 days'
  ORDER BY created_at
  LIMIT 5000
);
```

- **Redis:** TTL on every key. **Object storage:** lifecycle expiry by prefix. **Warehouse:**
  partition expiration. **Logs and vendors:** the retention setting in each tool, written into
  the data map.

A purge job fails silently by default. Emit rows purged per run and the age of the oldest
remaining row, and alert when that age exceeds retention plus a margin. Provide a legal-hold
flag that exempts a named account or tenant from purging when a dispute requires preservation.

## Analytics data

- **Pseudonymize at capture.** Events carry the internal user ID, never email, name or phone.
  Scrub query strings and free text before sending; URLs carry emails and tokens more often
  than anyone expects. Do not store full IP addresses unless there is a use for them.
- **Pseudonymous is still personal.** Data keyed by a user ID that can be joined back to a
  person remains in scope for deletion and export. Only aggregates without identifiers, and
  without groups small enough to single someone out, fall outside.
- **Keep identity in one place.** In the warehouse, hold directly identifying fields in a single
  dimension table keyed by the pseudonymous ID. Deleting that row plus the ID mapping
  de-identifies the person's event history, provided the events contain no other identifiers.
  Without this design, deletion means rewriting every fact table.
- **Batch deletions.** Row deletes are expensive in columnar stores; collect requests and run
  them on a schedule that fits within the legal deadline, across raw, staging, marts and
  snapshots.
- **Expire raw events.** Keep raw events for the documented period, then keep daily aggregates.
- Use the analytics vendor's person-deletion API as a handler; mask inputs in session replay.

## Deleting a tenant at contract end

1. **Contract.** The agreement states the window between termination and deletion (often 30 to
   90 days) and what is retained. Follow the contract, not a default.
2. **Lock.** At termination the tenant becomes read-only with export available.
3. **Delete.** After the window, run the handler registry by tenant ID. Require a second
   confirmation that includes the tenant's name, and a dry run that prints counts, because the
   operation is irreversible and a wrong ID is catastrophic.
4. **Verify.** Count rows per table for the tenant ID, list the tenant's object prefix
   including versions, query the search index and cache by tenant, and count warehouse rows.
   All must be zero.
5. **Prove.** Issue a deletion record: tenant, date, stores covered, verification results, the
   date by which backups expire, sub-processors instructed, and who executed it. Store it
   without tenant data.

What makes this a one-day feature instead of a month: `tenant_id` as a column on every tenant
table (not reachable only through joins), a tenant prefix in object keys and cache keys, and a
tenant attribute in every index. Enforce the first with a test:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
  AND table_name NOT IN (
    SELECT table_name FROM information_schema.columns
    WHERE table_schema = 'public' AND column_name = 'tenant_id'
  );
```

Every table returned must be on an explicit allowlist of global tables. Kept after deletion:
the business's own records of its relationship with the customer (invoices, contract,
the deletion record) and users who also belong to other tenants, minus their membership.

## Exit test for every store and vendor

Lock-in is discovered at the worst moment: a price change, an account suspension, an
acquisition. For each datastore and vendor holding data the business cannot recreate, perform
an actual export and load it elsewhere, once at adoption and yearly after.

| Holder | Verify |
|---|---|
| Managed Postgres | A logical dump (`pg_dump`) can be taken and restored outside the provider; provider snapshots usually cannot leave |
| Auth provider | User export including password hashes and the hash algorithm; whether it needs a support request |
| Payment provider | Customers, subscriptions and invoices export; stored cards move only by a provider-to-provider migration process, so know how to request it |
| Email provider | Suppression and unsubscribe lists; losing them means mailing people who opted out |
| Product analytics | Raw event export, not only charts |
| CRM, support desk | Full records with attachments and history |
| Object storage | Egress cost and time to copy everything out |
| Domains and DNS | Registrar account control and a zone file export |

At Launch, schedule automated exports of the data held only by vendors (billing, auth users)
into the business's own storage. That is also the backup against losing the vendor account.

## Archiving cold data while keeping it queryable

Archive when an append-only table (events, audit log, old orders) dominates database size and
slows backups, restores and migrations, and its old rows are rarely read.

1. Partition the table by time.
2. Export each closed partition to Parquet in object storage under a dated path, organized by
   tenant if per-tenant deletion must remain possible.
3. Write a manifest per file: path, row count, time range, checksum, schema version.
4. Verify row counts against the partition, then detach and drop it.
5. Query the archive in place with DuckDB or a warehouse external table.

```sql
-- DuckDB, with the httpfs extension and credentials configured
SELECT count(*) FROM read_parquet('s3://acme-archive/audit_log/**/*.parquet')
WHERE occurred_at >= TIMESTAMP '2024-01-01';
```

Rules: decide what the product still shows (for example, history older than two years is
available by export on request) before moving data out from under a feature. The archive stays
inside retention and deletion: set lifecycle expiry on the archive prefix at the retention
limit, and include it in the handler registry. Do not use deep-archive storage classes for data
that must stay queryable. Test reading a three-year-old file after schema changes; record the
schema version so old files remain interpretable.

## Field-level encryption

Disk and database encryption at rest protect against a stolen disk. They do nothing against
SQL injection, a leaked backup, an over-privileged dashboard or a curious operator, because
the database decrypts for anyone who can query. Application-level encryption keeps selected
fields unreadable everywhere except in the application process.

Encrypt: credentials held on behalf of customers (OAuth refresh tokens, third-party API keys),
which need it at every stage; government IDs, bank details, health data and TOTP seeds from
Launch. Do not encrypt everything, since encrypted fields cannot be filtered, sorted or
searched. Passwords are hashed, not encrypted (`0x:auth-identity`).

- **Envelope encryption.** A key-management service holds the master key and never releases
  it. The application asks it to generate or unwrap data keys, encrypts fields locally, and
  stores the wrapped data key or its ID beside the ciphertext.
- **Authenticated encryption through a vetted library** (the AWS Encryption SDK, libsodium,
  Tink; confirm a maintained release exists for the project's language), not hand-assembled
  primitives. With AES-GCM a nonce must never repeat under one key; a repeat breaks
  confidentiality and integrity, and random 96-bit nonces stay safe only up to about 2^32
  encryptions per key, one more reason for a data key per record or per tenant.
- **Bind ciphertext to its place.** Pass tenant ID, table, column and row ID as associated
  data so a ciphertext copied to another row fails to decrypt.
- **Store a key version with every value.** Rotating the master key re-wraps data keys cheaply;
  re-encrypting data is a background job driven by the version column.
- **Lookup by equality** uses a blind index: an HMAC of the normalized value under a separate
  key, in an indexed column. It reveals which rows share a value, so do not use it on
  low-entropy fields. Keep the last four characters in clear for display if needed.
- **Keep plaintext from escaping.** Decrypt at the point of use; exclude these fields from
  logs, caches, the search index, the error tracker and warehouse loads.
- **Restrict and audit decrypt permission** to the application's role. Cache unwrapped data
  keys in memory for minutes so a key-service outage does not stop every read.
- **Crypto-shredding:** with a data key per tenant or per user, destroying the key makes every
  copy unreadable, including backups and event logs. It is the strongest answer to deletion in
  immutable stores. The same property means a lost key is lost data; rely on the key service's
  durability and deletion-delay window. Whether key destruction counts as erasure under a
  given law is a `0x:privacy-compliance` question.

Avoid in-database encryption functions that take the key as a query parameter (pgcrypto's
`pgp_sym_encrypt` and similar): the key travels to the database and can land in statement logs. Key storage and algorithm choices are
`0x:web-security` (`secrets.md`).

## Ask the user

- **What do the privacy policy and customer contracts promise about retention and deletion?**
  The code must match. Default: the retention table above, a 30-day grace period, and deletion
  within the window the contract states.
- **When a user leaves a shared workspace, does their content stay?** Default: it stays with
  the tenant, attributed to a deleted user.
- **Which records must be kept for tax, accounting or sector rules, and for how long?** Needs
  an accountant or lawyer for the jurisdictions involved. Default: keep invoices and ledger
  entries, anonymize the person.
- **How long are backups kept?** That is the true upper bound on how long deleted data
  persists. Default: 30 days.
- **Does the product hold sensitive data or customers' third-party credentials?** If so,
  field-level encryption moves from optional to required. Default: yes for any stored OAuth
  token or third-party API key.
- **Do customers need a deletion certificate or data residency?** Common in enterprise deals;
  cheap if tenant scoping is in place, expensive to retrofit. Default: not yet, but keep
  tenant scoping complete so either can be added.
