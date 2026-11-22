# Metrics and distributed tracing

Read this when: instrumenting a service with OpenTelemetry, choosing an observability backend,
deciding which metrics to record, or following one failed request across CDN, proxy, app,
database and an outside provider.

By stage: Prototype needs only the error tracker and the platform's request metrics. Everything
below starts at Launch; per-tenant breakdowns, tail sampling and a Collector wait for Scale.

## Business metrics beside technical ones

Every technical graph can be green while checkout is broken: a bad price ID, a disabled button,
a webhook that silently stopped arriving. The fastest outage detector for a small product is a
counter of the thing customers do.

Record as counters, server-side, at the moment the state change commits:

| Counter | Labels (bounded) | Detects |
|---|---|---|
| `signups_total` | method, plan | Broken auth provider, broken email verification |
| `checkout_started_total`, `checkout_completed_total` | plan, provider | Payment path broken; the ratio is the signal |
| `payment_failed_total` | reason class | Provider incident, expired API key, fraud wave |
| `webhook_received_total` | provider, event type | Provider stopped delivering, signature secret rotated |
| `jobs_enqueued_total`, `jobs_completed_total`, `jobs_failed_total` | queue, job name | Stuck or dead workers |
| `emails_sent_total`, `emails_bounced_total` | template | Deliverability collapse |
| The product's core action (reports generated, messages sent) | type | The product silently not working |

Two traps. Create each series at process start (add 0 for every expected label set):
otherwise the first event after a restart creates the series and rate functions miss it,
which at low volume is most of the signal. And short-lived serverless functions cannot hold a
cumulative counter: there, count rows instead, with a scheduled check that queries the
database (orders created in the last hour) and alerts or pings a heartbeat on the result.

These are operational signals, counted in aggregate and alerted on within minutes. They are not
product analytics: no user ID, no funnel properties, and they live in the metrics backend so
they share dashboards and alerts with technical metrics. Per-user events and funnels belong to
`0x:product-analytics`. Alerting on a drop to zero is covered in `dashboards-alerting.md`.

## Rate, errors and duration for each service and dependency

For every service, per route template: request rate, error rate, duration as a histogram. Then
the same three for every dependency as seen from the caller: database, cache, each third-party
API, the queue. Caller-side measurement includes network, pool wait and timeouts, which the
dependency's own dashboard never shows.

Decisions that make these numbers usable:

- **Define "error" on purpose.** 5xx and timeouts count. 4xx are tracked separately: they are
  the client's fault until their rate jumps, at which point they are a deploy that broke a
  client. 429 gets its own series.
- **Duration is a distribution.** Record a histogram and read p50, p95 and p99. An average hides
  the slow tail, and the slow tail is where the heaviest customers live.
- **Split success and failure latency.** Fast failures drag percentiles down and make an outage
  look like an improvement.
- **Queues and jobs**: enqueue rate, completion rate, failure rate, run duration, and the age of
  the oldest waiting job. Depth alone misleads; age says how late work is.
- **Connection pools**: in use, idle, waiting, and time spent waiting for a connection. Pool
  exhaustion looks like a slow database when the database is idle.

Auto-instrumentation covers inbound HTTP, outbound HTTP and database clients. What is usually
missing afterward is the business counters, queue age and pool wait.

## OpenTelemetry in a Node service

Instrument with the OpenTelemetry API and SDK, export OTLP. Vendor agents and proprietary SDKs
tie the code to a bill; OTLP makes the backend a configuration value.

The SDK must start before the modules it patches are loaded, or HTTP and database calls go
untraced with no error. Load it with a preload flag, not from inside the app entry file.

```ts
// instrumentation.ts  ->  node --import ./instrumentation.js server.js
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";

export const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter(),
  // without a reader, counters and histograms are recorded and never exported;
  // SDK releases that predate the array option take a single `metricReader`
  metricReaders: [new PeriodicExportingMetricReader({ exporter: new OTLPMetricExporter() })],
  instrumentations: [
    getNodeAutoInstrumentations({ "@opentelemetry/instrumentation-fs": { enabled: false } }),
  ],
});
sdk.start();
// Workers and scripts: flush, then exit. A web server with its own SIGTERM drain
// (capacity-scaling.md) calls sdk.shutdown() at the end of that drain instead, because
// this handler exits while requests are still in flight.
process.on("SIGTERM", () => { sdk.shutdown().finally(() => process.exit(0)); });
```

Configure through the standard environment variables so nothing vendor-specific is in code:

```bash
OTEL_SERVICE_NAME=api
OTEL_RESOURCE_ATTRIBUTES=service.version=$GIT_SHA,deployment.environment.name=production
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.example-backend.com
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer%20$TOKEN
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
```

Notes that save an afternoon:

- Header name, auth scheme and the environment attribute differ per backend (an API-key header,
  Basic auth, the older `deployment.environment`): copy them from the vendor's OTLP page. Header
  values are percent-encoded, hence `%20` for the space. The `-otlp-http` exporters send JSON; if
  the backend accepts only protobuf, use the `-otlp-proto` packages.
