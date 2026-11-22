# Capacity and scaling

Read this when: asking whether the system survives growth or a traffic spike, removing single
points of failure, adding a second instance or a second zone, or configuring autoscaling.

## Before adding hardware

Capacity problems in small products are usually one inefficiency, not a lack of machines. In
order of cost, cheapest first:

1. Put static and cacheable responses behind the CDN, so the traffic never reaches the app
   (`0x:web-networking`).
2. Fix the slowest queries and missing indexes; one sequential scan on a hot path uses more
   database than everything else combined (`0x:postgres-database`).
3. Move slow work (email, exports, third-party calls, image processing) out of the request into
   background jobs.
4. Put a connection pooler in front of Postgres.
5. Then scale up. Then scale out.

## Scale up or scale out

| Scale up (bigger instance) when | Scale out (more instances) when |
|---|---|
| The bottleneck is the database: a larger plan is one click and no architecture change | Redundancy is needed anyway: two instances are an availability decision before a capacity one |
| The workload is not yet stateless | The process cannot use more cores |
| Traffic is steady | Traffic is spiky and instances can be added and removed |
| The next size up costs roughly proportionally | The largest practical size is reached, or price per unit jumps |

Decision rules:

- **Database: scale up for a long time.** A single well-indexed Postgres on a large instance
  serves far more than most products ever reach. Read replicas add lag and routing logic;
  sharding is a rewrite. Reach for them only with measurements (`0x:postgres-database`).
- **Node app servers: scale out, not up.** One Node process executes JavaScript on one core. An
  instance with eight cores runs one busy core and seven idle ones unless several processes are
  started. More small instances (or one process per core) is the unit of scaling; a bigger
  instance only helps with memory.
- **Workers: scale out by queue**, with concurrency per worker limited by what the database and
  the third-party rate limits accept, not by CPU.
- Scaling up usually needs a restart; with one instance that is downtime, with two it is a
  rolling change. This is one more reason the second instance comes first.
- Compare the monthly price of the bigger plan with a day of engineering time. Paying for
  headroom is often the correct decision at Launch; optimization is for when the bill or the
  ceiling is real.

## Two or more instances behind a health-checked load balancer

A second instance is useless, or harmful, until the app is stateless. Check before adding it:

| State on the instance | Symptom with two instances | Move it to |
|---|---|---|
| In-memory sessions | Users randomly logged out | Signed cookie or the database |
| Uploaded files on local disk | Files missing on half the requests | Object storage |
| In-process scheduled jobs | Every job runs twice: double emails, double charges | One scheduler, or a database lock or the queue's scheduler |
| In-memory cache or rate limiter | Limits are per instance, stale data differs per request | Redis or the database, or accept and document |
| WebSocket or SSE fan-out | Messages reach only clients on the same instance | A pub/sub backplane |
| Migrations run at app start | Two instances migrate concurrently | A single release step before rollout |

Health checks:

- The load balancer's check is **shallow**: the process is up and can answer. If it queries the
  database, a database blip removes every instance at once and the load balancer serves errors
  where a slow page would have done. Deep checks belong to external monitoring.
- Separate **readiness** (send me traffic) from **liveness** (restart me). Failing liveness on a
  dependency problem produces restart loops that add load to the struggling dependency.
- Typical settings: check every 5 to 10 seconds, 2 to 3 failures to remove, 2 successes to add.

Shutdown and connection handling, which cause most of the 502s seen during deploys:

```ts
let ready = true;                  // the readiness endpoint returns 503 once this is false
server.keepAliveTimeout = 65_000;  // must exceed the load balancer's idle timeout
server.headersTimeout = 66_000;    // must exceed keepAliveTimeout

process.on("SIGTERM", () => {
  ready = false;
  setTimeout(() => {               // first let the balancer stop sending
    server.close(() => process.exit(0)); // finish in-flight requests; flush telemetry before exit
  }, 10_000);
});
```

Older Node releases default `keepAliveTimeout` to 5 seconds, shorter than a typical load
balancer idle timeout (60 seconds on an AWS ALB unless changed); the balancer then reuses a
connection the app has just closed and returns 502. Newer Node releases raised the default, so
print `server.keepAliveTimeout` on the version in use, read the balancer's real idle timeout,
and set the app's value above it explicitly either way. Next.js does not expose the server
object: use `next start --keepAliveTimeout 65000`, or for the standalone server the keep-alive
environment variable named in the docs of the version in use.

On shutdown, fail readiness first, wait for the balancer to stop sending, finish in-flight
requests, then exit. The 10-second wait is a starting value: it must cover the balancer's
check interval times its failure threshold, and the wait plus the longest request must fit
inside the platform's termination grace period, or the process is killed mid-request.

