# Disaster recovery and resilience testing

Read this when: planning for the loss of a database, a region, a cloud account, a vendor or a
key person; setting recovery objectives; deciding on multi-region; or rehearsing any of these.

## Which disasters to plan for

Ordered roughly by how often they happen to small products. Region loss is the one people plan
for first and meet last.

| Scenario | Typical cause | What saves the company |
|---|---|---|
| Data deleted or corrupted | A bug, a bad migration, a script run against production, an agent or a person with too much access | Point-in-time recovery, tested; soft deletes on critical tables |
| Account locked or suspended | Failed payment, fraud flag, terms-of-service complaint, lost MFA device, departed owner | Second owner, recovery codes, backups outside that account |
| Account compromised | Stolen session or key; attacker deletes resources and backups | Backups in a separate account the main credentials cannot delete |
| Vendor fails or drops you | Payment account frozen, provider shutdown, price change, ban | Data export and a known alternative |
| Database lost | Provider incident, failed upgrade, storage failure | Standby plus backups |
| Zone or region outage | Provider incident | Multi-zone; cross-region backups and a rebuild path |
| Domain lost | Expired, hijacked, registrar dispute | Auto-renew, registrar lock, separate hardened account |
| Key person unavailable | Illness, accident, departure | Documented access and runbooks, a named successor |

By stage: Prototype needs code in git and nothing else. Launch needs tested database restore,
off-account backups of everything in the next section, two ways into every critical account
and a one-page plan. Scale adds rehearsed full rebuilds, written RPO and RTO per system and,
only if contracts demand it, a second region.

## Back up more than the database

A restored database without the encryption key, the uploads or the DNS zone is not a restored
product. Inventory every place state lives:

| Item | Where it lives | How to protect it | Trap |
|---|---|---|---|
| Database | Managed Postgres | PITR plus logical dumps copied elsewhere (`0x:postgres-database`) | Provider backups are deleted with the instance or account on many platforms |
| Secrets and environment variables | Platform dashboard, CI settings | A secrets manager or password manager as the source of truth, with an encrypted export stored separately | Dashboards often cannot export values; the only copy is the running app |
| Encryption and signing keys | KMS, environment | Documented key hierarchy; backup or multi-region keys for anything that encrypts stored data | Losing the key loses the data, however good the backup. Rotated-out keys are still needed for old data |
| Object storage (uploads, exports) | Bucket | Versioning, plus replication to a second region or provider; lifecycle rule to expire old versions | Replication carries overwrites, and in many setups deletions, to the copy; without versioning it is not a backup |
| Infrastructure definition | Terraform or OpenTofu in git; state file | State in versioned remote storage; avoid console-only changes | Hand-made resources that exist nowhere in code |
| DNS zone | DNS provider | Zone in code, or a periodic export | Rebuilding records from memory during an outage |
| Platform and vendor configuration | CDN and WAF rules, auth provider settings, payment products and webhooks, email templates and domain verification, feature-flag definitions | In code where the vendor has an API or Terraform provider; otherwise a dated export or screenshots | The forgotten setting that only matters once: redirect URIs, IP allowlists |
| Data held by vendors | Auth users, payment customers and subscriptions, mailing lists, analytics | Scheduled export; mirror the essentials into the database via webhooks | Card numbers are never exported to you: the provider transfers them only to another PCI-certified processor, on request, so start weeks ahead. Subscriptions and payment history are usually not part of that transfer and are rebuilt from your own records; with a merchant of record, ask whether any transfer is possible |
| Source code and CI | Git host | A mirror or a scheduled clone to other storage; issues and CI configuration if they matter | Every developer laptop is a copy of the code and of nothing else |
| Recovery material | MFA recovery codes, break-glass credentials, the runbooks themselves | Offline or in a second system that does not depend on the first | Storing the recovery codes in the account they recover |

Rules for all of it:

- **Three copies, two providers or accounts, one out of reach.** At least one copy sits in a
  separate account with different credentials, write-once or object-locked where available, so
  that neither a compromised admin nor a bad script can delete it.
- **Encrypt backups, and keep the key somewhere other than the system being backed up.**
- **Restore is the test.** A backup is proven only by restoring it and using the result. Put a
  heartbeat on every backup job and a calendar entry on every restore drill.
