---
name: roadmap
description: "Map of the 0x skill set for a solo founder: what to learn next and in what order for their stage and background, a whole-product launch gap check ranked by data loss, security and billing risk, which 0x skill and reference file owns a topic, and the stack the skills assume. Use when asked what to learn, where to start, am I ready to launch, which skill covers X, or how big the field is."
---

# roadmap: the map of the 0x set

The 0x set covers web development from the machine to the customer as a tree of 13 layers, 32
skills and 1673 competencies, each marked ● core, ◐ pro or ○ expert. This skill answers questions
about the tree rather than inside it: what matters now for this founder and this product, in what
order, and which skill holds the procedure. It does not do the work; it names the owner and hands
over.

1. **Stage first.** Settle Prototype, Launch or Scale from the repository and the conversation
   before answering. The same question has a different answer at each stage, and the wrong stage
   produces either a premature system or a missing safeguard.
2. **Core, then pro, then expert.** Core competencies before and during Prototype, pro ones when
   real users and money arrive, expert ones at Scale or on a named trigger (a contract, a
   measurement, a team). Expert work done early costs attention and adds systems to run.
3. **Irreversible before embarrassing.** Order every list by what cannot be undone: data loss,
   then security, then billing errors, then the inability to notice or roll back a failure. A
   slow page can be fixed next week; a lost table or a leaked customer record cannot.
4. **Learning means judging Claude's work.** Knowing an area means knowing its default, the
   condition that flips it, and the check that proves the work. Assign one reference file per real
   task, at most five next steps per answer, never a syllabus.
5. **Follow the project first.** What the repository already uses beats the house stack; the
   defaults are for greenfield choices and direct questions.
6. **Proof, not intent.** A gap is closed when its check was run: the restore performed, the
   rollback done, the alert rung. Configured but untested counts as missing.
7. **Route, do not duplicate.** Answer with the owning skill and its reference file. Restating
   its detail from memory here lets the two drift apart.

## How to answer

**"What should I learn next?"** Place the founder on a stage and a profile (frontend developer,
backend developer, non-technical founder working through Claude), from the repository and the
conversation; ask once if unclear. Read `references/learning-paths.md`. Give at most five steps,
each with the skill as `0x:<name>`, the reference file, why it comes now, and the good-enough
bar. Say what to skip at this stage. If the founder is in the middle of a task, the next thing to
learn is the file that owns that task.

**"Where do I start?"** No validated problem yet: start with `0x:product-discovery`, before any
code. A validated idea and no code: take the stack from `references/house-stack.md`, then follow
the Prototype path. Code exists: read the repository, place it on a stage, and continue the path
from the first unmet step.

**"What am I missing before launch?"** Read `references/launch-readiness.md`. Inventory the
repository and the hosting accounts before asking questions, walk the 13 layers, and return one
ranked table: gap, tier (data loss, security and billing errors first), how it was proved, owning
skill and file, decision (fix now, accept with a date, accept with a reason).

**"Which skill covers X?"** Read `references/skill-map.md` for the owner and its hand-offs, then
the layer file for the exact reference file. Answer in one line: the skill, the file, and why it
owns the topic. When two skills touch a topic, name the one that owns the decision and the one
that owns the mechanism. Outside the set: search visibility is `seo-aeo-geo-ultimate`, Claude API
details are `claude-api`.

**"How big is this field?"** Use the layer table below and its layer files. The tree holds 1673
competencies: 596 core, 789 pro, 288 expert. Backend (283) and Trust (194) are the largest
layers; Machine & OS (57) and Network (73) the smallest. A shipped product needs the core set
handled, mostly by following defaults, not mastered; nobody needs all of it before launching.

**"What stack should I use?" or "Should I switch?"** Read `references/house-stack.md`, check the
pairing rules, and respect what the project already runs. Deep vendor evaluation and build versus
buy belong to `0x:engineering-leadership`.

If an owning skill is not installed in this session, say so, answer from the skill map and the
layer file, and do not invent that skill's content.

## Route

| If the task is | Read |
|---|---|
| What to learn next, a study order for a stage or a background, what to skip for now | `references/learning-paths.md` |
| Which framework, tool or vendor to use, or whether to switch away from one | `references/house-stack.md` |
| What is missing before launch, or a gap check on a product already live | `references/launch-readiness.md` |
| Which skill or file owns a topic, what a skill hands off, what the set contains | `references/skill-map.md` |
| What there is to know about servers, SSH, processes, containers, time zones | `references/layer-00-machine-and-os.md` |
| What there is to know about DNS, TLS, HTTP, caching, CDNs, proxies | `references/layer-01-network.md` |
| Hosting, containers, IAM, infrastructure as code, CI, deploys, flags | `references/layer-02-cloud-and-delivery.md` |
| Postgres, Redis, search, file storage, pipelines, retention | `references/layer-03-data.md` |
| Server architecture, APIs, webhooks, email, payments, AI features | `references/layer-04-backend.md` |
| Sign-in, authorization, security, privacy law, compliance | `references/layer-05-trust.md` |
| HTML, CSS, TypeScript, React, Next.js, 3D product sites | `references/layer-06-frontend.md` |
| Visual design, UX flows, design systems, accessibility | `references/layer-07-design-and-accessibility.md` |
| Git, tests, debugging, coding agents, technical leadership | `references/layer-08-engineering-craft.md` |
| Monitoring, incidents, recovery, capacity, page and server speed | `references/layer-09-operations.md` |
| Discovery, MVP scope, specs, analytics, experiments | `references/layer-10-product.md` |
| Positioning, launches, pricing, sales, support, churn | `references/layer-11-growth-and-revenue.md` |
| Company formation, hiring, bookkeeping, runway, fundraising | `references/layer-12-company.md` |

