# Branching and commit workflow

Read this when: choosing or changing how work reaches `main` (branch model, squash versus merge versus rebase, commit message rules), keeping a long piece of work mergeable, or deciding whether release branches and signed commits are needed.

## The default: trunk-based, short-lived branches

One long-lived branch, `main`, always deployable. Every change is a branch off `main` that merges back within a day or two through a pull request. No `develop`, no `staging` branch; environments are a deploy concern, not a branch (see `0x:ci-cd-release`).

Why this is the default for a small team: integration pain grows faster than linearly with branch age, because each day adds both more of your changes and more of everyone else's. Short branches keep conflicts small, keep reviews small, and keep `main` close to what is in production, which makes rollback and bisecting meaningful.

| Stage | Practice |
|---|---|
| Prototype, solo | Committing straight to `main` is acceptable. Push at least daily; the remote is the backup |
| Launch, solo | Branch plus pull request for every change, self-merged once checks pass. The pull request is where CI, the preview deploy and automated review run, and it is the unit of rollback |
| Launch, 2+ people | Same, with one approval required on `main` |
| Scale | Add a merge queue when `main` breaks from changes that passed individually, and code owners for sensitive paths |

Rules that make trunk-based work:

- A branch that will take more than about two days gets split (see `pull-requests-review.md`) or merged dark behind a feature flag. Unfinished code may be on `main`; unfinished behavior may not be visible to users. Flags are in `0x:ci-cd-release`.
- `main` is protected: no direct pushes, no force pushes, required checks. The settings themselves are in `0x:ci-cd-release`.
- Delete branches on merge (enable the host's automatic deletion). A branch list of 80 stale names hides the three that matter.
- Branch names: `<type>/<short-topic>`, such as `fix/webhook-retry` or `feat/team-invites`. Include the issue key if a tracker links by it. The name matters little; the lifetime matters.
- Never reuse a branch after it was squash-merged. Its commits are not ancestors of `main`, so the next merge re-conflicts with its own earlier content. Start a new branch from `main`.

When not trunk-based: Git Flow style (`develop`, `release/*`, `hotfix/*`) exists for software shipped in numbered versions that customers install and that must be patched in parallel. A continuously deployed web product has one version in production, so those branches add merges with no benefit. If the project already uses Git Flow and ships fine, do not migrate it as a side effect of other work.

Local configuration that fits this workflow:

```bash
git config --global pull.rebase true          # no accidental merge commits on pull
git config --global rebase.autoStash true     # stash and restore around a rebase
git config --global fetch.prune true          # drop remote-tracking refs of deleted branches
git config --global push.autoSetupRemote true # first push sets the upstream
git config --global init.defaultBranch main
```

## Commits

A commit is the unit of revert, cherry-pick and bisect. Size it so each of those operations is useful: one logical change, building and passing on its own.

- Separate mechanical from meaningful. A rename, a formatter run or a dependency bump goes in its own commit (often its own pull request) so the behavioral diff is readable.
- Commit when something works, not at the end of the day. A sequence of small working states is what makes `reset`, `bisect` and conflict resolution cheap.
- Never commit generated secrets, `.env` files or credentials, even temporarily. Once pushed, treat as leaked (`0x:web-security`).

Message shape:

```text
Retry webhook delivery on 5xx with capped backoff

Stripe retries for three days, but our handler returned 500 on a
transient DB timeout and we dropped the event after the first try.
Retry up to 5 times, 1s to 60s, then park in the dead-letter table.

Refs: #214
```

- Subject: imperative mood, about 50 characters, no trailing period, says what the change does to the system. "Fix bug" and "Update file.ts" carry no information; the diff already shows which files changed.
- Blank line, then a body wrapped near 72 columns that explains why: the problem, the constraint that shaped the solution, the alternative rejected. The diff shows how.
- A body is optional for self-evident changes. It is mandatory for anything a future reader would question: a workaround, a deliberate inefficiency, a revert (say what broke), a behavior change.
- Trailers go at the end, one per line: `Refs: #214`, `Co-authored-by: Name <email>`. `Fixes #214` in a commit or pull request closes the issue on merge to the default branch on GitHub.

Under squash merge, the pull request title and description become the commit on `main`. Put the care there; branch commits may then be rough.

## Integration policy: merge, squash or rebase

Pick one for the repository and disable the others in the host settings; a mixed history is harder to read than any single choice.

| Policy | History on `main` | Choose when | Costs |
|---|---|---|---|
| Squash merge (default) | One commit per pull request, linear | Small team, short branches, branch commits are work-in-progress noise | Per-commit detail of the branch is gone from `main`; stacked branches need a rebase after the base lands; a large pull request becomes one large commit that is hard to bisect within |
| Merge commit | Branch commits plus a merge commit | Branch commits are curated and worth keeping; long-lived integration branches; open-source projects that value contributor history | Noisy graph; read `main` with `git log --first-parent`; a revert of a merge needs `-m 1` and complicates re-merging |
| Rebase merge | Branch commits replayed linearly, no merge commit | Every commit is curated and passes CI on its own | Commits get new hashes on `main`, so local branches look unmerged; intermediate commits were usually never tested by CI; no single commit to revert for a multi-commit change |

Settings that go with squash on GitHub: allow squash only, default the squash commit message to the pull request title and description, enable automatic branch deletion, and require linear history on `main`. Keep the pull request number in the subject (GitHub appends `(#123)`), which links every commit on `main` back to its discussion.

Squash traps:

- `git branch -d` reports the branch as not merged, because the squashed commit is a different commit. Use `-D` after confirming the pull request merged, or rely on `fetch.prune` and delete branches whose upstream is gone.
- Size is the hidden assumption. Squash is good because each pull request is small. A 3,000-line pull request squashed is a 3,000-line commit.
- Authorship of co-contributors is preserved only as `Co-authored-by` trailers.

Updating a branch with new `main`: rebase when the branch is yours alone (`git fetch && git rebase origin/main`, then `git push --force-with-lease`); merge `main` into the branch when someone else has pulled it or a review is in progress. Under squash merge either is fine, since neither survives on `main`.

## Keeping long-running work mergeable

Order of preference when a change is too big for one short branch:

1. **Sequence of independent pull requests into `main`**, each shippable alone, with unfinished behavior behind a flag. Nothing is long-running.
2. **Branch by abstraction** for replacing something in place: introduce an interface on `main`, move callers to it, build the new implementation beside the old one, switch by flag, delete the old one. Each step is a small pull request.
3. **Stacked branches** when later work truly depends on unreviewed earlier work: branch B is cut from branch A, and B's pull request targets A.
4. **A long-lived feature branch**, last resort (a framework major upgrade that cannot be staged). Rebase or merge from `main` daily, keep CI running on it, and set a date.

Stack mechanics with plain git:

```bash
git switch -c part-2 part-1                 # stack B on A
git rebase --update-refs origin/main        # from the top branch: moves every branch in the stack
# after part-1 is squash-merged into main:
git fetch
git rebase --onto origin/main part-1 part-2 # replay only part-2's own commits
git push --force-with-lease
```

- After the base of a stack is squash-merged, a plain `git rebase origin/main` on the next branch replays the base's original commits against their own squashed copy and conflicts. `--onto` with the old base as the cut point avoids that.
- Retarget the next pull request to `main` after the base merges. GitHub does this automatically when the base branch is deleted on merge.
- Keep stacks shallow: two or three levels. Deeper stacks make every review comment at the bottom a rebase of everything above. Dedicated stacking tools exist; adopt one only if stacking is a daily habit.
- `rerere.enabled true` pays off here: the same conflict recurs across repeated rebases and gets resolved automatically the second time.

Daily habit for any branch older than a day: `git fetch && git rebase origin/main`, run the tests, push. Conflicts found daily are a few lines; found after two weeks they are an afternoon.

## Commit-message convention for tooling

Adopt Conventional Commits when a tool will read the messages (automated version bumps, generated changelogs; see `versioning-releases.md`) or when the team wants scannable history. Skip the enforcement machinery at Prototype.

```text
<type>(<optional scope>)<!>: <description>

<optional body>

BREAKING CHANGE: <what breaks and how to migrate>
```

| Type | Meaning | Semver effect in release tools |
|---|---|---|
| `feat` | New user-visible capability | minor |
| `fix` | Bug fix | patch |
| `feat!` / `fix!` or a `BREAKING CHANGE:` footer | Incompatible change | major |
| `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf` | No release by default (tool-dependent) | none |

- With squash merge only the pull request title lands on `main`, so lint the title, not each commit. A check on the pull request title in CI is enough; a local commit hook on every WIP commit is friction with no effect on `main`.
- With merge or rebase policy every commit lands, so lint commits (commitlint in CI, optionally a `commit-msg` hook).
- The type is a claim about user impact. `fix` for a refactor triggers a release with an empty changelog entry; `chore` for a behavior change hides it from the changelog. Review the title like code.
- Scopes are useful in a monorepo (`feat(billing): ...`) when they match package or app names; free-form scopes drift into noise.

## Release branches and backports

A continuously deployed product needs none. Production runs a commit of `main`; a bad release is fixed by rolling back the deploy or reverting on `main` and deploying again.

Create a release branch only when an older version must keep receiving fixes while `main` has moved on: a published library with a supported previous major, a mobile app version in store review, a self-hosted or on-premises edition, or a customer contractually pinned to a version.

- Name by line, not by patch: `release/2.x` or `release/1.4`. Tags (`v1.4.3`) mark the individual releases on it.
- Fix on `main` first, then backport: `git cherry-pick -x <hash>` onto the release branch (`-x` records the original hash in the message). Fixing on the release branch first is how a bug gets fixed in 1.4.3 and reappears in 2.0.
- Exception: the bug exists only in the old line because `main` rewrote that code. Fix on the release branch and note in the pull request why no forward port is needed.
- Never merge a release branch back into `main` wholesale, and never merge `main` into a release branch; both drag unrelated changes across. Individual cherry-picks only.
- Protect release branches like `main` and run the same CI on them.
- Backport only security fixes and serious regressions. Each extra supported line roughly doubles the cost of every such fix; publish which lines are supported and until when (`versioning-releases.md`).

Hotfix when `main` holds changes that cannot ship yet (this itself signals missing flags): branch from the deployed tag or commit, fix, deploy from that branch, then immediately land the same fix on `main` and return to deploying from `main`.

## Signed commits and verified authorship

The author name and email on a commit are free text set by whoever made it; anyone with push access can commit as anyone. A signature binds the commit to a key, and the host's "Verified" badge binds that key to an account.

When it matters: several people with push access, an open-source project accepting contributions, a compliance requirement, or a release process where tags must be attributable. For a solo private repository it adds little security beyond account 2FA, but SSH signing is cheap enough to enable anyway.

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

- Add the public key to the host account as a signing key. On GitHub this is a separate entry from the authentication key, even when it is the same key.
- The committer email must match a verified email on the account, or the commit shows as unverified despite a valid signature.
- Local verification (`git log --show-signature`) of SSH signatures needs an allowed-signers file configured with `gpg.ssh.allowedSignersFile`; without it git reports the signature as unverifiable, which is not a sign of tampering.
- Enforcement is a branch rule ("require signed commits") on `main` and release branches. Before turning it on, confirm every path that writes to the branch can sign: merges performed in the host's web interface are signed by the host, while commits pushed by CI jobs or bots using plain git are unsigned unless a key is configured for them. Test the rule on one branch first.
- The rule interacts with the merge method: check that the chosen method (squash in the web interface is the safe case) still produces signed commits under the rule before requiring it.
- Signing proves which key made the commit, not that the code was reviewed. Required review and code owners (`pull-requests-review.md`) cover that; provenance of build artifacts is in `0x:ci-cd-release`.
- A lost or leaked signing key: remove it from the account and add a new one. Removing a key makes the commits it signed show as unverified on GitHub, so keep it listed if it was merely retired, and remove it only if it was compromised.

## Ask the user

- **Does anything need to keep working on an older version after `main` moves on?** Decides whether release branches exist at all. Default: no; deploy from `main` only.
- **Is `main` deployed automatically on merge?** If yes, unfinished work must be flagged or held back, and merge timing matters. Default: assume yes and keep `main` releasable.
- **Should individual branch commits be preserved on `main`?** Decides squash versus merge. Default: squash, with the pull request title and description as the commit.
- **Will a tool generate versions or changelogs from commit messages?** Decides whether to enforce Conventional Commits. Default: use the format for pull request titles without enforcement until a release tool is adopted.
- **Is there a compliance or customer requirement for signed commits?** Default: enable SSH signing locally, do not enforce it by branch rule until there are several committers.
