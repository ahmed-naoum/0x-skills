# Deploys, rollback and cutovers

Read this when: making deploys automatic, removing downtime from deploys, a release is bad and has
to come back out, deciding what to watch after a deploy, sequencing a change that spans database,
backend and frontend, or planning a move to a new platform or database.

## Deploy on merge

Every merge to main deploys. A manual deploy step batches changes, and a batch is harder to
diagnose and scarier to roll back than one small change.

Order inside the deploy, each step gating the next:

1. Checks pass on the merge commit (`ci-pipelines.md`).
2. Build one artifact, named by commit SHA.
3. Run migrations once (backward compatible with the running code).
4. Roll out the artifact; the platform shifts traffic only to instances that pass health checks.
5. Smoke test production; record the release in the error tracker.
6. On failure in 4 or 5: roll back automatically and alert.

```yaml
  deploy:
    needs: [ci-ok, build]
    if: github.ref == 'refs/heads/main'
    environment: production
    concurrency: { group: deploy-production, cancel-in-progress: false }
```

`cancel-in-progress: false` matters: a deploy cancelled between migration and rollout leaves a
half-applied release. Queued deploys run in order; if three merges queue up, deploying only the
newest is fine because the artifact is cumulative.

When the PaaS deploys from git by itself, keep that and gate it with required checks on main; do
not rebuild the same thing in Actions. Confirm two things: the platform waits for checks (or
deploys only what reached main through them), and migrations have a defined place (the platform's
release command or a pipeline job that finishes before promotion).

## Rollback

Rollback means redeploying the previous artifact, which already exists and already ran in
production. It is not `git revert`, which needs a full CI run and a build while users see errors.
Target: under 5 minutes from decision to old version serving, by one command or one button, and
practiced once before it is needed.

| Platform | Rollback |
|---|---|
| Vercel | `vercel rollback <deployment-url>` or Instant Rollback in the dashboard |
| Kubernetes | `kubectl rollout undo deployment/<name>`, or apply the previous image digest |
| Amazon ECS | `aws ecs update-service --cluster <c> --service <s> --task-definition <family>:<previous-revision>` |
| Heroku | `heroku rollback` |
| Image-based PaaS (Fly.io, Render, Railway, Cloud Run) | redeploy the previous image or revision by digest or ID |
| Any | a `workflow_dispatch` deploy workflow that takes a commit SHA and deploys that existing artifact without rebuilding |

Sequence in an incident:

1. Roll back first, diagnose after. If a release went out in the last hour and errors rose, the
   release is the suspect until shown otherwise.
2. Check whether the migration of the bad release allows it (table below).
3. Revert the commit on main (or fix forward) before the next merge, otherwise the next deploy
   ships the bug again. Some platforms pause automatic production promotion after a rollback until
   it is re-enabled; check, or later merges silently stop deploying.
4. Clean up what the release left behind.

### What migrations allow

Rolling back code does not roll back the schema, and should not: down-migrations in an incident
destroy data written since the deploy. The schema stays; the question is whether the previous code
runs on it.

| The bad release's migration | Roll back code? |
|---|---|
| None, or added a table, nullable column or index | Yes. Leave the schema. |
| Added a `NOT NULL` column without a default | No: the old code's inserts fail. Add a default or drop the constraint first. |
| Dropped or renamed a column or table, or changed a type, that the old code uses | No. Fix forward. |
| Added an enum value or a new status that new code already wrote | Only if the old code tolerates unknown values in rows it reads. |
| Backfilled or rewrote data in place | Depends on whether the old code reads the new shape; usually fix forward. |

This is why destructive changes ship at least one release after the code that stopped using the
column (expand, migrate, contract): every release must run on its own schema and on the next one.
Before merging any migration, answer "does the currently deployed code work after this runs?" If
not, split it. Writing these migrations: `0x:postgres-database` (`migrations.md`).

Rollback also does not undo: emails and webhooks already sent, jobs enqueued in a new payload
format (old workers must ignore or tolerate them), cache entries in a new shape (version the cache
key), third-party state, changed environment variables, and bad data written. Bad data is a
repair or restore task: `0x:postgres-database` (`backup-recovery.md`).

