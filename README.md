# 0x skills

Skills for Claude Code that cover web development from the machine to the customer: 33 skills on a tree of 13 layers and 1673 competencies. Each skill is what a principal engineer who has also founded companies would tell Claude before it touches that part of your product: the defaults, the decision rules, the numbers, what breaks in production, and what to skip until later.

## Install

In Claude Code (2.1.275 or later):

```
/plugin install 0x --marketplace ahmed-naoum/0x-skills
```

On older versions, in two steps:

```
/plugin marketplace add ahmed-naoum/0x-skills
/plugin install 0x@0x-skills
```

The skills appear as `0x:<name>` and load by themselves when a task falls in their area. Ask `0x:roadmap` what to learn next, what is missing before a launch, or which skill owns a topic.

## The tree

[TREE.md](TREE.md) lists all 1673 competencies, marked by level: ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases.

| # | Layer | The question it answers | Skills |
|---|---|---|---|
| 0 | Machine & OS | What is my code actually running on? | `linux-server` |
| 1 | Network | How does a request travel from a browser to my server and back? | `web-networking` |
| 2 | Cloud & delivery | Where does my code run, and how does a change reach production safely? | `cloud-infrastructure`, `ci-cd-release` |
| 3 | Data | Where does the truth live, and how do I keep it correct, fast and recoverable? | `postgres-database`, `data-stores` |
| 4 | Backend | What does the server do with a request, and what does it promise other systems? | `backend-architecture`, `api-design`, `email-notifications`, `payments-billing`, `ai-features` |
| 5 | Trust | Who is this, what may they do, and what keeps attackers and regulators away? | `auth-identity`, `web-security`, `privacy-compliance` |
| 6 | Frontend | What runs in the user's browser, on any device? | `frontend-foundations`, `react-nextjs`, `3dui` |
| 7 | Design & accessibility | Can every person see it, understand it and finish the task? | `ui-ux-design`, `accessibility` |
| 8 | Engineering craft | How do I keep changing the code quickly without breaking it? | `git-collaboration`, `code-quality`, `ai-coding-agents`, `engineering-leadership` |
| 9 | Operations | Is it up, is it fast, and what happens when it is not? | `site-reliability`, `web-performance` |
| 10 | Product | What should I build next, and is it working for users? | `product-discovery`, `product-analytics` |
| 11 | Growth & revenue | How do customers find it, pay for it and stay? | `growth-marketing`, `pricing-monetization`, `sales-support` |
| 12 | Company | How does this become a business that lasts? | `company-building`, `startup-finance` |

## Skills

11 of 32 are finished so far; the rest are being written and reviewed, the most used first. `roadmap`, the map of the set, is written last.

