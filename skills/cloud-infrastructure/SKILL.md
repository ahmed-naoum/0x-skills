---
name: cloud-infrastructure
description: Chooses where a web product runs and builds that infrastructure. Covers hosting model, Docker images and Compose, Kubernetes, serverless and edge runtimes, VPC networking, cloud IAM, Terraform or OpenTofu, and cloud cost. Use when deciding between a PaaS, VPS, containers or Kubernetes, writing a Dockerfile, setting up AWS, GCP or Azure accounts, debugging pods or cold starts, or cutting a cloud bill.
---

# Cloud infrastructure and hosting

## Stance

Infrastructure for a solo founder is a cost paid in attention before it is a cost paid in money. The expert move is usually the smaller one: stay on
the platform that works, put compute next to the database, cap everything that can scale, and make the few irreversible things (data, DNS, identities,
the address plan) boring and protected. Check what the project already runs on before proposing anything, and recommend a migration only when a named
limit is being hit.

- **Fewest moving parts that meet the requirement.** PaaS, then managed containers, then Kubernetes only with someone to run it. Every controller, gateway and cluster is something to patch, monitor and pay for.
- **Compute lives where the data lives.** One cross-region database round trip per query costs more than any edge or CDN trick recovers. Set the function or container region to the database's region explicitly.
- **Every scaler has a ceiling someone chose.** Autoscaling, function concurrency, serverless databases, logs and metered APIs all get a maximum, because platforms scale without regard for the database or the budget.
- **Nothing is public unless it is the one entry point.** One load balancer or gateway faces the internet; databases, caches and admin tools accept traffic only from the application or an identity-checked tunnel.
- **Identities are short-lived and single-purpose.** People through SSO and roles, each service its own role, CI through OIDC federation. Long-lived keys leak and never expire.
- **Stateful resources get layered protection.** Deletion protection, backups, separate state and a reviewed plan, because a replace on a database is data loss and no rollback exists for it.
- **The reviewed artifact is the plan or rendered diff, not the source.** A one-line HCL or Helm change can destroy a resource; only the plan shows it.
- **Lock-in is a price to estimate, not a sin.** Use standard interfaces for data (Postgres, S3-compatible storage); adopt proprietary services when the capability is worth the exit cost in engineer-weeks.
- **Build once, promote the same image.** Tag by commit SHA, deploy by digest, keep secrets out of layers, run as non-root with a health check and a memory limit.

## Route

| If the task is | Read |
|---|---|
| "Where should this run?", PaaS versus VPS versus containers versus Kubernetes, picking a provider or region, serverless versus always-on cost, block versus object storage, lock-in, leaving the cloud | `references/platform-choice.md` |
| Writing, shrinking, speeding up or securing a Dockerfile; Compose for local development; image tags and registry cleanup; ARM64 builds; deploying to one server with Kamal or Coolify | `references/docker-images.md` |
| A pod is Pending, crash-looping or not ready; writing a Deployment; requests, limits and autoscalers; Gateway API or ingress and certificates; GitOps or Helm; network policies; cluster upgrades | `references/kubernetes.md` |
| Functions are slow to start, time out, lose work after responding or exhaust database connections; deciding what runs at the edge; edge-runtime errors; cron and background work on serverless; invocation loops | `references/serverless-edge.md` |
| Designing a VPC and subnets; making the database private; reaching private resources; a connection that times out; NAT, static outbound IPs, peering or private link | `references/cloud-networking.md` |
| Setting up a cloud account or organization; root account security; SSO and roles; a least-privilege policy; service or CI identities; separate production account; auditing access and public exposure | `references/iam-accounts.md` |
| Writing or reviewing Terraform, OpenTofu or Pulumi; reading a plan; state and module layout; importing console-made resources; drift; scanning; whether to codify at all | `references/infrastructure-as-code.md` |
| Estimating infrastructure cost; a bill that jumped; budgets and caps; egress, NAT and log costs; orphaned resources; commitments; asking a provider for credits after an incident | `references/cost-control.md` |

## Defaults at a glance

