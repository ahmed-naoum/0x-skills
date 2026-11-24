# File uploads and document processing

Read this when: users upload, import or export files, or the server must process images, video, CSV
or PDFs; or an upload path is slow, fails on large files, or raises a security question. Bucket
configuration, lifecycle rules and providers: `0x:data-stores` (`object-storage.md`).

## Direct-to-storage upload

Bytes do not pass through the application server: serverless hosts cap request bodies at a few
megabytes, a slow mobile client occupies a connection for minutes, and buffering bodies in memory
lets a handful of uploads exhaust the process.

1. The client asks the server for an upload, sending the declared name, type and size.
2. The server authenticates, authorizes, checks the size limit, the type allowlist and the tenant's
   storage quota, and generates the object key itself: `tenants/{org_id}/uploads/{uuid}`. The
   client's filename is stored as metadata for display, never used in the key.
3. The server inserts a `pending` file row and returns a presigned request expiring within minutes.
4. The client uploads straight to storage, showing progress.
5. The client calls a `complete` endpoint (or a storage event fires). The server reads the object's
   real size and first bytes, verifies them (next section), moves the row to `uploaded` and enqueues
   processing.
6. A sweeper deletes `pending` rows older than a day with their objects; abandoned uploads are
   normal. A lifecycle rule can do the object half only if pending uploads sit under their own
   prefix or tag and are moved on completion.

The signature must bind the size, or the limit is a suggestion. A presigned POST policy can carry a
size range; a presigned PUT only an exact signed `Content-Length`, where the SDK and provider sign
that header. The AWS SDK for Rust has no POST-policy helper (it presigns PUT, GET and multipart
parts), and not every S3-compatible store implements POST (Cloudflare R2 documents it as
unsupported). So the Rust default is a PUT with the declared length and type, enforced at step 5:
anything over the limit is deleted.

```rust
use std::time::Duration;
use aws_sdk_s3::{Client, config::RequestChecksumCalculation};
use aws_sdk_s3::presigning::{PresignedRequest, PresigningConfig};

/// A client for presigning only: checksums only where the operation requires them.
pub fn presigning_client(base: &aws_sdk_s3::Config) -> Client {
    let conf = base.to_builder().request_checksum_calculation(RequestChecksumCalculation::WhenRequired);
    Client::from_conf(conf.build())
}

/// The browser sends `uri()` with every header in `headers()`.
pub async fn presign_put(s3: &Client, bucket: &str, key: &str, mime: &str, len: i64) -> anyhow::Result<PresignedRequest> {
    let expires = PresigningConfig::expires_in(Duration::from_secs(300))?;
    let put = s3.put_object().bucket(bucket).key(key).content_type(mime).content_length(len);
    Ok(put.presigned(expires).await?)
}
```

- Inspect `headers()` once in a test: if `content-length` is not among the signed headers, the size
  is not bound and step 5 is the only limit.
- AWS SDKs added default CRC32 checksums in 2025, and a presigned URL can then carry checksum
  parameters the browser's upload does not match or a non-AWS store rejects. Symptom:
  `SignatureDoesNotMatch` or another 4xx on presigned uploads only. Hence the `WhenRequired` client
  above; test a real upload against the real store.
- The bucket needs a CORS rule for the app's origin and the upload method (browser multipart
  uploads also need `ETag` exposed). Never trust the `complete` call's claims: the server reads
  size and type from storage, and a file is usable only once its row says so.
