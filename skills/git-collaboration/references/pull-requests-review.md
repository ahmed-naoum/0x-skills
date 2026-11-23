# Pull requests and code-review practice

Read this when: writing a pull request description, splitting a change that is too big to review, reviewing someone's change or responding to review, or setting up review rules, CODEOWNERS and a pull request template.

Finding bugs in a specific diff is the job of the installed `code-review` skill. This file covers how changes are packaged, routed and discussed.

## Opening a pull request

Size is the lever. Review quality drops sharply with size: a reviewer reads a 150-line change and rubber-stamps a 1,500-line one. Rule of thumb: one purpose per pull request, under about 400 changed lines excluding lockfiles, generated code and snapshots, reviewable in one sitting of 30 minutes or less. Larger is acceptable only when the bulk is mechanical and the description says so.

One purpose means the title needs no "and". Refactor-then-change is two pull requests; a drive-by fix noticed along the way is its own small one.

Title: what the change does to the product or system, imperative, specific enough for a changelog line. Under squash merge it becomes the commit subject on `main`, and release tooling may read it (`branching-workflow.md`).

Description, in this order:

```markdown
## What
One or two sentences: the behavior after this change.

## Why
The problem, user report or decision behind it. Link the issue.

## How to test
Exact steps or commands, and what the reviewer should see.

## Risk and rollout
Migrations, flags, config or env changes, what to watch after deploy, how to roll back.

## Notes for the reviewer
Where to start reading, what is mechanical, what is deliberately out of scope.
```

- "Why" is the part that cannot be recovered from the diff later. A description that restates the diff ("changed X to Y in file Z") fails the reader who arrives through `git blame` in a year.
- "How to test" must be runnable by someone without the author's context. For UI changes include before and after screenshots or a short recording, and the preview deploy link.
- State risk explicitly even when it is "none: pure refactor, covered by existing tests". A pull request that touches auth, billing, data deletion, migrations or permissions says so in the first lines.
- Call out anything the reviewer would otherwise have to discover: a new dependency (and why this one), a new environment variable, a changed public API, a deleted feature.
- Open as a draft while CI is red or the work is incomplete; request review only when it is ready to merge as far as the author knows.

```bash
gh pr create --draft --title "Retry webhook delivery on 5xx" --body-file pr.md
gh pr ready
gh pr merge --squash --auto --delete-branch   # merges itself once required checks pass
```

`--auto` needs auto-merge allowed in the repository settings, and it waits only for requirements the branch rules define. With no required checks on `main` there is nothing to wait for, and the pull request can merge while CI is still running. Set the required checks first (`0x:ci-cd-release`).

## Self-review, also when solo

Read the full diff in the host's pull request view before asking anyone, human or automated. The different rendering from the editor is the point: it is the first time the change is seen as a reader sees it.

Check:

- Every hunk belongs to this purpose. Remove stray formatting, renamed variables elsewhere, commented-out code, debug logging, `console.log`, `.only` on tests, TODOs without an issue.
- No secrets, tokens, internal URLs, customer data in fixtures, or `.env` files.
- Files that should not be there: build output, editor config, large binaries, an unintended lockfile change.
- The diff contains tests for the new behavior, or the description says why not.
- Error paths and empty states, not only the happy path.
- Migrations are reversible or the rollback path is described; they are safe to run while the old code is still serving (`0x:postgres-database`).
- CI is green, and the preview deploy was actually opened and exercised.
- Leave comments on your own pull request where the code has a non-obvious reason. If the explanation matters long-term, move it into a code comment or the commit message instead.

Working solo, the pull request still earns its place from Launch on: it is where CI gates the merge, where a preview environment appears, where an automated review runs, and it leaves one revertable commit with a written reason.

The substitute for a second human is time and a checklist: for risky changes (money, auth, data deletion, migrations), leave the pull request overnight and re-read it cold before merging. For code written by an agent, the person who asked for it is accountable as its reviewer; see `0x:ai-coding-agents`.

## Reviewing: the order of attention

Read the description first, then decide whether the approach is right before reading lines. A reviewer who starts with naming comments has spent the author's patience before reaching the design flaw.

| Order | Question | Typical findings |
|---|---|---|
| 1. Intent | Does this change solve the stated problem, and is the problem the right one? | Solves a different problem; scope creep; should be split |
| 2. Correctness | Does it do what it claims in every case? | Missing error handling, races, off-by-one, wrong null handling, unhandled states |
| 3. Design | Does it fit the codebase's structure? Will the next change here be easier or harder? | Wrong layer, duplicated logic, leaky abstraction, new pattern where one exists |
| 4. Risk | What happens on deploy, at load, under attack, on rollback? | Unsafe migration, missing authorization check, unbounded query, no flag, irreversible data change |
| 5. Tests | Would these tests fail if the code were wrong? | Tests that assert the mock, missing negative cases |
| 6. Readability | Can the next person understand it without the author? | Misleading names, missing reason for a workaround |
| 7. Style | — | Nothing: formatter and linter own this. If a style point is not automatable, add it to the written conventions once instead of repeating it in reviews |

