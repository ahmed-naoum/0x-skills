# Layer 4: Backend

Read this when: the user asks what there is to know about backend, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

What does the server do with a request, and what does it promise other systems?

Competencies: 283 (102 ● / 118 ◐ / 63 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## backend-architecture

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

## api-design

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

## email-notifications

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

## payments-billing

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

## ai-features

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
