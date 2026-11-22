# Performance budgets and audits

Read this when: auditing a site's performance, deciding what to fix first, setting targets,
adding performance checks to CI, monitoring field performance, or reporting results.

## Audit procedure

An audit produces a ranked list of fixes with expected effect, not a list of everything a tool
flagged. Work from field to lab, from outside in.

1. **Field data first.** PageSpeed Insights for the origin and the key URLs (shows CrUX at p75,
   phone and desktop), Search Console's Core Web Vitals report for URL groups, and own RUM if
   present. Note which metric fails, on which form factor, on which templates. If there is no
   field data (new or low-traffic site), say so and treat lab results as estimates.
2. **Pick the pages.** One URL per template, chosen by traffic and business role: top landing
   pages, the product or content template, signup, checkout, the main app screen. Five to eight
   URLs cover most sites.
3. **Lab runs under mobile throttling.** Lighthouse (mobile profile) or WebPageTest, several
   runs each, median taken. Record LCP and its element, CLS and the shifting elements, Total
   Blocking Time, TTFB, transfer sizes by type, request count, third-party share.
4. **Explain each failing number.** Waterfall for load problems, LCP subparts, Coverage tab for
   unused JS and CSS, bundle analyzer for composition, the Performance panel for interaction
   problems, traces for slow server responses. Each finding gets a cause, not a tool message.
5. **Check the multipliers.** Things that affect every page: caching and compression headers,
   HTML cacheability at the CDN, redirects, the shared JS chunk, fonts, tag manager contents,
   bfcache eligibility.
6. **Rank and write up.**

Rank by effect on users reached, divided by effort:

| Column | How to fill it |
|---|---|
| Finding | Cause, in one line: "hero image is client-rendered and lazy-loaded" |
| Evidence | The measurement: "LCP load delay 1.9 s of 3.8 s on phones, home and category templates" |
| Reach | Share of sessions or revenue passing through the affected templates |
| Expected effect | Which metric, roughly how much, with stated confidence |
| Effort | Hours or days, and who else is needed (marketing for tags, design for fonts) |
| Risk | What could break: layout, tracking, SEO |

Typical order on a site never audited before, as a rule of thumb: LCP resource priority and
discovery; oversized images; render-blocking and third-party scripts; HTML caching and TTFB;
font loading; layout-shift sources; shared JS weight; then interaction cost. The first items
are hours of work each and usually move the field numbers more than everything after them.

Do not put in the list: Lighthouse opportunities with negligible savings, micro-optimizations
on pages nobody visits, or rewrites ("migrate the framework") when configuration fixes are
still undone.

## Targets tied to the business

A target needs a metric, a percentile, a segment and a reason.

- **Floor:** Core Web Vitals "good" at p75 on phones for the top templates (LCP ≤ 2.5 s, INP
  ≤ 200 ms, CLS ≤ 0.1). It is the threshold search uses and a defensible default.
- **Server:** p95 response time per critical route (`backend-latency.md`).
- **Beyond the floor only with evidence** that it pays. Do not quote industry statistics of the
  "100 ms equals 1% revenue" kind as if they applied to this product; they come from other
  sites, other years and other audiences.

Getting own evidence, in increasing strength:

1. **Correlate.** Join RUM metrics to sessions and compare conversion (signup, purchase,
   activation) across LCP or INP buckets. Useful to see where the drop-off steepens, but
   confounded: users on slow devices and networks differ in income, intent and country. Segment
   within device class and country before believing the slope.
2. **Before and after.** Ship a real improvement and compare the same segment over equal
   windows. Still exposed to seasonality and campaigns.
3. **Experiment.** Serve the faster version to a random half, or (where acceptable) add an
   artificial delay to a small share of traffic. The only method that gives a causal number;
   worth it at Scale, rarely before. Method is in `0x:product-analytics`.

Where speed most plausibly pays: landing pages receiving paid traffic (every bounce was paid
for), checkout and signup steps, search and filtering in commerce, the first screen of the app
after login, anything used many times a day. Where it does not: settings pages, admin tools,
pages behind a committed workflow.

Write targets as a short table kept in the repository:

