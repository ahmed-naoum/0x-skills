# Cloud cost control

Read this when: estimating infrastructure cost for a design, investigating a bill that jumped, or putting limits in place before spend can run away. Prices quoted are orders of magnitude from hyperscaler list prices in common US regions; take the current figure from the provider's calculator before using one in a decision.

## Day-one guardrails on every account

Do these before deploying anything; a leaked key or a loop can spend thousands in hours.

1. **Budget with alerts** at 50, 80 and 100 percent of the expected monthly figure, plus a forecast-based alert, delivered to an inbox and a chat channel people read. Set a second, low budget on accounts that should cost nearly nothing (sandbox, management).
2. **Anomaly detection** where the provider offers it free (AWS Cost Anomaly Detection): it catches a new line item days before a monthly threshold does.
3. **Understand what a budget is not.** On AWS, GCP and standard Azure subscriptions a budget is an alert, not a cap, and billing data lags by hours to a day. Nothing stops spending unless it is built: a GCP budget can publish to Pub/Sub and a function can detach billing (which stops every service in the project, production included); AWS budget actions can apply a deny policy or stop specific instances. Several PaaS and edge platforms do offer a real spend limit that pauses the project; turn it on at Prototype and decide deliberately at Launch whether an outage is better than the bill.
4. **Service quotas as a safety net.** Default quotas bound what a stolen credential can launch. Do not raise them "for later"; keep GPU and large-instance quotas at zero or minimal in accounts that do not use them, and restrict unused regions (`iam-accounts.md`).
5. **Caps on everything metered** (see "Hard maximums").
6. **Third-party meters too**: LLM APIs, SMS, email, maps, error tracking and log vendors each have their own budget or usage-limit setting. Set them the same day.

## Hard maximums that bound spend

For each resource, a worst-case monthly cost should be computable: maximum units × unit price × 730 hours. If a maximum is "unlimited", set one.

| Resource | Cap to set |
|---|---|
| Autoscaling groups, container services, Kubernetes node pools and pod autoscalers | Maximum instance or replica count; alert when at maximum for more than a few minutes |
| Functions | Maximum concurrency and a short timeout per function (`serverless-edge.md`) |
| Serverless databases and on-demand tables | Maximum capacity units or autoscale ceiling |
| Logs and metrics | Retention on every log group (30 days is a reasonable default; "never expire" is the provider default in places), sampling for debug-level logs, a daily ingestion cap where the vendor offers one. Custom metrics with high-cardinality labels (user ID, URL) multiply cost; forbid them |
| Queues and retries | Maximum receive count and dead-letter queue, so a poison message cannot loop |
| LLM and other per-call APIs | Provider-side monthly limit, plus per-user and per-tenant quotas in the application; abuse of a free tier is a cost attack |
| Public endpoints that trigger paid work (image resize, PDF, AI, SMS, email) | Authentication, rate limits and input size limits. SMS pumping fraud and scraping of an image optimizer are common causes of surprise bills |
| Bandwidth | CDN in front of large files; alarm on egress bytes |

Scaling policy itself belongs to `0x:site-reliability`; the rule here is only that every policy has a ceiling someone chose.

## Costs that designs forget

Compute and database sizes are what people estimate. These are what surprise them:

| Line | Order of magnitude | Design response |
|---|---|---|
| Internet egress from a hyperscaler | Around $0.05 to $0.12 per GB after a small free allowance | Serve downloads, media and static assets through a CDN or a zero-egress object store; compress; never proxy large files through the app |
| Cross-zone and cross-region transfer | About a cent per GB each way between zones; more between regions | Keep chatty services and their database in the same zone where possible; replicate deliberately |
| NAT gateway | A fixed hourly fee (tens of dollars a month each) plus a per-GB processing fee comparable to half the egress price, on traffic in both directions | Gateway endpoints for object storage, interface endpoints or public subnets for heavy flows; one gateway outside production (`cloud-networking.md`) |
| Load balancers, public IPv4 addresses, idle managed services | Each a fixed monthly fee | Share one load balancer; delete unused addresses |
| Log ingestion | Roughly half a dollar per GB ingested on cloud-native logging, more on observability vendors, plus storage and query | Log at info, drop health-check and static-asset access logs, sample noisy paths, set retention |
| Storage that only grows | Object storage is a couple of cents per GB-month; snapshots, old object versions, backups and container images accumulate without anyone deciding | Lifecycle rules from day one (below) |
| Per-request charges on storage and APIs | Tiny per call, large at volume (listing buckets in a loop, tiny objects by the million) | Batch, cache, avoid polling by listing |
| Secrets and keys | A small monthly fee per secret and per key | Do not create one per environment variable; group |
| Managed service premiums and support plans | Support is a percentage of the bill above a minimum | Decide deliberately |
| Frontend PaaS extras | Bandwidth, image optimization, function duration, build minutes, seats | Read the usage page, not just the plan price |

