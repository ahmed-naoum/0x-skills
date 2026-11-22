---
name: site-reliability
description: "Sets up and runs production operations: logs, error tracking, metrics, tracing, uptime checks, alerts, SLOs, incident response, postmortems, runbooks, capacity planning and disaster recovery. Use when adding monitoring or logging, when production is down, when alerts are noisy, before a launch readiness check, or when planning for traffic spikes, outages and vendor or region loss."
---

# Observability, incidents and reliability

## Stance

Reliability for a small team is mostly three things done early: finding out before customers do,
being able to undo a change in minutes, and being able to get the data back. Everything else is
refinement. One person cannot watch dashboards or answer pages around the clock, so the system
has to detect, restart and roll back without a human wherever it can, and the human's attention
is spent only on what users actually feel.

- **Detection before prevention.** Failures that were not predicted outnumber those that were.
  An external check, an error tracker and a business-metric alert catch all of them; hardening
  catches only the ones imagined in advance.
- **Mitigate, then diagnose.** Roll back, flag off, scale or fail over first. Understanding
  takes hours, rollback takes minutes, and users are harmed for the difference.
- **Page on symptoms users feel.** Error rate, latency, a journey that fails, orders at zero.
  Causes such as CPU belong on the dashboard the page links to; cause alerts fire when users
  are fine and miss the outage nobody foresaw.
- **Untested means absent.** A backup never restored, a rollback never performed, an alert never
  fired and a runbook never followed by someone else do not count. Every claim of readiness is
  proven by doing the thing.
- **Reliability is a budget, not a virtue.** Choose a target per user journey from what
  customers need, measure it, and spend the remainder on shipping. Each extra nine costs
  roughly ten times more; most products need fewer than their founders assume.
- **Most outages are self-inflicted.** Deploys, config, migrations and expired things cause far
  more downtime than hardware or regions. Fast rollback and change markers on graphs beat a
  second region.
- **Every alert has an action, every action has a runbook.** A page that needs no action trains
  people to ignore pages; a page without a first step wastes the minutes that matter.
- **Telemetry is production data.** It leaks secrets and personal data, costs money in
  proportion to carelessness, and is read by more parties than the database. Scrub at the
  source, sample success, never sample errors.
- **Be honest about one-person coverage.** Promise what can be kept: automatic mitigation,
  business-hours response, best effort for critical failures at night.

## Route

| If the task is | Read |
|---|---|
| Add or clean up logging; set up Sentry-style error tracking, source maps and releases; logs leak tokens or personal data; logs are noisy or expensive; find all logs for one request | `references/logging-errors.md` |
| Add OpenTelemetry; decide which metrics to record; pick an observability vendor; trace a request across services or queues; work out which hop returned a 502 or 504; metric cardinality or a Collector | `references/metrics-tracing.md` |
| Set up uptime monitoring, cron or backup heartbeats, dashboards, alert rules or synthetic checks; too many alerts; an outage was reported by a customer first; sales dropped and nothing alerted | `references/dashboards-alerting.md` |
| Decide how reliable is reliable enough; define SLOs and SLIs; use an error budget; build burn-rate alerts; a customer asks for an uptime SLA | `references/slos-error-budgets.md` |
| Production is down or erroring now; set up paging, severity levels or an on-call rota; status page and incident messages; a vendor outage is taking the product down | `references/incident-response.md` |
| Write a postmortem; check whether the product is ready to go live; write or test runbooks; script recurring operational steps; review incident patterns | `references/postmortems-runbooks.md` |
| Will it survive launch-day traffic; how much headroom is there; add a second instance or zone; configure autoscaling; find single points of failure; forecast growth | `references/capacity-scaling.md` |
| What happens if the region, database, cloud account, a vendor or the founder is lost; set RPO and RTO; what to back up besides the database; multi-region; DR drills and game days | `references/disaster-recovery.md` |

During a live incident, go straight to the sequence at the top of
`references/incident-response.md` and act on it before reading anything else.

## Defaults at a glance

