# Core Web Vitals

Read this when: LCP, INP or CLS needs measuring or fixing, a Lighthouse score and the field data
disagree, or a field regression has to be traced to its cause.

## The numbers

| Metric | Good | Poor | What it times |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2.5 s | > 4.0 s | Navigation start to paint of the largest image or text block in the viewport |
| INP (Interaction to Next Paint) | ≤ 200 ms | > 500 ms | Input (click, tap, key press) to the next frame painted, near-worst interaction of the visit |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | > 0.25 | Largest burst of unexpected layout shifts (unitless) |
| TTFB (diagnostic, not a Core Web Vital) | ≤ 0.8 s | > 1.8 s | Navigation start to first response byte |

A page passes when the **75th percentile** of real page views is in "good", judged separately for
phone and desktop. Phone is almost always the failing one; design and test against it.

Details that change the diagnosis:

- LCP candidates are images, video posters, CSS background images and text blocks. Reporting
  stops at the first user input or scroll. An element removed from the DOM stays a candidate.
- INP ignores scrolling and hover. It covers the whole visit, not the load, so a page that loads
  fast and has one slow menu fails.
- CLS groups shifts into windows (shifts less than 1 s apart, window at most 5 s) and reports the
  worst window. Shifts within 500 ms of a discrete user input are excluded, so an accordion
  opening is fine but a click that inserts content 800 ms later, after a fetch, counts.
  Movement done with `transform` is not a shift at all.
- Client-side route changes are not page loads: in a single-page or App Router app the whole
  visit is attached to the URL of the last full navigation. Chromium has begun measuring these
  "soft navigations" and current `web-vitals` can report them (`reportSoftNavs`); keep that
  data separate from the pass criterion until the public sources adopt it.

## Lab and field are different instruments

| | Lab (Lighthouse, WebPageTest, DevTools) | Field (CrUX, own RUM) |
|---|---|---|
| Answers | Why is it slow; did this change help | Is it slow for real users; who; since when |
| INP | Not measured on load. Total Blocking Time is a proxy only | Measured |
| CLS | Load only, no scrolling | Whole visit |
| LCP | One device, one network, cold cache, no cookie banner state | Real mix, including cached and bfcache visits |

Rules that follow:

1. Decide pass or fail from field data. Use the lab to reproduce and to verify a fix.
2. Disagreement is normal in both directions. Good lab, failing field: consent banners,
   logged-in states, personalization, ads and slow phones do not exist in the lab run. Bad lab,
   passing field: warm caches and a desktop-heavy audience; do not spend a week on it.
3. Lighthouse mobile simulates a slow 4G link and a 4x CPU slowdown. Its performance score is a
   weighted blend whose weights change between versions; never set the score as the target.

### Field sources

- **CrUX** (Chrome User Experience Report): opted-in Chrome users only (no iOS browsers, Chrome
  on iOS included), 28-day rolling window, only for origins and URLs with enough traffic. Read it through PageSpeed Insights, Search
  Console's Core Web Vitals report, or the CrUX API. It is what Google Search uses. A new or small
  site has no CrUX data: that is not a failure, it means own RUM is the only field source.
- **Own RUM**: the `web-vitals` library, sending to the analytics or telemetry tool already in
  the project. Needed at Launch because CrUX cannot say which element, which script, which release.

```ts
// app/web-vitals.ts, loaded from a client component in the root layout
import { onCLS, onINP, onLCP, onTTFB, type MetricWithAttribution } from 'web-vitals/attribution';

// Send the fields that diagnose; the full attribution object holds raw performance entries.
function debug(m: MetricWithAttribution) {
  switch (m.name) {
    case 'LCP': { const a = m.attribution; return { target: a.target, url: a.url,
      ttfb: a.timeToFirstByte, loadDelay: a.resourceLoadDelay,
      loadDuration: a.resourceLoadDuration, renderDelay: a.elementRenderDelay }; }
    case 'INP': { const a = m.attribution; return { target: a.interactionTarget,
      type: a.interactionType, loadState: a.loadState, inputDelay: a.inputDelay,
      processing: a.processingDuration, presentation: a.presentationDelay }; }
    case 'CLS': return { target: m.attribution.largestShiftTarget, loadState: m.attribution.loadState };
    default: return {};
  }
}
function send(m: MetricWithAttribution) {
  navigator.sendBeacon('/rum', JSON.stringify({
    name: m.name, value: m.value, rating: m.rating, id: m.id,
    navigationType: m.navigationType,        // navigate, reload, back-forward-cache, prerender…
    path: location.pathname,                 // map to the route template on the server
    release: process.env.NEXT_PUBLIC_RELEASE, ...debug(m),
  }));
}
onLCP(send); onINP(send); onCLS(send); onTTFB(send);
```

