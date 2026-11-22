# Pipeline security and provenance

Read this when: CI needs cloud, registry or deploy credentials, a workflow runs code from forks or
bots, production deploys must be restricted, or the build has to prove what it produced.

## How pipelines get compromised

A pipeline executes third-party code (actions, dependency install scripts, pull-request code) next
to credentials that can change production. Routes, most common first:

1. A third-party action or its tag is compromised and reads every secret in the job. In the
   tj-actions/changed-files incident (March 2025) repointed tags made the action print job secrets
   into build logs.
2. A privileged trigger runs untrusted pull-request code.
3. Untrusted text is interpolated into a shell script.
4. A long-lived cloud key stored as a secret leaks once and works until someone rotates it.
5. Anyone with write access edits a workflow on a branch and uses production secrets.

Each section below closes one route. Secret storage and rotation, dependency scanning and SBOMs:
`0x:web-security` (`secrets.md`, `supply-chain.md`).

## Pin actions, shrink the token

```yaml
permissions: {}                 # workflow default: nothing

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write           # only what this job needs
    steps:
      - uses: actions/checkout@<40-character-commit-sha>   # vX.Y.Z
        with:
          persist-credentials: false
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
- Update weekly and grouped; delay brand-new releases by a few days (Dependabot's cooldown setting,
  Renovate's `minimumReleaseAge`) so a compromised release is found by someone else first.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule: { interval: weekly }
    groups:
      actions: { patterns: ['*'] }
```

Token rules:

- Declaring any permission sets every unlisted one to none. Start from `permissions: {}` and grant
  per job. Confirm the repository's default workflow permission is read-only; old repositories may
  still default to read-write.

| Job does | Grant |
|---|---|
| Checkout, test, build | `contents: read` |
| Push an image to GHCR | `packages: write` |
| Request an OIDC token (cloud login, trusted publishing) | `id-token: write` |
| Comment on or label a pull request | `pull-requests: write` |
| Create a release or push a tag | `contents: write` |
| Write a build attestation | `attestations: write` and `id-token: write` |

- `persist-credentials: false` on checkout unless the job pushes. Otherwise the token sits in
  `.git/config` for every later step and inside any artifact that includes the workspace.
- For cross-repository access, mint a GitHub App installation token in the job (short-lived,
  scoped) instead of storing a personal access token tied to a person. Events created with
  `GITHUB_TOKEN` do not start other workflows by design, which is why a release created by a
  workflow does not fire `on: release`.
- `${{ }}` is substituted into the script text before the shell runs. Pull-request titles and
  bodies, branch names, commit messages and comments are attacker-controlled; pass them through
  `env` and quote the variable:

```yaml
      - run: echo "Title: $TITLE"
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
claim conditions, and the subject claim changes shape:

| Job context | `sub` claim |
|---|---|
| Branch, no environment | `repo:ORG/REPO:ref:refs/heads/main` |
| Tag, no environment | `repo:ORG/REPO:ref:refs/tags/v1.2.3` |
| Pull-request event, no environment | `repo:ORG/REPO:pull_request` |
| Any job with `environment: production` | `repo:ORG/REPO:environment:production` |

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

```yaml
    permissions: { id-token: write, contents: read }
    environment: production
    steps:
      - uses: aws-actions/configure-aws-credentials@<commit-sha>
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/deploy-production
          aws-region: eu-central-1
```

- Trust the production role to the `environment:production` subject only, and let the environment
  restrict branches (below). A wildcard such as `repo:ORG/REPO:*` on a production role lets any
  branch or pull-request workflow assume it; `repo:ORG/*` extends that to every repository.
- Adding `environment:` to a job changes its subject from the `ref:` form to the `environment:`
  form. A trust policy written for `ref:refs/heads/main` then stops matching.
- One role per environment and purpose: deploy-staging, deploy-production, and a read-only role
  for infrastructure plans on pull requests. A deploy role pushes the image and updates the
  service; it does not administer IAM. Role design: `0x:cloud-infrastructure` (`iam-accounts.md`).
- Google Cloud: a workload identity pool provider with an attribute condition naming the
  repository (without it, tokens from any repository match), used through
  `google-github-actions/auth`. Azure: a federated credential on an app registration or managed
  identity whose subject equals the `sub` claim, used through `azure/login`; client, tenant and
  subscription IDs are identifiers, not secrets.
- No OIDC on the target platform: first prefer the platform's own git integration, so CI holds no
  deploy credential and required checks on main are the gate. Otherwise use the narrowest deploy
  token, stored as an environment secret, and rotate it on a schedule.
- After migrating, delete the old keys from CI and deactivate them in the cloud, then confirm in
  the cloud audit log that the session's subject is the expected one.

| Error | Cause |
|---|---|
| Not authorized to perform `sts:AssumeRoleWithWebIdentity` | `sub` mismatch: the job gained or lost an `environment`, the branch or repository was renamed, or the condition is misspelled |
| No ID token request URL available | `id-token: write` missing (declaring other permissions removed it), or the run comes from a fork |

## Fork and untrusted pull-request builds

| Trigger | Workflow file from | Secrets | `GITHUB_TOKEN` |
|---|---|---|---|
| `pull_request`, branch in the same repository | the pull request | available | as declared |
| `pull_request`, from a fork | the pull request | none | read-only |
| `pull_request`, opened by Dependabot | the pull request | Dependabot secrets only | read-only |
| `pull_request_target` | the base branch | available | can be read-write |
| `workflow_run` | the default branch | available | can be read-write |

- Jobs that execute pull-request code (install, lint, test, build) run on `pull_request` and hold
  no secrets. This protects a private solo repository too: the untrusted code there is a
  compromised dependency's install script or an unreviewed generated change.
- Use `pull_request_target` only for jobs that do not check out, install or run pull-request code,
  such as labeling. `pull_request_target` plus a checkout of
  `github.event.pull_request.head.sha` plus any install or build step hands every secret to the
  author of the pull request.
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

Which rules a private repository gets depends on the GitHub plan; required reviewers and wait
timers sit on higher tiers than branch restrictions. Check before designing around an approval
gate. Where reviewers are unavailable, the branch ruleset plus restricted merge rights is the gate.

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
workflow, commit and runner that built it. Keyless signing uses the job's OIDC identity to obtain a
short-lived certificate and records the signature in a public transparency log; there is no key
to manage.

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
  produce a valid keyless signature for any image; "is signed" proves nothing. With cosign that is
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
  needs `id-token: write`, a recent npm CLI (check the minimum version) and no `NODE_AUTH_TOKEN`;
  `npm publish` then attaches provenance automatically. The workflow file name must match the
  configuration exactly, and it is the entry workflow that counts, not a reusable workflow it
  calls. The package has to exist before a publisher can be attached, so a first release may need
  one manual publish. Afterwards set the package to disallow token publishing. npm has also been
  retiring long-lived write tokens; do not design a new pipeline around one.
- **PyPI.** Add the publisher in the project settings (a pending publisher works for a new name)
  and publish with `pypa/gh-action-pypi-publish`, no password.
- RubyGems, crates.io and NuGet follow the same model.
- **Container registries.** GHCR accepts `GITHUB_TOKEN` with `packages: write`; cloud registries
  use the OIDC role. A registry that only offers access tokens gets a scoped one in an environment
  secret.

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
- **Are packages published to a public registry?** Default: no; if yes, trusted publishing from
  the first release.