Fix forward instead of rolling back only when rollback is blocked by the table above, or the
previous version has the worse bug, and the fix is small and understood. A flag turned off is
faster than either (`feature-flags.md`).

## Zero-downtime mechanics

| Strategy | How | Choose when |
|---|---|---|
| Rolling | replace instances a few at a time behind the load balancer | default on PaaS and orchestrators |
| Blue-green | start a full second copy, switch traffic at once, keep the old copy warm | switch and rollback must be instant; capacity doubles briefly |
| Immutable deployment with alias switch (serverless and frontend platforms) | each deploy gets its own URL; production is a pointer | given by the platform; behaves like blue-green |
| Recreate (stop, then start) | downtime on every deploy | Prototype only |

In all of them two versions run against one database at the same time, so the compatibility rule
above applies regardless of strategy. What makes any strategy actually zero-downtime:

- **At least two instances**, and the rollout never drops below the capacity needed for current
  traffic (in Kubernetes: `maxUnavailable: 0` with a `maxSurge`).
- **Readiness check** that returns success only when the process can serve: config validated,
  database reachable. Do not include third-party services, or their outage takes every instance
  out of rotation. Liveness stays trivial (process responds); a liveness check that queries the
  database restarts the whole fleet when the database is slow.
- **Graceful shutdown.** On SIGTERM: fail readiness, keep serving for a few seconds while the load
  balancer stops sending, stop accepting, finish in-flight requests, close pools, exit, all inside
  the platform's grace period (30 s is a common default; check it).

```ts
process.on('SIGTERM', () => {
  ready = false;                                        // readiness endpoint now returns 503
  setTimeout(() => server.close(() => process.exit(0)), 5_000); // let the balancer drain first
  setTimeout(() => process.exit(1), 25_000).unref();    // hard stop before the platform kills
});
```

- **The app receives the signal.** A container whose command is `pnpm start` or a shell script
  makes the package manager or shell PID 1, and SIGTERM may never reach Node. Use the exec form,
  `CMD ["node", "server.js"]`, or an init process.
- **Long-lived connections** (WebSockets, SSE) are cut on every deploy. Clients reconnect with
  jittered backoff and resume from a cursor, or a deploy becomes a reconnect storm.
- **Workers** stop taking jobs on SIGTERM and finish or release the current one; jobs longer than
  the grace period must be resumable (`0x:backend-architecture`, `background-jobs.md`).
- **Single server.** A plain `docker compose up -d` restart drops requests. Run old and new
  containers briefly behind a proxy that switches on health (Kamal does this), or accept a few
  seconds of downtime at Prototype. Setup: `0x:cloud-infrastructure` (`docker-images.md`).

Check: run a loop of requests during a deploy and count non-2xx responses.

```bash
while true; do curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/healthz; sleep 0.2; done | sort | uniq -c
```

## Smoke tests and release health

A green deploy job proves the process started. Smoke tests prove users can use it.

1. Wait until the new version is what answers: the health endpoint returns the commit SHA.
2. Run 3 to 8 checks against production in under 2 minutes: home page renders, login with a
   dedicated test account, one authenticated read that hits the database, one write that is safe
   to repeat, the checkout page loads (no charge), a job enqueues and completes.
3. Fail the deploy and roll back automatically if any fails.

```bash
for i in $(seq 1 30); do
  [ "$(curl -fsS https://app.example.com/healthz | jq -r .sha)" = "$GITHUB_SHA" ] && exit 0
  sleep 10
done
echo "new version never became live" >&2; exit 1
```

Keep the suite small and non-flaky; a smoke test that fails falsely once a week gets ignored or
makes rollbacks random. Mark test-account traffic so analytics excludes it.

Per-release monitoring: set the error tracker's `release` to the commit SHA at build, upload
source maps for it, and send a deploy marker to dashboards. For 15 to 30 minutes after each deploy
watch, compared with the previous release: error rate, new error types first seen in this release,
p95 latency, saturation (CPU, memory, database connections), and one business signal such as
signups or checkouts per hour. Alert on "new issue in the latest release" so that the watch does
not depend on someone staring at a dashboard. Setup: `0x:site-reliability` (`logging-errors.md`).