- Proxying through the server is acceptable at Prototype for small files (avatars under a few
  megabytes): stream the body to storage instead of extracting `Bytes`, and set a per-route body
  limit (axum's `DefaultBodyLimit`) as well as one at the proxy.

## Type and size: verify content

The extension and the `Content-Type` header are chosen by the sender. Decide by content.

| Rule | How |
|---|---|
| Allowlist, never a blocklist | A short list of accepted types per upload field; everything else is refused |
| Sniff the leading bytes | Range-read the first kilobytes from storage and detect the format from its signature: `infer::get(&head)` returns the detected type, and its `mime_type()` must be on the allowlist and match the declared type |
| Images: decode and re-encode | Decoding proves the file is an image; re-encoding drops embedded payloads and metadata (EXIF location included) and normalizes the format. Apply EXIF orientation first or photos turn sideways |
| Pixel limits, not only byte limits | A small compressed file can decode to gigabytes: set width, height and allocation limits before decoding |
| SVG | A document that can carry script. Refuse it, rasterize it, or sanitize and serve it only from the user-content origin as an attachment |
| Archives and office files (zip inside) | Cap entry count and total uncompressed size while extracting, and reject entries whose path escapes the target directory |
| HTML, XML and anything unrecognized | Never served inline |

```rust
use std::io::Cursor;
use image::{DynamicImage, ImageDecoder, ImageError, ImageFormat, ImageReader, Limits};

/// Decode under limits, apply EXIF orientation, re-encode. CPU-heavy and parses hostile input:
/// call it from a job, inside spawn_blocking.
pub fn normalize_photo(bytes: &[u8]) -> Result<Vec<u8>, ImageError> {
    let mut limits = Limits::default();
    (limits.max_image_width, limits.max_image_height) = (Some(8_000), Some(8_000));
    limits.max_alloc = Some(256 * 1024 * 1024);
    let mut reader = ImageReader::new(Cursor::new(bytes)).with_guessed_format().map_err(ImageError::IoError)?;
    reader.limits(limits);
    let mut decoder = reader.into_decoder()?;
    let orientation = decoder.orientation()?;
    let mut img = DynamicImage::from_decoder(decoder)?;
    img.apply_orientation(orientation);
    let mut out = Cursor::new(Vec::new());
    DynamicImage::ImageRgb8(img.into_rgb8()).write_to(&mut out, ImageFormat::Jpeg)?;
    Ok(out.into_inner())
}
```

The pure-Rust `image` crate is memory-safe but slower than libvips; at volume use libvips bindings
or a managed image service. Text formats (CSV, JSON) have no signature: parse them to validate.

## Serving user files

A file a user uploaded is content an attacker wrote. Served from the application's origin and
rendered by the browser, it runs with the application's cookies and storage.

- Serve user content from a separate registrable domain (`example-usercontent.com`), not a subdomain
  of the app: subdomains can share cookies with the parent domain and count as the same site for
  cookie rules. Every response from that origin carries:

```text
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'none'; sandbox
Content-Disposition: attachment; filename="report.pdf"
```

- A signed storage URL bypasses the application, so the headers must come from the object and the
  signature: store the verified `Content-Type` on the object at upload, set the response disposition
  when signing the GET (`response_content_disposition` on the request builder), and add `nosniff`
  and the CSP with a response-header rule on the CDN in front of the bucket.
- Inline display is an allowlist (raster images, audio, video and, if the product needs it, PDF);
  everything else downloads as an attachment. `Content-Type` is the type the server verified and
  stored, never the one the client sent.
- Build the download filename from the stored display name with control characters, quotes and path
  separators removed; use the `filename*` form for non-ASCII names.
- Private files: authorize in the application, then redirect to a signed GET URL that lives for
  minutes; never render signed URLs into cached pages or logs. Public files: content-addressed or
  versioned keys behind a CDN with long cache lifetimes.
- Video and large downloads need range requests; object storage and CDNs provide them, a naive
  streaming proxy through the app does not. Delivery formats, responsive images and CDN image
  optimization: `0x:web-performance` (`images-fonts.md`).

## Processing in background jobs

Decoding media is CPU and memory heavy and parses hostile input. It never runs in the request, and
inside a job it runs in `spawn_blocking`, or it stalls every other task on that worker thread. File
status goes `pending`, `uploaded`, `processing`, then `ready` or `failed` (with a reason the UI can
show); the UI renders a placeholder until `ready` and polls or subscribes.

| Media | Default | Trap |
|---|---|---|
| Images | Keep the original private and immutable. Resize on demand through a CDN image service, or pre-generate a fixed set of variants in a job | Free-form on-demand dimensions let anyone generate unlimited variants: allowlist sizes or sign the transform URL |
| Video | A managed video service that ingests, transcodes to adaptive streaming and serves | Running ffmpeg in-house means long jobs, large instances and a codec matrix. Only for simple, short clips |
| Office documents to PDF or preview | Headless LibreOffice in its own container | Slow, memory-hungry and prone to hanging: hard timeout, one conversion per process |
| Text extraction, OCR, PDF thumbnails | A job per file with a page cap | A thousand-page PDF is a valid file; cap pages and time |

- Every job is idempotent: output keys derive from the file ID and the variant, so a rerun
  overwrites the same objects.
- Bounded: a timeout, a memory limit and low concurrency, sized by memory per job, not by cores.
- Isolated: the worker has no credentials beyond the bucket prefixes it needs; media crates and
  tools stay patched, because parsers are a recurring source of vulnerabilities.
- External tools run with an argument vector, never a shell string, and die with their timeout:

```rust
use std::{path::Path, process::Stdio, time::Duration};
use tokio::process::Command;

/// `input` is a generated temp name, never the user's filename.
pub async fn office_to_pdf(input: &Path, out_dir: &Path) -> anyhow::Result<()> {
    let mut child = Command::new("soffice").args(["--headless", "--convert-to", "pdf", "--outdir"])
        .arg(out_dir).arg(input).stdin(Stdio::null())
        .kill_on_drop(true) // the timeout drops `child`; without this the process keeps running
        .spawn()?;
    let status = tokio::time::timeout(Duration::from_secs(60), child.wait()).await??;
    anyhow::ensure!(status.success(), "converter exited with {status}");
    Ok(())
}
```

- Temp files in a `tempfile::TempDir`, deleted on drop; a SIGKILL skips the drop, so also clear the
  temp directory at worker start. Stream between storage and the tool where it allows; container
  disk is small and disappears.

## Resumable and multipart uploads

A single request is fine up to roughly 100 MB on a good connection (rule of thumb). Above that, or
for mobile users, split the file so a dropped connection costs one part, not the upload. S3-style
multipart is the default when the storage supports it:

1. Server: create the multipart upload, store `upload_id` with the pending file row.
2. Server: presign one URL per part number on request (`upload_part().presigned(...)`).
3. Client: upload parts of 8-16 MB, three or four in parallel, retrying each part on its own with
   backoff, and keep each part's `ETag`.
4. Server: complete with the ordered part numbers and ETags, then verify as for any upload.
5. Resume: the client keeps `upload_id` and finished part numbers; the server can list the parts.

- Every part except the last has a minimum size (5 MiB on S3) and the part count is capped (10,000
  on S3), so the part size must grow with the file.
- Incomplete multipart uploads are invisible in listings and billed until aborted. A lifecycle rule
  that aborts them after a few days is the most often forgotten step.
- The ETag of a multipart object is not a hash of the content. For integrity, use the storage's
  checksum feature or hash on the client and compare after completion.
- On the client, Uppy implements chunking, parallelism, retry and resume, and no Rust/WASM library
  matches it: embedding it through JS interop is the pragmatic exception (`0x:frontend-foundations`,
  `browser-runtime-wasm.md`). In Rust you own part sizing, bounded parallelism, per-part retry and
  resume state.

The alternative is the tus protocol: the client sends chunks to a tus server that tracks the offset,
and resumes by asking for it. Choose it when the storage has no multipart API or the upload must
pass through infrastructure under your control. It adds a stateful server component.

## CSV import and export

**Import** is a job with a preview, never a request that parses and inserts:

1. Upload the file to storage like any other.
2. Parse a sample, let the user map columns to fields, and preview the first rows as read.
3. Dry run: stream the whole file through validation without writing. Report counts and errors.
4. On confirmation, stream again and write in batches of 500-1,000 rows, each batch its own
   transaction, every row tagged with the `import_id`.
5. Produce an error report: a CSV of the failed rows with the original row number, the column and a
   message a non-developer understands, ready to fix and upload again.

- Parse with the `csv` crate (synchronous: inside `spawn_blocking`) or `csv-async`, deserializing
  rows into a serde struct whose errors carry the line number. Splitting on newlines and commas
  breaks on the first quoted field containing either.
- Encoding: strip a UTF-8 byte-order mark; bytes that are not valid UTF-8 probably come from a
  spreadsheet in a legacy Windows code page: decode with `encoding_rs`, or ask. Delimiter:
  decimal-comma locales export with semicolons; detect from the header line, show it in the preview.
- Keep identifiers, postal codes and phone numbers as `String` (leading zeros). Parse dates only in
  a declared format: `03/04/2026` is two different days. Decimal commas need the same care.
- Make reruns safe: upsert on a natural key or an external ID column, so fixing ten rows and
  uploading the whole file again does not duplicate the rest.
- One transaction for a million rows holds locks and blocks vacuum for the duration. Batches plus
  `import_id` give undo ("delete everything from import 42") without it.
- Default: import valid rows, report the rest, offer undo. Cap rows and file size per plan, show
  progress, and run imports on the bulk queue with per-tenant concurrency of one.

**Export.** Small and bounded: stream rows from the database (`fetch` returns a stream) into a
streaming body; never collect the file into a `Vec`. Large or slow: a job writes the file to storage
and notifies the user with a short-lived signed link.

- Formula injection: a cell starting with `=`, `+`, `-`, `@`, tab or carriage return runs as a
  formula in spreadsheet software. Prefix user-supplied text cells with a single quote, never
  numeric columns (negative numbers must survive); strip it again where the file is re-imported.
- Let the `csv` writer quote fields containing the delimiter, quotes or newlines. Write a UTF-8
  byte-order mark when the audience opens files in Excel, which otherwise misreads non-ASCII text.
- An export is bulk data leaving the system: require a permission, scope it by tenant through the
  normal data layer, and write an audit entry.

## Generating PDFs

| Approach | Use when | Cost |
|---|---|---|
| The provider's document (payment provider invoices and receipts) | It exists | None; do not rebuild it |
| Typst, as a CLI in the image or as a library | Invoices, tickets, reports, certificates from a template | Its own markup rather than HTML and CSS; fast and light enough for a job |
| A PDF crate that draws in code (`printpdf`, `genpdf`) | Labels and simple fixed layouts | Layout by hand |
| Headless Chromium printing HTML (a Gotenberg container, or a DevTools-protocol crate such as chromiumoxide) | Existing HTML and CSS, charts | Hundreds of megabytes per browser; a worker or separate service |
| Hosted HTML-to-PDF API | Serverless-only hosting, or no wish to run browsers | Per-document price; document content goes to a vendor |

- With a browser: one per worker, a fresh context per document, pages closed after each and the
  browser restarted periodically, or memory climbs until the container dies. It renders inside your
  network: use an escaping template engine (askama and maud escape by default) and block or
  allowlist the page's network requests, or a user-controlled `<img>` or `<iframe>` URL reaches
  internal services.
- Install the fonts in the image, including CJK and emoji fonts if content can contain them. A
  missing font renders as boxes and only shows up with real customer data.
- Print CSS does the layout in the browser route: `@page { size: A4; margin: 20mm }`, `break-inside:
  avoid` on rows and cards, `thead` repeating on each page.
- Legal and financial documents are generated once, stored in object storage and served from there.
  Regenerating an invoice from current data silently changes a document already sent.
- Generate in a job with a timeout (the process rules above); the user gets a link or an email.

## Malware scanning and quarantine

Add this when files uploaded by one party are downloaded by another, or an enterprise customer's
security questionnaire asks for it. Skip it at Prototype, and for images that are always re-encoded.

1. Uploads land in a quarantine bucket or prefix, status `pending_scan`; no download URL is issued.
2. A job scans the object: a ClamAV daemon as its own service (streamed to clamd over TCP), the
   cloud provider's malware scanning for object storage, or a scanning API.
3. Clean: move to the serving bucket, status `clean`, continue processing.
4. Infected: status `infected`, never served, uploader told, event logged, deleted after retention.
5. Scanner error, timeout or skipped file: stays quarantined. Fail closed.

- ClamAV loads its signature database into memory, and its documentation asks for several gigabytes
  of RAM (check the current figure; a signature reload briefly needs more). Run it as a daemon that
  jobs call, not as a process started per file, and keep signatures updating.
- Scanners skip files above their configured size limits and can report them as clean by default.
  Align the scanner limits with the upload limit (clamd: `MaxFileSize`, `MaxScanSize`,
  `StreamMaxLength`) and turn on the option that flags oversized files (`AlertExceedsMax`).
- Prove the pipeline with the EICAR test file in a test: it must end `infected` and undownloadable.
- Signature scanning catches known malware only: the separate origin, attachment disposition and
  type allowlist remain the main defense. Never send customer files to public multi-engine scanning
  sites, which share samples with third parties.

## Ask the user

- **Which file types and what maximum size must be accepted?** Each type adds parsing risk and
  processing work. Assume common raster images and PDF, 10 MB, until told otherwise.
- **Are uploaded files private to the uploader's organization or publicly reachable?** It decides
  between signed URLs and public CDN delivery. Assume private.
- **How long are originals and deleted files kept?** Storage cost and erasure duties depend on it.
  Assume originals are kept while the record exists and removed with it.
- **For imports, should valid rows go in when others fail?** Partial import with an error report is
  friendlier; all-or-nothing is safer for financial data. Assume partial with undo.
- **Do customers require malware scanning or will files be shared between organizations?** It adds a
  scanner service and a quarantine step. Assume not until Launch with B2B customers.
