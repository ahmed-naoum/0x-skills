# Load testing

Read this when: the question is how much traffic the system can take, what breaks first, whether
a launch or campaign will hold, or how to keep endpoint performance from regressing.

## Is a load test worth running now

A load test costs a day or more to do properly and produces a number that is only as good as
the traffic model. Decide before writing a script.

| Stage and situation | Decision |
|---|---|
| Prototype | Skip. There is no traffic to model and the architecture will change |
| Launch, organic growth, no known spike | Skip the full test. Do a 30-minute smoke and ramp on the three most expensive endpoints to catch gross problems (N+1, missing index, pool of 5), and set up per-endpoint latency tracking instead |
| Launch with a dated spike: press, product launch day, a large email send, a sale, a ticket drop, a demo to a big customer | Test. The date is fixed and failure is public |
| A contract or enterprise customer states a capacity or latency requirement | Test, and keep the report |
| A change to the data layer, queue, pooling or hosting model | Test before and after with the same script |
| Scale | Routine: before each peak season and on a schedule, with a reduced version in CI |

Cheaper questions to answer first, which often remove the need: what is the peak request rate
today and the realistic multiple expected; is the page cacheable at the CDN (then the origin
sees little of the spike); what are the hard limits already known (database connection limit,
serverless concurrency limit, third-party rate limits, plan quotas). A spike of anonymous
readers on a CDN-cached page is a caching task, not a load-testing task.

Capacity planning, autoscaling policy and SLOs belong to `0x:site-reliability`; this file is
about producing the measurement.

## A k6 test that finds the saturation point

Default tool: k6 (scripts in JavaScript, one binary, thresholds as pass or fail). The decision
that matters most is the workload model:

- **Closed model** (a fixed number of virtual users, each waiting for its response before
  sending the next request): when the server slows down, the test sends less. It hides overload,
  and the latency it reports is too optimistic. Fine for smoke tests and for modeling a fixed
  group of users.
- **Open model** (requests arrive at a set rate regardless of how the server is doing): this is
  how internet traffic behaves and what capacity questions need. In k6, the arrival-rate
  executors.

```js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-arrival-rate',
      startRate: 10, timeUnit: '1s',            // iterations per second
      preAllocatedVUs: 200, maxVUs: 2000,
      stages: [
        { target: 50, duration: '3m' },  { target: 50, duration: '5m' },
        { target: 100, duration: '3m' }, { target: 100, duration: '5m' },
        { target: 200, duration: '3m' }, { target: 200, duration: '5m' },
      ],
    },
  },
  thresholds: {
    http_req_failed: [{ threshold: 'rate<0.05', abortOnFail: true, delayAbortEval: '30s' }],
    'http_req_duration{name:product}': ['p(95)<500'],
  },
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  const id = 1 + Math.floor(Math.random() * 50000);
  const res = http.get(`${__ENV.BASE_URL}/api/products/${id}`, { tags: { name: 'product' } });
  check(res, { 'status is 200': (r) => r.status === 200 });
}
```

```bash
k6 run -e BASE_URL=https://staging.example.com ramp.js
```

What makes the result trustworthy:

- **Step and hold.** Ramp to a level, hold it for several minutes, then step up. Latency read
  during a ramp mixes levels; the plateau is the measurement.
- **Tag requests by name.** URLs with ids otherwise create one metric series per URL.
- **Check the response, not only the status.** An error page with status 200, or a cached
  "rate limited" body, passes a status check.
- **Watch `dropped_iterations`.** Non-zero means the generator could not start iterations at
  the requested rate (out of virtual users or out of generator CPU): the system under test or
  the generator is saturated. Check generator CPU and network before concluding anything.
- **Run the generator elsewhere.** Not on the machine under test, and not from a laptop on home
  internet for anything beyond a smoke test. Use a VM in the same region or the vendor's cloud
  runners; test through the same entry point users use (CDN and load balancer included) unless
  the aim is to isolate the origin.
- **Abort on high error rates.** The `abortOnFail` threshold stops the test before it turns
  into an outage of the test environment.

