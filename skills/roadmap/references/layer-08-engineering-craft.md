# Layer 8: Engineering craft

Read this when: the user asks what there is to know about engineering craft, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

How do I keep changing the code quickly without breaking it?

Competencies: 178 (74 ● / 78 ◐ / 26 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## git-collaboration

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

## code-quality

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

## ai-coding-agents

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

## engineering-leadership

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
