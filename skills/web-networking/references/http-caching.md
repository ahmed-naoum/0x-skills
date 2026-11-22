# HTTP and CDN caching

Read this when: setting `Cache-Control`, `ETag` or `Vary`, designing CDN cache keys, purging on deploy or on content change, raising cache hit ratio, or explaining why a user saw stale content or another user's content.

## The two failure directions

Caching fails in two ways with very different costs. Serving stale content is an annoyance with a purge button. Serving one user's private response to another is a data breach, which in many jurisdictions brings notification duties (`0x:privacy-compliance`). Every rule below is biased accordingly: public content must opt in to shared caching explicitly, and anything that depends on who is asking is never stored by a shared cache.

Three caches sit between the app and the user, and they differ in the one property that matters: whether they can be purged.

| Cache | Controlled by | Purgeable |
|---|---|---|
| Browser | `Cache-Control` (`max-age`, `no-cache`, `no-store`, `immutable`) | No. A response sent with a long `max-age` is out of reach until it expires. The only fix is a new URL |
| CDN / shared proxy | `s-maxage`, `CDN-Cache-Control` or the vendor's surrogate header, plus dashboard rules | Yes, by URL, prefix or tag |
| Framework/application data cache | Framework API | Yes; owned by `0x:react-nextjs` and `0x:data-stores` |

Consequence: give browsers short lifetimes on anything whose URL is stable, and give the CDN long lifetimes plus purging.

## Header recipes

Send an explicit `Cache-Control` on every response. A response with `Last-Modified` and no `Cache-Control` is cached heuristically (a fraction of the time since `Last-Modified`), which nobody intended, and some CDNs apply their own default lifetime to header-less responses.

| Response | Header | Reason |
|---|---|---|
| Fingerprinted static asset (`app.3f9a1c.js`) | `Cache-Control: public, max-age=31536000, immutable` | Content at this URL never changes |
| Public HTML, same for everyone | `Cache-Control: public, max-age=0, s-maxage=3600`, or `Cache-Control: public, max-age=0, must-revalidate` beside `CDN-Cache-Control: max-age=3600` where the CDN reads that header; purge on change | Browser always revalidates; the CDN absorbs the load |
| Public API `GET`, slightly stale is fine | `Cache-Control: public, max-age=60, stale-while-revalidate=300` | Small freshness window, no waiting on refresh |
| Personalized HTML or API, non-sensitive | `Cache-Control: private, no-cache` | Browser may keep it but must revalidate; shared caches must not store it |
| Sensitive: account, billing, tokens, health or financial data, anything after login by default | `Cache-Control: no-store` | Neither the browser's HTTP cache nor any shared cache keeps it. It does not reliably keep the page out of the back/forward cache (Chrome can restore it on Back while the cookies are unchanged), so logout must clear the session cookie |
| Non-fingerprinted static file (`/logo.png`, `/robots.txt`) | `Cache-Control: public, max-age=3600` at most | It will change one day at the same URL |
| Error responses | Short or `no-store`; never inherit the success lifetime | A cached 500 or 404 outlives the fault |

Directive meanings that are commonly reversed:

- `no-cache` means "store, but revalidate before every use". `no-store` means "do not store".
- `private` forbids shared caches only; the browser still caches. It is not a secrecy control by itself.
- `max-age=0, must-revalidate` and `no-cache` behave alike for browsers.
- `s-maxage` overrides `max-age` for shared caches, including a corporate proxy in front of the user. `CDN-Cache-Control` and vendor surrogate headers target only the CDN, which is cleaner when the browser and CDN lifetimes differ; not every CDN reads `CDN-Cache-Control`, so confirm in its documentation and in the cache-status header.
- `immutable` stops revalidation on reload; use it only on fingerprinted URLs.

**Validators.** Send an `ETag` on everything cacheable so expiry costs a 304 instead of a full transfer; requirements for stable ETags are in `http.md`.

**`Vary`.** Lists the request headers that change the response, and each distinct value becomes a separate cache entry. `Vary: Accept-Encoding` is normal.
`Vary: Cookie`, `Vary: User-Agent` or `Vary: Authorization` on a shared-cacheable response creates one entry per user or browser build, which is a 0% hit ratio; `Vary: *` is uncacheable.
CDNs differ in how much of `Vary` they honor, so a response that truly differs by a header must be verified on the actual CDN, or keyed explicitly in its cache-key configuration.

Follow the framework: Next.js sets these headers per route type, and overriding them blindly at the proxy breaks its revalidation model. Change them through the framework's configuration (`0x:react-nextjs`, `rendering-strategies.md`).

## Fingerprinted assets

A content hash in the filename makes the URL a name for exact bytes. That is what allows a one-year `immutable` lifetime, instant rollouts and safe rollbacks, with no purging at all for assets.