- **Retention covers slow discovery.** Corruption is often noticed weeks later; keep dailies for
  weeks and monthlies for months, within the retention limits and deletion duties set by privacy law
  and contracts (`0x:data-stores`, `0x:privacy-compliance`).

## RPO and RTO from business impact

RPO is how much recent data may be lost; RTO is how long until service is back. Set them per
system, because one pair for everything over-protects caches and under-protects payments.

| System | Question that sets RPO | Question that sets RTO | Typical at Launch |
|---|---|---|---|
| Primary database | Can users re-enter the last N minutes? Can it be rebuilt from a provider's records? | Revenue and trust lost per hour down | RPO of minutes (PITR; check the provider's stated figure), RTO 1 to 4 hours in waking hours |
| Uploaded files | Can the user upload again? | Is the product usable without them? | RPO near zero (versioned), RTO hours |
| Payments state | The provider is the source of truth; re-sync from its API | Can checkout run while the rest is down? | RPO zero by re-sync |
| Sessions, caches | Loss means sign in again, or slower | | No backup; rebuilt on demand |
| Search index, derived tables | Rebuildable | Rebuild duration, measured | No backup; RTO is reindex time |
| Analytics and logs | A day is usually tolerable | Days | RPO 24 hours |

Honest RTO is the sum of detection, the decision to declare, a human becoming available,
restore duration, redeploy, DNS or traffic switch, and verification. For a solo operator the
human term alone can be eight hours overnight. Restore duration grows with database size:
measure it, and re-measure as data grows. The RTO that exists is the one the last drill
achieved; the number in a document or contract is a wish until then.

Tighter objectives cost money in steps: daily dumps (RPO a day), PITR (minutes), synchronous
standby (zero for instance failure), cross-region replica (seconds to minutes for region loss).
Pick the step by the cost of an hour and of a lost transaction, not by habit.

## The disaster recovery plan

One or two pages, stored where it can be read when the primary systems are gone (a second
provider, an offline copy, print):

1. **Scenarios covered** and the objective for each.
2. **Who decides.** Declaring a disaster and restoring or failing over discards data and takes
   hours to reverse; name the person and the backup. Include the rule for when to stop waiting
   for the provider and start recovery (for example: no credible recovery estimate after one
   hour).
3. **Where things are**: backups, break-glass credentials, recovery codes, vendor support
   contacts and account IDs, the registrar login.
4. **The recovery sequence**, in dependency order: account and network, data stores, restore
   data, secrets, application, workers and schedulers, traffic switch, verification,
   communication.
5. **The side-effect lock.** A restored database contains pending jobs, scheduled emails and
   unprocessed webhooks from the moment of the backup. Bring the app up with schedulers,
   workers and outbound email and payment calls disabled, verify the data, then enable them one
   by one. Otherwise recovery sends last Tuesday's emails and retries last Tuesday's charges.
6. **Reconciliation** after restore: replay provider events since the recovery point (payments,
   auth sign-ups, inbound webhooks), and tell users what window of their work was lost.
7. **Failback and cleanup**.