Quick egress check for a design: bytes per response × responses per month. A 2 MB page payload served 5 million times is 10 TB; at hyperscaler rates that is on the order of a thousand dollars a month uncached and close to nothing through a CDN plan that includes bandwidth.

## Estimating cost at 100, 10,000 and 1,000,000 users

Estimate from drivers, not from instance guesses. For each tier write down:

```text
active users × requests per user per day                 -> requests/s at peak (peak is 3-10× average)
active users × stored bytes per user (DB rows, files)     -> database size, object storage GB
requests × response bytes not served from CDN             -> egress GB
requests × log bytes per request                          -> log ingestion GB
metered calls per user (LLM tokens, emails, SMS, search)  -> third-party spend, usually the largest variable line
fixed floor: load balancer, NAT, smallest HA database, monitoring, CI
```

Shape to expect for a typical CRUD SaaS (order of magnitude only; AI-heavy, media-heavy or realtime products differ by multiples):

| Users | Architecture | What dominates | Rough monthly range |
|---|---|---|---|
| 100 | PaaS free or hobby tiers, smallest managed Postgres | The fixed floor; usage is noise | Zero to low tens of dollars |
| 10,000 | PaaS paid tier or two small containers, a managed database with a standby, CDN, error tracking and logs | Database, PaaS plan and per-seat tools, observability | Low hundreds of dollars |
| 1,000,000 | Several app instances behind a load balancer, a large primary with replicas and a pooler, cache, queue, CDN, proper observability | Database, egress, logs, and any per-user metered API | Several thousand to tens of thousands of dollars |

How to use the estimate:

- **Compute cost per user per month** at each tier and compare it with revenue per user. Infrastructure for a healthy SaaS is typically a single-digit to low-teens percentage of revenue (rule of thumb). A free tier whose marginal cost per user is not near zero needs a limit.
- **Find the line that does not flatten.** Compute and database cost per user fall with scale; per-call API spend, egress and logs do not. Those are the ones to design down.
- **Mark the steps.** Costs jump at thresholds (first standby replica, first NAT, next plan tier, enterprise SSO add-on). Name each step and the user count that triggers it.
- State every assumption next to the number; the estimate's value is that it can be corrected when the first real month's bill arrives.

## The monthly bill review

Thirty minutes, once a month, at Launch and after. Open the cost explorer grouped by service, then by usage type within the top services, at daily granularity.

1. List the top five line items. For each, write one sentence: what it is, what drives it, whether it grew faster than usage. An item nobody can explain is the finding.
2. Compare with last month by service; investigate anything up more than about 20 percent without a matching growth in traffic or customers.
3. Group by usage type, not only by service: "EC2-Other" hides NAT, volumes, snapshots and data transfer; "data transfer" may be most of a storage or CDN line.
4. Check each region and each account for spend that should be zero.
5. Record cost per active user or per request alongside the total, so growth and waste can be told apart.

