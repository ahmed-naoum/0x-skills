# The git model and recovery

Read this when: a git command did something unexpected, history needs fixing or work looks lost, a merge or rebase stopped on conflicts, or the question is when and why a line of code changed.

## Predict before running

Four places hold state. Every command is a move between them; name which ones a command touches before running it.

| Place | What it is | Lost when |
|---|---|---|
| Commits (object store) | Immutable snapshots, addressed by hash, each pointing at its parents | Unreachable from any ref or reflog and then garbage-collected |
| Refs | Names pointing at a commit: branches, tags, `HEAD`, `origin/*` | Moved or deleted; the reflog remembers local moves |
| Index (staging area) | The next commit's snapshot | Overwritten by `reset`, `checkout`, `restore --staged` |
| Working tree | Files on disk | Overwritten by `reset --hard`, `restore`, `checkout -- path`, `clean` |

"Changing a commit" never happens. Amend, rebase and cherry-pick write new commits and move a ref; the old commits stay in the object store until garbage collection. That is why almost anything committed can be recovered, and why rewritten commits get new hashes that break everyone who had the old ones.

| Command | Moves branch ref | Index | Working tree | Notes |
|---|---|---|---|---|
| `git reset --soft X` | to X | kept | kept | Old commits' changes end up staged |
| `git reset X` (mixed) | to X | reset to X | kept | Changes become unstaged edits |
| `git reset --hard X` | to X | reset to X | reset to X | Destroys uncommitted tracked changes |
| `git switch B` | no (moves `HEAD`) | to B | to B | Refuses if it would overwrite local edits |
| `git restore f` | no | kept | from index | Destroys the unstaged edit to `f`; no reflog |
| `git restore --staged f` | no | from `HEAD` | kept | Unstage only |
| `git commit --amend` | to a new commit | — | — | Replaces the tip; old tip is in the reflog |
| `git revert X` | forward one commit | — | — | New commit that undoes X; safe on shared branches |
| `git rebase X` | to rewritten commits | — | — | Replays the branch's commits on X, new hashes |
| `git merge X` | forward (fast-forward or merge commit) | — | — | Does not rewrite anything |
| `git cherry-pick X` | forward one commit | — | — | Copy of X's diff with a new hash |
| `git clean -fd` | no | no | deletes untracked files | Not recoverable; run `git clean -nd` first |

Rules that follow from the model:

- `git pull` is `fetch` plus `merge` (or `rebase` with `pull.rebase true`). When unsure, `git fetch` and inspect `git log --oneline --graph HEAD origin/main` before integrating.
- `origin/main` is a local snapshot of the remote from the last fetch, not the remote. Compare against it only after fetching.
- A detached `HEAD` is a commit checked out with no branch. Commits made there are reachable only through the reflog; `git switch -c name` before leaving.
- Rewriting (amend, rebase, reset) is free on commits that exist only locally. On pushed commits it requires a force push, which is acceptable on a personal feature branch and not on `main` or any branch someone else has pulled.
- Force push with `git push --force-with-lease`, never bare `--force`: the lease refuses the push if the remote moved since the last fetch, so someone else's commits are not silently discarded. Background fetches (editors, tools) can defeat the lease by updating the snapshot; adding `--force-if-includes` closes that gap.

## Recovery

First move in any "I lost it" situation: stop running commands, then look at `git status`, `git log --oneline --graph -15` and `git reflog -20`. If the state is confusing, pin the current position with `git branch backup-before-fix` so every later step is itself reversible.

