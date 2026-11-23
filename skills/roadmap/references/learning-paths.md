# Learning paths

Read this when: the founder asks what to learn next, where to start, or how to get from where
they are to a launch; or wants a study order for a stage or for their background.

## How to read a path

The tree marks every competency by level, and the level maps to the stage at which it starts
paying for itself:

| Level | Share of the tree | Learn it | Signal that it is due |
|---|---|---|---|
| ● core | 596 of 1673 | Before and during Prototype | Every shipped product needs it, whatever its size |
| ◐ pro | 789 of 1673 | At Launch | The first stranger's data, the first payment, the first support email |
| ○ expert | 288 of 1673 | At Scale, or when a named trigger appears | A contract demands it, a measurement shows the need, or a team exists to run it |

For a founder who builds with Claude, "learned" means being able to judge Claude's work in that
area: knowing the default, the condition that flips it, and the check that proves the work is
right. It does not mean memorizing the material. So each step below names one reference file to
read inside a real task, not a course to finish first. Read the file when the task touches it;
an unused competency is forgotten by the time it is needed.

Rules for building any path, including ones not listed here:

- Order by what hurts most if missing: lost data, then a takeover or leak, then wrong money, then
  being unable to notice or undo a failure, then everything else.
- Never more than five next steps in one answer. A longer list is a syllabus, and the founder
  will do none of it.
- Every step ends in something checkable ("a restore drill is on record"), not in "understand X".
- Pull an expert competency forward only on its trigger: a buyer asks for SOC 2, a deal needs SSO,
  a query plan shows the database is the bottleneck.

## Prototype: no real users yet

Goal: something a real user can try within weeks, built so that Launch does not need a rewrite.
The only things worth rigor now are those that are cheap today and expensive after data exists:
the schema, the auth choice, the tenant model, strict types, and keeping secrets out of git.

| # | Learn | Why at this point | Good enough for now |
|---|---|---|---|
| 1 | `0x:product-discovery` `references/problem-validation.md` | Code built for an unvalidated problem is the largest waste a solo founder makes | A one-sentence problem statement, a customer profile narrow enough to name 100 prospects, a pass/fail threshold written before the test |
| 2 | `0x:product-discovery` `references/mvp-scoping.md` | Scope decides how much of the tree is needed at all | One user, one job, one happy path; a list of what is faked, done by hand or bought |
| 3 | `0x:ai-coding-agents` `references/context-setup.md` | Claude is the team; setup pays back on every later task | An agent instruction file with the run, test and lint commands; one-command setup |
| 4 | `0x:ai-coding-agents` `references/verification-review.md` | The founder approves every change; knowing what to check matters more than typing code | Each change arrives with test output; auth, payment and migration diffs get a closer read |
| 5 | `0x:engineering-leadership` `references/technical-strategy.md` | Hard-to-reverse choices are made once, at the start | The house stack accepted, or each deviation written with its reason (see `house-stack.md`) |
| 6 | `0x:postgres-database` `references/schema-modeling.md` | The schema is the most expensive thing to change once data exists | Invariants as constraints, `timestamptz`, money as integer minor units with a currency, one id scheme |
| 7 | `0x:auth-identity` `references/auth-architecture.md` | Hand-rolled auth is the classic irreversible mistake | A maintained library or provider, one or two sign-in methods, rate limits on auth endpoints |
| 8 | `0x:backend-architecture` `references/multi-tenancy.md` | B2B only: a tenant column added later touches every query | `org_id` on every row, a memberships table, the tenant scope in every query |
| 9 | `0x:web-security` `references/vulnerability-classes.md` | Injection and missing ownership checks are written on day one, not added later | A schema at every entry point, parameterized queries, ownership checked on every ID received |
| 10 | `0x:web-security` `references/secrets.md` | A key pushed to a repository must be treated as leaked | Secrets in the host's store, none in the repository or client bundle; push protection where the plan includes it (a paid add-on for private GitHub repositories), gitleaks or TruffleHog in pre-commit and CI regardless |
| 11 | `0x:react-nextjs` `references/rendering-strategies.md` | Rendering per route decides caching, cost and search visibility | Public pages static, logged-in pages rendered per request on the server |
| 12 | `0x:code-quality` `references/static-analysis-types.md` | Strict types are free in the first commit and costly later | `strict` TypeScript, a formatter, `tsc --noEmit` in CI |
| 13 | `0x:git-collaboration` `references/git-model.md` | Git is the undo button for everything Claude changes | Small commits; revert and reflog recovery done once on purpose |
| 14 | `0x:cloud-infrastructure` `references/platform-choice.md` | Hosting is chosen by limits, and a PaaS has none that matter yet | A PaaS deploying on merge, compute and database in the same region, a budget alert |
| 15 | `0x:ui-ux-design` `references/ux-flows.md` | Missing screen states are what first users hit | Every screen has its empty, loading, error and success state |
| 16 | `0x:product-analytics` `references/event-tracking.md` | The first users' behavior is the only evidence worth having | 5 to 10 events, facts (signup, payment) sent from the server |

