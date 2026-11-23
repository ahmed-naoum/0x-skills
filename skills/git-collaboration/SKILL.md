---
name: git-collaboration
description: Uses git and the repository as a team tool, covering recovery of lost work, conflicts, history search, branching and merge policy, pull requests and review conventions, monorepos, and release versioning with changelogs. Use when git history is messed up, a conflict needs resolving, choosing squash, merge or rebase, writing or splitting a pull request, setting up CODEOWNERS or workspaces, or versioning releases.
---

# Git and collaboration

## Stance

The repository is the team's shared memory and its integration point, also when the team is one person and a coding agent. An expert treats history as a product with readers: the person bisecting a regression, the reviewer, the future maintainer running blame. Most decisions here follow from keeping changes small, keeping `main` releasable, and never destroying what someone else may depend on.

- **Predict before running.** Every git command moves data between commits, refs, the index and the working tree. Name which of those a command touches before running it; surprises come from running commands by habit.
- **Committed work is almost never lost; uncommitted work is.** The reflog recovers resets, rebases and deleted branches for weeks. Nothing recovers an unstaged edit overwritten by `reset --hard`, `restore` or `clean`. Commit early, on a branch, and tidy later.
- **Rewrite private history freely, shared history never.** Amend and rebase what only exists locally or on a personal branch. On `main` or anything others have pulled, add a revert instead, because a rewrite breaks every clone and open pull request.
- **Small and short-lived beats everything else.** Integration cost grows faster than branch age and review quality collapses with size. A branch older than two days or a pull request over about 400 lines is the problem to solve, by splitting or by a feature flag.
- **`main` is always deployable.** Unfinished code may merge; unfinished behavior may not be visible. This is what makes rollback, bisect and continuous deploy work.
- **Write the why.** The diff records what changed. The commit message and pull request description are the only place the reason survives, and under squash merge the pull request title and description are the commit.
- **Human review is for judgment.** Formatting, types, tests and scanning belong to automated checks. People look at whether it is the right change, correctness, design and risk, in that order, and say which comments block.
- **One repository until a concrete reason splits it.** Atomic changes across app, API and shared code are worth more to a small team than isolation. Access control and outside consumers are the reasons that count.
- **Version only what someone else chooses to upgrade.** A deployed web app is identified by its commit SHA. Semantic versions, changelogs per release and support windows are for libraries, SDKs and APIs with consumers.

## Route

| If the task is | Read |
|---|---|
| "I messed up my history", lost commits, a bad reset or rebase, undoing a pushed commit, a merge or rebase conflict, `.gitignore` or line-ending problems, finding when and why a line changed, cleaning up commits before pushing, working on two branches at once, a repository bloated by large files | `references/git-model.md` |
| Choosing a branching model, squash versus merge versus rebase, commit message rules or Conventional Commits, keeping a long feature or a stack of branches mergeable, release branches and backports, signed commits | `references/branching-workflow.md` |
| Writing a pull request description, self-reviewing before merge, splitting a big change, how to review or word feedback, review rules and turnaround, CODEOWNERS, a pull request template, what automated checks can replace | `references/pull-requests-review.md` |
| Monorepo or separate repositories, pnpm workspaces, Turborepo and remote caching, shared internal packages, running CI only for what changed, publishing packages from a monorepo, merging or splitting repositories with history | `references/monorepos.md` |
| Tagging releases, knowing which commit is deployed, semantic versioning, writing a changelog or release notes, automating version bumps, announcing a breaking change, a supported-versions policy | `references/versioning-releases.md` |

## Defaults at a glance

Follow what the repository already does (merge method, message format, release tooling) before applying any of these.

