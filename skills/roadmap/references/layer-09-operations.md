# Layer 9: Operations

Read this when: the user asks what there is to know about operations, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

Is it up, is it fast, and what happens when it is not?

Competencies: 119 (40 ● / 60 ◐ / 19 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## site-reliability

Know what production is doing and keep it up: logs, errors, metrics and traces, dashboards and alerts, SLOs, incident response, postmortems and runbooks, capacity and scaling, and disaster recovery.

**Logs and error tracking** (`references/logging-errors.md`)

- ● Emit structured JSON logs carrying request and trace IDs
- ● Capture frontend and backend errors with source maps and release tags
- ● Scrub card data, tokens and personal data from logs and traces
- ● Choose log levels and what belongs at each
- ● Search and correlate logs to follow one request
- ● Ship logs off the host to a central store
- ◐ Triage error-tracker noise: group, assign, ignore and alert on new
- ○ Control telemetry cost with sampling and retention tiers

**Metrics and distributed tracing** (`references/metrics-tracing.md`)

- ● Record business metrics (signups, checkouts, jobs) beside technical ones
- ● Choose a hosted observability backend that fits a small team's budget
- ◐ Instrument services with OpenTelemetry traces, metrics and logs
- ◐ Instrument rate, errors and duration for each service and dependency
- ◐ Propagate W3C trace context across browser, services and queues
- ◐ Follow one failed request across CDN, load balancer, app, database and provider
- ○ Choose metric types and keep label cardinality bounded
- ○ Route telemetry through an OpenTelemetry Collector to stay vendor-neutral

**Dashboards and alerting** (`references/dashboards-alerting.md`)

- ● Set up external uptime checks that alert your phone
- ● Monitor scheduled jobs with heartbeat checks
- ● Alert on symptoms users feel, not on every cause
- ◐ Build one dashboard per service showing the golden signals
- ◐ Alert on saturation: disk, memory, connections and queue depth
- ◐ Make every page actionable and link it to a runbook
- ◐ Run synthetic probes of critical journeys from several regions
- ◐ Watch third-party dependencies and their status feeds
- ○ Alert on silent revenue drops with business-metric anomaly detection

**SLOs and error budgets** (`references/slos-error-budgets.md`)

- ● Decide the reliability target a product at each stage actually needs
- ◐ Define SLOs for key user journeys from real user impact
- ◐ Choose indicators: availability, latency, correctness and freshness
- ◐ Use the error budget to choose between features and reliability work
- ◐ Review SLOs regularly and adjust targets from evidence
- ○ Alert on error-budget burn rate over several windows
- ○ Offer an SLA with uptime credits you can actually meet

**On-call and incident response** (`references/incident-response.md`)

- ● Mitigate first: roll back, flag off, scale up or fail over before diagnosing
- ● Set up a status page and incident message templates before launch
- ● Design solo on-call: automatic mitigation, quiet hours and honest expectations
- ● Communicate through the status page and customer emails during an outage
- ◐ Run an incident: assign a lead, keep a timeline, decide in one place
- ◐ Define severity levels and who gets woken for what
- ◐ Set up paging and an on-call rota a small team can sustain
- ◐ Work an incident caused by a vendor outage you cannot fix

**Postmortems, runbooks and launch readiness** (`references/postmortems-runbooks.md`)

- ● Run a production-readiness review before launch: backups, alerts, rollback, limits and owners
- ◐ Write a blameless postmortem and track its actions to completion
- ◐ Find contributing causes beyond the first root cause
- ◐ Write runbooks for the ten most likely incidents
- ◐ Test a runbook by having someone else follow it
- ◐ Turn the most-used runbook steps into safe scripts
- ◐ Share a postmortem with customers when trust requires it
- ○ Review incident trends quarterly and fund the repeat offenders

**Capacity and scaling** (`references/capacity-scaling.md`)

- ● Decide when scaling up is cheaper than scaling out
- ◐ Run two or more instances behind a health-checked load balancer
- ◐ Measure current headroom and find which component saturates first
- ◐ Configure autoscaling with minimums, cooldowns and maximums
- ◐ Map dependencies and remove single points of failure
- ◐ Spread instances and the database across availability zones with automatic failover
- ◐ Prepare for a known spike: launch day, campaign or seasonal peak
- ○ Forecast capacity from growth trends and load per customer

**Disaster recovery and resilience testing** (`references/disaster-recovery.md`)

- ● Back up secrets, configuration and object storage, not only the database
- ◐ Define RPO and RTO per system from business impact
- ◐ Write and rehearse a disaster recovery plan
- ◐ Plan for losing a key account, vendor or person
- ○ Decide whether multi-region failover justifies its cost against your SLA
- ○ Design multi-region failover against stated RPO and RTO
- ○ Rebuild the whole stack in a new account or region from code and backups
- ○ Inject failures and run game days against critical paths

## web-performance

Make pages and endpoints fast and keep them fast: Core Web Vitals, loading and delivery, JavaScript bundles, images and fonts, rendering and runtime, backend latency and profiling, load testing, and performance budgets.

**Core Web Vitals** (`references/core-web-vitals.md`)

- ● Measure LCP, INP and CLS from real users, not only Lighthouse
- ● Prevent layout shift by reserving space for media, fonts and embeds
- ● Cut LCP with fetchpriority, preload and server-rendered hero content
- ◐ Fix poor INP by breaking long tasks and yielding to the main thread
- ◐ Segment field data by device, connection and country to find who is slow
- ◐ Trace a Core Web Vitals regression to the release that caused it
- ○ Attribute slow interactions using Long Animation Frames data

**Loading and delivery** (`references/loading-delivery.md`)

- ● Lazy-load below-the-fold content and defer non-critical work
- ● Decide which caching layer fixes a slow page: browser, CDN, app or database
- ● Remove render-blocking CSS and scripts from the critical path
- ● Audit third-party scripts and defer or remove the costly ones
- ◐ Cut time to first byte with caching, streaming and fewer origin round trips
- ◐ Use preconnect and resource hints for critical third-party origins
- ◐ Cut request count and bytes for slow radios and battery
- ○ Make navigations instant with bfcache eligibility and speculation-rules prerendering

**JavaScript bundles** (`references/javascript-bundles.md`)

- ● Analyze the bundle and remove duplicate or oversized dependencies
- ● Ship less JavaScript by rendering on the server and using platform features
- ● Code-split by route and lazy-load heavy components
- ◐ Enforce a JavaScript bundle budget in CI
- ◐ Make tree-shaking work: ES modules, side-effect flags, no barrel-file traps
- ○ Load third-party widgets through facades or workers

**Images, video and fonts** (`references/images-fonts.md`)

- ● Serve responsive AVIF or WebP images with srcset, sizes and lazy loading
- ● Set explicit dimensions and high priority on the LCP image
- ● Choose system or variable fonts to cut font weight
- ● Load web fonts with subsetting, preload and font-display without layout shift
- ◐ Resize and optimize images on demand through an image CDN or framework loader
- ◐ Deliver video with posters, streaming formats and lazy loading
- ◐ Replace icon fonts and heavy SVG with optimized sprites or inline SVG

**Rendering and runtime performance** (`references/rendering-runtime.md`)

- ● Profile a slow page with DevTools on a throttled low-end device
- ● Respond to input within 100 ms, optimistically where safe
- ◐ Profile style, layout, paint and composite in the Performance panel
- ◐ Find and fix layout thrashing and forced reflow
- ◐ Reduce DOM size and use content-visibility on long pages
- ◐ Keep typing and scrolling responsive by debouncing, deferring and batching updates

**Backend latency and profiling** (`references/backend-latency.md`)

- ● Profile a slow endpoint and find the slow query, lock or downstream call
- ● Run independent I/O in parallel instead of sequential awaits
- ◐ Track p95 and p99 latency per endpoint and log slow queries
- ◐ Set a latency budget for each hop of a critical request
- ◐ Profile CPU with a flame graph and fix the hot path
- ◐ Precompute expensive results in materialized tables or background jobs
- ◐ Reduce payload size and serialization cost
- ○ Find tail-latency causes: garbage collection, cold starts, pool waits, lock contention

**Load testing** (`references/load-testing.md`)

- ● Decide whether a load test is worth running at this stage
- ◐ Load-test critical endpoints with k6 and find the saturation point
- ◐ Model realistic traffic: request mix, think time, data variety and ramp
- ◐ Identify the first bottleneck from metrics during a test
- ○ Run soak, spike and stress tests and read what each reveals
- ○ Test against production-like data and infrastructure without harming users
- ○ Add performance regression checks for key endpoints to CI

**Performance budgets and audits** (`references/performance-budgets.md`)

- ● Audit a site's performance and produce a ranked fix list
- ● Set performance targets tied to conversion and retention
- ◐ Enforce a performance budget in CI with lab tests
- ◐ Monitor field performance continuously and alert on regressions
- ◐ Prioritize performance work by user and revenue impact
- ◐ Report performance to stakeholders with before-and-after field data