| Decision | Prototype | Launch | Scale |
|---|---|---|---|
| Hosting | PaaS | Same PaaS, or one VPS with Kamal if the founder has run servers; add a container service only for workloads the PaaS cannot run | Managed containers in one cloud (Cloud Run, ECS on Fargate, Container Apps); Kubernetes only with an owner for it |
| Workload unit | Platform default | Always-on container for the app and workers; functions for spiky glue; edge only for redirects, token checks and cache shaping | Same, plus spot capacity for CI and batch |
| Region | Database region nearest users; compute in the same region | Same; residency requirements checked against every sub-processor | Still one region, multi-zone; multi-region only for a contractual need |
| Images | Platform buildpack or a simple Dockerfile | Multi-stage, non-root, slim base pinned and rebuilt weekly, SHA tags, CI scan | Digest pins with update bot, ARM64, registry retention rules |
| Network | PaaS private network or IP allowlist plus TLS for the database | Database with no public access; one load balancer; session service or mesh VPN for humans | Three-tier VPC with non-overlapping CIDRs, endpoints for heavy flows, private link where contracts demand |
| Accounts and IAM | One account inside an organization; root MFA, no root keys; budget alert | Production in its own account; SSO with read-only and admin roles; role per service; OIDC for CI; audit log and public-access blocks on | Guardrail policies, log-archive account, quarterly access review |
| Infrastructure as code | None on a PaaS; platform config file plus a written list of manual settings | Terraform or OpenTofu for anything in a cloud account, DNS and IAM; remote locked state per environment and layer; plan in PR, apply on merge | Policy as code, nightly drift detection, rehearsed rebuild |
| Cost | Budget alerts and platform spend limit on | Caps on every scaler and metered API; log retention set; monthly top-five review | Tags and per-customer metering; rightsizing, then partial one-year commitments |

Other defaults: Debian slim base over Alpine for Node and Python; Gateway API over a new Ingress setup; Kustomize for own services and pinned vendor Helm charts; memory limit equal to request and no CPU limit for latency-sensitive services; a connection pooler in front of Postgres for any function platform; directories per environment over Terraform workspaces.

## Before you call it done

1. The hosting recommendation names the limit or requirement that justifies it, and the existing platform was checked first.
2. Compute and database are in the same region, and the region is set explicitly in config.
3. The image builds in CI, runs as a non-root user (`docker run --rm --entrypoint id <image>` is not uid 0), has no secrets in `docker history --no-trunc`, and has a `.dockerignore`.
4. The container starts its server as PID 1 in exec form, exits cleanly on SIGTERM within the grace period, and has a health endpoint that does not depend on the database for liveness.
5. Every container, function and autoscaler has a memory limit or maximum instance count, and maximum instances × pool size is below the database or pooler connection limit.
6. Deploys reference an immutable SHA tag or digest; nothing references `latest`.
7. From outside the network, the database, cache and admin ports time out (`nc -vz -w 5 <host> 5432`), and no security group allows `0.0.0.0/0` on anything but 80/443 at the load balancer.
8. The root identity has phishing-resistant MFA and no access keys; humans use SSO; no long-lived access keys were created for services or CI.
9. New IAM policies list specific actions and resource ARNs; no `Action: "*"`, no `iam:PassRole` on `*`, no trust policy accepting any repository or principal.
10. The Terraform plan was read: the destroy count is zero or each destroy is explained, and no stateful resource shows a replacement (`-/+` or `+/-`). A refactor produced an empty plan.
11. Databases, user-data buckets, DNS zones and keys have deletion protection and backups, and state is remote, locked, versioned and not in git.
12. A budget with alerts exists on every account, log groups have a retention period, and each metered third-party API has a usage limit.
13. Functions do not rely on in-memory state or un-awaited work after the response; scheduled and queued handlers are idempotent with a dead-letter path.
14. On Kubernetes: probes are defined with liveness independent of dependencies, a PodDisruptionBudget allows one eviction, and the rendered manifest diff was reviewed.
15. Any price or limit used in a decision was taken from the provider's current page, and assumptions are written next to the estimate.

## Not this skill

- CI pipelines, deploy strategies, rollbacks and feature flags → `0x:ci-cd-release`
- Shell access, systemd, host hardening, instance and disk sizing, and container internals on one machine → `0x:linux-server`
- DNS, TLS certificates, CDN configuration and load-balancer behavior → `0x:web-networking`
- Running and tuning Postgres itself → `0x:postgres-database`
- Autoscaling policy, capacity planning and disaster recovery → `0x:site-reliability`
- Secrets, staff SSO and devices, and admin-panel hardening → `0x:web-security`