| Skill | What it covers | Reference files | Competencies | Status |
|---|---|---|---|---|
| `linux-server` | Set up, harden, script and diagnose the Linux machine your code runs on, from CPU, memory and disk limits to systemd, SSH and container internals. | 7 | 57 | planned |
| `web-networking` | Configure and debug everything between the browser and the app: IP and transport, DNS and domains, TLS, HTTP and its caching, CDN and edge protection, reverse proxies and load balancers. | 8 | 73 | planned |
| [`cloud-infrastructure`](skills/cloud-infrastructure/SKILL.md) | Choose where the product runs and build it: hosting model, container images, Kubernetes, serverless and edge runtimes, cloud networking, IAM, infrastructure as code and cost control. | 8 | 62 | built and reviewed |
| [`ci-cd-release`](skills/ci-cd-release/SKILL.md) | Get a change from a merged pull request to production safely: CI pipelines, pipeline security, environments and config, zero-downtime deploys, rollback and feature flags. | 5 | 37 | built and reviewed |
| [`postgres-database`](skills/postgres-database/SKILL.md) | Model, query, migrate, tune, back up and scale a relational database, with PostgreSQL as the default: schemas, SQL, transactions, indexes, zero-downtime migrations, operations and recovery. | 8 | 68 | built and reviewed |
| `data-stores` | Decide when a product needs more than Postgres and run what it adds: Redis caching, search, object storage, event streams, an analytics warehouse and pipelines, and the data lifecycle across all of them. | 6 | 47 | planned |
| [`backend-architecture`](skills/backend-architecture/SKILL.md) | Structure the server side of a product: runtime choice, monolith and service boundaries, consistency under concurrency, multi-tenancy, background jobs, realtime features, file uploads and resilient third-party integrations. | 8 | 75 | built and reviewed |
| [`api-design`](skills/api-design/SKILL.md) | Design, document and evolve HTTP APIs and webhooks: style choice, request and response contracts, errors, pagination, idempotency, rate limits, versioning and a public developer platform. | 6 | 45 | built and reviewed |
| `email-notifications` | Send transactional email, SMS, push and in-app notifications that arrive, render and are wanted: provider setup, SPF, DKIM and DMARC, sender reputation, templates, channel choice and user preferences. | 4 | 33 | planned |
| [`payments-billing`](skills/payments-billing/SKILL.md) | Take money correctly: checkout integration, subscriptions and entitlements, usage billing, invoices and tax, refunds, disputes and fraud, ledger and reconciliation, and catalog, cart, inventory and fulfillment. | 8 | 66 | built and reviewed |
| `ai-features` | Design LLM-powered product features that are useful, safe and affordable: when to use a model, prompts and context, retrieval, agents and tools, evaluations, guardrails, cost and latency, streaming UX and data handling. | 8 | 64 | planned |
| [`auth-identity`](skills/auth-identity/SKILL.md) | Build sign-in and access control that resist takeover: auth architecture, sessions and tokens, passwords, MFA and passkeys, OAuth and OIDC, enterprise SSO, authorization models, account recovery and abuse defense. | 8 | 64 | built and reviewed |
| [`web-security`](skills/web-security/SKILL.md) | Build and run the product so it resists attack: threat modeling, vulnerability classes, browser security headers, secrets and cryptographic choices, the software supply chain, hardening of company accounts and admin tools, security logging and breach response, and security testing. | 8 | 69 | built and reviewed |
| `privacy-compliance` | Keep the product lawful and sellable: GDPR and US privacy law, consent and cookies, data-subject requests and retention, DPAs and vendors, PCI, SOC 2 and ISO 27001, sector and consumer rules, terms and policies, and software licenses. | 8 | 61 | planned |
| [`frontend-foundations`](skills/frontend-foundations/SKILL.md) | Build on the web platform itself: semantic HTML, CSS layout and responsive design, JavaScript and TypeScript, the browser's rendering and events, forms, animation, internationalization, and PWA and mobile packaging. | 8 | 72 | built and reviewed |
| [`react-nextjs`](skills/react-nextjs/SKILL.md) | Build the application layer of the frontend with React and a meta-framework: rendering strategy per route, where editable content lives, server components and server functions, data and state, routing, component architecture and build tooling. | 6 | 49 | built and reviewed |
| [`3dui`](skills/3dui/SKILL.md) | Build live 3D product websites with three.js and Next.js: the object is code, lit like a photo studio and directed by the scroll. | engine + templates | 10 | built and tested |
| [`ui-ux-design`](skills/ui-ux-design/SKILL.md) | Design interfaces people understand and enjoy: visual design, design tokens and component systems, UX flows, information architecture, usability testing, microcopy, motion and dark mode. | 8 | 58 | draft, review pending |
| `accessibility` | Make the product usable by people with disabilities and meet WCAG 2.2 AA: names, roles and ARIA, keyboard and focus, accessible forms, visual and cognitive access, and testing and audits. | 5 | 35 | planned |
| `git-collaboration` | Use git and the repository as a team tool: the git model and recovery, branching workflow, pull requests and code-review practice, monorepos, and versioning, changelogs and release notes. | 5 | 35 | planned |
| `code-quality` | Keep code correct and changeable: test strategy, unit, integration, end-to-end, contract and visual tests, test data and flaky tests, debugging method, refactoring, static analysis and types, and technical documentation. | 8 | 67 | planned |
| `ai-coding-agents` | Get reliable work out of coding agents such as Claude Code: scoping and specs, context and project setup, verification and review, parallel and automated runs, and permissions and governance. | 5 | 35 | planned |
| `engineering-leadership` | Make the technical decisions a CTO makes: technology strategy, build versus buy and vendor choice, decision records, estimation and planning, technical debt, and hiring and onboarding engineers. | 6 | 41 | planned |
| `site-reliability` | Know what production is doing and keep it up: logs, errors, metrics and traces, dashboards and alerts, SLOs, incident response, postmortems and runbooks, capacity and scaling, and disaster recovery. | 8 | 64 | planned |
| `web-performance` | Make pages and endpoints fast and keep them fast: Core Web Vitals, loading and delivery, JavaScript bundles, images and fonts, rendering and runtime, backend latency and profiling, load testing, and performance budgets. | 8 | 55 | planned |
| `product-discovery` | Decide what to build and why: customer interviews, problem validation, jobs-to-be-done, MVP scoping, specs, prioritization and roadmaps, and the feedback loops that tell you whether it worked. | 6 | 47 | planned |
| `product-analytics` | Instrument the product and decide what to measure: event taxonomy and tracking, funnels and activation, cohorts and retention, north-star metrics and metric trees, A/B test design and its traps, and attribution. | 6 | 39 | planned |
| `growth-marketing` | Get the product found and tried: positioning and messaging, landing pages and conversion, launches, content, lifecycle email, paid acquisition, referral and product-led loops, and community and partnerships. | 8 | 55 | planned |
| `pricing-monetization` | Decide how the product makes money: revenue model and value metric, price setting, plans and packaging, discounts and price changes, and the unit economics that show whether it works. | 5 | 32 | planned |
| `sales-support` | Win customers and keep them: prospecting and outreach, discovery calls and demos, proposals and contracts, procurement and security questionnaires, onboarding, support operations, customer success and churn, and reviews. | 8 | 62 | planned |
| `company-building` | Build the company around the product: strategy and moats, incorporation and founder legal basics, hiring, managing people, operating cadence and culture, and the founder's own effectiveness. | 6 | 50 | planned |
| `startup-finance` | Run the company's money: bookkeeping and tax, cash and runway forecasting, funding strategy, the fundraising process, equity and the cap table, and exit and due diligence. | 6 | 46 | planned |