**The saturation point** is the arrival rate at which the system stops keeping up: throughput
stops rising with offered load, latency turns from flat to steeply rising, errors and timeouts
begin, queues grow without draining. Below the knee latency is nearly flat; that flat region is
the usable capacity. Report three numbers: the highest rate at which the latency target still
holds, the rate at the knee, and the expected peak. Rule of thumb: the first should be at least
twice the expected peak for a dated event, because the traffic estimate is the weakest input.

## Model realistic traffic

A test that hammers one URL measures the cache. What to model, and where to get it:

| Element | Source | What goes wrong without it |
|---|---|---|
| Request mix (share of each endpoint, read to write ratio) | Access logs or APM for the busiest hour | Capacity looks ten times higher because the cheap endpoints dominate, or the expensive write path is never exercised |
| User journeys (login, browse, search, add, checkout) | Product analytics funnels | Session, auth and per-user data paths go untested |
| Think time between steps | Analytics, or a few seconds with randomness | In a closed model, zero think time turns 100 users into an unrealistic flood; in an open model, it distorts connection reuse |
| Data variety (which ids, search terms, accounts) | Sample from production keys with realistic skew: some items hot, a long tail cold | Every request hits the same cached row; the database's buffer cache and the CDN make everything look instant |
| Authenticated share | Analytics | Logged-in requests bypass shared caches and are several times more expensive |
| Payload sizes | Logs | Uploads and large responses stress different limits |
| Ramp shape and peak-to-average ratio | The event: an email send arrives within minutes, organic peaks build over an hour | Autoscaling and cold caches behave completely differently on a step than on a slope |
| Client connection behavior | Many clients with few requests each, not few connections with many | TLS handshakes, connection limits and load-balancer behavior go unmeasured |

Practical rules: load test data from a file with `SharedArray` so virtual users do not each hold
a copy; create test users and tokens in `setup()`, not inside the measured iterations (login is
deliberately slow because of password hashing and will dominate otherwise, unless the login
spike is the scenario); weight scenarios to the measured mix using several named scenarios with
their own rates. Start caches cold for one run and warm for another; a deploy or purge in the
middle of a spike is the cold case.

## Find the first bottleneck

During each plateau, watch the system's metrics, not only k6's. The first resource to saturate
sets capacity; everything behind it is still idle.

| Observation while latency rises | First bottleneck | Next step |
|---|---|---|
| App CPU near 100% on all instances | Application compute | CPU profile (`backend-latency.md`); more or larger instances |
| One Node process at 100% of one core, others idle | Single-threaded event loop | More instances or processes; move CPU work out |
| App CPU low, database CPU high | Queries | `pg_stat_statements` during the test, then `0x:postgres-database` |
| App and database CPU both low, latency high | Waiting: connection pool, locks, downstream service, rate limit | Pool wait time, lock waits, outbound spans |
| Errors mention too many connections, or pool timeouts | Connection limit | Pooler, smaller per-instance pools, shorter transactions |
| Database I/O wait high, memory full | Working set no longer fits in memory | More memory, better indexes, less data touched per query |
| Queue depth grows and does not drain | Workers | More workers, or the job is too slow |
| 429 or 503 from the edge or platform | Platform concurrency or rate limit, WAF | Raise the limit, or allowlist the test |
| Latency rises only after autoscaling starts | Cold starts and scale-out lag | Minimum instances; scale earlier |
| Memory climbs steadily until restart | Leak | Soak test and heap snapshots |
| Throughput flat, everything idle | The load generator | More generator capacity |

After fixing the first bottleneck, rerun: the next one appears at a higher rate. Stop when the
target with headroom is met; chasing further bottlenecks is work for a need that may never come.
Write down which resource is the limit and at what rate; that is the input capacity planning
needs.

## Test types and what each reveals

| Type | Shape | Reveals | Run when |
|---|---|---|---|
| Smoke | Minimal load, a minute or two | The script and environment work | Before every other test |
| Load | Expected peak, held 15 to 60 minutes | Whether targets hold at the planned level | Before a dated event |
| Stress or breakpoint | Stepped increase past the expected peak until failure | The knee, the first bottleneck, and how it fails: gracefully (shed load, clear errors) or by collapse | When capacity is unknown |
| Spike | Jump to several times normal within seconds, hold briefly, drop | Autoscaling lag, cold starts, connection storms, cache stampedes, whether the system recovers on its own afterward | Before sends, drops and launches |
| Soak | Moderate load (around 70 to 80% of capacity) for hours | Memory leaks, connection and file-handle leaks, disk filling with logs, tables or queues growing without bound, token and certificate expiry, slow degradation | Before relying on long uptimes; after changes to pooling or caching |

