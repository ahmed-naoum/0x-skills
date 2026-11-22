# On-call and incident response

Read this when: production is down or degraded right now, or when setting up paging, severity
levels, an on-call arrangement, a status page and incident messages before they are needed.

## During an incident: the sequence

1. **Acknowledge** the page so it stops escalating, and start a timeline (a notes file or the
   incident channel) with the current UTC time.
2. **Size the impact** in two minutes: which journey, all users or some, since when. The
   dashboard and the error tracker answer this; do not open code yet.
3. **Declare**: pick a severity (below), post "Investigating" on the status page if customers
   are affected.
4. **Ask what changed**: deploys, flags, config, migrations, scheduled jobs, vendor status,
   traffic. Most incidents start at a change made in the previous hour.
5. **Mitigate** with the cheapest reversible action (next section).
6. **Verify** on the same graph that showed the problem, and with a real request.
7. **Update** the status page, then keep watching for 15 to 30 minutes before resolving.
8. **Stop.** Root-cause work happens in daylight, from the timeline. The permanent fix written
   at 3 a.m. is the next incident.

If there is any sign of intrusion, data exposure or tampering, switch to the breach procedure in
`0x:web-security` before restarting or rolling back anything: evidence and notification duties
change the order of operations.

## Mitigate first

The goal of the first phase is to stop user harm, not to understand it. Understanding takes
hours; rollback takes minutes. Do not wait for proof that the deploy caused it: if a change
landed shortly before onset, revert it and see whether the graph recovers.

| Situation | First action | Trap |
|---|---|---|
| A deploy shortly before onset | Roll back to the previous release | A migration in that deploy may make the old code incompatible; check before rolling back, otherwise fix forward with the smallest change |
| A new feature misbehaving | Turn its flag off | Flags that were never tested in the off position |
| Overload: latency up, saturation high | Scale up or out; shed load; rate-limit or block the abusive client | Scaling app instances out can exhaust database connections and make it worse |
| One bad instance | Remove it from rotation or restart it | Restarting all instances at once turns a partial outage into a full one |
| Database primary unhealthy | Fail over to the standby (`0x:postgres-database`) | Failing over a database that is merely overloaded moves the overload |
| A dependency failing | Disable or degrade the feature that calls it; fail over if a fallback exists | Retry storms from the app keeping the dependency down |
| A job or queue damaging data | Pause the scheduler and the workers | Rolling back code does not undo written data; stopping the writer comes first |
| Bad cached content or bad config at the edge | Purge, or revert the config | Purging everything sends full load to an origin that may not take it |
| Unknown, getting worse | Maintenance page at the CDN and stop writes | Leaving a corrupting system up because the cause is unknown |

Before a restart or rollback destroys state, spend at most one minute preserving evidence: copy
the last logs of the failing instance, save `pg_stat_activity`, screenshot the graphs, note the
release SHA. Mechanics of rollback and flags are in `0x:ci-cd-release`.

Change one thing at a time and write it in the timeline before doing it. Three simultaneous
fixes leave nobody knowing which one worked or which one made it worse.

## Severity levels

Define severity by user impact, never by cause, and decide the response per level in advance so
nobody negotiates it at night.

| Level | Criterion | Who is woken | Status page | Afterwards |
|---|---|---|---|---|
| SEV1 | A core journey (sign-in, core action, payment) is failing for most users; data loss or corruption in progress; security incident | Anyone, any hour | Post within 15 minutes; update every 30 | Postmortem required; customer summary |
| SEV2 | A core journey degraded or failing for a subset; an important feature down; no workaround | On-call in waking hours; at night only if it will become SEV1 by morning | Post; update hourly | Postmortem if it recurs or burned real budget |
| SEV3 | Minor feature broken, workaround exists, internal tooling down | Nobody; next working day | Usually not | Ticket |

When unsure, pick the higher level and downgrade later; an over-declared incident costs an
apology, an under-declared one costs customers. Three levels are enough for a small team.

## Status page and message templates

Set these up before Launch. During the first outage there is no time to choose a vendor or
find words.

Setup decisions:

- Use a hosted status page (the uptime monitoring vendor usually includes one). It must not
  share the app's host, account or deploy pipeline, or it goes down with the thing it reports.
- A subdomain such as `status.example.com` breaks when the domain's own DNS breaks. Know the
  vendor-hosted fallback URL and link both from the footer and the support auto-reply.
- Three to five components in customer language: Website, App, API, Payments, Email
  notifications. Not one per microservice.
- Enable subscriptions (email, RSS or webhook). Business customers route these into their own
  chat tools, which removes most "is it down?" tickets.