| Decision | Default | Flips when |
|---|---|---|
| Branch model | Trunk-based: `main` plus branches living under two days | Software shipped in parallel supported versions needs release branches |
| Working solo | Prototype: commits straight to `main` are fine. Launch onward: branch and pull request for every change, self-merged on green checks | — |
| Integration method | Squash merge only, pull request title and description as the commit, branches auto-deleted, linear history | Curated commits worth keeping: merge commits, read with `--first-parent` |
| Updating a branch | Rebase on `origin/main` when the branch is private; merge `main` in when it is shared or under review | — |
| Force push | `--force-with-lease`, personal branches only | Never on `main` or release branches |
| Undoing on shared branches | `git revert` | Reset is for unpushed commits only |
| Commit messages | Imperative subject near 50 characters, body explains why | Conventional Commits format on pull request titles once a release tool reads them |
| Pull request size | One purpose, under about 400 changed lines excluding generated files | Mechanical changes may be larger if isolated and labeled |
| Approvals | Solo: self-merge after checks. Team: one approval, author merges, stale approvals dismissed | Two approvals for auth, billing, destructive migrations, infrastructure |
| CODEOWNERS | Skip until three or more people or a specialist-risk path | — |
| Repository layout | One repository; workspaces only when a second app or a second consumer of shared code exists | Per-part access control, an open-source part, or an unrelated toolchain |
| Monorepo tooling | pnpm workspaces, `workspace:*`, internal packages consumed as TypeScript source; Turborepo with remote cache when CI time hurts | Keep Nx or another runner if the project has it |
| App versioning | No semver; commit SHA injected at build and exposed in health endpoint, logs and error tracker | Mobile, desktop or self-hosted editions need version and build numbers |
| Package versioning | Semantic versioning, annotated immutable tags, Changesets in a monorepo, a release pull request a person merges | Fully automatic releases for mature libraries with strong tests |
| Signed commits | SSH signing enabled locally; not enforced | Enforce by branch rule with several committers or a compliance requirement |
| Git configuration | `pull.rebase true`, `rebase.autoStash true`, `fetch.prune true`, `merge.conflictStyle zdiff3`, `rerere.enabled true` | — |

Stage notes: at Prototype skip commit linting, CODEOWNERS, release automation and changelogs. At Launch, protect `main`, require checks, use pull requests, tie every deploy to a commit, and start a user-facing changelog. At Scale, add code owners, a merge queue where the host plan offers one, import-boundary enforcement and affected-only CI.

## Before you call it done

1. Before any destructive command (`reset --hard`, `clean`, `restore`, force push, history rewrite), `git status` was read and anything uncommitted was committed or deliberately discarded; a backup branch exists when the state was unclear.
2. No rewritten history was pushed to `main`, a release branch or a branch someone else has pulled; force pushes used `--force-with-lease`.
3. After a conflict resolution: `git diff --cached --check` was clean before the resolution was committed (plain `git diff --check` sees nothing once files are staged), lockfiles and generated files were regenerated rather than hand-merged, and typecheck and tests pass.
4. `git status` shows no stray files before committing: no `.env`, secrets, build output, large binaries or unintended lockfile changes; `.gitignore` covers what should never be tracked.
5. Each commit, or the squashed pull request, has one purpose; mechanical changes (formatting, renames, dependency bumps) are separate from behavioral ones.
6. The pull request title states the change in the repository's convention, and the description covers what, why, how to test, and risk and rollout.
7. The full diff was read in the host's pull request view; debug code, commented-out code and unrelated hunks are gone.
8. The branch is up to date with `main`, required checks are green, and the preview or local run was actually exercised.
9. Review comments carry a severity (blocking or not) and a reason; every received comment was answered or resolved.
10. Changes touching auth, money, data deletion or irreversible migrations were flagged as such and got human attention, whatever automated review said.
11. In a workspace: dependencies are declared in the package that imports them, imports go through the package's `exports`, no package depends on an app, and a clean install with the frozen lockfile succeeds.
12. Task-runner configuration changes were verified: second run is a full cache hit, outputs exist after a cache restore, and environment variables that affect output are declared.
13. The running application reports its commit SHA, and the error tracker release matches it.
14. For a published package: the bump matches the change (breaking changes are a major, with a migration note), the tag is annotated and was not moved, and the changelog entry describes the effect on the consumer.

## Not this skill

- Finding bugs in the current diff → `code-review`
- CI checks, branch protection in the pipeline and deploys → `0x:ci-cd-release`
- Removing a leaked secret from history and rotating it → `0x:web-security`
- Git worktrees and review habits for AI coding agents → `0x:ai-coding-agents`
- API versioning and deprecation policy → `0x:api-design`
- README, architecture and developer documentation → `0x:code-quality`