| Area | Prototype | Launch | Scale |
|---|---|---|---|
| Errors | Error tracker on frontend and backend with source maps and release tags | Same, with alerts on new and regressed issues to chat | Ownership rules, weekly triage |
| Logs | Platform log viewer; JSON to stdout | Central store via log drain; request and trace IDs on every line; scrubbing tested; 14 to 30 days searchable | Sampling of success lines, retention tiers, pipeline scrubbing |
| Metrics and traces | Platform metrics | Rate, errors, duration per route and per dependency; business counters; OpenTelemetry to one hosted OTLP backend; traces sampled | Collector, tail sampling, per-tenant views |
| Detection | None | External uptime check paging a phone; heartbeats on backups and billing jobs; zero-order alert; certificate and domain expiry | Multi-region synthetic journeys, burn-rate alerts |
| Paging | None | Symptoms only; night pages for SEV1 only | Rotation with primary and secondary |
| Target | None | 99.5% measured on the main journey; no published SLA | 99.9% per key journey; SLA looser than the SLO, credits only |
| Incidents | Fix when noticed | Hosted status page, message templates, three severity levels, timeline kept | Lead and communicator roles, postmortem for every SEV1 |
| Capacity | One instance | Two instances, stateless app, managed database with standby and pooler; peak under half of measured capacity | Multi-zone, autoscaling with minimum 2 and a hard maximum, quarterly forecast |
| Recovery | Code in git | PITR and off-account backups of data, secrets, config and uploads; restore tested quarterly; two ways into each critical account | Written RPO and RTO, yearly full rebuild, game days; multi-region only if a contract requires it |

Tool defaults when nothing is in place: pino for logs, Sentry-style error tracking,
OpenTelemetry SDK exporting OTLP to one hosted backend, a hosted uptime and heartbeat service
with a status page, Prometheus-style alert rules in the backend. Follow what the project
already uses first.

What to skip until Scale: self-hosted monitoring stacks, an OpenTelemetry Collector with one
backend, burn-rate alerting at low traffic, chaos tooling, multi-region, a formal on-call tool
for one person.

## Before you call it done

1. A deliberately thrown error in production appears in the error tracker with original file
   names, the release SHA, the environment and a user ID, from both frontend and backend.
2. One request can be followed end to end by a single ID across every service's logs, and the
   same ID is returned to the client.
3. A request carrying canary secrets in password, token and card fields leaves no trace of them
   in logs, error events or span attributes.
4. No metric has a label with unbounded values (user ID, raw URL, error message); unmatched
   routes are bucketed.
5. The external uptime check asserts page content, runs from outside the hosting account,
   confirms from two locations, and a test alert rang the phone through silent mode.
6. Every critical scheduled job pings a heartbeat only after verifying its result, and a
   withheld ping produced an alert.
7. Every paging rule states user impact, has a minimum duration, links to a dashboard and a
   runbook, and was fired once on purpose. No rule pages on a cause alone.
8. A business alert or synthetic journey covers sign-in and payment, with the absent-series
   case handled.
9. Rollback was performed in production and timed; the database was restored to a scratch
   instance and timed; both dates are recorded.
10. Backups of data, secrets, configuration and uploads exist outside the primary account, and
    the primary credentials cannot delete them.
11. The status page is hosted off the app's infrastructure, with incident templates saved and a
    link in the footer and support auto-reply.
12. Killing one app instance causes no user-visible errors, or the single-instance recovery time
    is measured and accepted in writing.
13. Limits and expiries that can stop the product (connections, quotas, sending limits,
    certificates, domain, API keys, payment card on vendor accounts) are listed with current
    use and an alert or calendar entry.
14. Any stated SLO, SLA, RPO or RTO is backed by a measurement or a drill, not by intent.
15. Postmortem actions are tickets with owners and dates, and at least one improves detection
    or mitigation speed.

## Not this skill

- Deploy mechanics, rollback commands and feature flags → `0x:ci-cd-release`
- Database backups, restore drills and replica failover → `0x:postgres-database`
- Running load tests and profiling slow code → `0x:web-performance`
- Security incidents, intrusions and audit logging → `0x:web-security`
- Diagnosing a single host's CPU, memory or disk → `0x:linux-server`
- Product analytics events, funnels and business dashboards → `0x:product-analytics`