| Situation | Fix |
|---|---|
| Bad `reset --hard`, bad rebase, amended over a commit | `git reflog`, find the entry before the mistake, `git reset --hard HEAD@{n}` (or `git branch rescue <hash>`) |
| Just finished a rebase or merge and want it undone | `git reset --hard ORIG_HEAD` (valid until the next command that sets it) |
| Deleted a branch | `git reflog` (the `HEAD` reflog still has its commits), then `git branch name <hash>` |
| Committed to the wrong branch, not pushed | `git switch right-branch && git cherry-pick <hash>`, then on the wrong branch `git reset --hard HEAD~1` |
| Committed on `main` instead of a feature branch | `git branch feature` then `git reset --hard origin/main` (the commits stay on `feature`) |
| Bad commit already on shared `main` | `git revert <hash>` and push; do not reset a shared branch |
| Bad merge commit on `main` | `git revert -m 1 <merge-hash>`; to bring the branch back later, revert the revert first, otherwise git considers those changes already merged |
| Dropped or cleared a stash | `git fsck --no-reflogs --unreachable` and look for commit objects; inspect with `git show <hash>`, restore with `git stash apply <hash>` |
| Staged a file (`git add`) then overwrote it, never committed | `git fsck --lost-found` lists dangling blobs; `git show <blob>` to read them |
| Mid-operation and lost | `git merge --abort`, `git rebase --abort`, `git cherry-pick --abort` return to the pre-operation state |
| Pushed a force push over a teammate's work | The teammate's clone or their reflog still has it; the host's activity view for the branch often shows the previous tip as well |

What git cannot recover: edits that were never staged or committed (`restore`, `reset --hard`, `clean` on those are final). Check the editor's local history before giving up. The practical defense is to commit early and often on a branch; a WIP commit is free and can be squashed later.

Reflog facts: it is local to one clone, never pushed, and entries expire (by default after about 90 days, about 30 days for commits no longer reachable from a ref). A fresh clone has no history of the old one's mistakes.

`reset` versus `revert`: reset moves a ref backward and suits unshared history; revert adds a commit and suits shared history. A leaked secret is a different problem: removing the commit does not un-leak it. Rotate first; see `0x:web-security`.

## Conflicts

Set these once; they make every conflict easier:

```bash
git config --global merge.conflictStyle zdiff3   # shows the common ancestor between the two sides
git config --global rerere.enabled true          # remembers resolutions and replays them
```

Procedure:

1. `git status` lists the unmerged paths. Know which operation is in progress, because "ours" and "theirs" swap. In a merge, ours is the branch being merged into. In a rebase, ours is the branch being rebased onto (usually `main`) and theirs is the commit of the feature branch being replayed.
2. For each file, read all three versions: base, ours, theirs. The question is what each side intended to change relative to the base, then apply both intentions. Picking one side wholesale is right only when the other side's change is truly obsolete.
3. To see what led to the conflict: `git log --merge -p -- path` (merge only) shows the commits from both sides touching the file.
4. Take a whole side when that is correct: `git checkout --theirs path` or `--ours path`. To start a file over: `git checkout --merge path` restores the conflict markers.
5. `git add` each resolved file. Finish with `git merge --continue` or `git rebase --continue`. During a rebase do not run `git commit` for the resolution; `--continue` commits it.
6. Verify before pushing: `git diff --check` (leftover markers and whitespace errors), then typecheck and run the tests. Git reports textual conflicts only; two changes that merge cleanly can still break each other (a renamed function on one side, a new caller on the other).

Special cases:

- Lockfiles (`pnpm-lock.yaml`, `package-lock.json`): never hand-edit. Resolve `package.json` first, take either side of the lockfile, then run the package manager's install to regenerate it and commit the result.
- Generated files (snapshots, built schema, migration metadata): take one side and regenerate with the tool.
- Database migrations: two branches each adding a migration is a semantic conflict even when the files do not collide. Re-order or re-number so the branch landing second comes after what is on `main`; see `0x:postgres-database`.
- Rebasing a long branch hits the same conflict once per commit. Either squash the branch first (`git reset --soft $(git merge-base main HEAD) && git commit`) and rebase one commit, or merge `main` into the branch instead and resolve once.
- Delete-versus-modify: decide whether the modification must move to wherever the code went. Check with `git log --diff-filter=D --follow -- path` and by searching for the moved code.

## .gitignore and .gitattributes

`.gitignore` rules that cause real trouble:

- Ignoring does nothing to a file already tracked. Stop tracking with `git rm --cached path` (keeps the file on disk), then commit.
- A file cannot be re-included with `!` if its parent directory is excluded. Ignore the contents instead: `dir/*` followed by `!dir/keep.txt`.
- A leading `/` anchors to the directory of the `.gitignore`; without a slash the pattern matches at any depth. `build` ignores every `build` directory in the tree, which breaks a source folder with that name.
- Debug with `git check-ignore -v path`: it prints the file, line and pattern responsible.
- Project-wide rules go in the committed `.gitignore`. Personal editor and OS files (`.DS_Store`, `.idea/`) belong in the global excludes file (`core.excludesFile`) or `.git/info/exclude`, so the project file stays about the project.

Commit: lockfiles, `.env.example`, migrations, editor settings the team shares. Ignore: `node_modules/`, build output (`.next/`, `dist/`, `coverage/`), `.env` and `.env.*` with `!.env.example`, local databases, logs, and OS files. Before the first commit of a new project, run `git status` and read the list; a secret or a 200 MB folder committed once is in history permanently.

`.gitattributes` baseline for a web project:

```gitattributes
* text=auto eol=lf
*.png binary
*.jpg binary
*.woff2 binary
pnpm-lock.yaml -diff linguist-generated=true
```

- `text=auto eol=lf` normalizes line endings in the repository and on checkout, which ends whole-file diffs between Windows and other machines. After adding it to an existing repository, run `git add --renormalize .` and commit that alone.
- `-diff` keeps lockfile noise out of `git diff` and `git log -p`; `linguist-generated` collapses the file in GitHub diffs.
- `export-ignore` keeps paths out of `git archive` output.
- Attributes are also where LFS tracking lives (below), so review changes to this file like code.

## Reading history

The goal is the reason for the code, which lives in the commit message and the pull request, not in the blame line.

| Question | Command |
|---|---|
| Who last touched these lines, ignoring whitespace and moves | `git blame -w -C -C -L 40,60 path` |
| When did this string appear or disappear | `git log -S'retryLimit' --oneline -- src/` |
| When did lines matching a pattern change at all | `git log -G'retryLimit\s*=' -p -- src/` |
| The full history of one function | `git log -L :functionName:path/file.ts` |
| History across renames | `git log --follow -p -- path` |
| When was a file deleted | `git log --diff-filter=D --oneline -- path` |
| What merged into main, one line per pull request | `git log --first-parent --oneline main` |
| Which commit introduced a bug | `git bisect start <bad> <good>` then `git bisect run <test command>` |
| Which pull request carried a commit | `gh pr list --state merged --search <hash>` |

- `-S` (pickaxe) finds commits where the number of occurrences of the string changed; `-G` finds commits whose diff lines match a regex. Use `-S` for "where was this introduced or removed", `-G` for "where was this edited".
- Blame usually lands on a formatting or refactoring commit first. Step past it with `git blame <hash>^ -- path`, or permanently by listing bulk-reformat commits in `.git-blame-ignore-revs` and setting `git config blame.ignoreRevsFile .git-blame-ignore-revs`. GitHub's blame view honors a file with that name at the repository root.
- `git bisect run` needs a command that exits 0 for good and non-zero for bad (125 means skip this commit). It finds the commit in about log2(n) steps, and it only works well when most commits build, which is one argument for small commits that each pass.
- End with `git bisect reset`.

## Cleaning local history before sharing

Rewrite only what has not been reviewed or pulled by anyone else. With squash merge as the integration policy (see `branching-workflow.md`), heavy cleanup of a branch is mostly wasted effort; clean up when individual commits will land on `main` or when a reviewer will read commit by commit.

```bash
git commit --fixup=<hash>            # mark a correction for an earlier commit
git rebase -i --autosquash main      # fold fixups in, reorder, reword, drop
git rebase -i --exec "pnpm typecheck" main   # prove every commit still builds
```

- `git config --global rebase.autoSquash true` makes `--autosquash` the default for interactive rebases.
- `git add -p` stages hunks, which is how one messy working tree becomes two coherent commits.
- To split a commit: mark it `edit` in the rebase, `git reset HEAD^`, commit the parts, `git rebase --continue`.
- After rewriting a pushed branch: `git push --force-with-lease`. If a reviewer has already read the branch, add commits instead and let the squash merge tidy up; force pushes can make "changes since last review" views less useful.
- `git rebase --update-refs` moves intermediate branch names along with the rebase, which keeps a stack of branches intact.