Deliberately skip at Prototype: Kubernetes, infrastructure as code on a PaaS, separate services,
Redis, a search engine, a vector database, SLOs and on-call, load tests, A/B tests, enterprise
SSO, usage billing, a double-entry ledger, tax registration work, SOC 2, a design system beyond a
few tokens, refactoring code that may be deleted, hiring, fundraising mechanics.

## Launch: real users and first paying customers

Goal: nothing irreversible can happen silently. Work through the blocks in order; within a block
the order matters less. The gap check in `launch-readiness.md` is the same list seen as an audit.

| Block | Learn | Good enough for now |
|---|---|---|
| A. Data survives | `0x:postgres-database` `references/backup-recovery.md` | Point-in-time recovery of 7 days or more, an off-provider dump, one timed restore drill on record |
| A | `0x:ci-cd-release` `references/deploy-rollback.md` | Rollback done once for real in under 5 minutes; migrations run as one step before rollout |
| A | `0x:postgres-database` `references/migrations.md` | Each migration works with the previous and next application version |
| B. Nobody else gets in | `0x:web-security` `references/accounts-admin-hardening.md` | Passkey or hardware-key MFA on email, registrar, repository, cloud and payments; company-owned; a second way in |
| B | `0x:auth-identity` `references/authorization.md` | A test shows another tenant gets 404 on every endpoint |
| B | `0x:auth-identity` `references/sessions-tokens.md` | Logout and password change revoke sessions on the server |
| C. Money is right | `0x:payments-billing` `references/checkout-integration.md` | Webhook signature verified on the raw body, events deduped, totals computed server-side, idempotency keys persisted |
| C | `0x:payments-billing` `references/subscriptions.md` | Status maps explicitly to access; renewal failure, upgrade and cancel run on the provider's simulated clock |
| C | `0x:payments-billing` `references/invoices-tax.md` | The tax decision is written down: merchant of record, or a tax engine plus registrations |
| D. Failure is noticed | `0x:site-reliability` `references/logging-errors.md` | Errors from frontend and backend arrive with readable stack traces and the release tag |
| D | `0x:site-reliability` `references/dashboards-alerting.md` | An external uptime check rang the phone; heartbeats on backup and billing jobs |
| E. Lawful and sellable | `0x:privacy-compliance` `references/terms-policies.md` | Terms and a privacy policy that match the actual data flows, acceptance recorded with its version |
| E | `0x:privacy-compliance` `references/consent-cookies.md` | EU, EEA and UK visitors: no non-essential tracker before opt-in; US visitors: an opt-out of sale and sharing that honors Global Privacy Control |
| E | `0x:company-building` `references/incorporation-founders.md` | A company formed before the first contract with real liability, a co-founder or outside money (the form depends on the country); IP assigned to it; accounts and contracts in its name |
| F. Reach and quality | `0x:email-notifications` `references/deliverability.md` | SPF, DKIM and DMARC aligned; transactional and marketing mail on separate streams |
| F | `0x:accessibility` `references/testing-audits.md` | axe in CI on key flows; a keyboard and screen-reader pass on sign-up, sign-in, the core task and payment |
| F | `0x:web-performance` `references/core-web-vitals.md` | Field data on phones at p75: LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1 |
| G. Customers arrive and stay | `0x:pricing-monetization` `references/price-setting.md` | A price set from customer value and alternatives, not from cost |
| G | `0x:growth-marketing` `references/launches.md` | A staged launch: private beta, waitlist, then public channels, with a measurement plan |
| G | `0x:sales-support` `references/support-operations.md` | A shared inbox someone reads, response targets, a written refund and cancellation policy |
| G | `0x:startup-finance` `references/bookkeeping-tax.md` | Business money in a business account; books kept monthly |

