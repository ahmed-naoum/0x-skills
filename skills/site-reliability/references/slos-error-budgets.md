# SLOs and error budgets

Read this when: setting a reliability target, deciding whether the product is reliable enough,
choosing between feature work and reliability work, building burn-rate alerts, or being asked by
a customer for an SLA.

## What a target allows

Allowed full downtime for an availability target:

| Target | Per 30 days | Per year | What it demands |
|---|---|---|---|
| 99% | 7.2 hours | 3.65 days | A person who notices the same day |
| 99.5% | 3.6 hours | 1.8 days | Paging to a phone, tested rollback |
| 99.9% | 43 minutes | 8.8 hours | Automatic restart and failover, redundancy, fast rollback; one slow human response uses the month |
| 99.95% | 22 minutes | 4.4 hours | No single point of failure, on-call rotation, automated mitigation |
| 99.99% | 4.3 minutes | 53 minutes | Multi-region, no human in the recovery path; not a small-team target |

Three facts bound the choice:

- **Human response time.** Alert delay, waking up, opening a laptop and rolling back takes 15 to
  30 minutes for a solo operator. Any target whose monthly budget is smaller than one such
  response can only be met by automation, not by effort.
- **Dependencies multiply.** A request that needs the host, the database, the auth provider and
  the CDN, each at 99.95 percent, cannot be better than about 99.8 percent unless failures are
  absorbed by redundancy, caching or degradation. Read each vendor's SLA before promising a
  number above them.
- **The user's own path.** Home networks, mobile coverage and laptops are less reliable than
  99.9 percent. Beyond that level most users cannot perceive the difference; they do perceive
  the features not built to pay for it.

## The target each stage needs

| Stage | Target | Reasoning |
|---|---|---|
| Prototype | None. Fix what users report | No users to disappoint; measurement costs more than outages |
| Launch | 99.5% on the main journey, measured; 99.9% as the aim for sign-in and payment | Achievable alone with a PaaS, a managed database and tested rollback |
| Scale | 99.9% across key journeys; 99.95% where contracts require it | Needs redundancy and a rotation; as a rule of thumb each further nine costs about ten times more |

Adjust by what the product is: a tool used in working hours tolerates night maintenance; an API
in other companies' request paths, a payment step, or anything used in emergencies needs a
higher target on that path only. Set targets per journey, not one number for the product, so
the expensive reliability is bought only where it pays.

A target of 100 percent is wrong for everything: it forbids deploys, and the last fraction is
invisible to users behind their own network.

## Journeys and indicators

Pick two to four journeys by asking what a customer would call an outage: cannot sign in, cannot
do the core action, cannot pay, the API they integrate with fails, the data shown is stale. Each
gets one or two indicators. An indicator is a ratio of good events to valid events, so that it
reads as a percentage and yields a budget.

| Indicator | Good event | Use for | Trap |
|---|---|---|---|
| Availability | Valid request answered without a server error | Every request-serving journey | Measured in the app, it cannot count requests that never arrived |
| Latency | Valid request answered faster than a threshold | Interactive paths | An average or a single percentile target hides the tail; use "N percent under T" |
| Correctness | Response was right: the charge matched the cart, the export had every row | Payments, calculations, imports | A 200 with wrong content counts as good in every other indicator |
| Freshness | Data served is younger than a threshold | Dashboards, search indexes, sync, webhook delivery | Pipelines fail silently; freshness is the only indicator that notices |
| Completion (jobs) | Job finished successfully within its deadline | Emails, reports, async processing | Counting only failures misses jobs that never ran |

Decisions to write down per indicator:

- **Where it is measured.** Load balancer or CDN logs are closest to the user and see requests
  the app never received. App metrics are easier and blind to total outages. Synthetic probes
  fill the gap at low traffic. Default at Launch: app metrics plus an external probe; move to
  edge logs at Scale.
- **What is valid.** Exclude health checks, bots and client errors (4xx) from the denominator,
  except 408 and the 429s that hit legitimate use (load shedding, limits set too tight), which
  are the service failing the user; 429s served to abusive clients stay out. Include errors from
  dependencies: the user does not care whose fault it was.
