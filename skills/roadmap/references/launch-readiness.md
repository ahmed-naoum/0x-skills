# Launch readiness

Read this when: a launch date is set, the founder asks what is missing before launch or before
taking the first payment, or an existing project needs a gap check across every layer.

## How to run the check

1. Fix the scope: what launches, the date and whether it can move, whether it takes money, and
   who the users are (businesses or consumers, countries, children, health or financial data).
2. Inventory what exists before asking (see "Checking an existing project").
3. Walk the layers. Mark each check pass, fail or unknown. A check passes only when it was done:
   an untested backup or an unpracticed rollback counts as absent, and unknown counts as fail.
4. Rank the gaps and give each a decision: fix before launch, accept with a date, or accept with
   a written reason. Launch can go ahead with accepted gaps, never with unknown ones and never with an open gap
   in tiers 1, 2 or 4 (tier 3 as well when it takes money).
5. Hand each fix to the skill named in its row.

The operational core is the readiness table in `0x:site-reliability` `references/postmortems-runbooks.md`;
the layers below extend it to the whole product.

## Ranking the gaps

| Tier | What | Examples | Rule |
|---|---|---|---|
| 1 | Data loss | No point-in-time recovery, no restore ever done, uploads not backed up, a destructive migration pending | Blocks launch |
| 2 | Security | Cross-tenant reads, secrets in the repository or bundle, no MFA on company accounts, hand-rolled auth, exposed admin | Blocks launch |
| 3 | Billing errors | Unverified webhooks, prices from the client, no idempotency, access not tied to subscription state, tax undecided | Blocks taking money |
| 4 | Blindness | No error tracker, no uptime alert to a phone, no practiced rollback | Blocks launch |
| 5 | Legal exposure | No privacy policy or terms, trackers before consent, no DPA where customers need one | Fix before launch unless the founder accepts it in writing |
| 6 | Reach | Email failing authentication, broken signup on phones | Fix before announcing |
| 7 | Quality | Accessibility failures on core flows, slow pages, missing screen states | Accept with a date if needed |
| 8 | Growth and operations | No onboarding email, no help articles | Accept and schedule |

Inside a tier, rank by irreversibility first, then by how many users it touches, then by how
much cheaper it is to fix now. Anything irreversible outranks anything embarrassing.

## Layer by layer

Layer 0, Machine & OS. Only when the product runs on a server the founder manages; on a PaaS,
skip all but time handling.

| Check at Launch | Detail |
|---|---|
| SSH by key only, root login and password login off; inbound default-deny at the provider firewall and on the host except SSH, 80 and 443; no Docker-published port reachable from outside (`nc -vz -w 5 host <port>` times out) | `0x:linux-server` `references/ssh-hardening.md` |
| Security updates install unattended; reboots happen on a schedule | `0x:linux-server` `references/packages-updates.md` |
| Every service restarts on failure and survives a reboot (proved by rebooting); disk usage alert and log rotation in place | `0x:linux-server` `references/processes-systemd.md`, `references/hardware-resources.md` |
| Timestamps stored in UTC, converted only at the edges | `0x:linux-server` `references/time-encoding.md` |

Can wait until Scale: kernel tuning, custom images, container-runtime internals.

Layer 1, Network.

| Check at Launch | Detail |
|---|---|
| Domain in a company-owned registrar account with MFA, lock and auto-renew; an expiry alert outside the registrar | `0x:web-networking` `references/dns-domains.md` |
| HTTPS everywhere; one canonical host, other variants redirected in one hop; HSTS staged toward one year; a certificate expiry alert | `0x:web-networking` `references/tls-certificates.md` |
| Fingerprinted assets cached `immutable`, authenticated responses `no-store` by default; origin reachable only through the CDN; edge rate limits on expensive endpoints | `0x:web-networking` `references/http-caching.md`, `references/cdn-edge.md` |

Can wait until Scale: WAF in block mode, registry lock, a second DNS provider, HSTS preload.

Layer 2, Cloud & delivery.

| Check at Launch | Detail |
|---|---|
| Budget alerts on every account; caps on scalers and metered APIs | `0x:cloud-infrastructure` `references/cost-control.md` |
| Root identity with phishing-resistant MFA and no access keys; production separated | `0x:cloud-infrastructure` `references/iam-accounts.md` |
| Database and admin ports time out from outside (`nc -vz -w 5 host 5432`) | `0x:cloud-infrastructure` `references/cloud-networking.md` |
| Every pull request runs typecheck, lint, tests and build; main requires the check; end-to-end tests cover signup, login and payment | `0x:ci-cd-release` `references/ci-pipelines.md` |
| Rollback done once in production, under 5 minutes; migrations run once, before rollout | `0x:ci-cd-release` `references/deploy-rollback.md` |
| Config parsed by a schema at boot; non-production cannot reach production data, charge cards or email real users | `0x:ci-cd-release` `references/environments-config.md` |
| Actions pinned to commit SHAs, `permissions` declared, cloud access through OIDC | `0x:ci-cd-release` `references/pipeline-security.md` |