Rehearsal schedule: restore the database to a scratch instance at least quarterly and time it;
walk the whole plan as a tabletop exercise (read each step aloud and ask "with what login, from
which machine?") twice a year; do a full rebuild (below) yearly at Scale. Every rehearsal ends
with fixes to the plan. Unrehearsed plans fail at step one, usually on access.

## Losing an account, a vendor or a person

**Accounts.** The cloud, git host, domain registrar, DNS, email workspace, payment provider and
app-store accounts are each a single point of failure with a human-speed recovery process.

- Hold them in the company's name on a company email, never a personal login, with two owners
  or admins. Solo: a second hardware key and recovery codes stored offline, plus a trusted
  person or the password manager's emergency-access feature.
- Break the circular dependency: the login and recovery addresses for the registrar, DNS and
  email accounts must not be on the domain those accounts control. Use a company-owned mailbox
  on a second domain held at a different registrar.
- Keep a second payment card on file and send billing notices to a monitored address;
  suspension for non-payment is the most avoidable outage.
- Registrar lock and auto-renew on; renew key domains for several years.
- Keep backups outside each account, as above, so a suspension is an outage and not an ending.
- Hardening these accounts against takeover: `0x:web-security`.

**Vendors.** For each vendor the product cannot run without, write four lines: what data they
hold and how it is exported (and schedule that export); what the alternative is; how long a
migration would take; what the product does meanwhile. Keep integrations behind one module so
the switch is contained (`0x:backend-architecture`). Specific risks: payment providers can
freeze payouts or close accounts with little notice, so keep cash reserves for it and, at
Scale, an approved account with a second processor; auth providers must allow export of
password hashes or every user resets; a PaaS is portable if the app builds from a Dockerfile
and uses standard Postgres. Vendor selection and exit terms: `0x:engineering-leadership`.

**People.** For a solo founder the plan is short: a password manager with emergency access for
a named person; a document that says what the company runs, where, and how to keep it running
or shut it down properly; a technical contact who has agreed to be called; and customers'
contracts read for continuity or escrow duties. Access is not authority: who may legally act for
the company, its bank and its vendor accounts if the founder is incapacitated depends on the
company form and the jurisdiction, so arrange it with a lawyer (`0x:company-building`). For a team: no system that only one person can
deploy, restore or log in to; test this by having the second person do it.

## Is multi-region worth it

Usually not before Scale, and often not then. Weigh it explicitly:

| It costs | It buys |
|---|---|
| From a small addition (backups, pilot light) to more than double the infrastructure (warm standby, active-active), plus cross-region traffic | Survival of a full region outage, which is rare and usually lasts hours |
| Permanent complexity in data replication, deploys, testing and incident response | A lower RTO for that one scenario |
| Regular failover drills, or it will not work when needed | Sometimes: latency for distant users, or data residency (different problems with simpler solutions) |

Decision rules:

- As a rule of thumb, a single region across multiple zones, done properly, supports targets of
  99.9 to 99.95 percent; compare the provider's own SLA for the services used. Multi-region enters when a contract or regulator requires recovery from region loss
  within about an hour, when the target is 99.99 percent, or when an hour of downtime costs
  more than a year of the second region.
- Most downtime is self-inflicted: deploys, configuration, data bugs. A second region does not
  help with any of it and replicates a bad migration in seconds. Spend on rollback, detection
  and restore first.
- The cheap alternative covers most needs: cross-region backup copies plus infrastructure as
  code plus a rehearsed rebuild gives an RTO of hours for region loss at almost no running cost.
  State that RTO in the SLA rather than building a standby nobody tests.
- Global low latency is served by a CDN, edge caching and read replicas, without multi-region
  writes.

## Designing multi-region failover

Choose the pattern from the stated objectives:

| Pattern | Second region contains | RPO | RTO | Running cost |
|---|---|---|---|---|
| Backup and restore | Backup copies, nothing running | Minutes to hours | Hours | Minimal |
| Pilot light | Replicated database, app defined and deployable, scaled to zero or minimum | Replication lag: seconds | Tens of minutes | Low |
| Warm standby | Full stack at reduced size, receiving every deploy | Seconds | Minutes | Medium |
| Active-active | Full stack serving traffic | Near zero if the data model allows | Near zero | Highest, and the hardest engineering |

Design decisions that determine whether it works:

- **Data.** Asynchronous cross-region replication loses the lag at failover: say so in the RPO.
  Synchronous replication across regions adds the inter-region round trip to every commit.
  Default: one writer region, asynchronous replica in the second. Multi-writer needs
  conflict-free data design and is rarely worth it.
- **Split brain.** Before promoting the replica, make sure the old primary cannot accept
  writes (fence it, or revoke its traffic), or two diverging databases result and must be
  merged by hand.
- **The trigger.** Automate the steps; keep the decision human. Automatic cross-region failover
  on a flapping health check causes more outages than it prevents.
- **Traffic switch.** DNS failover with health checks and a short TTL (60 seconds), or a global
  load balancer. Some clients ignore TTLs, so expect a tail of traffic to the old region.
- **No dependence on the failed region.** The failover procedure must run from the surviving
  region: the switch, the deploy pipeline, the secrets and the dashboards. Check where the
  provider's own control plane for DNS, identity and the registry lives.
- **Everything else stateful**: object storage replication, secrets in both regions, queues
  (in-flight jobs are lost or duplicated, so handlers must be idempotent), caches start cold and
  the database takes the load.
- **Capacity.** Quotas in the second region approved in advance. In a real regional outage
  other customers fail over to the same place and capacity runs short.
- **Standby rot.** Every deploy and every migration goes to both regions, always. A standby that
  is a week behind fails at failover.
- **Failback** is a second migration: resynchronize, switch in a quiet hour, verify.

Prove it by switching production to the second region on purpose at least twice a year and
running there for a day.

## Rebuilding the whole stack from code and backups

This is the real test of infrastructure as code and of the backups, and the recovery path for a
lost account. Do it into a new account or project, not next to the existing resources, because
only an empty account shows what was never written down.

Sequence: account bootstrap (billing, identity, state storage) → network → data stores → restore
data → secrets → container images or builds → app with side effects locked → verification →
workers and schedulers → traffic.

What is found missing, nearly every time:

- Resources and settings created by hand in a console.
- Secrets whose only copy was the old environment; third-party credentials tied to the old
  account.
- Default quotas in a fresh account far below production needs, and email sending that starts
  in a restricted mode on some providers; both can need a support request and days.
- External registrations that name the old endpoints: OAuth redirect URIs, webhook URLs, IP
  allowlists at partners and banks, email domain verification records.
- Container images and build artifacts that existed only in the old registry; unpinned base
  images that have since changed.
- The CI pipeline's own credentials to the new account.
- Restore duration and data transfer time, which dominate the total.

Time the whole run; that is the RTO for account or region loss. A cheap continuous version:
build staging or preview environments from scratch with the same code regularly, so drift is
caught weekly and the yearly drill only tests data and external registrations.

## Failure injection and game days

A game day is a planned failure with people watching, to learn whether detection, mitigation
and runbooks work. Start with the failures already expected to be handled:

| Stage | Inject | Expect |
|---|---|---|
| Launch | Kill an app instance; withhold a heartbeat; point the uptime check at a failing path; roll back a release; restore the database to scratch; sign in with the break-glass account | Alerts arrive on the phone within minutes; no user-visible errors for the instance kill; runbook steps work as written |
| Scale | Fail the database over; block or slow a dependency; exhaust the connection pool in staging; fill a disk in staging; expire a certificate in staging; revoke a key; take a zone's instances out | Degradation as designed, alerts and dashboards show the cause, recovery without manual repair |

Rules:

- Write the hypothesis first: what should happen, which alert fires, within how long. A game
  day without a prediction is just an outage.
- Limit the blast radius: staging first, then production in working hours with the team
  present, one failure at a time, customers informed if they could notice.
- Define the abort condition and the undo before starting.
- Inject slowness, not only failure. A dependency that answers in 30 seconds is worse than one
  that refuses connections, and it is the case timeouts are rarely tested against. A proxy such
  as Toxiproxy, or a fault flag in the client wrapper, is enough; chaos platforms are for
  larger teams.
- Do not inject a failure whose outcome is already known to be bad. A single instance with no
  standby needs redundancy, not an experiment.
- Every surprise becomes a ticket; rerun the same game day after the fix.

## Ask the user

- **How much recent data could be lost without lasting damage, and how long could the product
  be down?** These set RPO and RTO and through them the cost. Default for the primary
  database: a few minutes of data (what PITR gives) and 4 hours down in waking hours, longer
  overnight for a solo operator.
- **Does any contract, regulator or large customer require specific recovery objectives, a
  second region or data residency?** A requirement overrides the cost argument. Default: none;
  single region, multi-zone, cross-region backups.
- **Who can act if you are unreachable for a week?** Decides the people plan and break-glass
  setup. Default: nobody yet; set up emergency access for one trusted person.
- **Which vendor would hurt most to lose, and is an export in place?** Default: payment
  provider and auth provider; schedule exports and mirror essentials into the database.
- **May failure tests run against production?** They are the only real proof and carry some
  risk. Default: staging only until two instances and a database standby exist, then production
  in working hours.
