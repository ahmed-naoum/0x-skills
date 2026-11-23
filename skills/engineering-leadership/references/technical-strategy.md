# Technical strategy

Read this when: choosing the whole stack for a new product, setting technical direction for the
next year, deciding whether to offer self-hosted or customer-cloud deployments, preparing for
technical due diligence, or explaining technical risk to investors, customers or a co-founder.

## The default stack, with the condition that flips each choice

Pick the whole stack in one sitting from the defaults below, and spend thinking time only on the
rows where the product has a concrete reason to differ. If the project already exists, its
choices win; this table is for greenfield work and for "what should I use?".

| Layer | Default | Flips when |
|---|---|---|
| Language | TypeScript, strict, front and back | ML or data science is the core → Python for that one service; CPU-bound hot path → Go or Rust for one isolated service |
| Runtime, packages | Node.js current LTS, pnpm | |
| Web framework | Next.js App Router, server components by default | Mostly static content → static-first framework; API only, no UI → small HTTP framework |
| Styling, components | Tailwind with Radix-style headless primitives | Team already owns a design system |
| Validation | Zod at every trust boundary | |
| Database | Managed PostgreSQL | Almost never replaced; additions (search, cache, warehouse) are decided by `0x:data-stores` |
| Data access | Drizzle, raw SQL where clearer | Prisma already in the project → keep it |
| Auth | Maintained provider or library | Selling to companies → one that supports SAML/OIDC SSO and SCIM without a rewrite |
| Payments | Stripe | Founder wants VAT and sales tax handled → merchant of record |
| Background jobs | Postgres-backed queue | Throughput, fan-out or rate-limiting needs beyond it → Redis-backed queue |
| Cache | HTTP and CDN caching, then Redis | |
| Hosting | A PaaS | Runtime, region, networking or cost limits → containers on a cloud; Kubernetes only with people to run it |
| CI/CD | GitHub Actions | |
| Infrastructure as code | Terraform or OpenTofu once there is cloud infrastructure outside the PaaS | PaaS only → its config file in the repo is enough |
| Tests | Vitest, Playwright | |
| Telemetry | Error tracker plus OpenTelemetry to a hosted backend, JSON logs | |
| Product analytics | PostHog-style single tool | |
| Email | Postmark, Resend or SES | |
| LLM features | Claude through the Anthropic API | |

Three rules settle most rows. One language across the stack unless a service truly needs
another, because a solo founder pays for every extra toolchain in CI, context switching and
hiring. Managed beats self-run until the managed bill exceeds the person-time to run it (see
`build-vs-buy.md`). Prefer what coding agents and the hiring market know best: mainstream stacks
get better generated code, more answered questions and a larger pool of candidates.

## Boring technology and the innovation budget

