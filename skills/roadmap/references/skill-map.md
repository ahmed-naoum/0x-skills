# Skill map

Read this when: you need to know which skill, and which file inside it, owns a topic; or the user asks what the set covers.

| Layer | Skill | Owns | Competencies |
|---|---|---|---|
| 0 Machine & OS | `0x:linux-server` | Set up, harden, script and diagnose the Linux machine your code runs on, from CPU, memory and disk limits to systemd, SSH and container internals. | 57 (17 ● / 30 ◐ / 10 ○) |
| 1 Network | `0x:web-networking` | Configure and debug everything between the browser and the app: IP and transport, DNS and domains, TLS, HTTP and its caching, CDN and edge protection, reverse proxies and load balancers. | 73 (27 ● / 29 ◐ / 17 ○) |
| 2 Cloud & delivery | `0x:cloud-infrastructure` | Choose where the product runs and build it: hosting model, container images, Kubernetes, serverless and edge runtimes, cloud networking, IAM, infrastructure as code and cost control. | 62 (16 ● / 31 ◐ / 15 ○) |
| 2 Cloud & delivery | `0x:ci-cd-release` | Get a change from a merged pull request to production safely: CI pipelines, pipeline security, environments and config, zero-downtime deploys, rollback and feature flags. | 37 (14 ● / 15 ◐ / 8 ○) |
| 3 Data | `0x:postgres-database` | Model, query, migrate, tune, back up and scale a relational database, with PostgreSQL as the default: schemas, SQL, transactions, indexes, zero-downtime migrations, operations and recovery. | 68 (23 ● / 31 ◐ / 14 ○) |
| 3 Data | `0x:data-stores` | Decide when a product needs more than Postgres and run what it adds: Redis caching, search, object storage, event streams, an analytics warehouse and pipelines, and the data lifecycle across all of them. | 47 (11 ● / 26 ◐ / 10 ○) |
| 4 Backend | `0x:backend-architecture` | Structure the server side of a product: runtime choice, monolith and service boundaries, consistency under concurrency, multi-tenancy, background jobs, realtime features, file uploads and resilient third-party integrations. | 75 (25 ● / 28 ◐ / 22 ○) |
| 4 Backend | `0x:api-design` | Design, document and evolve HTTP APIs and webhooks: style choice, request and response contracts, errors, pagination, idempotency, rate limits, versioning and a public developer platform. | 45 (18 ● / 18 ◐ / 9 ○) |
| 4 Backend | `0x:email-notifications` | Send transactional email, SMS, push and in-app notifications that arrive, render and are wanted: provider setup, SPF, DKIM and DMARC, sender reputation, templates, channel choice and user preferences. | 33 (14 ● / 13 ◐ / 6 ○) |
| 4 Backend | `0x:payments-billing` | Take money correctly: checkout integration, subscriptions and entitlements, usage billing, invoices and tax, refunds, disputes and fraud, ledger and reconciliation, and catalog, cart, inventory and fulfillment. | 66 (24 ● / 28 ◐ / 14 ○) |
| 4 Backend | `0x:ai-features` | Design LLM-powered product features that are useful, safe and affordable: when to use a model, prompts and context, retrieval, agents and tools, evaluations, guardrails, cost and latency, streaming UX and data handling. | 64 (21 ● / 31 ◐ / 12 ○) |
| 5 Trust | `0x:auth-identity` | Build sign-in and access control that resist takeover: auth architecture, sessions and tokens, passwords, MFA and passkeys, OAuth and OIDC, enterprise SSO, authorization models, account recovery and abuse defense. | 64 (22 ● / 29 ◐ / 13 ○) |
| 5 Trust | `0x:web-security` | Build and run the product so it resists attack: threat modeling, vulnerability classes, browser security headers, secrets and cryptographic choices, the software supply chain, hardening of company accounts and admin tools, security logging and breach response, and security testing. | 69 (26 ● / 32 ◐ / 11 ○) |
| 5 Trust | `0x:privacy-compliance` | Keep the product lawful and sellable: GDPR and US privacy law, consent and cookies, data-subject requests and retention, DPAs and vendors, PCI, SOC 2 and ISO 27001, sector and consumer rules, terms and policies, and software licenses. | 61 (13 ● / 32 ◐ / 16 ○) |
| 6 Frontend | `0x:frontend-foundations` | Build on the web platform itself: semantic HTML, CSS layout and responsive design, JavaScript and TypeScript, the browser's rendering and events, forms, animation, internationalization, and PWA and mobile packaging. | 72 (34 ● / 33 ◐ / 5 ○) |
| 6 Frontend | `0x:react-nextjs` | Build the application layer of the frontend with React and a meta-framework: rendering strategy per route, where editable content lives, server components and server functions, data and state, routing, component architecture and build tooling. | 49 (26 ● / 21 ◐ / 2 ○) |
| 6 Frontend | `0x:3dui` | Build live 3D product websites with three.js and Next.js: the object is code, lit like a photo studio and directed by the scroll. | 10 (2 ● / 6 ◐ / 2 ○) |
| 7 Design & accessibility | `0x:ui-ux-design` | Design interfaces people understand and enjoy: visual design, design tokens and component systems, UX flows, information architecture, usability testing, microcopy, motion and dark mode. | 58 (28 ● / 24 ◐ / 6 ○) |
| 7 Design & accessibility | `0x:accessibility` | Make the product usable by people with disabilities and meet WCAG 2.2 AA: names, roles and ARIA, keyboard and focus, accessible forms, visual and cognitive access, and testing and audits. | 35 (16 ● / 16 ◐ / 3 ○) |
| 8 Engineering craft | `0x:git-collaboration` | Use git and the repository as a team tool: the git model and recovery, branching workflow, pull requests and code-review practice, monorepos, and versioning, changelogs and release notes. | 35 (13 ● / 16 ◐ / 6 ○) |
| 8 Engineering craft | `0x:code-quality` | Keep code correct and changeable: test strategy, unit, integration, end-to-end, contract and visual tests, test data and flaky tests, debugging method, refactoring, static analysis and types, and technical documentation. | 67 (31 ● / 27 ◐ / 9 ○) |
| 8 Engineering craft | `0x:ai-coding-agents` | Get reliable work out of coding agents such as Claude Code: scoping and specs, context and project setup, verification and review, parallel and automated runs, and permissions and governance. | 35 (20 ● / 12 ◐ / 3 ○) |
| 8 Engineering craft | `0x:engineering-leadership` | Make the technical decisions a CTO makes: technology strategy, build versus buy and vendor choice, decision records, estimation and planning, technical debt, and hiring and onboarding engineers. | 41 (10 ● / 23 ◐ / 8 ○) |
| 9 Operations | `0x:site-reliability` | Know what production is doing and keep it up: logs, errors, metrics and traces, dashboards and alerts, SLOs, incident response, postmortems and runbooks, capacity and scaling, and disaster recovery. | 64 (19 ● / 33 ◐ / 12 ○) |
| 9 Operations | `0x:web-performance` | Make pages and endpoints fast and keep them fast: Core Web Vitals, loading and delivery, JavaScript bundles, images and fonts, rendering and runtime, backend latency and profiling, load testing, and performance budgets. | 55 (21 ● / 27 ◐ / 7 ○) |
| 10 Product | `0x:product-discovery` | Decide what to build and why: customer interviews, problem validation, jobs-to-be-done, MVP scoping, specs, prioritization and roadmaps, and the feedback loops that tell you whether it worked. | 47 (22 ● / 22 ◐ / 3 ○) |
| 10 Product | `0x:product-analytics` | Instrument the product and decide what to measure: event taxonomy and tracking, funnels and activation, cohorts and retention, north-star metrics and metric trees, A/B test design and its traps, and attribution. | 39 (14 ● / 19 ◐ / 6 ○) |
| 11 Growth & revenue | `0x:growth-marketing` | Get the product found and tried: positioning and messaging, landing pages and conversion, launches, content, lifecycle email, paid acquisition, referral and product-led loops, and community and partnerships. | 55 (15 ● / 35 ◐ / 5 ○) |
| 11 Growth & revenue | `0x:pricing-monetization` | Decide how the product makes money: revenue model and value metric, price setting, plans and packaging, discounts and price changes, and the unit economics that show whether it works. | 32 (13 ● / 17 ◐ / 2 ○) |
| 11 Growth & revenue | `0x:sales-support` | Win customers and keep them: prospecting and outreach, discovery calls and demos, proposals and contracts, procurement and security questionnaires, onboarding, support operations, customer success and churn, and reviews. | 62 (19 ● / 33 ◐ / 10 ○) |
| 12 Company | `0x:company-building` | Build the company around the product: strategy and moats, incorporation and founder legal basics, hiring, managing people, operating cadence and culture, and the founder's own effectiveness. | 50 (11 ● / 31 ◐ / 8 ○) |
| 12 Company | `0x:startup-finance` | Run the company's money: bookkeeping and tax, cash and runway forecasting, funding strategy, the fundraising process, equity and the cap table, and exit and due diligence. | 46 (11 ● / 21 ◐ / 14 ○) |

