# Dashboards and alerting

Read this when: deciding what to watch and what should wake someone, setting up uptime checks,
heartbeats for scheduled jobs, dashboards, alert rules or synthetic probes, or when alerts are
too many, too late or ignored.

## The order to build in

| Stage | Build | Skip |
|---|---|---|
| Prototype | Error tracker notifications to chat | Everything else |
| Launch | External uptime check to the phone; heartbeats on backups and billing jobs; one dashboard; pages on error rate, latency and imminent saturation; business zero-alerts; certificate and domain expiry | Burn-rate alerts, anomaly detection products, per-host alerts |
| Scale | SLO burn-rate paging (`slos-error-budgets.md`), multi-region synthetic journeys, per-tenant views, on-call rotation | |

The Launch row is about two hours of work and catches the large majority of outages a small
product has. Do it before anything sophisticated.

## Three destinations for every alert

Decide the destination before writing the rule. An alert with no destination decision defaults
to "everything pages", and then to "everything is muted".

| Destination | Criterion | Examples |
|---|---|---|
| Page (phone, overrides silent mode) | Users are affected now or will be within hours, and a human can do something about it now | Site unreachable, error rate over threshold, checkout producing zero orders, disk full in 4 hours |
| Ticket (chat channel or issue, next working day) | Needs a human, not tonight | Backup heartbeat missed once, disk at 80 percent, certificate expires in 14 days, new error-tracker issue, slow budget burn |
| Record (dashboard only) | Useful when investigating, never by itself | CPU at 90 percent, one instance restarted, a retry succeeded, cache hit ratio dipped |

## Symptoms, not causes

Page on what a user would report: cannot load, errors, slow, the action did not complete, data
is stale. Do not page on what might cause it. High CPU with fast, correct responses is a machine
doing its job; a restarted container that the platform replaced is the system working.

Cause-based alerts fail both ways: they fire when users are fine, and they miss the outage whose
cause nobody predicted. A symptom alert on error rate catches every cause, including next
year's. Causes belong on the dashboard that the symptom alert links to.

The exception is saturation that is predictable and irreversible within hours (below): there the
cause alert buys time that the symptom alert cannot.

Symptom rules for a web product at Launch, with starting thresholds to tune from a week of data:

| Signal | Page when | Notes |
|---|---|---|
| Availability from outside | Two consecutive failures from two or more locations | See uptime checks |
| Server error rate | Over 5 percent of requests for 5 minutes, with a minimum request count | Without the minimum, one failure out of three requests at 4 a.m. pages |
| Latency | p95 over two to three times normal for 10 minutes | Per route group, not globally; one slow export endpoint should not hide the rest |
| Critical journey | Synthetic login or checkout fails twice in a row | |
| Business flow | Zero completions in a window where zero is implausible | See the last section |
| Queue | Oldest job older than the delay users tolerate | Age, not depth |

Always alert on the absence of data too. A rule over a metric that stopped arriving evaluates
to "no data", which most systems treat as healthy; the monitoring pipeline failing is otherwise
silent.

## External uptime checks

The check must run outside everything it checks: not on the same host, not in the same cloud
account, ideally not depending on the same DNS provider. A hosted service (Better Stack,
UptimeRobot, Pingdom, Checkly and similar) is the default; self-hosting the checker on the app's
own server measures nothing.

Set up three checks:

1. **The public URL users hit**, through DNS, TLS and CDN, asserting status 200 and a keyword
   from the real page. Status alone passes when a CDN serves a cached page over a dead origin,
   or when a maintenance or parked-domain page returns 200.
2. **A deep health endpoint** that is never cached (`Cache-Control: no-store`) and runs one
   trivial database query and, if the product cannot work without it, a cache or queue ping.
   Give it a short internal timeout and return 503 on failure.
3. **The API or webhook hostname**, if it differs from the site.

Keep this deep endpoint separate from the shallow one the load balancer uses for instance
health. If the load balancer's check touches the database, a brief database blip marks every
instance unhealthy at once and turns a slowdown into a total outage (`capacity-scaling.md`).

Settings: interval of one minute; a request timeout near the worst latency users would accept;
confirmation from at least two locations before alerting, since a single probe location has its
own network failures; alert on recovery too. Add certificate expiry (alert at 14 days: auto
renewal that has silently failed still leaves time) and domain registration expiry (30 days).

To the phone: use the service's mobile app with critical alerts that bypass silent mode, with
SMS or a voice call as the second step. Email and plain chat notifications are not paging.
Send a test alert at 2 a.m. settings before trusting it: focus modes, battery optimization and
an unverified phone number are the usual reasons the first real page never rings.

## Heartbeats for scheduled jobs

