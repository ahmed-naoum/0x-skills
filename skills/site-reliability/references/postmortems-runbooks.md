# Postmortems, runbooks and launch readiness

Read this when: an incident is over and needs writing up, a launch is approaching and readiness
must be checked, or the failures that can be expected need written procedures.

## Production-readiness review before launch

Run this before the first real users, and again before any launch that changes the traffic or
data shape. Every line is checked by doing the thing, not by reading the configuration: an
untested backup and an untested rollback count as absent.

| Area | Check | Proof |
|---|---|---|
| Backups | Database backups run automatically, are stored outside the database's own account or provider, and point-in-time recovery is on | A restore into a scratch database was performed this month and the row counts were compared |
| Other data | Uploaded files, secrets and configuration are recoverable (`disaster-recovery.md`) | The list exists and each item has a copy location |
| Rollback | The previous release can be redeployed in minutes | It was done once, in production, on a harmless change |
| Migrations | Schema changes are backward compatible with the previous release | The last migration was reviewed for this (`0x:postgres-database`) |
| Detection | External uptime check pages a phone; error tracker receives frontend and backend errors with readable stack traces | The site was deliberately broken in a safe way, or the check pointed at a failing URL, and the phone rang |
| Scheduled jobs | Heartbeats on backup, billing and other critical jobs | A heartbeat was withheld and the alert arrived |
| Business alerts | Zero-signup or zero-order alert, or a synthetic journey | Fired once on purpose |
| Logs | Central, searchable by request ID, scrubbed | One request was followed end to end; a canary secret was absent |
| Redundancy | At least two app instances, or a known restart time for one; managed database with failover | An instance was killed and the site stayed up or recovered unattended |
| Limits | Every quota that can stop the product is known with current usage: plan limits on the host and database, connection maximum, email sending limit, payment provider limits, LLM and API rate limits, storage | A table of limit, current use and what happens at the limit |
| Spend | Billing alerts and caps on cloud, telemetry and usage-priced APIs | Alerts exist; a runaway cannot spend unbounded money overnight |
| Abuse | Rate limits on sign-up, login, and anything that sends email or costs money per call | A burst from one IP was rejected |
| Timeouts | Every outbound call has a timeout and bounded retries | Search the code for clients without one |
| Expiries | Domain auto-renew on with a valid card; certificates auto-renew; API keys and OAuth secrets with expiry dates recorded | Dates in a calendar |
| Access | Two people or two devices can reach every critical account; MFA on; recovery codes stored; no single personal login owns the domain, DNS, cloud or payment account | The second path was used to sign in |
| Status and support | Status page live, templates saved, a support address that is read | Linked from the footer |
| Owners | Every component, vendor account and alert has a named person; solo, that means a named backup | Written in the runbook index |
| Runbooks | The top incidents below have a page each | Someone else followed one |

Outcome: a short list of gaps, each with a decision (fix before launch, accept with a date, or
accept permanently and say why). A launch can go ahead with accepted gaps; it should not go
ahead with unknown ones. Gaps in backups, rollback and detection are not acceptable at Launch.

## Runbooks for the incidents to expect

A runbook exists so that a tired person, or a different person, can mitigate without
reconstructing the system from memory. Write the ten most likely first; for a typical web
product they are:

1. Bad deploy: roll back.
2. Site down or returning 5xx: triage path to the failing layer.
3. Database: connections exhausted, disk full, runaway query, failover.
4. Restore from backup, whole database and single table or row.
5. Queue backed up or workers dead; replay of dead-lettered jobs.
6. Payment provider or webhook failures; reconciling missed events.
7. Email not being delivered.
8. Traffic spike or abusive client: scale, rate-limit, block.
9. Certificate, domain or DNS problem.
10. Leaked secret: rotate each credential, and where each is used.

Then one per alert that pages, linked from the alert. A page without a runbook is unfinished.

Format, one page each:

```markdown
# <Symptom as the alert states it>
Severity: SEV1 if <condition>, otherwise SEV2.   Last tested: <date> by <name>.

## Confirm (1 min)
- <dashboard link>: <what it looks like when this is the problem>

## Mitigate
1. <exact command or click path> -- expected result: <what to see>
2. If that did not work: <next step>

## Verify
- <graph or request that proves recovery>

## Escalate
- <who, how, after how long>; vendor support link and account ID

## Afterwards
- <cleanup: scale back, re-enable job, replay queue>
```

