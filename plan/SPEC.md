# Plan spec: the web-development skill tree

## What this is for

One person — a solo developer-founder who builds web products with Claude Code — wants two things:

1. **A tree** of everything you must be able to do to build, ship, run and sell a web product,
   from the physical machine and the network up to customers and the company. It is their
   learning roadmap.
2. **A set of Claude skills** (expert playbooks loaded on demand) that together cover every
   branch of that tree, so Claude works at staff/principal level across the whole stack.

The plan in this folder is the single source for both: it defines the layers, the skills, the
reference files inside each skill, and the leaves (competencies) each reference file must teach.
Writers will later turn each skill entry into a `SKILL.md` plus one markdown file per reference.

## Design decision already made (do not reopen)

Few deep skills, not many thin ones. Every skill's description is always in Claude's context, so
each extra skill costs every session; reference files cost nothing until read. So: **26–32
skills**, each a branch of the tree with **3–8 reference files**, and all the depth lives in the
reference files.

## Files

- `layers.json` — ordered list, machine first, company last:
  `[{"id": 0, "name": "Machine & OS", "question": "What is my code actually running on?"}, ...]`
  9–13 layers. `question` is the plain-language question that layer answers.
- `skills/<name>.json` — one file per skill:

```json
{
  "name": "networking",
  "layer": 1,
  "title": "Networking",
  "summary": "One sentence: what Claude can do for the user with this skill loaded.",
  "useWhen": ["5–10 concrete situations or phrases, the way a user would actually put the task"],
  "notFor": [{"topic": "what a user might wrongly expect here", "use": "name of the skill that owns it"}],
  "references": [
    {
      "file": "dns.md",
      "title": "DNS",
      "purpose": "One line: when Claude should read this file.",
      "leaves": [
        {"topic": "Choose record types and TTLs for a new domain and its subdomains", "level": "core"}
      ]
    }
  ]
}
```

- `build.py` — merges and validates. Run `python3 build.py` from this folder after every change.
  It writes `plan.json` (merged) and `tree.md` (compact outline: read this to see the whole
  tree at once) and prints every error and warning. **The plan is not done until it prints
  `0 errors`.**

## Rules

- **Skill names**: lowercase kebab-case, 1–3 words, specific (`web-performance`, not
  `performance`). No prefix — the plugin namespace adds one.
- **Skill boundaries follow how tasks arrive**, not an academic taxonomy. Ask: "what is the user
  asking for at the moment this skill should load?" Two skills must never both be the obvious
  answer to the same request; where it's close, each gets a `notFor` entry pointing at the other.
- **A leaf is one competency**, phrased as something you can DO or DECIDE, at most ~14 words:
  "Read an EXPLAIN plan and fix a sequential scan", not "Databases" or "Understand indexes".
- **Levels**: `core` = needed to ship a real product at all; `pro` = needed to run it in
  production with paying customers; `expert` = specialist depth, needed at scale. Roughly
  40% core, 40% pro, 20% expert overall — a tree that is all "expert" is useless as a roadmap.
- **Every leaf appears exactly once** in the whole plan. If two skills need the same idea, one
  owns the leaf and the other points to it via `notFor`.
- **Sizes**: 3–8 references per skill, 5–10 leaves per reference, 5–10 `useWhen`, 1–6 `notFor`.
- **Reference file names**: lowercase kebab-case ending `.md`, unique within the skill.
- Current year is 2026. Include what current practice requires; leave out what is obsolete.

## Already installed — do not duplicate, point to them with `notFor`

| Topic | `use` value |
|---|---|
| SEO, answer-engine and AI-search optimisation (27 skills already) | `seo-aeo-geo-ultimate` |
| Data analysis, analytics SQL, statistics, dashboards from query results | `data` |
| Chart and data-visualisation design | `dataviz` |
| Claude / Anthropic API details: model ids, params, tool use, caching, SDK | `claude-api` |
| Reviewing a diff for bugs | `code-review` |
| Reviewing pending changes for vulnerabilities | `security-review` |