Read recovery as carefully as the peak: after the load drops, latency and error rate must
return to baseline without intervention. A system that stays degraded (stuck connections, a
queue that never drains, retry storms keeping it down) has a worse problem than a low ceiling.

## Production-like data and infrastructure, without harm

The result transfers to production only as far as the test environment resembles it.

- **Data volume matters most.** Query plans change with table size; an index that is irrelevant
  at 10,000 rows decides everything at 50 million. Seed the test database to production scale
  with synthetic data of similar distribution, or use an anonymized copy. Copying real personal
  data into a test environment has privacy implications; see `0x:privacy-compliance`.
- **Same shape, smaller is acceptable; different shape is not.** The same database engine and
  version, the same pooling, the same number of hops. Results from a smaller instance class
  do not scale linearly; state that as a limit of the result.
- **Third parties.** Do not load test payment, email, SMS or AI providers through their real
  APIs: it violates terms, burns quota and money, and sends real messages. Stub them with a
  mock that responds with realistic latency and error rates. Sandbox modes have their own low
  rate limits.
- **Test only what the user owns or has written permission to test.** Load aimed at someone
  else's system is indistinguishable from a denial-of-service attack and can be unlawful as
  well as a breach of terms. That includes shared platforms: some hosting, CDN and
  DDoS-protection providers require notice or forbid load tests, so read the current terms
  first. Expect bot protection and rate limiting to block an un-allowlisted generator, which
  then measures the WAF.
- **Mind the bill.** On usage-priced platforms a load test is billable traffic: function
  invocations, bandwidth, database compute. Estimate before a long soak.

Testing in production is sometimes the only realistic option. Conditions: run off-peak; mark
test traffic with a header and a dedicated test tenant so it can be filtered from analytics,
excluded from billing and emails, and deleted afterward; ramp slowly while watching real-user
error rate and latency; define the abort condition in advance and automate it; have the person
who can roll back present; never run destructive or money-moving flows against real accounts.
Read-only endpoints first.

## Regression checks in CI

Full load tests do not belong in the pull-request pipeline: shared runners are noisy, and
ephemeral environments are not production-shaped. What does work, in order of value:

1. **Query-count assertions in integration tests.** Assert that an endpoint issues at most N
   queries for a seeded dataset. Deterministic, fast, and catches the N+1 regression, which is
   the most common one. Do this from Launch.
2. **A short k6 run with thresholds against a preview or staging deploy,** nightly or on merge
   to main: a few minutes at a fixed modest arrival rate on the five key endpoints. k6 exits
   non-zero when a threshold fails, which fails the job.
3. **Comparison against a stored baseline** with a tolerance (for example fail when p95 is more
   than 20 to 30% worse than the trailing baseline on the same environment), not against an
   absolute number tuned for production.

Keep the environment fixed (same instance size, same seeded data, nothing else running), run
each check more than once before failing a build, and alert a person rather than block merges
until the check has proven stable for a few weeks. A flaky performance gate gets disabled, and
then there is none. Production percentile alerts per endpoint (`backend-latency.md`,
`performance-budgets.md`) remain the real safety net.

## Ask the user

- **What traffic is expected, and when?** The peak estimate drives everything. Default: take
  the current peak hour, multiply by the realistic uplift of the event, and test to twice that.
- **What counts as failure?** A latency target and an acceptable error rate. Default: p95 under
  500 ms and under 1% errors at expected peak.
- **Which environment may be loaded, and may production be tested off-peak?** Risk decision.
  Default: a short-lived production-shaped environment with seeded data (or staging where one
  exists, `0x:ci-cd-release`); production only read-only
  and with an owner present.
- **What is the budget for the test itself?** Environment, generator and usage costs. Default:
  a few hours of a production-sized environment, torn down afterward.
- **What should happen beyond capacity?** Shed load with a waiting page, degrade features, or
  scale and pay. Default: protect checkout and sign-in, shed or queue the rest.