## What each skill hands to another

**linux-server** does not cover:
- Writing Dockerfiles, Compose files or Kubernetes manifests → `cloud-infrastructure`
- DNS, TLS, reverse proxies and anything between the browser and the box → `web-networking`
- Deploy pipelines, releases and rollbacks → `ci-cd-release`
- Postgres tuning, backups and slow queries → `postgres-database`
- Application logs, dashboards, alerts and incident process → `site-reliability`
- A slow page or endpoint when the host has CPU, memory and disk to spare → `web-performance`

**web-networking** does not cover:
- CORS errors, Content Security Policy and other security headers → `web-security`
- SPF, DKIM, DMARC and email landing in spam → `email-notifications`
- Building WebSocket, SSE or WebRTC features → `backend-architecture`
- VPCs, subnets, security groups and private cloud networking → `cloud-infrastructure`
- Page-load speed, Core Web Vitals and image delivery → `web-performance`
- Login rate limits, credential stuffing and signup bots → `auth-identity`

**cloud-infrastructure** does not cover:
- CI pipelines, deploy strategies, rollbacks and feature flags → `ci-cd-release`
- Shell access, systemd, host hardening, instance and disk sizing, and container internals on one machine → `linux-server`
- DNS, TLS certificates, CDN configuration and load-balancer behavior → `web-networking`
- Running and tuning Postgres itself → `postgres-database`
- Autoscaling policy, capacity planning and disaster recovery → `site-reliability`
- Secrets, staff SSO and devices, and admin-panel hardening → `web-security`