A scheduled job that stops running produces no error, no log line and no failed request. The
only detector is a dead man's switch: the job reports in after each successful run, and a
monitor (Healthchecks.io, Cronitor, the error tracker's cron monitoring) alerts when the report
is late.

```bash
pg_dump "$DATABASE_URL" | gzip > "$FILE" \
  && test "$(stat -c %s "$FILE")" -gt 1000000 \
  && curl -fsS -m 10 --retry 5 -o /dev/null "$HEARTBEAT_URL"
```

Rules:

- Ping only after verifying the result, not merely the exit code. A backup that wrote an empty
  file exited zero. Assert a plausible size or row count first.
- Set the expected period to the schedule and the grace time to the normal runtime plus a
  margin. Where the monitor supports start and fail signals, send them: it then also catches
  jobs that hang and reports failures without waiting for the grace time.
- Cover every job whose silence costs money or data: backups, billing and invoice runs, dunning,
  certificate renewal, data imports and exports, digest emails, cleanup and retention jobs,
  search reindexing, and each queue worker (a ping from the worker loop, to detect a worker that
  is running and consuming nothing).
- Make sure `set -o pipefail` or equivalent is in effect in shell jobs, or a failed first
  command in a pipeline is hidden by a successful last one.
- A missed backup heartbeat is a ticket once and a page if it is missed twice.

## One dashboard per service

A dashboard exists to answer, in under a minute during an incident: is it us, since when, what
changed, and which part. Build one per service to that purpose and resist adding panels.

| Row | Panels |
|---|---|
| 1. What users feel | Request rate; error ratio; latency p50, p95, p99; the business counter for that service |
| 2. Dependencies, from the caller's side | Error ratio and latency per dependency: database, cache, each provider, queue age |
| 3. Saturation | CPU, memory, disk, connections and pool wait, instance count |

Conventions that matter under stress: deploy and feature-flag markers on every time-series
panel (most incidents start at a change); one shared time range and UTC throughout; units on
every axis; error ratio rather than error count, so traffic changes do not look like incidents;
alert thresholds drawn on the panel; a link from every alert to this dashboard. Keep it to about
a dozen panels. Add one overview dashboard with row 1 for each service once there are more than
three services. Delete dashboards nobody opened in a quarter.

## Saturation: disk, memory, connections, queues

Resources that fill up fail suddenly and take hours to remedy. Alert on time-to-exhaustion
where possible, since a threshold is too early on a large volume and too late on a fast leak.

| Resource | Ticket | Page | Trap |
|---|---|---|---|
| Disk space | 80 percent used | Predicted full within 4 hours | A full database disk can stop writes and block the cleanup that would fix it |
| Inodes | 80 percent | 95 percent | "No space left" with free bytes; many small files |
| Memory | Steady growth across days (leak) | Repeated out-of-memory kills | Usage percentage on a garbage-collected runtime is noise; count OOM kills and restarts |
| Database connections | 70 percent of the server maximum | 90 percent, or requests waiting on the pool | Each new app instance and serverless concurrency adds connections; scaling out can cause it |
| Queue | Age of oldest job over the normal maximum | Over what users tolerate, or growing for 30 minutes | Depth grows harmlessly in a burst; age growing means workers cannot keep up |
| Third-party quota | 70 percent of rate or monthly limit | 90 percent | Email sends, LLM tokens, API call quotas fail like outages |
| Certificates, domains, cards on vendor accounts | 14 to 30 days before expiry | | A declined card suspends a vendor as surely as an outage |

Disk prediction in PromQL, as an example of the shape:

```promql
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 4 * 3600) < 0
```

On a PaaS most of these are the provider's limits rather than a host's: find where the platform
exposes memory restarts, connection counts and plan quotas, and alert there. Postgres-specific
saturation (bloat, transaction ID age, replication lag) is in `0x:postgres-database`.

## Every page actionable, every page with a runbook

A page that requires no action trains the reader to ignore pages. The alert text must carry:

- What users experience and how much (`Checkout error ratio 12% for 6 min`), not the metric
  name.
- A link to the dashboard and to the runbook, whose first line is the first mitigation step.
- Severity and the service, so a routing rule and a tired reader can both parse it.

Hygiene rules:

- Require the condition to hold for a duration (`for: 5m`) and require recovery to hold before
  resolving, or a flapping signal pages ten times.
- Group related alerts into one notification; when the database is down, forty endpoint alerts
  are one incident.
- Silences for maintenance always carry an expiry. A forgotten permanent silence is how the
  next outage goes unnoticed.
- After every page, record one of: acted, no action needed, false. Anything other than "acted"
  twice in a row gets its threshold fixed, gets demoted to a ticket, or gets deleted that week.
- Rule of thumb for one person: more than about two pages a week outside working hours is not
  sustainable; treat the count as a defect in the alerts or the system.
- Fire each new page rule once on purpose (lower the threshold temporarily) to prove the whole
  path to the phone.

## Synthetic probes of critical journeys

An uptime check proves a page loads. A synthetic probe proves a user can sign in and do the
thing: it catches broken JavaScript, a failed third-party script, an expired OAuth client
secret. Run two to four journeys (sign in, the core action, checkout to the point of payment)
as scripted browser checks, typically the same Playwright code as the end-to-end tests, in a
service such as Checkly or the observability vendor's synthetics.

| Decision | Default | Reason |
|---|---|---|
| Regions | Three, near the customers | Tells a regional network or CDN problem from an outage; alert when two of three fail |
| Frequency | 5 to 10 minutes for browser journeys, 1 minute for API checks | Browser runs are billed per run and are slower |
| Identity | A dedicated probe account in a dedicated tenant, flagged internal | Keeps probe activity out of analytics, billing, emails and customer-visible data |
| Payments | The provider's test mode or a free internal plan | A probe that charges real cards creates refunds, fees and fraud flags |
| Bot defenses | Allow the probe through with a secret header or token checked at the edge | CAPTCHA and rate limits will otherwise block it and page |
| Data | Each run cleans up after itself or writes to a resettable record | Thousands of probe objects accumulate within weeks |
| Flakiness | Retry once before failing; page only after two consecutive failed runs | A flaky probe gets muted, then misses the real outage |

A probe is production traffic with real side effects; if it sends email or webhooks, point those
at a sink.

## Third-party dependencies

List every outside service the product needs to serve a request or take money: host, DNS, CDN,
database provider, auth, payments, email, storage, LLM API, feature flags, error tracker. For
each:

1. Record caller-side error ratio and latency per provider (`metrics-tracing.md`). This is the
   primary detector. Vendor status pages are updated by humans, often well after the problem
   starts, and understate partial outages.
2. Subscribe to the vendor's status feed (email, RSS, webhook or chat integration) into the
   incident channel, for confirmation and for the all-clear, not for detection.
3. Alert on that provider's error ratio like on an internal dependency, routed as a page only
   if there is a mitigation (fail over, degrade, queue) and otherwise as a ticket plus a status
   page note.
4. Track expiries and quotas: API key and OAuth secret expiry dates, plan limits, the payment
   card on the account. Put dates in a calendar with a reminder two weeks ahead.

Working an incident that a vendor caused is in `incident-response.md`.

## Silent revenue drops: business-metric alerts

The outage that costs most is the one where everything returns 200 and orders stop. Alert on
the business counters from `metrics-tracing.md`.

**Zero-in-window alerts** are the reliable form for small volume. Choose the window so that
zero is implausible in normal operation: if events arrive at random, the chance of seeing none
in a window that normally holds 5 is under 1 percent, and with a normal count of 3 it is about
5 percent. So take the quietest period of the week, find the window that still averages at
least 5 events, and alert on zero in that window. A product with 3 checkouts a day cannot have
a fast checkout alert; use a synthetic checkout probe for that instead.

**Ratio and baseline alerts** work at higher volume: completed-to-started checkout ratio below
half of its 7-day norm; or volume against the same hour one week earlier, which absorbs daily
and weekly seasonality:

```promql
(sum(increase(checkout_completed_total[1h])) or vector(0))
  < 0.5 * sum(increase(checkout_completed_total[1h] offset 1w))
```

Traps: a counter that has recorded nothing returns no series rather than zero, so the
comparison never fires without the `or vector(0)`; holidays and campaign days break
week-over-week baselines both ways; a marketing spike last week makes this week look like a
drop. Run a new business alert to a chat channel for two weeks, tune it, then promote it to a
page. Vendor anomaly-detection features are worth trying only after these static rules exist;
they need weeks of history and still need a human-chosen sensitivity.

Also alert on inbound silence from payment webhooks: no events from the provider within a
window that normally has several usually means a changed endpoint, a rotated secret or a
disabled webhook.

## Ask the user

- **Whose phone rings, and during which hours?** Decides whether pages exist at night at all.
  Default: the founder, all hours for "site down" and "no orders", working hours for the rest.
- **Which two or three user actions mean the business is working?** These become the business
  alerts and synthetic journeys. Default: sign in, the core product action, payment.
- **How long can the product be broken before it costs a customer?** Sets check intervals and
  alert delays. Default: detect within 5 minutes.
- **May a synthetic probe create real records in production?** Needs a probe tenant and cleanup.
  Default: yes, in a dedicated internal tenant with payments in test mode.
