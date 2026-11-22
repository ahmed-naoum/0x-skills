# Loading and delivery

Read this when: a page takes too long to appear or to navigate, time to first byte is high,
third-party scripts are suspected, or it is unclear which caching layer would fix a slow page.

## Diagnose in this order

Read a waterfall (DevTools Network with throttling, or WebPageTest) top to bottom and stop at
the first stage that is slow. Later stages cannot be fixed while an earlier one dominates.

| Stage | Look at | Slow when (rule of thumb) | Go to |
|---|---|---|---|
| 1. Redirects and connection | Rows before the HTML document; DNS, connect, TLS bars | Any redirect on a landing URL; a slow handshake on a phone profile | TTFB section |
| 2. Server think time | "Waiting for server response" on the document | Over ~200 ms for cacheable pages, over ~600 ms for dynamic ones | TTFB section, `backend-latency.md` |
| 3. Critical path | Requests in `<head>` before first paint | Any sync script; CSS chains; fonts discovered from CSS | Critical path section |
| 4. LCP resource | When the hero request starts and ends | Starts late or is large | `core-web-vitals.md`, `images-fonts.md` |
| 5. Everything else | JS evaluation, third parties, below-the-fold media | Main thread busy for seconds after paint | Third parties, lazy loading, `javascript-bundles.md` |

Always throttle. An unthrottled desktop run on office fiber hides every problem in this file.

## Time to first byte

TTFB at p75 should be under 0.8 s in the field; that includes redirects, DNS, connection and
server time, so the server itself has far less. Break it down before fixing:

```bash
curl -s -o /dev/null -w 'dns %{time_namelookup}  connect %{time_connect}  tls %{time_appconnect}  ttfb %{time_starttransfer}  total %{time_total}\n' https://example.com/
```

Run it from a machine far from the origin as well. The `Server-Timing` response header exposes
server-side phases to DevTools and to RUM; add it for the slow routes
(`Server-Timing: db;dur=53, render;dur=20`).

| Cause | Symptom | Fix |
|---|---|---|
| Redirect chain | `http → https → www → /en` each costs a full round trip | One hop at most; link to the final URL in ads, emails and sitemaps; HSTS removes the http hop for returning visitors |
| HTML not cached at the edge | TTFB grows with distance from the origin | Cache the HTML at the CDN for anonymous visitors (static generation or a shared-cache lifetime with background revalidation). Headers belong to `0x:web-networking` |
| Whole page waits for the slowest query | TTFB equals the slowest data fetch | Stream: send the shell and `<head>` first, slow parts in Suspense boundaries. The browser starts CSS, fonts and the hero while the server works |
| Compute far from the database | Many small queries, each paying cross-region latency | Put the app in the database's region. Edge compute with a single-region database is slower for anything doing more than one query |
| Sequential origin calls | Session lookup, then user, then data, one after another | Parallelize and remove round trips (`backend-latency.md`) |
| Cold starts | First request after idle is slow, the rest are fine | Keep an instance warm, shrink the server bundle, or move the route off scale-to-zero |
| Personalization blocks caching | One cookie makes every page uncacheable | Cache the page shell for everyone; fetch the personal fragment separately or stream it |

Streaming caveats: the status code and headers are committed with the first byte, so a failure
after that cannot become a 404 or a redirect at the HTTP level; proxies or compression layers
that buffer cancel the benefit. Verify with `curl -N` that bytes arrive progressively.

`103 Early Hints` lets the server or CDN send preload and preconnect hints while the origin
still computes. Worth turning on where the host offers it as a setting; not worth building.

## Which caching layer fixes this page

Pick the outermost layer that can hold the response correctly. Each layer inward costs more to
run and saves less.