## Parallel work: stash, worktrees, sparse checkout

| Need | Use | Trap |
|---|---|---|
| Set changes aside for minutes | `git stash -u` (`-u` includes untracked files) | Stashes are unnamed, easy to forget and easy to pop onto the wrong branch. For anything longer than minutes, make a WIP commit on a branch |
| Stash no longer applies cleanly | `git stash branch tmp-branch` | A `pop` that conflicts leaves the stash in the list; drop it by hand after resolving |
| Two branches checked out at once (hotfix during a feature, long test run, review) | `git worktree add ../app-hotfix -b hotfix origin/main` | One branch can be checked out in only one worktree. Each worktree needs its own install and its own untracked files (`.env` is not copied). Two dev servers need different ports |
| Finished with a worktree | `git worktree remove ../app-hotfix`; `git worktree prune` after deleting a folder by hand | Deleting the folder alone leaves stale metadata that blocks reuse of the branch |
| Huge repository, need a few directories | `git clone --filter=blob:none --sparse <url>` then `git sparse-checkout set apps/web packages/ui` | Tools that scan the whole tree (search, codemods, root-level lint) see only the checked-out part |

Worktrees share one object store and one set of refs, so a commit made in one is immediately visible in the others, and they cost little disk beyond the checked-out files. Running several coding agents in separate worktrees is covered in `0x:ai-coding-agents`.

## Large files and LFS

Git stores every version of every file forever, and binaries do not delta-compress well. A repository that grows past a few hundred megabytes slows every clone and CI run. Hosts also reject single files over a hard size limit (GitHub's is 100 MB, with a warning well below that).

Decision rule: build output, dependencies, database dumps and user uploads never belong in git (object storage or a release artifact instead). Source binaries that change with the code (design files, large fixtures, video) go in LFS when they exceed roughly a megabyte and change over time. Small static images and fonts can stay in plain git.

```bash
git lfs install
git lfs track "*.psd"          # writes the rule to .gitattributes; commit that file
```

LFS traps: storage and bandwidth are metered by the host, so check the quota before adopting it; CI and the deploy host must fetch LFS objects or the build receives small text pointer files instead of the binaries; a file committed before the track rule stays a normal blob until migrated.

Removing a large file already in history is a history rewrite of the whole repository. Sequence:

1. Find the offenders:
   ```bash
   git rev-list --objects --all \
     | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
     | sort -k3 -n | tail -20
   ```
2. Merge or close open pull requests and tell every collaborator; all commit hashes after the first affected commit change.
3. Work in a fresh clone with `git filter-repo` (the maintained replacement for `filter-branch`): `git filter-repo --strip-blobs-bigger-than 10M`, or `git filter-repo --path path/to/file --invert-paths`. To move existing binaries into LFS instead, use `git lfs migrate import --include="*.psd" --everything`.
4. Force-push all branches and tags. `filter-repo` removes the `origin` remote on purpose; add it back first.
5. Everyone re-clones. An old clone that pushes again reintroduces the old objects.
6. The host may keep the old objects reachable through pull request refs and caches until it garbage-collects; forks keep their copies regardless.

If the file was only committed locally and not pushed, none of this is needed: drop it with an interactive rebase or amend.

## Ask the user

- **Has anyone else pulled this branch?** Decides between rewriting (reset, rebase, force push) and adding a revert. Assume yes for `main` and for any branch with an open reviewed pull request; assume no for a branch created in this session.
- **Is a history rewrite of the whole repository acceptable right now?** It invalidates every clone, open pull request and commit link. Default: no; prefer leaving a moderately large file in history and stopping the growth, and rewrite only when the repository is unusable or a host limit is hit.
- **Who pays for LFS storage and bandwidth, and does the deploy host support it?** Default when unknown: keep large assets in object storage and reference them by URL rather than adopting LFS.
- **When a conflict pits two intentional behaviors against each other, which one is the product supposed to have?** Code cannot answer this. Default: keep the behavior on `main` and re-apply the branch's intent on top, then flag the spot in the pull request.