Can wait until Scale: Kubernetes, canary releases, staging, provenance, policy as code.

Layer 3, Data.

| Check at Launch | Detail |
|---|---|
| Point-in-time recovery of 7 days or more, an off-provider dump, a timed restore drill on record | `0x:postgres-database` `references/backup-recovery.md` |
| The app connects as a non-owner role with statement, lock and idle-in-transaction timeouts; pools fit the connection limit | `0x:postgres-database` `references/postgres-operations.md` |
| Invariants are constraints; money is integer minor units; each foreign key has an index and a deliberate `ON DELETE` | `0x:postgres-database` `references/schema-modeling.md` |
| Migrations set `lock_timeout`, build indexes `CONCURRENTLY`, and work with the previous release | `0x:postgres-database` `references/migrations.md` |
| Buckets private, downloads through short-lived signed URLs, every object tied to a row, uploads backed up | `0x:data-stores` `references/object-storage.md` |
| Personal data classified with where each class lives and how long it is kept | `0x:data-stores` `references/data-lifecycle.md` |

Can wait until Scale: replicas, a standby (unless an hour of downtime costs more than a month of
it), partitioning, a warehouse, a search engine.

Layer 4, Backend.

| Check at Launch | Detail |
|---|---|
| Every outbound call has a timeout and bounded retries | `0x:backend-architecture` `references/integrations-resilience.md` |
| Jobs enqueued in the business transaction, idempotent, with heartbeats on critical schedules | `0x:backend-architecture` `references/background-jobs.md` |
| Tenant scope enforced in the data layer, with isolation tests in CI | `0x:backend-architecture` `references/multi-tenancy.md` |
| Graceful shutdown: readiness fails, in-flight work drains, then exit | `0x:backend-architecture` `references/runtime-language.md` |
| Idempotency keys wherever money, messages or third-party calls are involved; per-tenant rate limits, stricter on auth; inbound webhooks verified on raw bytes, stored in an inbox and deduped | `0x:api-design` `references/idempotency-rate-limits.md`, `references/webhooks.md` |
| Payment webhook verified and deduped; totals computed server-side; live and test keys separate | `0x:payments-billing` `references/checkout-integration.md` |
| Subscription lifecycle run on the provider's simulated clock with assertions on access | `0x:payments-billing` `references/subscriptions.md` |
| A scheduled reconciliation job compares provider and database and alerts on mismatches | `0x:payments-billing` `references/ledger-reconciliation.md` |
| Tax decision recorded; invoices carry the legal entity and its tax ID, and a gapless sequential number where the seller's country requires one (many VAT countries do) | `0x:payments-billing` `references/invoices-tax.md` |
| Refund policy published; dispute alerts on | `0x:payments-billing` `references/refunds-disputes-fraud.md` |
| SPF, DKIM and DMARC aligned; separate streams; bounces and complaints suppressed | `0x:email-notifications` `references/deliverability.md` |
| AI features: a hard spend limit at the provider, per-user quotas checked before each call, an eval set gating prompt and model changes | `0x:ai-features` `references/cost-latency.md`, `references/evals.md` |

Can wait until Scale: extracted services, durable execution, an own WebSocket tier, a public API
platform, usage billing, a second processor, dedicated sending IPs, DMARC at reject.

Layer 5, Trust.

