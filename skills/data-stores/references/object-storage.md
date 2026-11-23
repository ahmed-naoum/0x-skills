# Object storage and files

Read this when: storing files in S3-compatible storage: bucket setup, access control, signed
URLs, key design, lifecycle rules, public delivery, cleanup and cost. The upload flow itself
(validation, scanning, processing) is `0x:backend-architecture` (`file-uploads.md`).

## Bucket setup

Files go to object storage from the first upload, at every stage. Not in database rows (they
bloat backups, replication and memory) and not on the application's disk (lost on redeploy,
invisible to a second instance).

| Decision | Default | Reason |
|---|---|---|
| Access | Private, public access blocked at account and bucket level | A public bucket is the classic data leak; anything public goes through a CDN instead |
| Buckets | Separate per environment, and separate for private user files, public assets, and backups or logs | Different access, lifecycle and blast radius; a staging bug cannot touch production files |
| Access control lists | Disabled (bucket owner owns everything); policies only | Per-object ACLs are unauditable |
| Encryption at rest | Provider default server-side encryption | Customer-managed keys only for a compliance requirement |
| Credentials | A role or scoped token for the application: get, put, delete on its bucket and prefix only | The application never needs to list buckets, change policy or delete the bucket |
| CORS | Only if the browser uploads or fetches directly; list exact origins and methods | `*` with credentials-bearing flows invites abuse |
| Listing | Never public; never used on a request path | Listing is slow, paginated and billed |

Create buckets through infrastructure as code so the settings are reviewable and identical
across environments.

## Every object has a database row

The database is the index, the access-control list and the inventory. The bucket is a dumb blob
holder. Anything the product needs to know about a file is a column, because object metadata
cannot be queried.

```sql
CREATE TABLE files (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     uuid NOT NULL REFERENCES tenants(id),
  uploaded_by   uuid REFERENCES users(id),
  bucket        text NOT NULL,
  storage_key   text NOT NULL UNIQUE,
  original_name text NOT NULL,
  content_type  text NOT NULL,
  size_bytes    bigint,
  checksum_sha256 text,
  status        text NOT NULL DEFAULT 'pending',  -- pending | ready | deleted
  created_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz
);
```

Key design:

```text
tenants/<tenant_id>/<kind>/<file_id>            private files
public/<kind>/<content-hash>.<ext>              public, cacheable assets
tmp/<file_id>                                   expires by lifecycle rule
```

- **Never put the user's filename in the key.** It carries personal data into URLs and logs,
  collides, and breaks on encoding. Keep it in `original_name` and send it back through the
  download's content-disposition.
- **Tenant prefix first.** It makes per-tenant deletion, export, cost attribution, prefix-scoped
  credentials and lifecycle rules possible.
- **Random IDs, not sequential ones.** Keys end up in URLs.
- **Objects are immutable. A changed file is a new key and an updated row.** Overwriting in
  place causes stale CDN copies, torn reads during upload and no way back.

Order of operations, which is where consistency is won or lost:

- **Create:** insert the row as `pending` → the client uploads → the server confirms with a
  `HEAD` request and records the real size and checksum → mark `ready`. Only `ready` rows are
  shown or downloadable. Never trust a client-declared size or type.
- **Delete:** mark the row deleted in the transaction → a job deletes the object → the row is
  removed later. Never delete the object inside a transaction that can still roll back, and
  never rely on `ON DELETE CASCADE` to clean files: the database removes the rows and the
  objects stay, billed forever. Either soft-delete, or have the deletion write the keys to a
  deletion queue table.
- **Keep deleted objects at least as long as the database's point-in-time recovery window.** A
  database restored to yesterday must still find the files its rows point to.

## Signed URLs for private downloads

The application authorizes, the storage serves. On each download request: load the file row,
check that the caller may read it, then sign a URL for that key.

```ts
import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const url = await getSignedUrl(
  s3,
  new GetObjectCommand({
    Bucket: file.bucket,
    Key: file.storageKey,
    ResponseContentDisposition: `attachment; filename="${asciiSafeName}"`,
    ResponseContentType: file.contentType,
  }),
  { expiresIn: 300 }, // seconds
);
```

- **A signed URL is a bearer token.** Whoever has it can download until it expires; it cannot
  be revoked individually. It ends up in browser history, proxy logs and chat messages.
- **Expiry: 1 to 15 minutes for a download started by a click.** Longer only for large files on
  slow connections (expiry is checked when the request starts, not during transfer). There is a
  provider maximum, and a URL signed with temporary role credentials stops working when those
  credentials expire, whatever expiry was requested.
