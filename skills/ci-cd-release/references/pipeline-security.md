# Pipeline security and provenance

Read this when: CI needs cloud, registry or deploy credentials, a workflow runs code from forks or
bots, production deploys must be restricted, or the build has to prove what it produced.

## How pipelines get compromised

A pipeline executes third-party code (actions, dependency install scripts, pull-request code) next
to credentials that can change production. Routes, most common first:

1. A third-party action or its tag is compromised and reads every secret in the job (in the
   tj-actions/changed-files incident, March 2025, repointed tags printed job secrets into logs).
2. A privileged trigger runs untrusted pull-request code, or untrusted text reaches a shell script.
3. A long-lived cloud key stored as a secret leaks once and works until someone rotates it.
4. Anyone with write access edits a workflow on a branch and uses production secrets.

Each section below closes one route. Secret storage and rotation, dependency scanning and SBOMs:
`0x:web-security` (`secrets.md`, `supply-chain.md`).

## Pin actions, shrink the token

```yaml
permissions: {}                 # workflow default: nothing
jobs:
  build:
    permissions:
      contents: read
      packages: write           # only what this job needs
    steps:
      - uses: actions/checkout@<40-character-commit-sha>   # vX.Y.Z
        with: { persist-credentials: false }
```

- Tags and branches are mutable; a full commit SHA is not. Keep the version in a trailing comment
  so Dependabot or Renovate updates both. Turn on the Actions policy that requires full-SHA pins
  and restricts which actions may run.
- Copy the SHA from the action's own repository. A commit that exists only in a fork resolves
  under the upstream name too.
- A pin does not cover what the action downloads at run time (`curl | bash`, a `latest` binary),
  container actions on a mutable image tag, or actions it calls by tag. Fewer actions is the
  stronger control: prefer a `run:` step with a CLI already on the runner (`gh`, `aws`, `docker`)
  over a wrapper action from an unknown author.
