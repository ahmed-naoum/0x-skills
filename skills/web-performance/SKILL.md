---
name: web-performance
description: Makes pages and endpoints fast and keeps them fast, covering Core Web Vitals, loading and delivery, JavaScript bundle size, images and fonts, runtime jank, backend latency and profiling, load testing and performance budgets. Use when the site feels slow, Lighthouse or LCP, INP or CLS scores are bad, the bundle is too big, an endpoint takes seconds, or a load test is needed before launch.
---

# Web performance

## Stance

Performance work is measurement first and removal second. An expert does not start from a list
of optimizations; they find the one stage where the time goes, for the users who are actually
slow, fix that, and prove it with the same measurement. Most slow sites have three or four
causes that account for nearly all of the delay, and they are usually cheap: a late-discovered
hero image, an oversized image, a third-party tag, an uncached HTML response, a query per row.

1. **Field data decides, lab data explains.** Pass or fail is judged at the 75th percentile of
   real users on phones. Lighthouse reproduces and verifies; its score is never the target,
   because it measures one synthetic visit and cannot measure INP.
2. **Find the slow stage before touching code.** Split LCP into its four parts, INP into its
   three phases, a slow request into its spans. Optimizing a stage that is not the bottleneck
   changes nothing and costs a day.
3. **Test on what users have.** Production build, throttled CPU and network, realistic data
   volume. A development laptop on fiber with twelve seeded rows hides every problem.
4. **Remove before optimizing.** Deleting a tag, a dependency, a font weight or a query is
   cheaper than tuning it and cannot regress.
5. **Fix the outermost layer that can solve it.** CDN before application cache, a correct
   query before a cache in front of it, server rendering before client-side tuning. Inner
   layers cost more to run and hide the cause.
6. **Waiting and working are different problems.** Backends are mostly waiting (queries,
   locks, pools, downstream calls); trace first, profile CPU only when a core is busy.
7. **Percentiles, not averages.** p75 for user-centric metrics, p95 and p99 per endpoint. The
   mean hides the users who leave.
8. **What is not enforced regresses.** A byte budget in CI and field monitoring with release
   markers are what keep a fix fixed. Start with deterministic checks; timing checks in CI are
   noisy.
9. **Stop at the target.** Past "good" the returns fall quickly. Say so, and return the time
   to product work unless own evidence shows more speed pays.

Follow the project's framework, host and tooling. The defaults below are for greenfield
choices and for when the user asks.

## Route

| If the task is… | Read |
|---|---|
| LCP, INP or CLS is failing; Lighthouse and field data disagree; set up real-user measurement; find who is slow or which release broke it | `references/core-web-vitals.md` |
| The page takes too long to appear; high TTFB; render-blocking resources; third-party scripts; which cache layer to use; back/forward or prerendered navigations | `references/loading-delivery.md` |
| The JavaScript bundle is too big; a dependency is heavy; code splitting; tree-shaking does not work; a bundle size check in CI; chat or video widgets | `references/javascript-bundles.md` |
| Images are heavy or the hero is slow; fonts flash or shift text; video delivery; icon fonts and SVG | `references/images-fonts.md` |
| Scrolling or typing is janky; clicks respond late; long lists are slow; profiling with DevTools; layout thrashing | `references/rendering-runtime.md` |
| An endpoint or server-rendered page takes seconds; find the slow query or call; p95 and p99 tracking; flame graphs; occasional very slow requests | `references/backend-latency.md` |
| How much traffic can it take; load-test before launch; k6 scripts; what breaks first; performance checks for endpoints in CI | `references/load-testing.md` |
| Audit the site and rank fixes; set targets; Lighthouse CI budgets; monitor and alert on field performance; report results | `references/performance-budgets.md` |