When a bill has jumped: find the day it started in the daily view, the service and usage type that moved, then the resource (tag, resource-level view or the service's own metrics), then what changed that day (deploy, new feature, traffic source, a failing job retrying, a new log level). The usual culprits in order: data transfer or NAT after a new integration, logs after a debug flag or an error loop, a forgotten large instance or database, a retry or recursion loop, runaway autoscaling, a compromised key launching compute in an unused region.

## Orphans and idle resources

Things that bill while doing nothing: unattached volumes; snapshots and machine images of deleted instances; unassociated static IPs; load balancers with no targets; NAT gateways in dev accounts; stopped instances (their disks still bill); databases for abandoned experiments; preview environments and database branches never torn down; old container images; log groups with no retention; incomplete multipart uploads and noncurrent object versions; resources in regions nobody opens.

```bash
# Unattached volumes and unassociated addresses (repeat per region)
aws ec2 describe-volumes --filters Name=status,Values=available \
  --query 'Volumes[].[VolumeId,Size,CreateTime]' --output table
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==`null`].[PublicIp,AllocationId]' --output table
```

Method: start from the bill (every line maps to something that exists), not from the console. Use the provider's recommendations (AWS Compute Optimizer and Trusted Advisor, GCP Recommender, Azure Advisor) for idle findings. Before deleting: confirm ownership by tag, snapshot anything stateful, stop before terminating and wait a week when unsure. Prevent recurrence structurally: everything created by IaC with tags, preview environments with a time-to-live, a lifecycle rule on every bucket to abort incomplete multipart uploads after a few days and expire noncurrent versions, registry retention rules (`docker-images.md`), and a sandbox account that is wiped on a schedule.

## Tags and attribution

- Tag every resource with at least `environment`, `service` and `owner`, set once through the IaC provider's default tags. On AWS, tags must be **activated as cost allocation tags** in billing before they appear in cost reports, and they are not retroactive; do it on day one. Separate accounts per environment give the first split for free.
- Some spend cannot be tagged (data transfer, shared clusters, support). Allocate it proportionally and say so.
- **Per-customer cost** does not come from tags when tenants share infrastructure. Meter it in the application: requests, compute seconds, stored bytes, egress bytes and third-party calls (LLM tokens above all) per tenant, written to the analytics store; then multiply by unit costs derived from the bill. Purpose: find tenants whose cost exceeds their revenue, set plan limits and overage prices from data, and price enterprise deals. Start when one customer plausibly accounts for more than a tenth of a variable line. Billing on usage belongs to `0x:payments-billing`.

## Cutting spend, in order of return on attention

1. **Delete** what is unused (above). Free and immediate.
2. **Turn off non-production** outside working hours and shrink it; staging does not need production sizes or multi-zone.
3. **Fix the design leaks**: NAT and egress paths, log volume and retention, chatty cross-zone traffic, uncached assets.
4. **Rightsize**: look at two weeks of p95 CPU and memory. Sustained p95 under about 40 percent means one size down; the database is usually the largest and most oversized item, but check memory and connection headroom before shrinking it. Move general-purpose volumes to the current generation type, and move to ARM instances where the stack allows (`docker-images.md`).
5. **Storage lifecycle**: transition objects to infrequent-access classes only when they are genuinely rarely read and not tiny, because those classes add retrieval fees, minimum storage durations (30 days and more) and a minimum billable object size; archive classes have longer minimums and slow retrieval. Use the provider's automatic tiering class when access patterns are unknown. Expire what has no reason to exist (`0x:data-stores` `data-lifecycle.md` for retention decisions).
6. **Commitments last**: savings plans, reserved capacity and committed-use discounts trade flexibility for a substantial discount. Buy only after rightsizing, with at least three months of stable usage, covering about 60 to 80 percent of the steady baseline, one-year and no-upfront first, preferring the flexible kind that follows instance family and region changes. A commitment on an oversized or soon-to-be-replaced resource locks in the waste. Spot or preemptible capacity suits CI, batch and stateless workers that tolerate interruption, not the database or a single-instance service.
7. **Leaving the provider** for cost is the most expensive option in attention; see `platform-choice.md`.

Skip until the bill is worth it: an hour of a founder's time has a price. Below a few hundred dollars a month, do steps 1 and 2 and the guardrails, and stop.

## After an accidental or attack-driven bill

Providers do grant one-time adjustments for genuine accidents and compromises; it is discretionary, faster when handled well, and never guaranteed.

1. **Stop the spend first**: revoke or rotate exposed credentials, terminate unauthorized resources in **every** region, set concurrency to zero on looping functions, remove public access. Keep evidence (resource IDs, audit log extracts) before deleting.
2. **Open a support case immediately**, in the billing or account category, before the invoice closes if possible. For a compromise, say so explicitly; the provider has a defined process and will list remediation steps that must be completed before any adjustment is considered.
3. **Write the case as a timeline**: what happened, when it was detected, the affected services and amounts, what was done to stop it, and what has been put in place so it cannot recur (budgets and anomaly alerts, MFA, key removal, caps, guardrails). The prevention list matters; a second request for the same cause is rarely granted.
4. **Ask plainly for a billing adjustment or credit** for the unintended usage, and ask that collection be paused while the case is open. Respond to every follow-up quickly.
5. **Do not dispute the charge with the card issuer** while the case is open: chargebacks get accounts suspended, production with them. If the amount threatens the company, ask about a payment plan.
6. Afterwards: run the full credential and resource audit in `iam-accounts.md`, and add the missing cap.

For platforms billed by usage where an attack (DDoS, scraping, bot signups) drove the bill, the same sequence applies: enable the platform's attack or firewall mode, then contact support with the traffic evidence. Startup credit programs from the major clouds are worth applying for early; design for the bill after credits expire, and note the expiry date in the calendar.

## Ask the user

- **What monthly spend is expected, and at what figure should someone be woken?** Sets budget thresholds. Default: expected = last month plus 20 percent; alert at 50, 80 and 100 percent and on forecast.
- **If spend hits the limit, should the product go down or keep running?** A hard stop is an outage by design. Default: hard stop at Prototype, alert-only for production at Launch with caps on every scaler.
- **What does a paying customer bring in per month, and is there a free tier?** Needed to judge cost per user and to cap free usage. Default: assume free-tier users must cost close to nothing and limit metered features for them.
- **Is usage stable enough to commit for a year?** Commitments are a financial decision with lock-in. Default: no commitment until three stable months, then partial coverage.
- **Who owns the monthly bill review?** Without a named owner it does not happen. Default: the founder, on a recurring calendar entry.