Deliberately skip at Launch: Kubernetes, multi-region, a database standby unless an hour of
downtime costs more than a month of the standby, read replicas and partitioning, SOC 2 or ISO
27001 until a buyer asks, a penetration test until a customer or framework asks, bug bounty,
SIEM, WAF block mode before tuning, published SLAs, A/B tests without the traffic to detect a
plausible lift within 4 weeks, a public API platform, outbound webhooks for customers,
enterprise SSO without a deal that needs it, a ledger unless the app holds balances, hiring.

## Scale: meaningful traffic or revenue, and a team

Scale work is pulled by signals, not by the calendar. Learn the file when its signal appears.

| Signal | Learn | Good enough for now |
|---|---|---|
| Database CPU or p95 latency climbing | `0x:postgres-database` `references/indexes-query-plans.md` | Top statements from `pg_stat_statements` explained and indexed; a bigger instance before replicas |
| Read load outgrows one instance | `0x:postgres-database` `references/replication-scaling.md` | Replicas serve only lag-tolerant reads and never decide a write |
| A second person shares on-call | `0x:site-reliability` `references/slos-error-budgets.md` | 99.9% per key journey, measured; SLA looser than the SLO |
| Incidents repeat | `0x:site-reliability` `references/postmortems-runbooks.md` | A postmortem per SEV1; actions are tickets with owners and dates |
| An enterprise deal requires SSO | `0x:auth-identity` `references/enterprise-sso.md` | Bought or bridged SSO, SCIM deprovisioning, a break-glass path |
| A buyer sends a security questionnaire | `0x:sales-support` `references/procurement-security.md` | Reusable answers backed by real controls |
| A buyer requires SOC 2 or ISO 27001 | `0x:privacy-compliance` `references/pci-soc2-iso.md` | Scope chosen, minimal policy set written and followed |
| Cloud bill grows faster than revenue | `0x:cloud-infrastructure` `references/cost-control.md` | Tags, per-customer metering, rightsizing before commitments |
| The PaaS blocks a workload | `0x:cloud-infrastructure` `references/platform-choice.md` | Managed containers in one cloud; Kubernetes only with an owner for it |
| Enough traffic to detect a lift | `0x:product-analytics` `references/experiments.md` | Sample size computed before the test; guardrail metrics |
| Search is slow or relevance poor in Postgres | `0x:data-stores` `references/search.md` | A search engine fed from the database, tenant filters inside every query |
| First hire | `0x:company-building` `references/hiring.md` | A scorecard for the role and a structured interview |
| Raising money | `0x:startup-finance` `references/fundraising-process.md` | A forecast, a data room, the cap table understood |

Skip even at Scale unless a contract or a measurement forces it: multi-region active-active,
self-hosted databases without someone who has run them, a service mesh, splitting services to
mirror an org chart, a second payment processor before the business category makes it urgent.

## Paths by starting profile

Start from the founder's strengths and fill the layers they have never had to own. Each list is
the order to learn in, interleaved with the stage path above; the stage path wins on conflicts.

### Frontend developer

Already strong in layers 6 and 7. The gaps are where the server must not trust the browser, and
everything that keeps data and money correct.

1. `0x:postgres-database` `references/schema-modeling.md`, then `references/transactions-concurrency.md`. Good enough: constraints enforce invariants, read-modify-write uses an atomic update.
2. `0x:auth-identity` `references/authorization.md`. Good enough: authorization lives in the data layer, not only in route guards or the `proxy` file.
3. `0x:web-security` `references/vulnerability-classes.md`. Good enough: every input parsed on the server, even when the form already validated it.
4. `0x:api-design` `references/requests-responses.md`. Good enough: one error shape, keyset pagination, no REST layer for the app's own UI.
5. `0x:backend-architecture` `references/background-jobs.md`. Good enough: slow work and retries run in a job, enqueued in the same transaction.
6. `0x:payments-billing` `references/checkout-integration.md`. Good enough: fulfillment on the verified webhook, never on the redirect alone.
7. `0x:site-reliability` `references/logging-errors.md`, then `0x:ci-cd-release` for rollback.