Sizing: with N instances, plan for N minus one. Two instances must each be able to carry the
whole peak, so each runs under 50 percent of its capacity at peak; with three, under about 65
percent. Capacity here is the load-tested knee, not 100 percent CPU: a survivor running at its
limit is already slow.

Connections: instances times pool size, plus workers, plus migrations and admin tools, must stay
under the database's connection limit with a reserve. This sum is what breaks first when
instances are added. Use a pooler (PgBouncer or the provider's) before raising instance counts.

## Measuring headroom and finding what saturates first

Headroom is peak demand against the limit of the tightest component. Build this table from a
week of production metrics at the peak hour:

| Component | Limit | At peak | Watch for |
|---|---|---|---|
| App CPU per instance | One core per Node process | % of that core, event-loop delay | An average across cores hides a saturated single core |
| App memory | Instance or container limit | Peak resident size | OOM restarts |
| Database CPU and IO | Plan vCPU, IOPS, burst credits | Peak %, credit balance | Burstable plans that run out of credits mid-spike |
| Database connections | Server maximum | Peak in use, pool wait | See above |
| Queue workers | Jobs per minute at current concurrency | Age of oldest job | |
| Platform limits | Concurrent executions, request duration, bandwidth, build minutes | Current against quota | Soft quotas that need a support ticket and days to raise |
| Third parties | Email sends per hour, payment API rate limit, LLM tokens per minute | Peak use | They fail like outages and cannot be scaled by spending on your side |

Method:

1. From metrics, take peak request rate and each component's utilization at that moment.
   Linear extrapolation gives a first estimate of the multiple of current peak the system holds.
2. The estimate is optimistic: response time rises sharply well before 100 percent utilization,
   often from around 70 to 80 percent (a rule of thumb), and locks and pool waits are not linear
   at all.
3. Verify with a load test on a production-like environment, ramping until p95 latency bends
   upward or errors start. The component that is saturated at that knee is the bottleneck; the
   rate at the knee is real capacity (`0x:web-performance`).
4. Fix or enlarge that component, then repeat: the bottleneck moves.

Expect the first limit to be database connections, one slow query, or a third-party rate limit,
rather than app CPU. Target at Launch: normal peak uses no more than half of measured capacity
with one instance down.

## Autoscaling

Autoscaling handles gradual and daily variation. It does not handle a step spike that arrives
faster than new instances start, and it cannot scale the database.

| Setting | Default | Reason |
|---|---|---|
| Minimum | 2 | Redundancy, and capacity while new instances start |
| Maximum | What the database connection limit and the budget allow | An unbounded maximum turns a retry storm or an attack into a bill and a database outage |
| Metric | CPU target 50 to 60 percent for CPU-bound services; concurrent requests per instance for IO-bound ones; queue age for workers | CPU stays low on a service that is waiting on a slow dependency, so it never scales |
| Scale out | Fast: react within a minute or two, add several at once | Under-capacity costs users |
| Scale in | Slow: stabilization of 5 to 10 minutes, remove one at a time | Prevents flapping and dropped capacity between bursts |
| Readiness gate | New instances take traffic only after passing readiness | Otherwise cold instances serve errors |

Traps: startup time bounds reaction time (an instance that takes three minutes to become ready
cannot absorb a one-minute spike, so shorten startup or keep more warm); scale-in must drain
connections and let in-flight work finish; scaling on a metric that scaling does not improve
(database-bound latency) adds instances that add connections that make it worse; scale-to-zero
saves money and adds cold starts and should not sit on a paid user path; serverless concurrency
multiplies database connections without a pooler or an HTTP-based driver.

Alert when the group sits at maximum for more than a few minutes: at that point autoscaling has
stopped being the answer. Test it once with generated load and watch instances join and leave.

## Dependency map and single points of failure

List everything a request, a payment and a deploy depend on, including what is easy to forget:
DNS provider, registrar, CDN, TLS issuance, load balancer, app, database, cache, queue, object
storage, auth provider, payment provider, email, feature-flag service, secrets store, CI,
container registry, and the people with access.

| Component | If it fails | Redundancy now | Recovery time | Decision |
|---|---|---|---|---|
| (one row each) | What users see | None, standby, multi-zone, fallback | Measured or guessed | Remove, soften, or accept |

Three ways to treat each:

- **Remove**: add redundancy (second instance, database standby, second DNS provider).
- **Soften**: turn a hard dependency into a soft one with a timeout and a fallback. A
  feature-flag service that is down should yield default values, not a failed page; a failed
  analytics call should never fail a request; a failed email send should queue.
- **Accept**, written down with the expected downtime, when the fix costs more than the outage.
  A single payment provider is usually accepted at Launch.

Order the work by likelihood times impact, not by elegance. At Launch the typical list is: one
app instance, a database with no standby, scheduled jobs on one host, secrets known to one
laptop, and one person with access. Vendors, accounts and people are in `disaster-recovery.md`.

## Across availability zones

A zone is a data center; zone failures are the realistic infrastructure outage, far more common
than region failures.

- **App**: instances in at least two zones, preferably three, so losing one loses a third of
  capacity rather than half. The surviving zones must carry the peak.
- **Database**: the managed service's high-availability option, with a standby in another
  zone and automatic failover. Check two things with the provider: whether replication to the
  standby is synchronous (if not, a failover can lose the last commits) and the stated failover
  time, typically a minute or two. Existing connections break: the app must connect through the
  provider's endpoint (not an instance address), and the pool must discard dead connections and
  retry.
- **Everything else in the path**: cache, queue, load balancer and NAT each need to be
  zone-redundant, or the app survives and still cannot serve.
- **Test it**: trigger the provider's manual failover in staging, then in production at a quiet
  hour while watching error rate. Until then the failover is a hope. Record how long writes
  failed and whether the app recovered without a restart.
- **On a PaaS**: find out whether instances are spread across zones and which database plan
  includes a standby; the entry-level plans usually have neither.

Cost: on the large clouds a standby about doubles the database price, plus cross-zone traffic;
other providers price it differently, so check. Take the
database standby once revenue depends on the product (Launch); a backup-only database means an
outage of restore duration, typically hours.

## Preparing for a known spike

Launch day, a campaign, a newsletter feature, a seasonal peak. Autoscaling is not the plan; the
plan is to be scaled before it starts.

| When | Do |
|---|---|
| Two weeks before | Estimate the peak: expected visitors in the peak hour, pages and API calls per visit, then double it. Load test to two or three times the estimate. Fix the first bottleneck and repeat |
| Two weeks before | Request quota increases now: cloud instance quotas, email sending limits, payment and LLM rate limits can take days and need justification |
| One week before | Make the landing page static and CDN-cached so the crowd never reaches the app; only sign-up and checkout should hit the origin |
| One week before | Prepare degradation switches: flags to disable expensive features, a queue or waitlist for sign-ups, a static fallback page |
| Days before | Tell vendors whose fraud or abuse systems react to sudden volume (payment provider, email provider) |
| 24 to 48 hours before | Freeze deploys and migrations. Scale up the database (needs a restart) and scale out the app to the tested level |
| The day | Someone watches the dashboard for the whole peak with the runbook open; status page and support ready |
| After | Scale back down on a set date; write down actual peak against estimate for next time |

What breaks in practice: sign-up email (sending limits and warm-up, see
`0x:email-notifications`), database connections, one unindexed query that was fine at low
volume, a third-party script on the landing page, and the founder deploying a fix mid-spike.

## Forecasting capacity

Do this quarterly at Scale; at Launch, a glance at storage growth is enough.

1. **Find the load unit**: per active customer or per tenant, measure requests per day, rows and
   bytes added per month, jobs per day, and third-party calls. Averages hide the heavy tail, so
   also take the largest tenant: one enterprise customer can equal hundreds of small ones.
2. **Project demand**: customers over the next two to four quarters times load per customer,
   plus the pipeline's known large accounts.
3. **Compute time-to-limit per resource** from the headroom table. Storage and row counts only
   grow; treat them separately from request load.
4. **Compare with lead time**: a plan upgrade takes minutes, a quota increase days, partitioning
   a large table or splitting a service months. Start the work when time-to-limit is less than
   about twice the lead time.
5. **Watch for superlinear costs**: queries that scan growing tables, fan-out per follower or
   per member, per-tenant cron loops, backups and restores whose duration grows with size
   (restore time is part of RTO).

Tie the same per-customer figures to cost per customer (`0x:cloud-infrastructure`,
`0x:pricing-monetization`): a customer whose load costs more than the plan pays is a pricing
problem that capacity work cannot fix.

## Ask the user

- **What traffic is expected, and when?** Launch dates, campaigns, press, seasonal peaks.
  Default: plan for three times the current peak with no dated event.
- **What is the monthly infrastructure budget ceiling?** Sets the autoscaling maximum and
  whether to buy headroom or optimize. Default: allow doubling the current bill at peak, capped.
- **If the system must shed load, what goes first?** Which features may be turned off or queued
  under pressure. Default: protect sign-in and checkout; degrade exports, search and
  recommendations.
- **Is a few minutes of downtime for a database resize acceptable, and when?** Default: yes, in
  the quietest hour, announced on the status page.
- **Are large customers about to be onboarded?** One big tenant changes the forecast more than a
  quarter of organic growth. Default: none known; re-check when a deal is in contract.