- Update weekly and grouped, and delay brand-new releases by a few days (Dependabot's `cooldown`,
  which has a short default on github.com; Renovate's `minimumReleaseAge`) so a compromised
  release is found by someone else first. Security updates are not delayed by it.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule: { interval: weekly }
    cooldown: { default-days: 7 }
    groups: { actions: { patterns: ['*'] } }
```

Token rules. Declaring any permission sets every unlisted one to none: start from
`permissions: {}` and grant per job. Confirm the repository's default workflow permission is
read-only; old repositories may still default to read-write.

| Job does | Grant |
|---|---|
| Checkout, test, build | `contents: read` |
| Push an image to GHCR | `packages: write` |
| Request an OIDC token (cloud login, trusted publishing) | `id-token: write` |
| Comment on or label a pull request | `pull-requests: write` |
| Create a release or push a tag | `contents: write` |
| Write a build attestation | `attestations: write` and `id-token: write` |

- `persist-credentials: false` on checkout unless the job pushes. Otherwise the token stays on the
  runner for every later step; older checkout versions wrote it into `.git/config`, where it also
  travels inside any artifact that includes the workspace.
- For cross-repository access, mint a GitHub App installation token in the job (short-lived,
  scoped) instead of storing a personal access token tied to a person. Events created with
  `GITHUB_TOKEN` do not start other workflows by design, which is why a release created by a
  workflow does not fire `on: release`.
- `${{ }}` is substituted into the script text before the shell runs. Pull-request titles and
  bodies, branch names, commit messages and comments are attacker-controlled; pass them through
  `env` and quote the variable:

```yaml
      - run: echo "$TITLE"
        env:
          TITLE: ${{ github.event.pull_request.title }}
```

- Log masking matches the exact secret string. A base64 or URL-encoded copy, or one field of a
  JSON secret, is printed in clear. Store fields as separate secrets and keep `set -x` out of
  steps that hold them.
- Lint workflows in CI: `actionlint` for correctness, `zizmor` for these security patterns.

## OIDC federation instead of stored cloud keys

The job asks the CI provider for a signed identity token (`id-token: write`), the cloud checks its
claims against a trust policy and returns credentials that expire within about an hour. Nothing is
stored, so nothing leaks from secrets and nothing needs rotation. The security is entirely in the
claim conditions, and the subject claim changes shape with the job context and with the age of the
repository:

| Job context | `sub` claim, classic format |
|---|---|
| Branch, no environment | `repo:ORG/REPO:ref:refs/heads/main` |
| Tag, no environment | `repo:ORG/REPO:ref:refs/tags/v1.2.3` |
| Pull-request event, no environment | `repo:ORG/REPO:pull_request` |
| Any job with `environment: production` | `repo:ORG/REPO:environment:production` |

Repositories created or renamed since mid-2026 get an immutable subject by default, in which owner
and repository names each carry a numeric ID (`repo:ORG@<owner-id>/REPO@<repo-id>:...`); older
ones keep the classic form until they opt in. A policy copied from an older project, or a wildcard
such as `repo:ORG/*`, then fails. Get the IDs with `gh api repos/ORG/REPO --jq '.id, .owner.id'`
and confirm the exact string against the `sub` of a real token (the cloud's audit log records it
on a rejected login) before pasting it into the policy.

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": { "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:ORG/REPO:environment:production"
  } }
}
```

The job declares `permissions: { id-token: write, contents: read }` and `environment: production`,
then runs `aws-actions/configure-aws-credentials` with `role-to-assume` and `aws-region`. No
access key is stored anywhere.

- Trust the production role to the `environment:production` subject only, and let the environment
  restrict branches (below). A wildcard such as `repo:ORG/REPO:*` on a production role lets any
  branch or pull-request workflow assume it; `repo:ORG/*` extends that to every repository.
- Adding `environment:` to a job changes its subject from the `ref:` form to the `environment:`
  form. A trust policy written for `ref:refs/heads/main` then stops matching.
- One role per environment and purpose: deploy-staging, deploy-production, and a read-only role
  for infrastructure plans on pull requests. A deploy role pushes the image and updates the
  service; it does not administer IAM. Role design: `0x:cloud-infrastructure` (`iam-accounts.md`).
- Google Cloud: a workload identity pool provider with an attribute condition naming the
  repository (without it, tokens from any repository match), through `google-github-actions/auth`.
  Azure: a federated credential whose subject equals the `sub` claim exactly, through
  `azure/login`; client, tenant and subscription IDs are identifiers, not secrets.
- No OIDC on the target platform: first prefer the platform's own git integration, so CI holds no
  deploy credential and required checks on main are the gate. Otherwise use the narrowest deploy
  token, stored as an environment secret, and rotate it on a schedule.
- After migrating, delete the old keys from CI and deactivate them in the cloud, then confirm in
  the cloud audit log that the session's subject is the expected one.

| Error | Cause |
|---|---|
| Not authorized to perform `sts:AssumeRoleWithWebIdentity` | `sub` mismatch: the job gained or lost an `environment`, the branch or repository was renamed, or the condition is misspelled |
| `Unable to get ACTIONS_ID_TOKEN_REQUEST_URL`, or the login action finds no OIDC token | `id-token: write` missing (declaring other permissions removed it), or the run comes from a fork |

## Fork and untrusted pull-request builds

| Trigger | Workflow file from | Secrets | `GITHUB_TOKEN` |
|---|---|---|---|
| `pull_request`, branch in the same repository | the pull request | available | as declared |
| `pull_request`, from a fork | the pull request | none | read-only |
| `pull_request`, opened by Dependabot | the pull request | Dependabot secrets only | read-only |
| `pull_request_target` | the default branch | available | can be read-write |
| `workflow_run` | the default branch | available | can be read-write |

- Jobs that execute pull-request code (install, lint, test, build) run on `pull_request` and hold
  no secrets. This protects a private solo repository too: the untrusted code there is a
  compromised dependency's install script or an unreviewed generated change.
- Use `pull_request_target` only for jobs that do not check out, install or run pull-request code,
  such as labeling. That trigger plus a checkout of `github.event.pull_request.head.sha` plus any
  install or build step hands every secret to the pull request's author. GitHub keeps tightening
  it: recent `actions/checkout` versions refuse to fetch fork pull-request code under it unless
  `allow-unsafe-pr-checkout` is set, and public repositories are moving to blocking the event
  unless a policy allows it. Needing the override means the design is wrong; use the split below.
- For a privileged follow-up on untrusted code (coverage comment, preview deploy), split it. The
  `pull_request` workflow uploads its result as an artifact; a `workflow_run` workflow downloads it
  and treats it as data: nothing in it is executed or unpacked over the workspace, and pull-request
  numbers or paths found inside are validated.
- Dependabot runs fail on steps that need secrets. Define only non-production values as Dependabot
  secrets, or skip the step with `if: github.event.pull_request.user.login != 'dependabot[bot]'`.
- A preview deployment runs pull-request code with the preview environment's runtime secrets.
  Previews get throwaway credentials only (`environments-config.md`); fork pull requests get no
  automatic preview.
- Public repository: require approval before workflows run for outside contributors. That protects
  compute, not secrets. Do not attach self-hosted runners.

## Environment protection rules

A repository secret is readable by any workflow on any branch, so whoever can push a branch can
write a workflow that uses it. An environment secret is released only to a job that names the
environment, after the environment's rules pass. Set up `production` like this:

1. Deployment branches and tags: `main` only. Without this rule a feature-branch workflow can
   declare `environment: production`.
2. Move every production credential from repository secrets to environment secrets, and bind the
   cloud trust policy to the environment subject.
3. Required reviewers once more than one person can merge, with self-review prevented. For a solo
   founder a reviewer gate adds a pause, not a control; skip it unless a deliberate click before
   production is wanted.
4. Turn off administrator bypass.
5. The deploy job declares `environment: production` and a `concurrency` group.
6. Protect what feeds it: the ruleset on main; a tag ruleset when tags start releases (otherwise
   anyone with write access pushes a version tag and ships); code owners on `.github/` in a team.

Plan limits for private repositories (at the time of writing; check the current plan table): Free
has no environments, environment secrets or deployment branch rules; Pro and Team add those;
required reviewers and wait timers need Enterprise. Without environments, let the PaaS git
integration deploy so CI holds no production credential, or upgrade before storing one. Without
reviewers, the ruleset on main plus restricted merge rights is the gate.

The pipeline is not the only path. Everyone with a PaaS dashboard role or cloud console access can
deploy: list them and require MFA (`0x:web-security`, `accounts-admin-hardening.md`). Keep one
documented manual deploy path for when CI is down, with its credentials stored apart and its use
logged.

## Sign artifacts and verify provenance

Skip until Scale, a customer questionnaire asks for SLSA or signed builds, or other parties consume
the artifacts. Deploying by digest from a protected pipeline with OIDC covers most of the risk for
one team deploying its own image. Signing adds proof that the bytes in the registry came from one
specific workflow, which matters when the registry or a push credential could be compromised.

A provenance attestation is a signed statement binding an artifact digest to the repository,
workflow and commit that built it. Keyless signing uses the job's OIDC identity for a short-lived
certificate and a public transparency log, so there is no key to manage.

```yaml
    permissions: { id-token: write, attestations: write, packages: write, contents: read }
    steps:
      # ...build and push; capture the image digest as steps.push.outputs.digest
      - uses: actions/attest-build-provenance@<commit-sha>
        with:
          subject-name: ghcr.io/ORG/APP
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true
```

```bash
gh attestation verify oci://ghcr.io/ORG/APP@sha256:<digest> --repo ORG/REPO
```

- Sign and verify the digest, not a tag.
- Verification must pin the expected identity: repository, workflow file and ref. Anyone can
  produce a valid keyless signature for any image; "is signed" proves nothing. With
  `gh attestation verify`, `--repo` pins the repository and `--signer-workflow` the workflow file.
  With cosign that is
  `--certificate-identity` (or `-regexp`) plus
  `--certificate-oidc-issuer https://token.actions.githubusercontent.com`.
- Verify in the deploy job just before rollout. Cluster admission policies are a Scale concern.
- Attestation support for private repositories depends on the plan; check before relying on it.
- Provenance says where the artifact was built, not that the source or its dependencies were sound.

## Trusted publishing for packages

A long-lived registry token in CI lets whoever steals it publish malware under the package name.
Trusted publishing replaces it: the registry is told which repository, workflow file and
environment may publish, and accepts that job's OIDC token.

- **npm.** Configure the trusted publisher in the package settings on npmjs.com. The publish job
  needs `id-token: write`, a recent npm CLI (11.5.1 or later at the time of writing; the one
  bundled with an older Node is too old) and no `NODE_AUTH_TOKEN`; `npm publish` then attaches
  provenance automatically for a public package built from a public repository. The workflow file
  name must match the configuration exactly, and it is the entry workflow that counts, not a
  reusable workflow it calls. The package has to exist before a publisher can be attached, so a
  first release needs one manual publish, and a new publisher configuration lapses unless a
  publish succeeds soon after it is created (check the current window). Afterwards set the package
  to disallow token publishing. Classic tokens are gone and write tokens have short enforced
  lifetimes; do not design a pipeline around one. npm also has staged publishing, where CI stages
  a release and a maintainer approves it with 2FA: check which mode the configuration allows.
- **PyPI.** Add the publisher in the project settings (a pending publisher works for a new name)
  and publish with `pypa/gh-action-pypi-publish`, no password.
- RubyGems, crates.io and NuGet follow the same model.
- **Container registries.** GHCR accepts `GITHUB_TOKEN` with `packages: write`; cloud registries
  use the OIDC role; a registry with only access tokens gets a scoped one in an environment secret.

Job design: publish from a tag or release on a protected ref, in a dedicated job with its own
environment (`environment: npm`) named in the publisher configuration. Build and test in earlier
jobs, so `id-token: write` exists only where the publish command runs.

## Verify

```bash
grep -rnE 'uses: +[^ @]+@(v[0-9]|main|master)' .github/   # expect no output: all pinned
grep -rLE '^permissions:' .github/workflows/                # expect no output: all declare it
grep -rn 'pull_request_target' .github/workflows/           # each hit: no checkout of the PR head
gh secret list && gh secret list --env production           # no long-lived cloud keys at repo level
```

Then push a branch whose workflow declares `environment: production`: the run must be rejected by
the deployment branch rule.

## Ask the user

- **Is the repository public or open to outside contributors?** Decides how strict fork handling
  must be. Default: private; still keep secrets out of jobs that run pull-request code.
- **Who may deploy to production, and is an approval click wanted?** Default: merges to main
  deploy; no reviewer gate while solo; one required reviewer once a second person can merge.
- **Which GitHub plan is the organization on?** Protection rules and attestations for private
  repositories depend on it. Default: assume branch restrictions only and verify.
- **Do customers or auditors ask for build provenance (SLSA, SOC 2 change control)?** Default: no;
  add attestations when the first questionnaire asks.