| Scope | Metric | Target | Source |
|---|---|---|---|
| Landing and product templates, phones | LCP p75 | ≤ 2.5 s | RUM, CrUX |
| All templates, phones | INP p75 | ≤ 200 ms | RUM, CrUX |
| All templates | CLS p75 | ≤ 0.1 | RUM, CrUX |
| Landing route | JS transferred on first load | ≤ agreed kB | CI |
| Checkout API | p95 latency | ≤ agreed ms | APM |

## Budgets in CI with lab tests

A budget is a target enforced before merge. Three kinds, with different reliability:

| Kind | Examples | Variance | CI role |
|---|---|---|---|
| Quantity | JS, CSS, image and font bytes; request count; third-party count | None | Hard fail |
| Rule | Specific audits pass: images have dimensions, no render-blocking resources, text compression on | Low | Hard fail on a chosen few |
| Timing | LCP, Total Blocking Time, CLS in a lab run | High on shared runners | Warn, or fail only on large regressions over several runs |

Start with quantity budgets (`javascript-bundles.md` for bundle size). Add Lighthouse CI when
the site is at Launch and regressions have actually happened.

```json
{
  "ci": {
    "collect": {
      "startServerCommand": "pnpm start",
      "url": ["http://localhost:3000/", "http://localhost:3000/pricing"],
      "numberOfRuns": 5
    },
    "assert": {
      "assertions": {
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "resource-summary:script:size": ["error", { "maxNumericValue": 350000 }],
        "total-blocking-time": ["warn", { "maxNumericValue": 300 }],
        "largest-contentful-paint": ["warn", { "maxNumericValue": 3000 }]
      }
    },
    "upload": { "target": "temporary-public-storage" }
  }
}
```

Save as `lighthouserc.json`, build the app, then run `npx @lhci/cli autorun` in the workflow.
`temporary-public-storage` uploads reports to a public URL; use `filesystem` or a private
server for anything not meant to be public.

Rules:

- Test a production build served locally or a preview deployment, never the dev server.
- Several runs per URL. Check which run the assertion uses by default (the aggregation method
  is configurable per assertion) and make it the median for timing metrics.
- Lab numbers in CI are not field numbers. A CI runner is not a phone; set thresholds from a
  week of observed CI results plus margin, not from the Core Web Vitals thresholds.
- Assert on metrics, not on the performance score: the score's weights change between
  Lighthouse versions and a version bump would fail the build for no code reason. Pin the
  Lighthouse version for the same reason.
- Few URLs (three to five templates). Every added URL adds minutes and flake.
- Lab runs do not measure INP. Total Blocking Time is the available proxy for main-thread load
  during startup; interaction regressions need field monitoring or a scripted user flow.
- Pages behind login need a scripted session (Lighthouse user flows through Puppeteer, or a
  test-only auth cookie). Skip until the public pages are covered.
- When a budget fails, the options are fix, or raise the budget in the same pull request with
  a stated reason. Silent bypasses end the practice.

## Continuous field monitoring and alerting

Lab checks catch what the pipeline can see. Third-party tags, content changes, CDN settings and
traffic shifts are only visible in the field.

Minimum from Launch:

- RUM beacons for LCP, INP, CLS and TTFB with route template, release id, device class and
  country (`core-web-vitals.md`), in the analytics or telemetry tool already in use.
- A dashboard: p75 per metric per template for phones, as a time series with release markers,
  plus the share of page views rated good, needs-improvement and poor.
- Server-side: p95 per route.

Alerting, rules of thumb to tune against observed noise:

| Signal | Condition | Why this shape |
|---|---|---|
| p75 of a metric on a key template | Worse than the trailing seven-day value for the same weekday by more than about 15%, sustained for several hours | Daily and weekly cycles in device mix make fixed thresholds noisy |
| Share of "poor" experiences | Rises by a few points | Catches a regression in one segment that p75 does not move |
| Crossing the "good" threshold | p75 moves from good to needs-improvement for a full day | The line that matters externally |
| After each release | Compare the new release id against the previous for the first hours | Fastest attribution |

Require a minimum sample size per window before alerting (a few hundred page views as a
starting point), or low-traffic templates page someone every night. Route alerts to the same
place as other production alerts; alert design in general is in `0x:site-reliability`.