**ci-cd-release** does not cover:
- Choosing a host, writing Dockerfiles or Terraform → `cloud-infrastructure`
- What tests to write and how to fix flaky ones → `code-quality`
- Writing the zero-downtime schema migration itself → `postgres-database`
- Secret storage, rotation, and dependency and supply-chain scanning → `web-security`
- Branching model, pull requests and version numbers → `git-collaboration`
- A/B experiment design and statistics → `product-analytics`

**postgres-database** does not cover:
- Redis, search engines, object storage, warehouses and other non-relational stores → `data-stores`
- Analytics queries, reporting SQL and statistics on business data → `data`
- Choosing a multi-tenancy model and row-level tenant isolation → `backend-architecture`
- SQL injection and other vulnerability classes → `web-security`
- Running the migration step inside the deploy pipeline → `ci-cd-release`
- Company-wide disaster recovery plans, RPO and RTO → `site-reliability`

**data-stores** does not cover:
- Schema design, SQL, indexes, migrations and backups in Postgres → `postgres-database`
- HTTP and CDN caching headers and purging → `web-networking`
- Job queues, retries, scheduled jobs and workflows → `backend-architecture`
- The upload flow: validation, scanning and processing of user files → `backend-architecture`
- Analyzing data, writing analytics SQL and building dashboards → `data`
- Legal duties behind retention and deletion requests → `privacy-compliance`