- **Sign at click time, not at page render.** A list of 50 files with 50 signed URLs in the
  HTML goes stale while the tab is open and gets cached. Link to an application route such as
  `/files/:id/download` that checks access and answers with a redirect to a fresh URL.
- **Never put signed URLs in emails, notifications or stored records.** Store and send the
  application route.
- **Force download for untrusted types.** `attachment` disposition and the stored content type
  stop an uploaded HTML or SVG file from rendering as a page. Sanitize the filename before
  placing it in the header.
- **Log the grant** (who, which file, when) in the application; storage access logs do not know
  the user.
- For pages showing many private images, per-object signing defeats caching. Use the CDN's
  signed cookies or signed URLs over a path prefix, or an authenticated image route with
  private cache headers.

Signed upload URLs: a presigned `PUT` cannot cap the upload size by itself; a presigned `POST`
policy can (`content-length-range`), where the provider supports it. Details and the
verification step belong to `0x:backend-architecture`.

## Choosing a provider

The price of storage per gigabyte differs little. The bill is decided by egress (bytes leaving
the provider), request counts for small objects, and where the compute that reads the files runs.

| Provider | Choose when | Know |
|---|---|---|
| AWS S3 | The application runs on AWS; compliance features are needed (object lock, replication, fine-grained IAM, event notifications, many storage classes) | Internet egress is billed per gigabyte and dominates for download-heavy products; put a CDN in front |
| Cloudflare R2 | Download-heavy or media-heavy products; the site is already behind Cloudflare; multi-cloud readers | No egress fee; storage and operations are billed. S3-compatible API with gaps; verify each feature needed (lifecycle, storage classes, notifications, object lock) against current documentation |
| Backblaze B2 and similar | Large volumes of backups and archives at low cost | Fewer integrations; check egress terms |
| Google Cloud Storage, Azure Blob | The application runs in that cloud | Same economics as S3 |
| Storage bundled with a PaaS | Prototype; small files; convenience matters more than unit cost | Usually a markup over an underlying store; check egress and size limits before Launch |

Rules: keep storage in the same cloud and region as the code that processes the files, because
every cross-provider read pays egress and latency. If the bytes mostly flow to end users, weigh
zero-egress storage. If the user has no preference and no AWS footprint, R2 behind its CDN is a
sound default for user files; on AWS, S3.

"S3-compatible" is not identical. Expect to set the endpoint, a placeholder region, and
sometimes path-style addressing; newer AWS SDK releases enable integrity checksums by default,
which some compatible stores reject until configured (`requestChecksumCalculation:
"WHEN_REQUIRED"` in the JavaScript SDK). Keep provider specifics in one storage module with a
small interface (put, get-signed-url, head, delete) so a move is a configuration change plus a
copy job.

## Lifecycle rules, storage classes and versioning

Set these when the bucket is created; nobody returns to do it until the bill hurts.

| Rule | Setting | Why |
|---|---|---|
| Abort incomplete multipart uploads | After 1 to 7 days, on every bucket | Abandoned parts are invisible in listings and billed indefinitely |
| Expire `tmp/` | 1 day | Scratch space cleans itself |
| Expire generated exports and reports | 7 to 30 days | They can be regenerated |
| Expire noncurrent versions | 30 days (match the recovery need) | Without it, versioning keeps every overwritten and deleted byte forever |
| Remove expired delete markers | On | Housekeeping for versioned buckets |

**Versioning.** Enable it on buckets holding user data that cannot be recreated: an overwrite
or delete (including one by a bug or a leaked credential) becomes recoverable. Two consequences:
it must be paired with the noncurrent-version expiry above, and a "deleted" object still exists
as an older version until that rule removes it, which matters for deletion promises
(`data-lifecycle.md`). Versioning is not a backup against losing the account or the bucket; for
data whose loss would end the business, replicate to a second account or provider at Scale.
Object lock (write-once retention) is for compliance and ransomware resistance, and locked
objects cannot be deleted early by anyone, so apply it only to buckets that need it.

**Storage classes.** Cheaper classes charge less for storage and more for access, with strings
attached: a minimum storage duration (deleting early still bills the full period), a minimum
billable object size, per-request transition fees and retrieval fees. So:

- Standard for anything accessed, small, or short-lived. Millions of small objects moved to an
  infrequent-access class can cost more than leaving them.
- Automatic tiering (S3 Intelligent-Tiering) when access patterns are unknown and objects are
  large enough to benefit.
