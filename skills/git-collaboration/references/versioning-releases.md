# Versioning, changelogs and release notes

Read this when: deciding how to number releases, tagging a release, tracing a deploy back to a commit, writing a changelog or release notes, automating version bumps, announcing a breaking change, or stating which versions are supported.

## First decide what kind of thing is being versioned

| Artifact | Who chooses when to upgrade | Scheme |
|---|---|---|
| Continuously deployed web app or SaaS | Nobody: everyone gets the new version | No semantic version. Identity is the commit SHA plus the deploy time. A dated product changelog for users |
| Library, SDK, CLI, package installed by others | The consumer | Semantic versioning, tags, a changelog per release |
| HTTP API consumed by customers | The consumer, slowly | API versioning policy; see `0x:api-design`. The server itself is still continuously deployed |
| Mobile or desktop app, self-hosted edition | The user or an app store | A marketing version plus a monotonically increasing build number; semver optional |

The common mistake is applying semver ceremony to a SaaS app: nobody consumes the number, "major" has no meaning when users cannot stay behind, and the version in `package.json` drifts from reality. Leave it at `0.0.0` with `"private": true` and use the SHA.

## Tie every deploy to a commit

Mandatory from Launch: for any running instance and any error report, the exact commit must be recoverable in under a minute. Without it, "which change broke this" becomes guesswork and rollback targets are unknown.

- Inject the commit SHA at build time as an environment variable. Most hosts and CI systems expose one; map it to a name the app owns (such as `APP_COMMIT_SHA`) so the code does not depend on a vendor variable.
- Expose it: in the health or version endpoint, in a response header or page metadata for the frontend, in every structured log line, and as the `release` in the error tracker. Upload source maps under the same release identifier so stack traces resolve (`0x:site-reliability`).
- Deploy only committed, pushed code built by CI. A deploy from a laptop with uncommitted changes has no commit that describes it.
- Build once and promote the same artifact through environments where the platform allows, so the SHA in staging and production means the same bytes (`0x:ci-cd-release`).
- Record deploys: the host's deploy history is usually enough. Tagging every production deploy in git is optional noise for a product deployed many times a day; tag when a deploy is a named release that people will refer to.

Tags for named releases:

```bash
git tag -a v1.4.0 -m "v1.4.0"      # annotated: has author, date, message, can be signed
git push origin v1.4.0             # tags are not pushed by a plain git push
git describe --tags                # e.g. v1.4.0-3-g9fceb02: 3 commits after v1.4.0
gh release create v1.4.0 --generate-notes
```

- Use annotated tags for releases. Lightweight tags are bare pointers with no metadata, and `git describe` ignores them by default.
- `gh release create` creates the tag itself, at the tip of the default branch, when the named tag does not exist on the remote. Add `--verify-tag` so a typo or an unpushed tag fails instead of releasing whatever is on `main`.
- A published tag never moves. Consumers, caches and registries have already resolved it; re-pointing it means two different things share one name. If a release is bad, publish the next patch. Protect release tag patterns with the host's tag rules so they cannot be deleted or force-updated.
- Tag the commit that was actually built and tested, on `main` or the release branch, after CI passed for that commit.
- Prefix consistently (`v1.4.0`). In a monorepo with several published packages, tags carry the package name (`@acme/sdk@1.4.0`).

## Semantic versioning for libraries and packages

`MAJOR.MINOR.PATCH`: major for incompatible changes, minor for backward-compatible additions, patch for backward-compatible fixes. The version is a promise about the public API, so the first task is to define that API: what is exported and documented. Anything reachable but undocumented should be made unreachable (the `exports` map) or it becomes API by use.

What counts as breaking, beyond the obvious removals and renames:

| Change | Breaking? |
|---|---|
| Removing or renaming an export, option, CLI flag, config key | Yes |
| Changing a default value or default behavior | Yes |
| Tightening accepted input, or widening what a function may return (new union member, now nullable) | Yes, including at the type level: consumers' builds fail |
| Adding a required parameter or required field | Yes |
| Raising the minimum runtime (Node version) or a peer dependency's minimum major | Yes |
| Changing the `exports` map, module format (CommonJS to ESM only) or file layout that consumers import | Yes |
| Changing error types, codes or messages that consumers are documented to match on | Yes |
| Adding an optional parameter, a new export, a new optional field | No (minor) |
| A bug fix that changes behavior people relied on | Judgment: patch if the old behavior contradicted the docs, otherwise treat as breaking or gate it behind an option |
| Performance, internal refactors, dependency patch updates | No (patch) |

Rules that are easy to get wrong:

- `0.y.z` means "anything may change", and package managers treat it differently: a caret range on `^0.2.3` allows `0.2.x` only, so on 0.x the minor position acts as the breaking position. Ship `1.0.0` as soon as real users depend on the package; staying on 0.x for years removes the signal semver exists to give.
- Pre-releases sort before the release: `1.0.0-rc.1 < 1.0.0`. Publish them under a non-default npm dist-tag (`npm publish --tag next`): without it the release candidate becomes `latest` for everyone, and recent npm versions refuse to publish a prerelease that has no explicit tag.
- Deprecate in a minor, remove in the next major. The deprecation ships with a runtime warning (once per process, not per call), a `@deprecated` annotation that editors display, and the replacement named in both.
- Batch breaking changes. Each major costs every consumer an upgrade project; several small majors a year train consumers to stop upgrading.
- A published version is immutable. Do not unpublish or republish; mark a bad version with `npm deprecate` and release a fix.
- Calendar versioning (`2026.11.0`) fits products where compatibility is not the message and recency is: apps, distributions, data releases. Do not use it for a library whose consumers rely on caret ranges.

## Changelogs and release notes

Two audiences, two documents. Mixing them fails both.

| | Developer changelog (`CHANGELOG.md`, GitHub release) | Customer release notes (product changelog page, email, in-app) |
|---|---|---|
| Reader | Someone upgrading a dependency or debugging a regression | A user deciding whether something matters to them |
| Unit | A version | A date or a named release |
| Content | Every notable change, grouped: Added, Changed, Deprecated, Removed, Fixed, Security | What they can now do, what changed in their workflow, what they must do |
| Source | Pull request titles or changeset summaries, edited | Written by a person from the user's point of view |

Writing rules for both:

- Describe the effect on the reader, not the implementation. "Exports larger than 10,000 rows no longer time out" instead of "Refactor export job to stream".
- Lead with what requires action: breaking changes, deprecations, security fixes, required configuration. Then additions, then fixes.
- One line per change, starting with a verb or the affected feature, with a link to the pull request or docs for detail.
- Leave out what the reader cannot perceive: refactors, test changes, CI, internal dependency bumps. A changelog that is a dump of the git log is noise people stop reading.
- Security fixes: say that a vulnerability was fixed, its severity and affected versions, and who must upgrade. Publish exploit detail only after users have had time to update.
- Newest first, each entry dated in ISO format (`2026-11-23`). Keep an `Unreleased` section at the top of a hand-maintained file so entries are written with the change, not reconstructed at release time.
- Never rewrite a published entry's meaning. Corrections are appended.

Customer release notes for a SaaS: write only for user-visible changes, in the product's vocabulary, with a screenshot when the UI changed.

Announce behavior changes to existing workflows before they ship, not after. Group small fixes into a periodic entry rather than a post per fix. Skip until Launch; from then on a public changelog page is cheap proof that the product is alive and is where support can point people.

## Automating bumps and changelogs

Automate once releases are frequent enough that doing it by hand gets skipped or done wrong. All of these depend on disciplined input, either commit messages or explicit change files; the tool only moves what people wrote.

| Tool | Input | Fits |
|---|---|---|
| Host-generated release notes (`gh release create --generate-notes`, categories from labels via `.github/release.yml`) | Merged pull request titles and labels | The lowest-effort start; apps and simple libraries. A person still picks the version number |
| release-please | Conventional Commits on `main` | A maintained "release pull request" accumulating the changelog and version bump; merging it tags and releases. Good default for a single package where a human should press the button |
| semantic-release | Conventional Commits on `main` | Fully automatic release on every qualifying merge, no human step. Fits mature libraries with strong tests |
| Changesets | A change file per pull request | Monorepos and any case where one commit affects several packages; see `monorepos.md` |

Traps:

- Under squash merge the pull request title is the only commit message the tool sees. Enforce the format on titles in CI (`branching-workflow.md`), and review the type: `feat` versus `fix` versus `feat!` decides the version number.
- A commit pushed or a tag created by a workflow using the default `GITHUB_TOKEN` does not trigger other workflows. The symptom is a release pull request with no CI run, or a tag that never starts the publish workflow. Use a GitHub App token (or a fine-scoped personal token) for the step that must trigger further runs, or publish in the same workflow.
- Tools compute the next version from the last release they can find: the last tag reachable from the branch, or a tag plus a version manifest file the tool keeps in the repository. A missing or mis-prefixed tag makes them propose `1.0.0` again or re-list the whole history; CI must fetch tags and full history for the release job.
- Which commit types cut a release differs per tool and is configurable (`feat` and `fix` do everywhere; `perf`, `deps`, `docs` and `revert` vary), as does the bump a breaking change gets below `1.0.0`. Read the tool's defaults before assuming a merge will or will not publish.
- Generated changelogs are drafts. Edit the release notes for anything user-facing; a line reading "fix: handle null" helps nobody.
- Publishing credentials, protected release environments and provenance belong to the pipeline (`0x:ci-cd-release`).

