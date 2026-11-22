# Dependencies and software supply chain

Read this when: adding a package, setting up dependency updates or scanning, handling a vulnerability alert, responding to a package or build tool reported as compromised, planning a runtime upgrade before end of life, or dealing with a dependency that looks abandoned.

## The attack pattern to design against

The recurring incident: a maintainer's registry account is phished or a token stolen; a malicious patch release of a popular package is published; its install script or import-time code harvests tokens from developer machines and CI; the registry pulls it hours to days later. Some variants propagate by publishing further packages with the stolen tokens.

Four cheap controls each break the chain at a different point: a frozen lockfile (the new version is not picked up), a release cooldown (it is gone before it becomes eligible), disabled install scripts (the commonest trigger does not run), and scoped short-lived CI credentials (little to steal).

| Control | Stage |
|---|---|
| Lockfile committed; frozen installs in CI and images; vulnerability alerts on | Prototype |
| Install scripts off except an allow-list; cooldown; update automation | Launch |
| CI gate on high-severity findings; patch deadlines; end-of-life calendar | Launch |
| Image scanning; license allow-list in CI | Launch, where applicable |
| SBOM per release; artifact signing | Scale, or when a customer or regulation asks |

## Lockfile and frozen installs

| Tool | Install command for CI and images |
|---|---|
| pnpm | `pnpm install --frozen-lockfile` |
| npm | `npm ci` |
| Yarn (Berry) | `yarn install --immutable` |
| Bun | `bun install --frozen-lockfile` |
| pip | `pip install --require-hashes -r requirements.txt` |
| uv | `uv sync --locked` |

The lockfile pins every transitive version with an integrity hash. Without frozen mode each install re-resolves version ranges, and a malicious patch release reaches production on the next deploy with no commit to show for it.

Traps:

- A Dockerfile that copies `package.json` without the lockfile, or runs a plain install. With pnpm, copy `pnpm-workspace.yaml` too: since pnpm 11 it holds the settings (overrides, build allow-list, release-age rule), and an install without it ignores them.
- `npx <tool>` or `pnpm dlx <tool>` in CI, scripts or documentation runs the latest release outside the lockfile. Add the tool as a development dependency and call it with `pnpm exec`.
- `curl ... | bash` installers in CI: pin a version and verify a checksum.
- Mutable references elsewhere in the chain. Third-party GitHub Actions referenced by tag: pin to a full commit SHA (`0x:ci-cd-release`, `pipeline-security.md`). Base images referenced by tag: pin production images by digest (`node:22-slim@sha256:...`) and let the update bot bump the digest.
- Two lockfiles from two package managers. Pin one manager with the `packageManager` field.
- Lockfile changes in a pull request from outside the team: a `resolved` URL pointing off the registry, or a changed integrity hash for an unchanged version, is an attack and not noise.
- Internal package names without a scope: an attacker publishes the same name publicly with a higher version (dependency confusion). Put internal packages under an owned scope and map that scope to the private registry in `.npmrc`.

When a direct dependency has not caught up with a fix, force the patched transitive version with `overrides` (in `pnpm-workspace.yaml` for pnpm, which stopped reading the `pnpm` field of `package.json` in version 11; in `package.json` for npm), and delete the override once it has.

## Before adding a dependency

A two-minute identity check, mandatory when the name came from an AI assistant, a forum answer or memory. Models produce plausible package names that do not exist and attackers register them (slopsquatting), alongside classic typos and look-alike scopes.

```bash
npm view <package> time.created time.modified maintainers repository.url dist-tags.latest
```

Stop if the package is weeks old with few downloads and a name close to a popular one, if the repository named on the registry page does not link back to the package, or if the name differs from the one in the project's official documentation. A provenance attestation on the registry (built in CI from a named commit) is a positive signal, not proof.

Then evaluate:

| Question | Acceptable | Walk away, or plan around it |
|---|---|---|
| Maintained? | A release or meaningful commits within the last year; or small, finished and dependency-free | Unanswered security issues, archived repository, broken on the current runtime |
| Bus factor | Several maintainers with publish rights, or an organization or foundation behind it | One person on the critical path, unless the code is small enough to vendor |
| Weight | Few transitive dependencies | Dozens for a small feature: each is another maintainer account that can be phished |
| License | MIT, Apache-2.0, BSD, ISC; MPL-2.0 with care for modified files | GPL or AGPL in a proprietary product without counsel's view; source-available terms; no license file, which means no permission. Details: `0x:privacy-compliance` (`licenses-ip.md`) |
| Security-critical role: auth, crypto, parsing, sanitizing, templating | A record of handled advisories and a disclosure policy | No history, single maintainer |
| Needed at all? | Hard to get right, or large | Replaceable by a platform API (`fetch`, `URL`, `Intl`, `structuredClone`, `crypto`) or by thirty lines of owned code |

Rule: depend when the problem is hard to get right, the project has more than one maintainer or is small enough to own, and the license fits. Otherwise write it or vendor it. Recheck the license on major upgrades; projects relicense.