- Bundlers do this by default; the gap is usually files referenced by fixed paths (favicons, images in `public/`, fonts loaded by a hand-written URL, a third-party script copied locally). Either route them through the bundler or keep their lifetime short.
- A version query string (`app.js?v=12`) is weaker: some caches ignore or strip query strings, and old and new HTML cannot coexist.
- **Keep old assets after a deploy.** HTML cached minutes ago, an open tab, or a CDN entry still references the previous hashes. Deleting them on deploy produces chunk-load errors and unstyled pages. Retain at least the last several builds, or everything from the past few days.
- Serve a missing asset as 404 with a very short lifetime, so a request that raced the upload does not poison the URL.

## Private and sensitive responses

- Default every authenticated route to `no-store` in one place (middleware or the proxy), and relax per route where caching is deliberate. Per-handler opt-out is how one gets missed.
- Responses with `Set-Cookie` must never be stored by a shared cache: the stored cookie is handed to every later visitor. Many CDNs refuse by default; an "ignore origin headers" or "cache everything" rule overrides that protection.
- By specification a shared cache does not reuse a response to a request that carried `Authorization` unless the response opts in with `public`, `s-maxage` or `must-revalidate`. There is no such rule for cookies, and not every CDN applies the `Authorization` rule either. A cookie-authenticated page that is marked `public`, or that sends no directive under a cache-everything rule, will be cached and served to strangers.
- `no-store` also covers signed URLs, password-reset pages, export downloads and API responses containing tokens.

## Cache keys

The cache key is the set of request properties that select a stored response: by default scheme, host, path and query string. A response is safe to share only if **every input that influenced it is in the key**. The classic leak is a page rendered from the session cookie and cached under a key that contains no cookie.

Patterns for mixed public and personal content, in order of preference:

1. **Split.** Cache the public shell or data for everyone; fetch the personal part from a `no-store` endpoint on the client or in a streamed, uncached region.
2. **Bypass on session.** A CDN rule: if the session cookie is present, skip the cache in both directions (no lookup, no store). Anonymous traffic stays cached.
3. **Key on a small normalized dimension.** When content differs by locale, currency, country, plan tier or experiment bucket, compute that value at the edge and add it to the key. Never key on the raw cookie or a user ID: that is per-user storage of private pages on shared infrastructure with no hit ratio.

Normalization raises hit ratio and removes poisoning surface:

- Drop marketing parameters (`utm_*`, `gclid`, `fbclid`) from the key, or allow-list the parameters each route actually reads. Sort the rest.
- Lowercase the host; settle trailing-slash handling in redirects, not in duplicate entries.
- Keep device class out of the key unless the HTML differs by device.

Check for a leak: request a page logged in, then the same URL without cookies from another machine. Any personal content, any `Set-Cookie`, or a cache-hit status on the logged-in request is a failure.

## Purge and revalidate on deploy

With fingerprinted assets, only HTML and data need invalidating. The order matters:

1. Upload new assets alongside the old ones.
2. Switch the app or HTML to the new version.
3. Purge or revalidate the HTML and data affected, by tag or path.
4. Leave old assets in place.

- Purge narrowly. A purge-everything empties the CDN at once and sends full traffic to the origin while it is busiest restarting; at Scale that is a self-inflicted outage. If a full purge is unavoidable, prefer a soft purge that marks entries stale and serves them while refreshing.
- Version skew is the normal state for minutes after a deploy: old HTML talks to new API, new HTML requests chunks from a node still running the old build. Keep APIs backward compatible across one release and keep both builds' assets reachable (`0x:ci-cd-release`, `deploy-rollback.md`).
- Browsers cannot be purged. If a stable URL was sent out with a long `max-age` by mistake, change the URL; correcting the header only helps users who never fetched it.
- A service worker is a fourth cache with its own update rules (`0x:frontend-foundations`, `pwa-mobile.md`).
- Check after deploy: `curl -sS -D - -o /dev/null https://example.com/ | grep -iE 'cache-control|age|etag|cache'` and confirm `age` restarted and the HTML references the new asset hashes.

## Tag-based invalidation

Time-based expiry forces a trade between freshness and hit ratio. Tags remove it: cache for hours or days and purge exactly what changed, the moment it changes.

- The origin labels each response with the entities it was built from, in the header the CDN defines (`Surrogate-Key` on Fastly, `Cache-Tag` on Cloudflare; the header is consumed by the CDN and not sent to browsers). A product page carries `product-123 category-7 pricing`; a listing carries the tags of everything it shows plus one for the list itself.
- On write, purge the entity's tag. One call invalidates the detail page, every listing and every API response that included it.
- Purge after the transaction commits, from a retried job rather than inline, so a failed purge call is not a permanently stale page. With read replicas, a purge that arrives before the replica catches up lets the next request re-cache old data: read from the primary for the regeneration or delay the purge slightly.
- Prefer soft purge with `stale-while-revalidate` so no user waits on regeneration.
- Not every CDN or plan has tags, and headers have size limits. Without tags, fall back to versioned cache keys (a version number in the key, bumped on change) or path-prefix purges.
- Framework-level tags (Next.js `revalidateTag`) apply the same idea to the framework's data cache; when a CDN sits in front, both layers must be invalidated.

