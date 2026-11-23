# House stack

Read this when: the founder asks which stack, tool or vendor to use, starts a new project, wants
to know why the skills assume a tool, or is considering switching away from one.

## Follow the project first

Every 0x skill names the same defaults so that their advice fits together, but a default is for
a greenfield decision or a direct "what should I choose?". In an existing project, the project
wins: the framework, ORM, package manager, host, test runner and providers already in use stay,
and advice is translated into them. A switch is its own decision with its own cost, never a side
effect of a feature.

Before naming any default, read what is there:

| Look at | It tells you |
|---|---|
| `package.json` dependencies | Framework, ORM (`drizzle-orm`, `@prisma/client`), auth library, payment SDK, email provider, test runner |
| Lockfile (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lock`) | Package manager; keep it and install in frozen mode |
| `.nvmrc`, `.node-version`, `engines`, `packageManager` | Runtime and package manager versions to stay on |
| `vercel.json`, `fly.toml`, `render.yaml`, `railway.json`, `Procfile`, `Dockerfile`, `compose.yaml` | Host and deploy model |
| `drizzle.config.ts`, `prisma/schema.prisma`, a `migrations/` folder | Data access and migration tool |
| `.github/workflows/` | CI system and what is already enforced |
| `vitest.config.*`, `jest.config.*`, `playwright.config.*` | Test runners |
| `.env.example`, config module | External services in use |
| `*.tf`, `*.tofu` | Infrastructure already managed as code |

Propose switching only when the current choice blocks a concrete requirement (a feature the tool
cannot do, a limit already hit, a contract it cannot meet). Then state the requirement, the cost
of migrating, the cost of staying, and record the decision
(`0x:engineering-leadership` `references/decision-records.md`). Migrate incrementally, behind
the same interface, never as a big-bang rewrite (`0x:code-quality` `references/refactoring.md`).

## The default stack

| Area | Default | Why this default | Flips when, and to what | Detail |
|---|---|---|---|---|
| Language | TypeScript, strict mode, end to end | One language and one type system from database row to button; Claude is strongest where types catch its mistakes | A capability needs another runtime (heavy ML, a library only in Python): a second language as a separate service for that capability only, at Scale | `0x:backend-architecture` `references/runtime-language.md` |
| Runtime, packages | Node.js current LTS, pnpm | Longest support window, widest library and host support; pnpm is fast and strict about undeclared dependencies | The project uses npm, Yarn or Bun: keep it. Edge runtimes only for redirects, token checks and cache shaping | `0x:backend-architecture` `references/runtime-language.md`; pnpm: `0x:react-nextjs` `references/build-tooling.md` |
| Web framework | Next.js App Router with React, server components by default | Server rendering, routing, data and mutations in one deployable; the largest ecosystem | Content site with little interactivity: Astro. App wholly behind login with explicit loaders: React Router. Existing server-rendered backend with modest interactivity: HTML over the wire | `0x:react-nextjs` `references/rendering-strategies.md` |
| Styling | Tailwind CSS with accessible headless primitives (Radix-style) | Styles stay next to markup; primitives bring focus, keyboard and ARIA behavior that is hard to get right | The project has a component library with its own primitives: keep it | `0x:ui-ux-design` `references/design-systems.md` |
| Validation | A schema at every trust boundary (Zod) | One schema validates the request, types the handler and generates API docs | The project uses another schema library: keep it; the rule stays | `0x:web-security` `references/vulnerability-classes.md` |
| Database | PostgreSQL, managed | Covers relational data, JSON, full-text search, queues and vectors well enough to delay every other datastore | Self-host only at Scale with someone who has run it; another store only for a measured need | `0x:data-stores` `references/choosing-datastores.md` |
| Data access | Typed SQL-first layer (Drizzle); raw parameterized SQL where clearer | Types without hiding the SQL; window functions, locking clauses and bulk writes stay expressible | The project has Prisma or another ORM: keep it | `0x:postgres-database` `references/sql-queries.md` |
| Auth | A maintained library or provider (Better Auth on Postgres for new TypeScript work); never hand-rolled crypto or session code | Auth bugs are account takeovers; libraries carry years of fixes | B2B with SSO, SCIM and organization management due within a year, or nobody wants to own auth: a managed provider. Data already on Supabase or Firebase: that platform's auth | `0x:auth-identity` `references/auth-architecture.md` |
| Payments | Stripe with hosted checkout | Widest coverage, hosted pages keep card data out of the app | Low-priced software sold to consumers and small businesses in many countries, the founder wants sales tax handled for them, or the entity's country is unsupported: a merchant of record (Paddle or similar). Decide before Launch: switching migrates subscriptions and cards | `0x:payments-billing` `references/checkout-integration.md` |
| Background jobs | Postgres-backed queue, enqueued in the business transaction | No second system; the job commits or rolls back with the data | Volume or features measured beyond it: Redis-backed or managed queue; long multi-step workflows: durable execution | `0x:backend-architecture` `references/background-jobs.md` |
| Cache | HTTP and CDN caching first, then Redis | Edge caching is free and removes load before it reaches the app | A measured hot read that HTTP caching cannot serve: Redis, never for balances, entitlements or payment state | `0x:data-stores` `references/caching-redis.md` |
| Hosting | A PaaS | No servers to patch; deploy on merge; preview environments | The PaaS limits you: managed containers in one cloud (or one VPS with Kamal if the founder has run servers); Kubernetes only with an owner for it | `0x:cloud-infrastructure` `references/platform-choice.md` |
| CI/CD | GitHub Actions | Next to the code; OIDC to clouds; the default most hosts integrate with | The repository lives elsewhere: that host's CI. Private repositories need a paid GitHub plan for rulesets and deployment environments | `0x:ci-cd-release` `references/ci-pipelines.md` |
| Infrastructure as code | Terraform or OpenTofu | Reviewable plans, one tool for every cloud, DNS and SaaS provider | On a PaaS at Prototype: none, the platform's config file plus a written list of manual settings. In a hyperscaler account beyond a single bucket: from the first resource. DNS, IAM, networks, databases and buckets: codified at Launch wherever they live | `0x:cloud-infrastructure` `references/infrastructure-as-code.md` |
| Tests | Vitest for unit and integration, Playwright for end-to-end | Fast, TypeScript-native, real browsers | The project has Jest or Cypress: keep it | `0x:code-quality` `references/unit-integration-tests.md` |
| Errors, telemetry | An error tracker plus OpenTelemetry to a hosted backend; structured JSON logs | Vendor-neutral instrumentation; one place to follow a request | At Scale: a collector with tail sampling when volume and cost demand it | `0x:site-reliability` `references/logging-errors.md` |
| Product analytics | One PostHog-style suite: events, funnels, flags, experiments | One identity model and one tool to run | At Scale: add warehouse export for finance-grade and cross-system numbers | `0x:product-analytics` `references/event-tracking.md` |
| Transactional email | Postmark or Resend over the HTTP API (SES as the AWS option) | Deliverability is the product; these keep transactional reputation clean | Already on AWS and volume makes price matter: SES | `0x:email-notifications` `references/transactional-email.md` |
| LLM features | Claude through the Anthropic API, called from the server | Strong at structured output and tool use; one provider to evaluate | A customer contract demands a specific cloud or region. API parameters and model IDs belong to the `claude-api` skill | `0x:ai-features` `references/feature-design.md` |

## Defaults the skills add

These follow from the table and recur across skills; the owner holds the reasoning.

| Area | Default | Detail |
|---|---|---|
| Keys and ids | UUIDv7 for anything exposed, `bigint` identity for internal high-volume tables | `0x:postgres-database` `references/schema-modeling.md` |
| Money | Integer minor units plus an ISO currency code, everywhere | `0x:payments-billing` `references/ledger-reconciliation.md` |
| API for the app's own UI | Server components for reads, server functions for writes, no REST layer | `0x:api-design` `references/api-style.md` |
| API for outsiders | REST, JSON, OpenAPI 3.1 generated from the Zod schemas | `0x:api-design` `references/api-style.md` |
| Files | Object storage, private buckets, short-lived signed URLs; S3 or R2 chosen by egress | `0x:data-stores` `references/object-storage.md` |
| Search | Postgres full-text and trigram search before a search engine | `0x:data-stores` `references/search.md` |
| Retrieval for AI | Whole documents in a cached prompt if they fit, else `pgvector` plus full-text search | `0x:ai-features` `references/retrieval.md` |
| Realtime | Polling, then server-sent events down and POST up | `0x:backend-architecture` `references/realtime.md` |
| Feature flags | A constant or environment variable, then a Postgres table or the analytics suite's flags | `0x:ci-cd-release` `references/feature-flags.md` |
| Lint and format | React and Next.js: ESLint flat config with `eslint-plugin-react-hooks`, formatted by Biome or Prettier; other greenfield TypeScript: Biome | `0x:code-quality` `references/static-analysis-types.md` |
| Content | MDX in the repository; a CMS when a non-developer must publish | `0x:react-nextjs` `references/rendering-strategies.md` |
| Self-managed proxy | Caddy on a new server; nginx where already in use | `0x:web-networking` `references/proxies-load-balancers.md` |

## The stack by stage

The defaults are not all present from day one. Add each piece when its stage arrives.

| Area | Prototype | Launch | Scale |
|---|---|---|---|
| Hosting | PaaS | Same PaaS; a container service only for workloads it cannot run | Managed containers in one cloud; Kubernetes only with an owner |
| Database | The platform's one-click Postgres | Paid tier with point-in-time recovery, no idle pausing, a pooler | Bigger instance, then replicas; a standby once downtime costs more than it |
| Jobs | A hosted job service, or none | Postgres-backed queue, separate `web` and `worker` processes | Redis-backed or managed queue when measured; durable execution |
| Caching | Fingerprinted assets immutable, the rest uncached | Public HTML at the CDN, purged on deploy | Redis for measured hot reads; tag-based purging |
| Observability | Error tracker and platform logs | Log drain with request IDs, OpenTelemetry to a hosted backend, uptime check paging a phone | Collector, tail sampling, burn-rate alerts |
| CI | One job: typecheck, lint, test, build | Plus end-to-end tests on signup, login, payment behind one required gate | Shards, build cache, merge queue |
| Infrastructure as code | On a PaaS, none: a written list of manual settings; in a hyperscaler account, from the first resource | Terraform or OpenTofu for DNS, IAM, networks, databases and buckets | Policy as code, drift detection |
| Flags | A constant or environment variable | Postgres table or the analytics suite's flags; kill switches | A flag service with expiry enforced |
| Analytics | 5 to 10 events, or the database and conversations | 15 to 30 events in a tracking plan | Plus warehouse export |
| Email | One provider, one send function, DKIM | Outbox, separate streams, full alignment, DMARC at `p=none` | DMARC at reject, reputation monitoring |
| Payments | Hosted checkout in test mode | Daily reconciliation, tax decision, dispute and webhook alerts | Ledger if the app holds balances, payout-level reconciliation |
| Auth | Library defaults, one or two sign-in methods | MFA for admins, verified email, breach check, revocation | Enterprise SSO and SCIM, organization-wide MFA policy |

## Pairing rules

Some choices constrain others. Check the pair whenever one side changes.

| If the project has | Then | Because |
|---|---|---|
| Serverless or function hosting | A transaction-mode pooler in front of Postgres; maximum instances × pool size below the connection limit | Each instance opens its own connections; a traffic spike exhausts the database (`0x:postgres-database` `references/postgres-operations.md`) |
| Serverless or function hosting | No in-memory state and no un-awaited work after the response; jobs run in a hosted job service or a worker container | The instance may freeze or vanish once the response is sent (`0x:cloud-infrastructure` `references/serverless-edge.md`) |
| A Postgres-backed queue | A long-running worker process somewhere | A queue nobody polls is a table that grows |
| Realtime on serverless hosting | A hosted realtime service; own server-sent events or WebSockets only on always-on containers | Functions cannot hold long connections economically (`0x:backend-architecture` `references/realtime.md`) |
| Next.js self-hosted on several instances | A shared cache handler | Each instance otherwise serves its own stale cache (`0x:react-nextjs` `references/rendering-strategies.md`) |
| A managed auth provider | User records live with that provider; plan the join to the app's own tables and the export path | Leaving later means migrating password hashes and identities |
| A merchant of record | It is the seller on the invoice and handles tax; no tax engine or registrations of your own | Mixing it with your own tax setup double-handles the same sale (`0x:payments-billing` `references/invoices-tax.md`) |
| Balances, credits or seller earnings held by the app | An immutable double-entry ledger | Mirrored provider objects cannot explain a balance (`0x:payments-billing` `references/ledger-reconciliation.md`) |
| Compute and database | The same region, set explicitly | Every cross-region query adds a round trip to each request |
| A data-residency promise | Every subprocessor checked, including email, analytics, error tracking and the LLM provider | Residency is broken by the first vendor that copies data elsewhere (`0x:privacy-compliance` `references/vendors-dpas.md`) |
| An email provider | SPF, DKIM and DMARC on the domain; transactional and marketing on separate subdomains | Mail from an unauthenticated domain is filtered (`0x:email-notifications` `references/deliverability.md`) |
| GitHub Actions deploying to a cloud | OIDC federation, no stored cloud keys | Long-lived keys in CI are the most common cloud credential leak (`0x:ci-cd-release` `references/pipeline-security.md`) |
| Analytics in the EU or other consent regimes | Consent before tracking storage, and fact events sent server-side | Client events vanish when consent is refused; server facts stay (`0x:product-analytics` `references/event-tracking.md`) |
| B2B with organizations | `org_id` on every row, a scoped data layer, row-level security from Launch | One missing filter leaks a customer's data to another (`0x:backend-architecture` `references/multi-tenancy.md`) |
| Tailwind with headless primitives | Primitives wrapped once in `components/ui/` with typed variants from tokens | Direct use everywhere scatters behavior and accessibility fixes (`0x:react-nextjs` `references/components.md`) |
| Vitest or Playwright against a database | The same Postgres major version as production, real migrations applied | Behavior differs between engines and versions (`0x:code-quality` `references/unit-integration-tests.md`) |

## When the project differs

Translate the advice; do not migrate the project. Common cases:

| The project has | Treat it as | Watch for |
|---|---|---|
| Prisma | The data layer; keep it | Raw SQL only through the tagged-template query methods, never the `Unsafe` variants |
| Supabase | Managed Postgres plus auth; keep both | Row-level security policies are the authorization layer for any query from the browser; the service-role key never reaches the client |
| Firebase or another document store | Keep it unless a relational need is blocking | Constraints and transactions that Postgres gives for free must be enforced in code and security rules |
| MySQL | Keep it; schema, index and migration principles transfer | Locking, DDL behavior and syntax differ; check each migration against MySQL's rules |
| A Python, Ruby, PHP or Go backend | Keep the language; Zod becomes that language's schema library | Do not add a Node.js service beside it for one feature |
| npm or Yarn | Keep it | Frozen installs in CI: `npm ci`, `yarn install --immutable` (Yarn 2+) or `--frozen-lockfile` (Yarn 1) |
| Jest, Mocha or Cypress | Keep the runner | The test strategy transfers; only the commands change |
| A single VPS | Keep it while it fits | Backups off the box, unattended security updates, a rehearsed rebuild (`0x:linux-server` `references/packages-updates.md`) |
| Another error tracker or analytics tool | Keep it | One tool per job; do not run two in parallel |

## Ask the user

- **Is there an existing codebase?** It overrides every default here. Default: look at the
  repository first; treat the defaults as greenfield only when nothing exists.
- **Do you want sales tax and VAT handled for you?** Decides Stripe versus a merchant of record,
  which is costly to reverse once subscriptions exist. Default: B2B in a few countries, Stripe with a tax
  engine in monitoring mode from the first sale; low-priced sales to consumers in many
  countries, a merchant of record.
- **Has anyone on the team run servers in production?** Decides PaaS versus a single server.
  Default: no, so a PaaS.
- **Will enterprise customers need SSO or SCIM soon?** Decides auth library versus managed
  provider. Default: library on the project's Postgres, revisited when a deal needs SSO.
- **Are there data-residency or customer-cloud requirements?** Constrains region and every
  vendor. Default: none; one region near most users.
- **Are customers allowed to have their data sent to an LLM provider?** Gates AI features.
  Default: yes under commercial API terms with no training on inputs; regulated data blocked until
  confirmed.
