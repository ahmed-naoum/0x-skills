# Layer 2: Cloud & delivery

Read this when: the user asks what there is to know about cloud & delivery, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

Where does my code run, and how does a change reach production safely?

Competencies: 99 (30 ● / 46 ◐ / 23 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## cloud-infrastructure

Choose where the product runs and build it: hosting model, container images, Kubernetes, serverless and edge runtimes, cloud networking, IAM, infrastructure as code and cost control.

**Choosing where to run** (`references/platform-choice.md`)

- ● Decide between a PaaS, managed containers, a VPS and Kubernetes for your stage
- ● Choose container, function, edge isolate or VM for each workload
- ● Choose block, file or object storage for each kind of data
- ◐ Choose regions for latency, data residency and sovereignty requirements
- ◐ Calculate when per-request serverless pricing loses to always-on containers
- ◐ Assess lock-in and exit cost before adopting a platform's proprietary services
- ○ Decide cloud versus bare metal versus colocation on cost and risk

**Docker images, Compose and single-server deploys** (`references/docker-images.md`)

- ● Write a multi-stage Dockerfile producing a small non-root image
- ● Run the whole stack locally with Compose or dev containers
- ● Keep build secrets and development dependencies out of the final image
- ● Set a health check and resource limits on every container
- ◐ Order layers and use build cache so image builds stay fast
- ◐ Choose a minimal or distroless base image and keep it patched
- ◐ Tag images immutably and manage a registry with retention rules
- ◐ Build multi-arch images and run on ARM64 for price-performance
- ◐ Deploy containers to one VPS with Kamal or Coolify and zero downtime

**Kubernetes operations** (`references/kubernetes.md`)

- ○ Write a Deployment with probes, a rollout strategy and externalized config
- ○ Debug a pod stuck Pending, crash-looping or failing readiness
- ○ Set resource requests and limits and configure pod autoscaling
- ○ Route traffic with Gateway API or ingress and automate certificates
- ○ Deploy with GitOps and reviewable manifests or Helm charts
- ○ Isolate workloads with namespaces, network policies and pod security settings
- ○ Upgrade cluster versions and node pools without downtime

**Serverless and edge runtimes** (`references/serverless-edge.md`)

- ● Write to Web-standard APIs (fetch, Request, Streams) portable across runtimes
- ● Design around cold starts, time limits and stateless invocations
- ● Decide what runs at the edge versus in-region beside the database
- ◐ Work within edge-runtime limits: missing Node APIs, CPU caps, eventually consistent stores
- ◐ Set concurrency limits so functions cannot exhaust the database or the budget
- ◐ Run background and scheduled work on a serverless platform
- ◐ Guard against recursive triggers and unbounded retry loops

**Cloud networking** (`references/cloud-networking.md`)

- ● Keep databases and admin panels off the public internet
- ◐ Design the VPC: CIDR ranges, subnets, security groups, NAT and private endpoints
- ◐ Reach private resources through a bastion or identity-aware proxy
- ◐ Expose services through one load balancer or gateway, not public instance IPs
- ◐ Debug a blocked connection through security groups, routes and network ACLs
- ○ Control egress with static IPs and an allowlist of destinations
- ○ Connect networks and services privately with peering or private links

**Cloud accounts and IAM** (`references/iam-accounts.md`)

- ● Secure the cloud root account: MFA, no access keys, break-glass recovery
- ● Give people access through SSO and roles, not shared users
- ◐ Grant least-privilege IAM roles scoped to specific resources and actions
- ◐ Give each service its own identity with scoped permissions
- ◐ Isolate environments in separate cloud accounts or projects
- ◐ Audit unused permissions and publicly exposed resources with the provider's analyzer
- ○ Apply organization-wide guardrails that no account can override

**Infrastructure as code** (`references/infrastructure-as-code.md`)

- ● Decide what a small team should leave to the PaaS instead of codifying
- ◐ Define cloud resources in Terraform or OpenTofu with plans reviewed in pull requests
- ◐ Read a plan diff and catch a destructive change before applying
- ◐ Structure state, modules and environments so changes stay small and safe
- ◐ Import hand-made resources into code and stop console drift
- ◐ Protect stateful resources from accidental destroy
- ◐ Scan infrastructure code and cloud configuration for misconfigurations
- ◐ Rebuild an environment from infrastructure code from scratch
- ○ Enforce policy as code on infrastructure changes and detect drift

**Cloud cost control** (`references/cost-control.md`)

- ● Set budgets, billing alerts and service quotas on every cloud account
- ● Review the cloud bill monthly and explain the top five line items
- ◐ Estimate monthly infrastructure cost at 100, 10,000 and 1,000,000 users
- ◐ Estimate egress, NAT, log-ingestion and storage costs before committing to a design
- ◐ Cap autoscaling and metered services with hard maximums that bound spend
- ◐ Find and delete orphaned resources, snapshots and idle instances
- ○ Tag resources and attribute cost per service and per customer
- ○ Cut spend with rightsizing, commitments and storage lifecycle rules
- ○ Negotiate credits after an accidental or attack-driven bill

## ci-cd-release

Get a change from a merged pull request to production safely: CI pipelines, pipeline security, environments and config, zero-downtime deploys, rollback and feature flags.

**CI pipelines** (`references/ci-pipelines.md`)

- ● Build a pipeline that type-checks, lints, tests and builds every pull request
- ● Protect main with required checks and review
- ● Run database migrations as a gated, ordered deploy step
- ● Make a CI failure reproducible on a laptop
- ◐ Keep CI fast with caching, parallelism and affected-only runs
- ◐ Build one immutable artifact and promote it through environments
- ○ Choose hosted or self-hosted runners and control CI spend
- ○ Automate mobile builds, code signing, store submission and over-the-air updates

**Pipeline security and provenance** (`references/pipeline-security.md`)

- ● Pin CI actions to commit SHAs and minimize token permissions
- ◐ Authenticate CI to the cloud with OIDC federation, not long-lived keys
- ◐ Keep secrets away from fork and untrusted pull-request builds
- ◐ Restrict who and what can deploy to production with environment protection rules
- ○ Sign build artifacts and verify provenance before deploy
- ○ Publish packages with trusted publishing instead of long-lived registry tokens

**Environments and configuration** (`references/environments-config.md`)

- ● Separate development, staging and production with distinct secrets and data
- ● Validate configuration and environment variables at startup and fail fast
- ● Keep local, CI and production environments close enough to trust
- ◐ Create a preview environment with its own database per pull request
- ◐ Seed staging with safe, anonymized data
- ◐ Decide what staging is for and when to skip it

**Deploys, rollback and cutovers** (`references/deploy-rollback.md`)

- ● Deploy automatically on merge with one-command rollback
- ● Roll back a bad release within minutes, knowing what its migrations allow
- ● Deploy without downtime using rolling or blue-green releases
- ● Run post-deploy smoke tests and watch error rate per release
- ◐ Keep stale cached frontends and old clients working across a deploy
- ◐ Order deploys across database, backend and frontend changes
- ◐ Set deploy frequency and freeze windows around risk and support cover
- ○ Release progressively with canaries that roll back on SLO burn
- ○ Plan a cutover with dual writes, shadow traffic and a rollback point

**Feature flags** (`references/feature-flags.md`)

- ● Hide unfinished work behind a flag instead of a long-lived branch
- ● Choose a flag service or build a minimal table-backed one
- ◐ Target flags by user, account or plan for betas and staged access
- ◐ Ship risky changes behind a kill switch
- ◐ Roll out by percentage or cohort while watching guardrail metrics
- ◐ Remove stale flags on a schedule before they rot the codebase
- ○ Evaluate flags consistently for a user across requests, services and devices
- ○ Use operational flags to shed features under load