- Next.js: use the framework's `instrumentation.ts` `register()` hook; on Vercel the
  `@vercel/otel` helper wires the SDK for both Node and edge runtimes. The Node SDK does not run
  in the edge runtime: import it only when `process.env.NEXT_RUNTIME === "nodejs"`.
- ES modules need the OpenTelemetry loader hook registered as well as the preload; without it
  auto-instrumentation silently patches nothing. Check the current SDK documentation for the
  exact flag, since this area has changed between releases.
- Bundlers break auto-instrumentation by inlining the libraries it patches. Mark instrumented
  packages as external in the server bundle.
- Serverless: spans are exported in batches; force a flush before the invocation ends or the
  last spans never leave.
- Manual spans (`tracer.startActiveSpan`) go around units of work the auto-instrumentation
  cannot see: a pricing calculation, a document render, an LLM call. In the callback, call
  `span.recordException(err)` and `span.setStatus({ code: SpanStatusCode.ERROR })` on failure
  and `span.end()` in a `finally`; a span that is never ended is never exported.
- Use semantic-convention attribute names for HTTP, database and messaging, so backends render
  them; put product attributes under one prefix (`app.tenant_id`, `app.plan`). High-cardinality
  values are welcome on spans and forbidden on metrics.
- Logs: keep writing JSON to stdout with `trace_id` on each line (`logging-errors.md`). The
  OpenTelemetry logs SDK is optional; correlation is what matters.

## Trace context across browser, services and queues

The W3C header is `traceparent: 00-<32 hex trace id>-<16 hex parent span id>-<2 hex flags>`;
flag `01` means sampled. `tracestate` carries vendor data and `baggage` carries key-value pairs
to every downstream hop, including third parties if propagation is not restricted, so never put
personal data or secrets in baggage.

| Hop | What to do | Trap |
|---|---|---|
| Browser to API | Enable propagation only for your own API origins | A custom header triggers a CORS preflight; the API must list `traceparent` (and `baggage`) in allowed headers or every call fails |
| Public edge | Decide sampling at your edge instead of honoring the caller's sampled flag | A parent-based sampler obeys any client that sends flag `01`, so anyone can force full sampling and raise the bill |
| Service to service | Automatic with instrumented HTTP clients | A hand-rolled fetch wrapper or a proxy that strips unknown headers breaks the chain |
| Queue or job | Inject context into the message or job payload at enqueue, extract in the worker | Async context does not cross the queue by itself; the worker starts an unrelated trace |
| Outbound to third parties | Do not propagate | It leaks internal IDs and baggage |
| Scheduled job | Starts a new trace; log the trace ID with the job run ID | |

Queue propagation with the API:

```ts
import { context, propagation } from "@opentelemetry/api";

// producer
const carrier: Record<string, string> = {};
propagation.inject(context.active(), carrier);
await queue.add("send-invoice", { invoiceId, _otel: carrier });

// consumer
const parent = propagation.extract(context.active(), job.data._otel ?? {});
await context.with(parent, () => handle(job));
```

For jobs that run long after the request, or one worker run that handles a batch from many
requests, use a span link to the originating context instead of a parent-child relation; a
trace that stays open for hours is unreadable and breaks tail sampling.

If the error tracker has its own tracing headers, pick one propagation format across all
services. Two tracers each starting their own trace per request is a common cause of "the trace
stops at the API".

## Following one failed request across hops

Each layer has its own identifier. Log all of them on the app's request line so one line links
every system:

| Layer | Identifier | Where to find it |
|---|---|---|
| CDN | The CDN's request ID header (Cloudflare `cf-ray`) | Response header to the user; request header to the origin |
| Load balancer | Its request or trace ID (AWS ALB `X-Amzn-Trace-Id`) | Access logs; request header to the app |
| App | `request_id`, `trace_id` | Response header, logs, error event |
| Database | Trace ID in a SQL comment, `application_name` | Slow-query log, `pg_stat_activity` |
| Provider | Their request ID (Stripe returns `Request-Id`) | Response header on every outbound call; log it, support will ask for it |

Procedure:

1. Get the time (with time zone), the user or tenant, the URL and, if possible, the request ID
   shown on the error page.
2. Establish which layer generated the response. An error page in the CDN's or proxy's style
   means the app may never have seen the request.
3. Read the status code as a statement about who failed:

| Code | Meaning at a proxy |
|---|---|
| 502 | Upstream answered with garbage or closed the connection: crash, restart mid-request, or the app's keep-alive timeout shorter than the proxy's idle timeout |
| 503 | No healthy upstream, or deliberate load shedding |
| 504 | Upstream did not answer, or could not be connected to, within the proxy timeout |
| 499 (nginx) | The client gave up first; usually slowness upstream |
| Cloudflare 520 to 526 | Origin-side classes: 521 refused, 522 connect timeout, 524 origin connected but too slow, 525 and 526 TLS between CDN and origin |

4. If the app saw it, open the trace: the failing or longest span names the dependency. No
   trace because of sampling: use `request_id` in logs.