Attribution fields have been renamed between `web-vitals` majors (the LCP selector was `element`
before `target`); typing the callback as above makes the compiler check the installed version.

Rules for the collector:

- Import from `web-vitals/attribution`, not the plain build; the extra bytes buy the diagnosis.
- The beacon endpoint accepts anonymous writes from the internet: validate the body against a
  schema, cap its size, rate-limit it, and use the values for statistics only.
- INP and CLS are final only when the page is hidden. The library reports then; `sendBeacon`
  (or `fetch` with `keepalive: true`) is what survives the unload. Do not batch on a timer and
  expect the last values to arrive.
- Store the route **template** (`/product/[id]`), not the raw URL, plus release id, device class
  and country. Without these dimensions the data cannot answer any later question.
- Aggregate as p75 per metric per template. Never average percentiles across segments; recompute
  from raw values or histograms.
- Browser coverage differs by metric. At the time of writing LCP and INP are measurable in
  Chromium, Firefox and recent Safari, CLS only in Chromium (the library's README lists current
  support). Own RUM has no CLS from iOS and CrUX has nothing from iOS: no data is not "fine".
- Next.js exposes `useReportWebVitals` from `next/web-vitals`. It reports plain values;
  attribution is off unless enabled per metric through the experimental `webVitalsAttribution`
  config option. Use it for a quick start, the library directly once a metric fails.
- Sampling: at Launch volumes send everything. Sample only when the bill says so, and then
  sample by session, not by event.

## LCP: find which of four parts is slow

LCP = TTFB + resource load delay + resource load duration + element render delay. The
attribution build reports each (`timeToFirstByte`, `resourceLoadDelay`, `resourceLoadDuration`,
`elementRenderDelay`) and the element. Fix the largest part; optimizing the image when the
delay is the problem changes nothing.

| Largest part | Typical cause | Fix |
|---|---|---|
| TTFB | Slow origin, redirects, no CDN for HTML | See `loading-delivery.md` and `backend-latency.md` |
| Load delay (browser learned about the image late) | Image set by client JS, CSS background, `loading="lazy"`, carousel hydrated later, low priority behind other requests | Put a real `<img>` in server-rendered HTML; `fetchpriority="high"`; preload if it must stay in CSS |
| Load duration | File too large, wrong size for the viewport, slow image host, new connection to another origin | Responsive AVIF or WebP, same origin or preconnect (see `images-fonts.md`) |
| Render delay | Render-blocking CSS or sync script, element hidden until hydration, font block period for a text LCP, A/B anti-flicker snippet | Unblock the head, render visible on the server, `font-display: swap` or `optional` |

A healthy split, as a rule of thumb: TTFB and load duration take roughly 40% each, the two
delays under 10% each. Large load delay is the most common finding and the cheapest to fix.

The order of fixes that works:

1. Make the LCP element exist in the initial HTML. If it is client-rendered (a hero inside a
   component that fetches on mount, a slider library, an image whose `src` is set by script), no
   hint rescues it. Server-render it.
2. Make it discoverable by the preload scanner: `<img src>` or `<img srcset>` in markup.
3. Raise its priority and remove laziness:

```html
<img src="/hero-1200.avif" srcset="/hero-800.avif 800w, /hero-1200.avif 1200w, /hero-2000.avif 2000w"
     sizes="100vw" width="1200" height="600" alt="…" fetchpriority="high">
```

4. Only when the image cannot be in markup (CSS background, late component), preload it:

```html
<link rel="preload" as="image" href="/hero-1200.avif" fetchpriority="high"
      imagesrcset="/hero-800.avif 800w, /hero-1200.avif 1200w" imagesizes="100vw">
```

