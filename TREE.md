# The tree: web development from the machine to the customer

13 layers, 32 skills, 1673 competencies. Read it top to bottom: each layer stands on the ones above it.

● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

| # | Layer | The question it answers | Skills |
|---|---|---|---|
| 0 | [Machine & OS](#layer-0-machine-and-os) | What is my code actually running on? | [linux-server](#linux-server) |
| 1 | [Network](#layer-1-network) | How does a request travel from a browser to my server and back? | [web-networking](#web-networking) |
| 2 | [Cloud & delivery](#layer-2-cloud-and-delivery) | Where does my code run, and how does a change reach production safely? | [cloud-infrastructure](#cloud-infrastructure), [ci-cd-release](#ci-cd-release) |
| 3 | [Data](#layer-3-data) | Where does the truth live, and how do I keep it correct, fast and recoverable? | [postgres-database](#postgres-database), [data-stores](#data-stores) |
| 4 | [Backend](#layer-4-backend) | What does the server do with a request, and what does it promise other systems? | [backend-architecture](#backend-architecture), [api-design](#api-design), [email-notifications](#email-notifications), [payments-billing](#payments-billing), [ai-features](#ai-features) |
| 5 | [Trust](#layer-5-trust) | Who is this, what may they do, and what keeps attackers and regulators away? | [auth-identity](#auth-identity), [web-security](#web-security), [privacy-compliance](#privacy-compliance) |
| 6 | [Frontend](#layer-6-frontend) | What runs in the user's browser, on any device? | [frontend-foundations](#frontend-foundations), [react-nextjs](#react-nextjs), [3dui](#3dui) |
| 7 | [Design & accessibility](#layer-7-design-and-accessibility) | Can every person see it, understand it and finish the task? | [ui-ux-design](#ui-ux-design), [accessibility](#accessibility) |
| 8 | [Engineering craft](#layer-8-engineering-craft) | How do I keep changing the code quickly without breaking it? | [git-collaboration](#git-collaboration), [code-quality](#code-quality), [ai-coding-agents](#ai-coding-agents), [engineering-leadership](#engineering-leadership) |
| 9 | [Operations](#layer-9-operations) | Is it up, is it fast, and what happens when it is not? | [site-reliability](#site-reliability), [web-performance](#web-performance) |
| 10 | [Product](#layer-10-product) | What should I build next, and is it working for users? | [product-discovery](#product-discovery), [product-analytics](#product-analytics) |
| 11 | [Growth & revenue](#layer-11-growth-and-revenue) | How do customers find it, pay for it and stay? | [growth-marketing](#growth-marketing), [pricing-monetization](#pricing-monetization), [sales-support](#sales-support) |
| 12 | [Company](#layer-12-company) | How does this become a business that lasts? | [company-building](#company-building), [startup-finance](#startup-finance) |

## Layer 0: Machine & OS

What is my code actually running on? Competencies: 57 (17 ● / 30 ◐ / 10 ○).

### linux-server

Set up, harden, script and diagnose the Linux machine your code runs on, from CPU, memory and disk limits to systemd, SSH and container internals.

**Shell, files and permissions** (`references/shell-files.md`)

- ● Find files, logs and config using the standard Linux directory layout
- ● Fix permission-denied errors using users, groups, modes and sudo rules
- ● Compose pipes with grep, sed, awk, jq and xargs to answer a question
- ● Write a safe Bash script with strict mode and correct quoting
- ● Manage environment variables, PATH and shell profiles without surprises
- ● Make scripts idempotent so rerunning them is safe
- ◐ Transfer and sync files with rsync and scp, preserving permissions
- ◐ Decide when a shell script should become a real program
- ◐ Mount, resize and check filesystems and volumes without losing data

**Hardware resources and limits** (`references/hardware-resources.md`)

- ● Read live CPU, memory, disk and network usage and name the bottleneck
- ● Tell CPU saturation from I/O wait or memory pressure when load average is high
- ● Choose instance size by CPU architecture, memory and network needs
- ◐ Set log rotation, disk alerts and swap policy before a host fills
- ◐ Diagnose a saturated host with the USE method
- ◐ Choose disk type and size by IOPS, throughput and durability needs
- ◐ Free a full disk safely without deleting database or WAL files
- ○ Benchmark disk IOPS and fsync latency for a database volume
- ○ Diagnose tail latency from CPU steal, NUMA and noisy neighbors

**Processes, systemd and kernel limits** (`references/processes-systemd.md`)

- ● Inspect processes, signals and exit codes to find why a service died
- ● Read and filter service logs with journalctl
- ◐ Write a systemd unit that restarts on crash and starts on boot
- ◐ Inspect open sockets, files and system calls with ss, lsof and strace
- ◐ Read the OOM killer's log and tell a too-low limit from a leak
- ◐ Schedule recurring work with systemd timers or cron, with overlap protection
- ○ Raise file-descriptor, conntrack and ephemeral-port limits before exhaustion
- ○ Tune kernel TCP backlog, buffers and congestion control
- ○ Trace kernel and network latency with eBPF tools

**Packages, updates and provisioning** (`references/packages-updates.md`)

- ● Install language runtimes with version managers, not distro packages
- ◐ Install and pin packages with apt or dnf from trusted repositories
- ◐ Apply kernel and package security updates on a schedule, including reboots
- ◐ Audit what is installed, running and listening before exposing a host
- ◐ Provision a server repeatably with cloud-init or a script, not by hand
- ◐ Decide when to patch a host in place versus replace it
- ◐ Track operating-system end-of-life dates and plan the upgrade

**SSH access and host hardening** (`references/ssh-hardening.md`)

- ● Manage SSH keys, config files, agent and jump hosts safely
- ◐ Create a non-root sudo user and lock root's password on a fresh VPS
- ◐ Harden SSH: keys only, no root login, restricted users
- ◐ Configure a host firewall that allows only the ports in use
- ◐ Use SSH tunnels and port forwarding to reach private services
- ◐ Throttle brute-force attempts and review authentication logs
- ○ Replace long-lived SSH keys with short-lived certificates or identity-based access

**Virtualization and container internals** (`references/container-internals.md`)

- ● Tell whether a fault is in the app, the container or the host
- ● Inspect a running container's processes, network and filesystem from the host
- ◐ Debug OOM-killed or CPU-throttled containers from cgroup metrics
- ◐ Run containers non-root, read-only and with dropped capabilities
- ◐ Handle PID 1, signal forwarding and zombie reaping inside a container
- ◐ Find which image layers and container writes consume disk and prune them safely
- ○ Decide when untrusted code needs a microVM or VM instead of a shared-kernel container
- ○ Trace container networking: bridges, port mapping and DNS between containers

**Time, time zones and text encoding** (`references/time-encoding.md`)

- ● Store timestamps in UTC and convert time zones only at the edges
- ● Store and transmit text as UTF-8 and fix mojibake at its source
- ◐ Run servers in UTC and keep clocks synced with NTP
- ◐ Store time-zone names, not offsets, and keep the zone database current
- ◐ Handle DST and recurring local-time schedules without off-by-one-hour bugs
- ◐ Choose monotonic versus wall-clock time for durations and timeouts
- ○ Write code tolerant of clock skew between machines
- ○ Handle Unicode normalization, grapheme length and case-folding in comparisons

## Layer 1: Network

How does a request travel from a browser to my server and back? Competencies: 73 (27 ● / 29 ◐ / 17 ○).

### web-networking

Configure and debug everything between the browser and the app: IP and transport, DNS and domains, TLS, HTTP and its caching, CDN and edge protection, reverse proxies and load balancers.

**IP, TCP, UDP and QUIC** (`references/ip-transport.md`)

- ● Trace a request from browser through DNS, TCP, TLS and HTTP to the server
- ● Distinguish latency, bandwidth, loss and jitter when someone reports slowness
- ● Diagnose a refused or timed-out connection through ports, NAT and firewall rules
- ◐ Serve dual-stack IPv6 end to end, including IPv6-only mobile networks
- ◐ Survive a Wi-Fi to cellular switch with QUIC connection migration and safe client retries
- ◐ Allow and debug UDP traffic for QUIC, DNS and WebRTC through firewalls
- ○ Count round trips for TCP plus TLS 1.3 versus QUIC and remove extras
- ○ Tell congestion-control backoff from head-of-line blocking when latency spikes on a lossy link
- ○ Diagnose MTU black holes, carrier NAT and proxy interference
- ○ Interpret a regional outage using BGP and anycast routing data

**DNS and domains** (`references/dns-domains.md`)

- ● Register a domain with registrar lock, auto-renew and MFA
- ● Configure A, AAAA, CNAME, ALIAS, MX and TXT records for a production domain
- ● Trace delegation from root to authoritative servers with dig
- ● Diagnose stale caches, negative caching and propagation complaints
- ◐ Choose TTLs balancing failover speed against cache efficiency
- ◐ Move a domain between registrars or DNS providers without downtime
- ◐ Remove dangling records to prevent subdomain takeover
- ○ Configure health-checked failover and latency-based DNS routing
- ○ Enable DNSSEC and roll keys without breaking resolution
- ○ Run authoritative DNS across two providers

**TLS and certificates** (`references/tls-certificates.md`)

- ● Automate certificate issuance and renewal with ACME
- ● Alert on certificate and domain expiry before it breaks the site
- ● Enable HSTS with a staged max-age; preload only once every subdomain serves HTTPS
- ◐ Serve TLS 1.3 with a TLS 1.2 fallback and disable everything older
- ◐ Debug handshake, chain and SNI failures with openssl s_client
- ◐ Restrict certificate issuance with CAA records
- ◐ Decide where TLS terminates and whether to re-encrypt to backends
- ○ Monitor Certificate Transparency logs for unexpected issuance
- ○ Deploy mutual TLS between internal services
- ○ Enable hybrid post-quantum key exchange and test client compatibility

**HTTP semantics and versions** (`references/http.md`)

- ● Choose the HTTP method and status code each endpoint and error should use
- ● Reproduce any request with curl, including headers, cookies and timing
- ● Choose 301, 302, 307 or 308 redirects and avoid redirect chains
- ● Compress text with Brotli or zstd, never already-compressed bodies
- ◐ Serve conditional and range requests so clients revalidate and resume instead of refetching
- ◐ Enable HTTP/3 with HTTP/2 fallback and verify negotiation with curl
- ◐ Send 103 Early Hints and preload instead of HTTP/2 push or domain sharding
- ○ Publish HTTPS/SVCB records to advertise HTTP/3 and ECH
- ○ Decide whether 0-RTT is safe given replay risk on non-idempotent requests

**HTTP and CDN caching** (`references/http-caching.md`)

- ● Set Cache-Control, ETag and Vary so browsers and CDNs cache safely
- ● Serve static assets from immutable, fingerprinted URLs
- ● Mark private and sensitive responses no-store so nothing caches them
- ● Design cache keys and Vary so no user sees another user's page
- ● Purge or revalidate cached content safely on deploy
- ◐ Invalidate content instantly using cache tags or surrogate keys
- ◐ Serve stale on origin error with stale-while-revalidate and stale-if-error
- ◐ Measure cache hit ratio and fix the top misses
- ○ Prevent cache poisoning and web cache deception

**CDN setup and edge protection** (`references/cdn-edge.md`)

- ● Put a CDN before the origin and decide what it caches, proxies and bypasses
- ● Derive the real client IP without trusting spoofable headers
- ◐ Lock the origin so only the CDN can reach it
- ◐ Run redirects, header rewrites and simple auth checks in edge functions
- ◐ Tune WAF rules without blocking real customers
- ◐ Rate-limit and challenge abusive traffic at the edge
- ◐ Set an AI-crawler and scraper policy: allow, block or charge
- ○ Rehearse the DDoS response: who flips which control and how to reach the provider

**Reverse proxies and load balancers** (`references/proxies-load-balancers.md`)

- ● Write health checks that reflect real readiness
- ● Identify which hop produced a 502, 503 or 504
- ◐ Configure a reverse proxy with upstreams, timeouts, compression and forwarded headers
- ◐ Route by host and path to several backends from one proxy or load balancer
- ◐ Drain connections from the load balancer gracefully during deploys
- ◐ Align timeouts across client, CDN, load balancer, app and database
- ◐ Proxy WebSockets and long-lived streams through load balancers without drops
- ○ Choose layer-4 or layer-7 load balancing for a workload
- ○ Tune keep-alive and idle timeouts so connections are reused at every hop

**Network debugging tools and method** (`references/network-debugging.md`)

- ● Debug connectivity step by step with dig, curl and traceroute
- ● Find the slow phase in a DevTools waterfall or HAR file
- ● Tell a client, network or server fault apart from timing data
- ● Emulate slow 4G, packet loss and high latency against a critical flow
- ◐ Locate a lossy hop with mtr
- ◐ Test from several regions and networks to localize a fault
- ◐ Capture and read packets with tcpdump and Wireshark
- ○ Diagnose retransmits, resets and congestion-window limits from a capture

## Layer 2: Cloud & delivery

Where does my code run, and how does a change reach production safely? Competencies: 99 (30 ● / 46 ◐ / 23 ○).

### cloud-infrastructure

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

### ci-cd-release

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

## Layer 3: Data

Where does the truth live, and how do I keep it correct, fast and recoverable? Competencies: 115 (34 ● / 57 ◐ / 24 ○).

### postgres-database

Model, query, migrate, tune, back up and scale a relational database, with PostgreSQL as the default: schemas, SQL, transactions, indexes, zero-downtime migrations, operations and recovery.

**Relational modeling** (`references/schema-modeling.md`)

- ● Model a domain in normalized tables with keys and foreign keys
- ● Make invalid states impossible with NOT NULL, CHECK, UNIQUE and exclusion constraints
- ● Choose column types: timestamptz, text, numeric, enums and JSONB
- ● Store money as integer minor units with an explicit currency
- ● Choose between a typed ORM (Drizzle, Prisma) and raw SQL
- ● Choose primary keys: UUIDv7, identity columns or natural keys
- ◐ Use JSONB for variable attributes without losing integrity or indexability
- ◐ Model soft deletes, audit history and temporal data deliberately
- ◐ Model hierarchies, many-to-many and polymorphic relations idiomatically
- ◐ Decide when to denormalize and how to keep the copies consistent

**Writing application SQL** (`references/sql-queries.md`)

- ● Write joins, aggregates, window functions and CTEs by hand
- ● Eliminate N+1 queries in the ORM
- ● Wrap manual production SQL in a transaction and review it first
- ● Write upserts and bulk writes with ON CONFLICT and batching
- ● Read the SQL an ORM generates and override it when it is wrong
- ◐ Write keyset pagination queries that stay fast on deep pages
- ◐ Use RETURNING, lateral joins and recursive CTEs to simplify application code
- ◐ Write, dry-run and execute a backfill to correct bad records

**Transactions, isolation and locking** (`references/transactions-concurrency.md`)

- ● Use transactions to keep multi-step writes atomic
- ● Prevent lost updates with atomic SQL updates or optimistic version checks
- ● Keep external API calls outside database transactions
- ◐ Choose an isolation level and retry serialization failures
- ◐ Lock rows with SELECT FOR UPDATE and avoid deadlocks
- ◐ Set statement, lock and idle-in-transaction timeouts to protect the pool
- ○ Use SKIP LOCKED and advisory locks for queues and single-run work
- ○ Diagnose blocked queries and deadlocks from pg_locks and logs

**Indexes and query plans** (`references/indexes-query-plans.md`)

- ● Read an EXPLAIN ANALYZE plan and fix a sequential scan
- ● Add an index that matches a slow query's filter and sort order
- ◐ Design composite and partial indexes from real query patterns
- ◐ Find the costliest queries with pg_stat_statements and fix them
- ◐ Choose index types: B-tree, GIN, GiST, BRIN or hash
- ◐ Remove unused and duplicate indexes that slow writes
- ○ Use covering indexes and index-only scans for hot reads
- ○ Fix bad plans caused by stale statistics or row misestimates

**Zero-downtime schema migrations** (`references/migrations.md`)

- ● Run schema migrations as versioned, reviewed code
- ● Write backward-compatible migrations using expand-then-contract
- ◐ Add indexes and constraints without long table locks
- ◐ Rename or retype a column across several deploys without downtime
- ◐ Backfill large tables in throttled, resumable batches
- ◐ Rehearse migrations on a production-sized copy with lock timeouts set
- ◐ Decide whether a migration needs a down script or a forward fix
- ○ Recover from a half-applied migration without losing data

**Running Postgres in production** (`references/postgres-operations.md`)

- ● Choose a managed database provider by backups, limits, support and exit path
- ● Pool connections and size the pool against database limits
- ◐ Configure pooling for serverless and high-concurrency workloads with PgBouncer
- ◐ Grant least-privilege database roles per service
- ◐ Monitor connections, locks, cache hit rate, disk and long transactions
- ◐ Kill a runaway query safely
- ◐ Use serverless Postgres with branching for previews and tests
- ○ Control vacuum, bloat and transaction-ID wraparound
- ○ Tune memory and planner settings for the instance and workload
- ○ Upgrade a major database version with minimal downtime

**Backup, restore and data recovery** (`references/backup-recovery.md`)

- ● Configure automated backups with point-in-time recovery
- ● Restore from backup on a schedule and time it
- ● Take a verified snapshot before a risky change
- ◐ Store immutable backups in a separate account and region
- ◐ Restore a database to a chosen timestamp and reconcile lost writes
- ◐ Guard critical tables with deletion protection and restricted destructive grants
- ○ Recover one tenant's deleted rows from backup without a full rollback

**Replication and scaling** (`references/replication-scaling.md`)

- ◐ Scale vertically first and recognize when that is exhausted
- ◐ Set up a standby replica and rehearse failover
- ◐ Monitor replication lag and alert before reads go stale
- ◐ Offload reporting queries so they cannot starve transactional traffic
- ○ Route reads to replicas while handling replication lag
- ○ Promote a replica and rebuild the failed primary
- ○ Partition large tables by time or tenant
- ○ Decide when to add read replicas, partition tables or shard
- ○ Migrate between database providers with minimal downtime via logical replication

### data-stores

Decide when a product needs more than Postgres and run what it adds: Redis caching, search, object storage, event streams, an analytics warehouse and pipelines, and the data lifecycle across all of them.

**Choosing a datastore** (`references/choosing-datastores.md`)

- ● Default to Postgres and justify every additional datastore
- ● Decide when to add Redis, a search engine, object storage or a vector index
- ◐ Decide when a job queue must yield to a broker or Kafka-style event log
- ◐ Use SQLite, libSQL or D1 where a single writer fits
- ◐ Keep every derived store rebuildable from the source of truth
- ○ Choose a document, key-value or wide-column store only for a proven access pattern
- ○ Run analytics on a columnar engine such as ClickHouse or DuckDB
- ○ Choose a time-series or event store for metrics-shaped data at volume

**Application caching with Redis** (`references/caching-redis.md`)

- ● Decide what must never be cached: balances, entitlements, payment state
- ◐ Cache hot reads in Redis or Valkey with TTLs and explicit invalidation
- ◐ Choose cache-aside, read-through or write-through for a use case
- ◐ Design cache keys and versions so deploys never read stale shapes
- ◐ Size memory, set an eviction policy and decide whether persistence matters
- ◐ Use Redis for counters, locks and rate limits without treating it as truth
- ◐ Measure hit rate and prove a cache earns its complexity
- ○ Prevent cache stampedes with locking or stale serving

**Search** (`references/search.md`)

- ● Use Postgres full-text and trigram search before adding a search engine
- ● Enforce tenant and permission filters inside every search query
- ◐ Choose a search engine by data size, features and operating burden
- ◐ Keep a search index in sync with the database and rebuild it without downtime
- ◐ Build autocomplete, facets and filters that stay fast
- ◐ Store and query embeddings with pgvector and HNSW indexes
- ◐ Measure search quality with zero-result and click-through rates
- ○ Tune relevance with analyzers, typo tolerance, synonyms and ranking rules

**Object storage and files** (`references/object-storage.md`)

- ● Store files in object storage with private buckets by default
- ● Issue short-lived signed URLs for private downloads
- ● Tie every object to a database row with keys, metadata and ownership
- ● Choose S3, R2 or another compatible store by egress cost and features
- ◐ Set lifecycle rules, storage classes and versioning for cost and recovery
- ◐ Serve public assets through a CDN with immutable object keys
- ◐ Clean up orphaned objects and enforce per-tenant storage quotas

**Warehouse, pipelines and event streams** (`references/streams-pipelines.md`)

- ● Decide when a warehouse is needed versus querying a read replica
- ◐ Load product, billing and marketing data into one warehouse
- ◐ Choose managed connectors or custom scripts for each data source
- ◐ Build tested, versioned SQL transformations into trusted metric tables
- ◐ Monitor pipelines with freshness and data-quality alerts
- ○ Sync warehouse segments back into CRM, email and ad tools
- ○ Stream database changes to search, cache and warehouse with change data capture
- ○ Design event streams with schemas, partition keys, ordering and replay

**Data lifecycle, retention and deletion** (`references/data-lifecycle.md`)

- ● Classify data by sensitivity and record where each class lives
- ◐ Build per-user data export and deletion that reaches every store
- ◐ Purge expired data automatically on a retention schedule
- ◐ Apply retention, deletion and pseudonymization rules to analytics data
- ◐ Delete a tenant completely at contract end and prove it
- ◐ Test that you can export your data from every datastore and SaaS vendor
- ○ Archive cold data to cheap storage while keeping it queryable
- ○ Encrypt sensitive fields at application level with managed keys

## Layer 4: Backend

What does the server do with a request, and what does it promise other systems? Competencies: 283 (102 ● / 118 ◐ / 63 ○).

### backend-architecture

Structure the server side of a product: runtime choice, monolith and service boundaries, consistency under concurrency, multi-tenancy, background jobs, realtime features, file uploads and resilient third-party integrations.

**Language, runtime and process model** (`references/runtime-language.md`)

- ● Choose a backend language and runtime by workload and team skill
- ● Choose and pin a JavaScript runtime: Node.js, Bun or Deno
- ● Keep the event loop unblocked under load
- ● Prefer runtime built-ins (fetch, crypto, watch mode, env files) over extra dependencies
- ● Finish in-flight requests and jobs on SIGTERM before exiting
- ◐ Size workers, threads and pools to CPU, memory and downstream limits
- ◐ Move CPU-heavy work to worker threads, a job or another runtime
- ◐ Run TypeScript natively in Node with type stripping and ESM-only modules
- ○ Propagate deadlines and cancel work when the client disconnects
- ○ Tune garbage collection and memory limits to stop latency spikes

**Monolith, modules, services and events** (`references/architecture-shape.md`)

- ● Start as a modular monolith and extract services only on proven need
- ● Choose between the meta-framework's server and a separate API service with its own framework
- ● Draw module boundaries around business capabilities with explicit interfaces
- ● Keep business logic out of transport code so API, jobs and CLI share it
- ● Handle errors by kind: expected failures, bugs and what the user sees
- ◐ Scale horizontally with stateless app servers and external session state
- ○ Decouple modules with events without creating a distributed monolith
- ○ Decide when to extract a service and define its contract and owner
- ○ Apply event sourcing or CQRS only where audit or read scale demands it

**Consistency and concurrency across systems** (`references/consistency-concurrency.md`)

- ● Model workflows as explicit state machines with guarded transitions
- ◐ Choose where strong consistency is required and where eventual is acceptable
- ◐ Publish events atomically with the write using a transactional outbox
- ◐ Avoid dual writes between the database and external systems
- ◐ Write consumers that tolerate duplicate, reordered and delayed messages
- ○ Give users read-your-writes when reads lag behind writes
- ○ Orchestrate multi-step processes as a saga with compensations
- ○ Use distributed locks correctly, with expiry and fencing tokens
- ○ Write reconciliation jobs that check invariants across tables and systems

**Multi-tenancy** (`references/multi-tenancy.md`)

- ● Choose row, schema or database isolation for multi-tenancy
- ● Model accounts, workspaces and users so one user can join many tenants
- ● Scope every query, cache key, job and file path by tenant
- ● Write tests proving cross-tenant reads and writes fail
- ◐ Enforce tenant isolation with row-level security policies
- ◐ Support per-tenant settings and overrides without forking the codebase
- ○ Limit noisy tenants with per-tenant quotas and fair scheduling
- ○ Serve customer custom domains with ownership verification and on-demand TLS certificates
- ○ Pin each tenant to a home region with isolated regional stacks and global routing
- ○ Move a large tenant to dedicated infrastructure without downtime

**Background, scheduled and durable jobs** (`references/background-jobs.md`)

- ● Move slow work off the request path into background jobs
- ● Write idempotent job handlers for at-least-once delivery
- ● Start with a Postgres-backed queue and know when to outgrow it
- ● Configure retries with backoff, jitter and a dead-letter queue
- ◐ Run scheduled jobs exactly once across multiple instances
- ◐ Set timeouts, concurrency limits and priorities per queue
- ◐ Pass IDs, not payloads, and version job arguments across deploys
- ◐ Alert on queue depth and age and scale workers to match
- ○ Orchestrate multi-step workflows with a durable execution engine
- ○ Drain or replay a poisoned queue without duplicating side effects

**Realtime features** (`references/realtime.md`)

- ● Choose polling, SSE, WebSockets or WebRTC for a realtime feature
- ● Handle reconnects, missed messages and ordering on the client
- ● Authenticate, authorize and rate-limit long-lived connections
- ◐ Stream with Server-Sent Events, including reconnect and resume
- ◐ Build presence, typing indicators and live cursors without flooding the server
- ◐ Decide between a hosted realtime service and running your own
- ○ Scale WebSocket connections across instances with pub/sub
- ○ Build collaborative or offline-first features with a sync engine or CRDTs
- ○ Use WebRTC with STUN, TURN and a managed media server

**File uploads and document processing** (`references/file-uploads.md`)

- ● Upload directly to storage with presigned, size-limited requests
- ● Restrict upload type and size and verify content, not the extension
- ◐ Serve user files from a separate origin with safe content headers
- ◐ Process images, video and documents in background jobs
- ◐ Support resumable multipart uploads for large files and flaky networks
- ◐ Import and export CSV with streaming, validation and row-level error reports
- ◐ Generate PDFs and other documents server-side reliably
- ○ Scan uploads for malware and quarantine them before use

**Third-party integrations and resilience** (`references/integrations-resilience.md`)

- ● Set a timeout on every outbound call
- ◐ Add jittered retries and circuit breakers to outbound calls
- ◐ Degrade features gracefully when a third-party API is down
- ◐ Wrap critical vendors behind an interface you can reimplement
- ◐ Pin third-party API versions and test upgrades in a sandbox
- ◐ Respect third-party rate limits with queues and token buckets
- ◐ Store third-party OAuth tokens encrypted and refresh them before expiry
- ○ Shed load and apply backpressure so overload degrades gracefully
- ○ Stop retry storms with retry budgets and hedging limits
- ○ Build two-way syncs with external systems and resolve conflicts

### api-design

Design, document and evolve HTTP APIs and webhooks: style choice, request and response contracts, errors, pagination, idempotency, rate limits, versioning and a public developer platform.

**Choosing and shaping an API style** (`references/api-style.md`)

- ● Choose REST, typed RPC, GraphQL or server functions for each consumer
- ● Design resources, names and URL structure consistently
- ● Agree the API contract before implementing either side
- ● Describe REST APIs in OpenAPI and generate typed clients
- ○ Design a GraphQL schema with complexity limits, batching and persisted queries
- ○ Use gRPC or Connect between internal services where it pays

**Validation, errors, pagination and payloads** (`references/requests-responses.md`)

- ● Validate every input at the boundary against a schema
- ● Return consistent RFC 9457 problem-details errors
- ● Paginate every list endpoint with opaque cursors and stable ordering
- ● Represent dates, money, IDs and enums unambiguously in JSON
- ● Design filtering, sorting and field selection without exposing the schema
- ● Cap body size, header size and request duration
- ◐ Support partial updates with clear semantics for null and absent fields
- ◐ Model long-running operations as job resources clients can poll
- ◐ Report partial failure clearly in batch endpoints

**Idempotency, concurrency control and rate limits** (`references/idempotency-rate-limits.md`)

- ● Make write endpoints safe to retry with client-supplied idempotency keys
- ● Rate-limit per tenant and key with clear 429 and Retry-After responses
- ◐ Store the request fingerprint and response so replays return the original result
- ◐ Choose a rate-limit algorithm and store: token bucket, sliding window, Redis
- ◐ Meter API usage per key and expose quotas in response headers
- ◐ Use ETags and If-Match for optimistic concurrency on updates
- ◐ Tell clients which errors to retry, with backoff and jitter
- ○ Cap expensive operations with cost-based limits and concurrency ceilings

**Webhooks, inbound and outbound** (`references/webhooks.md`)

- ● Verify webhook signatures and reject replays
- ● Acknowledge webhooks fast and process them asynchronously
- ● Process webhooks idempotently, out of order and after delays
- ◐ Reconcile missed webhooks by polling the source API
- ◐ Send signed webhooks with retries, backoff and delivery logs
- ◐ Deliver outbound webhooks without letting customer URLs reach internal networks
- ○ Let customers manage endpoints, secret rotation and event subscriptions
- ○ Version webhook payloads and choose thin or fat events

**Versioning and evolving an API** (`references/versioning-evolution.md`)

- ● Evolve an API with additive changes and tolerant readers
- ● Recognize which changes break clients before shipping them
- ◐ Version a public API and publish a deprecation policy
- ◐ Detect breaking changes by diffing the OpenAPI document in CI
- ◐ Sunset an endpoint using usage data, response headers and customer notice
- ○ Run two API versions side by side with one implementation

**Public API and developer platform** (`references/public-api-platform.md`)

- ● Decide whether and when to commit to a public API
- ◐ Issue scoped, expiring, hash-stored API keys customers can rotate
- ◐ Publish API reference from OpenAPI with runnable examples
- ◐ Get a new developer from signup to first successful call in minutes
- ◐ Expose the product to AI agents through an MCP server
- ○ Ship versioned SDKs generated from the schema
- ○ Provide a sandbox or test mode separate from live data
- ○ Offer OAuth so third-party apps can act for your users

### email-notifications

Send transactional email, SMS, push and in-app notifications that arrive, render and are wanted: provider setup, SPF, DKIM and DMARC, sender reputation, templates, channel choice and user preferences.

**Sending transactional email** (`references/transactional-email.md`)

- ● Choose an email provider and separate transactional from marketing streams
- ● Send transactional email through a provider API with versioned templates
- ● Send from a background job, idempotently, so retries never double-send
- ● Write emails with a plain-text part, a clear subject and one action
- ● Build templates that render across mail clients and dark mode
- ● Preview and test emails locally and in CI without mailing real users
- ◐ Log every send and its delivery status for support lookups
- ○ Receive inbound email and replies through provider webhooks

**Email deliverability** (`references/deliverability.md`)

- ● Authenticate the sending domain with SPF, DKIM and DMARC alignment
- ● Verify addresses at signup so the list stays clean
- ● Process bounces and complaints and suppress bad addresses
- ● Offer one-click unsubscribe and stay under mailbox-provider complaint limits
- ◐ Send from a dedicated subdomain and warm it up before volume
- ◐ Monitor sender reputation and diagnose spam-folder placement
- ○ Move DMARC policy to reject using aggregate reports
- ○ Decide between shared and dedicated sending IPs by volume
- ○ Recover sender reputation after a blocklisting

**SMS, push and chat channels** (`references/sms-push.md`)

- ● Decide which messages deserve SMS, push, email or in-app delivery
- ● Ask for push permission at a moment users will accept
- ◐ Send SMS through a provider with sender registration and country rules
- ◐ Guard SMS and OTP sending against pumping fraud with limits and geo-allowlists
- ◐ Implement web push with a service worker and subscription cleanup
- ◐ Send mobile push through APNs and FCM with token hygiene
- ○ Handle delivery receipts, failures and fallback between channels
- ○ Message customers through WhatsApp or other chat channels where they expect it

**Notification system design** (`references/notification-system.md`)

- ● Model notifications with types, channels and per-user preferences
- ● Separate required transactional messages from opt-out marketing
- ◐ Build an in-app notification inbox with read state
- ◐ Batch and digest notifications to prevent fatigue
- ◐ Deduplicate and throttle notifications triggered by bursts of events
- ◐ Respect quiet hours, time zones and locale in every send
- ◐ Measure delivery, open and action rates per notification type
- ◐ Decide between a notification service and in-house channel routing

### payments-billing

Take money correctly: checkout integration, subscriptions and entitlements, usage billing, invoices and tax, refunds, disputes and fraud, ledger and reconciliation, and catalog, cart, inventory and fulfillment.

**Payment provider and checkout integration** (`references/checkout-integration.md`)

- ● Choose a payment provider by markets, payment methods, fees and payout terms
- ● Use hosted checkout or provider-hosted fields so card data never touches your servers
- ● Create the payment server-side from item IDs, never client-computed amounts
- ● Treat the provider webhook, not the browser redirect, as the source of truth
- ● Generate an idempotency key per payment attempt so retries never double-charge
- ● Block reload, back button and second tabs from resubmitting a payment
- ● Handle 3-D Secure and asynchronous payment states correctly
- ◐ Resolve an unknown outcome after a timeout by querying, never re-charging
- ◐ Offer Apple Pay, Google Pay and local payment methods per market
- ○ Add a second processor with portable payment tokens for uptime and freeze risk

**Checkout experience and payment errors** (`references/checkout-experience.md`)

- ● Show localized price, tax and total before the customer commits
- ● Map every provider error and decline code to a clear customer action
- ● Confirm the order with an ID, receipt and next steps on every outcome path
- ◐ Monitor checkout conversion and decline rates by method and country
- ◐ Recover abandoned checkouts with reminders and saved carts
- ○ Tune retries and payment-method order to raise authorization rate

**Subscriptions and entitlements** (`references/subscriptions.md`)

- ● Implement subscriptions with hosted checkout, a customer portal and webhooks
- ● Sync entitlements from billing webhooks as the source of truth
- ● Model trials, proration, upgrades, downgrades and grace periods explicitly
- ● Implement cancel, pause and reactivate states in billing and access
- ◐ Gate features through an entitlements layer separate from billing
- ◐ Recover failed renewals with smart retries, card updater and dunning emails
- ◐ Support seats, add-ons and annual plans in the subscription model
- ◐ Test billing lifecycles with the provider's simulated clocks
- ○ Migrate subscribers between plans or price versions safely

**Usage-based and credit billing** (`references/usage-billing.md`)

- ◐ Meter usage with accurate, idempotent events
- ◐ Enforce quotas in real time without blocking on the billing provider
- ◐ Show customers live usage with spend alerts and caps
- ○ Bill usage-based plans from metered totals at period end
- ○ Implement prepaid credits with top-ups, expiry and a balance ledger
- ○ Implement hybrid plans: seats plus usage with allowances and overages
- ○ Reconcile metered usage against invoices before each billing run

**Invoices and sales tax** (`references/invoices-tax.md`)

- ● Decide between a merchant of record and handling sales tax and VAT yourself
- ● Issue compliant invoices and receipts with tax details
- ◐ Collect and validate tax IDs and billing addresses from business customers
- ◐ Register for, collect and remit VAT, GST or sales tax
- ◐ Correct an invoice with a credit note instead of editing it
- ◐ Accept bank transfers, purchase orders and net payment terms
- ○ Track tax registration thresholds across jurisdictions
- ○ Support mandatory e-invoicing formats where required
- ○ Handle multi-currency pricing, settlement and exchange-rate differences

**Refunds, chargebacks and fraud** (`references/refunds-disputes-fraud.md`)

- ● Issue full and partial refunds and update entitlements
- ◐ Prevent disputes with clear descriptors, receipts and easy cancellation
- ◐ Contest chargebacks with evidence before the deadline
- ◐ Watch dispute rate against card-network monitoring thresholds
- ◐ Stop card-testing attacks with fraud rules, challenges and velocity limits
- ◐ Refund, credit and correct entitlements after a billing bug
- ◐ Stay within processor terms and hold reserves for a payout freeze
- ○ Tune fraud rules against false declines using decline-code data

**Ledger and reconciliation** (`references/ledger-reconciliation.md`)

- ● Design a schema for orders, payments and ledger entries
- ● Make double charges impossible with unique constraints and state checks
- ● Answer a double-charge complaint from logs, ledger and provider dashboard
- ◐ Reconcile provider records against your database daily
- ◐ Match provider payouts, fees and refunds to ledger entries
- ◐ Export transactions to accounting software cleanly
- ○ Implement an immutable double-entry ledger
- ○ Hold and pay out marketplace funds through connected accounts

**Catalog, cart, inventory and fulfillment** (`references/commerce.md`)

- ● Decide between a commerce platform, a headless backend and a custom build
- ● Model a product catalog with variants, options and per-currency prices
- ● Build a cart that survives sessions, devices and price changes
- ● Compute discounts, coupons, shipping and tax server-side in one pricing engine
- ◐ Reserve stock or seats without overselling under concurrency
- ◐ Orchestrate fulfillment: pick, ship, track and notify, with failure handling
- ◐ Handle returns, exchanges and restocking tied to refunds
- ◐ Deliver digital goods and license keys securely after payment
- ○ Sync inventory and orders with external channels and warehouses

### ai-features

Design LLM-powered product features that are useful, safe and affordable: when to use a model, prompts and context, retrieval, agents and tools, evaluations, guardrails, cost and latency, streaming UX and data handling.

**Designing an LLM feature** (`references/feature-design.md`)

- ● Decide which product problems need an LLM versus deterministic code
- ● Choose a model tier for each task by quality, latency and cost
- ● Write prompts with a clear role, examples, constraints and output format
- ● Define an LLM call's contract: inputs, structured output schema and failure handling
- ● Engineer context: decide what enters the window and in what order
- ◐ Diagnose a quality gap as a prompt, context, retrieval or model problem first
- ◐ Version prompts as code and test them like code
- ○ Decide when to fine-tune or self-host models instead of calling APIs
- ○ Run open-weight models locally or in-browser when privacy or cost demands

**Retrieval over your own data** (`references/retrieval.md`)

- ● Decide whether a feature needs retrieval, long context or a tool call
- ● Build retrieval with chunking, embeddings and source citations
- ● Enforce per-user and per-tenant permissions inside retrieval
- ◐ Parse PDFs, tables and HTML into clean chunks with metadata
- ◐ Improve retrieval with hybrid search and reranking
- ◐ Keep the index fresh as source documents change and are deleted
- ◐ Make the model decline when sources do not cover the question
- ○ Evaluate retrieval separately from generation with recall and precision

**Agents and tools** (`references/agents-tools.md`)

- ● Choose a fixed workflow or an autonomous agent for a task
- ● Require human approval before agents take irreversible actions
- ◐ Design tools that are narrow, well described, idempotent and return typed errors
- ◐ Build an agent loop with tools, step limits and stop conditions
- ◐ Connect tools and data through Model Context Protocol servers
- ○ Run long agent tasks durably with checkpoints, resume and cancel
- ○ Sandbox agent code execution and scope its credentials
- ○ Give agents memory that persists across sessions safely
- ○ Split work across sub-agents only when one agent demonstrably fails

**Evaluations and quality monitoring** (`references/evals.md`)

- ● Build an eval set from real user cases before tuning prompts
- ● Regression-test prompt and model changes against the eval set
- ◐ Choose graders: exact checks, rubrics, LLM judges or human review
- ◐ Trace LLM calls with OpenTelemetry GenAI conventions
- ◐ Log and review AI outputs for wrong, harmful or leaked content
- ◐ Feed user signals (ratings, edits, retries) back into the eval set
- ○ Calibrate an LLM judge against human labels
- ○ Compare prompts or models online with guardrail metrics

**Guardrails and AI security** (`references/guardrails.md`)

- ● Treat model output as untrusted input before rendering, executing or storing it
- ● Label AI output and let users report and correct it
- ● Defend against prompt injection in tools that read untrusted content
- ◐ Limit agent privileges: least-privilege tools, scoped data, no excessive agency
- ◐ Filter inputs and outputs for abuse, personal data and unsafe content
- ◐ Protect AI endpoints from scraping and free-tier farming
- ○ Prevent data exfiltration through tool calls, links and rendered markdown
- ○ Red-team an AI feature with adversarial prompts before launch

**Cost, latency and provider resilience** (`references/cost-latency.md`)

- ● Set latency budgets: time to first token, total time and timeouts
- ● Meter AI usage per user and enforce quotas to protect margin
- ◐ Attribute token cost per feature and customer
- ◐ Cut token cost with prompt caching, batching and context trimming
- ◐ Send easy requests to a cheaper model and escalate the hard ones
- ◐ Add fallbacks for model outages and rate limits
- ◐ Plan for model deprecation: pin versions, re-evaluate, migrate
- ◐ Cache or precompute responses where inputs repeat

**AI interaction and streaming UX** (`references/ai-ux.md`)

- ● Choose chat, inline assist or background automation as the interaction pattern
- ● Stream output to the UI with cancel, retry and partial-result handling
- ● Design the failure states: refusal, timeout, low confidence and empty retrieval
- ◐ Show sources so users can verify an answer
- ◐ Let users edit, regenerate and steer output rather than only accept it
- ◐ Show what an agent is doing and let users stop it mid-task
- ◐ Render streamed markdown, code and structured UI safely

**Data handling for AI features** (`references/ai-data-privacy.md`)

- ● Decide what customer data may be sent to which model providers
- ◐ Secure vendor retention and no-training terms for customer data
- ◐ Redact or minimize personal data before it enters prompts and logs
- ◐ Set retention for prompts, outputs and traces
- ◐ Give customers opt-out, deletion and admin controls for AI features
- ◐ Document AI data flows for customers' security reviews
- ○ Meet regional processing and residency demands for AI workloads

## Layer 5: Trust

Who is this, what may they do, and what keeps attackers and regulators away? Competencies: 194 (61 ● / 93 ◐ / 40 ○).

### auth-identity

Build sign-in and access control that resist takeover: auth architecture, sessions and tokens, passwords, MFA and passkeys, OAuth and OIDC, enterprise SSO, authorization models, account recovery and abuse defense.

**Auth architecture and signup** (`references/auth-architecture.md`)

- ● Decide between a managed auth provider and a vetted library; never hand-roll crypto
- ● Choose sign-in methods for the audience: passkeys, social, magic links, passwords
- ● Model users, linked identities, credentials and sessions in the schema
- ● Design signup and email verification that resist typos and abuse
- ◐ Prevent user enumeration and timing leaks on auth endpoints
- ◐ Test auth flows end to end, including expiry and revocation paths
- ○ Migrate users between auth systems without forcing password resets

**Sessions, cookies and tokens** (`references/sessions-tokens.md`)

- ● Keep sessions in HttpOnly, Secure, SameSite cookies, not tokens in localStorage
- ● Implement sessions with rotation, expiry and revocation
- ● Protect state-changing requests against CSRF
- ● Choose server-side sessions or JWTs and accept the revocation trade-off
- ◐ Scope cookies correctly across subdomains and environments
- ◐ Rotate refresh tokens and detect reuse
- ◐ Let users view and revoke active sessions and devices
- ◐ Authenticate native and mobile clients with tokens in secure storage
- ○ Require step-up authentication for sensitive actions

**Passwords, MFA and passkeys** (`references/passwords-mfa-passkeys.md`)

- ● Hash passwords with Argon2id and reject known-breached passwords
- ● Implement email magic links and one-time codes that resist interception and replay
- ◐ Offer passkeys via WebAuthn as primary sign-in with a safe fallback
- ◐ Offer TOTP or passkey MFA and never rely on SMS alone
- ◐ Generate, store and consume MFA recovery codes safely
- ◐ Enforce MFA by policy for admins and organizations
- ○ Handle synced passkeys, multiple devices and cross-device sign-in
- ○ Upgrade legacy password hashes transparently at login

**OAuth and OpenID Connect login** (`references/oauth-oidc.md`)

- ● Add social login with Google, GitHub, Apple or Microsoft
- ● Debug an OAuth flow failing on redirect, state or cookie errors
- ● Link a provider login to an existing account without enabling takeover
- ◐ Implement OAuth 2.1 with PKCE and strict redirect URI validation
- ◐ Validate ID tokens: issuer, audience, nonce, signature and expiry
- ◐ Request minimal scopes at login and discard provider tokens you do not need
- ○ Issue scoped, short-lived credentials to AI agents acting for users

**Enterprise SSO and provisioning** (`references/enterprise-sso.md`)

- ◐ Decide build versus buy for enterprise single sign-on
- ◐ Add SAML or OIDC single sign-on for enterprise customers
- ○ Route users to their identity provider by verified email domain
- ○ Provision and deprovision users with SCIM
- ○ Map identity-provider groups to roles with just-in-time provisioning
- ○ Enforce SSO per organization while keeping a break-glass admin
- ○ Test SSO against Okta, Entra ID and Google Workspace

**Authorization models** (`references/authorization.md`)

- ● Check authorization on every object access to prevent IDOR
- ● Enforce authorization in server functions, APIs, jobs and realtime channels alike
- ● Implement organizations, invitations and role-based access for teams
- ● Centralize permission checks in one policy layer and test them
- ◐ Choose role-based, attribute-based or relationship-based authorization
- ◐ Design roles and permissions customers can understand and administer
- ◐ Share resources by link or invitation with expiring, revocable grants
- ○ Adopt a policy engine or Zanzibar-style service when checks outgrow code

**Account recovery and lifecycle** (`references/account-recovery.md`)

- ● Design password-reset and email-change flows that resist hijacking
- ● Issue reset tokens that are single-use, short-lived and stored hashed
- ● Build account deletion, deactivation and reactivation flows
- ◐ Notify users of every security-relevant account change
- ◐ Design recovery for lost passkeys and MFA devices without a backdoor
- ◐ Verify identity before support changes account ownership or MFA
- ◐ Transfer organization ownership when the owner leaves
- ◐ Recover hijacked accounts: force resets, restore ownership, undo attacker changes

**Bot and abuse defense** (`references/abuse-defense.md`)

- ● Rate-limit login, signup and reset endpoints per IP and per account
- ● Throttle signups by IP, device and email-domain reputation
- ◐ Stop credential stuffing with breach checks, device signals and MFA prompts
- ◐ Alert on failed-login spikes and anomalous-location sign-ins
- ◐ Add CAPTCHA or invisible challenges only where risk justifies the friction
- ◐ Design free tiers and trials so abuse is unprofitable
- ◐ Stop invites and sharing features being used to send spam or phishing
- ◐ Answer host, registrar and browser-blocklist abuse notices before they suspend you
- ○ Build abuse signals, a review queue and bulk-suspension tooling
- ○ Detect multi-accounting and ban evasion

### web-security

Build and run the product so it resists attack: threat modeling, vulnerability classes, browser security headers, secrets and cryptographic choices, the software supply chain, hardening of company accounts and admin tools, security logging and breach response, and security testing.

**Threat modeling and security priorities** (`references/threat-modeling.md`)

- ● Draw trust boundaries and data flows for the system
- ● Identify the crown-jewel data and the shortest paths to it
- ● Apply a security baseline checklist before a product launches
- ◐ Threat-model a feature and list abuse cases before building it
- ◐ Rank risks by likelihood and impact and decide what to accept
- ◐ Treat third-party scripts and vendors as part of the attack surface
- ○ Decide between a fractional CISO, a security hire and a managed service

**Vulnerability classes and safe input and output handling** (`references/vulnerability-classes.md`)

- ● Use parameterized queries everywhere and ban string-built SQL
- ● Escape output by context to prevent cross-site scripting
- ● Prevent path traversal, command injection and unsafe deserialization
- ● Reject mass assignment by allow-listing writable fields
- ● Sanitize untrusted HTML, markdown and SVG before rendering
- ◐ Block SSRF by allow-listing outbound destinations and guarding metadata endpoints
- ◐ Prevent open redirects and unsafe URL handling
- ◐ Close business-logic flaws: coupon reuse, negative amounts, race-condition double spends
- ◐ Bound attacker-sized inputs to prevent ReDoS and resource exhaustion
- ○ Sandbox user-supplied code, HTML and custom domains

**CSP, CORS and browser security headers** (`references/browser-security.md`)

- ● Configure CORS precisely, without wildcard origins on credentialed requests
- ● Block clickjacking with frame-ancestors
- ● Set Referrer-Policy, Permissions-Policy and nosniff headers
- ◐ Deploy a strict nonce-based Content Security Policy
- ◐ Roll out CSP in report-only mode and fix violations before enforcing
- ◐ Inventory third-party scripts and pin them with Subresource Integrity
- ◐ Validate postMessage origins and sandbox embedded iframes
- ○ Enforce Trusted Types to remove DOM XSS sinks
- ○ Apply cross-origin isolation headers (COOP, COEP, CORP) where needed

**Secrets, key management and cryptographic primitives** (`references/secrets.md`)

- ● Keep secrets in a secrets manager, never in repositories, images or client bundles
- ● Enable secret scanning with push protection on all repositories
- ● Rotate a leaked key, audit its use and purge it from history
- ● Share credentials through a team password manager with role-based access
- ● Turn on provider-managed encryption at rest for databases, disks, buckets and backups
- ● Pick the right primitive: random tokens, hashes, HMAC, authenticated encryption or signatures
- ◐ Issue short-lived, scoped credentials instead of static keys
- ◐ Rotate secrets on a schedule without downtime
- ◐ Store recovery codes and break-glass credentials where a second person can reach them

**Dependencies and software supply chain** (`references/supply-chain.md`)

- ● Commit lockfiles and install in frozen mode everywhere
- ● Evaluate a library's maintenance, license and bus factor before depending on it
- ● Scan dependencies and images in CI and patch within a deadline
- ◐ Automate dependency updates with a release cooldown window
- ◐ Disable install scripts and vet packages against typosquatting and slopsquatting
- ◐ Upgrade dependencies and runtimes on a cadence, ahead of end-of-life dates
- ○ Generate an SBOM for each release
- ○ Establish a compromised package's blast radius and rotate everything exposed
- ○ Fork, vendor or replace an abandoned dependency

**Hardening company accounts, staff access and admin tools** (`references/accounts-admin-hardening.md`)

- ● Enforce MFA and least privilege on registrar, repository, payment and SaaS accounts
- ● Hold domains, cloud, code and payment accounts in company-owned identities
- ● Remove default credentials, debug routes and forgotten internal endpoints before launch
- ◐ Enforce SSO, phishing-resistant MFA and same-day offboarding for staff
- ◐ Put internal tools behind zero-trust access instead of a VPN
- ◐ Harden admin panels with separate authentication, access restrictions and audit
- ◐ Secure staff devices with disk encryption, updates and screen locks
- ◐ Limit who can read production data and log every access

**Security logging, detection and breach response** (`references/logging-breach-response.md`)

- ● Decide which security events to log and how long to keep them
- ◐ Record security-relevant actions in an append-only audit log
- ◐ Log every internal admin action and customer impersonation
- ◐ Ship audit logs off-host and alert on anomalous cloud API calls
- ◐ Write a security incident plan before you need it: roles, contacts, decisions
- ◐ Contain an intrusion: isolate hosts, revoke sessions, rotate credentials, preserve evidence
- ○ Give customers exportable audit logs of account activity
- ○ Reconstruct from logs what an attacker accessed and when
- ○ Detect anomalies: export spikes, privilege changes and new credentials

**Security testing and disclosure** (`references/security-testing.md`)

- ● Test endpoints for broken access control using two accounts
- ● Verify security headers, TLS and cookie flags with external scanners
- ◐ Probe your own app against the OWASP Top 10 with an intercepting proxy
- ◐ Run automated security scanners in CI and triage their findings
- ◐ Commission a penetration test and triage findings by exploitability
- ◐ Fix findings by severity with deadlines and regression tests
- ◐ Publish a security.txt and run a vulnerability disclosure program
- ○ Run a tabletop exercise for a breach scenario

### privacy-compliance

Keep the product lawful and sellable: GDPR and US privacy law, consent and cookies, data-subject requests and retention, DPAs and vendors, PCI, SOC 2 and ISO 27001, sector and consumer rules, terms and policies, and software licenses.

**GDPR, CCPA and privacy fundamentals** (`references/privacy-law.md`)

- ● Map what personal data you hold, why, where and for how long
- ● Collect only the personal data a feature needs
- ◐ Choose a lawful basis for each processing purpose
- ◐ Decide whether you are controller or processor for each data flow
- ◐ Meet CCPA and US state privacy duties, including Global Privacy Control
- ◐ Notify regulators and affected users of a breach within legal deadlines
- ○ Handle cross-border transfers and EU data-residency requests
- ○ Run a data-protection impact assessment for high-risk processing
- ○ Appoint an EU or UK representative or DPO when required

**Consent, cookies, tracking and marketing permission** (`references/consent-cookies.md`)

- ● Implement cookie consent that actually blocks non-essential trackers
- ● Design a consent banner with equal accept and reject and no dark patterns
- ● Obtain marketing-email consent and honor unsubscribe and suppression
- ◐ Record, version and honor consent across devices and sessions
- ◐ Choose analytics that need no consent where the law allows
- ◐ Audit third-party tags and pixels for personal-data leakage
- ◐ Wire consent state into ad and analytics tags
- ◐ Check anti-spam rules before sending cold outreach in each country

**Data-subject requests and retention policy** (`references/data-subject-requests.md`)

- ● Fulfill access, deletion and export requests on deadline
- ◐ Verify a requester's identity without collecting more data
- ◐ Write a request runbook covering every system and subprocessor
- ◐ Set retention periods with a legal basis and legal-hold exceptions
- ◐ Keep a request log proving timely responses
- ○ Decide how deletion applies to backups, logs and analytics
- ○ Respond to objection, rectification and restriction requests

**Vendors, DPAs and subprocessors** (`references/vendors-dpas.md`)

- ◐ Sign DPAs with processors and maintain a subprocessor list
- ◐ Offer customers a DPA and notify them of subprocessor changes
- ◐ Assess a vendor's privacy and security before sending it customer data
- ◐ Keep a vendor inventory with owners, data categories and renewal dates
- ◐ Publish the subprocessor list and data locations on a trust page
- ○ Put transfer mechanisms in place for vendors outside the EU

**PCI DSS, SOC 2 and ISO 27001** (`references/pci-soc2-iso.md`)

- ● Decide when buyers actually require SOC 2 or ISO 27001
- ◐ Determine PCI DSS scope and complete the correct self-assessment questionnaire
- ◐ Write the minimal security policy set and actually follow it
- ○ Choose a compliance automation platform and auditor
- ○ Achieve SOC 2 Type II or ISO 27001 with automated evidence collection
- ○ Run access reviews, vendor reviews and risk assessments on a cadence
- ○ Inventory and monitor payment-page scripts per PCI DSS 6.4.3 and 11.6.1

**Other rules that may apply: sector, consumer, accessibility, AI and trade regulation** (`references/sector-consumer-rules.md`)

- ● Determine whether HIPAA, COPPA, financial or other sector rules apply
- ◐ Meet consumer-law rules on auto-renewal, cancellation and price display
- ◐ Remove dark patterns from consent, pricing and cancellation flows
- ◐ Meet accessibility law (EAA, ADA) with audits and a public statement
- ◐ Disclose AI-generated content and chatbots where transparency rules require
- ◐ Block sanctioned countries and parties and check export-control rules before selling abroad
- ○ Classify AI features under the EU AI Act and meet the resulting duties
- ○ Decide whether the EU Cyber Resilience Act covers software you distribute and meet it
- ○ Triage and remediate an accessibility complaint or demand letter

**Terms, privacy policy and platform duties** (`references/terms-policies.md`)

- ● Publish terms of service and a privacy policy matching actual data flows
- ● Write terms with liability caps and record versioned acceptance
- ● Decide what to template yourself and when to pay a lawyer
- ◐ Publish an acceptable use policy and enforce it
- ◐ Change terms with notice and re-acceptance when the change is material
- ◐ Process takedown notices (DMCA, DSA) within required timelines
- ○ Meet DSA and online-safety duties for user-generated content
- ○ Respond to a legal demand, subpoena or regulator letter with counsel

**Open-source licenses and third-party IP** (`references/licenses-ip.md`)

- ● License the fonts, images, icons and data you ship
- ● Check dependency licenses and avoid copyleft conflicts
- ◐ Generate a license inventory and attribution notices for a release
- ◐ Choose a license for your own code: open-source, source-available or proprietary
- ◐ Check license and IP exposure of AI-generated code and assets
- ◐ Respect the API terms, scraping limits and data licenses of your sources
- ○ Accept outside contributions with a CLA or DCO

## Layer 6: Frontend

What runs in the user's browser, on any device? Competencies: 131 (62 ● / 60 ◐ / 9 ○).

### frontend-foundations

Build on the web platform itself: semantic HTML, CSS layout and responsive design, JavaScript and TypeScript, the browser's rendering and events, forms, animation, internationalization, and PWA and mobile packaging.

**HTML semantics and document structure** (`references/html-semantics.md`)

- ● Write semantic HTML with correct landmarks, headings and lists
- ● Choose native elements (button, a, details, dialog) before custom widgets
- ● Set document metadata: title, viewport, lang, icons and social cards
- ● Mark up tables, figures and code for structure, not layout
- ● Target Baseline feature availability instead of browser-version lists
- ● Build overlays with native dialog, popover and anchor positioning
- ◐ Use progressive enhancement so core content works before JavaScript loads
- ◐ Embed media and iframes with dimensions, lazy loading and sandboxing

**CSS layout and responsive design** (`references/css-layout.md`)

- ● Lay out responsive pages mobile-first with grid, flexbox and container queries
- ● Debug layout using the cascade, specificity and box model
- ● Style with Tailwind or CSS modules driven by design tokens
- ● Handle safe areas, the virtual keyboard and dynamic viewport units
- ● Prevent overflow, stacking-context and z-index bugs systematically
- ◐ Use native nesting, cascade layers and :has() without a preprocessor
- ◐ Build fluid type and spacing with clamp() instead of breakpoint ladders
- ◐ Align nested components with subgrid and intrinsic sizing
- ◐ Implement themes with color-scheme, light-dark() and OKLCH custom properties, without a load flash
- ◐ Keep a growing stylesheet maintainable: scoping, naming and dead-style removal

**JavaScript and TypeScript** (`references/javascript-typescript.md`)

- ● Fix async ordering bugs by reasoning about the event loop and microtasks
- ● Start every project in strict TypeScript, including config and scripts
- ● Model states with discriminated unions so invalid states cannot compile
- ● Narrow unknown data at boundaries instead of casting with as or any
- ● Handle errors, cancellation and timeouts in async code with AbortController
- ● Use generics, inference and utility types without unreadable type gymnastics
- ◐ Use ES modules, package exports and CommonJS interop correctly
- ◐ Use Baseline built-ins (structuredClone, Intl, iterator helpers, Temporal when Baseline) instead of libraries
- ◐ Find and fix leaks from listeners, timers and detached DOM nodes

**The browser: rendering pipeline, DOM, events and DevTools** (`references/browser-dom.md`)

- ● Inspect and live-edit DOM, computed styles and layout in DevTools to find a bug
- ● Debug a real phone remotely with Chrome DevTools or Safari Web Inspector
- ● Handle pointer, keyboard and touch events with delegation and passive listeners
- ● Choose client storage: cookies, localStorage, IndexedDB, Cache API or OPFS
- ◐ Predict whether a change triggers layout, paint or only compositing before making it
- ◐ Use Intersection, Resize and Mutation observers instead of polling
- ◐ Move heavy work off the main thread with web workers
- ◐ Use platform APIs (clipboard, share, file, fullscreen) with permission and fallback
- ○ Build framework-free widgets with custom elements where they fit

**Forms** (`references/forms.md`)

- ● Write semantic HTML forms that work before JavaScript loads
- ● Set input types, autocomplete and inputmode for autofill and the right keyboard
- ● Validate inline and on the server, showing each error beside its field
- ● Block double submits and show pending state on submit
- ● Share one validation schema between client and server
- ◐ Preserve form state across reload, back navigation and app switch
- ◐ Prevent lost work with autosave, drafts and unsaved-changes warnings
- ◐ Build multi-step forms with per-step validation and resumable progress
- ◐ Build date, combobox and file-drop inputs from accessible primitives

**Animation on the web** (`references/animation.md`)

- ● Animate transform and opacity so motion stays on the compositor
- ● Choose CSS transitions, the Web Animations API or a library for an effect
- ● Honor prefers-reduced-motion with meaningful alternatives
- ◐ Animate navigations with View Transitions
- ◐ Build scroll-driven animations with CSS timelines instead of scroll listeners
- ◐ Animate elements entering and leaving, including display and auto height
- ◐ Animate layout changes with FLIP or a layout-animation library
- ◐ Profile janky animation and fix dropped frames
- ○ Sequence complex timelines and decide when to move to canvas or WebGL

**Internationalization** (`references/internationalization.md`)

- ● Format dates, numbers and currencies with Intl for the user's locale
- ● Design layouts that survive text expansion and long words
- ● Externalize strings as ICU messages with plurals and interpolation
- ◐ Route and detect locales with URLs and a user override
- ◐ Support right-to-left layouts with logical CSS properties
- ◐ Run a translation workflow: extraction, context, AI drafts and human review
- ◐ Display and accept times correctly for users in different time zones
- ○ Localize names, addresses, phone numbers and sort order

**PWA, offline and the native boundary** (`references/pwa-mobile.md`)

- ● Decide between responsive web, installable PWA, cross-platform and native apps
- ● Detect offline state and queue or block actions honestly
- ◐ Ship an installable PWA with manifest, service worker and offline shell
- ◐ Version and update a service worker without serving stale or private responses
- ◐ Wrap the web app with Capacitor or build with Expo, reusing the API
- ◐ Open emailed and shared URLs in the installed app with universal and app links
- ◐ Fix in-app webviews that break cookies, redirects and wallets
- ◐ Pass App Store and Play review (privacy labels, account deletion) and appeal rejections
- ○ Implement in-app purchases and follow store billing rules per region
- ○ Run staged rollouts, crash reporting and forced upgrades of old app versions

### react-nextjs

Build the application layer of the frontend with React and a meta-framework: rendering strategy per route, where editable content lives, server components and server functions, data and state, routing, component architecture and build tooling.

**Framework, rendering strategy and content sources** (`references/rendering-strategies.md`)

- ● Choose per route between static, server-rendered, streamed and client rendering
- ● Choose a meta-framework: Next.js, React Router, TanStack Start, Astro, SvelteKit or Nuxt
- ● Render useful HTML for crawlers and link previews
- ● Control framework caching with explicit tags and revalidation
- ● Choose where content lives: repo MDX, a headless CMS or a site builder
- ◐ Ship static shells with dynamic holes via partial prerendering or islands
- ◐ Decide when HTML-over-the-wire (htmx, Hotwire) beats a JavaScript framework
- ◐ Model content types and wire draft preview and publish-time revalidation
- ○ Self-host Next.js and know what a managed platform was doing for you

**Server components, server functions and hydration** (`references/server-components.md`)

- ● Build with React Server Components, keeping client components at the leaves
- ● Mutate data with server functions that validate and authorize every call
- ● Mark server-only modules so importing them from client code fails the build
- ● Stream HTML through Suspense boundaries with designed loading states
- ● Avoid request waterfalls by fetching in parallel and preloading
- ● Diagnose and fix a hydration mismatch
- ◐ Cut hydration cost by shrinking client boundaries and serialized props

**Data fetching and state** (`references/data-state.md`)

- ● Keep server data in a query cache, not a global store
- ● Put view state in the URL so pages are shareable
- ● Choose local state, context or an external store for client state
- ● Fetch data where it is used and deduplicate requests across components
- ● Invalidate and optimistically update cached server data after mutations
- ● Wire forms to mutations with pending, error and optimistic states
- ◐ Compute derived values during render instead of syncing state in effects
- ◐ Merge realtime updates into cached data without flicker or duplicates
- ◐ Let the React Compiler memoize instead of hand-written useMemo

**Routing and navigation** (`references/routing-navigation.md`)

- ● Structure routes, layouts and nested segments around the product's navigation
- ● Protect routes with server-side checks, not client redirects
- ● Add loading, error and not-found boundaries to each route segment
- ◐ Restore scroll, focus and state on back and forward navigation
- ◐ Build modal and parallel routes that deep-link correctly
- ◐ Handle redirects, rewrites and locale or tenant routing in middleware
- ◐ Type links and route params so broken routes fail at compile time
- ○ Migrate routes incrementally between routers or frameworks

**Component architecture** (`references/components.md`)

- ● Compose accessible headless primitives with owned styles, shadcn-style
- ● Write custom hooks that encapsulate one concern and are testable
- ◐ Design component APIs: composition over configuration, controlled versus uncontrolled
- ◐ Split components at server, client and data boundaries, not by file size
- ◐ Build typed component variants from design tokens
- ◐ Develop and document components in isolation with a component workshop
- ◐ Render long lists with virtualization and stable keys
- ◐ Review a frontend pull request for component boundaries and render cost

**Build tooling** (`references/build-tooling.md`)

- ● Bundle with Vite or Turbopack instead of hand-written Webpack config
- ● Configure TypeScript, path aliases and module resolution for the framework
- ● Manage environment variables and their public or private exposure at build time
- ● Process fonts, images, SVG and CSS through the build pipeline
- ◐ Debug build failures from module resolution and ESM or CommonJS mismatches
- ◐ Set browser targets, polyfills and transpilation from Baseline data
- ◐ Speed up dev-server startup, hot reload and production builds
- ◐ Pin toolchain versions so builds are identical on laptops and CI

### 3dui

Build live 3D product websites with three.js and Next.js: the object is code, lit like a photo studio and directed by the scroll.

**Live 3D product sites**

- ● Drive all motion from one shared clock
- ● Adapt render quality to phones to hold frame rate
- ◐ Lathe-turn round parts from a profile curve
- ◐ Author physical metal and glass materials with brushed anisotropic finishes
- ◐ Light the product with a PMREM studio environment rotated by the cursor
- ◐ Direct a scroll-driven camera cue list that frames objects by size
- ◐ Stagger exploded views with two-column callouts and a blueprint edges-only mode
- ◐ Apply film-style post: MSAA HDR, bloom, ACES tone mapping and grain
- ○ Build procedural geometry in millimeters: SDF shapes, marching-squares trace, beveled extrude
- ○ Synthesize sound with Web Audio; unlock audio and tilt with one hold-to-act gesture

## Layer 7: Design & accessibility

Can every person see it, understand it and finish the task? Competencies: 93 (44 ● / 40 ◐ / 9 ○).

### ui-ux-design

Design interfaces people understand and enjoy: visual design, design tokens and component systems, UX flows, information architecture, usability testing, microcopy, motion and dark mode.

**Visual design: type, color, spacing and layout** (`references/visual-design.md`)

- ● Establish visual hierarchy so each screen has one clear primary action
- ● Set a type scale, line length and vertical rhythm
- ● Build a color palette with semantic roles and accessible contrast
- ● Use a spacing scale and grid for consistent layout
- ● Define a minimal brand kit: logo, palette, type and imagery rules
- ● Critique a screen and name exactly what makes it look amateur
- ◐ Choose and pair typefaces that fit the brand and render well on screens
- ◐ Design data-dense screens: tables, filters and dashboards
- ◐ Choose one icon set and imagery style and write the rules for using them

**Design tokens and component systems** (`references/design-systems.md`)

- ● Define design tokens for color, type, space, radius and shadow
- ● Decide when to adopt an existing component kit versus designing custom
- ● Specify every component state: hover, focus, active, disabled, loading, error
- ● Inventory the components a product needs before designing screens
- ◐ Structure tokens in primitive, semantic and component tiers
- ○ Keep design files and coded components in sync from one source
- ○ Govern a design system: contribution, versioning and deprecation

**UX flows and screen states** (`references/ux-flows.md`)

- ● Map the user journey from first visit to repeated value
- ● Sketch low-fidelity wireframes for every screen before styling
- ● Design empty, loading, error and success states for every screen
- ● Cut a flow's steps, decisions and fields to the minimum
- ● Decide what changes between phone, tablet and desktop layouts
- ● Design first-run onboarding screens that lead to first value
- ● Design undo, confirmation and forgiveness for destructive actions
- ◐ Design settings, permissions and team flows that scale
- ◐ Prototype a flow in Figma or code before building it

**Information architecture and navigation** (`references/information-architecture.md`)

- ● Name things in the user's vocabulary and keep the object model consistent
- ● Choose navigation patterns: sidebar, tabs, breadcrumbs or command palette
- ◐ Design navigation that survives ten times more features
- ◐ Design search, filtering and sorting for large collections
- ◐ Structure URLs to mirror the information architecture
- ◐ Design a home screen that answers what the user needs next
- ○ Validate structure with card sorting and tree testing

**Usability testing and design review** (`references/usability-testing.md`)

- ● Run a five-user usability test and rank the issues found
- ● Write task scenarios that do not lead the participant
- ● Run a heuristic review against established usability principles
- ◐ Recruit representative test participants quickly and cheaply
- ◐ Use session replays to locate where users struggle
- ◐ Run a design critique that ends in decisions, not opinions
- ○ Run unmoderated remote tests and first-click tests

**Microcopy and interface writing** (`references/microcopy.md`)

- ● Write labels, buttons and confirmations in plain language
- ● Write error messages that say what happened and what to do
- ● Label dialog actions with specific verbs, not Yes and No
- ● Write empty states and hints that teach the next action
- ◐ Set a voice and tone guide with a word list and examples
- ◐ Name features and plans so users understand them without explanation
- ◐ Write copy that translates cleanly and reads well aloud

**Motion design** (`references/motion-design.md`)

- ● Use motion to explain change, not to decorate
- ● Design loading feedback: skeletons, spinners, progress and optimistic updates
- ◐ Set durations and easing by distance and purpose
- ◐ Choreograph page and element transitions consistently
- ◐ Design micro-interactions for success, error and drag moments
- ◐ Define motion tokens and their reduced-motion variants

**Dark mode and theming** (`references/dark-mode-theming.md`)

- ◐ Decide whether to offer a theme switcher and default to the system setting
- ◐ Map every color use to a semantic token so themes swap cleanly
- ◐ Design dark surfaces, elevation and contrast instead of inverting colors
- ◐ Adapt images, shadows, charts and brand colors for dark surfaces
- ○ Support high-contrast and forced-colors modes
- ○ Offer per-customer branded themes through tokens

### accessibility

Make the product usable by people with disabilities and meet WCAG 2.2 AA: names, roles and ARIA, keyboard and focus, accessible forms, visual and cognitive access, and testing and audits.

**Names, roles, states and ARIA** (`references/names-roles-aria.md`)

- ● Give every control an accessible name, role and state
- ● Write alt text that conveys purpose, and hide decorative images
- ● Remove redundant, conflicting or invalid ARIA from existing markup
- ◐ Apply ARIA patterns correctly for tabs, menus, comboboxes and dialogs
- ◐ Announce dynamic changes with live regions
- ◐ Replace an inaccessible custom widget with a tested primitive
- ◐ Make data tables understandable without sight: headers, scope and captions

**Keyboard, focus and pointer access** (`references/keyboard-focus.md`)

- ● Make every flow keyboard-operable with visible focus
- ● Provide skip links and a logical tab order
- ● Size and space touch targets to WCAG 2.2 minimums
- ● Manage focus on route changes and dynamically inserted content
- ● Trap focus in modals and restore it on close
- ◐ Offer alternatives to drag, hover and gesture-only interactions
- ○ Support switch and voice-control users through standard semantics

**Accessible forms and authentication** (`references/accessible-forms.md`)

- ● Label every field and associate hints and errors programmatically
- ● Announce validation errors and move focus to the first one
- ◐ Make sign-in accessible: allow paste and password managers, no cognitive tests
- ◐ Warn before session timeouts and let users extend them
- ◐ Make multi-step and payment flows completable by screen reader
- ◐ Avoid redundant entry and let users review before submitting

**Visual, media and cognitive access** (`references/visual-cognitive.md`)

- ● Meet contrast minimums for text, icons and focus indicators
- ● Support 200% zoom, text resizing and reflow at 320px
- ● Never convey meaning by color alone
- ◐ Caption video and provide transcripts for audio
- ◐ Avoid flashing, autoplay and motion that triggers vestibular problems
- ◐ Write content in plain language with clear structure
- ◐ Reduce cognitive load with consistent navigation and no time pressure

**Accessibility testing and audits** (`references/testing-audits.md`)

- ● Run automated accessibility checks with axe in CI
- ● Test key flows with a screen reader (VoiceOver, NVDA)
- ● Run a keyboard-only, zoom and high-contrast pass on every feature
- ◐ Run a manual WCAG 2.2 AA audit and prioritize findings
- ◐ Fix accessibility failures in order of user impact
- ◐ Build accessibility into the definition of done and the component library
- ○ Include disabled users in usability testing
- ○ Produce a VPAT or conformance report for enterprise buyers

## Layer 8: Engineering craft

How do I keep changing the code quickly without breaking it? Competencies: 178 (74 ● / 78 ◐ / 26 ○).

### git-collaboration

Use git and the repository as a team tool: the git model and recovery, branching workflow, pull requests and code-review practice, monorepos, and versioning, changelogs and release notes.

**The git model and recovery** (`references/git-model.md`)

- ● Predict what a git command does to commits, refs, index and working tree
- ● Recover lost work with reflog, reset and revert
- ● Resolve merge and rebase conflicts correctly
- ● Write .gitignore and .gitattributes files that keep the repository clean
- ● Search history with log, blame and pickaxe to learn why code exists
- ◐ Clean up local history with interactive rebase and fixup before sharing
- ◐ Juggle parallel work with stash, worktrees and sparse checkout
- ○ Remove large files from history and keep binaries out with LFS

**Branching and commit workflow** (`references/branching-workflow.md`)

- ● Work trunk-based with short-lived branches
- ● Write small commits with messages that explain why
- ● Choose merge, squash or rebase as the integration policy
- ◐ Keep long-running work mergeable with stacked changes and frequent rebases
- ◐ Adopt a commit-message convention that tooling can read
- ○ Maintain release branches and backport fixes only when needed
- ○ Sign commits and verify authorship on protected branches

**Pull requests and code-review practice** (`references/pull-requests-review.md`)

- ● Open small pull requests describing what, why and how to test
- ● Self-review your diff before requesting review, even when solo
- ● Review for correctness, design and risk before style
- ◐ Give review feedback that is specific, kind and prioritized
- ◐ Split a large change into a reviewable sequence
- ◐ Set written review conventions: turnaround, approvals and ownership
- ◐ Route and standardize reviews with CODEOWNERS and templates
- ◐ Decide what needs human review and what automated checks can cover

**Monorepos and shared code** (`references/monorepos.md`)

- ● Decide between one repository and many
- ◐ Manage a monorepo with pnpm workspaces and Turborepo remote caching
- ◐ Share code through internal packages with clear boundaries
- ◐ Build and test only what a change affects
- ○ Version and publish packages from a monorepo
- ○ Split or merge repositories while preserving history

**Versioning, changelogs and release notes** (`references/versioning-releases.md`)

- ● Tag releases and tie every deploy to a commit
- ◐ Apply semantic versioning to libraries and APIs
- ◐ Write changelogs and release notes customers can act on
- ◐ Automate version bumps and changelogs from commit conventions
- ◐ Communicate breaking changes with migration guides
- ○ Publish a supported-versions policy with end-of-life dates

### code-quality

Keep code correct and changeable: test strategy, unit, integration, end-to-end, contract and visual tests, test data and flaky tests, debugging method, refactoring, static analysis and types, and technical documentation.

**Test strategy** (`references/test-strategy.md`)

- ● Decide what to test at each layer and what to skip
- ● Test the riskiest behavior first: money, auth and data loss
- ● Run a pre-launch bug bash on real devices and slow networks
- ● Design code so logic is testable without the network or database
- ◐ Define release criteria someone else can enforce without asking you
- ◐ Use test-driven development where behavior is clear and design is not
- ◐ Judge the suite by escaped defects and change failures, not coverage alone

**Unit and integration tests** (`references/unit-integration-tests.md`)

- ● Write fast, deterministic unit tests for business logic
- ● Write integration tests against a real database instead of mocks
- ● Test API routes through the HTTP layer, including auth and errors
- ● Mock only at system boundaries and fake third parties from recorded responses
- ● Test UI components through user-visible behavior, not implementation details
- ◐ Test failure paths: timeouts, retries, partial writes and concurrency
- ◐ Keep the suite fast enough to run on every change
- ○ Use property-based tests for parsers, money and invariants
- ○ Run mutation testing on critical modules to check test strength

**End-to-end, contract and visual tests** (`references/e2e-contract-visual.md`)

- ● Cover critical journeys end to end with Playwright
- ● Select elements by role and label, not CSS paths
- ◐ Decide how few end-to-end tests are enough
- ◐ Run cross-browser and mobile-viewport end-to-end tests in CI
- ◐ Test sign-in, payment and email flows with test modes and test inboxes
- ◐ Debug a failing end-to-end test from its trace, video and network log
- ◐ Catch visual regressions with screenshot diffing
- ○ Contract-test API consumers and providers so changes cannot silently break clients

**Test data and flaky tests** (`references/test-data-flaky.md`)

- ● Build test data with factories and builders, not shared fixtures
- ● Seed realistic local and preview data with scripts
- ● Isolate tests with per-test transactions or databases
- ◐ Freeze clocks and seed randomness so tests are repeatable
- ◐ Quarantine and fix flaky tests so CI stays trusted
- ◐ Find the root cause of flakiness: time, order, network or shared state
- ○ Parallelize and shard tests without cross-test interference
- ○ Use anonymized production-shaped data for performance and migration tests

**Debugging method** (`references/debugging.md`)

- ● Write a reproducible bug report and triage by severity and reach
- ● Reproduce a bug reliably before attempting a fix
- ● Read the actual error and test one hypothesis at a time
- ● Bisect history or inputs to find the change that broke it
- ● Use a debugger, breakpoints and logpoints, not only print statements
- ● Write the regression test that fails before the fix
- ● Reproduce a production bug locally from its trace and logs
- ◐ Debug safely in production with read-only access, flags and sampled logs
- ◐ Find a server-side memory leak by comparing heap snapshots under load
- ○ Debug intermittent concurrency failures with targeted logging and stress loops

**Refactoring and rewrites** (`references/refactoring.md`)

- ● Refactor in small behavior-preserving steps under tests
- ● Separate refactoring commits from behavior changes
- ● Delete dead code as soon as it is unreachable, not in a cleanup project
- ◐ Add characterization tests before changing legacy code
- ◐ Spot the smells worth fixing: duplicated knowledge, long functions, wide interfaces
- ◐ Apply codemods for mechanical large-scale changes
- ◐ Upgrade a language or framework major version incrementally
- ○ Decide when to rewrite, refactor or leave a system alone
- ○ Migrate incrementally with a strangler pattern instead of a big-bang rewrite

**Static analysis, linting and types** (`references/static-analysis-types.md`)

- ● Gate CI on type checking as the first test
- ● Lint and format with Biome or ESLint flat config, enforced not debated
- ● Run pre-commit hooks that are fast enough to keep on
- ● Ban unsafe patterns with lint rules: any, floating promises, unchecked access
- ◐ Tighten TypeScript strictness incrementally in a legacy codebase
- ◐ Find dead exports, unused dependencies and circular imports with tooling
- ◐ Generate types from database and API schemas so drift fails the build
- ○ Enforce architecture boundaries with import rules

**Technical documentation** (`references/technical-docs.md`)

- ● Write a README and quickstart that gets someone running in minutes
- ● Keep docs in the repository and update them in the same pull request
- ● Comment code to explain why, not what
- ◐ Document architecture with a map, key flows and constraints
- ◐ Write tutorials, how-to guides, reference and explanation as distinct types
- ◐ Structure docs so AI assistants and search retrieve correct answers
- ◐ Hand over a codebase with setup script, architecture notes and ownership map
- ◐ Stop docs rotting with owners, review dates and tested examples

### ai-coding-agents

Get reliable work out of coding agents such as Claude Code: scoping and specs, context and project setup, verification and review, parallel and automated runs, and permissions and governance.

**Scoping and delegating work** (`references/delegation-specs.md`)

- ● Delegate a scoped task to a coding agent with acceptance criteria
- ● Write a spec and plan first, then implement in small verified steps
- ● Decide which code you must write or deeply read yourself
- ● Delegate mechanical, well-tested, low-blast-radius work first
- ● Interrupt, redirect or restart an agent that is going wrong
- ● Break a large feature into agent-sized tasks with checkpoints
- ◐ Ask for options and trade-offs before code on design decisions

**Context and project setup** (`references/context-setup.md`)

- ● Maintain AGENTS.md or CLAUDE.md with conventions and commands
- ● Provide one-command setup so an agent can run the app and tests
- ● Give agents the files, examples and constraints they need, not everything
- ● Keep the codebase agent-legible: small modules, strong types, documented commands
- ● Manage long sessions: compact, write handoff notes, start fresh
- ◐ Extend agents with MCP servers, skills and hooks for your stack
- ◐ Write reusable commands and skills for recurring tasks

**Verifying and reviewing agent work** (`references/verification-review.md`)

- ● Give agents fast feedback: types, tests, linters and a runnable app
- ● Make the agent prove its work with test output and screenshots
- ● Review every agent diff like a junior's pull request
- ● Catch agent failure modes: invented APIs, weakened tests, over-broad changes
- ● Apply extra scrutiny to agent changes in auth, payments and migrations
- ◐ Have agents write failing tests first and reject tests that assert nothing
- ◐ Add AI code review in CI while keeping human merge approval
- ◐ Keep your own understanding of the architecture as agents write more

**Parallel and automated agents** (`references/parallel-automation.md`)

- ◐ Run parallel agents in git worktrees or cloud sandboxes
- ◐ Partition work so parallel agents do not touch the same files
- ◐ Schedule recurring agent tasks: dependency bumps, flaky-test fixes, doc sync
- ○ Measure whether agents speed delivery: cycle time, rework and defects
- ○ Run agents headlessly in CI for triage, fixes and upgrades
- ○ Orchestrate multi-agent workflows with independent verification

**Agent permissions and governance** (`references/permissions-governance.md`)

- ● Run agents in sandboxes with no production credentials
- ● Require approval for destructive commands, pushes and deploys
- ● Restrict agent permissions, secrets and network access
- ● Decide what code and customer data may be sent to AI tools
- ◐ Set a team policy for AI tool use and code provenance
- ◐ Guard against prompt injection from repositories, issues and web pages agents read
- ◐ Track agent spend and set budgets

### engineering-leadership

Make the technical decisions a CTO makes: technology strategy, build versus buy and vendor choice, decision records, estimation and planning, technical debt, and hiring and onboarding engineers.

**Technical strategy** (`references/technical-strategy.md`)

- ● Pick a full default stack for a new product, with each choice's flip condition
- ● Choose boring, well-supported technology and spend innovation budget deliberately
- ● Identify the few hard-to-reverse decisions and slow down only for those
- ◐ Write a technical strategy tied to business goals and constraints
- ◐ Split engineering time across features, reliability and debt
- ◐ Explain technical risk and trade-offs to non-technical stakeholders
- ◐ Plan for ten times the scale without building for it now
- ○ Pass technical due diligence on architecture, security, tests and bus factor
- ○ Decide whether to offer self-hosted or customer-cloud deployments and price their upkeep

**Build versus buy and vendor decisions** (`references/build-vs-buy.md`)

- ● Decide build versus buy from differentiation, yearly ownership cost and exit path
- ● Evaluate a vendor's lock-in, pricing power, viability and exit path
- ● Run a time-boxed spike to decide between options
- ◐ Compare self-hosted open source with a managed service on total cost
- ◐ Negotiate SaaS contracts, startup credits and renewal terms
- ○ Execute a vendor migration under a hard deadline

**Decision records and design docs** (`references/decision-records.md`)

- ● Keep a lightweight decision log, even when solo
- ◐ Write architecture decision records for hard-to-reverse choices
- ◐ Write a design doc with alternatives and risks before a large change
- ◐ Run a design review that surfaces risks early
- ◐ Revisit and supersede a decision when its assumptions change
- ○ Decide who decides: owner, consulted and informed for technical choices

**Estimation, planning and delivery** (`references/estimation-planning.md`)

- ● Break work into small shippable increments with rough estimates
- ● Cut scope, not quality, when a project slips
- ◐ Estimate with ranges and re-forecast from actual throughput
- ◐ Plan a multi-week project with riskiest work first and a demo each week
- ◐ Measure delivery by deploy frequency, lead time, failure rate and recovery time
- ◐ Negotiate commitments with stakeholders using explicit trade-offs
- ○ Coordinate dependencies across several teams

**Technical debt** (`references/technical-debt.md`)

- ● Take on debt deliberately and record the trigger for repaying it
- ◐ Track technical debt in a visible register
- ◐ Rank debt by interest: what slows or endangers the team most
- ◐ Make the case for a refactor or migration in business terms
- ◐ Retire systems and features that no longer pay for their upkeep
- ○ Spot architecture erosion early and correct it with small investments

**Hiring and onboarding engineers** (`references/hiring-engineers.md`)

- ◐ Decide when to make the first engineering hire and for which role
- ◐ Interview engineers with a work sample from your own product
- ◐ Vet a contractor or agency with a paid trial and keep code ownership
- ◐ Onboard an engineer to a first production deploy within a week
- ◐ Set engineering norms: review, testing bar, on-call and documentation
- ○ Decide when to hire platform, QA, data, security or AI specialists
- ○ Hire or promote a first engineering manager and define a career ladder

## Layer 9: Operations

Is it up, is it fast, and what happens when it is not? Competencies: 119 (40 ● / 60 ◐ / 19 ○).

### site-reliability

Know what production is doing and keep it up: logs, errors, metrics and traces, dashboards and alerts, SLOs, incident response, postmortems and runbooks, capacity and scaling, and disaster recovery.

**Logs and error tracking** (`references/logging-errors.md`)

- ● Emit structured JSON logs carrying request and trace IDs
- ● Capture frontend and backend errors with source maps and release tags
- ● Scrub card data, tokens and personal data from logs and traces
- ● Choose log levels and what belongs at each
- ● Search and correlate logs to follow one request
- ● Ship logs off the host to a central store
- ◐ Triage error-tracker noise: group, assign, ignore and alert on new
- ○ Control telemetry cost with sampling and retention tiers

**Metrics and distributed tracing** (`references/metrics-tracing.md`)

- ● Record business metrics (signups, checkouts, jobs) beside technical ones
- ● Choose a hosted observability backend that fits a small team's budget
- ◐ Instrument services with OpenTelemetry traces, metrics and logs
- ◐ Instrument rate, errors and duration for each service and dependency
- ◐ Propagate W3C trace context across browser, services and queues
- ◐ Follow one failed request across CDN, load balancer, app, database and provider
- ○ Choose metric types and keep label cardinality bounded
- ○ Route telemetry through an OpenTelemetry Collector to stay vendor-neutral

**Dashboards and alerting** (`references/dashboards-alerting.md`)

- ● Set up external uptime checks that alert your phone
- ● Monitor scheduled jobs with heartbeat checks
- ● Alert on symptoms users feel, not on every cause
- ◐ Build one dashboard per service showing the golden signals
- ◐ Alert on saturation: disk, memory, connections and queue depth
- ◐ Make every page actionable and link it to a runbook
- ◐ Run synthetic probes of critical journeys from several regions
- ◐ Watch third-party dependencies and their status feeds
- ○ Alert on silent revenue drops with business-metric anomaly detection

**SLOs and error budgets** (`references/slos-error-budgets.md`)

- ● Decide the reliability target a product at each stage actually needs
- ◐ Define SLOs for key user journeys from real user impact
- ◐ Choose indicators: availability, latency, correctness and freshness
- ◐ Use the error budget to choose between features and reliability work
- ◐ Review SLOs regularly and adjust targets from evidence
- ○ Alert on error-budget burn rate over several windows
- ○ Offer an SLA with uptime credits you can actually meet

**On-call and incident response** (`references/incident-response.md`)

- ● Mitigate first: roll back, flag off, scale up or fail over before diagnosing
- ● Set up a status page and incident message templates before launch
- ● Design solo on-call: automatic mitigation, quiet hours and honest expectations
- ● Communicate through the status page and customer emails during an outage
- ◐ Run an incident: assign a lead, keep a timeline, decide in one place
- ◐ Define severity levels and who gets woken for what
- ◐ Set up paging and an on-call rota a small team can sustain
- ◐ Work an incident caused by a vendor outage you cannot fix

**Postmortems, runbooks and launch readiness** (`references/postmortems-runbooks.md`)

- ● Run a production-readiness review before launch: backups, alerts, rollback, limits and owners
- ◐ Write a blameless postmortem and track its actions to completion
- ◐ Find contributing causes beyond the first root cause
- ◐ Write runbooks for the ten most likely incidents
- ◐ Test a runbook by having someone else follow it
- ◐ Turn the most-used runbook steps into safe scripts
- ◐ Share a postmortem with customers when trust requires it
- ○ Review incident trends quarterly and fund the repeat offenders

**Capacity and scaling** (`references/capacity-scaling.md`)

- ● Decide when scaling up is cheaper than scaling out
- ◐ Run two or more instances behind a health-checked load balancer
- ◐ Measure current headroom and find which component saturates first
- ◐ Configure autoscaling with minimums, cooldowns and maximums
- ◐ Map dependencies and remove single points of failure
- ◐ Spread instances and the database across availability zones with automatic failover
- ◐ Prepare for a known spike: launch day, campaign or seasonal peak
- ○ Forecast capacity from growth trends and load per customer

**Disaster recovery and resilience testing** (`references/disaster-recovery.md`)

- ● Back up secrets, configuration and object storage, not only the database
- ◐ Define RPO and RTO per system from business impact
- ◐ Write and rehearse a disaster recovery plan
- ◐ Plan for losing a key account, vendor or person
- ○ Decide whether multi-region failover justifies its cost against your SLA
- ○ Design multi-region failover against stated RPO and RTO
- ○ Rebuild the whole stack in a new account or region from code and backups
- ○ Inject failures and run game days against critical paths

### web-performance

Make pages and endpoints fast and keep them fast: Core Web Vitals, loading and delivery, JavaScript bundles, images and fonts, rendering and runtime, backend latency and profiling, load testing, and performance budgets.

**Core Web Vitals** (`references/core-web-vitals.md`)

- ● Measure LCP, INP and CLS from real users, not only Lighthouse
- ● Prevent layout shift by reserving space for media, fonts and embeds
- ● Cut LCP with fetchpriority, preload and server-rendered hero content
- ◐ Fix poor INP by breaking long tasks and yielding to the main thread
- ◐ Segment field data by device, connection and country to find who is slow
- ◐ Trace a Core Web Vitals regression to the release that caused it
- ○ Attribute slow interactions using Long Animation Frames data

**Loading and delivery** (`references/loading-delivery.md`)

- ● Lazy-load below-the-fold content and defer non-critical work
- ● Decide which caching layer fixes a slow page: browser, CDN, app or database
- ● Remove render-blocking CSS and scripts from the critical path
- ● Audit third-party scripts and defer or remove the costly ones
- ◐ Cut time to first byte with caching, streaming and fewer origin round trips
- ◐ Use preconnect and resource hints for critical third-party origins
- ◐ Cut request count and bytes for slow radios and battery
- ○ Make navigations instant with bfcache eligibility and speculation-rules prerendering

**JavaScript bundles** (`references/javascript-bundles.md`)

- ● Analyze the bundle and remove duplicate or oversized dependencies
- ● Ship less JavaScript by rendering on the server and using platform features
- ● Code-split by route and lazy-load heavy components
- ◐ Enforce a JavaScript bundle budget in CI
- ◐ Make tree-shaking work: ES modules, side-effect flags, no barrel-file traps
- ○ Load third-party widgets through facades or workers

**Images, video and fonts** (`references/images-fonts.md`)

- ● Serve responsive AVIF or WebP images with srcset, sizes and lazy loading
- ● Set explicit dimensions and high priority on the LCP image
- ● Choose system or variable fonts to cut font weight
- ● Load web fonts with subsetting, preload and font-display without layout shift
- ◐ Resize and optimize images on demand through an image CDN or framework loader
- ◐ Deliver video with posters, streaming formats and lazy loading
- ◐ Replace icon fonts and heavy SVG with optimized sprites or inline SVG

**Rendering and runtime performance** (`references/rendering-runtime.md`)

- ● Profile a slow page with DevTools on a throttled low-end device
- ● Respond to input within 100 ms, optimistically where safe
- ◐ Profile style, layout, paint and composite in the Performance panel
- ◐ Find and fix layout thrashing and forced reflow
- ◐ Reduce DOM size and use content-visibility on long pages
- ◐ Keep typing and scrolling responsive by debouncing, deferring and batching updates

**Backend latency and profiling** (`references/backend-latency.md`)

- ● Profile a slow endpoint and find the slow query, lock or downstream call
- ● Run independent I/O in parallel instead of sequential awaits
- ◐ Track p95 and p99 latency per endpoint and log slow queries
- ◐ Set a latency budget for each hop of a critical request
- ◐ Profile CPU with a flame graph and fix the hot path
- ◐ Precompute expensive results in materialized tables or background jobs
- ◐ Reduce payload size and serialization cost
- ○ Find tail-latency causes: garbage collection, cold starts, pool waits, lock contention

**Load testing** (`references/load-testing.md`)

- ● Decide whether a load test is worth running at this stage
- ◐ Load-test critical endpoints with k6 and find the saturation point
- ◐ Model realistic traffic: request mix, think time, data variety and ramp
- ◐ Identify the first bottleneck from metrics during a test
- ○ Run soak, spike and stress tests and read what each reveals
- ○ Test against production-like data and infrastructure without harming users
- ○ Add performance regression checks for key endpoints to CI

**Performance budgets and audits** (`references/performance-budgets.md`)

- ● Audit a site's performance and produce a ranked fix list
- ● Set performance targets tied to conversion and retention
- ◐ Enforce a performance budget in CI with lab tests
- ◐ Monitor field performance continuously and alert on regressions
- ◐ Prioritize performance work by user and revenue impact
- ◐ Report performance to stakeholders with before-and-after field data

## Layer 10: Product

What should I build next, and is it working for users? Competencies: 86 (36 ● / 41 ◐ / 9 ○).

### product-discovery

Decide what to build and why: customer interviews, problem validation, jobs-to-be-done, MVP scoping, specs, prioritization and roadmaps, and the feedback loops that tell you whether it worked.

**Customer interviews and research** (`references/customer-interviews.md`)

- ● Recruit target-customer interviews through cold outreach and communities
- ● Run a non-leading interview about past behavior, not hypothetical futures
- ● Extract jobs-to-be-done, triggers and current spend from interview notes
- ● Synthesize interviews into ranked problems with evidence counts
- ◐ Pick the research method that fits the decision and deadline
- ◐ Write a survey without leading questions and interpret results cautiously
- ◐ Keep a weekly habit of customer conversations after launch
- ○ Maintain a research repository that links every insight to evidence

**Problem and demand validation** (`references/problem-validation.md`)

- ● Write a one-sentence problem statement naming who suffers and how often
- ● Define an ideal customer profile narrow enough to list 100 named prospects
- ● Map existing alternatives, including spreadsheets and doing nothing
- ● Score ideas on pain, payer clarity, reachability and founder advantage
- ● Test demand with a landing page, fake door or concierge test
- ● Set a falsifiable validation threshold and decide pivot, persevere or kill
- ◐ Collect pre-orders or letters of intent to prove willingness to pay
- ◐ Sign design partners who commit time and feedback before launch
- ◐ Estimate bottom-up market size from countable customers and realistic price
- ◐ Tear down a competitor's onboarding, pricing and reviews to find gaps

**MVP scoping** (`references/mvp-scoping.md`)

- ● Cut the MVP to one user, one job and one happy path
- ● Scope around the riskiest assumption and cut everything else
- ● Decide what to fake, do manually or buy instead of build
- ● Ship a narrow MVP in weeks and iterate on real usage
- ● Define what is good enough to charge for
- ◐ Set the quality bar per area: polish the core, stub the rest

**Specs and requirements** (`references/specs.md`)

- ● Write a one-page spec with problem, non-goals and a success metric
- ● Write user stories with acceptance criteria someone else can test
- ● Specify edge cases, states and error behavior before building
- ◐ Define in the spec how success will be measured and instrumented
- ◐ Review a spec with customers or teammates before committing
- ◐ Write a press release and FAQ first for a larger bet

**Prioritization and roadmaps** (`references/prioritization-roadmaps.md`)

- ● Prioritize the backlog by impact, confidence and effort
- ● Decide which feature requests to refuse and say no gracefully
- ◐ Balance customer requests, strategic bets and maintenance
- ◐ Run a quarterly roadmap process tied to metrics, not opinions
- ◐ Publish a now, next, later roadmap without committing to dates
- ◐ Decide to kill, pivot or double down on a feature from usage data
- ◐ Deprecate a feature using usage data and a migration notice
- ○ Delegate a product area with outcome targets instead of feature lists
- ○ Hire a first product manager once founder attention is the bottleneck

**Feedback loops and product-market fit** (`references/feedback-loops.md`)

- ● Onboard the first fifty users by hand and record every stumble
- ● Collect in-app feedback at the moment of use
- ◐ Turn support tickets and calls into tagged, counted product feedback
- ◐ Run churn-reason surveys and exit interviews
- ◐ Run win/loss interviews and fix the top objection
- ◐ Run a beta or early-access program for new features
- ◐ Tell users when the thing they asked for ships
- ◐ Judge product-market fit from retention, the 40% survey and organic pull

### product-analytics

Instrument the product and decide what to measure: event taxonomy and tracking, funnels and activation, cohorts and retention, north-star metrics and metric trees, A/B test design and its traps, and attribution.

**Event taxonomy and tracking** (`references/event-tracking.md`)

- ● Define an event tracking plan with consistent names and properties
- ● Choose an analytics tool: product suite, warehouse-first or both
- ● Track revenue and activation events server-side, where they are facts
- ● Instrument analytics that respect consent and minimize personal data
- ● Identify users and accounts across devices and anonymous sessions
- ◐ Validate events in tests so tracking does not silently break
- ○ Version and govern the tracking plan as the product changes

**Funnels and activation** (`references/funnels-activation.md`)

- ● Define the activation event that predicts retention and measure it
- ● Find the biggest drop-off in the signup-to-paid funnel
- ◐ Build conversion funnels segmented by source, device and plan
- ◐ Measure time to first value and what delays it
- ◐ Analyze feature adoption and what retained users do differently
- ◐ Separate correlation from causation in funnel findings

**Cohorts and retention** (`references/retention-cohorts.md`)

- ● Define active use in a way that reflects real value
- ● Build cohort retention curves and find where they flatten
- ◐ Track logo churn and net revenue retention by cohort
- ◐ Segment retention by acquisition channel, plan and persona
- ◐ Measure engagement depth: frequency, breadth and stickiness
- ○ Break growth into new, retained, resurrected and churned users

**North-star metric and metric trees** (`references/north-star-metrics.md`)

- ● Choose a north-star metric and the input metrics that move it
- ● Specify one weekly scorecard: the few numbers, their owners and targets
- ◐ Build a metric tree linking product inputs to revenue
- ◐ Write metric definitions once so everyone reports the same numbers
- ◐ Set guardrail and counter-metrics so one number is not gamed
- ◐ Run a weekly metrics review that ends in decisions

**A/B tests and their statistical traps** (`references/experiments.md`)

- ● Decide when traffic is too low to A/B test and what to do instead
- ◐ Design an A/B test with sample size, guardrails and a stopping rule
- ◐ Avoid peeking, multiple-comparison and novelty-effect traps
- ◐ Assign variants consistently and check for sample-ratio mismatch
- ◐ Write an experiment brief and record the decision and learning
- ○ Choose the randomization unit: user, account or session
- ○ Run holdouts to measure long-term retention effects

**Attribution** (`references/attribution.md`)

- ● Capture first-touch attribution with consistent UTM conventions
- ● Ask new users how they heard about you and reconcile with tracked data
- ◐ Connect acquisition source to revenue and retention, not only signups
- ◐ Choose an attribution model and know what it cannot tell you
- ◐ Track paid conversions server-side within consent limits
- ○ Attribute signups despite cookie loss and AI-referral traffic
- ○ Measure channel incrementality with holdouts or geo tests

## Layer 11: Growth & revenue

How do customers find it, pay for it and stay? Competencies: 149 (47 ● / 85 ◐ / 17 ○).

### growth-marketing

Get the product found and tried: positioning and messaging, landing pages and conversion, launches, content, lifecycle email, paid acquisition, referral and product-led loops, and community and partnerships.

**Positioning and messaging** (`references/positioning-messaging.md`)

- ● Write positioning: who it is for, what it replaces, why it wins, proof
- ● Write a homepage headline a stranger understands in five seconds
- ● Choose a name after checking domain, trademark and handle availability
- ● Collect testimonials and write case studies with quantified results
- ◐ Build a messaging hierarchy: value propositions, proof points, objections
- ◐ Choose the category you compete in and name the alternatives honestly
- ◐ Test messaging with real prospects before scaling spend

**Landing pages and conversion** (`references/landing-conversion.md`)

- ● Build a landing page with one clear promise, proof and call to action
- ● Structure a marketing site: home, pricing, use cases, comparisons, docs
- ◐ Find why visitors leave using recordings, scroll depth and five-second tests
- ◐ Place social proof and trust signals where doubt occurs
- ◐ Record a short demo video that sells the outcome
- ◐ Build dedicated landing pages per campaign and intent

**Launches** (`references/launches.md`)

- ● Build an audience and waitlist before launch day
- ● Plan a staged launch: private beta, waitlist drip, then public channels
- ● Write launch posts tailored to each community's norms
- ● Run a launch with a checklist, announcement and measurement
- ◐ Pitch journalists, newsletters and creators with a real story
- ◐ Follow up after launch to convert attention into retained users
- ◐ Treat every major feature as a launch moment

**Content marketing** (`references/content-marketing.md`)

- ● Edit AI-drafted content to a quality bar readers trust
- ◐ Build in public with consistent founder-led content
- ◐ Run a content engine from customer-question research to publication
- ◐ Write from proprietary expertise and data competitors cannot copy
- ◐ Publish docs, examples and tools as an acquisition channel
- ◐ Build free tools, templates and calculators as lead magnets
- ◐ Repurpose one piece across formats and channels
- ◐ Measure content by signups and pipeline, not pageviews

**Email list and lifecycle messaging** (`references/email-lifecycle.md`)

- ● Add email capture with a reason to subscribe at each high-intent moment
- ● Write a welcome and activation sequence triggered by behavior
- ◐ Trigger in-app messages and nudges that build habit
- ◐ Segment the list by behavior, plan and lifecycle stage
- ◐ Pick a newsletter format and cadence you can sustain and measure replies
- ◐ Re-engage dormant users and sunset unengaged subscribers
- ◐ Measure lifecycle messages by activation and revenue, not opens

**Channel selection and paid acquisition** (`references/paid-acquisition.md`)

- ● Test a few channels cheaply, then master one before adding a second
- ◐ Run paid ads with conversion tracking and a hard CAC ceiling
- ◐ Test ad creative and audiences systematically
- ◐ Sponsor newsletters, podcasts and creators and measure the result
- ◐ Decide when to stop a channel from its payback data
- ◐ Judge an agency or freelancer by pipeline produced, not activity
- ○ Run retargeting within consent and frequency limits

**Referral and product-led loops** (`references/referral-loops.md`)

- ◐ Build a referral or invite loop into the core workflow
- ◐ Build sharing and public pages that expose the product to new users
- ◐ Design referral incentives that resist fraud
- ◐ Use templates, galleries and badges as distribution surfaces
- ○ Score product-qualified leads from usage and route them to sales
- ○ Measure a loop's viral coefficient and cycle time

**Community, partnerships and market expansion** (`references/community-partnerships.md`)

- ● Contribute to existing communities as a member before promoting
- ◐ Avoid depending on one channel or platform for customers
- ◐ Build and moderate your own community
- ◐ Ship integrations and marketplace listings as distribution channels
- ◐ Co-market with complementary products
- ○ Set up affiliate and reseller programs with tracking and payouts
- ○ Localize product, pricing and payment methods for a new market

### pricing-monetization

Decide how the product makes money: revenue model and value metric, price setting, plans and packaging, discounts and price changes, and the unit economics that show whether it works.

**Revenue model and value metric** (`references/revenue-model.md`)

- ● Choose the revenue model: subscription, usage, transaction fee or marketplace take
- ● Pick a value metric that scales price with customer value
- ● Decide free trial, freemium, reverse trial or paid-only entry
- ● Decide self-serve, sales-assisted or enterprise motion from the price point
- ◐ Price AI features against inference cost with credits, caps or bundling
- ◐ Decide whether to offer one-time or lifetime deals

**Setting the price** (`references/price-setting.md`)

- ● Set initial prices from customer value and alternatives, not cost
- ● Anchor against competitors and the cost of the status quo
- ● Price so gross margin covers infrastructure, support and acquisition
- ◐ Research willingness to pay with interviews and structured price questions
- ◐ Test a price with real offers rather than surveys alone
- ◐ Decide whether to publish enterprise prices or sell by quote
- ○ Set regional prices, currencies and purchasing-power discounts

**Plans, packaging and the pricing page** (`references/packaging-tiers.md`)

- ● Keep plans few and comparable, with one recommended
- ● Design a pricing page that makes the right plan obvious
- ● Design tiered packaging with a clear upgrade trigger
- ◐ Decide which features and limits fence each tier
- ◐ Set free-plan limits that show value yet leave a reason to pay
- ◐ Build expansion paths: seats, usage tiers, add-ons and annual prepay
- ◐ Package an enterprise tier: SSO, audit logs, SLA and support

**Discounts and price changes** (`references/discounts-price-changes.md`)

- ● Set a discount policy: who, how much and in exchange for what
- ● Offer annual plans with incentives that improve cash flow
- ◐ Run a price increase with grandfathering and measure churn impact
- ◐ Announce pricing changes with notice that protects trust
- ◐ Run promotions and coupons without training customers to wait
- ◐ Review pricing on a schedule using win/loss, usage and margin data
- ○ Migrate customers off legacy plans and retire old prices

**Unit economics** (`references/unit-economics.md`)

- ● Calculate break-even: customers needed to cover fixed costs
- ◐ Model CAC, gross margin, payback and LTV on one sheet
- ◐ Calculate cost to serve and gross margin per plan, including AI inference
- ◐ Decide whether a segment or channel is profitable enough to pursue
- ◐ Find and fix customers or plans that lose money

### sales-support

Win customers and keep them: prospecting and outreach, discovery calls and demos, proposals and contracts, procurement and security questionnaires, onboarding, support operations, customer success and churn, and reviews.

**Prospecting, outreach and pipeline** (`references/prospecting-outreach.md`)

- ● Build a qualified prospect list from the ideal customer profile
- ● Start with warm introductions and existing networks
- ● Track every deal in a CRM with stage, next step and close date
- ● Write cold outreach that earns replies and stays deliverable
- ● Follow up with a multi-touch sequence without becoming spam
- ◐ Hire a first salesperson only after founder-led sales is repeatable
- ○ Build a sales playbook a hired rep can repeat
- ○ Set quota, commission plan and a weekly pipeline review

**Discovery calls, demos and pilots** (`references/discovery-demos.md`)

- ● Run a discovery call that uncovers pain, impact and decision process
- ● Qualify a lead on pain, budget, authority and timeline
- ● Give a demo tailored to the buyer's stated problem
- ● Handle price, security and timing objections
- ◐ Map the stakeholders: champion, economic buyer, blocker and users
- ◐ Run a paid pilot with written success criteria and conversion terms
- ◐ Agree a mutual close plan with dates and owners
- ◐ Recognize a deal that will not close and walk away

**Proposals, contracts, custom work and collection** (`references/proposals-contracts.md`)

- ● Write a proposal restating the problem, outcome, price and next step
- ● Store signed contracts and track renewal dates
- ◐ Shorten contracting with an order form on standard terms
- ◐ Negotiate discounts, annual prepay and terms without eroding price
- ◐ Decide which contract terms to concede, trade or refuse
- ◐ Collect annual prepayments and chase overdue invoices
- ◐ Scope custom work in a statement of work with change control and acceptance
- ◐ Price services as fixed bid, day rate or retainer without subsidizing the customer
- ○ Negotiate an enterprise MSA: liability caps, SLA, indemnity and termination
- ○ Handle redlines with a playbook of fallback positions

**Procurement and security questionnaires** (`references/procurement-security.md`)

- ◐ Complete a security questionnaire from a reusable answer library
- ◐ Prepare a security and compliance pack before the first enterprise deal
- ◐ Decide which enterprise requirement to build next from the deals it blocks
- ◐ Register in vendor portals and supply insurance and tax forms
- ○ Navigate enterprise procurement and vendor onboarding
- ○ Decide whether to answer an RFP and how

**Customer onboarding** (`references/customer-onboarding.md`)

- ● Decide high-touch or self-serve onboarding by contract value
- ● Onboard a new account to first value with a checklist
- ◐ Run a kickoff and implementation plan for larger customers
- ◐ Build importers that migrate customers off a competitor quickly
- ◐ Train users with guides, videos and office hours
- ◐ Track each account's onboarding milestones and chase the stalled ones

**Support operations** (`references/support-operations.md`)

- ● Set up a shared support inbox with response-time targets
- ● Triage a ticket: reproduce, classify as bug, gap or confusion, and close the loop
- ● Write help articles and saved replies for the top ten questions
- ● Handle refund and cancellation requests by a written policy
- ◐ Decide what an AI support agent may answer and when a human takes over
- ◐ Decide which audited admin actions, including impersonation, the support team gets without an engineer
- ◐ Tag tickets by root cause and review the trends
- ◐ Review support quality with CSAT, response time and ticket sampling
- ◐ Hire a first support person and hand over a documented playbook

**Customer success and churn** (`references/success-churn.md`)

- ◐ Separate involuntary from voluntary churn and find each one's causes
- ◐ Build a customer health score and trigger outreach before churn
- ◐ Design a cancellation flow with reasons, pause and save offers
- ◐ Win back churned customers with targeted offers
- ◐ Announce new releases to customers to re-engage dormant accounts
- ○ Run renewal and expansion conversations from account health
- ○ Run business reviews for key accounts
- ○ Stand up customer success with onboarding, reviews and renewal ownership

**Reviews, complaints and reputation** (`references/reviews-reputation.md`)

- ● Ask happy customers for reviews and referrals at the right moment
- ● De-escalate an angry customer and turn the complaint around
- ◐ Answer a bad review or viral complaint publicly
- ◐ Apologize and compensate well after an outage or mistake
- ◐ Monitor mentions on review sites, social media and communities
- ◐ Measure satisfaction with NPS or CSAT and act on detractors
- ○ Build a reference-customer program for sales

## Layer 12: Company

How does this become a business that lasts? Competencies: 96 (22 ● / 52 ◐ / 22 ○).

### company-building

Build the company around the product: strategy and moats, incorporation and founder legal basics, hiring, managing people, operating cadence and culture, and the founder's own effectiveness.

**Strategy and moats** (`references/strategy-moats.md`)

- ● Write a one-page strategy: customer, wedge, moat and business model
- ● Decide what to do yourself, automate, outsource or hire next
- ◐ Identify a durable advantage: data, network effects, switching costs, brand or distribution
- ◐ Choose a wedge and the sequence of markets after it
- ◐ Analyze competitors and decide where not to compete
- ◐ Respond to a copycat: ignore, out-ship, reposition or enforce your rights
- ◐ Set quarterly goals with measurable key results

**Incorporation, founder legal basics, IP protection and the board** (`references/incorporation-founders.md`)

- ● Choose an entity and jurisdiction and keep filings current
- ● Sign a co-founder agreement on roles, decision rights and what happens if one leaves
- ● Check employer IP-assignment clauses before building on the side
- ● Assign all founder, employee and contractor IP to the company in writing
- ● Keep standard templates: NDA, contractor agreement and offer letter
- ◐ Clear and register a trademark before investing in the brand
- ◐ Enforce trademark and copyright against clones with takedowns and platform complaints
- ◐ Buy cyber, professional-liability and D&O insurance matched to risk
- ○ Decide whether patents or trade-secret protection are worth their cost
- ○ Build a board and run its meetings with a pre-read and clear asks

**Hiring** (`references/hiring.md`)

- ◐ Choose the first hire by the bottleneck, not the org chart
- ◐ Write a role scorecard and job description from outcomes
- ◐ Source candidates from networks, communities and direct outreach
- ◐ Run structured interviews with work samples and scorecards
- ◐ Check references and verify identity against fraudulent remote candidates
- ◐ Choose contractor, employee or employer-of-record for each country
- ◐ Set compensation bands from market data and what the company can afford
- ◐ Make an offer and close the candidate without overpromising
- ○ Hire a first marketing lead and define the metrics they own

**Managing people** (`references/managing-people.md`)

- ◐ Onboard a new hire to productive within two weeks
- ◐ Set 30/60/90-day expectations and review against them
- ◐ Run one-on-ones that surface blockers and growth goals
- ◐ Delegate outcomes with a clear owner and check-ins
- ◐ Give direct feedback and manage underperformance to a resolution
- ◐ Let someone go lawfully and humanely
- ◐ Run payroll, benefits and required employer registrations
- ○ Design an org structure with clear ownership beyond ten people
- ○ Decide when to add a people lead versus outsourced HR

**Operating cadence, process and culture** (`references/operating-cadence.md`)

- ● Set a weekly, monthly and quarterly operating rhythm
- ◐ Name a deputy with legal and account authority if the founder is unreachable
- ◐ Work async-first with written decisions
- ◐ Stay a small team by automating back-office work with SaaS and agents
- ◐ Write down values and working norms that actually guide decisions
- ◐ Keep a company handbook as the single source of truth
- ◐ Replace status meetings with documents and keep the meetings that decide

**Founder effectiveness** (`references/founder-effectiveness.md`)

- ● Split your own week across building, selling and operating
- ● Protect your energy and avoid burnout over a multi-year effort
- ● Build a support network of advisors, peers and mentors
- ◐ Raise co-founder disagreements early and resolve them
- ◐ Learn an unfamiliar function well enough to hire for it
- ○ Negotiate a co-founder exit: separation agreement, board seat, access handover and announcement
- ○ Step back from coding and redefine your own role as CEO
- ○ Plan succession or stepping aside

### startup-finance

Run the company's money: bookkeeping and tax, cash and runway forecasting, funding strategy, the fundraising process, equity and the cap table, and exit and due diligence.

**Bookkeeping and tax** (`references/bookkeeping-tax.md`)

- ● Open business banking and keep business money separate from personal
- ● Keep monthly books in accounting software
- ● File and pay corporate, payroll and sales taxes on time
- ● Read a profit and loss statement, balance sheet and cash-flow statement
- ● Choose an accountant and decide which tasks to delegate
- ◐ Close the books monthly with a checklist
- ◐ Claim R&D credits and startup tax reliefs where available
- ○ Recognize revenue correctly and reconcile billing to the books

**Cash, runway and financial planning** (`references/runway-forecasting.md`)

- ● Maintain a cash-flow forecast and know runway in months
- ● Set a personal runway budget and a kill date for the idea
- ● Calculate MRR, expansion and churn correctly from billing data
- ◐ Review burn, margin, CAC payback and runway in a monthly finance pack
- ◐ Build an 18-month financial model with scenario cases
- ◐ Manage cash using burn multiple and default-alive calculations
- ◐ Spread deposits and hold reserves so one bank or processor cannot sink you
- ◐ Reduce reliance on any single customer for most revenue
- ○ Cut burn decisively: reprioritize, renegotiate contracts, reduce headcount lawfully
- ○ Bring in a fractional CFO when reporting, audits or fundraising demand it

**Funding strategy and investor communication** (`references/funding-strategy.md`)

- ● Decide bootstrapped niche versus venture-scale before raising
- ● Choose between bootstrapping, angels, venture capital and revenue-based financing
- ◐ Use grants, cloud credits and other non-dilutive funding
- ◐ Set the milestones to reach before each round from what investors expect
- ◐ Pitch the company in two minutes to customers, hires and investors
- ◐ Send a monthly stakeholder update with real numbers

**Running a fundraise** (`references/fundraising-process.md`)

- ◐ Write a pitch deck and data room that survive investor scrutiny
- ◐ Read a term sheet and spot the terms that matter
- ◐ Vet investors through founder references before taking their money
- ○ Run a fundraising process with a target list and parallel conversations
- ○ Negotiate a SAFE or priced round: valuation, dilution, preferences, board seats
- ○ Close a round: legal documents, filings and funds received

**Equity and the cap table** (`references/equity-cap-table.md`)

- ● Vest founder equity with a cliff and file required tax elections on time
- ◐ Maintain a cap table and model dilution through future rounds
- ◐ Size equity grants with vesting for hires and advisors
- ◐ Explain an equity offer to a candidate honestly
- ○ Set up an option pool with a defensible fair-market valuation
- ○ Handle a departure: repurchase, exercise window and acceleration

**Exit and due diligence** (`references/exit-due-diligence.md`)

- ◐ Document systems so the business runs without the founder
- ◐ Value a small software business and sell it through a marketplace or broker
- ◐ Sunset a product gracefully with notice, refunds and customer data export
- ◐ Wind down the company: settle debts, notify customers and staff, dissolve, file final returns
- ○ Keep a standing data room: contracts, IP, financials, policies and cap table
- ○ Prepare quality-of-earnings-ready financials and cohort metrics
- ○ Decide sell, merge, raise or keep running from offers and personal goals
- ○ Run a competitive sale process with advisors and multiple bidders
- ○ Negotiate deal terms: price, earn-out, escrow, representations and warranties
- ○ Plan post-acquisition integration, customer communication and team retention
