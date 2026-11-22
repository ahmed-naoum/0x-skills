# HTTP semantics and versions

Read this when: choosing methods, status codes or redirects, reproducing a request with curl, configuring compression, conditional or range requests, or enabling and verifying HTTP/2, HTTP/3, Early Hints, HTTPS DNS records or 0-RTT.

## Methods and status codes

Intermediaries act on the method and the status code without reading the body. Caches store by them, proxies and clients retry by them, monitoring counts by them. Choose them for what the machines in the middle will do.

| Method | Safe | Idempotent | Use | Consequence |
|---|---|---|---|---|
| `GET`, `HEAD` | yes | yes | Read | Cached, prefetched, retried, replayed in 0-RTT, fetched by crawlers and link scanners |
| `PUT` | no | yes | Replace at a known URL | Clients and proxies may retry it |
| `DELETE` | no | yes | Remove | Repeating it must not fail differently in a harmful way |
| `POST` | no | no | Create, trigger an action | Not retried automatically; needs an idempotency key to be retry-safe |
| `PATCH` | no | no (unless designed so) | Partial update | Same as `POST` |

The rule that prevents real incidents: **a `GET` never changes state.** Email security scanners, browser prefetch, chat link previews and crawlers follow every link. "Unsubscribe", "confirm", "delete" and one-time login links that act on `GET` get triggered by robots. Show a page on `GET`, act on `POST`.

| Situation | Status | Notes |
|---|---|---|
| Success with body | 200 | |
| Created | 201 + `Location` | |
| Accepted for background work | 202 | Return where to poll |
| Success, nothing to return | 204 | No body at all |
| Malformed request (unparseable, wrong shape) | 400 | |
| Well-formed but fails validation | 422 | Or 400 everywhere; pick one convention and hold it |
| No or invalid credentials | 401 + `WWW-Authenticate` | "Who are you?" |
| Authenticated, not allowed | 403 | Use 404 instead when existence itself is secret |
| Method not supported here | 405 + `Allow` | |
| State conflict, duplicate | 409 | |
| Precondition (`If-Match`) failed | 412 | |
| Too many requests | 429 + `Retry-After` | |
| Gone permanently | 410 | Deindexed faster than 404 |
| Bug or unhandled failure | 500 | |
| Dependency or overload, try later | 503 + `Retry-After` | Also for maintenance pages, so crawlers do not index them |
| A proxy could not get a valid answer | 502 / 504 | Emitted by proxies; an app rarely should (`proxies-load-balancers.md`) |

Traps: 200 with `{"error": ...}` defeats monitoring, caching rules and retries at every layer. A 5xx for a client mistake pages someone and invites retries; a 4xx for a server fault tells the client not to retry something that would have worked. A 404 page served with status 200 gets cached and indexed. Error body format and API conventions: `0x:api-design`, `requests-responses.md`.

## Reproduce any request with curl

Take the browser out of the problem. In DevTools, right-click the request, "Copy as cURL", then cut it down until the behavior changes.

```bash
curl -sv https://example.com/api/items -o /dev/null          # full exchange: DNS, TLS, request and response headers
curl -sS -D - -o /dev/null https://example.com/              # response headers of a real GET
curl -sS https://example.com/api/items \
  -H 'Authorization: Bearer TOKEN' -H 'Accept: application/json'
curl -sS --json '{"name":"x"}' https://example.com/api/items # POST with JSON content type and accept
curl -sS -c jar.txt -b jar.txt -L https://example.com/login  # keep cookies across requests, follow redirects
curl -sS --resolve example.com:443:203.0.113.10 https://example.com/   # hit one specific server, correct SNI and Host
curl -sS -o /dev/null -w 'dns %{time_namelookup}  tcp %{time_connect}  tls %{time_appconnect}  ttfb %{time_starttransfer}  total %{time_total}  %{http_code} h%{http_version}\n' https://example.com/
```