**backend-architecture** does not cover:
- Endpoint contracts, pagination, API rate limits and generic webhooks → `api-design`
- Schema design, transactions, locks and query tuning → `postgres-database`
- Choosing and running Redis, search, object storage or streams → `data-stores`
- Roles, permissions and per-object access checks → `auth-identity`
- Sending email, SMS and push notifications → `email-notifications`
- Profiling slow endpoints and load testing → `web-performance`

**api-design** does not cover:
- User login, sessions and permission models behind the endpoints → `auth-identity`
- Service boundaries, background jobs and realtime transports → `backend-architecture`
- Payment-provider webhooks and billing state → `payments-billing`
- HTTP caching headers, CDN rules and edge rate limiting → `web-networking`
- Contract tests and other API test automation → `code-quality`
- Claude API parameters, tool-use syntax and SDK usage → `claude-api`

**email-notifications** does not cover:
- Lifecycle, newsletter and marketing email strategy and copy → `growth-marketing`
- Dunning emails and failed-payment recovery logic → `payments-billing`
- Magic links, OTP login and reset-flow security → `auth-identity`
- DNS record mechanics beyond the mail records → `web-networking`
- Anti-spam and consent law for marketing and cold email → `privacy-compliance`
- The queue and retry machinery that sends in the background → `backend-architecture`

**payments-billing** does not cover:
- What to charge, plan design and pricing strategy → `pricing-monetization`
- Generic webhook and idempotency-key mechanics → `api-design`
- PCI DSS scope, SAQ and consumer-law rules on renewal and cancellation → `privacy-compliance`
- Bookkeeping, revenue recognition and tax filing → `startup-finance`
- Cancellation save offers and churn reduction → `sales-support`
- Checkout page conversion experiments → `product-analytics`

**ai-features** does not cover:
- Anthropic API parameters, model IDs, tool-use syntax, caching and SDK code → `claude-api`
- Using coding agents to build the product itself → `ai-coding-agents`
- Vector indexes and search-engine setup → `data-stores`
- EU AI Act classification and legal transparency duties → `privacy-compliance`
- Exposing your own API to outside agents through MCP → `api-design`
- Pricing AI features and credit packaging → `pricing-monetization`

**auth-identity** does not cover:
- XSS, injection, CSP, CORS and other vulnerability classes → `web-security`
- Tenant data isolation and row-level security design → `backend-architecture`
- API keys and OAuth for third-party developers → `api-design`
- Sending the verification, reset and security emails or SMS → `email-notifications`
- WAF rules and DDoS protection at the edge → `web-networking`
- Staff SSO, device security and internal access control → `web-security`

**web-security** does not cover:
- Reviewing the current diff or pending changes for vulnerabilities → `security-review`
- Login, sessions, MFA, permission checks and signup abuse → `auth-identity`
- TLS configuration, HSTS, WAF and DDoS protection → `web-networking`
- SOC 2, ISO 27001, PCI scope and breach-notification law → `privacy-compliance`
- Hardening a single Linux host and SSH → `linux-server`
- Prompt injection and LLM-specific guardrails → `ai-features`

**privacy-compliance** does not cover:
- Engineering the export, deletion and retention jobs → `data-stores`
- Technical security controls and breach containment → `web-security`
- Making the interface itself accessible → `accessibility`
- Incorporation, founder agreements and employment contracts → `company-building`
- Negotiating customer contracts and answering security questionnaires → `sales-support`
- Sales tax and VAT handling → `payments-billing`

