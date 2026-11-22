---
name: ci-cd-release
description: Gets a merged change to production, covering CI pipelines, pipeline security, environments and config, zero-downtime deploys, rollback, cutovers and feature flags. Use when setting up or speeding up GitHub Actions, replacing stored CI keys with OIDC, fixing deploy downtime or rollback, adding staging or preview environments, a missing environment variable crashed production, or adding feature flags or a kill switch.
---

# CI/CD, environments and releases

## Stance

Delivery for a solo founder has one goal: any small change reaches production within minutes of
merging, and any bad change leaves production within minutes of being noticed. Everything below
serves that loop. Rigor goes into making releases small and reversible, not into ceremony before
them.

1. **Small releases, every merge.** Risk grows with batch size. One change per deploy makes the
   cause of a failure obvious and the rollback cheap.
2. **Rollback is redeploying the previous artifact.** It already ran in production. A revert that
   needs a new build is too slow and depends on CI working during an incident.
3. **Two versions always run at once.** During every deploy, and in every open browser tab and
   installed app, old code meets the new schema and new API. Each release must work with the
   previous release's code, clients and data: add first, remove one release later.
4. **Build once, configure at runtime.** The artifact tested is the artifact shipped, identified by
   commit SHA and digest. Environments differ in configuration, never in code.
5. **Separate deploy from release.** Deploying puts code on servers; a flag decides who sees it.
   This removes long-lived branches, makes staff-only testing in production possible, and gives a
   faster off switch than any rollback.
6. **The pipeline is production access.** Whoever controls a workflow, an action it uses or a
   secret it holds can change production. Least privilege, pinned dependencies and short-lived
   credentials apply to CI as they do to servers.
7. **Fail before traffic, not during.** Type errors fail the pull request, bad configuration fails
   the boot, a bad boot fails the health check, a bad release fails the smoke test. Each gate is
   cheaper than the one after it.
8. **CI runs repository scripts.** The workflow file orchestrates; `package.json` scripts hold the
   logic, so a failure reproduces on a laptop with the same command.
9. **Add machinery when a problem demands it.** Staging, canaries, signing and self-hosted runners
   each cost attention. Previews, flags, smoke tests and one-command rollback cover most needs
   through Launch.

## Route

| If the task is … | Read |
|---|---|
| Set up GitHub Actions to check and build every pull request; protect main; CI is slow or expensive; CI fails but passes locally; where migrations run in the pipeline; mobile builds, signing and store submission | `references/ci-pipelines.md` |
| CI needs cloud or registry credentials; replace stored keys with OIDC; pull requests from forks or bots; restrict who can deploy to production; pin actions; sign artifacts or publish packages | `references/pipeline-security.md` |
| Add staging or preview environments; a missing or wrong environment variable broke the app; it works locally but not in production; seed or anonymize staging data; decide whether staging is needed | `references/environments-config.md` |
| Deploy on merge; remove deploy downtime; roll back a bad release; smoke tests and what to watch after a deploy; errors from old tabs or apps after deploy; order database, backend and frontend changes; deploy freezes; canaries; move to a new platform or database | `references/deploy-rollback.md` |
| Merge unfinished work safely; flag service or own table; beta access by account or plan; kill switch; roll out to 5% of users; remove old flags; a feature flickers on and off for a user; shed load in an incident | `references/feature-flags.md` |

Tasks often span files. A new deploy pipeline needs `ci-pipelines.md` for the checks,
`pipeline-security.md` for credentials and `deploy-rollback.md` for the rollout.

## Defaults at a glance

Follow what the project already uses first. For greenfield choices:

| Decision | Prototype | Launch | Scale |
|---|---|---|---|
| CI | GitHub Actions, one job: typecheck, lint, test, build | plus end-to-end tests on signup, login, payment; single required gate job | shards, remote build cache, affected-only runs |
| Main branch | pull request plus required check, 0 approvals when solo | same; no bypass | 1 approval, code owners on CI and migrations, merge queue |
| Deploy trigger | merge to main, by the PaaS git integration | same, gated by required checks; smoke tests after | same, with progressive rollout |
| Artifact | whatever the platform builds | one build per commit, deployed by SHA or digest | plus provenance attestation when customers ask |
| Migrations | a deploy step, not app startup | one serialized step before rollout, additive only per release | same, with rehearsal on production-sized data |
| Rollback | platform's previous-deployment button | one command, practiced, under 5 minutes; automatic on smoke failure | automatic on SLO burn |
| Deploy strategy | whatever the platform does | rolling or immutable deployments, at least 2 instances, graceful shutdown | canary where traffic supports it |
| CI credentials | platform git integration, no stored cloud keys | OIDC federation; production secrets in a protected environment | plus required reviewers |
| Actions | pinned to commit SHAs, `permissions` declared | same, with weekly grouped updates | plus an allowlist policy |
| Environments | local, production | plus preview per pull request with its own database | plus staging that every merge deploys to |
| Configuration | schema-validated at startup | same; values set in every environment before the code merges | same |
| Flags | constant or environment variable | Postgres table or the analytics tool's flags; kill switches on risky paths | flag service, expiry enforced in CI |
| Mobile | manual builds | EAS or fastlane from a tag, managed signing, staged rollout | plus over-the-air updates with runtime versioning |

GitHub plan caveat: on a private repository, branch rulesets and deployment environments exist
only on a paid plan. Confirm the plan before relying on either (`references/ci-pipelines.md`,
`references/pipeline-security.md`).

Numbers used as rules of thumb throughout: pull-request feedback under 10 minutes; merge to
production under 15 minutes; smoke suite under 2 minutes; rollback under 5 minutes; watch each
release for 15 to 30 minutes; release flags removed within 2 weeks of reaching 100%.

## Before you call it done

1. Every pull request runs typecheck, lint, tests and a production build, and main requires one
   aggregating check that fails when any upstream job fails or is cancelled; a direct push to main
   is rejected.
2. Every job has `timeout-minutes`; workflows declare `permissions`; third-party actions are
   pinned to full commit SHAs.
3. Jobs that run pull-request code or install dependencies hold no deploy credentials or
   production secrets.
4. Production credentials are short-lived (OIDC) or scoped deploy tokens stored as environment
   secrets, and the production environment accepts deployments from `main` only.
5. The deploy job has a concurrency group with `cancel-in-progress: false`.
6. Migrations run once per deploy, before the rollout, from versioned files, and the currently
   deployed code works after they run.
7. The deployed artifact is identified by commit SHA, and a health endpoint reports which SHA is
   serving.
8. Rollback has been executed once for real, and the command is written down.
9. A deploy under a request loop returns no failed requests: readiness check, graceful shutdown on
   SIGTERM, the app process receives the signal.
10. Smoke tests run against production after each deploy and a failure rolls back or alerts.
11. The error tracker tags events with the release, and a new error in the latest release alerts.
12. Configuration is parsed by a schema in one module at boot; `.env.example` lists every
    variable; a new variable exists in every environment before the code that reads it merges.
13. Non-production environments cannot reach production data, charge cards or email real users,
    and are not indexable.
14. Each flag has a kind, an owner and (for release flags) an expiry date; its default when the
    flag system is unreachable is the safe path; both states are tested.
15. Previous builds' static assets stay available after a deploy, and HTML is not cached long.

## Not this skill

- Choosing a host, writing Dockerfiles or Terraform → `0x:cloud-infrastructure`
- What tests to write and how to fix flaky ones → `0x:code-quality`
- Writing the zero-downtime schema migration itself → `0x:postgres-database`
- Secret storage, rotation, and dependency and supply-chain scanning → `0x:web-security`
- Branching model, pull requests and version numbers → `0x:git-collaboration`
- A/B experiment design and statistics → `0x:product-analytics`