Traps:

- `fetchpriority="high"` on more than one or two images cancels itself out. Mark exactly the LCP
  candidate. In a carousel, the first slide only.
- A preload that does not match the request actually made (different URL, missing
  `imagesrcset`, wrong `crossorigin`) downloads the file twice.
- The LCP element differs by viewport. On phones it is often a heading or a cookie banner, not
  the hero image. Read the element selector in the LCP attribution (`target` in current
  library majors, `element` in older ones) from field data before optimizing.
- With `next/image` the hero prop depends on the version: `priority` through Next.js 15; from
  16 it is deprecated in favor of `fetchPriority="high"` with `loading="eager"`, or `preload`
  when the request must start from the `<head>` (the docs say not to combine it with the others).
- When LCP is text, the levers are TTFB, blocking CSS and fonts, not images.

## CLS: reserve the space before the content arrives

| Source of shift | Fix |
|---|---|
| Images and video without dimensions | `width` and `height` attributes on every `<img>` and `<video>` (the browser derives the aspect ratio), or CSS `aspect-ratio` on the container |
| Web font swap changes text metrics | Metric-matched fallback font or `font-display: optional` (see `images-fonts.md`) |
| Embeds, ads, iframes, maps | Fixed-size container with `min-height` or `aspect-ratio`; pick the most common ad size; never collapse the slot when empty |
| Content injected above existing content (banners, consent bars, "new version" notices) | Overlay with `position: fixed` or `sticky`, or reserve the slot in the server HTML |
| Client-only state changing layout after hydration (auth-dependent header, saved theme, personalized block) | Render the final layout on the server from the cookie; otherwise a skeleton of identical size |
| Skeleton differs in height from real content | Match dimensions; a skeleton that shifts is worse than none |
| Animating `top`, `left`, `height`, `margin` | Animate `transform` and `opacity` |

Field CLS is usually worse than lab CLS because it includes scrolling: lazy-loaded images
without dimensions, infinite-scroll inserts and late ad refreshes. Use
`attribution.largestShiftTarget` and `loadState` to tell load-time shifts from post-load ones.
In DevTools, the Performance panel's layout-shift track shows each shift and the nodes that moved.

## INP: three phases, three different fixes

INP = input delay + processing duration + presentation delay. The attribution build reports the
three plus `interactionTarget`, `interactionType` and `loadState`.

| Dominant phase | Meaning | Fix |
|---|---|---|
| Input delay | Main thread was busy when the user acted: hydration, third-party script, a timer, another handler | Ship and run less JS during load; break up long tasks; defer third parties. If `loadState` is `loading` or `dom-interactive`, it is a load problem |
| Processing duration | The event handlers themselves are slow | Do the visible update first, yield, then the rest; move heavy work off the handler |
| Presentation delay | Rendering after the handlers is slow: big DOM, expensive style and layout, large React commit | Smaller DOM, `content-visibility`, fewer re-rendered components (see `rendering-runtime.md`) |

The core technique is to yield: paint the response to the input before doing work the user does
not see.

```ts
const yieldToMain = (): Promise<void> =>
  (globalThis as any).scheduler?.yield?.() ?? new Promise((r) => setTimeout(r, 0));

async function onAddToCart() {
  setPending(true);              // visible feedback, cheap
  await yieldToMain();           // let the browser paint it
  recalculateCartTotals();       // heavy
  await yieldToMain();
  trackAnalytics();              // not user-visible, last
}
```

- `scheduler.yield()` continues ahead of other queued tasks; `setTimeout` goes to the back of
  the queue. Feature-detect, as above, because support is not universal.
- In loops over large collections, yield on a time budget (every ~50 ms of work), not every
  iteration: each yield costs.
- In React, wrap non-urgent state updates in `startTransition` or read them through
  `useDeferredValue`; the urgent update (the input value, the pressed state) renders first.
- Analytics and tag-manager handlers attached to every click are a frequent cause. Move them
  behind a yield or `requestIdleCallback` with a `setTimeout` fallback.

### Attribution with Long Animation Frames

The Long Animation Frames API (LoAF, Chromium) reports each frame that took over 50 ms and
which scripts ran in it. It is the tool that names the guilty script in the field, where the
profiler cannot go. The web-vitals INP attribution includes the overlapping entries
(`longAnimationFrameEntries`); to observe directly:

```ts
new PerformanceObserver((list) => {
  for (const f of list.getEntries() as any[]) {
    for (const s of f.scripts) {
      report({ frame: f.duration, blocking: f.blockingDuration, script: s.sourceURL,
               fn: s.sourceFunctionName, invoker: s.invoker, type: s.invokerType,
               ms: s.duration, forcedLayout: s.forcedStyleAndLayoutDuration });
    }
  }
}).observe({ type: 'long-animation-frame', buffered: true });
```

Reading it:

- Group by `sourceURL` host: own bundle versus each third party. This is the evidence needed to
  remove or defer a vendor tag.
- `invokerType` separates event listeners, timers, promise resolutions and script evaluation.
  Slow `classic-script` or `module-script` evaluation during load points at bundle size.
- High `forcedStyleAndLayoutDuration` means layout thrashing inside that script.
- Frame time not covered by any script is rendering work: style, layout, paint.
- Cross-origin scripts loaded without CORS expose little detail. Scripts need source maps on the
  collector side for function names to mean anything.

## Segment to find who is slow

p75 over everyone hides the failing group. Cut the same metric by:

| Dimension | How to get it | What it reveals |
|---|---|---|
| Page template | Route pattern | One template usually carries the failure |
| Device class | `navigator.deviceMemory`, `hardwareConcurrency` (coarse, not everywhere), viewport, UA platform | INP failing only on low-memory Android means too much JS, not network |
| Connection | `navigator.connection.effectiveType` (Chromium only), TTFB as a proxy | LCP failing only on slow links means bytes and round trips |
| Country or region | CDN or host geo header on the beacon request | High TTFB far from the origin means missing edge caching or one region |
| Navigation type | `metric.navigationType` | Back-forward-cache and prerender hits are near-instant; a low share means lost wins |
| Logged-in state, experiment variant, consent state | Own flags | Personalization and banners are common hidden causes |

Then decide by reach: a segment that is 3% of sessions and not in the target market is a note,
not a project. A segment that is 30% of paying traffic is the project.

## Trace a regression to the release

CrUX moves slowly: a change takes up to 28 days to show fully, and a Search Console "issue
started" date lags the cause by days to weeks. Work backward with faster evidence.

1. Confirm it is real and not traffic mix: compare the same segment (phone, same country, same
   template) before and after. A campaign that brings slower devices worsens p75 with no code
   change.
2. Find the date in own RUM split by release id, where the step is visible within hours. If
   there is no RUM, use the CrUX History API (weekly points) and treat the first worsened week
   as "cause was up to four weeks earlier".
3. List what changed around that date, including what is not in git: tag manager edits, a new
   chat or A/B tool, consent banner changes, CDN or image service settings, a font change, an
   ad network update, a framework upgrade.
4. Identify the metric part that moved (LCP subpart, INP phase, CLS target element). That
   usually points to one item on the list.
5. Reproduce in the lab: run the old and new build under identical throttling, or block the
   suspect third-party domain in DevTools request blocking and compare.
6. Fix or revert, then watch RUM for the release that carries the fix. Report the CrUX recovery
   only after the 28-day window has turned over. Keep a dated log of third-party tag changes
   so the next regression starts at step 4.

## Ask the user

- **Which pages matter?** Fixing every template is rarely worth it. Default: the top landing
  pages by entrances plus the signup and checkout path.
- **Who is the audience?** Device and country mix decides whether mid-range Android on mobile
  data is the target. Default: yes, test at that level.
- **Can third-party tags be removed or delayed?** Marketing often owns them, and they are often
  the largest INP cost. Default: propose deferring until after first interaction or idle, with the
  measured cost of each.
- **Is field data allowed to be collected?** A RUM beacon with no cookies and no user id is
  usually low-risk, but consent rules vary; see `0x:privacy-compliance`. Default: collect metric
  values, route template, release and coarse device class only.
- **Does search ranking drive the work, or conversion?** Passing "good" is enough for search;
  conversion may justify going further on specific pages. Default: reach "good" at p75 on
  phones, then stop unless own data shows more is worth it.