- The `-w` times are cumulative from the start: TLS cost is `time_appconnect - time_connect`, server think time is roughly `time_starttransfer - time_appconnect` minus one round trip. Interpretation: `network-debugging.md`.
- `-I` sends `HEAD`, which many apps and CDNs answer differently from `GET`. To see `GET` headers use `-D - -o /dev/null`.
- `--resolve` is how to test a new server before the DNS cutover, or the origin behind a CDN, without editing `/etc/hosts`.
- curl sends no `Accept-Encoding` unless told (`--compressed` or an explicit header), no cookies, and a different `User-Agent`. When curl succeeds and the browser fails, the difference is in those headers, a cache, or CORS (`0x:web-security`).
- Force a version with `--http1.1`, `--http2`, `--http3`. Never paste `-k` into a script.

## Redirects

| Code | Permanent | Method on the follow-up | Use |
|---|---|---|---|
| 301 | yes | May become `GET` | Moved pages, HTTP to HTTPS, canonical host |
| 308 | yes | Preserved | Permanent move of an endpoint that receives `POST`/`PUT` |
| 302 | no | May become `GET` | Temporary detour, post-login bounce |
| 303 | no | Always `GET` | After a successful form `POST`, so reload does not resubmit |
| 307 | no | Preserved | Temporary move that must keep method and body |

- **Permanent means cached.** Browsers store a 301/308 and stop asking, for a long time when no cache headers limit it. Launch a move as 302/307, verify, then switch to 301/308, and put `Cache-Control: max-age=3600` on permanent redirects while there is any chance of reversal.
- **One hop.** `http://example.com/x` should reach `https://www.example.com/x` in a single redirect, not HTTP→HTTPS→www→trailing slash. Each hop to a new origin costs a full connection setup.
  Write the rule to emit the final URL directly; HSTS then removes the HTTP hop for returning visitors. One deliberate exception: an apex that is HSTS-preloaded, or that must carry its own HSTS header, redirects to HTTPS on itself before redirecting to `www` (`tls-certificates.md`).
- **Preserve path and query** unless the move is to a single page; dropped query strings break campaign tracking and deep links.
- **Do not redirect API calls.** Clients handle redirected `POST` bodies inconsistently and strip `Authorization` when the redirect crosses origins. An API base URL answers at its final address; give a wrong scheme or host an error rather than a redirect.
- Decide trailing-slash and case conventions once, and make the framework, the proxy and the CDN agree; disagreement is where loops come from.
- A redirect target taken from a request parameter is an open redirect: `0x:web-security`.

Check: `curl -sS -o /dev/null -L -w '%{num_redirects} hops -> %{url_effective}\n' http://example.com/some/path` should print 1 from any entry point (2 from `http://` on an HSTS-preloaded apex).

## Compression

| Content | Do |
|---|---|
| HTML, CSS, JS, JSON, SVG, XML, plain text, source maps, WebAssembly | Compress |
| JPEG, PNG, WebP, AVIF, video, audio, WOFF2, zip, gzip archives | Never compress again: it burns CPU and can grow the body |
| Bodies under about 1 KB | Skip; the saving does not cover the overhead |

- **Negotiate, do not assume.** Serve by `Accept-Encoding`: Brotli (`br`) or Zstandard (`zstd`) where offered, gzip as the universal fallback. Every compressed variant carries `Vary: Accept-Encoding`.
- **Static assets:** compress once at build or let the CDN do it, at the maximum level (Brotli 11). **Dynamic responses:** a low-to-middle level (Brotli 4 to 5, or zstd at its default); high levels cost more CPU time than they save in transfer.
- **Compress at one hop.** With a CDN, the edge compresses toward the browser; the origin can send gzip or identity. Confirm the CDN is not delivering uncompressed because the origin omitted a `Content-Type` it recognizes.
- **Streaming breaks under buffering compression.** Exclude `text/event-stream` and other incrementally flushed responses, or tokens arrive in bursts.
- Compressing a response that contains both a secret and attacker-influenced text enables length side channels (BREACH); mitigation belongs to `0x:web-security`.
- Dynamic compression changes the bytes, so a strong `ETag` no longer matches across encodings; servers weaken it (`W/"..."`) or must vary it per encoding.

Check: `curl -sS -D - -o /dev/null -H 'Accept-Encoding: br, zstd, gzip' https://example.com/app.js | grep -iE 'content-encoding|vary|content-type'`.

## Conditional and range requests

**Conditional requests** let a client that holds a copy ask "still the same?" and get a bodiless 304.

