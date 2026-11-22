# Choosing where to run

Read this when: deciding or revisiting the hosting model, provider or region for a product or for one workload; or when someone asks "should we move off X" or "should this be serverless".

## First: what already exists

Check the repo before recommending anything: `vercel.json`, `fly.toml`, `render.yaml`, `railway.json`, `Dockerfile`, `config/deploy.yml` (Kamal),
`*.tf`, `serverless.yml`, `wrangler.toml` or `wrangler.jsonc`, `netlify.toml`, `Procfile`, Helm charts. A working platform is worth more than a
better one. A migration typically costs a solo founder one to four weeks of attention (rule of thumb) and produces no customer-visible value, so
recommend one only when a named limit is being hit (see "Signals to move"), not on taste.

## Hosting model by stage

| Model | Examples | Pick it when | Operating burden | Leaves you when |
|---|---|---|---|---|
| Frontend-centric PaaS | Vercel, Netlify, Cloudflare Pages/Workers | Next.js-style app, request/response work, no long-running processes | Near zero | Long jobs, websockets, heavy compute, usage-priced bill grows faster than revenue |
| Container PaaS | Railway, Render, Fly.io | App plus workers plus cron plus managed Postgres in one place | Low | Private networking or compliance needs, per-GB RAM price at larger sizes |
| Managed containers on a cloud | Google Cloud Run, AWS ECS on Fargate (Express Mode is its low-configuration entry), Azure Container Apps | Need the cloud's VPC, IAM, managed data services, or enterprise customers ask where data lives | Medium: IAM, networking and IaC are now yours | Rarely; this scales a long way |
| One or a few VPS | Hetzner, DigitalOcean, OVH with Kamal or Coolify | Cost-sensitive, steady load, comfortable with a server, or needs big RAM/CPU cheaply | Medium: patching, backups, monitoring are yours | Need multi-zone availability or many services |
| Kubernetes (managed) | EKS, GKE, AKS | Many services, several engineers, at least one person whose job includes the cluster | High, and continuous | n/a |

Check a platform's status before recommending it for a new project. Two changes from 2026: Heroku moved to maintenance-only engineering (keep an
existing app there; do not start one), and AWS App Runner closed to new customers (AWS points to ECS Express Mode instead).

Default path: **Prototype** on a PaaS. **Launch** on the same PaaS unless a signal below fires. **Scale** on managed containers in one cloud, with
managed Postgres. Kubernetes is not a stage on this path; it is a choice a team makes when it has roughly ten or more services or needs something only
the Kubernetes ecosystem provides (operators, custom scheduling, portability across clouds for a contract), and has someone to upgrade it three times
a year.

A VPS with Kamal is a legitimate Launch choice, not a step backwards: it is the cheapest way to run a steady workload and avoids usage-priced surprises. Its cost is paid in attention: patching, backups, disk-full pages. Choose it when the founder has run a Linux server before; otherwise the PaaS premium is the cheapest operations hire available.

### Signals to move

| Signal | Move to |
|---|---|
| PaaS bill above roughly what one mid-size cloud VM plus managed DB would cost, three months running, and growing | Managed containers or VPS; calculate first (below) |
| Need jobs longer than the platform's function limit, websockets, or a persistent process | Add a container PaaS or one container service for that workload only; keep the rest |
| A customer contract requires VPC peering, private link, a specific region, or audit evidence the PaaS cannot give | Managed containers in a hyperscaler |
| Database must be private and the PaaS cannot reach it privately | Managed containers in the same cloud as the database |
| Cold starts or per-request limits are hurting a core path | An always-on container for that path |
| "We might need to scale" | Nothing. Stay. |

Move one workload at a time. A common stable shape at Launch is a frontend PaaS for the web app plus one container service for workers and websockets, both in the same region as the database.

### Kubernetes: the honest test

Say yes only if all hold: more than a handful of independently deployed services; someone on the team has operated a cluster through a version
upgrade; a managed control plane is used; and the alternative (ECS, Cloud Run) was considered and found missing a specific capability. "Avoids
lock-in" is not such a capability for a small team: Kubernetes replaces lock-in to a cloud's simple API with lock-in to a large body of YAML,
controllers and operational habit.

## Workload unit: container, function, isolate or VM

Decide per workload, not per product.