**frontend-foundations** does not cover:
- React components, server components, Next.js routing and data fetching → `react-nextjs`
- Visual design choices, flows and design tokens → `ui-ux-design`
- Screen readers, ARIA and keyboard access → `accessibility`
- Core Web Vitals, bundle size, image and font loading → `web-performance`
- three.js, WebGL scenes and 3D product pages → `3dui`
- Linting, type-check policy and test setup → `code-quality`

**react-nextjs** does not cover:
- Plain HTML, CSS, TypeScript language questions, forms and animation → `frontend-foundations`
- Bundle size, Core Web Vitals and image and font loading → `web-performance`
- Design tokens, visual design and UX flows → `ui-ux-design`
- three.js scenes and 3D product pages → `3dui`
- API contracts the frontend consumes → `api-design`
- Search rankings, metadata strategy and AI-search visibility → `seo-aeo-geo-ultimate`

**3dui** does not cover:
- CSS, View Transitions and scroll-driven animation without WebGL → `frontend-foundations`
- Next.js routing, data and rendering around the scene → `react-nextjs`
- Core Web Vitals and loading performance of the page as a whole → `web-performance`
- Layout, typography and visual design of the surrounding page → `ui-ux-design`

**ui-ux-design** does not cover:
- Implementing layout, theming and animation in CSS → `frontend-foundations`
- Building the React component library → `react-nextjs`
- WCAG conformance, screen readers and keyboard access → `accessibility`
- Customer interviews, problem validation and what to build → `product-discovery`
- Chart and data-visualization design → `dataviz`
- Landing-page messaging and conversion copy → `growth-marketing`

**accessibility** does not cover:
- Accessibility law, statements and responding to legal complaints → `privacy-compliance`
- General HTML structure, forms, CSS and reduced-motion animation code → `frontend-foundations`
- Visual design, color palettes and usability testing in general → `ui-ux-design`
- Accessible charts and data-visualization design → `dataviz`
- Setting up the end-to-end test runner that hosts axe checks → `code-quality`

**git-collaboration** does not cover:
- Finding bugs in the current diff → `code-review`
- CI checks, branch protection in the pipeline and deploys → `ci-cd-release`
- Removing a leaked secret from history and rotating it → `web-security`
- Git worktrees and review habits for AI coding agents → `ai-coding-agents`
- API versioning and deprecation policy → `api-design`
- README, architecture and developer documentation → `code-quality`

**code-quality** does not cover:
- Reviewing the current diff for bugs → `code-review`
- The CI pipeline that runs the checks, and deploys → `ci-cd-release`
- Load tests and performance profiling → `web-performance`
- Security testing and penetration tests → `web-security`
- Pull-request conventions and code-review practice → `git-collaboration`
- Help-center articles and customer-facing support docs → `sales-support`

**ai-coding-agents** does not cover:
- LLM features inside the product itself → `ai-features`
- Claude API usage, model IDs and SDK details → `claude-api`
- Reviewing a specific diff for bugs → `code-review`
- Writing the tests and lint setup agents rely on → `code-quality`
- License and IP status of AI-generated code → `privacy-compliance`
- Product specs and acceptance criteria as product decisions → `product-discovery`

**engineering-leadership** does not cover:
- Choosing a backend runtime or designing a system's modules and services → `backend-architecture`
- Choosing the hosting platform → `cloud-infrastructure`
- General hiring, compensation, org structure, managing people and firing → `company-building`
- What the product should do and feature prioritization → `product-discovery`
- Carrying out a refactor or rewrite in the code → `code-quality`
- Vendor privacy review, DPAs and subprocessor lists → `privacy-compliance`