## Communicating breaking changes

A breaking change is a cost imposed on someone else; the release is judged by how cheap that cost was made. Sequence:

1. **Announce before removal.** Ship the replacement and the deprecation together in a minor release, so consumers can migrate while both work. Removing the old path in the same release that introduces the new one forces a flag-day upgrade.
2. **Warn in the channel the consumer actually sees**: a runtime deprecation warning and editor annotation for libraries; response headers and direct email to affected accounts for APIs; in-app notice and email for product behavior. A changelog entry alone reaches almost nobody.
3. **Give a date or a version** for the removal and keep it.
4. **Measure remaining use** where possible (calls to the deprecated endpoint per customer, telemetry on the old option) and contact the stragglers directly before the date.
5. **Remove in a major**, with the migration guide linked from the first line of the release notes.

Migration guide structure:

```markdown
# Migrating from v2 to v3

Who is affected: anyone calling `createClient` with `retries`, or running Node below the new minimum.
Time needed: about 15 minutes for a typical project.

## 1. `retries` option renamed to `retry.attempts`
Why: retry now also configures backoff.
Before: createClient({ retries: 3 })
After:  createClient({ retry: { attempts: 3 } })
How to find usages: search for `retries:` in files importing `@acme/sdk`.

## Removed with no replacement
...
## Behavior changes that will not fail at compile time
...
```

- One section per breaking change, each with why, before, after, and how to find affected code. "Behavior changes that will not fail at compile time" is the most important section, because nothing else will tell the consumer.
- Provide a codemod when the change is mechanical and widespread; it converts a deterrent into a command.
- State what happens to someone who does nothing: an error at install, at build, at runtime, or silently different results.
- For a paid product, removing functionality or changing pricing-relevant behavior can be constrained twice: by notice and change clauses in the customer contract or terms of service, and by consumer-protection law, which in some jurisdictions requires advance notice or a right to cancel when a subscription changes materially.
- Those rules differ by country and by whether the customers are businesses or consumers. Read the contracts before setting the date, and get legal advice before taking something away from paying customers (`0x:privacy-compliance` covers terms and consumer rules).

## Supported-versions policy

Publish one when anyone outside the team runs a version they chose: a library with more than one major in use, a self-hosted edition, a versioned API. Skip it for a SaaS app with a single deployed version.

```markdown
| Version | Status       | Released   | Bug fixes until | Security fixes until |
|---------|--------------|------------|-----------------|----------------------|
| 3.x     | Active       | 2026-09-01 | —               | —                    |
| 2.x     | Maintenance  | 2025-03-10 | ended           | 2027-03-01           |
| 1.x     | End of life  | 2023-06-02 | ended           | ended                |
```

- Define each status in a sentence: active gets features and all fixes; maintenance gets security fixes and critical regressions only; end of life gets nothing, including for security issues.
- State the rule, not just the table, so the future is predictable: for example, "the previous major receives security fixes for 12 months after the next major is released". Dates come from the rule.
- Set the end-of-life date when the successor ships, and announce it in the release notes of that successor. A date announced a month ahead is not notice.
- Promise only what one person can deliver. Each supported line is a branch to maintain, a CI matrix entry and a backport per fix (`branching-workflow.md`). For a solo maintainer, "latest major, plus security fixes for the previous one for a fixed period" is the sustainable ceiling.
- Include the supported runtime range (Node versions) and tie it to the runtime's own support schedule: dropping a runtime version that has itself reached end of life is the conventional moment, done in a major.
- Put the policy where people look: `SECURITY.md` for the security-fix scope, the README or docs site for the table.
- At end of life, publish a final release whose notes say so, and deprecate the line on the registry with a message pointing at the migration guide.

## Ask the user

- **Does anyone outside the team install or pin a version of this?** Decides between SHA-only identity and full semver with changelog. Default: for a web app, no version numbers, commit SHA plus a dated product changelog.
- **Should releases be published automatically on merge, or after a person approves a release pull request?** A risk preference. Default: a release pull request that a person merges.
- **How long will an old major keep receiving security fixes?** A commitment of future time. Default for a small team: the previous major only, for 12 months after its successor ships, stated in writing.
- **How much notice do customers get before a breaking change, and does any contract set a minimum?** Default when unknown: announce with the replacement available, remove no sooner than the next major, and check contract terms for paying customers before fixing a date.
- **Who is the audience of the changelog: developers integrating, or end users?** Decides tone and what is listed. Default: a developer changelog for packages and APIs, separate user-facing notes for the product.