- **The latency threshold.** Take it from what the interaction needs (a page navigation, an
  autocomplete and a report export differ by orders of magnitude), then check it against the
  measured p95. Two thresholds per path work well: most requests under a comfortable bound and
  nearly all under a tolerable one.
- **The window.** Rolling 28 or 30 days. Rolling windows make the budget a continuous quantity;
  calendar months reset the budget and invite risky behavior on the first day.

Written form, kept in the repository:

```yaml
journey: checkout
owner: founder
window: 30d
slis:
  - name: availability
    valid: requests to /api/checkout*, excluding 4xx other than 408 and 429
    good: valid requests answered without 5xx, 408 or 429
    objective: 99.9
  - name: latency
    valid: same as availability
    good: answered in under 800 ms
    objective: 95
```

Start from evidence: measure the indicator for four weeks, then set the objective slightly below
what was achieved. A target copied from another company is either already violated or
meaninglessly loose.

## The error budget as a decision tool

Budget = 1 minus the objective, applied to valid events in the window. At 99.9 percent and one
million valid requests a month, 1,000 may fail. Deploys, experiments, migrations, vendor outages
and planned maintenance all spend from the same budget; nothing is exempt, because users
experienced all of it.

Write the policy down before it is needed. For one person it is a commitment to oneself, which
is why it has to be written:

| Budget state | What changes |
|---|---|
| Most of the budget left, steady burn | Ship normally. Take the risky migration now rather than later |
| One incident used more than about a quarter | Postmortem required; its top action is scheduled before new feature work |
| Under a quarter left | No risky changes on that journey (schema changes, dependency upgrades, big launches) without a rollback rehearsal |
| Exhausted | Feature work on that journey stops; reliability work is the roadmap until the window recovers. Security and data-loss fixes still ship |
| Never spent, quarter after quarter | The target is looser than reality or reliability is over-funded: ship faster, or tighten the target if customers would value it |

Budget lost to a vendor still counts, and the response differs: the reliability work it funds is
a fallback, a cache or a second provider, not internal hardening.

The budget also answers "should this be fixed?" for recurring small errors: a bug that burns 2
percent of the budget a month is cheap to live with; one that burns 40 percent is the priority
regardless of how minor each failure looks.

## Reviewing and adjusting

Monthly while the SLOs are new, quarterly after. Bring the SLO report, the incident list and the
support inbox, and compare them:

| Observation | Meaning | Change |
|---|---|---|
| SLO met, customers complained about reliability | The indicator misses what they feel (wrong journey, wrong measurement point, latency threshold too generous) | Fix the indicator before touching the target |
| SLO missed, nobody noticed | Target tighter than users need | Loosen it, and spend the effort elsewhere |
| SLO missed, customers noticed | Working as designed | Apply the budget policy |
| Always met with large margin | Target too loose or traffic too low to measure | Tighten one step, or accept and review less often |
| Alerts fired without budget impact, or budget burned without alerts | Alert rules and SLO disagree | Rebuild alerts from the SLO (next section) |

Tighten only after two consecutive windows of meeting the tighter number, and only when someone
will benefit. Record each change with the date and the evidence, because an SLA or a sales
promise may later depend on that history.

## Burn-rate alerts

Burn rate is how fast the budget is being spent relative to exactly spending it over the
window: observed error ratio divided by (1 minus the objective). Burn rate 1 uses the whole
budget in the window; at 99.9 percent, an error ratio of 1.44 percent is burn rate 14.4.

Alert on two windows at once: a long one to prove the burn is significant and a short one to
prove it is still happening, so the alert resets quickly after recovery. The standard set for a
30-day window:

| Budget consumed | Long window | Short window | Burn rate | Destination |
|---|---|---|---|---|
| 2% | 1 hour | 5 minutes | 14.4 | Page |
| 5% | 6 hours | 30 minutes | 6 | Page |
| 10% | 3 days | 6 hours | 1 | Ticket |

As a Prometheus-style rule for the first row at 99.9 percent:

```promql
(
  sum(rate(http_requests_total{status=~"5.."}[1h])) / sum(rate(http_requests_total[1h]))
) > (14.4 * 0.001)
and
(
  sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
) > (14.4 * 0.001)
```

Traps and limits:

- **Low traffic.** With a few hundred requests an hour, a handful of failures crosses 14.4 and
  pages. Add a minimum request count to the rule, widen the windows, or generate steady
  synthetic traffic that counts toward the indicator. Below roughly a few thousand requests an
  hour on the journey (a rule of thumb), skip burn-rate paging and rely on uptime checks,
  static error-rate thresholds and business zero-alerts from `dashboards-alerting.md`.
- **Total outages** produce no requests in app metrics, so the ratio is undefined and the rule
  is silent. The external uptime check remains mandatory beside any burn-rate alert.
- **High targets.** At 99.99 percent, burn rate 14.4 is an error ratio of 0.144 percent; make
  sure the measurement has that resolution before alerting on it.
- **Replacing, not adding.** Once burn-rate pages work, delete the static error-rate pages for
  the same journey, or every incident pages twice.

## Offering an SLA

An SLO is an internal target. An SLA is a contract term with a remedy. As a rule of thumb, do
not offer one until the indicator has been measured for about two quarters, bad months
included. The rules below describe common practice in SaaS contracts, not law:

- **Promise less than the SLO.** If the internal objective is 99.9 percent, the SLA is 99.5 or
  99.9 with generous exclusions; the gap is the margin for a bad month.
- **Never promise more than the dependency chain can deliver.** Vendor SLA credits refund a
  fraction of that vendor's fee; they do not cover the credits owed downstream.
- **The remedy is service credit, not refund or damages.** Tiered by how far the month fell
  short, capped at a fraction of that month's fee, applied to a future invoice, and stated as
  the sole and exclusive remedy for unavailability.
- **The customer claims it.** A written request within a set number of days after the month,
  checked against the provider's own measurement, which the contract names as authoritative.
- **Define downtime precisely.** For example: the share of minutes in the calendar month in
  which the external check of a named endpoint failed, or in which the server error ratio
  exceeded a stated level. Slowness, a degraded non-core feature and a single customer's
  integration problem are not downtime unless the definition says so.
- **Exclusions.** Scheduled maintenance announced a stated time ahead, and with a monthly cap;
  the customer's own systems, network and misuse; force majeure; beta and free features;
  suspension for non-payment or abuse. Whether third-party provider outages are excluded is
  negotiated; buyers resist that exclusion because the vendor chose those providers.
- **Scope it to plans that pay for it.** An SLA is an enterprise or annual-plan feature with a
  price, not a line on the public pricing page for every tier.
- **Expect the chronic-failure clause.** Larger buyers ask for a termination right after
  repeated misses (for example, three months in a rolling year). It is reasonable, and it is
  the clause with real consequences.

Related promises usually requested alongside: support response times by severity, RPO and RTO
(`disaster-recovery.md`), incident notification deadlines and postmortem delivery. Each is a
separate commitment to cost separately. Have a lawyer review the wording before signing; caps
on liability and exclusive-remedy clauses are enforced differently by jurisdiction and are often
restricted in consumer contracts. Negotiating the contract around it is in
`0x:sales-support`.

Publish a status page with history (`incident-response.md`) before offering an SLA: buyers check
it, and it is the cheapest evidence that the number is real.

## Ask the user

- **What would customers call an outage?** Defines the journeys. Default: cannot sign in, cannot
  complete the core action, cannot pay.
- **Is the product used around the clock or in working hours in a few time zones?** Decides
  whether night downtime counts as much and whether maintenance windows are acceptable.
  Default: around the clock, no maintenance windows assumed.
- **Has anyone been promised an uptime number, in a contract, a sales call or on the website?**
  An existing promise overrides any chosen target. Default: none; do not publish one.
- **If the budget runs out, will feature work really stop?** A policy that will not be followed
  should be replaced by a weaker one that will. Default: freeze risky changes on the affected
  journey only.
- **Is a customer asking for an SLA with credits?** Then pricing, legal review and two quarters
  of measurements are needed first. Default: offer the measured history and a status page
  instead.