| Check at Launch | Detail |
|---|---|
| Passkey or hardware-key MFA on email, registrar, repository, cloud, payments and password manager; a second way in; the admin panel and internal tools behind an identity-aware proxy, no inbound port open | `0x:web-security` `references/accounts-admin-hardening.md` |
| No secret in the repository, image or client bundle; push protection where the plan includes it, gitleaks or TruffleHog in pre-commit and CI regardless | `0x:web-security` `references/secrets.md` |
| Baseline security headers on every response; CSP rolled out report-only first | `0x:web-security` `references/browser-security.md` |
| Lockfile committed, frozen installs, dependency alerts on | `0x:web-security` `references/supply-chain.md` |
| Audit table for auth, permission, money and admin events; a one-page incident plan; `security.txt` published | `0x:web-security` `references/logging-breach-response.md`, `references/security-testing.md` |
| A test shows another tenant gets 404 on every endpoint | `0x:auth-identity` `references/authorization.md` |
| Session cookie `HttpOnly`, `Secure`, `SameSite`; logout and password change revoke server-side; MFA required for owners and admins | `0x:auth-identity` `references/sessions-tokens.md`, `references/passwords-mfa-passkeys.md` |
| Login, signup, reset and code verification rate-limited per account and per IP | `0x:auth-identity` `references/abuse-defense.md` |
| Account deletion flow and an account lock switch exist | `0x:auth-identity` `references/account-recovery.md` |
| Privacy policy and terms match the real data flows; acceptance recorded with its version | `0x:privacy-compliance` `references/terms-policies.md` |
| EU, EEA, UK and Swiss visitors: opt-in blocks non-essential trackers, reject as easy as accept; US visitors: an opt-out of sale and sharing that honors Global Privacy Control | `0x:privacy-compliance` `references/consent-cookies.md` |
| DPAs signed with processors; a subprocessor list exists | `0x:privacy-compliance` `references/vendors-dpas.md` |
| A runbook to fulfill deletion and export requests across every system | `0x:privacy-compliance` `references/data-subject-requests.md` |
| Auto-renewal, cancellation and price-display rules checked for consumer subscriptions | `0x:privacy-compliance` `references/sector-consumer-rules.md` |
| Dependency licenses checked for copyleft conflicts | `0x:privacy-compliance` `references/licenses-ip.md` |

Can wait until Scale, unless a buyer asks: SOC 2 or ISO 27001, a penetration test, bug bounty,
SIEM, enterprise SSO and SCIM, a sessions and devices page.

Layer 6, Frontend.

| Check at Launch | Detail |
|---|---|
| Loading, error and not-found states per data segment; the error tracker wired in | `0x:react-nextjs` `references/routing-navigation.md` |
| Session and authorization checked in every server function, not only in the `proxy` file | `0x:react-nextjs` `references/server-components.md` |
| Forms validate on the server, survive double submit and keep input on error; core flows work at phone width with no horizontal scroll | `0x:frontend-foundations` `references/forms.md`, `references/css-layout.md` |

Can wait until Scale: PWA and offline, a component workshop, virtualization, typed routes.

Layer 7, Design & accessibility.

| Check at Launch | Detail |
|---|---|
| Every screen has empty, loading, error and success states | `0x:ui-ux-design` `references/ux-flows.md` |
| Error messages say what happened and what to do next | `0x:ui-ux-design` `references/microcopy.md` |
| A few target users completed the core task unassisted | `0x:ui-ux-design` `references/usability-testing.md` |
| axe in CI on key flows; keyboard and screen-reader pass on sign-up, sign-in, core task, payment | `0x:accessibility` `references/testing-audits.md` |
| Labels on every field, errors tied to fields and announced; text contrast 4.5:1; focus ring visible | `0x:accessibility` `references/accessible-forms.md`, `references/visual-cognitive.md` |

Can wait until Scale: a third-party audit and conformance report (unless a contract or law
requires one), dark mode, a full design system.

Layer 8, Engineering craft.

| Check at Launch | Detail |
|---|---|
| Tests cover money, auth and data-loss paths, end-to-end tests the critical journeys; `strict` TypeScript and type-aware lint rules run in CI | `0x:code-quality` `references/test-strategy.md`, `references/static-analysis-types.md` |
| A tested quickstart plus deploy and rollback notes in the repository | `0x:code-quality` `references/technical-docs.md` |
| Every deploy maps to a commit; releases tagged | `0x:git-collaboration` `references/versioning-releases.md` |
| Coding agents hold no production credentials; deploys and destructive commands need approval | `0x:ai-coding-agents` `references/permissions-governance.md` |
| Hard-to-reverse decisions recorded with their reason | `0x:engineering-leadership` `references/decision-records.md` |

Can wait until Scale: merge queue, code owners, mutation testing, monorepo tooling.

Layer 9, Operations.

| Check at Launch | Detail |
|---|---|
| A thrown error appears in the tracker with source maps, release and user ID, from both sides | `0x:site-reliability` `references/logging-errors.md` |
| External uptime check rings a phone; heartbeats on backups and billing; a zero-order alert | `0x:site-reliability` `references/dashboards-alerting.md` |
| Data, secrets, configuration and uploads backed up outside the primary account | `0x:site-reliability` `references/disaster-recovery.md` |
| Status page hosted off the app's infrastructure, with templates | `0x:site-reliability` `references/incident-response.md` |
| Two app instances, or a measured single-instance recovery time | `0x:site-reliability` `references/capacity-scaling.md` |
| Field Core Web Vitals measured; one audit with a ranked fix list; a byte budget on client JavaScript fails CI | `0x:web-performance` `references/core-web-vitals.md`, `references/performance-budgets.md` |

Can wait until Scale: SLOs with burn-rate alerts, an on-call rotation, multi-region, chaos
testing, routine load tests (Launch only for a dated spike).

