# Refactoring and rewrites

Read this when: improving the structure of existing code, changing code nobody understands,
removing dead code, making a mechanical change across many files, upgrading a framework or
language major version, or deciding between refactoring, rewriting and leaving a system alone.

## When to refactor at all

Refactoring is a change in structure with no change in observable behavior. It is not a
project; it is paid for by the next change it makes cheaper.

| Situation | Decision |
|---|---|
| The code is about to be changed and its shape makes the change hard | Refactor first, then make the change ("make the change easy, then make the easy change") |
| The code was just touched and a small cleanup is obvious | Do it, in its own commit |
| The code is ugly but stable, rarely read, rarely changed | Leave it. Ugliness that nobody visits costs nothing |
| No tests and the behavior is not understood | Characterize first (below); do not restructure blind |
| Prototype stage, code likely to be deleted | Do not refactor; finish learning what the product is |
| Deadline today, S1 open | Fix, note the debt, refactor after |

Allocate by churn times pain: files changed most often in `git log` that are also hard to
change are where refactoring pays. A rule of thumb: tolerate duplication until the third
occurrence, because the first two rarely show the right abstraction. Planning debt work as a
portfolio is in `0x:engineering-leadership`.

## Small behavior-preserving steps

The method that keeps refactoring safe is step size. Each step is small enough that if tests
go red, the cause is the last edit and the remedy is undo, not debugging.

1. Start green: type check and the relevant tests pass, and the working tree is clean.
2. Confirm the tests cover the code being moved (run with coverage on that file, or break the
   code on purpose and see a test fail). If not, add characterization tests first.
3. Make one named transformation: rename, extract function, inline, move, change signature,
   replace conditional with a table, introduce a parameter object.
4. Run type check and the nearby tests. Seconds, not minutes; use watch mode.
5. Commit. Repeat.

Rules:

- Use the editor's or language server's automated rename, move and extract. They update every
  reference and are safer than hand edits; prefer them even when slower to invoke.
- If red for more than a few minutes, revert to the last green commit and take a smaller step.
  Debugging a broken refactor is a sign the step was too big.
- Do not change tests and code in the same step unless the test was bound to implementation
  detail; a test that must change during a refactor is no longer checking that behavior was
  preserved. Fix such tests first, in a separate commit, to assert on outputs.
- For a signature or module change with many callers, use parallel change: add the new form
  beside the old, migrate callers in batches, delete the old. Every intermediate commit ships.
- Types are the fastest safety net: change the type first and let the compiler list every
  place that needs to follow.
- Keep the branch short-lived. A refactoring branch open for a week conflicts with everything;
  merge behavior-preserving steps to main daily.

## Separate refactoring from behavior change

A commit or pull request is either structural (behavior identical) or behavioral (structure
minimal), not both.

- Review: a structural diff can be skimmed for "nothing changed"; a behavioral diff is small
  enough to read fully. Mixed, a one-line behavior change hides inside 400 moved lines.
- Bisect and revert: a regression lands on a small behavioral commit, and it can be reverted
  without losing the cleanup.
- When a needed cleanup is discovered mid-feature: stash the feature work, do the refactor on
  green, commit, then reapply. If already entangled, split with `git add -p`.
- Label structural commits (`refactor:` prefix or similar) and state in the message that
  behavior is unchanged and how that was verified.
- Purely mechanical mass edits (formatting, renames, codemod output) go in their own commit,
  with nothing hand-edited in it, and can be listed in `.git-blame-ignore-revs` so blame skips
  them (GitHub reads the file by itself; local git needs `blame.ignoreRevsFile` set). Commit
  and pull-request conventions are in `0x:git-collaboration`.

## Delete dead code now

Unreachable code is not free: it is read, searched, type-checked, migrated in every upgrade,
flagged by scanners, and believed. Version control is the archive; a deleted function is one
`git log -S` away.

Delete in the same change that makes it unreachable:

- The old branch when a feature flag reaches 100% and has been stable for an agreed period
  (put the removal date in the flag's description when creating it).
- The old implementation when the last caller moves to the new one.
- Commented-out code, always. It rots immediately and nobody dares remove it later.
- Unused exports, files, dependencies, environment variables, routes, database columns (the
  column drop goes through the migration sequence in `0x:postgres-database`), and the tests
  and docs of the deleted thing.

Before deleting, prove it is dead at the right boundary: the compiler and an unused-export
tool cover in-repo references (tooling in static-analysis-types.md); for HTTP routes, jobs,
webhooks and public API fields, check access logs or add a counter and wait one full business
cycle (a month covers monthly jobs and billing runs; annual renewals, year-end jobs and old
mobile app versions need a check of schedules and client versions, not a wait). Dynamic
references (string-built imports, reflection, names stored in the database or a queue)
defeat static tools; search for the string.

A "cleanup sprint" is the wrong tool: by then nobody remembers what is safe to remove, and it
competes with features for time. If a deletion is large and risky, stage it: stop calling,
log-and-wait, then delete. Code comes back from git; data does not. Dropping a column or
table comes last, after a verified backup or export, and only once nothing reads or writes it.

## Characterization tests for legacy code

Legacy here means code without tests whose exact behavior is not known. Before changing it,
pin what it does today, bugs included, so that the refactor can be shown to preserve it.

1. Find a seam: the nearest public entry point where inputs can be supplied and outputs
   observed (a function, a route, a job handler, a CLI). Prefer the outermost seam; it leaves
   the most freedom to restructure inside.
2. Collect realistic inputs: from logs, production-shaped data, existing callers, edge cases.
3. Run the code and record the outputs as the expected values (snapshot or golden files are
   appropriate here, unlike in normal tests). Do not write what it should do; write what it
   does.
4. Make it deterministic first: freeze the clock, seed randomness, fake the network boundary,
   sort unordered output.
5. Check sensitivity: change the code on purpose and confirm the tests fail. Use coverage to
   find branches no input reaches and add inputs for them.
6. Refactor under these tests. Replace them with intention-revealing tests as understanding
   grows; delete the goldens when the module is understood.

When an observed behavior looks like a bug, keep it in the characterization, flag it, and fix
it afterwards as a separate behavioral change: callers or stored data may depend on it.

If the code has no usable seam (logic inside a framework callback, a global, a database
trigger), make the smallest possible untested change to create one: extract a function and
pass dependencies as parameters, using automated refactoring only. For risky replacements,
run old and new in parallel on real inputs and log differences before switching.

## Smells worth fixing

Most smell catalogs list everything; these three account for most of the cost of change.

| Smell | How to recognize it | Fix | Do not over-apply |
|---|---|---|---|
| Duplicated knowledge | One business rule (a price, a limit, a permission, a status transition, a validation) encoded in two places that must change together; a bug fixed in one place and not the other | One owner for the rule: a function, a schema, a constant, a database constraint. Derive the rest | Code that looks alike but changes for different reasons is not duplication. Merging it couples unrelated things; the wrong abstraction costs more than the copy |
| Long function | Mixed levels of abstraction; comments marking sections; many local variables; nesting more than about three deep; needs scrolling to hold in mind | Extract the sections the comments name, pull the pure decision out of the I/O (see test-strategy.md), replace nested conditionals with early returns or a lookup table | A long linear function that reads top to bottom is fine. Do not shred it into one-line helpers that must be read in five files |
| Wide interface | A function with many parameters or boolean flags; a module exporting most of its internals; a component with dozens of props; an "options" object every caller fills differently; types with many optional fields | Narrow to what callers need, split by use case, replace boolean flags with separate functions, make invalid combinations unrepresentable (discriminated unions) | Do not design for callers that do not exist |

Secondary signals: shotgun surgery (one change touches many files, meaning a concept is
scattered), feature envy (a function that mostly manipulates another module's data, so it
belongs there), primitive obsession (IDs, money and emails as bare strings and numbers; give
them branded or wrapper types), and speculative generality (hooks, parameters and layers for
needs that never came; delete them).

## Codemods for mechanical changes

When the same edit is needed in more than about 20 places, script it. A codemod is
repeatable (rerun after rebasing), reviewable (review the script, sample the output) and
consistent.

| Tool | Use when |
|---|---|
| Editor or language-server rename and move | A symbol or file rename; always try this first |
| The framework's or library's official codemod | A version migration; maintainers encoded the edge cases |
| ast-grep | Structural search and replace by pattern; quick to write, many languages |
| jscodeshift | JavaScript and TypeScript transforms needing logic over the syntax tree |
| ts-morph | Transforms that need type information (only change calls where the argument is of type X) |
| Regex search and replace | Only for text that is unambiguous as text (an import path, a string constant) |
| A coding agent applying a written rule file by file | Changes needing judgment per site; give it the rule, a few worked examples, and run the checks after each batch |

Procedure:

1. Start from a clean tree, so the diff is only the codemod.
2. Write the transform against two or three representative files, including an awkward one.
3. Dry-run and read a sample of the diff. Count matched sites and compare with a plain text
   search for the old pattern: the difference is what the transform missed.
4. Run on everything, run the formatter, then type check and tests.
5. Commit the mechanical output alone, naming the command in the message. Hand fixes for the
   cases the script could not handle go in a following commit.
6. Add a lint rule banning the old pattern, so it does not come back.

For a large codebase, land it directory by directory if every intermediate state builds;
otherwise in one commit at a quiet time, since a long-lived branch will conflict with all
other work.

## Upgrading a language or framework major version

The failure mode is a branch that upgrades everything, breaks in forty ways at once and is
never merged. Sequence that avoids it:

1. Read the official migration guide and the changelog of breaking changes fully before
   touching anything. List the ones that apply.
2. On the current major, move to its latest minor and patch release, and clear every
   deprecation warning there. Most breaking changes are announced as deprecations first, and
   these fixes ship to production on the old version, one at a time.
3. Check that the dependencies around it (plugins, adapters, type packages, the runtime
   version) have releases supporting the target. An unmaintained plugin is the usual blocker;
   replace it before the upgrade, not during.
4. One major at a time, one core dependency at a time. Do not skip majors and do not combine
   a framework upgrade with a runtime or bundler upgrade.
5. Run the official codemods, commit their output alone, then fix what remains.
6. Adopt new features later. An upgrade changes versions; it does not also migrate to the new
   recommended patterns. Old and new patterns usually coexist for at least one major.
7. Verify beyond the unit suite: production build, end-to-end critical journeys, bundle size
   and startup, then a preview or canary deploy with error rates watched. Have the rollback
   ready; a lockfile revert is a clean one if nothing else rode along.

For runtimes (Node): upgrade from one LTS line to the next, and keep the version pinned in
one place that CI, the host and local tooling all read (`.nvmrc` or `engines` plus the
platform setting), or environments drift apart.

Cadence at Launch stage and later: patch and minor updates continuously through an automated
update bot with CI as the gate; majors on a schedule, soon after the ecosystem has caught up
and well before the old version leaves support. Skipping two majors turns a day into weeks.
Dependency risk and update automation are in `0x:web-security`.

## Rewrite, refactor or leave alone

Default: refactor incrementally. A from-scratch rewrite discards the bug fixes and edge-case
handling that the old code accumulated, takes longer than estimated because the old system's
behavior is the spec and nobody wrote it down, and delivers no user value until the end while
the old system still needs maintenance.

| Evidence | Decision |
|---|---|
| Works, rarely changes, no pressure | Leave it alone, however old or inelegant |
| Painful to change but changeable; tests exist or can be added | Refactor in place, funded by the features that touch it |
| The foundation is the problem: unsupported platform or language, a data model that contradicts the product, a vendor going away | Replace incrementally with a strangler (below) |
| Small enough to rebuild in days and fully understood (a script, one service, a prototype) | Rewrite; the risk is bounded |
| Prototype that found product-market fit on throwaway code | Rewrite or replace in slices is legitimate, since it was built to learn. Keep the data model migration explicit |
| "It is ugly", "I did not write it", "the new framework is better" | Not reasons. These predict the same complaints about the rewrite in two years |

Questions that decide it: what specifically cannot be done today, and what does that cost per
month? Could that be fixed by replacing one part? Is there a full list of what the old system
does, including the behaviors nobody remembers? Can the rewrite ship in slices that each go
to production? If the last answer is no, the plan is a big-bang rewrite; do not start it.

## Strangler migration

Replace a system piece by piece behind a stable front, with both running, until the old one
has no traffic and is deleted.

1. **Put a facade in front.** A routing layer the team controls: reverse-proxy rules, a
   framework rewrite, or a module interface inside the codebase. At first it sends everything
   to the old system.
2. **Pick the first slice** for learning, not for value: small, low risk, real traffic. It
   proves the routing, deploy, auth and observability path.
3. **Build the slice in the new system** and verify against the old: replay recorded requests
   and compare responses, or shadow live traffic (new system receives a copy, its response is
   discarded and diffed). Shadow only reads, or make writes no-ops, or effects happen twice.
4. **Shift traffic gradually** by flag or percentage (internal users, one tenant, 5%, 50%,
   all), watching error rate and latency per side. Keep the switch back to old instant.
5. **Remove the old slice** as soon as the new one has held full traffic for the agreed
   period. Then take the next slice.

Data is the hard part. Prefer one writer per table at any time; when both systems must write
the same data, choose deliberately between sharing the database (simple, couples the schemas),
syncing through events or change capture (decoupled, eventually consistent), and dual writes
(avoid: the two writes diverge on partial failure). Change schemas by expand, migrate,
contract (`0x:postgres-database`). Sessions and auth must be valid on both sides during the
migration, or users are signed out at each boundary.

Traps:

- **The migration stalls at 80%.** Two systems then cost more than either one, forever. Before
  starting, list all slices, set a finish date, and schedule the hard ones (reports, admin
  tools, batch jobs, integrations) early instead of last.
- **Feature work continues in the old system.** Freeze each area as its slice begins, or the
  target keeps moving.
- **The facade becomes a third system** with its own logic. Keep it to routing.
- **No comparison step.** Without replay or shadowing, differences are found by customers.

## Ask the user

- **What change is this code blocking, and how often is it touched?** Decides whether
  refactoring pays at all. Assume: refactor only what the current task touches.
- **Is any behavior here relied on by customers or integrations, even if it looks wrong?**
  Decides whether an odd behavior is preserved or fixed. Assume preserve, and flag it.
- **How long may a framework or runtime stay behind the current supported version?** Sets the
  upgrade cadence. Assume: never past the vendor's end of support, majors within a few months
  of release once dependencies support them.
- **For a proposed rewrite: what is the monthly cost of the current system's limits, and can
  delivery be sliced?** Assume no rewrite unless a foundation problem is named and slices can
  ship independently.
- **How long must a retired route, field or job be kept before deletion?** Contracts and
  external clients set this. Assume one full billing cycle of zero traffic for internal use,
  and the published deprecation period for public APIs (`0x:api-design`).