## Stale frontends and old clients

After a deploy, browsers keep running the previous JavaScript for hours, open tabs for days, and
installed mobile apps for months. The server must serve version N-1 clients correctly.

| Symptom | Cause | Fix |
|---|---|---|
| `ChunkLoadError` or a blank page on navigation after a deploy | old HTML requests hashed chunks the deploy deleted | keep previous builds' assets served for days (object storage or CDN, never deleted on deploy; the platform's skew protection); on chunk load failure reload once |
| 404 on assets during a rolling deploy | HTML came from a new instance, the asset request hit an old one | serve static assets from shared storage or a CDN, not from each instance |
| "Failed to find Server Action" or failed form posts after deploy | action identifiers change per build | platform skew protection; self-hosted Next.js: a stable `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` across instances and a `deploymentId`; treat the error as "reload" |
| Users stay on old code for days | HTML cached too long, or a service worker serves the old shell | HTML `Cache-Control: no-cache`; hashed assets `public, max-age=31536000, immutable`; service worker update flow (`0x:frontend-foundations`, `pwa-mobile.md`) |
| API errors from open tabs | response or request shape changed in place | additive API changes only; remove fields after old clients are gone |

Detect skew instead of guessing: send the build SHA in a response header, compare it in the client
with the SHA it was built from, and on mismatch reload at the next navigation (not mid-form).

Mobile clients cannot be reloaded. Ship the first store version with a minimum-supported-version
check and a force-upgrade screen, keep API changes additive, and remove an old API behavior only
when analytics show its app versions are gone. API evolution: `0x:api-design`
(`versioning-evolution.md`). Cache headers and CDN purge: `0x:web-networking` (`http-caching.md`).

## Ordering changes across database, backend and frontend

Rule: whoever provides goes first when adding; whoever consumes goes first when removing.

| Change | Order of deploys |
|---|---|
| Add a field or endpoint | database (add) → backend (write and serve it) → frontend (use it) |
| Remove a field or endpoint | frontend (stop using) → wait for old clients to drain → backend (stop reading and writing) → database (drop) |
| Rename or change a type | add new → write both → backfill → read new → stop writing old → drop old; never one step |
| New job or event payload | consumers that accept old and new → producers that send new |
| New required environment variable | set in every environment → code that reads it |
| Third-party API version or webhook format | handler that accepts both → switch the version at the provider |

An additive migration and the backend code that uses it can ship in one pull request, because the
pipeline runs the migration before the rollout. A removal is always a later, separate deploy. In a
Next.js monolith, frontend and backend deploy together, but open tabs still make them different
versions; the table applies anyway. Each step must leave production working and reversible if the
next step never ships.

## Frequency and freezes

- Deploy every merge, in working hours, when someone can watch for the next 30 to 60 minutes.
- Risky changes (migrations on large tables, auth, billing, infrastructure) go early in the day
  and early in the week of whoever would handle the fallout. Small flagged changes with automatic
  rollback can go any time.
- Do not deploy risky changes right before being unreachable: a flight, a weekend away, a
  customer's launch day.
- Freeze only for a concrete reason: a peak revenue period, a major customer event, no support
  cover. Define the dates, what is exempt (security fixes, incident fixes), and who can lift it.
- A freeze builds a backlog, and the first deploy after it is the riskiest of the quarter. Merge
  behind flags during the freeze or release the backlog one change at a time afterwards.
- Urgent fixes use the same pipeline. A bypass path that skips checks is used at the moment of
  least care; make the normal path fast enough (under 15 minutes merge to production) instead.

Low-traffic hours shrink the blast radius but also shrink the signal and find the founder tired.
Use them for changes with unavoidable user impact (a short read-only window), not as the default.

## Canary releases

Skip until Scale. A canary needs enough traffic for a 5% slice to show a difference within
minutes; below roughly a few requests per second it produces noise, and a percentage flag rollout
with staff first (`feature-flags.md`) gives more control for less machinery.

When traffic supports it:

- Steps such as 5% → 25% → 50% → 100%, each held 5 to 15 minutes, advanced automatically.
- Compare canary with the stable version over the same minutes, not with yesterday: traffic mix
  changes by hour.