"The site feels slow" with no other detail: start with the audit procedure in
`references/performance-budgets.md`, then follow the failing metric.

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Pass criterion | LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at p75 on phones, from field data | Own conversion evidence justifies a stricter target on specific pages |
| Field measurement | `web-vitals` attribution build, beacons tagged with route template, release id, device class, country | Prototype: PageSpeed Insights and a lab run are enough |
| Lab profile | Mobile emulation, slow 4G, 4x CPU throttle, production build | Audience is verifiably desktop on good hardware |
| LCP element | Real `<img>` in server HTML, `fetchpriority="high"`, not lazy, dimensions set | LCP is text: work on TTFB, blocking CSS and fonts |
| Images | AVIF with WebP fallback through the framework loader or an image CDN; `srcset` with correct `sizes`; lazy below the fold | A handful of static images: build-time variants |
| Fonts | System stack for app UI; one self-hosted, subsetted variable WOFF2 via the framework font loader for brand pages | Brand requires more: two families at most |
| JavaScript | Server components by default, client boundary at the leaf, heavy widgets loaded on interaction | Highly interactive app screens carry more, behind login |
| Third parties | Loaded after load or on interaction, behind facades; none synchronous in the head | Consent, fraud and error tracking that must run early: async |
| Caching | HTML for anonymous pages at the CDN, fingerprinted assets immutable; application cache only after that | Per-user content: private cache or streamed fragment |
| Backend targets | p95 under 500 ms for page responses, 300 ms for interactive API calls; every outbound call has a timeout | The product sets its own per-route budget |
| Server latency tracking | Per-route duration histograms and a slow-query log | Prototype: skip |
| Load testing | Skip at Prototype; at Launch only for a dated spike or a contractual need; open-model k6 with step-and-hold | Scale: routine before peaks |
| CI enforcement | Byte budget on client JS as a hard fail; lab timings as warnings | Scale: Lighthouse CI on key templates, nightly endpoint checks |

By stage:

- **Prototype:** take the free wins (framework image and font components, server rendering, no
  synchronous third parties, pagination on lists). No budgets, no RUM, no load tests.
- **Launch:** field measurement with release markers, one audit with a ranked fix list, bundle
  budget in CI, per-route p95 and slow-query logging, query-count assertions on key endpoints.
- **Scale:** alerting on field regressions, lab budgets per template, scheduled load tests,
  experiments that tie speed to conversion, a named owner for third-party tags.

## Before you call it done

1. The problem was measured before the change and the same measurement was repeated after, with
   the same throttling, device profile and data.
2. The claim of improvement names its source: field (which tool, which segment, which window)
   or lab (which profile, how many runs). A single unthrottled local run is not evidence.
3. Profiling and lab runs used a production build.
4. The LCP element on phones was identified, is in the server HTML, is not lazy-loaded, and
   exactly one image on the page has high fetch priority.
5. Every image, video, iframe, embed and ad slot has reserved dimensions; a throttled reload
   shows no visible shift, including when the font arrives.
6. No synchronous third-party script is in the head; each remaining third party has a stated
   reason and a load strategy.
7. Below-the-fold images are lazy; nothing in the first viewport is.
8. Each font file is requested once, only faces in use are loaded, and text is visible
   immediately on a slow reload.
9. `"use client"` sits on leaf components; the shared chunk was checked in the analyzer for
   heavy or duplicate dependencies after the change.
10. A slow interaction was re-recorded under CPU throttling and its duration is within target;
    visible feedback appears in the first frame.
11. A slow endpoint has a before-and-after trace with production-sized data; independent calls
    run in parallel; the query count per request does not grow with result size; every outbound
    call has a timeout.
12. A cache that was added has a defined key, lifetime and invalidation, cannot serve one
    user's response to another, and the uncached path was measured too.
13. A load test used an arrival-rate model, held each level, checked response content, and
    reports the limiting resource and the rate at which the target stops holding.
14. Something now prevents the regression: a budget, an assertion, or an alert, with the
    threshold written down.
15. The user was told what was left undone and why, and when public field data (the 28-day
    window) will reflect the change.

## Not this skill

- Reading query plans, indexing and fixing a slow SQL query → `0x:postgres-database`
- Cache-Control headers, CDN configuration and HTTP/3 → `0x:web-networking`
- Adding a Redis application cache → `0x:data-stores`
- Rendering strategy, server components and hydration design → `0x:react-nextjs`
- Capacity planning, autoscaling and SLOs → `0x:site-reliability`
- Frame rate of three.js scenes → `0x:3dui`