## Install scripts

Dependency lifecycle scripts (`preinstall`, `postinstall`) run arbitrary code with the installing user's access, on every laptop and CI runner.

- pnpm 10 and later does not run dependency build scripts unless the package is on the project's allow-list; `pnpm approve-builds` reviews and records them (the setting's name has changed between majors, so let the command write it). Keep the list to packages that compile or download binaries (typically a bundler's native binary, an image library, a database driver, the ORM's engine), and review every addition in the pull request.
- npm 12 and later skips dependency install scripts unless the package is approved (`npm approve-scripts`). A skipped script only warns by default, so a native module can end up unbuilt; turn on the strict setting in CI (see `npm help config`). On npm 11 and earlier set `ignore-scripts=true` in `.npmrc` and run `npm rebuild <package> --ignore-scripts=false` for the few that need a build. Bun skips dependency scripts by default and has a `trustedDependencies` allow-list. Yarn Berry: `enableScripts: false`.
- Scripts off filters the common trigger only; malicious code can still run when the module is imported. The cooldown and credential scoping cover that case.
- On CI, install in a step whose environment holds no deploy or publish credentials. Run unfamiliar repositories and take-home code in a container, not on the machine that holds cloud and registry logins.

## Update automation with a cooldown

Most malicious releases are detected and removed within days. Refusing versions younger than a few days removes most of that risk at no cost; 7 days is a sound default and 3 to 14 the reasonable range.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    cooldown:
      default-days: 7
    groups:
      minor-and-patch:
        update-types: ["minor", "patch"]