- Decide manual versus automatic posting: automatic from uptime checks is fast but posts false
  alarms. Default: automatic component status, human-written incident text.

Templates to keep ready, one per phase:

```text
Investigating: We are investigating problems with [what users experience, e.g. signing in].
Some users see [symptom]. Next update by [time, UTC].

Identified: The problem affecting [function] is identified and a fix is being applied.
[What works, what does not, any workaround.] Next update by [time, UTC].

Monitoring: A fix is in place and [function] is working again. We are monitoring.
[Whether anything needs redoing: failed payments, missed emails.]

Resolved: Between [start] and [end] UTC, [share of users] could not [action]. The cause was
[one plain sentence]. [What is being done to prevent it / a full write-up follows by date.]
```

Writing rules: describe what the user experiences, not internals; give the next update time and
keep it, even when the update is "no change"; no estimated time to resolution unless certain;
no guesses about cause before it is known; say explicitly whether data is safe once that is
known; do not minimize ("a small number of users") without the number; do not promise compensation
or accept legal liability in incident text, since credits are decided afterward
(`postmortems-runbooks.md`).

## Communicating during an outage

| Channel | Use it when | Notes |
|---|---|---|
| Status page | Any customer-visible impact lasting more than a few minutes | Post within 15 minutes of confirming. An all-green page during an outage costs more trust than the outage |
| In-app banner | The app still loads but a function is degraded | Driven by a flag or the status feed so it needs no deploy |
| Support auto-reply and a saved reply | From the first ticket | Link the status page; do not answer each ticket by hand |
| Email to affected customers | They must act (retry a payment, re-upload), their data was affected, or the outage was long and severe | Affected accounts only; one email after resolution is usually better than several during |
| Direct message to key accounts | Contracted customers and anyone mid-launch on the product | A personal note from the founder within the hour is remembered longer than the downtime |
| Social | Only if customers look there or the outage is already being discussed | Link to the status page; do not maintain a second narrative |

Email sent during a vendor or network incident may itself be delayed; never rely on it as the
only channel. If personal data was lost or exposed, legal notification deadlines may apply:
`0x:privacy-compliance` and `0x:web-security`.

After resolution: reply to every ticket that came in, say what happened in two sentences, and
say whether the customer needs to do anything. Public postmortems are covered in
`postmortems-runbooks.md`.

## Solo on-call

One person cannot provide 24/7 human response. Sleep, flights and illness exist, and an
exhausted operator lengthens incidents. Design for that instead of pretending otherwise.

**Let the system mitigate without a person:**

- Health-checked instances that the platform restarts and replaces; at least two of them.
- Deploys that verify health and roll back automatically when the new version fails its checks.
- A managed database with automatic failover and point-in-time recovery.
- Timeouts, bounded retries with backoff and circuit breakers on every outbound call, so a slow
  vendor degrades one feature instead of the site (`0x:backend-architecture`).
- Queues that retry and dead-letter, so work delayed by an outage is done afterward, not lost.
- Rate limits and an edge maintenance page that can be switched on from a phone.

**Limit what may wake the operator.** Night pages for SEV1 only: site down, no orders, data
loss in progress. Everything else waits for morning as a ticket.

**Reduce self-inflicted night incidents.** No deploys, migrations or config changes in the last
hours before going offline, before a weekend away or before a flight. Schedule risky changes
for a morning with a clear day behind it.

**Arrange a second person.** Someone trusted (co-founder, contractor, a founder friend on a
mutual arrangement) with break-glass access and the runbook, who can at least roll back, switch
on the maintenance page and post to the status page. Test that their access works. Without
this, a week of vacation is a week of no coverage; say so to customers who ask.

**Be honest outwardly.** Publish support hours and a response-time expectation. Do not promise
24/7 response in sales calls or contracts. Customers of small vendors accept "monitored
continuously, human response in business hours, critical issues best effort" far better than a
broken promise.

**Make the phone reliable.** Critical alerts that bypass silent mode, a second notification
method, the laptop and a charger within reach, a tethering fallback, credentials in a password
manager that works offline.

## Running an incident with more than one person

- **One lead.** The lead decides and coordinates and does not type commands. Whoever noticed
  first is lead until explicitly handed over ("you have the incident"). With two people: one
  leads and communicates, one operates.
- **One place.** A single channel or call for decisions. Side conversations in direct messages
  produce two people making conflicting changes.
- **One timeline.** Timestamped lines: observations, hypotheses, actions and their results. It
  keeps the team from repeating a failed step, makes handover possible and is the raw material
  for the postmortem. A solo operator keeps it too.
