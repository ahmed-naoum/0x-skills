# Logs and error tracking

Read this when: adding or cleaning up application logging and error reporting, or when logs are
noisy, costly, unsearchable or leaking secrets and personal data.

## Division of labor

| Signal | Answers | Tool | Keep |
|---|---|---|---|
| Error tracker | What is broken, since which release, for how many users | Sentry or equivalent | Every error, grouped |
| Logs | What happened to this one request, job or user | Central log store | Every error and warn, sampled info |
| Traces and metrics | Where the time went, how often | See `metrics-tracing.md` | Sampled |

Exceptions go to the error tracker, not to a log search. A log line saying `error` that nobody is
alerted on is a diary entry. The error tracker gives grouping, release attribution and
deduplicated alerts for free; logs give the surrounding story.

## Structured logs

Write one JSON object per line to stdout. No log files inside the app, no multi-line stack traces
as raw text (they split into separate events in every log store), no string interpolation of
values into the message. The message is a constant string; values go in fields, so that
`msg="payment failed"` can be counted and filtered.

Fields every line carries, set once in the logger and request context, not per call:

| Field | Value | Why |
|---|---|---|
| `time` | ISO 8601 UTC | Correlating across hosts and vendors; local time makes this impossible |
| `level` | String label | Numeric levels differ between libraries |
| `service`, `env`, `release` | Name, environment, git SHA | "Did this start with the last deploy" is the first incident question |
| `request_id` | Per inbound request | Works even when tracing is off or sampled out |
| `trace_id`, `span_id` | From the active span | Jump from a log line to the trace and back |
| `user_id`, `tenant_id` | Internal IDs only | Find everything for one customer without logging email |
| `route` | Template (`/orders/:id`), not the raw path | Raw paths cannot be grouped and may carry tokens |

Node default: pino, with context from `AsyncLocalStorage` so that no function has to pass a
logger around.

```ts
import pino from "pino";
import { AsyncLocalStorage } from "node:async_hooks";

export const requestContext = new AsyncLocalStorage<Record<string, unknown>>();

export const log = pino({
  level: process.env.LOG_LEVEL ?? "info",
  base: { service: "api", env: process.env.APP_ENV, release: process.env.GIT_SHA },
  timestamp: pino.stdTimeFunctions.isoTime,
  formatters: { level: (label) => ({ level: label }) },
  mixin: () => requestContext.getStore() ?? {},
  redact: {
    paths: ["req.headers.authorization", "req.headers.cookie",
      "password", "token", "*.password", "*.token"],
    censor: "[redacted]",
  },
});
```

Two traps in this configuration. A redact wildcard matches exactly one level: `*.password`
covers `{ user: { password } }` but neither a top-level `password` nor a deeper one, so list
every depth that occurs and trust the canary test below, not the pattern. And `env` comes from
a deployment variable, not `NODE_ENV`, which is `production` in staging and preview builds too.

In the request middleware, call `requestContext.run({ request_id, user_id, tenant_id }, next)`.
With OpenTelemetry running, the pino instrumentation adds `trace_id` and `span_id` to each line;
otherwise read them from `trace.getActiveSpan()?.spanContext()` in the mixin.

Request ID rules: generate it at the first hop you control; accept an inbound `x-request-id` only
from your own proxy or CDN, because a client-supplied one lets a caller forge or collide IDs;
return it in a response header and print it on error pages, so a support message can quote it.

**One wide event per request.** Emit a single line when the request finishes with route, status,
`duration_ms`, user, tenant, and the handful of facts that describe what it did (rows returned,
cache hit, provider called, feature flag variant). Ten scattered lines per request cost ten times
as much and answer fewer questions than one wide one. Do the same per job run and per outbound
webhook delivery.

Pretty printing is for the developer terminal only (`pino-pretty` as a dev pipe). Production
output stays raw JSON.

## Levels

| Level | Belongs here | Does not belong |
|---|---|---|
| `fatal` | The process cannot continue and is exiting | Anything the process survives |
| `error` | A request or job failed for a reason a human must fix; also sent to the error tracker | Validation failures, 401/403/404, user typos, expected provider declines |
| `warn` | Handled but abnormal: retry succeeded, fallback used, limit approaching, deprecated call | Anything that happens on every request |
| `info` | The request line, job start and finish, state changes (order paid, plan changed), deploy and config at boot | Loop iterations, payload dumps |
| `debug` | Developer detail, off in production | Secrets, even here |

Rules that keep levels meaningful:

- Production runs at `info`. Make the level changeable without a deploy (environment variable
  plus restart is enough) so an incident can turn on `debug` for one service.
- A client error is not an `error`. A card decline is a business outcome at `info`; a spike of
  them is an alert on a metric, not a log level.
- Log an exception once, at the boundary that handles it. Log-and-rethrow at every layer produces
  five lines and five error-tracker events for one failure.
- If `error` lines occur in normal operation, nobody reads them during an incident. Count
  `error` per hour in a healthy week; the target is near zero, and each recurring one is either
  fixed or demoted.

## Error tracking

Set up at Prototype; it is the cheapest observability there is. Backend and frontend are separate
projects (different volume, noise and owners) sharing one release identifier.

Sequence that makes stack traces readable and regressions attributable:

1. Compute the release once in CI (git SHA) and pass it to the build, the SDK `release` option
   and the source map upload. A mismatch between these three is the usual reason frames stay
   minified.
2. Build with source maps, upload them to the tracker in CI, then remove the `.map` files from
   the deployed output (or build "hidden" maps without the `sourceMappingURL` comment). Public
   maps hand out the original source.
3. Set `environment` so that preview and staging noise never alerts.
4. Mark the deploy in the tracker so "first seen in release X" and suspect commits work.
5. Throw a test error from production, on both sides, and confirm the event shows original file
   names, the release and the user ID.

Backend capture points people miss: unhandled promise rejections, background jobs and cron
(wrap the job runner, not each job), queue consumers, framework error boundaries that swallow
exceptions before the SDK sees them (in Next.js 15 and later, the `onRequestError` hook in
`instrumentation.ts` for server errors and the root `global-error` boundary for render errors), and serverless handlers, where the
SDK must flush before the function is frozen or the event is lost.

Frontend noise to filter at the SDK, before it costs quota: browser extensions and injected
scripts (restrict to your own script origins), `ResizeObserver loop` messages, aborted fetches on
navigation, chunk-load failures after a deploy (handle with a reload prompt, then ignore), and
crawlers on ancient browsers. Do not filter "Network Error" blindly: a spike of it is how a CORS
or CDN breakage shows up.

Attach to every event: user ID and tenant ID (not email), request ID, route template, and the
feature flags in effect. An error without a user count cannot be prioritized.

## Scrubbing secrets and personal data

Never write these to logs, error events, traces or session replays, because every telemetry
store is readable by more people and vendors than the database and is retained on a different
schedule:

- Passwords, session cookies, API keys, `Authorization` headers, JWTs, OAuth codes, password
  reset and magic links, signed URLs, webhook signing secrets.
- Card numbers, CVV, bank details. A card number in logs pulls the log pipeline into PCI scope.
- Request and response bodies wholesale. Email, name, address and phone count as personal data
  under most privacy laws; log the internal ID and look the person up when needed. IP address is
  personal data too: leave it off ordinary application and trace lines, and keep it only on
  authentication, audit and edge access-log lines, where security needs it, under the retention
  in `0x:web-security` (`logging-breach-response.md`).

How to enforce it, in order of strength:

1. **Allowlist at the call site.** Log named fields, never `log.info({ user })` or
   `log.info({ body: req.body })`. Give sensitive classes a `toJSON` that omits secrets.
2. **Redaction in the logger** (the `redact` paths above) as a net for headers and known keys.
3. **Scrubbing in the pipeline** (collector or log agent processor) for patterns such as
   card-like digit runs and bearer tokens. Pattern scrubbing misses things; it is the last layer.
4. **SDK settings**: keep the error tracker's default-PII option off, add a `beforeSend` hook
   that drops bodies and cookies, mask all inputs in session replay.

Traps: tokens in query strings end up in access logs, CDN logs, `http.url` span attributes and
referrers, so keep secrets out of URLs; SQL statements captured on spans may include literal
values unless the instrumentation is set to parameterized text only; exception messages often
embed the offending input (`invalid email: a@b.c`); third-party error payloads can echo the
request including keys.

A test that proves it: send a request carrying canary values (`canary-secret-123`) in the
password, token and card fields, capture stdout and the error-tracker payload in a test
transport, and assert the canaries are absent.

When a secret has reached the logs: rotate it first (deleting the line does not un-leak it),
then purge from the store and any archive, then check who and which vendors had access. Leaked
personal data may be a notifiable breach: see `0x:web-security` and `0x:privacy-compliance`.

## Shipping logs off the host