- Send a validator on every cacheable response: `ETag` (preferred) or `Last-Modified`. The client returns it in `If-None-Match` / `If-Modified-Since`.
- A 304 carries the same `Cache-Control`, `ETag` and `Vary` the 200 would, because it refreshes the stored entry's freshness.
- **ETags must be identical across every server and deploy for identical content.** Validators derived from file modification time or inode differ per machine and per build, so each node invalidates the others' caches. Derive from content hash.
- For dynamic responses the saving is real only if the validator is computed before the expensive work (from a version column or `updated_at`), returning 304 without rendering. Hashing the rendered body saves bytes, not server time.
- `If-Match` on writes gives optimistic concurrency with 412 on mismatch: `0x:api-design`, `idempotency-rate-limits.md`.

**Range requests** let a client fetch part of a body: resuming downloads, seeking in media. Some browsers will not play `<video>` at all from a server that ignores ranges.

- Supporting server: `Accept-Ranges: bytes`; a request with `Range: bytes=0-99` gets `206` with `Content-Range: bytes 0-99/12345`; an unsatisfiable range gets 416. `If-Range` with the ETag makes a resume safe when the file changed.
- Object storage and CDNs implement this correctly; an app route that streams a file by hand usually does not. Serve large files from storage through the CDN (`0x:data-stores`, `object-storage.md`), not through application code.
- Ranges apply to the encoded bytes, so on-the-fly compression and ranges do not combine; large downloadable files are served uncompressed or precompressed as a distinct file.

Check: `curl -sS -o /dev/null -D - -H 'Range: bytes=0-99' https://example.com/big.mp4` → `206`; `curl -sS -o /dev/null -w '%{http_code}\n' -H 'If-None-Match: "<etag>"' https://example.com/app.css` → `304`.

## HTTP/2 and HTTP/3

Default: HTTP/3 on at the edge with HTTP/2 and HTTP/1.1 fallback. Behind a CDN or PaaS it is a switch. The hop from the proxy to the app can stay HTTP/1.1 with keep-alive; HTTP/2 to the backend is needed only for gRPC.

How a client finds HTTP/3: it connects over TCP first, sees `Alt-Svc: h3=":443"; ma=86400` on a response, and uses QUIC on later connections; or it learns it before connecting from an `HTTPS` DNS record (below). So a first visit is normally HTTP/2 and a single curl request proves little.

Self-managed:

- Caddy serves HTTP/3 by default; only UDP 443 has to be open.
- nginx (1.25.1 or later with the HTTP/3 module; `nginx -V` must list `--with-http_v3_module`):

```nginx
listen 443 ssl;
listen 443 quic reuseport;
http2 on;
add_header Alt-Svc 'h3=":443"; ma=86400' always;
```

- The firewall, security group and any load balancer in front must pass UDP 443 to the QUIC terminator (`ip-transport.md`). A layer-7 load balancer that does not speak HTTP/3 ends the story there: QUIC terminates at the outermost hop or not at all.
- Start with a short `ma` (an hour) so a bad rollout ages out quickly.
- In nginx, `reuseport` may appear on only one `listen` line per address and port across all server blocks; the other servers use `listen 443 quic;`.

Verify:

```bash
curl -V | grep -o HTTP3                       # is this curl able to speak it at all
curl -sS -o /dev/null -w '%{http_version}\n' --http3 https://example.com/       # 3 if negotiated, falls back otherwise
curl -sS -o /dev/null -w '%{http_version}\n' --http3-only https://example.com/  # fails rather than fall back
curl -sS -D - -o /dev/null https://example.com/ | grep -i alt-svc
```

In DevTools, add the Protocol column to the Network panel: `h3` should appear after a reload. Then confirm in CDN or proxy logs what share of requests uses each version; a rollout that shows 0% h3 is a blocked UDP port.

## Early Hints and preload instead of push or sharding