A skill here may still own the *design-level* side of those (e.g. "decide whether a feature needs
RAG or a tool call" belongs here; the API call syntax belongs to `claude-api`).

## The one existing skill

`3dui` already exists and must appear in the plan, in the frontend layer, as:

```json
{
  "name": "3dui", "existing": true, "layer": <frontend layer id>, "title": "Live 3D product sites",
  "summary": "Build live 3D product websites with three.js and Next.js: the object is code, lit like a photo studio and directed by the scroll.",
  "useWhen": [...], "notFor": [...],
  "references": [{"file": "SKILL.md", "title": "Live 3D product sites", "purpose": "...", "leaves": [...]}]
}
```

Its content: procedural geometry in real millimetres (2D signed-distance shapes → marching-squares
trace → bevelled extrude; lathe-turned parts), physical metal and glass materials with brushed
anisotropic finishes, a PMREM studio-lighting environment rotated by the cursor, a scroll-driven
camera cue list that frames by size, staggered exploded views with two-column callouts, a
blueprint (edges-only) mode, one shared clock for all motion, Web Audio synthesized sound, a
hold-to-act gesture that unlocks audio and tilt, film-style post (MSAA HDR, bloom, ACES, grain),
adaptive quality for phones. It counts toward the 26–32 and is exempt from the 3–8 references rule.

A `roadmap` skill (the tree itself plus how to learn from it) will be written separately — do
not include it.

## Coverage floor

Every area below must be represented by at least one reference file somewhere. Group them into
skills however task boundaries dictate; several areas may share a skill, and a large area may
span more than one.

- **Machine & OS** — hardware resources and limits (CPU, memory, disk, network card); Linux
  processes, files, permissions, systemd, shell; package management; SSH; virtualisation and
  container internals; time, timezones, text encoding.
- **Network** — IP, TCP/UDP/QUIC; DNS; TLS and certificates; HTTP semantics and caching;
  HTTP/2 and HTTP/3; CDN and edge; proxies and load balancers; WebSockets, SSE, WebRTC; domains
  and email deliverability (SPF, DKIM, DMARC); network debugging tools.
- **Cloud & delivery** — compute/storage/network primitives; IAM; infrastructure as code; Docker
  images; choosing PaaS vs serverless vs containers vs Kubernetes; edge runtimes; CI/CD;
  environments, config and secrets; release strategies and rollback; feature flags; cost control.
- **Data** — relational modelling; SQL; transactions and isolation; indexes and query plans;
  zero-downtime migrations; Postgres operations; backup and restore; replication; choosing
  non-relational stores; caching; queues and streams; search; object storage and files;
  analytics warehouse and pipelines; data lifecycle and deletion.
- **Backend** — language and runtime choice; API design (REST, GraphQL, gRPC, webhooks);
  validation, errors, pagination, idempotency, rate limiting; background and scheduled jobs;
  architecture (monolith, modular, services, events); concurrency and consistency;
  multi-tenancy; file uploads; email, SMS and push notifications; third-party integrations;
  realtime features.
- **Identity** — sessions, cookies, tokens; passwords; MFA; passkeys; OAuth and OIDC; enterprise
  SSO (SAML, SCIM); authorisation models; account recovery; bot and abuse defence.
- **Payments & commerce** — checkout; subscriptions; usage billing; invoices; sales tax and VAT;
  refunds, chargebacks and fraud; ledger and reconciliation; e-commerce catalogue, cart,
  inventory and fulfilment.
- **Frontend** — HTML semantics; CSS layout and responsive design; JavaScript and TypeScript;
  the browser rendering pipeline; DOM and events; forms; React and Next.js rendering strategies;
  state and data fetching; routing; build tooling; PWA and offline; internationalisation;
  mobile (responsive, wrappers, the native boundary); animation; 3D (the existing `3dui`).
- **Design** — visual design (type, colour, spacing, layout); design tokens and component
  systems; UX flows; information architecture; usability testing; microcopy; motion; dark mode.
- **Accessibility.**
- **Performance** — Core Web Vitals; loading; rendering; bundles; images and fonts; caching
  layers; backend and database latency; load testing; profiling.
- **Quality** — test strategy; unit, integration, end-to-end, contract and visual tests; test
  data; flaky tests; debugging method; refactoring; code review practice; static analysis and
  types; technical documentation.
- **Security** — threat modelling; the OWASP vulnerability classes; input and output handling;
  security headers, CSP, CORS; secrets; dependencies and supply chain; infrastructure hardening;
  security logging; incident response; penetration testing basics.
- **Privacy & compliance** — GDPR and CCPA; consent and cookies; data-subject requests;
  retention; DPAs and subprocessors; PCI scope; SOC 2 and ISO 27001; accessibility law; terms
  and privacy policy; open-source licences.
- **Operations** — logs, metrics, traces; dashboards; alerting; SLOs and error budgets; on-call
  and incident management; postmortems; capacity and scaling; disaster recovery; status pages;
  runbooks.
- **Git & collaboration** — the git model; branching; pull requests; monorepos; versioning,
  changelogs and release notes.
- **Product** — customer-discovery interviews; problem validation; jobs-to-be-done; MVP scoping;
  specs; prioritisation; roadmaps; feedback loops.
- **Analytics & experimentation** — event taxonomy; funnels; cohorts and retention; north-star
  and metric trees; A/B tests and their statistical traps; attribution.
- **Growth** — positioning and messaging; landing pages and conversion; launches; content; email
  and lifecycle; paid acquisition; referral loops; community; partnerships. (SEO: pointer only.)
- **Pricing & monetisation.**
- **Sales & customers** — B2B sales process; demos; proposals and contracts; procurement and
  security questionnaires; onboarding; support operations; customer success; churn; reviews.
- **Company** — business models and unit economics; incorporation and equity basics; founder
  legal basics (terms, IP, contractors); bookkeeping, tax and runway; fundraising vs
  bootstrapping; hiring and managing; process and culture; strategy and moats; exit and due
  diligence.
- **Engineering leadership** — technical strategy; build vs buy; architecture decision records;
  estimation and planning; technical debt; hiring and onboarding engineers.
- **AI in the product** — designing LLM features; retrieval; agents and tools; evaluations;
  guardrails; cost and latency; streaming UX; data and privacy.
- **AI-assisted development** — working with coding agents: specs, context, review, tests.