Layer 10, Product.

| Check at Launch | Detail |
|---|---|
| A tracking plan of 15 to 30 events, facts sent server-side, internal accounts excluded; an activation event and its funnel | `0x:product-analytics` `references/event-tracking.md`, `references/funnels-activation.md` |
| A one-page spec with a success metric for what is launching | `0x:product-discovery` `references/specs.md` |
| In-app feedback, and the first users onboarded by hand | `0x:product-discovery` `references/feedback-loops.md` |

Can wait until Scale: experiments, metric trees, attribution beyond first and last touch plus a
"how did you hear about us" question.

Layer 11, Growth & revenue.

| Check at Launch | Detail |
|---|---|
| Positioning written; a headline a stranger understands in five seconds; a landing page with one promise, proof and one call to action | `0x:growth-marketing` `references/positioning-messaging.md`, `references/landing-conversion.md` |
| A staged launch plan with a measurement plan | `0x:growth-marketing` `references/launches.md` |
| Few plans, one recommended, an obvious pricing page | `0x:pricing-monetization` `references/packaging-tiers.md` |
| A read support inbox, response targets, help articles for the top questions, a refund policy | `0x:sales-support` `references/support-operations.md` |

Can wait until Scale: paid acquisition beyond cheap tests, referral programs, partnerships,
security questionnaires (unless selling to larger companies).

Layer 12, Company.

| Check at Launch | Detail |
|---|---|
| A company formed once there is a contract with real liability, a co-founder or outside money (form and timing depend on the country); founder and contractor IP assigned to it; vendor accounts in its name | `0x:company-building` `references/incorporation-founders.md` |
| Business bank account separate; books kept monthly; tax filings known | `0x:startup-finance` `references/bookkeeping-tax.md` |
| Runway known in months | `0x:startup-finance` `references/runway-forecasting.md` |

Can wait until Scale: a board, fundraising process, hiring, an operating cadence beyond a weekly
review.

## Checking an existing project

In the repository:

- `package.json`, lockfile, `.env.example`: framework, auth library (maintained, or hand-rolled
  hashing and sessions?), payment SDK, ORM, test runner, every external service.
- Migrations: constraints, money types, any drop or rename not yet deployed. Workflows: required
  checks, pinned actions, declared `permissions`. Tests: do any cover auth, tenancy, payments?
- Webhook handlers verify the raw-body signature and dedupe; outbound clients have timeouts; the
  unsafe-SQL search in `0x:web-security` `references/vulnerability-classes.md` finds nothing unreviewed.

```bash
rg -n 'sk_live_|rk_live_|whsec_|-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}' --hidden -g '!.git' .
rg -n 'sk_live_|sk_test_|rk_live_|whsec_' .next/static   # secrets in the built client bundle
curl -sI https://example.com/ | grep -iE 'strict-transport|content-security|x-content-type|referrer-policy|cache-control'
dig +short TXT example.com; dig +short TXT _dmarc.example.com
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -enddate
pnpm audit --prod     # pnpm 11+; older versions call npm's retired audit endpoint
```

In the hosting accounts (the founder reads values out or grants read-only access; Claude never
needs production write credentials for this):

| Account | Look at |
|---|---|
| Database provider | Point-in-time recovery on and its window; plan tier (no idle pausing); public access; date of the last restore |
| Host | Instance count, region, variables per environment, rollback button, log drain |
| Payment provider | Live and test keys, restricted keys, webhook endpoint and its failure rate, tax settings, dispute notifications |
| Email provider | Domain verified, DKIM and Return-Path, bounce and complaint webhooks |
| Registrar and DNS | Owner, MFA, lock, auto-renew, expiry date, the card on file |
| Cloud | Budget alerts, root MFA, users with long-lived keys |
| Error tracker, uptime monitor | Present, receiving events, alerting a phone |

Report as one ranked table: gap, tier, how it was proved, owner skill and file, decision.

## Ask the user

- **What is the launch date, and can it move?** Decides which gaps are fixed and which are
  accepted. Default: tiers 1 to 4 block; the rest are accepted with dates.
- **Who are the first users and where are they?** EU residents, children, health or financial
  data each add legal checks. Default: EU users included; no children, no health data.
- **Will you take money at launch, and from whom?** Consumers add auto-renewal and cancellation
  rules; businesses add DPAs and invoices. Default: B2B subscriptions through hosted checkout.
- **Who can reach the accounts if you are unavailable?** Default: nobody yet; name a break-glass
  person before Launch.
- **How much data loss and downtime is acceptable?** Sets backup and redundancy depth. Default:
  minutes of data through point-in-time recovery, hours of downtime, one region.
