# File uploads and document processing

Read this when: users upload, import or export files, or the server must process images, video,
CSV or PDFs; or an upload path is slow, fails on large files, or raises a security question.

Bucket configuration, lifecycle rules and storage providers are in `0x:data-stores`
(`object-storage.md`). This file covers the application flow around them.

## Direct-to-storage upload

Bytes do not pass through the application server. Serverless hosts cap request bodies at a few
megabytes, a slow mobile client occupies a server connection for minutes, and buffering a body in
memory lets a handful of uploads exhaust the process.

1. The client asks the server for an upload, sending the declared name, type and size.
2. The server authenticates, authorizes, checks the size limit, the type allowlist and the
   tenant's storage quota, and generates the object key itself:
   `tenants/{orgId}/uploads/{uuid}`. The client's filename never becomes part of the key; it is
   stored as metadata for display.
3. The server inserts a file row with status `pending` and returns a presigned request that
   expires within minutes.
4. The client uploads straight to storage, showing progress.
5. The client calls a `complete` endpoint (or a storage event notification fires). The server
   reads the object's real size and first bytes, verifies them (next section), and moves the row
   to `uploaded`, then enqueues processing.
6. A sweeper deletes `pending` rows older than a day together with their objects. Abandoned
   uploads are normal. A storage lifecycle rule can do the object half only if pending uploads
   sit under their own prefix or tag and are moved on completion.

The signature must bind the size, or the limit is a suggestion. A presigned POST policy can carry
a size range; a presigned PUT cannot express a range, only an exact signed `Content-Length` where
the SDK and provider support signing that header.

```ts
import { createPresignedPost } from '@aws-sdk/s3-presigned-post';

const { url, fields } = await createPresignedPost(s3, {
  Bucket: bucket,
  Key: key,
  Conditions: [
    ['content-length-range', 1, 10 * 1024 * 1024],
    ['eq', '$Content-Type', contentType],
  ],
  Fields: { 'Content-Type': contentType },
  Expires: 300, // seconds
});
// Browser: multipart/form-data POST to `url`, every entry of `fields` first, the file last.
```