- **Announce before acting.** "Rolling back api to abc123" before pressing the button.
- **A check-in timer** every 15 to 30 minutes: is the current approach working, should the
  severity change, is help needed, is the status page current. Tunnel vision on one hypothesis
  is the most common way incidents run long.
- **Escalate early.** Calling the person who wrote the code after ten minutes is cheaper than
  after ninety.
- **Close deliberately.** Metrics recovered and stable, status page resolved, follow-ups listed,
  postmortem owner and date named, temporary changes (scaled-up instances, disabled flags,
  silences) written down so they are undone.

## Paging and a sustainable rota

Tooling: at one or two people, the uptime monitor's own alerting and phone app is enough. Add a
paging tool (PagerDuty, incident.io, Better Stack on-call or similar) when there is a rotation
to schedule, escalation between people, or several alert sources to merge and deduplicate. Check
that a tool is still sold and supported before adopting it: Opsgenie, long a default here, is
being shut down by its vendor, so migrate off it if the project uses it.

Escalation policy that works for a small team: page the primary; re-page after 5 minutes
without acknowledgment; page the secondary at 10 to 15 minutes; then everyone. An
unacknowledged SEV1 must never end at one sleeping phone.

Sustainability, by team size:

| People | Arrangement |
|---|---|
| 1 | Solo on-call as above. Night pages for SEV1 only; a break-glass backup person |
| 2 to 3 | Alternate weeks as primary, the other as secondary. Human response in waking hours, best effort at night for SEV1. Around-the-clock coverage at this size burns people out within months |
| 4 or more | Weekly primary and secondary rotation with real night coverage. Rule of thumb: nobody primary more than one week in four |

Rules whatever the size: a written handover at each rotation (open issues, risky changes
planned); time off after a night spent on an incident; swaps are free and need no approval;
every person on the rota has production access that works and has personally performed a
rollback and a status-page post in a drill; page volume is reviewed monthly and anything over
about two off-hours pages per on-call week (a rule of thumb) is treated as a defect to fix, not
a duty to absorb.

On-call for employees is also an employment matter: whether standby counts as working time,
the rest owed after a night call and the pay due for being on call differ by country and by
contract. Agree it in writing before the rota starts, with local advice where people are
employed (`0x:company-building`).

## When a vendor is down

1. **Confirm it is them.** Caller-side error and latency for that provider, their status page,
   and other customers reporting. Many "vendor outages" are an expired key, an exhausted quota
   or an unpaid invoice on the account: check those first.
2. **Protect the rest of the product.** Short timeouts and an open circuit so their slowness
   does not occupy every worker. Turn off the feature that depends on them rather than letting
   it hang.
3. **Degrade deliberately.** Queue writes for replay, serve cached reads, accept the order and
   charge later, show "email delivery is delayed" instead of an error. Fail over to a second
   provider only if that path was built and tested beforehand.
4. **Communicate as owner.** Customers bought from this product, not from the vendor. Post to
   the status page what does not work and what does; naming the upstream provider factually is
   fine, blaming it is not.
5. **Open a ticket with the vendor** with request IDs and timestamps, even when their status
   page already shows the incident: it establishes the record for credits and gets specific
   answers.
6. **Do not migrate in a panic.** Switching providers mid-incident trades a known outage for an
   unknown one.
7. **Plan the recovery.** When the vendor returns, queued work and retries arrive at once:
   drain gradually. Then reconcile what was missed, especially payment webhooks and emails:
   re-fetch events from the provider's API rather than assuming redelivery.
8. **Afterward**, decide with numbers whether a fallback is worth building: hours lost per year
   to this vendor against the cost of a second integration (`disaster-recovery.md`).

## Ask the user

- **Who can be woken, and for what?** Sets the night paging policy. Default: the founder, for
  SEV1 only.
- **Who is the backup when you are unreachable?** Without one, coverage has gaps that customers
  with contracts must be told about. Default: none; note it as a known risk and propose a
  break-glass person.
- **What have customers been promised about response and uptime?** Contracts override defaults.
  Default: no commitments; publish business-hours support.
- **How open should public incident communication be?** Some markets expect detail, some
  founders fear it. Default: post every customer-visible incident, plain language, no internal
  detail during, a short cause statement after.
- **Which key accounts get a personal message during an outage?** Default: any customer on an
  annual contract or above a revenue share the user names.
- **Are the people on the rota employees, and is on-call paid?** Standby pay, rest time and
  working-time limits come from local employment law and contracts. Default: nobody employed is
  required to be on call until terms are agreed in writing; until then the founder carries it.
