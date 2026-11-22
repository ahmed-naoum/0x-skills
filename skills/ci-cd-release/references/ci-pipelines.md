# CI pipelines

Read this when: creating or speeding up the pipeline that checks every pull request and builds the
deployable artifact, protecting main, wiring migrations into the deploy, choosing runners, or
automating mobile builds and store submission.

## Pipeline shape

One workflow checks every pull request and every push to main. On main only, further jobs build the
artifact and deploy it (`deploy-rollback.md`). The YAML orchestrates; the logic lives in
`package.json` scripts so the same commands run on a laptop.

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
  merge_group:        # only with a merge queue; without this trigger the queue waits forever

concurrency:
  group: ci-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: true          # a new push to a pull request cancels its superseded run

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    services:
      postgres:
        image: postgres:17          # same major version as production
        env: { POSTGRES_PASSWORD: postgres }
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready --health-interval 5s --health-timeout 5s --health-retries 10
    env:
      DATABASE_URL: postgres://postgres:postgres@localhost:5432/postgres
    steps:
      - uses: actions/checkout@<commit-sha>    # vX.Y.Z, pinned: see pipeline-security.md
      - uses: pnpm/action-setup@<commit-sha>   # takes the pnpm version from "packageManager"
      - uses: actions/setup-node@<commit-sha>
        with: { node-version-file: .nvmrc, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm db:migrate        # the whole migration chain, applied to an empty database
      - run: pnpm test
      - run: pnpm build
```

Decisions inside that file:

- **One job until it passes about 5 minutes.** Every job pays checkout and install again, so
  splitting a 3-minute pipeline into four jobs makes it slower and costlier. Split when one step
  dominates: lint and typecheck, unit tests, and end-to-end tests then run as parallel jobs.
- **Cheapest step first.** Typecheck and lint fail in seconds and catch most mistakes; build last.
- **`timeout-minutes` on every job.** The default is 360 minutes; one hung test bills six hours.
- **End-to-end tests run against the production build** (`pnpm build && pnpm start`), not the dev
  server, which hides caching, minification and env-inlining bugs. Upload traces and reports with
  `if: ${{ !cancelled() }}` so they exist when the job failed.
- **Check jobs hold no secrets.** They execute dependency install scripts and pull-request code;
  credentials belong to deploy jobs (`pipeline-security.md`).

Targets (rules of thumb): median pull-request feedback under 10 minutes; investigate at 15. At
Prototype, typecheck, lint, unit tests and build in one job is enough. Add end-to-end tests at
Launch for signup, login and payment. Which tests to write: `0x:code-quality` (`test-strategy.md`).

## Protect main

Apply a branch ruleset (or classic branch protection) to `main`:

| Rule | Solo | Team |
|---|---|---|
| Require a pull request | yes | yes |
| Required approvals | 0: an author cannot approve their own pull request | 1, dismiss stale approvals on new commits |
| Required status checks | the single gate job below | same |
| Require branch up to date | yes while merges are few | switch to a merge queue when merges collide |
| Block force pushes and deletion | yes | yes |
| Bypass list | empty, admins included | empty; emergencies use a documented, logged exception |
| Code owners | skip | `.github/`, migrations, infrastructure |

Required checks are matched by job name, which creates three traps:

1. A workflow skipped by a workflow-level `paths` filter never reports, so the required check stays
   pending and the pull request cannot merge. Filter at job level instead.
2. A job skipped by `if:`, or skipped because a job it `needs` failed, counts as passing. A required
   check on a downstream job therefore passes when an upstream job fails.
3. Renaming a job or changing a matrix removes the gate until the ruleset is updated.

One aggregating job closes all three. Make it the only required check:

```yaml
  ci-ok:
    if: always()
    needs: [check, e2e]
    runs-on: ubuntu-latest
    steps:
      - if: contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled')
        run: exit 1
```

The push to main reruns the checks on the merge result, and deploy jobs `needs` them. Deploy from
the main run, not from a pull-request run. Review practice: `0x:git-collaboration`.

## Migrations as a gated, ordered deploy step

Order on every production deploy: build artifact, run migrations once, roll out code, smoke test.

- **One runner, once.** A pipeline job or the platform's release command, not application startup:
  N instances booting together race each other, and a slow migration fails the health check and
  crash-loops the fleet.
- **Serialized.** The deploy job has `concurrency: { group: deploy-production,
  cancel-in-progress: false }`, so two deploys cannot migrate at once and a run is not cancelled
  halfway through a migration.
- **Gated.** The job names `environment: production`. A failed migration stops the pipeline before
  any code rolls out; because migrations are backward compatible, production stays healthy on the
  old code.
- **Compatible with the running code.** The old version serves traffic during and after the
  migration. Expand first, contract in a later release. Writing such a migration:
  `0x:postgres-database` (`migrations.md`). What it means for rollback: `deploy-rollback.md`.
- **Bounded.** Set `lock_timeout` (a few seconds) and a `statement_timeout` in the migration
  session. DDL that waits behind a long transaction blocks every query queued behind it; failing
  fast and retrying is safer than waiting.
- **Own credentials.** From Launch, a migration role owns the schema and the runtime role cannot
  alter tables.
- **Versioned files only.** Apply with `drizzle-kit migrate` or `prisma migrate deploy`. Schema-sync
  commands (`drizzle-kit push`, `prisma db push`) apply an unreviewed diff and can drop columns;
  they are for local prototyping.
- **Backfills are not migrations.** Bulk row changes run as batched background jobs outside the
  deploy path, so a deploy cannot time out or hold locks on them.

Pull-request checks: the chain applies from zero (the step above); schema definition and migration
files agree (run the ORM's generate command, fail if the working tree changes); two pull requests
that each add a migration merge in order, which "require branch up to date" enforces.

## Make a CI failure reproducible on a laptop

Design for it: CI calls repository scripts only; the Node version comes from one file read by CI and
the local version manager; `packageManager` pins the exact pnpm version; installs use
`--frozen-lockfile`; service images carry the same pinned tags in CI and in the local Compose file.

When CI fails and the laptop passes, reproduce in this order and stop at the first that fails:

1. Read the first error in the log, not the last one.
2. Fresh checkout of the exact commit: `git worktree add ../repro <sha>`, then
   `pnpm install --frozen-lockfile`. This removes stale `node_modules` and untracked files.
3. Same environment: `CI=true TZ=UTC pnpm test`. Many tools change behavior when `CI` is set.
4. Same OS: `docker run --rm -it --cpus 2 -v "$PWD":/app -w /app node:<same-major> bash`. The CPU
   limit surfaces races and timeouts that a fast laptop hides.
5. The failing test alone, then its file, then the suite in CI's shard and order.

| Symptom | Usual cause |
|---|---|
| Module not found only in CI | import path casing (macOS is case-insensitive, Linux is not), or the file is ignored or uncommitted |
| Install fails or resolves differently | lockfile stale; code imports a package it does not declare |
| Date assertions off by hours | runner clock is UTC; test depends on local time zone or DST |
| Passes alone, fails in the suite | shared state, order dependence, parallel workers on one database |
| Tool cannot find the base branch | shallow clone; set `fetch-depth: 0` on checkout |
| Variable undefined | it lives in a local `.env` file; declare it in the workflow and validate at startup |
| Different result on re-run | flaky test: re-run once to classify, then fix it (`0x:code-quality`, `test-data-flaky.md`); no blanket retries |

Failing only on the runner: re-run with debug logging enabled, print tool versions at the top of
the job, and upload logs, traces and screenshots as artifacts. `act` runs workflows locally in
containers, but its images and contexts differ from hosted runners: good for iterating on YAML, not
proof.

## Keep CI fast

Read step timings in the run view before changing anything. Apply in this order; each usually
beats the next:

1. Cancel superseded runs (`concurrency`).
2. Dependency cache keyed on the lockfile hash. `cache: pnpm` caches the pnpm store. Do not cache
   `node_modules`: platform binaries and postinstall state go stale.
3. Parallel jobs, then shards: `--shard=${{ matrix.shard }}/4` works in Playwright and Vitest; set
   `fail-fast: false`. Stop adding shards when per-shard setup time equals per-shard test time.
4. Build caches: `.next/cache`, a Turborepo or Nx remote cache, Docker layers through BuildKit
   (`cache-from` and `cache-to` with `type=gha` or a registry).
5. Browser binaries: cache Playwright's browser directory keyed on its version, or run the job in
   the Playwright container image.
6. Affected-only runs: `turbo run test --affected` or `pnpm --filter "...[origin/main]" test` in a
   monorepo; job-level path conditions in a single app so docs-only changes skip tests.
7. Larger runners, last: they hide waste instead of removing it.

Cache facts that shape the design: a run restores caches from its own branch and from the default
branch, not from sibling branches, so main must run the pipeline to seed what pull requests hit. A
key is immutable once written; use `restore-keys` prefixes for near matches. The repository has a
size cap with least-recently-used eviction and unused entries expire after about a week; check the
current limits. A cache is input written by an earlier run; release jobs should not restore one
that less-trusted runs can write.

Affected-only traps: it needs git history (`fetch-depth: 0`), otherwise it runs everything or
nothing; lockfile, root config and CI file changes must trigger everything; main still runs the
full suite as the backstop.

## One immutable artifact

Build once from the merge commit, name the artifact by commit SHA, deploy by digest. Staging and
production run the same bytes with different configuration. Rebuilding per environment ships
something no test ran: dependency ranges, base images and build-time variables move between builds.

- Tag `:<git-sha>`, deploy `@sha256:<digest>`. A mutable tag (`latest`, `production`) as the deploy
  reference makes "what is running?" and "roll back to what?" unanswerable.
- Configuration and secrets arrive at runtime from the environment; nothing environment-specific
  is baked in.
- Record the SHA each environment runs: a deployment record plus a health endpoint returning it.
- Keep at least the last 10 production artifacts or 30 days (rule of thumb); prune the rest.
- Deployable artifacts come from CI only, not from a laptop.

Next.js exception: `NEXT_PUBLIC_*` values are inlined into the client bundle at build time, so an
image built with staging's public values carries them into production. Either keep
environment-specific values out of `NEXT_PUBLIC_*` (read them on the server at request time and
pass them down), or build per environment from the same commit and lockfile and accept the weaker
guarantee. On a PaaS that builds per environment, use its promote feature where one exists and
check whether promoting rebuilds.

## Runners and spend

| Option | Choose when | What it costs |
|---|---|---|
| Hosted standard Linux | default | per-minute billing on private repositories past the plan's included minutes |
| Hosted larger or ARM | the job is CPU-bound and parallel (builds, shards) | price scales with cores; worth it only if wall time drops about as much |
| Third-party managed runners (a different `runs-on` label) | the CI bill or build time hurts at Scale | another vendor sees code and secrets |
| Self-hosted | GPUs, private-network access, very high volume | patching, isolation and cleanup are yours |

Self-hosted runners must be ephemeral (one job per fresh VM or container) or state and credentials
leak between jobs. Attaching one to a public repository lets any fork pull request execute code on
the machine. Check whether the provider bills a platform fee for self-hosted minutes before
assuming they are free.

Spend controls by effect: cancel superseded runs; job timeouts; macOS runners only for the iOS
build and only when mobile paths change (macOS minutes cost several times Linux minutes; check the
current rate); a version or OS matrix on main or nightly instead of every pull request (an app
deploys on one runtime; matrices are for libraries); short artifact `retention-days` because
storage is billed; grouped dependency-update pull requests; a budget alert on CI usage.

## Mobile builds, signing, submission and over-the-air updates

Default for Expo and React Native: EAS Build, EAS Submit and EAS Update, with managed credentials
and no Mac to maintain. Native iOS, native Android and Flutter: fastlane lanes on hosted macOS
runners or a mobile CI service. On any toolchain:

- **Triggers.** Pull requests run JavaScript checks only. Store builds start from a tag or
  `workflow_dispatch`: native builds are slow and macOS minutes are expensive.
- **iOS signing.** Authenticate CI with an App Store Connect API key (issuer ID, key ID, `.p8`),
  not an Apple ID behind two-factor prompts. Keep one distribution certificate and its profiles in
  a shared encrypted store (EAS credentials or fastlane `match`), so CI and laptops do not each
  mint certificates: the account has a small cap, and certificates expire yearly, which shows up
  as a failed release unless the date is on a calendar.
- **Android signing.** Enroll in Play App Signing, so Google holds the app signing key and a lost
  upload key can be reset; without it a lost keystore means the app can never be updated. CI
  uploads through a Play service account, and the first build of a new app has to be uploaded by
  hand in Play Console before the API accepts uploads.
- **Build numbers** strictly increase (iOS build number per version, Android `versionCode`
  forever). Derive them from CI or let the build service auto-increment; hand edits collide.
- **Tracks.** iOS: TestFlight, App Review, phased release. Android: internal track, closed or open
  testing, production with a staged rollout percentage. A staged rollout can be halted, but a
  store binary cannot be rolled back: the fix is a higher build through review. New personal Play
  developer accounts must pass a closed-testing requirement before production access; check it
  early because it takes weeks.
- **Review time is outside the pipeline.** Put behavior that may need to change fast behind
  server-side flags, and give launches days of slack.
- **Over-the-air updates** replace JavaScript and assets only. A new native module, SDK upgrade,
  permission or native config needs a store build. Bind updates to compatible binaries with a
  `runtimeVersion` policy (`fingerprint` or `appVersion`); an update that reaches a binary lacking
  the native code it calls crashes on launch. Roll updates out by percentage and keep the previous
  update ready to republish. An update that changes what the app is for needs review. App Center
  CodePush is retired; do not start on it.
- **Old versions stay installed for months.** Keep the API backward compatible and ship version 1
  with a minimum-version check and a force-upgrade screen (`deploy-rollback.md`).

```bash
# CI authenticates through the EXPO_TOKEN environment variable
eas build --platform all --profile production --non-interactive --auto-submit
```

## Ask the user

- **Is the repository public, or will outside contributors open pull requests?** It changes runner
  and secret rules. Default: private, no forks.
- **Who else merges?** Decides approvals and code owners. Default: solo, pull request plus checks,
  zero approvals.
- **What is the monthly CI budget?** Decides runner type and how hard to optimize. Default: stay
  inside the plan's included minutes, with an alert before the limit.
- **May destructive schema changes deploy automatically?** Default: additive migrations run
  automatically; drops and rewrites wait for an explicit approval.
- **Who owns the Apple Developer and Play Console accounts?** Signing identities and listings must
  belong to the company. Default: organization accounts with the founder as owner.
- **How fast must a mobile fix reach users?** Decides whether over-the-air updates are worth
  setting up. Default: yes for Expo apps.