- **HTTP/2 server push is dead.** Chrome and Firefox removed support and nginx dropped the directive; delete any push configuration.
- **Domain sharding is harmful under HTTP/2 and HTTP/3.** Splitting assets across hostnames was a workaround for HTTP/1.1's per-host connection limit; now it adds handshakes and splits prioritization and congestion state. Consolidate onto one hostname.
- **`103 Early Hints`** sends `Link: <...>; rel=preload` or `rel=preconnect` headers while the server is still computing the real response, so the browser starts fetching during server think time.
  It pays off only when think time is substantial (hundreds of milliseconds) and the hinted resources are render-critical.
  Chromium browsers and Firefox act on it, for navigations only and only over HTTP/2 or HTTP/3; do not count on Safari, and repeat the same `Link` headers on the final response so every browser gets them. Simplest deployment: the CDN's Early Hints feature, which replays `Link` headers it saw on earlier responses.
  Emitting 103 from the origin requires every proxy on the path to pass informational responses; test it, and never send it to HTTP/1.1 clients, some of which mishandle 1xx.
- **Preload sparingly**: only resources discovered late and needed for first render. Over-preloading competes with what matters. Selection and measurement: `0x:web-performance`, `loading-delivery.md`.

## HTTPS and SVCB DNS records

An `HTTPS` record tells a client, during DNS resolution, which protocols the origin speaks and optionally its ECH configuration:

```text
example.com.  300  IN  HTTPS  1 . alpn="h3,h2"
```

- Effects: supporting browsers use HTTP/3 on the first connection, and treat the name as HTTPS-only without the plain-HTTP redirect.
- The record is a promise. Advertising `h3` while UDP 443 is closed, or leaving `ipv4hint`/`ipv6hint` values behind after a move, makes clients attempt and fall back slowly. Publish it from the same source of truth as the `A`/`AAAA` records. When a CDN hosts the DNS for a proxied name it publishes and maintains the record itself, which is the right way to get it.
- Alias mode (priority `0`, pointing the apex at another name) is specified but not something to rely on for apex aliasing across browsers; keep `ALIAS`/flattening for that.
- **Encrypted Client Hello** hides the hostname in the handshake by encrypting it to a key published in the `ech` parameter. Keys rotate frequently and must stay in sync between DNS and the TLS terminator, so use it only as a CDN-managed feature. Some corporate and national networks block ECH connections; expect fallback behavior to matter.
- Check: `dig example.com HTTPS +short` (`dig example.com TYPE65` on old versions).

Default: let the CDN manage it; do not hand-write one before Scale.

## 0-RTT early data

TLS 1.3 and QUIC let a returning client send its first request inside the first flight, saving a round trip. That early data has no replay protection: anyone who captured the packets can send them again and the server will process the request again.

Decision rule:

- **Off** by default at any self-managed terminator.
- **On** only when the audience is latency-sensitive (mobile, far from the edge), and every route reachable in early data is safe to repeat.
- "Safe to repeat" is stricter than "is a `GET`": a `GET` that consumes a one-time token, logs someone in from a magic link, increments a counter that matters, or triggers a payment-provider callback is not safe.

Mechanism when enabled: the terminator marks forwarded early requests with `Early-Data: 1`; the application answers `425 Too Early` to anything not replay-safe, and the client retries after the handshake completes. In nginx: `ssl_early_data on;` plus `proxy_set_header Early-Data $ssl_early_data;`.
A CDN's 0-RTT switch typically limits early data to requests it considers safe by method; read which ones before enabling, and make sure the origin sees the `Early-Data` header.

Check: with the feature on, send a state-changing request flagged `Early-Data: 1` to the origin and confirm it returns 425.

## Ask the user

- **Is a URL change permanent?** A 301/308 is remembered by browsers and search engines and is hard to retract. Default: 302/307 until the new URL has been live and verified, then permanent.
- **Which host is canonical, and do old URLs from a previous site need to keep working?** Decides the redirect map. Default: keep every previously public URL working with a single-hop redirect.
- **Are there non-browser clients (mobile apps, partner integrations, devices) calling the API?** They constrain status-code changes, redirects and protocol upgrades. Default: assume yes for any public API and change nothing about its codes without a versioning plan.
- **Is shaving one round trip for returning mobile users worth the replay review that 0-RTT needs?** Default: no; leave 0-RTT off.
- **Does the product serve large downloads or video?** Decides whether range support and storage-backed delivery need work now. Default: serve them from object storage through the CDN.