**site-reliability** does not cover:
- Deploy mechanics, rollback commands and feature flags → `ci-cd-release`
- Database backups, restore drills and replica failover → `postgres-database`
- Running load tests and profiling slow code → `web-performance`
- Security incidents, intrusions and audit logging → `web-security`
- Diagnosing a single host's CPU, memory or disk → `linux-server`
- Product analytics events, funnels and business dashboards → `product-analytics`

**web-performance** does not cover:
- Reading query plans, indexing and fixing a slow SQL query → `postgres-database`
- Cache-Control headers, CDN configuration and HTTP/3 → `web-networking`
- Adding a Redis application cache → `data-stores`
- Rendering strategy, server components and hydration design → `react-nextjs`
- Capacity planning, autoscaling and SLOs → `site-reliability`
- Frame rate of three.js scenes → `3dui`

**product-discovery** does not cover:
- Event tracking, funnels, retention analysis and A/B tests → `product-analytics`
- Wireframes, flows, usability tests and interface copy → `ui-ux-design`
- Positioning, launch and acquisition channels → `growth-marketing`
- Price points, plans and packaging → `pricing-monetization`
- Engineering estimates, technical planning and build-versus-buy → `engineering-leadership`
- Briefing a coding agent to implement the spec → `ai-coding-agents`

**product-analytics** does not cover:
- Running the analysis: SQL queries, statistics and dashboards from data → `data`
- Chart design and visualization choices → `dataviz`
- Cookie consent and the legal limits on tracking → `privacy-compliance`
- Warehouse loading, pipelines and data modeling → `data-stores`
- Feature-flag rollout mechanics → `ci-cd-release`
- MRR, burn, runway and financial reporting → `startup-finance`

**growth-marketing** does not cover:
- SEO, keyword research, technical SEO and AI-search visibility → `seo-aeo-geo-ultimate`
- Email deliverability, SPF, DKIM and sending infrastructure → `email-notifications`
- Attribution, funnel analysis and experiment statistics → `product-analytics`
- Outbound sales, demos and closing deals → `sales-support`
- Price points and plan packaging → `pricing-monetization`
- Validating the problem before there is a product → `product-discovery`

**pricing-monetization** does not cover:
- Implementing checkout, subscriptions, metering and invoices → `payments-billing`
- Cash-flow forecasts, runway, bookkeeping and fundraising → `startup-finance`
- A/B test design and statistics for a pricing experiment → `product-analytics`
- Negotiating a specific enterprise deal → `sales-support`
- Legal rules on price display, auto-renewal and cancellation → `privacy-compliance`
- Reducing the cloud bill itself → `cloud-infrastructure`

**sales-support** does not cover:
- Positioning, landing pages, launches and inbound marketing → `growth-marketing`
- List prices, plans and discount policy → `pricing-monetization`
- Processing refunds, cancellations and billing states in code → `payments-billing`
- DPAs, terms of service and compliance certifications themselves → `privacy-compliance`
- Retention metrics, cohorts and churn analysis → `product-analytics`
- Turning feedback into roadmap decisions → `product-discovery`

**company-building** does not cover:
- Bookkeeping, runway, fundraising, cap table and exit → `startup-finance`
- Hiring, interviewing and onboarding engineers specifically → `engineering-leadership`
- Terms of service, privacy policy and regulatory compliance → `privacy-compliance`
- Choosing which problem and customer to pursue → `product-discovery`
- Positioning against competitors in the market → `growth-marketing`
- Revenue model and unit economics → `pricing-monetization`

**startup-finance** does not cover:
- Prices, plans, CAC, LTV and margin per customer → `pricing-monetization`
- Sales tax and VAT collection, invoices and payment reconciliation → `payments-billing`
- Incorporation, founder agreements, the board, hiring and payroll setup → `company-building`
- Cloud bills and infrastructure cost reduction → `cloud-infrastructure`
- Technical due diligence on the codebase → `engineering-leadership`
- Analyzing financial data with SQL or statistics → `data`