## The tree

● core: every shipped product needs it. ◐ pro: needed once real users and money arrive.
○ expert: needed at scale or in special cases. Each layer stands on the ones above it.

<!-- layers:start -->
| # | Layer | Skills | Tree file |
|---|---|---|---|
| 0 | Machine & OS: What is my code actually running on? | `0x:linux-server` | `references/layer-00-machine-and-os.md` |
| 1 | Network: How does a request travel from a browser to my server and back? | `0x:web-networking` | `references/layer-01-network.md` |
| 2 | Cloud & delivery: Where does my code run, and how does a change reach production safely? | `0x:cloud-infrastructure`, `0x:ci-cd-release` | `references/layer-02-cloud-and-delivery.md` |
| 3 | Data: Where does the truth live, and how do I keep it correct, fast and recoverable? | `0x:postgres-database`, `0x:data-stores` | `references/layer-03-data.md` |
| 4 | Backend: What does the server do with a request, and what does it promise other systems? | `0x:backend-architecture`, `0x:api-design`, `0x:email-notifications`, `0x:payments-billing`, `0x:ai-features` | `references/layer-04-backend.md` |
| 5 | Trust: Who is this, what may they do, and what keeps attackers and regulators away? | `0x:auth-identity`, `0x:web-security`, `0x:privacy-compliance` | `references/layer-05-trust.md` |
| 6 | Frontend: What runs in the user's browser, on any device? | `0x:frontend-foundations`, `0x:react-nextjs`, `0x:3dui` | `references/layer-06-frontend.md` |
| 7 | Design & accessibility: Can every person see it, understand it and finish the task? | `0x:ui-ux-design`, `0x:accessibility` | `references/layer-07-design-and-accessibility.md` |
| 8 | Engineering craft: How do I keep changing the code quickly without breaking it? | `0x:git-collaboration`, `0x:code-quality`, `0x:ai-coding-agents`, `0x:engineering-leadership` | `references/layer-08-engineering-craft.md` |
| 9 | Operations: Is it up, is it fast, and what happens when it is not? | `0x:site-reliability`, `0x:web-performance` | `references/layer-09-operations.md` |
| 10 | Product: What should I build next, and is it working for users? | `0x:product-discovery`, `0x:product-analytics` | `references/layer-10-product.md` |
| 11 | Growth & revenue: How do customers find it, pay for it and stay? | `0x:growth-marketing`, `0x:pricing-monetization`, `0x:sales-support` | `references/layer-11-growth-and-revenue.md` |
| 12 | Company: How does this become a business that lasts? | `0x:company-building`, `0x:startup-finance` | `references/layer-12-company.md` |
<!-- layers:end -->

## Before you call it done

1. The stage is stated, and every recommendation fits it.
2. Every skill is named as `0x:<name>`, and every file named is in that skill's reference list.
3. No more than five next steps, each with why now and a checkable good-enough bar.
4. What to skip at this stage is said explicitly.
5. Gap lists are ranked with data loss, security and billing errors first, and each gap has its
   proof, its owner and a decision.
6. The project's existing choices are respected; any proposed switch names the requirement it
   serves and its cost.
7. Numbers and vendor facts held by an owning skill are pointed to, not restated from memory.
8. Every "pass" in a gap check names its evidence: a date, a command's output, a screenshot.
9. Legal and tax points say which jurisdiction they hold in and where a professional is needed.

## Not this skill

Doing the work itself belongs to the skill that owns the topic; this skill only maps and routes.

- Building, fixing or reviewing anything in an area → the owning skill, found in `references/skill-map.md`
- A full stack decision in depth, build versus buy, vendor evaluation → `0x:engineering-leadership`
- What to build, MVP scope, the product roadmap → `0x:product-discovery`
- Running the production-readiness review and writing runbooks → `0x:site-reliability`
- Directing Claude Code itself: specs, context files, permissions → `0x:ai-coding-agents`
- Search visibility and SEO → `seo-aeo-geo-ultimate`; Claude API parameters and model IDs → `claude-api`