Traps for this profile: client-side checks treated as security; secrets in variables exposed to
the browser bundle; fetching everything in client effects instead of on the server; trusting a
price or quantity sent by the client. Skip: re-learning React, CSS depth, animation polish.

### Backend developer

Already strong in layers 0 to 4. The gaps are the browser, the interface, and the business.

1. `0x:react-nextjs` `references/rendering-strategies.md`, then `references/server-components.md`. Good enough: rendering chosen per route, client components only at the leaves.
2. `0x:frontend-foundations` `references/html-semantics.md`, then `references/forms.md`. Good enough: native elements, labels, server-side validation messages shown inline.
3. `0x:ui-ux-design` `references/ux-flows.md`, then `references/visual-design.md`. Good enough: screen states complete, one type scale and spacing scale.
4. `0x:accessibility` `references/keyboard-focus.md`. Good enough: every task completes by keyboard with a visible focus ring.
5. `0x:web-performance` `references/core-web-vitals.md`. Good enough: field data on phones, the LCP element in server HTML.
6. `0x:product-discovery` `references/mvp-scoping.md`, then `0x:growth-marketing` positioning and `0x:pricing-monetization` price setting.

Traps for this profile: building infrastructure before users (Kubernetes, Kafka, a separate API
service, a custom queue); a REST layer for a UI that only the app consumes; screens without
empty and error states; `div` buttons. Skip: Kubernetes, self-hosting, multi-service designs.

### Non-technical founder working through Claude

Claude writes the code; the founder decides, checks and owns the accounts. Their path is about
judgment and ownership, and their comparative advantage is the customer.

1. `0x:product-discovery` `references/customer-interviews.md`, then `references/problem-validation.md` and `references/mvp-scoping.md`. This is the founder's own job and cannot be delegated to Claude.
2. `0x:ai-coding-agents` `references/delegation-specs.md`, then `references/verification-review.md`. Good enough: each request states acceptance criteria; each result arrives with proof (test output, a screenshot, a URL).
3. `0x:ai-coding-agents` `references/permissions-governance.md`. Good enough: Claude has no production credentials; deploys, pushes and destructive commands need approval.
4. `0x:git-collaboration` `references/git-model.md`. Good enough: knows that every change is a commit and can be reverted, and asks Claude to show the diff summary.
5. `0x:web-security` `references/accounts-admin-hardening.md`. Good enough: domain, hosting, database, payment and email accounts are in the company's name, with MFA and a second way in.
6. `0x:payments-billing` `references/checkout-integration.md`. Good enough: hosted checkout; a merchant of record if they want tax handled for them.
7. `0x:postgres-database` `references/backup-recovery.md`. Good enough: knows where backups live and has watched a restore succeed.
8. `0x:privacy-compliance` `references/terms-policies.md`, then `0x:growth-marketing`, `0x:pricing-monetization` and `0x:sales-support` as launch nears.

Red flags this founder should learn to recognize and question: Claude proposing to write its own
password hashing or session code, to store card numbers, to skip webhook signature checks, to
use the production database from a development machine, to delete or loosen a failing test to
make CI pass, or to run a migration that drops or renames a column in one step. Skip: learning
syntax in depth, CSS, Kubernetes, server administration. Bring in a professional for
incorporation, tax and contracts; the skills explain the mechanism, not jurisdiction-specific
advice.

## Ask the user

- **Which stage is the product in?** Paths differ more by stage than by topic. Default: Prototype
  if nobody has paid yet, Launch if someone has or a launch date exists.
- **What is your background?** Picks the profile path. Default: infer it from the repository and
  the conversation, and ask once if unclear.
- **Is the product sold to businesses or to consumers?** B2B pulls tenancy, SSO and procurement
  earlier; B2C pulls abuse defense, consent and page speed earlier. Default: B2B SaaS.
- **Will it take money at launch?** Moves payments, tax and company formation into the Launch
  path. Default: yes, through hosted checkout.
- **How much time goes to learning versus building?** Sets the length of each answer. Default:
  learning happens inside the work, one reference file per task, at most five next steps.