Practice:

- Review the whole change, including what is absent: the caller that was not updated, the missing migration, the missing test. Check out the branch (`gh pr checkout 123`) and run it when the change is risky or visual.
- Verify claims instead of trusting them. "Covered by existing tests" is checked by finding the test.
- Time-box. If understanding the change takes more than about an hour, the finding is "too large or under-explained; please split or add context", and that is legitimate feedback.
- Decide the verdict explicitly: approve, approve with non-blocking comments, or request changes. "Comment" without a verdict leaves the author guessing.
- Approve when the change improves the codebase and has no known defect, even if it is not how the reviewer would have written it. Holding approval for preference turns review into a queue.

## Giving and receiving feedback

Each comment carries a severity label so the author knows what must change before merge:

| Label | Meaning | Blocks merge |
|---|---|---|
| `blocking:` | Defect, security or data risk, violates an agreed convention | Yes |
| `question:` | Reviewer does not understand; the answer may become a code comment | Until answered |
| `suggestion:` | A better way exists; author decides | No |
| `nit:` | Trivial preference | No |
| `praise:` | Something done well, stated specifically | No |

- Be specific and give the reason: what is wrong, why it matters, what would fix it. "This is confusing" is not actionable; "this returns early when `items` is empty, so the audit log entry on line 88 is skipped; move the log above the guard" is.
- Comment on the code, not the person: "this function" not "you". Ask before asserting when unsure: the author may know something.
- Offer the fix when it is short. GitHub suggestion blocks let the author apply it in one click:

  ````markdown
  ```suggestion
  if (items.length === 0) return [];
  ```
  ````

- Batch comments into one review submission rather than a trickle of notifications, and lead the summary with the blocking items.
- Two rounds of back-and-forth on the same thread means text is failing: talk, then record the decision in the thread.
- Do not expand scope in review. Pre-existing problems near the diff become an issue or a follow-up, unless the change makes them worse.

Receiving: answer every comment (fixed, with the commit; or declined, with the reason). Push fixes as new commits during review so the reviewer can see what changed since last time; the squash merge cleans up. The author resolves threads for nits and suggestions; the reviewer resolves blocking threads. Disagreement on a blocking item is settled by the code owner of that area, not by attrition.

## Splitting a large change

Split along lines where each piece is correct and deployable alone. Common sequence for a feature:

1. Preparatory refactor with no behavior change (move, rename, extract). Reviewable by skimming because tests do not change.
2. Schema change, additive only (new nullable column, new table), deployed before any code depends on it.
3. Backend behavior behind a flag or an unreferenced endpoint, with tests.
4. UI, still behind the flag.
5. Flag on, then a cleanup pull request removing the flag and the old path.
6. Destructive schema cleanup (drop the old column) last, after the old code is gone from production.

Other seams: by layer (data access, service, route, UI), by entity when the same pattern is applied to many (do one as the reviewed exemplar, then the rest mechanically), and always mechanical apart from semantic (a codemod, a formatter run or a dependency upgrade alone).

Techniques when the work already exists as one big branch:

```bash
git fetch && git switch big-branch && git rebase origin/main   # or merge: it must contain current main
git switch -c part-1 origin/main
git checkout big-branch -- src/lib/billing/       # take whole paths from the big branch
git commit -m "Extract invoice calculation"
# or rebuild commits from the full diff:
git switch -c rebuild big-branch
git reset origin/main          # all changes become unstaged edits; new files become untracked
git add -N .                   # register new files so add -p offers them
git add -p                     # stage one coherent piece at a time, commit, repeat
```

Both recipes take the big branch's content relative to `origin/main`. If the big branch is behind `main`, they silently carry reverts of everything `main` gained since, which is why the first line comes first. `git checkout <branch> -- path` also leaves in place files the big branch deleted; remove those by hand. The original branch stays untouched as the reference: when the last part is done, `git diff big-branch` on the final part should be empty.

Each part must build and pass on its own; run the checks per part, not only at the end. If parts depend on each other, stack them (`branching-workflow.md`) and say in each description where it sits: "2 of 4, depends on #231". A part that cannot be made independently correct is a sign the seam is wrong.

## Written review conventions

Write these down once in `CONTRIBUTING.md` or the repository docs, at Launch when a second person joins. Unwritten conventions are relitigated in every review.