Without own RUM: check the CrUX data monthly (PageSpeed Insights or the CrUX API, which also
offers weekly history) and Search Console's report. This detects regressions weeks late and
without a cause; acceptable at Prototype, not after Launch for a site that depends on search or
paid traffic.

Keep a change log of things outside git that affect performance: tag manager publishes, CMS
template changes, CDN and image-service settings, new embeds. Most "nothing changed"
regressions are in that list.

## Prioritize the work

Performance work competes with features. Rank each candidate on three questions:

1. **How many users, and which ones?** Reach by sessions, weighted by value: paying customers
   and high-intent pages first. A fix on the template carrying 60% of entrances beats a larger
   fix on one carrying 2%.
2. **How bad is it for them?** Moving users out of "poor" matters more than moving "good" to
   better. A page at 6 s LCP on phones is losing visitors; one at 2.2 s is not, whatever the
   Lighthouse report still lists.
3. **What does it cost and risk?** Hours, dependencies on other people, and what could break.

Decision rules:

- Fix site-wide multipliers before page-specific issues: one change to caching, the shared
  chunk, fonts or the tag manager improves every page.
- Fix causes of failed thresholds before optimizing passing metrics.
- Prefer removal (a tag, a dependency, a carousel, a font weight) over optimization: it is
  cheaper and does not regress.
- Timebox investigations. If a day of profiling has not found the cause, add field attribution
  (LCP subparts, INP target, Long Animation Frames) and let the data find it.
- Stop when targets are met. Past "good", returns fall quickly unless own evidence says
  otherwise. State this to the user rather than continuing to polish.
- At Prototype: do the free things (image component, font loader, server rendering, no sync
  third parties) and nothing else. At Launch: field measurement, the audit above, a bundle
  budget. At Scale: experiments, per-team budgets, performance review as part of release.

On search: Core Web Vitals are one ranking input among many, and relevance dominates. Passing
is worth doing; expecting a ranking jump from it is not a promise to make.

## Reporting with before-and-after field data

A performance report is believed when it shows field data for real users over comparable
periods, and connected to something the reader cares about.

- **Lead with the outcome in user terms:** "On phones, the product page now shows its main
  content in 2.1 s for three quarters of visits, down from 3.9 s."
- **Use field data, same segment, equal windows.** Same templates, same form factor, same
  countries, same weekdays. Lab numbers and Lighthouse scores go in an appendix if anywhere.
- **Show the distribution,** not only p75: the share of visits rated good, needs-improvement
  and poor before and after. "Poor visits fell from 22% to 6%" is understood by everyone.
- **Respect the lag.** Own RUM shows the change within a day; CrUX and Search Console take up
  to 28 days to reflect it fully. Report RUM first and say when the public numbers will follow.
- **Add the business metric with honest attribution:** conversion, bounce or engagement for the
  same segment and windows, with what else changed in the period. Without an experiment, say
  "coincided with", not "caused".
- **State what was done and what it cost,** in one line per change, and what is deliberately
  left undone and why.
- **One chart:** the metric over time with the release marked. A table of forty audits does
  not get read.

Template:

| | Before (dates) | After (dates) | Change |
|---|---|---|---|
| LCP p75, phones, product template | | | |
| INP p75, phones, all templates | | | |
| Share of visits with all three vitals good | | | |
| JS transferred, landing route | | | |
| Conversion, same segment | | | (note confounders) |

## Ask the user

- **Which business outcome should performance serve?** Search traffic, paid-landing
  conversion, checkout completion or daily-use retention each point at different pages.
  Default: landing pages and the signup or checkout path.
- **What is the target and who agreed to it?** A target nobody owns is not enforced. Default:
  Core Web Vitals good at p75 on phones for the top templates.
- **May CI block a merge on a performance budget?** Process decision. Default: hard fail on
  byte budgets, warnings on lab timings.
- **How much time is performance worth this quarter?** Sets where the ranked list is cut.
  Default: do the items that take hours, schedule the ones that take days, drop the rest.
- **Who owns third-party tags and content templates?** Fixes there need their agreement.
  Default: ask for a named owner and a review rule for new tags.