The app writes to stdout; something outside the process ships. In-process network transports
block or drop under load and lose the last lines of a crash, which are the ones needed.

| Where it runs | How logs leave |
|---|---|
| PaaS or serverless | The platform's log drain or integration to a central store. Built-in viewers keep hours or days and search poorly: add the drain at Launch |
| Containers on a VM or cluster | Container runtime captures stdout; an agent (Vector, Fluent Bit, Grafana Alloy or an OpenTelemetry Collector) tails and forwards with a disk buffer |
| Plain systemd service | journald captures stdout; the same agent reads the journal |

Checks: kill the app with `SIGKILL` and confirm its last lines arrived; block the log endpoint
and confirm the app keeps serving and the agent catches up afterward; confirm host disk cannot
fill from logs (journald and container log size caps set); confirm proxy, CDN and database logs
land in the same store, or at least that their locations are written in the runbook.

## Following one request

1. Get an anchor: the request ID from the error page or response header, the error-tracker
   event, or user ID plus approximate time (ask for the time zone).
2. From the error event or the request line, take `trace_id`. Search the log store for that one
   field across all services, sorted by time. This is why the field name must be identical in
   every service.
3. No ID at all: filter `user_id` and `route` in a five-minute window, find the failing request
   line, then pivot to its `request_id`.
4. Jobs: the enqueuing request logs the job ID; the worker logs the same job ID plus the
   originating `trace_id`. Without that link an async failure is unattributable.
5. For hops outside the app (CDN, load balancer, provider) see `metrics-tracing.md`.

Save the queries that worked as named searches; the next incident will need the same three.

## Triage of error-tracker noise

An inbox with thousands of unresolved issues is the same as no error tracking. Weekly, fifteen
minutes, and after every deploy:

| Issue | Action |
|---|---|
| New in the latest release | Look now; a new issue minutes after a deploy is the best rollback signal there is |
| Real bug, low impact | Assign, link to a ticket, resolve when the fix ships so a recurrence shows as a regression |
| Not actionable (extension, bot, client offline) | Add an SDK filter or a server-side inbound filter, then delete. In Sentry-style trackers an archived or ignored issue only stops notifications; its events still count against quota |
| Known, will not fix soon | Archive until it affects N more users or its rate multiplies |
| One bug split into many issues, or many bugs merged | Fix grouping with a fingerprint rule |

Alert rules worth having: a new issue in production; a resolved issue that regressed; an issue
affecting more than a set number of users per hour. Send these to a chat channel, not to the
pager; paging belongs to symptoms (`dashboards-alerting.md`). Do not alert on every event.

## Cost: sampling and retention

Telemetry bills grow with traffic and with carelessness, usually the second. In order of yield:

1. Drop at the source what nobody will read: health checks, static asset requests, bot probes
   for `/wp-login.php`, `debug` lines.
2. Never sample errors. Sample success: keep all `warn` and `error` lines and all slow requests,
   keep a fraction of fast successful request lines, and record the sample rate on the line so
   counts can be scaled back up.
3. Traces: a head sampling rate set by environment variable; tail sampling (keep every trace
   with an error or high latency) needs a collector and is a Scale concern.
4. Retention tiers: searchable hot storage for the window incidents are actually investigated in
   (days to a few weeks), then a cheap object-storage archive if needed to reach 30 to 90 days in
   total for application and access logs (`0x:web-security`), longer only if a contract or
   regulation requires it. Audit logs are a separate stream with its own, longer retention.
5. Set the error tracker's spike protection and per-key rate limits so one looping client cannot
   burn the monthly quota in an hour.
6. Put a budget alert on the telemetry vendor like on any cloud bill.

Session replay is the most expensive signal per event: sample sessions lightly and capture all
sessions with an error.

## Ask the user

- **Which data may leave for telemetry vendors, and in which region?** Decides vendor region,
  scrubbing strictness and whether a DPA is needed. Default: IDs only, no personal data, vendor
  region matching the database.
- **How long must logs be kept?** Contracts and regulation may set a minimum or a maximum.
  Default: 14 to 30 days searchable; 30 to 90 days in total for application and access logs
  (cheap archive tier if the store needs one; `0x:web-security`); audit logs handled separately.
- **Is session replay acceptable to your users?** It records behavior and needs disclosure and,
  depending on jurisdiction, consent (`0x:privacy-compliance`). Default: off until there is a specific debugging need, then masked.
- **What may be spent on telemetry per month?** Sets sampling rates. Default: stay inside the
  free or lowest tier until Launch, then cap at a figure the user names.