5. If the slow span is the database, distinguish pool wait, lock wait and execution
   (`0x:postgres-database`). If it is a provider, compare with their status page and quote
   their request ID.
6. If no layer has a record, the request died before the edge: DNS, TLS or the client network
   (`0x:web-networking`).

## Metric types and cardinality

| Type | Use for | Trap |
|---|---|---|
| Counter | Things that happen: requests, errors, signups | Graph the rate, not the raw value; resets on restart are handled by rate functions |
| Up-down counter or gauge | A current level: queue depth, pool in use, memory | Sampled at scrape or export time; spikes between samples are invisible |
| Histogram | Durations and sizes | Percentiles are only as precise as the bucket boundaries |

Rules:

- Never average percentiles across instances or time windows; the result is meaningless.
  Aggregate the histogram buckets, then compute the percentile.
- With fixed buckets, put a boundary exactly at each latency threshold that an SLO or alert
  uses, or the "under 300 ms" ratio cannot be computed. Use exponential histograms when the
  backend supports them.
- Every distinct combination of label values is a separate time series, stored and billed
  separately. Series count is the product of the label value counts.

| Safe as metric labels | Never a metric label |
|---|---|
| Route template, method, status class, region, plan tier, queue name, dependency name | User ID, email, tenant ID at scale, request ID, raw URL, error message, any free text |

Unbounded values go on spans and log lines, which are built for them. Two cardinality leaks to
check for: requests that match no route falling back to the raw path (vulnerability scanners
then create thousands of series; bucket them as `unmatched`), and tenant labels that were fine
at 50 tenants and are a bill at 5,000. Rule of thumb: one metric should stay in the hundreds to
low thousands of series; look at the backend's cardinality report monthly.

## Choosing a hosted backend

Do not self-host Prometheus, Grafana, Loki or an ELK stack before Scale: the monitoring system
becomes the least-monitored production system, and it fails in the same incident as the app if
it shares the app's infrastructure.

Selection criteria for a small team, in order:

1. **Native OTLP ingest** for traces, metrics and logs, so leaving is a configuration change.
2. **A pricing unit that tracks something controllable.** Per-GB or per-event pricing with a
   hard cap is predictable. Per-host pricing punishes many small instances and autoscaling.
   Per-custom-metric or per-series pricing punishes cardinality mistakes. Per-seat pricing
   punishes sharing dashboards.
3. **A free or low tier that covers Launch** with alerting included, not sold separately.
4. **Logs, traces and metrics linked** by trace ID in one place. Three best-of-breed tools mean
   three logins during an incident.
5. **Data region and a DPA**, if customers ask.

Reasonable shapes: the hosting platform's observability plus an error tracker (Prototype); one
OTLP-native hosted backend such as Grafana Cloud, Honeycomb, Axiom or Better Stack plus the
error tracker (Launch); a full suite such as Datadog or New Relic when the breadth is used and
someone watches the bill (Scale). The names are examples, not a ranking: check current
OTLP support, pricing, free-tier limits and whether alerting is included before recommending;
all of these change. Whatever is chosen, set an ingest cap and a billing alert on
the first day.

## Routing through an OpenTelemetry Collector

Skip the Collector while there is one backend that accepts OTLP directly. Add it when one of
these is true: two backends must receive the same data (migration or evaluation); scrubbing and
attribute filtering must happen in one place; tail sampling is needed; host and database
metrics must be collected alongside app telemetry; credentials for the vendor must stay out of
app containers.

The minimal configuration is one `otlp` receiver (gRPC on 4317, HTTP on 4318), the
`memory_limiter` processor, and one OTLP/HTTP exporter per backend with its sending queue, retry
and batching enabled, wired into three pipelines (traces, metrics, logs). Batching has moved
from the standalone `batch` processor, now deprecated, to the exporter's queue settings; copy
component names and batching syntax from the documentation of the Collector version in use. Apps then point `OTEL_EXPORTER_OTLP_ENDPOINT` at the
Collector and hold no vendor credentials.

Traps: `memory_limiter` goes first in every pipeline or a backend outage kills the Collector by
memory; ports 4317 and 4318 must not be reachable from the internet; tail sampling needs every
span of a trace to reach the same Collector instance, which a plain load balancer in front of
several Collectors breaks; the Collector is now a production service, so alert on its own
dropped-data and queue metrics; apps must keep serving when it is down (exporters fail open
and drop, they do not block requests).

## Ask the user

- **Which actions are the business?** The two or three events whose absence means the product
  is down for customers. Default: signup, the core product action, and payment success.
- **What may telemetry cost per month?** Sets sampling and vendor tier. Default: free or lowest
  tier, 10 percent trace sampling, all errors kept.
- **Is there an existing vendor contract or a compliance requirement on data region?** Decides
  the backend before any technical comparison. Default: none; choose an OTLP-native backend in
  the database's region.
- **Do customers need per-tenant reliability reporting?** That requires tenant attributes on
  spans and logs from the start. Default: yes on spans and logs, no as a metric label.