- Not every S3-compatible store implements presigned POST (Cloudflare R2 documents it as
  unsupported; check the provider's current API table). Where only PUT exists, sign the exact
  length and type if possible and treat step 5 as the enforcement: delete anything over the limit.
- Recent AWS SDK versions add a CRC32 checksum to uploads by default, and a presigned PUT URL can
  then carry checksum parameters that the browser's upload does not match or that a non-AWS
  store rejects. Symptom: `SignatureDoesNotMatch` or another 4xx on presigned uploads only. Set
  `requestChecksumCalculation: 'WHEN_REQUIRED'` on the signing client and test a real upload.
- The bucket needs a CORS rule for the app's origin and the upload method. Multipart uploads from
  a browser also need `ETag` in the exposed headers.
- Never trust the `complete` call's claims. The server reads size and type from storage.
- The row, not the object, is what the product sees: a file is usable only once its row says so.
- Proxying through the server is acceptable at Prototype for small files (avatars under a few
  megabytes). Stream to storage instead of buffering, and cap the body at the proxy and in the app.

## Type and size: verify content

The extension and the `Content-Type` header are chosen by the sender. Decide by content.

| Rule | How |
|---|---|
| Allowlist, never a blocklist | A short list of accepted types per upload field; everything else is refused |
| Sniff the leading bytes | Range-read the first kilobytes from storage and detect the format from its signature (the `file-type` package does this); compare with the allowlist and the declared type |
| Images: decode and re-encode | Passing through an image library (sharp) proves the file is an image, drops embedded payloads and metadata, and normalizes the format. sharp strips metadata unless asked to keep it; apply EXIF orientation before stripping or photos turn sideways |
| Pixel limits, not only byte limits | A small compressed file can decode to gigabytes. Keep the library's input-pixel limit on and cap dimensions |
| SVG | It is a document that can carry script. Refuse it, rasterize it, or sanitize and serve it only from the user-content origin as an attachment |
| Archives and office files (which are zip archives) | Cap entry count and total uncompressed size while extracting, and reject entries whose path escapes the target directory |
| HTML, XML and anything unrecognized | Never served inline |

Location data in photo metadata is a privacy leak when images are shown to other users: strip
it on every derivative. Text-based formats (CSV, JSON, plain text) have no signature; validate
them by parsing.

## Serving user files

A file a user uploaded is content an attacker wrote. If it is served from the application's
origin and the browser renders it, it runs with the application's cookies and storage.

- Serve user content from a separate registrable domain (`example-usercontent.com`), not a
  subdomain of the app: subdomains can share cookies with the parent domain and count as the
  same site for cookie rules.
- Headers on every response from that origin:

```text
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'none'; sandbox
Content-Disposition: attachment; filename="report.pdf"
```

- A signed storage URL bypasses the application, so the headers must come from the object and
  the signature: store the verified `Content-Type` on the object at upload, set the response
  disposition when signing the GET, and add `nosniff` and the CSP with a response-header rule on
  the CDN in front of the bucket.
- Inline display is an allowlist: raster images, audio, video and, if the product needs it, PDF.
  Everything else downloads as an attachment.
- `Content-Type` is the type the server verified and stored, never the one the client sent.
- Build the download filename from the stored display name with control characters, quotes and
  path separators removed; use the `filename*` form for non-ASCII names.
- Private files: authorize in the application, then redirect to a signed GET URL that lives for
  minutes. Do not render signed URLs into cached pages, and do not log them.
- Public files: content-addressed or versioned keys behind a CDN with long cache lifetimes; a
  changed file gets a new key.
- Video and large downloads need range requests; object storage and CDNs provide them, a naive
  streaming proxy through the app does not.

Delivery formats, responsive images and CDN image optimization: `0x:web-performance`
(`images-fonts.md`).

## Processing in background jobs

Decoding media is CPU and memory heavy and parses hostile input. It never runs in the request.

File status: `pending` → `uploaded` → `processing` → `ready` or `failed` (with a reason the UI
can show). The UI renders a placeholder until `ready` and polls or subscribes.

| Media | Default | Trap |
|---|---|---|
| Images | Keep the original private and immutable. Resize on demand through the host's or CDN's image service, or pre-generate a fixed set of variants in a job | On-demand resizing with free-form dimensions lets anyone generate unlimited variants: allowlist sizes or sign the transform URL |
| Video | A managed video service that ingests, transcodes to adaptive streaming and serves | Running ffmpeg in-house means long jobs, large instances and a codec matrix. Do it only for simple, short clips |
| Office documents to PDF or preview | Headless LibreOffice in its own container | Slow, memory-hungry and prone to hanging: hard timeout, one conversion per process, restart often |
| Text extraction, OCR, thumbnails of PDFs | A job per file with a page cap | A thousand-page PDF is a valid file; cap pages and time |

Rules for every processing job:

- Idempotent: output keys are derived from the file ID and the variant, so a rerun overwrites
  the same objects.
- Bounded: a timeout, a memory limit and low concurrency. Size worker concurrency by memory per
  job, not by CPU count.
- Isolated: the worker has no credentials beyond the bucket prefixes it needs, and media
  libraries are kept patched because their parsers are a recurring source of vulnerabilities.
- Spawn external tools with an argument array, never by interpolating a filename into a shell
  string. Use generated temp names, and clean the temp directory in a `finally`.
- Stream between storage and the tool where the tool allows it; local disk on a container is
  small and disappears.

## Resumable and multipart uploads

A single request is fine up to roughly 100 MB on a good connection (rule of thumb). Above that,
or for mobile users, split the file so a dropped connection costs one part, not the upload.

S3-style multipart, the default when the storage supports it:

1. Server: create the multipart upload, store `uploadId` with the pending file row.
2. Server: presign one URL per part number on request.
3. Client: upload parts of 8-16 MB, three or four in parallel, retrying each part on its own
   with backoff, and keep each part's `ETag`.
4. Server: complete the upload with the ordered list of part numbers and ETags, then verify as
   for any upload.
5. Resume: the client keeps `uploadId` and finished part numbers locally; the server can list
   the parts storage already holds.

- Every part except the last has a minimum size (5 MiB on S3) and the part count is capped
  (10,000 on S3), so the part size must grow with the file.
- Incomplete multipart uploads are invisible in listings and billed until aborted. Add a
  lifecycle rule that aborts them after a few days. This is the most often forgotten step.
- The ETag of a multipart object is not a hash of the content. For integrity, use the storage's
  checksum feature or hash on the client and compare after completion.
- A maintained client (Uppy) implements chunking, parallelism, retry and resume. Do not write it
  by hand.

The alternative is the tus protocol: the client sends chunks to a tus server that tracks the
offset, and resumes by asking for it. Choose it when the storage has no multipart API or the
upload must pass through infrastructure under your control. It adds a stateful server component.

## CSV import and export

**Import** is a job with a preview, never a request that parses and inserts.

1. Upload the file to storage like any other.
2. Parse a sample, let the user map columns to fields, and show the first rows as they will be
   read.
3. Dry run: stream the whole file through validation without writing. Report counts and errors.
4. On confirmation, stream again and write in batches of 500-1,000 rows, each batch its own
   transaction, every row tagged with the `import_id`.
5. Produce an error report: a CSV of the failed rows with the original row number, the column
   and a message a non-developer understands, ready to fix and upload again.

- Parse with a streaming CSV parser. Splitting on newlines and commas breaks on the first quoted
  field containing either.
- Encoding: strip a UTF-8 byte-order mark; if the bytes are not valid UTF-8, the file probably
  came from a spreadsheet in a legacy Windows code page, so decode accordingly or ask.
- Delimiter: spreadsheets in locales that use a decimal comma export with semicolons. Detect
  from the header line and show the result in the preview.
- Keep identifiers, postal codes and phone numbers as strings (leading zeros). Parse dates only
  in a declared format: `03/04/2026` is two different days. Decimal commas need the same care.
- Make reruns safe: upsert on a natural key or an external ID column, so fixing ten rows and
  uploading the whole file again does not duplicate the rest.
- One transaction for a million rows holds locks and blocks vacuum for the duration. Batches
  plus `import_id` give undo ("delete everything from import 42") without it.
- Decide partial versus all-or-nothing with the user. Default: import valid rows, report the
  rest, offer undo.
- Cap rows and file size per plan, show progress, and run imports on the bulk queue with
  per-tenant concurrency of one.

**Export**:

- Small and bounded: stream the response from a database cursor with keyset pagination. Never
  build the file in memory.
- Large or slow: a job writes the file to storage and notifies the user with a short-lived
  signed link.
- Formula injection: a cell beginning with `=`, `+`, `-`, `@`, tab or carriage return is run as
  a formula by spreadsheet software. Prefix user-supplied text cells with a single quote; leave
  numeric columns alone so negative numbers survive. The quote stays in the data, so strip it
  again when the same file can be imported back.
- Quote fields containing the delimiter, quotes or newlines, doubling embedded quotes. Write a
  UTF-8 byte-order mark when the audience opens files in Excel, which otherwise misreads
  non-ASCII text.
- An export is bulk data leaving the system: require a permission, scope it by tenant through
  the normal data layer, and write an audit entry.

## Generating PDFs

| Approach | Use when | Cost |
|---|---|---|
| The provider's document (payment provider invoices and receipts) | It exists | None; do not rebuild it |
| A PDF library that draws or lays out in code (PDFKit, pdf-lib, a React PDF renderer) | Fixed layouts: invoices, tickets, labels, certificates | Layout is manual, CSS does not apply; light enough for a job or even a request |
| Headless Chromium printing HTML (Playwright, Puppeteer) | Rich layouts, charts, existing HTML and CSS | Hundreds of megabytes of memory and a large binary; a worker or separate service, not a serverless function without a build made for it |
| Hosted HTML-to-PDF API | Serverless-only hosting, or no wish to run browsers | Per-document price; document content goes to a vendor |

```ts
const page = await context.newPage();
await page.setContent(html, { waitUntil: 'networkidle' });
const pdf = await page.pdf({ format: 'A4', printBackground: true });
await page.close();
```

- Launch one browser per worker and a fresh context per document; close pages in a `finally`
  and restart the browser periodically, or memory climbs until the container dies.
- The HTML is rendered by a real browser inside the network. Escape every interpolated value,
  and block or allowlist network requests from the page: a user-controlled `<img>` or `<iframe>`
  URL can otherwise reach internal services or local files.
- Install the fonts in the image, including CJK and emoji fonts if content can contain them.
  A missing font renders as boxes and only shows up with real customer data.
- Print CSS does the layout: `@page { size: A4; margin: 20mm }`, `break-inside: avoid` on rows
  and cards, `thead` repeating on each page.
- Legal and financial documents are generated once, stored in object storage and served from
  there. Regenerating an invoice from current data silently changes a document already sent.
- Generate in a job with a timeout; the user gets a link or an email when it is ready.

## Malware scanning and quarantine

Add this when files uploaded by one party are downloaded by another, or when an enterprise
customer's security questionnaire asks for it. Skip it at Prototype, and for images that are
always re-encoded.

1. Uploads land in a quarantine bucket or prefix. Status `pending_scan`; no download URL is
   issued in this state.
2. A job scans the object: a ClamAV daemon as its own service, the cloud provider's malware
   scanning for object storage, or a scanning API.
3. Clean: move to the serving bucket, status `clean`, continue processing.
4. Infected: status `infected`, never served, uploader told, event logged. Delete after a
   retention period.
5. Scanner error, timeout or skipped file: stays quarantined. Fail closed.

- ClamAV loads its signature database into memory, and its documentation asks for several
  gigabytes of RAM (check the current figure; a signature reload briefly needs more). Run it as
  a daemon that jobs call, not as a process started per file, and keep signatures updating.
- Scanners skip files above their configured size limits and can report them as clean by
  default. Align the scanner limits with the upload limit (clamd: `MaxFileSize`, `MaxScanSize`,
  `StreamMaxLength`) and turn on the option that flags oversized files (`AlertExceedsMax`).
- Prove the pipeline with the EICAR test file in an automated test: it must end as `infected`
  and be undownloadable.
- Signature scanning catches known malware only. The separate origin, attachment disposition
  and type allowlist remain the main defense.
- Do not send customer files to public multi-engine scanning sites: samples are shared with
  third parties.

## Ask the user

- **Which file types and what maximum size must be accepted?** Each type adds parsing risk and
  processing work. Assume common raster images and PDF, 10 MB, until told otherwise.
- **Are uploaded files private to the uploader's organization or publicly reachable?** It
  decides between signed URLs and public CDN delivery. Assume private.
- **How long are originals and deleted files kept?** Storage cost and erasure duties depend on
  it. Assume originals are kept while the record exists and removed with it.
- **For imports, should valid rows go in when others fail?** Partial import with an error report
  is friendlier; all-or-nothing is safer for financial data. Assume partial with undo.
- **Do customers require malware scanning or will files be shared between organizations?** It
  adds a scanner service and a quarantine step. Assume not until Launch with B2B customers.
- **Is video part of the product?** It means a managed video service and its bill. Assume no.