Treat novelty as a budget. A young company can afford roughly three "innovation tokens" (Dan
McKinley's framing): each unusual database, language, framework or architecture spends one,
because it brings undocumented failure modes, few answers and a thin hiring pool. Spend tokens
where the product differentiates and nowhere else.

Before adopting anything outside the default stack, all of these must hold:

1. It solves a problem the product has now, not one it might have at Scale.
2. The default cannot do it with reasonable effort, shown by an attempt or a spike.
3. Other teams run it in production at a similar size, and its failure modes are written up.
4. Someone on the team can debug it at night without its original author.
5. There is an exit: how it would be removed and roughly what that costs.
6. It replaces something, or the team explicitly accepts running one more system.

Traps:

- **Two tools for one job.** Two queues, two ORMs, two state libraries. The most common token
  waste. Adding a second one needs a decision record and a plan to remove the first.
- **Boring is not abandoned.** Check release cadence, open security issues and who funds the
  project. A proven tool with no maintainer is a migration waiting to happen.
- **Novelty in the money or identity path.** Payments, auth and data integrity get the most
  proven option even when a newer one is nicer.
- **Choosing for interest.** If the honest reason is "I want to learn it", do that in a side
  project or behind a seam that can be ripped out in a day.

## One-way doors: the few decisions that deserve slowness

Most technical decisions are two-way doors: reversible in days. Make those quickly, with the
default, and move on. Slow down (spike, write a decision record, sleep on it) only for the
decisions that are expensive to undo.

| Decision | Why it is hard to reverse | Get right now |
|---|---|---|
| Core entities and ID format | IDs end up in URLs, APIs, exports, integrations and customer spreadsheets | Opaque public IDs (time-ordered UUIDs or prefixed random IDs); sequential integers in URLs leak volume and invite enumeration |
| Tenancy model | Changing isolation means migrating every customer's data | Account or tenant key on every tenant-owned row from the first table (`0x:backend-architecture`) |
| Primary database engine | Data, queries and operational knowledge all depend on it | PostgreSQL |
| User identity | Some auth providers will not export password hashes; sessions and user IDs leak everywhere | Own `users` table with own IDs; the provider's ID is a column, not the key |
| Payment provider | Card vault and subscription state live with the provider | Provider IDs mirrored; billing logic behind one module |
| Public API and webhook contracts | Customer code depends on them | Versioned from the first external consumer (`0x:api-design`) |
| Domain, URL structure, sending domain | Links, SEO and email reputation attach to them | Own domain; a subdomain for transactional email |
| Data region and residency | Moving data across regions can need contractual notice to customers, a privacy review and downtime | Pick the region of the first serious market and record why |
| License of your own code, if published | Relicensing later burns goodwill and needs rights from every outside contributor | Decide before the first public commit; accept contributions only under terms (a CLA or equivalent) that allow relicensing |

Two-way doors to decide in minutes: CSS approach, component library, test runner, queue library
behind one interface, analytics tool, logging vendor when telemetry goes through OpenTelemetry,
and the PaaS when the app is a standard container.

A decision is a one-way door when it shapes stored data, is visible in customers' code or URLs,
involves a vendor holding data in a form that cannot be exported, or would require touching
every module to reverse. Record each one with `decision-records.md`.

## A technical strategy tied to the business

A technical strategy is a one-page answer to "given where the business must be in 12 months,
what will engineering do and refuse to do?" Use Richard Rumelt's kernel: a diagnosis, a guiding
policy, and coherent actions. A list of technologies is not a strategy.

```markdown
# Technical strategy, <quarter/year>

Diagnosis: the business must reach <milestone> by <date> with <team size>, <runway> months.
The technical obstacle is <the one thing most likely to stop that>.

Guiding policy: <the rule that resolves trade-offs, e.g. "enterprise readiness before new
features" or "nothing that adds a system to operate">.

Actions (each with an owner and a quarter):
1. ...
Not doing: <attractive work explicitly declined, and why>
Constraints: <compliance targets, data residency, budget ceiling, hiring plan>
Revisit when: <fundraise, new segment, team doubles, a constraint changes>
```

Weak: "Move to microservices for scalability" (no diagnosis, no business link). Strong: "Deals
with mid-market buyers stall on SSO and audit logs; for two quarters, enterprise readiness
comes before new features, and nothing new gets added to operate."

Get the inputs from the founder, not from the code: runway, next business milestone, target
customer, expected team size, compliance demands. Rewrite after a fundraise, a segment change or
a doubling of the team; skim it quarterly.

## Splitting engineering time

Reserve capacity explicitly; "debt when we have time" means never. Rules of thumb by stage:

| Stage | Features | Reliability and operations | Debt and tooling |
|---|---|---|---|
| Prototype | about 90% | backups, error tracking, nothing more | the rest |
| Launch | about 70% | about 15-20% | about 10-15% |
| Scale | about 50-60% | about 20% | about 20-25% |

Overrides beat the split: an error budget burning or repeated incidents put reliability first
until it recovers (`0x:site-reliability`); debt that blocks a revenue deal is feature work; a
security hole is done now. Implement the split as a standing slot (one item per cycle, or one
day a week) and check it quarterly from issue or pull-request labels.

## Explaining technical risk to non-technical people

Lead with the decision needed, then the risk in money, time and customers, then the options with
their cost, always including "do nothing". Keep likelihood and impact separate, give ranges
rather than false precision, and use at most one analogy.

```text
If <event> happens (likely: about once a year / unlikely this year), then <customers affected,
hours down, revenue or deal at risk>. Preventing it costs <days or money>.
Options: A <cost, residual risk>, B <cost, residual risk>, do nothing <expected cost>.
Recommendation: A, because <one sentence>.
```

Keep a register of the top five technical risks with likelihood, business impact, mitigation,
cost and owner, and bring it to investor updates or co-founder reviews. Report bad news as soon
as it is known, with the plan; a surprise slip costs more trust than an early warning. Do not
inflate every risk either: stakeholders stop listening to an engineer who rates everything high.

## Plan for ten times the scale, build for one

Build for current load, keep cheap seams for ten times, and accept that a hundred times means
rewriting parts. Seams that cost almost nothing now:

- Stateless app processes; sessions and files outside the process.
- Slow or failure-prone work in background jobs, all of them idempotent.
- A limit and pagination on every list endpoint and query.
- An index for every query path, tenant key leading where tenants exist.
- Connection pooling to the database from day one.
- No third-party call in a hot request path without a timeout.
- A modular monolith with clear module boundaries, so a piece can be split out later.

Skip until a measurement demands it: microservices, sharding, multi-region active-active,
Kubernetes, event sourcing, read replicas, a self-built CDN layer.

Write the ten-times paragraph: for each likely bottleneck (database connections, the heaviest
query, job throughput, third-party rate limits, cost per customer), name the first sign and the
planned response. That paragraph replaces most premature architecture. Load testing belongs to
`0x:web-performance`; capacity planning to `0x:site-reliability`.

## Passing technical due diligence

Investors at later rounds and acquirers send an engineer or a firm to check the following. A
known, ranked debt register reads as maturity; a problem the reviewer finds first reads as risk.

| Area | What they look for | Red flag |
|---|---|---|
| IP ownership | Every founder, employee and contractor signed an IP assignment valid in their country, with confirmatory assignments for work done before signing | Contractor or pre-incorporation code with no assignment |
| Open-source licenses | Inventory; no GPL code in distributed or on-premises builds and no modified AGPL code serving users over a network, unless reviewed | Copyleft obligations nobody has checked |
| Security | MFA everywhere, secrets outside the repo and its history, dependency scanning, access reviews, pen test if selling to enterprises | Shared admin logins, secrets in git history |
| Architecture | A current diagram, decision records, a scaling story | Nobody can explain why the system is shaped this way |
| Quality and delivery | CI on every change, tests on critical paths, frequent deploys, rollback | Manual deploys from a laptop |
| Operations | Tested backup restores, monitoring, incident history with postmortems | Backups never restored |
| Bus factor | Knowledge and access spread beyond one person | One person holds the only credentials or understands billing |
| Cost | Infrastructure spend and its trend per customer | Cost growing faster than revenue, unexplained |

Checks to run weeks before:

```bash
pnpm licenses list --prod                      # license inventory of shipped dependencies
git shortlog -sn --no-merges HEAD -- src/billing  # who knows each critical area (HEAD is required
                                                  # when stdin is not a terminal, as in agents)
```

Run a secrets scanner over the full git history (`0x:web-security` covers which and how), and
rotate anything it finds; deleting the commit is not enough. Prepare a folder with the
architecture overview, decision records, debt register, security overview, license report,
infrastructure map with monthly costs, incident log and an access list. Deal mechanics belong
to `0x:startup-finance`; license questions to `0x:privacy-compliance`.

## Self-hosted and customer-cloud deployments

Default answer: no, until a specific deal pays for the upkeep. Every customer-run copy is a
version in the field that cannot be observed, upgraded or hotfixed at will. Offer the least
invasive rung that satisfies the buyer's real requirement (usually data control or isolation):

| Option | What the customer gets | Upkeep for you | Typical trigger |
|---|---|---|---|
| Dedicated single-tenant stack in your cloud | Isolation, region choice | Moderate: N stacks from the same IaC | Isolation or residency demand |
| Bring your own cloud: you operate it in their account | Data stays in their account | High: cross-account access, their policies and quotas | Large deal with strict data-control rules |
| Customer-managed install (Compose or Helm) | Full control | Very high: many versions, blind debugging | Regulated buyer, deal size justifies |
| Air-gapped install | No outbound network | Highest: offline updates, licensing, support | Government, defense |

Prerequisites before saying yes: one versioned artifact with all configuration from the
environment; no hard dependency on your own SaaS-only services (email, telemetry, billing), or
those made optional; migrations that run unattended across skipped versions, tested in CI from
the oldest supported version; a support-bundle command that collects logs and config without
secrets; an offline license check; a published support window (for example the current and
previous minor releases).

Price the upkeep, not the deal. Estimate per customer per year: packaging and testing each
release for that target, upgrade assistance, support tickets without telemetry, and security
backports, times the loaded hourly cost. Rule of thumb: sell self-hosted as its own plan with a
minimum annual contract several times that upkeep, usually above the cloud price for the same
usage, because the customer gains control and the company loses efficiency. Write into the
contract that only supported versions get support, upgrades are required within a window, and
infrastructure, backups and network security are the customer's. Proposal and contract mechanics
are in `0x:sales-support`.

The trap is the first on-premises customer turning the company into a consultancy: release
cadence drops to the slowest customer and per-customer forks appear. Refuse forks outright.

## Ask the user

- **What must the business achieve in the next 12 months, with how much runway?** The strategy
  and the time split follow from it. Default: assume the next milestone is revenue growth on
  about a year of runway, and optimize for speed with the fewest systems.
- **Who is the target buyer: individuals, small teams or enterprises?** Enterprises pull SSO,
  audit logs, data residency and security reviews forward. Default: self-serve small teams.
- **Is a fundraise or acquisition likely within a year?** If yes, due diligence preparation
  starts now. Default: assume a raise is possible and keep IP assignments and licenses clean.
- **Would the company support self-hosted or customer-cloud installs, at what minimum price?**
  It changes the release process for years. Default: no; offer a dedicated cloud stack instead.
- **Are there hard constraints: compliance targets, data regions, a monthly cost ceiling?**
  They are one-way doors. Default: one region near the first market, no certification yet.