## Serving stale on purpose

```http
Cache-Control: public, max-age=60, stale-while-revalidate=600, stale-if-error=86400
```

- `stale-while-revalidate`: after `max-age`, serve the stored copy immediately and refresh in the background. Users never pay for regeneration, and a burst of requests for an expired entry does not stampede the origin.
- `stale-if-error`: if the origin fails (5xx or unreachable), keep serving the stored copy for the window. For public pages this converts an origin outage into slightly old content, which is the cheapest reliability feature available.
- The origin must fail honestly: an error page returned with 200 gets cached as content and defeats `stale-if-error`.
- Support differs by CDN and plan, and some implement serve-stale through their own settings instead of these directives. Verify by stopping the origin in staging and requesting a cached URL.
- `must-revalidate`, `proxy-revalidate` and `no-cache` forbid serving stale, and by the letter of the specification `s-maxage` does too for shared caches; CDNs differ in how literally they read this. Keep `must-revalidate` off responses that should survive an origin outage, and put the stale directives where the CDN documents reading them.
- Do not apply to personalized or sensitive responses, or to data whose staleness has a cost (prices at checkout, stock, permissions).

## Hit ratio

Read the cache status header on any response (`cf-cache-status`, `x-cache`, or the standard `Cache-Status`) together with `Age`: `HIT` with a growing `Age` is cached; `MISS` twice in a row is not being stored; `BYPASS` or `DYNAMIC` means a rule or header excluded it; `EXPIRED`/`REVALIDATED` means the lifetime is short.

Procedure: export the top URLs by count of non-hit requests from CDN analytics or logs, then classify each:

| Cause | Sign | Fix |
|---|---|---|
| Not cacheable by header | `private`, `no-store`, `Set-Cookie`, or no directive | Correct the header for content that is truly public; stop setting cookies on public pages |
| Key fragmentation | Same path, many query strings or `Vary` values | Normalize the key |
| Lifetime too short | Mostly `EXPIRED`/`REVALIDATED` | Longer CDN lifetime plus purge or tags |
| Long tail spread over many edge locations | Each URL rarely requested per location | Tiered caching or an origin shield, so edges fill from one upstream cache |
| Over-broad purging | Hit ratio collapses after each deploy | Purge by tag or path |

Track request hit ratio and byte hit ratio separately; the second drives egress cost. Rule of thumb: fingerprinted assets should sit above 95%; HTML depends on how much is personalized. A session cookie set on the first anonymous page view is the most common reason a marketing site caches nothing.

## Cache poisoning and cache deception

**Poisoning**: an attacker gets a harmful response stored under a key that ordinary users request. It works when a request input changes the response but is not part of the key.

- Typical unkeyed inputs: `X-Forwarded-Host`, `X-Forwarded-Scheme`, `X-Original-URL`, `X-HTTP-Method-Override`, and query parameters excluded from the key but still read by the app.
- Defenses: build absolute URLs and redirects from configuration, never from request headers; strip headers the app does not need at the edge; anything that legitimately varies the response goes into the key; reflect no request header into a cacheable response.
- Poisoned denial of service: a malformed or oversized header makes the origin return 400, and the CDN caches it for the clean URL. Do not cache error statuses from the origin beyond seconds.

**Deception**: the attacker tricks the cache into storing a victim's private page. They send a logged-in victim to `/account/profile.css` or `/account;x.js`. The origin's router ignores the suffix and returns the account page; the CDN sees a static-looking extension and stores it; the attacker fetches the same URL.

- Defenses: decide cacheability from the origin's `Cache-Control` and `Content-Type`, not from the URL extension; send `no-store` on every authenticated route so the mismatch cannot matter; make the router return 404 for unknown trailing segments; never deploy a cache-everything rule over paths that include authenticated routes; enable the CDN's deception protection where it exists.
- Path-normalization differences between the CDN and the origin (encoded slashes, dot segments, delimiters such as `;`) are the same bug in another form; normalize at the edge and reject what remains ambiguous.

Test: logged in, request a private path with `.css` appended and with `/x.js` appended. The response should be a 404, or carry `no-store` and a non-hit cache status; then confirm the same URL without cookies returns nothing private.

## Ask the user

- **How stale may each kind of public content be: seconds, minutes, an hour?** This sets every lifetime. Default: public pages may be up to a few minutes stale unless purged on change; prices, stock and permissions are never served stale.
- **Which pages differ by user, plan, locale, country or experiment?** Each such dimension must be bypassed or keyed. Default: anything behind login is `no-store` and uncached at the CDN.
- **Should the site stay up on old content when the origin is down?** Default: yes for public and marketing pages (`stale-if-error`), no for the logged-in app.
- **Is there a legal or contractual reason some content must disappear immediately** (takedowns, embargoes, deleted user content)? Decides whether tag purging is required at Launch. Default: purge by URL on delete and keep CDN lifetimes at an hour or less until tags exist.
- **Does the product run price or content experiments on cached pages?** Default: assign the bucket at the edge and key on it, or keep experimented pages uncached.