## How a skill is shaped

```
skills/<name>/
├── SKILL.md           stance, route table, defaults by stage, done-checks, what it hands to other skills
└── references/*.md    one file per sub-area, read only when the task needs it
```

Advice is tagged by stage: **Prototype** (no real users yet), **Launch** (real users and first revenue), **Scale** (meaningful traffic or revenue, and a team). The default stack the skills assume when you have not chosen one is TypeScript, Next.js, PostgreSQL, Stripe and a PaaS; every skill follows what your project already uses first.

## How the set is built and extended

The `plan/` folder is the source of the tree and of every skill:

- `plan/layers.json` and `plan/skills/<name>.json`: the layers, and for each skill its triggers, its hand-offs and the competencies each reference file must cover.
- `plan/build.py`: validates the plan (every competency exactly once, size limits, hand-offs that point at real skills) and writes `plan/tree.md` and `plan/index.md`.
- `plan/WRITING.md`: the standard every skill is written to.
- `plan/check_skill.py <name>`: checks a written skill against its plan entry and the standard.
- `plan/make_roadmap.py`: regenerates `TREE.md`, this README and the roadmap skill's tree files.

To add or change a skill: edit its plan entry, run `python3 plan/build.py`, write the files to the standard, run `python3 plan/check_skill.py <name>`, then `python3 plan/make_roadmap.py`.

Each skill was written from its plan entry, then reviewed by a second, adversarial pass that checked commands, code, numbers and vendor facts and fixed what it found. That lowers the error rate; it does not make it zero. Legal, tax and accounting sections describe common practice and say where a professional is needed.