| Topic | Reasonable default |
|---|---|
| Turnaround | First response within one working day; reviews come before starting new work |
| Approvals | One approval to merge into `main`; two for changes to auth, billing, migrations that drop data, and infrastructure |
| Who merges | The author, after approval and green checks |
| New commits after approval | Dismiss stale approvals on protected branches, so the approved code is the merged code |
| Size | Soft limit of about 400 changed lines; larger needs a reason in the description |
| Severity labels | The table above |
| Emergency path | A production fix may merge with review after the fact, within one working day, recorded in the pull request |
| Solo self-merge | Allowed when checks pass; risky categories get the cold re-read. Do not turn on required approvals while solo: hosts do not count an author's approval of their own pull request, so the rule locks out the only committer or teaches them to bypass it |
| Ownership | Once CODEOWNERS exists, every path has an owner; the owner settles disputes for that path |

Review latency is the number to watch. Slow reviews cause large pull requests (people batch to avoid the wait), which cause slower reviews.

## CODEOWNERS and templates

CODEOWNERS routes review requests automatically and, combined with the branch rule "require review from code owners", makes that review mandatory.

```text
# .github/CODEOWNERS
*                         @acme/engineering
/apps/web/src/billing/    @acme/payments
/packages/db/migrations/  @acme/backend
*.tf                      @acme/platform
/.github/                 @acme/platform
```

- The last matching pattern wins, not the most specific and not the union. Put the catch-all first and specific paths after it.
- GitHub reads the file from `.github/`, the repository root or `docs/`, on the base branch of the pull request.
- Owners must have write access to the repository; an owner without it is ignored. An invalid line is skipped rather than failing loudly, so check the file after editing (GitHub flags errors when viewing it).
- Prefer teams to individuals: a person on vacation otherwise blocks merges. With a team as owner, any one member's approval satisfies the rule. Teams exist only in organizations (a personal-account repository lists usernames), and the team must be visible and be granted write access itself, not only through its members.
- Own the CODEOWNERS file and the CI configuration themselves (`/.github/`), or anyone can remove their own review requirement.
- Without the branch rule, CODEOWNERS only requests review. Enforcement lives in branch protection or rulesets (`0x:ci-cd-release`). On GitHub those rules, and with them required code-owner review, are a paid-plan feature for private repositories; check the plan before designing a process that depends on them.
- Skip CODEOWNERS until there are at least three people or a path with real specialist risk. For two people it adds nothing over "the other person reviews".

Pull request template: `.github/pull_request_template.md`, containing the description headings above and at most three or four checkboxes that are true decisions (migration safe to run before deploy; flagged or safe to release; docs or changelog updated). A twenty-item checklist gets ticked without reading. Anything a machine can verify belongs in CI, not in the template.

## What needs a human and what does not

Spend human attention where judgment is required; automate everything that has a mechanical answer, and make the automated checks required so no one needs to ask.

| Concern | Owner |
|---|---|
| Formatting, import order, lint rules, type errors | Formatter, linter, typechecker in CI (`0x:code-quality`) |
| Tests pass, coverage of changed lines, build succeeds | CI (`0x:ci-cd-release`) |
| Known vulnerable dependencies, committed secrets, license problems | Scanners in CI (`0x:web-security`) |
| Bundle size, performance budgets, accessibility smoke checks | CI budgets |
| Pull request title format, size warnings, missing description | A lightweight check or bot |
| Likely bugs, missed edge cases, inconsistent patterns | Automated AI review as a first pass on every pull request; findings are advisory and the author triages them |
| Is this the right problem and the right approach | Human |
| Authorization and tenant-isolation logic, money movement, data deletion, irreversible migrations | Human, always, even when automated review is clean |
| New dependencies, new external services, new data collected about users | Human: these are cost, supply-chain and privacy decisions |
| Public API or schema shape that will be hard to change | Human |

Low-risk classes that can merge without human review once checks pass, if the team agrees in writing: dependency patch updates with passing tests, copy and documentation changes, generated code. Review the policy when one of these causes an incident.

## Ask the user

- **Who must approve before merging to `main`, and may the author merge their own change?** A risk decision about how much friction is acceptable. Default: solo, self-merge after green checks; team, one approval, author merges.
- **Which areas require a named owner's review?** Default: authentication and authorization, billing, migrations, infrastructure and CI configuration.
- **What review turnaround will the team commit to?** It sets how small pull requests need to be to keep flowing. Default: first response within one working day.
- **Which change classes may merge on automated checks alone?** Default: dependency patch updates and documentation; nothing touching auth, money or data deletion.
- **Is there a production-emergency path that skips review?** Default: yes, with review after the fact within one working day and a note in the pull request.