```

The Renovate equivalent is `"minimumReleaseAge": "7 days"`. Dependabot's cooldown delays version updates only; its security updates still arrive at once. Enforce the same rule at install time, so that a manual `pnpm add` or `pnpm update` obeys it: pnpm's `minimumReleaseAge` setting in `pnpm-workspace.yaml` (in minutes; 10080 is 7 days; pnpm 11 and later default to one day), with its exclude list for packages that must bypass it. The other managers have the same control under their own names and units (npm `min-release-age`, Yarn `npmMinimalAgeGate`, Bun `minimumReleaseAge`); read the unit in the manager's documentation before setting a number.

Policy:

- One grouped pull request per week for minor and patch updates; majors one at a time.
- A security update bypasses the cooldown deliberately, after reading the advisory and the diff, when the vulnerability is reachable in the product.
- Auto-merge only patch and minor updates of development dependencies, after the cooldown, and only with a test suite that would notice breakage. No tests, no auto-merge.
- Frequent small updates exist to keep the emergency path short. When a critical fix lands, one minor version behind is a ten-minute change; three majors behind is a migration under pressure.

## Scanning and patch deadlines

| What | Tool | Where |
|---|---|---|
| Dependency advisories, always on | The source host's dependency alerts with automatic security pull requests | Repository settings |
| Gate | `pnpm audit --prod --audit-level=high` (needs pnpm 11 or later: the registry retired the audit endpoints that older versions call, so they fail), or `osv-scanner` against the lockfile | CI on pull requests, plus a scheduled daily run, because new advisories appear against unchanged code |
| Container images | `trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 <image>` | CI after the build; rebuild weekly to pick up base-image fixes |
| Registry signatures | `npm audit signatures` | CI, optional |

Triage: most advisories are not exploitable in the product; the typical one is a ReDoS in a build-time
transitive package. Ask in order: is the package in the production dependency graph, does attacker-controlled
input reach the vulnerable function, is exploitation known in the wild? Then upgrade; or override the transitive
version; or `pnpm patch`; or mitigate in configuration; or record an ignore with a reason and an expiry date.
Never switch the check off to get a green build.

Deadlines count from the advisory and follow exploitability in the product, not the raw score. Rule of thumb, on the same scale as other findings in `security-testing.md`; a compliance policy may fix its own.

| Class | Deadline |
|---|---|
| Critical and reachable from the internet, or exploited in the wild | Mitigated within 24 to 72 hours, patched within 7 days |
| High | 30 days; 14 for internet-facing components |
| Medium | 90 days |
| Low, or not reachable | Next routine update |

The advisories that matter most concern the framework, runtime, auth library, database driver, proxy and base image. Subscribe to those projects' security announcements directly instead of waiting for a scanner to relay them.

## Upgrade cadence and end of life

A version past end of life receives no security fixes, and libraries drop it soon after, which blocks their fixes too.

| Component | Rule |
|---|---|
| Node.js | Production runs a release line that is in LTS. Move to the next LTS line within about six months of its promotion, and be off a line at least a quarter before its end-of-life date. The cadence changes with Node 27 in 2027 (one major a year, each becoming LTS), so read the dates from the project's release schedule, not from the old even-numbered pattern |
| PostgreSQL | One major release a year, each supported for five years. Managed hosts force upgrades at end of life; schedule the upgrade before they do (`0x:postgres-database`, `postgres-operations.md`) |
| Framework | Stay within one major of current; security fixes are backported only to recent majors |
| Base image and OS | Track the distribution's support window; rebuild weekly |
| Serverless and PaaS runtimes | Providers retire runtime versions on announced dates, after which deploys fail |

Keep an end-of-life calendar in the repository: component, current version, end-of-life date, planned upgrade quarter. `endoflife.date` lists the dates.

A cadence that keeps upgrades boring: the weekly grouped pull request; a monthly pass over what the bot could not merge; a quarterly review of majors and the calendar; one runtime LTS move per year. The rule behind it: never be forced to do a major upgrade and a security patch on the same day. Take majors one at a time, behind tests (`0x:code-quality`, `refactoring.md`).

## SBOM per release

Skip until a customer contract, a regulation covering products with software in them, or the team's own incident response needs it. Its internal value is answering "which releases contain package X at version Y?" in minutes.

```bash
syft <image> -o cyclonedx-json > sbom.cdx.json
trivy image --format cyclonedx --output sbom.cdx.json <image>   # alternative generator
grype sbom:sbom.cdx.json                                        # scan a stored SBOM later
```

- Generate in CI from the built artifact, not from `package.json`: the image contains OS packages and the full transitive tree.
- Format: CycloneDX or SPDX; produce whichever the requester names.
- Store it beside the release artifact, keyed by version and image digest. `docker buildx build --sbom=true --provenance=true` attaches both to the image as attestations.
- Scan stored SBOMs on a schedule. An SBOM that is generated and never read is paperwork.

## A package was compromised: blast radius

Commands for the exposure search in step 2:

```bash
pnpm why -r <package>
git log --oneline -S'<package>@<bad-version>' -- pnpm-lock.yaml
find . -path '*/node_modules/<package>/package.json' -not -path './.git/*' | xargs grep '"version"'
```

1. From the advisory, record the exact bad versions and the window during which they were live.
2. Was a bad version ever resolved? Check the lockfile and its history, then everything that installs without it: CI runs during the window (install logs), image builds, `npx` and global installs, developer machines that ran `add` or `update` in that window.
3. Where did it execute? Install time on CI or a laptop exposes everything that process could read: the job's CI secrets, registry and source-host tokens, SSH keys, cloud CLI sessions, `.env` files. Runtime in production exposes application secrets and data in memory. In the browser bundle it exposes user sessions and form input.
4. Contain: pin or override to a known-good version; clear CI caches, image layers and the package store; rebuild from clean.
5. Rotate everything exposed, from a clean machine, starting with credentials that publish or mint others: registry tokens, source-host tokens, CI secrets, cloud keys, then database and API credentials (`secrets.md`).
6. Look for persistence and misuse: new workflows, branches, repositories, deploy keys or package versions published under the team's accounts; the cloud audit trail and provider logs for the window.
7. A machine that ran an unknown payload is a compromised host. Reimage it instead of cleaning it.
8. If production or customer data was exposed, it is a security incident: `logging-breach-response.md`.

## An abandoned dependency

Signals: no release in roughly two years while security reports go unanswered, an archived repository, a deprecation notice, breakage on the current runtime. Stable, small and quiet is not abandoned; leave it alone.

| Situation | Action |
|---|---|
| A maintained successor or fork with real adoption exists | Migrate; vet the fork's publishers like a new package |
| The platform or framework now provides the function | Replace with the built-in |
| Small, permissive license | Vendor it: copy the source into the repository with its license notice, add tests, own it |
| One fix needed, upstream slow | `pnpm patch <package>@<version>`, edit, `pnpm patch-commit <dir>`. The patch file lives in the repository and reapplies on install. Pin the exact version and send the fix upstream |
| Large, critical, no alternative | Fork under the organization and publish under an owned scope, or depend on a commit SHA. Security fixes are now the team's job: budget for them, or pay for maintenance |
| Central to the product | Put it behind an interface first, so that replacement is a local change |

Traps: a git dependency without a commit SHA; a fork that silently falls behind; copyleft code vendored into a
proprietary product; and the revived package, since a new maintainer publishing after years of silence is what
an account or name takeover looks like. The defense is the cooldown plus reading the diff: `npm pack
<package>@<version>` and compare with the previous tarball, because the registry tarball need not match the
repository.

## Ask the user

- **Who patches a critical vulnerability within 72 hours, weekends included?** A deadline without an owner is fiction. Default: the founder, with alerts routed to a phone.
- **Is copyleft (GPL, AGPL) acceptable in the product?** That is a legal and business decision. Default: no; permissive licenses only, with counsel for exceptions.
- **How much auto-merge is acceptable?** It trades attention for risk. Default: development-dependency patch and minor updates only, after the cooldown and green tests.
- **Do customers or regulators ask for an SBOM or signed artifacts?** Otherwise skip both. Default: not required before Scale.
- **Are there internal packages or a private registry?** Dependency confusion then applies. Default: none; scope them if any appear.