Rules: commands are complete and copy-pasteable, with placeholders marked; every step states
what to expect, so the reader knows when to stop following; decision points are explicit ("if
replication lag is over 60 s, do not fail over"); destructive steps are labeled and say how to
undo them; no explanation of architecture beyond a link. Keep runbooks in the repository next to
the code so they are reviewed with changes, with a copy reachable when the repository host or
the company's own systems are down (an exported PDF or an offline clone).

## Testing a runbook

A runbook written by the person who knows the system omits what that person considers obvious:
the VPN, the account to select, the flag that must be passed. The only test is another person,
or the author in a deliberately fresh session, following it literally on staging or on a
harmless production target while the author watches silently and notes every hesitation,
question and missing permission.

- Solo: hand it to the backup person, or give it to a coding agent with read-only instructions
  and ask it to list every step it could not execute as written.
- Test access as part of the run. The usual failure is not a wrong step but a missing login,
  expired token or absent MFA device.
- Record the test date on the runbook. Untested for six months, or older than the last large
  infrastructure change, means untested.
- Restore and rollback runbooks are exercised on a schedule (restore at least quarterly);
  the others when used or when the system changes.
- After every real use, the person who used it edits it the same week.

## From runbook steps to scripts

When a step has been performed by hand three times, or is long enough to mistype under stress,
script it. Order of value: rollback, restore to a scratch database, scaling, toggling the
maintenance page, pausing and resuming queues, rotating a given secret.

Properties of a safe operational script:

- **Dry run by default**; it prints what it would do and requires an explicit flag to act.
- **Names its target and asks for it back.** For production, require typing the environment
  name; never default to production from an unset variable.
- **Idempotent.** Running it twice, or re-running after it failed halfway, is safe.
- **Checks preconditions and stops** (replication healthy before failover, backup newer than N
  hours before a destructive migration).
- **Logs who ran what and when** to a place that survives the incident.
- **Bounded.** A scale-up script has a maximum; a delete script has a limit and a filter that
  cannot be empty.
- **Reviewed and versioned** like application code, and exercised in the runbook test.

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${TARGET_ENV:?set TARGET_ENV explicitly}"
DRY_RUN="${DRY_RUN:-1}"
run() { if [ "$DRY_RUN" = "1" ]; then echo "would run: $*"; else "$@"; fi; }
```

Do not automate a judgment call. Failing over a database, restoring over live data and deleting
anything stay behind a human confirmation until the conditions for doing them are well enough
understood to be written as code. Full automatic remediation is a Scale topic; at Launch the
script the human runs is the automation.

## Writing the postmortem

Write one for every SEV1, for any incident that used a large share of the error budget, for any
data loss however small, and for near misses that were caught by luck. Draft within two working
days while memory and logs exist; keep it to one or two pages.

Blameless means the document explains why the action made sense to the person at the time,
given what they saw and what the system allowed. It is a practical rule, not politeness: when
the finding is "X made a mistake", the fix is "be more careful", which changes nothing, and
people stop reporting. This applies fully to a solo founder writing about themselves and to
mistakes made by a coding agent: ask what let the change through.

Structure:

| Section | Content |
|---|---|
| Summary | Three sentences: what happened, impact, current state |
| Impact | Duration, share of users or requests, failed orders or lost data in numbers, support tickets, budget consumed |
| Timeline | UTC timestamps from the incident log: change made, first error, detection, each action, mitigation, resolution |
| Detection | How it was noticed and how long after onset. "A customer told us" is a finding |
| Response | What helped, what slowed things down (access, missing runbook, unclear ownership) |
| Contributing causes | See next section |
| What went well | Kept because these are the things not to break |
| Actions | Table: action, type (prevent, detect, mitigate), owner, due date, ticket link |

Measure three intervals from the timeline: onset to detection, detection to mitigation,
mitigation to resolution. They say where the next hour of work pays most; for small teams it is
usually detection.

**Tracking actions to completion** is where postmortems fail. Rules: at most five actions, each
small enough to finish in days; each is a ticket in the normal backlog with an owner and date,
not a line in a document; at least one improves detection or mitigation speed, since prevention
of the exact same failure is the least reusable kind; review open actions at a fixed weekly or
monthly point; an action that has been postponed twice is either done now or closed with a
written acceptance of the risk. A postmortem with no completed actions was a diary.

## Contributing causes beyond the first one

The first cause found is the trigger (the deploy, the full disk, the expired key). Stopping
there fixes one instance. Incidents need several conditions to line up; find them by asking a
fixed set of questions rather than repeating "why" along a single chain, which follows one
branch and ends at a person.

| Question | Typical finding |
|---|---|
| Why was the triggering change possible? | No test for the case, no review, no staging data like production, a config change with no validation |
| Why did it reach all users at once? | No gradual rollout, no flag, a shared component with no isolation |
| Why was it not detected sooner? | No alert on the symptom, alert routed to email, threshold too loose, monitoring down with the system |
| Why did mitigation take as long as it did? | Rollback untested, access missing, runbook absent, the one person who knew was asleep |
| Why was the impact as wide as it was? | No timeout, no fallback, retries amplified load, one tenant could affect all |
| What made it worse, and what stopped it from being worse? | Luck is a finding: "it happened at low traffic" means the same failure at peak is still open |
| Has it happened before in another form? | A previous postmortem's action was never done |

Expect three to six contributing causes. Avoid "human error" and "root cause" as final answers,
and avoid counterfactuals ("should have checked") in favor of what the system showed and
allowed.

## Sharing a postmortem with customers

Publish or send one when: the outage was long or widely felt; data was lost, wrong or exposed;
money was affected (double charges, missed payouts); contracted customers were affected or the
contract requires it; or it was publicly discussed. Skip it for brief incidents few noticed; a
resolved status entry with one sentence of cause is enough.

Within about five working days, half a page:

1. What happened and when, in the customer's terms, with numbers.
2. What the impact was, including what was not affected (especially data) if that is certain.
3. The cause, in one honest paragraph without internal names or jargon.
4. What has already been changed and what will be, with dates only for things certain to ship.
5. What the customer needs to do, if anything, and any credit being applied.
6. A plain apology, once, without "any inconvenience".

Rules: the external version is derived from the internal one and never contradicts it; do not
blame a vendor for a dependency chosen without a fallback; do not publish details that help an
attacker repeat it; do not promise "this will never happen again". If personal data was
involved, legal notification rules decide content and timing: get that reviewed
(`0x:privacy-compliance`).

## Quarterly incident trends

One incident is an anecdote; the list is data. Keep a table with one row per incident: date,
severity, duration, journey affected, trigger category, how detected, time to detect, time to
mitigate, budget used, actions done or open. Once a quarter, an hour:

- **Group by trigger category** (deploy, config, capacity, dependency, data, expiry, unknown)
  and by component. Two or more from the same group is a repeat offender and gets funded work,
  not another postmortem.
- **Detection source split**: alert, customer, luck. The share detected by customers should
  fall each quarter; if not, the next investment is detection.
- **Total minutes of impact per category**, not incident count: one long vendor outage can
  outweigh ten small deploy issues.
- **Open actions** older than a quarter: do or close.
- **Pages** that needed no action, by rule: delete or fix the top offender.
- **Near misses and toil**: manual steps repeated more than monthly are script candidates.

Output: the one or two reliability investments for the next quarter, sized against the error
budget policy in `slos-error-budgets.md`, and any SLO target change.

## Ask the user

- **What is the launch date, and can it move?** Decides which readiness gaps are fixed and which
  are accepted. Default: backups, rollback and detection gaps block the launch; the rest are
  accepted with dates.
- **Who else can act when you cannot?** Needed for owners, access and runbook testing. Default:
  none yet; name a break-glass person before Launch.
- **Should postmortems be public?** A public record builds trust and constrains wording.
  Default: internal always; an external summary for SEV1 and anything touching data or money.
- **Will credits or refunds be offered after serious incidents?** A commercial decision that
  should not be improvised mid-apology. Default: goodwill credit for affected paying customers
  after a SEV1, decided case by case.
- **How much time per quarter goes to reliability work?** Without an allocation, postmortem
  actions lose to features every time. Default: the top two actions per SEV1, and one day a
  month.