| Workload | Unit | Why |
|---|---|---|
| Web app and API, steady or growing traffic | Always-on container (or the PaaS's function runtime if already there) | Warm, pooled DB connections, predictable cost |
| Spiky or rare endpoints, webhooks receivers, glue between services | Function | Scale to zero; cost follows use |
| Redirects, header and cookie logic, auth token checks, geolocation, A/B bucketing, cache-key shaping | Edge isolate | Runs before origin, starts in milliseconds; no heavy CPU, limited APIs |
| Queue workers, cron longer than a function limit, video or PDF processing, websockets | Container | No time limit, full runtime, holds connections |
| Databases you run yourself, GPU inference, software needing a kernel module, license-bound software | VM | Needs stable disk, hardware or kernel control |
| CI builds, batch jobs that can restart | Spot or preemptible containers/VMs | Large discount for tolerating interruption |

Rules that settle most cases:

- Anything that holds a connection (websocket, database pool, queue consumer) belongs in a container.
- Anything that must finish (a payment webhook's processing, an export) should not depend on a function staying alive after it responds; enqueue it. See `serverless-edge.md`.
- Put compute in the same region as its database before optimizing anything else. One cross-region query per request costs more latency than any edge trick wins back.
- One container image used for web, worker and cron (different commands) is simpler than three build pipelines.

## Storage: block, file or object

| Data | Storage | Notes |
|---|---|---|
| User uploads, generated files, exports, backups, static assets, logs archives | Object (S3, R2, GCS) | Default for any blob. Serve through a CDN or signed URLs. Details: `0x:data-stores` `object-storage.md` |
| Database files, a search index, anything needing low-latency random writes | Block volume attached to one instance | One writer. Zonal: a volume cannot follow an instance to another zone. Snapshot it |
| Legacy app that expects a shared POSIX directory across instances | Network file (EFS, Filestore) | Last resort. Slow on many small files, priced high per GB, latency per operation. Rewrite to object storage when possible |
| Scratch during a request or job | Container's ephemeral disk or `/tmp` | Gone on restart; size-capped on functions; never the only copy |

Traps: writing uploads to the container's local disk works on one instance and loses files on the first deploy or second instance. SQLite on a network
file system corrupts or crawls; SQLite needs a block volume and a single writer (and a replication tool such as Litestream for backup). Object storage
is not a file system: no atomic rename, no append, list operations are slow and billed; design keys so that listing is rarely needed.

## Regions

Order of decisions:

1. **Legal and contractual constraints first.** If customers or regulation require data to stay in a jurisdiction (EU, UK, Australia, Canada, India and
   others each have their own rules or customer expectations), pick a region there. Residency (where bytes are stored) is different from sovereignty
   (whose law can compel access): an EU region of a US provider satisfies most residency clauses but not a strict sovereignty requirement, which calls
   for an EU-headquartered provider or a sovereign cloud offering. Which applies is a legal question; ask the user what their contracts say and suggest
   counsel if a regulated sector is involved.
2. **Database region = where most users are.** Everything else follows the database.
3. **Compute in the same region as the database**, including the PaaS functions region. Platforms default to a US region; check it explicitly.
4. **Check what else stores data**: logs, error tracker, analytics, email provider, LLM API, backups. A residency promise covers all of them, not only the database. Transfer rules and the sub-processor list itself are in `0x:privacy-compliance`.

Other region rules: choose a large, old region over a new one (more services, more capacity, fewer quota surprises); prices differ by region by a
noticeable margin, so compare before choosing between two acceptable ones; stay in one region until Scale. Multi-region active-active is a database
problem first and is rarely justified before a contractual uptime commitment demands it; multi-zone within one region is the right availability target
at Launch. Disaster recovery design belongs to `0x:site-reliability`.

A CDN in front solves global latency for static and cacheable content without multi-region compute. For dynamic, per-user responses from far-away users, measure first: 150 to 250 ms of added round trip is noticeable on chatty pages and tolerable on well-batched ones.

## When per-request pricing loses to always-on

Serverless bills for each request's wall-clock duration times allocated memory, including time spent waiting on the database or an API. A container bills for existing, and multiplexes many concurrent I/O-bound requests in one process. That difference, not the per-request fee, decides the break-even.

Method:

```text
function cost / month  = R × (price_per_request + D × M × price_per_GB_second)
                         + gateway fee per request, if an API gateway fronts it
container cost / month = N × hourly_price × 730
  where N = max(2 for redundancy, peak_concurrent_requests / concurrency_per_instance)
R = requests per month, D = average duration in seconds, M = memory in GB
```

Worked example with illustrative Lambda-style list prices (take current ones from the provider's calculator): 10 million requests a month, 200 ms
each, 512 MB. Compute charge is 10M × 0.2 s × 0.5 GB = 1M GB-seconds; at about $0.0000167 per GB-second plus about $0.20 per million requests this
is roughly $19 a month before any gateway fee. Ten million requests a month is under 4 requests per second on average, which one small container
handles; two of the smallest instances, for redundancy, cost a similar amount. So for this profile both options cost about the same at 10 million
requests and the containers win beyond it: at 100 million requests the function bill is ten times larger and the container count has perhaps
doubled.

Rules of thumb:

- Below about a million requests a month, functions are effectively free and the comparison is not worth making.
- Sustained traffic with average utilization above roughly 20 to 30 percent of an always-on instance favors the container.
- Slow requests (LLM calls, streaming, long upstream waits) hit the break-even far earlier, because the function bills for the whole wait. Platforms
  that bill active CPU or allow multiple concurrent requests per instance (Cloud Run concurrency, Vercel's concurrent function model, Cloudflare Workers
  CPU-time billing) change this substantially; check which billing model the platform uses before calculating.
- An API gateway in front of functions can cost more per request than the functions do. Include it.
- Include the non-compute lines on frontend PaaS: bandwidth, image optimization, build minutes, per-seat fees. They are often the larger part of the bill.

## Lock-in and exit cost

Lock-in is a price, not a sin. Estimate the exit in engineer-weeks and decide whether the service is worth that.

| Dependency | Exit cost | Guidance |
|---|---|---|
| Containers, Postgres, S3-compatible object storage, Redis protocol, SMTP, OIDC | Days | Standard interfaces; use freely |
| Managed queue, cron, secrets store, managed load balancer | Days to two weeks | Wrap in a thin module so call sites do not import the SDK directly |
| Platform KV, platform image optimization, platform-specific cache or ISR behavior, build system conventions | Weeks | Fine at Prototype; write down each one adopted |
| Proprietary database with its own data model and query API (DynamoDB, Firestore, Durable Objects, Spanner-specific features) | Months: data model, queries and consistency assumptions all change | Adopt only for a capability Postgres lacks at the needed scale |
| Auth provider holding password hashes | Weeks, plus user friction if hashes cannot be exported | Confirm hash export before adopting; see `0x:auth-identity` |
| Proprietary workflow or state-machine definitions, vendor-specific IAM woven through code | Months | Keep business logic in plain code that the workflow calls |

Before adopting a proprietary service, answer in writing: can the data be exported in bulk in a standard format, and has it been tried once? Is there
a second implementation of the interface (an S3-compatible store, a Postgres-compatible host)? What is billed on exit (egress per GB is the usual exit
tax; the large clouds waive it for departing customers on application and with conditions, so read the current terms)? What is the smallest
wrapper that keeps the SDK out of business logic?

Do not pay for portability that will not be used: a "cloud-agnostic" abstraction layer over three clouds costs more than the migration it insures against. The exception is data: keep it in formats and engines that exist elsewhere.

## Cloud, bare metal or colocation

| Option | Makes sense when | Risk carried |
|---|---|---|
| Hyperscaler | Default at Launch and Scale. Managed data services, IAM, compliance reports, elasticity | Price, egress fees, complexity |
| Budget cloud or rented dedicated servers (Hetzner, OVH) | Steady compute-, RAM- or bandwidth-heavy workload; price-sensitive product; team can run Postgres or accepts a separate managed DB | Fewer managed services, hardware failure means a rebuild, fewer regions, thinner compliance paperwork |
| Colocation, owned hardware | Rule of thumb: a cloud bill in the high six figures (USD) a year with a flat, predictable base load, and staff to run it | Capital outlay, lead times, hardware lifecycle, on-call for physical failure |

Rule of thumb: rented dedicated hardware is several times cheaper per core and per GB of RAM than hyperscaler on-demand, and bandwidth is cheaper by a
larger factor still. That saving is real only if the managed services being given up (database failover, backups, load balancers, zonal redundancy)
are either unnecessary or rebuilt and operated, and operating them is someone's time. Before a solo founder leaves a hyperscaler for cost, exhaust the
cheaper moves first: rightsizing, commitments, ARM instances, removing NAT and egress waste (`cost-control.md`).

A hybrid that works for small teams: stateless compute on cheap servers, database on a managed service in a nearby region of the same metro, object storage on a zero-egress provider. Measure latency between them before committing; cross-provider traffic crosses the public internet and is billed as egress on the managed side.

## Ask the user

- **What do customer contracts or regulators say about where data is stored?** Decides region and sometimes provider. Default if unknown: the region nearest most users, in the user's own jurisdiction when in doubt, with all sub-processors listed so the question can be answered later.
- **Who will be woken when the server is down, and have they run a Linux server before?** Decides PaaS versus VPS. Default: PaaS.
- **What is the monthly infrastructure budget now, and what would be alarming?** Sets whether cost optimization is worth any attention. Default: optimize nothing until the bill exceeds a few percent of revenue or a fixed amount the user names.
- **Is there traffic that is predictable and steady, or mostly spikes and quiet?** Decides always-on versus per-request. Default: assume steady for the main app, spiky for webhooks and admin tools.
- **Are cloud credits in play, and when do they expire?** Credits make an expensive architecture look free. Default: design for the bill after credits end.
- **Is an enterprise customer or a compliance audit expected within a year?** Favors a hyperscaler with private networking and audit reports. Default: no; stay on the PaaS.