- Roll back automatically on a threshold fixed before the release: canary error rate or p95
  latency clearly worse than baseline, or the SLO burn rate above the fast-burn alert level
  (`0x:site-reliability`, `slos-error-budgets.md`). A human decides only whether to retry.
- Assign by user or session (sticky), not per request, or a user alternates between versions and
  hits skew on every click.
- A canary starts with cold caches and looks slower for its first minute; exclude warm-up.
- The database is not canaried. Schema changes reach 100% of versions at once, so the
  compatibility rules still carry the risk.
- Rarely used paths (monthly billing run, export) see no traffic during a canary; a flag and a
  test cover those.

Tooling: the platform's traffic splitting where it exists (managed container services, serverless
platforms), Argo Rollouts or Flagger on Kubernetes.

## Cutover to a new platform or database

First decision: is a short announced maintenance window acceptable? For most products before
Scale, 10 to 30 minutes read-only at a quiet hour replaces weeks of dual-write engineering and
removes its failure modes. Choose the live cutover only when downtime truly costs more.

With a window:

1. Days before: build the new side fully, deploy the app to it against a restored copy, run the
   smoke suite. Lower DNS TTLs to 60 to 300 s at least one old-TTL period ahead.
2. Rehearse the data copy on a production-sized copy and time it. The window is that time doubled.
3. At cutover: put the app read-only or in maintenance mode, stop workers and cron on the old
   side, take the final copy or let replication catch up to zero lag.
4. Verify: row counts per table, checksums on critical tables, sequences ahead of the maximum IDs.
5. Switch traffic (DNS, proxy upstream or connection string), run the smoke suite, open writes.
6. Rollback point: until writes open on the new side, going back is lossless and is just undoing
   step 5. After that, going back loses data unless changes are replicated in reverse. State this
   moment in the plan and make an explicit go or no-go decision at it.
7. Keep the old side intact and read-only for days to weeks before decommissioning.

Live, without a window:

- Prefer replication over application dual writes for moving a database: logical replication or
  change data capture keeps the new side current, and the cutover is a brief write pause while lag
  reaches zero. With Postgres logical replication, schema changes and sequence values are not
  replicated and tables need a primary key or replica identity; freeze migrations during the move
  and set sequences at cutover.
- Dual writes from the application are for cases replication cannot do (different data model,
  different system). They are not atomic: one write succeeds, the other fails, and the stores
  drift. Keep one side authoritative, write it first, write the other asynchronously through an
  outbox, and run a reconciliation job that compares and repairs; cut over only after it reports
  zero drift for days.
- Shadow traffic validates the new side under real load: mirror reads (or replay requests),
  compare results, log differences, and return only the old side's answer. Shadowed requests must
  not send email, charge cards or call third parties; stub side effects before mirroring writes.
- Move reads by percentage behind a flag, then writes. Keep reverse replication running for the
  rollback period so that going back stays lossless.

What cutover plans forget: webhook endpoints registered at providers, OAuth redirect URIs,
customer or partner IP allowlists for outbound traffic, email-sending DNS records, cron and
workers running on both sides at once, files in object storage, TLS certificates on the new side
before DNS moves, and resolvers that ignore TTLs (keep the old side serving or proxying until its
traffic is gone). Write the plan as a timed checklist with an owner and a customer notice.

## Ask the user

- **Is a short announced maintenance window acceptable for a migration or cutover?** It decides
  between a simple and a much more complex plan. Default: yes, at the quietest hour, announced.
- **How long may a bad release stay live before it must be rolled back?** Sets how much automation
  is needed. Default: automatic rollback on failed smoke tests; manual within 5 minutes otherwise.
- **When is nobody available to respond?** Defines deploy hours and freezes. Default: deploy in
  the founder's working hours, no risky deploys before time off.
- **Are there dates when a failure costs far more than usual** (launch, sales peak, a customer's
  event)? Default: none; freeze only around ones the user names.
- **Is there a test account and safe write path in production for smoke tests?** Default: create a
  dedicated test account excluded from analytics and billing.
- **Which old mobile app versions must keep working, and for how long?** Default: support every
  released version until usage data shows it is gone, then force upgrade.