| Situation | Layer | Why |
|---|---|---|
| Fingerprinted assets (JS, CSS, fonts, images with a hash in the name) | Browser plus CDN, immutable, one year | Never changes under that URL |
| Same HTML for every anonymous visitor (marketing, docs, blog, product pages) | CDN, with revalidation or on-demand purge | Removes the origin from the path entirely |
| Same data for all users, changes on a known event | Framework data cache or CDN with tag-based invalidation | Invalidate on the write, not on a timer |
| Same for one user across requests | Browser private cache, or client-side query cache | Must not land in a shared cache |
| Expensive computation, shared, tolerates staleness | Application cache (in-process for one instance, Redis for several) | See `0x:data-stores` before adding Redis |
| Slow aggregate over large tables | Precomputed table or materialized view | Caching a 5 s query still serves a 5 s miss (`backend-latency.md`) |
| Slow single query | Fix the query or the index first | A cache in front of a missing index hides it until the cache is cold (`0x:postgres-database`) |

Decision rules:

- Ask first "who may see this response, and how stale may it be". If the answer is "everyone,
  one minute", it is a CDN problem and no application code is needed.
- Cache hit ratio decides the win. A cache keyed too finely (per user, per query string with
  tracking parameters) has a hit ratio near zero. Strip marketing parameters from cache keys.
- A cache needs an invalidation story before it ships. "Short lifetime plus serve stale while
  revalidating" is the story with the fewest bugs.
- Never let a response that depends on a cookie or `Authorization` header be stored in a shared
  cache without that dependence in the key; the failure is one user seeing another's page.
- Measure the miss path too. Users on a cold cache, after a deploy or a purge, get the uncached
  time; if that is 8 s, the cache is hiding an outage.

Header syntax, CDN setup and purge mechanics: `0x:web-networking`. Framework cache semantics:
`0x:react-nextjs`.

## Critical path: what blocks the first paint

Stylesheets in `<head>` block rendering. Scripts without `defer`, `async` or `type="module"`
block parsing as well. Everything else does not block.

| Resource | Rule |
|---|---|
| Own scripts | `defer` (ordered, runs after parsing) or `type="module"` (deferred by default). Frameworks do this already; check hand-added tags |
| Independent third-party scripts | `async`, or injected after load. Never sync in `<head>` |
| CSS | One small file for the route. With utility CSS the whole sheet is usually small enough that inlining "critical CSS" is not worth the machinery |
| `@import` inside CSS | Remove: each import is discovered only after its parent downloads, forming a chain |
| CSS for print or wide screens | `media` attribute so it loads at low priority without blocking |
| Fonts | Discovered only after CSS is parsed; preload the one or two used above the fold (`images-fonts.md`) |
| Inline scripts after a stylesheet | Block until that stylesheet has loaded; keep inline scripts above stylesheets or make them unnecessary |

Numbers: the first response round trip carries roughly 14 KB compressed (the initial TCP
congestion window), so an HTML document whose `<head>` and above-the-fold markup fit in that
budget can start rendering after one round trip. It is a rule of thumb, not a cliff.

Check: Lighthouse lists render-blocking resources; the DevTools Coverage tab shows how much of
each CSS and JS file went unused during load. Over half unused in a blocking file means it
should be split or deferred.

A/B testing snippets that hide the page until the experiment loads ("anti-flicker") add their
timeout directly to LCP for every visitor. Run experiments on the server, or accept flicker on
the tested element only.

## Third-party scripts

Third parties are usually the largest main-thread cost on a marketing site and nobody on the
team wrote them. Audit with numbers, then negotiate.

1. Inventory: list every third-party origin in the waterfall, including those injected by the
   tag manager (they are in no repository).
2. Cost each one: transfer size, main-thread time (the Performance panel groups time by third
   party; Lighthouse has a third-party summary), and whether it blocks rendering.
3. Measure the counterfactual: block the domain with DevTools request blocking and rerun. The
   difference in LCP and Total Blocking Time is that vendor's price.
4. Decide per script:

| Verdict | When | How |
|---|---|---|
| Remove | Nobody reads its data, or two tools do the same job | Delete; the cheapest fix there is |
| Delay until idle or after load | Analytics, heatmaps, most pixels | Load after the `load` event or on idle; in Next.js, `next/script` with `strategy="lazyOnload"` |
| Delay until interaction | Chat widgets, video players, maps, share buttons | Facade: a static placeholder that loads the real thing on click or hover (`javascript-bundles.md`) |
| Load on the pages that need it | Payment SDKs, captcha, editors | Only on checkout, signup and so on, not in the root layout |
| Self-host or proxy | Small, stable scripts and fonts | Saves a connection; lose automatic updates |
| Keep, load async | Consent manager, error tracker, fraud signals needed early | `async`, preconnect to its origin |

Traps: a tag manager lets non-engineers add sync scripts to production, so agree on a review
rule; consent banners are often the LCP element and a CLS source, so render their space
server-side; a "small" vendor snippet commonly loads a much larger second script.

## Resource hints

| Hint | Use for | Limit |
|---|---|---|
| `preconnect` | An origin certain to be used within the first seconds: font host, image CDN, API | Two to four origins. Each holds a socket open and costs TLS work; unused ones are waste |
| `dns-prefetch` | Origins likely but not certain | Cheap; fallback for the above |
| `preload` | A late-discovered resource needed for first paint: font, hero in CSS, critical chunk | Must set `as`; a wrong `as` or missing `crossorigin` double-downloads. Console warns when unused within a few seconds |
| `modulepreload` | ES module chunks needed immediately | Framework usually emits these |
| `prefetch` | A resource for the likely next navigation | Low priority; wasted bytes if the guess is wrong |
| `fetchpriority` | Reordering among already-discovered resources | `high` on the LCP image, `low` on carousel slides and non-critical fetches |

```html
<link rel="preconnect" href="https://cdn.example.com">
<link rel="preconnect" href="https://fonts.example.com" crossorigin>
```

`crossorigin` is required when the later request is a CORS request (fonts always are);
otherwise the browser opens a second connection and the hint is wasted. Every preload competes
with everything else: preloading five things means prioritizing nothing. Serving assets from
the page's own origin removes the need for most hints.

## Lazy-load and defer what is not needed yet

- Images and iframes below the fold: `loading="lazy"`. Never on anything in the first viewport;
  it delays LCP. For the first screen of a list, load eagerly the first few items and lazy-load
  the rest.
- Heavy components not visible at load (modals, editors, charts lower on the page, comment
  sections): dynamic `import()` triggered by visibility (IntersectionObserver) or by intent
  (hover, focus, click).
- Non-urgent work after load (analytics init, prefetching, warming caches): `requestIdleCallback`
  where available with a `setTimeout` fallback.
- Long pages: `content-visibility: auto` skips rendering work for off-screen sections
  (`rendering-runtime.md`).
- Reserve dimensions for everything lazy, or the deferred load becomes a layout shift.
- Lazy-loaded content must still be reachable: links and text needed for search and for
  no-JS readers belong in the HTML.

## Slow radios and battery

On mobile data, each burst of network activity wakes the radio and keeps it at high power for
seconds afterwards; latency per round trip is high and variable. What follows:

- Fewer round trips beat fewer bytes. Remove redirects, extra origins, request chains (CSS that
  loads CSS, JS that fetches config that fetches data).
- Batch background traffic: one beacon on page hide instead of an event per interaction; no
  polling at short intervals, use push or back off when the tab is hidden
  (`document.visibilityState`).
- Compress text with Brotli or Zstandard at the CDN; check that JSON API responses are
  compressed, they are often missed.
- Honor `Save-Data` (request header, `navigator.connection.saveData` in Chromium): skip
  autoplay video, heavy hero media and prefetching.
- Do not over-split: hundreds of tiny chunks compress worse and add per-request overhead even
  on HTTP/2 and HTTP/3. Aim for tens of requests on first load, not hundreds.