- Infrequent-access for large objects kept more than a few months and rarely read: old
  attachments, completed exports that must be retained.
- Archive classes for data kept for obligations and essentially never read. Retrieval can take
  minutes to hours and must be requested; never put anything a user can click on there.

Check current thresholds and prices before writing a transition rule; do the arithmetic for
the bucket's real object-size distribution.

## Public assets through a CDN

- The application emits URLs on a domain it controls (`assets.example.com`), never the raw
  bucket hostname. The CDN reads from the bucket with origin credentials while the bucket stays
  private. This keeps caching, TLS, logs and the ability to change providers.
- **Immutable keys make caching trivial.** With a content hash or unique ID in the key, set
  `Cache-Control: public, max-age=31536000, immutable` at upload and never purge. A replaced
  avatar is a new key and a row update. A mutable key (`avatars/123.png`) means purges, stale
  images and support tickets.
- Cache-control and content-type are object metadata fixed at upload; changing them later means
  copying the object onto itself. An object uploaded without a content type is served as a
  generic binary and downloads instead of displaying.
- **Serve user-uploaded content from a separate registrable domain** (not a subdomain of the
  app), with `X-Content-Type-Options: nosniff`. Uploaded HTML, SVG or scripts must never run
  with the application's cookies or origin.
- Store the original once and derive resized variants through an image service or on-demand
  transformation with cached results (`0x:web-performance`).
- Large public files are a cost-attack surface where egress is billed: set a budget alert, and
  rate-limit or require a signed URL for big downloads.

Header semantics and purging are in `0x:web-networking` (`http-caching.md`).

## Orphans and quotas

Orphans are objects with no live row. Sources: abandoned uploads, failed delete jobs, cascade
deletes, multipart leftovers, old versions. They are invisible to the product and visible only
on the invoice.

1. **Pending sweeper** (hourly): rows `pending` for more than 24 hours → delete object, delete row.
2. **Deletion worker**: processes soft-deleted rows or the deletion queue, with retries;
   deleting a missing object is a success.
3. **Reconciliation** (monthly at Launch): take the bucket's inventory report, or a full
   listing done offline, and diff it against `files.storage_key`. Report objects without rows
   and rows without objects. Delete only orphans older than a few days, to avoid racing live
   uploads, and run in report-only mode first. Rows without objects are the worse finding:
   they are lost user files.
4. **Watch** total bytes and object count per bucket and alert on unexpected growth.

Per-tenant quotas:

- Usage is `sum(size_bytes)` over `ready` rows, with sizes recorded from the server-side `HEAD`,
  or a per-tenant counter updated in the same transaction that marks a file ready or deleted.
- Check the quota before issuing an upload URL, counting `pending` reservations so parallel
  uploads cannot overshoot, and enforce a per-file maximum in the upload policy and again at
  confirmation.
- Decide what counts: derived variants and old versions usually do not count against the
  customer, but they do cost money, so track them separately.
- Warn at 80 percent, block new uploads at 100 percent, and never delete data for being over
  quota.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Storage bill grows while usage is flat | No multipart-abort rule, versioning without expiry, orphans | Lifecycle rules; reconciliation |
| Download links fail for some users | URL signed at render and expired, or temporary credentials rotated | Sign at click through an application route |
| File shows as broken after a database restore | Objects hard-deleted inside the recovery window | Delay object deletion past the window |
| User sees an old image after replacing it | Mutable key cached | Immutable keys |
| Browser upload fails with a CORS error | Bucket CORS lacks the origin, method or header | Exact origins; expose `ETag` if the client reads it |
| Image downloads instead of displaying | Missing content type at upload | Set it at upload; copy-in-place to repair |
| Egress dominates the invoice | Direct bucket delivery, or compute in another cloud | CDN; co-locate; zero-egress store |

## Ask the user

- **Which provider, and where does the application run?** Default: the cloud the app is in; R2
  when there is no AWS footprint or downloads dominate.
- **How long are deleted files recoverable?** Sets noncurrent-version expiry and deletion delay.
  Default: 30 days, shortened if a deletion promise in the privacy policy requires it.
- **Are any files public, and may they be indexed or hotlinked?** Default: everything private;
  public only for assets meant for anonymous visitors.
- **What are the per-file size limit and per-plan storage quota?** These are pricing decisions.
  Default: a conservative per-file cap and a quota per plan, shown in the product.
- **Is there a retention obligation for any file type** (invoices, contracts, medical or
  financial records)? It overrides lifecycle expiry; see `0x:privacy-compliance`.