- Prefetching and prerendering spend the user's data and battery on guesses; restrict them to
  likely navigations and disable them under `Save-Data`.

## Instant navigations

**Back/forward cache (bfcache).** The browser keeps the whole page in memory and restores it
instantly on back and forward, a large share of navigations on content and shopping sites.
Pages lose eligibility through:

- An `unload` event listener, often added by an old third-party script. Use `pagehide` instead;
  `Permissions-Policy: unload=()` blocks it for all scripts in supporting browsers.
- `Cache-Control: no-store` on the document. Most browsers refuse to keep such a page; Chrome
  has started to allow it in limited cases. Use `no-store` only on pages with sensitive data.
- Open connections or locks at the moment of leaving. The rules differ by browser and have
  been loosening (Chrome has moved toward closing a WebSocket on entry instead of refusing the
  page), so close WebSockets and finish IndexedDB transactions in `pagehide` and test.

Check in Chrome DevTools: Application panel, Back/forward cache, "Test back/forward cache",
which lists the blocking reasons. After a restore the page's JS state is exactly as it was
left, which is a privacy problem as well as a staleness one: after sign-out, Back can show the
previous user's page. In a `pageshow` handler, when `event.persisted` is true, re-check the
session and reload if it changed, and refresh stale state such as the cart count. In RUM,
bfcache restores appear as navigation type `back-forward-cache`.

Stage: checking bfcache eligibility is a free win at Launch. Speculation rules come after the
basics pass, for content and commerce sites with ordinary link navigation.

**Speculation rules** (Chromium at the time of writing; browsers without support ignore the
script, so it is safe as progressive enhancement) let the browser prefetch or fully prerender
likely next pages of a multi-page site:

```html
<script type="speculationrules">
{ "prerender": [{ "where": { "and": [ { "href_matches": "/*" },
    { "not": { "href_matches": "/logout" } }, { "not": { "href_matches": "/cart/*" } } ] },
  "eagerness": "moderate" }] }
</script>
```

- `moderate` waits for a sign of intent: on desktop a short hover or pointer-down, which wastes
  little; on phones, where nothing hovers, Chrome uses viewport-based heuristics and speculates
  more often. `eager` and `immediate` do not wait for intent and are for one or two
  near-certain next pages. The exact triggers have changed between Chrome versions; read the
  current documentation before tuning. The browser caps concurrent speculations.
- A Content-Security-Policy that restricts inline scripts blocks the rules unless `script-src`
  allows them (a nonce, or the `'inline-speculation-rules'` source). The only symptom is a
  console message.
- Exclude every URL where a GET has side effects (logout, add-to-cart links, one-time tokens).
  GET requests should not have side effects at all; prerendering exposes the ones that do.
- Prerendered pages run their scripts before the user sees them. Analytics must wait for
  activation (`document.prerendering` and the `prerenderingchange` event) or page views inflate;
  major analytics tools handle this, custom code does not.
- Server load rises with speculation; the requests carry a `Sec-Purpose` header for accounting.
- In a Next.js App Router app, `<Link>` already prefetches a route when the link enters the
  viewport (production builds only; not in `next dev`), so speculation rules matter for
  classic multi-page sites and for links into the app from a marketing site.

## Ask the user

- **How stale may each page be?** Decides whether HTML can live on the CDN. Default: marketing
  and content pages up to a few minutes with purge on publish; anything showing account data
  never shared-cached.
- **Which third-party tools are still in use, and who owns each?** Removal needs a business
  owner's agreement. Default: present measured cost per vendor and propose deferral, not
  removal, for anything with an owner.
- **Where are the users?** Decides region placement and whether edge caching of HTML is worth
  the invalidation work. Default: one region next to the database, CDN in front.
- **Is prerendering acceptable given data use and server cost?** Default: `moderate` eagerness
  on content pages, none on authenticated or transactional pages.
