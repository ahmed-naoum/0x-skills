# Refactoring and rewrites

Read this when: restructuring code, changing code nobody understands, removing dead code, a
mechanical change across many files, a new Rust edition or crate major, porting an app to Rust,
or deciding between refactoring, rewriting and leaving a system alone.

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
change. Rule of thumb: tolerate duplication until the third occurrence; the first two rarely
show the right abstraction. Debt as a portfolio is in `0x:engineering-leadership`.

## Small behavior-preserving steps

The method that keeps refactoring safe is step size. Each step is small enough that if tests
go red, the cause is the last edit and the remedy is undo, not debugging.

1. Start green: `cargo clippy` and the relevant tests pass, and the working tree is clean.
2. Confirm the tests cover the code being moved (cargo-llvm-cov on that module, or break the
   code on purpose and see a test fail). If not, add characterization tests first.
3. Make one named transformation: rename, extract function, inline, move, change signature,
   replace conditional with a table, introduce a parameter struct.
4. Run `cargo check` and the nearby tests (`cargo nextest run -p <crate>`). Seconds to a
   minute, not more; rust-analyzer shows errors as you type.
5. Commit. Repeat.

Rules:

- Use rust-analyzer's rename, move and extract assists. They update every reference, including
  across crates in the workspace, and are safer than hand edits. Macros are their blind spot:
  names built inside macros or used from `sqlx::query!` strings, serde attributes and
  templates are not renamed; search for them.
- Red for more than a few minutes: revert to the last green commit and take a smaller step.
  Fighting the borrow checker through a large edit means the step was too big.
- Do not change tests and code in the same step unless the test was bound to implementation
  detail; a test that must change during a refactor is no longer checking that behavior was
  preserved. Fix such tests first, in a separate commit, to assert on outputs.
- For a signature or module change with many callers, use parallel change: add the new form
  beside the old, mark the old `#[deprecated(note = "use ...")]` so the compiler lists every
  remaining caller, migrate callers in batches, delete the old. Every intermediate commit ships.
- Types are the fastest safety net, and Rust's is strong: change the type first (a new enum
  variant, a newtype for a bare `String`, an extra parameter) and let the compiler list every
  place that must follow. A `_ =>` arm in a `match` hides a new variant from this list; that
  is why clippy's `wildcard_enum_match_arm` exists (static-analysis-types.md).
- Keep the branch short-lived. A refactoring branch open for a week conflicts with everything;
  merge behavior-preserving steps to main daily.

## Separate refactoring from behavior change

A commit or pull request is either structural (behavior identical) or behavioral (structure
minimal), not both.

- Review: a structural diff is skimmed for "nothing changed", a behavioral one read fully;
  mixed, a one-line behavior change hides in 400 moved lines. Bisect and revert then land on a
  small behavioral commit without losing the cleanup.
- Cleanup found mid-feature: stash, refactor on green, commit, reapply; or split with `git add -p`.
- Label structural commits (`refactor:` prefix or similar) and state in the message that
  behavior is unchanged and how that was verified.
- Purely mechanical mass edits (`cargo fmt` adoption, renames, codemod output) go in their
  own commit, with nothing hand-edited in it, and can be listed in `.git-blame-ignore-revs` so
  blame skips them (GitHub reads the file by itself; local git needs `blame.ignoreRevsFile`
  set). Commit and pull-request conventions are in `0x:git-collaboration`.

## Delete dead code now

Unreachable code is not free: it is read, searched, compiled on every build, migrated in every
upgrade, flagged by scanners, and believed. Version control is the archive; a deleted function
is one `git log -S` away.

Delete in the same change that makes it unreachable:

- The old branch when a feature flag reaches 100% and has been stable for an agreed period
  (put the removal date in the flag's description when creating it).
- The old implementation when the last caller moves to the new one.
- Commented-out code, always. It rots immediately and nobody dares remove it later.
- Unused `pub` items, modules, dependencies, Cargo features, environment variables, routes,
  database columns (the column drop goes through the migration sequence in
  `0x:postgres-database`), and the tests and docs of the deleted thing.

Before deleting, prove it is dead at the right boundary. The compiler's `dead_code` warning
covers private items; `pub` items of a library crate are never reported, which is why items
should be `pub(crate)` unless another crate uses them (tooling in static-analysis-types.md).
For HTTP routes, server functions, jobs, webhooks and public API fields, check access logs or
add a counter and wait one full business cycle (a month covers monthly jobs and billing runs;
annual renewals, year-end jobs and old mobile app versions need a check of schedules and
client versions, not a wait). Dynamic references (route paths in strings, serde field names,
column names in SQL, names stored in the database or a queue) defeat the compiler; search for
the string.

A "cleanup sprint" is the wrong tool: by then nobody remembers what is safe to remove. Stage a
large, risky deletion: stop calling, log-and-wait, then delete. Code comes back from git; data
does not: drop a column or table last, after a verified backup, once nothing reads or writes it.

## Characterization tests for legacy code

Legacy here means code without tests whose exact behavior is not known. Before changing it,
pin what it does today, bugs included, so that the refactor can be shown to preserve it.

1. Find a seam: the nearest public entry point where inputs can be supplied and outputs
   observed (a function, a route through the router, a job handler, a CLI). Prefer the
   outermost seam; it leaves the most freedom to restructure inside.
2. Collect realistic inputs: from logs, production-shaped data, existing callers, edge cases.
3. Run the code and record the outputs as the expected values. Snapshot files are right here,
   unlike in normal tests: insta records each output, and `cargo insta review` accepts them.
   Do not write what it should do; write what it does.
4. Make it deterministic first: inject the clock, seed randomness, fake the network, sort
   `HashMap`-ordered output. Then change the code on purpose and confirm the tests fail; use
   coverage to find branches no input reaches.
5. Refactor under these tests. Replace them with intention-revealing tests as understanding
   grows; delete the snapshots when the module is understood.

```rust
/// Pins what the legacy quote code returns today, bugs included, before restructuring it.
#[test]
fn legacy_quote_characterization() {
    let cases = [
        ("monthly_one_seat", QuoteInput { seats: 1, annual: false, coupon: None }),
        ("annual_eleven_seats", QuoteInput { seats: 11, annual: true, coupon: None }),
        ("expired_coupon", QuoteInput { seats: 3, annual: false, coupon: Some("SPRING24") }),
        ("zero_seats", QuoteInput { seats: 0, annual: false, coupon: None }),
    ];
    for (name, input) in cases {
        insta::assert_debug_snapshot!(name, quote(&input));
    }
}
```

When an observed behavior looks like a bug, keep it in the characterization, flag it, and fix
it afterwards as a separate behavioral change: callers or stored data may depend on it.

If the code has no usable seam (logic inside a handler that also queries and calls out, a
`static`, a database trigger), make the smallest possible untested change to create one:
extract a function and pass dependencies as parameters, using rust-analyzer's assists only.
For risky replacements, run old and new in parallel on real inputs and log differences before
switching.

## Smells worth fixing

Most smell catalogs list everything; these three account for most of the cost of change.

| Smell | How to recognize it | Fix | Do not over-apply |
|---|---|---|---|
| Duplicated knowledge | One business rule (a price, a limit, a permission, a status transition, a validation) encoded in two places that must change together; a bug fixed in one place and not the other | One owner for the rule: a function, a newtype constructor, a constant, a database constraint. Derive the rest | Code that looks alike but changes for different reasons is not duplication. Merging it couples unrelated things; the wrong abstraction (often a generic or a trait) costs more than the copy |
| Long function | Mixed levels of abstraction; comments marking sections; many local variables; nesting more than about three deep; needs scrolling to hold in mind | Extract the sections the comments name, pull the pure decision out of the I/O (see test-strategy.md), replace nested conditionals with early returns, `?` or a `match` | A long linear function that reads top to bottom is fine. Do not shred it into one-line helpers that must be read in five files |
| Wide interface | A function with many parameters or `bool` flags; a crate exporting most of its internals; a component with dozens of props; a struct with many `Option` fields that are only valid in some combinations | Narrow to what callers need, split by use case, replace `bool` flags with an enum or separate functions, make invalid combinations unrepresentable (an enum per state) | Do not design for callers that do not exist |

Secondary signals: shotgun surgery; feature envy; primitive obsession (IDs, money and emails
as bare `String` and `i64`: give them newtypes); errors as `String` or `Box<dyn Error>` in
domain code, which callers cannot match on (use a `thiserror` enum); `Arc<Mutex<_>>` threaded
through many modules, which is shared state wanting one owner; speculative generality (traits
with one implementation, added for a hypothetical second or only for mocking). A `.clone()` to
satisfy the borrow checker is usually fine unless large or on a hot path.

## Codemods for mechanical changes

When the same edit is needed in more than about 20 places, script it. A codemod is
repeatable (rerun after rebasing), reviewable (review the script, sample the output) and
consistent.

| Tool | Use when |
|---|---|
| rust-analyzer rename, move and extract | A symbol, module or file change; always try this first |
| `cargo fix` and `cargo clippy --fix` | Applying the compiler's and clippy's machine-applicable suggestions, including edition migrations |
| rust-analyzer structural search and replace | Pattern rewrites that need name resolution (`foo($a, $b) ==>> bar($b, $a)`) |
| ast-grep | Structural search and replace by syntax pattern across many files; quick to write |
| Regex search and replace | Only for text that is unambiguous as text (a path in a string, a config key) |
| A coding agent applying a written rule file by file | Changes needing judgment per site; give it the rule, a few worked examples, and run `cargo check` after each batch |

Procedure:

1. Start from a clean tree; write the transform against two or three representative files,
   including an awkward one (code inside macro invocations is where syntax tools miss).
2. Dry-run and read a sample. Compare the matched count with a plain text search for the old
   pattern: the difference is what the transform missed.
3. Run on everything, then `cargo fmt`, `cargo clippy --all-targets` and the tests.
4. Commit the mechanical output alone, naming the command; hand fixes go in the next commit.
5. Ban the old pattern so it does not come back: `#[deprecated]` on the old API, or a
   `disallowed-methods` entry in `clippy.toml`.

## Editions, crate majors and the toolchain

The failure mode is a branch that upgrades everything, breaks in forty ways at once and is
never merged. Sequence that avoids it:

1. Read the migration guide and the changelog of breaking changes fully before touching
   anything. List the ones that apply.
2. On the current version, move to its latest compatible release (`cargo update`) and clear
   every deprecation warning there. These fixes ship on the old version, one at a time.
3. Check that the crates around it have releases supporting the target. Crates that share
   public types must move together (axum, tower-http and leptos_axum; sqlx and anything built
   on it): two major versions of one crate can coexist in the dependency graph, and the result
   is an error such as "expected `Request`, found `Request`" between their types.
   `cargo tree -d` lists duplicated crates. An unmaintained crate is the usual blocker; replace
   it before the upgrade, not during.
4. One major at a time, one core crate at a time. Do not combine a framework upgrade with an
   edition change or a toolchain bump.
5. Fix what the compiler reports, then look for what it cannot: behavior changes that still
   compile. Axum 0.8, for example, moved path parameters from `/:id` to `/{id}` and rejects the
   old form when the router is built, at startup, not at compile time; any test that builds
   the router catches it.
6. Adopt new features later. An upgrade changes versions; it does not also migrate to new
   patterns.
7. Verify beyond the unit suite: release build, end-to-end critical journeys, WASM size and
   startup, then a preview or canary deploy with error rates watched. A `Cargo.lock` revert is
   a clean rollback if nothing else rode along.

**Editions** are per crate, and crates of different editions link together, so a workspace
migrates one crate at a time: `cargo fix --edition -p <crate>`, set `edition = "2024"` in its
`Cargo.toml`, build, test, commit. Review what the tool flags rather than accepting it blindly;
the 2024 edition changed when some temporaries are dropped (in `if let` and in a block's tail
expression), which can move when a lock guard is released, and made `std::env::set_var`
`unsafe`.

**The toolchain** is pinned in `rust-toolchain.toml`, read by rustup, CI and editors alike.
Stable releases come every six weeks with new clippy lints that fail a `-D warnings` build:
bump the pin on a schedule in its own pull request and fix the new lints there.

Cadence from Launch: compatible updates continuously through an update bot with CI as the
gate; majors on a schedule once the ecosystem has caught up; skipping two majors turns a day
into weeks. Dependency risk and update automation are in `0x:web-security`.

## Rewrite, refactor or leave alone

Default: refactor incrementally. A from-scratch rewrite discards the bug fixes and edge-case
handling that the old code accumulated, takes longer than estimated because the old system's
behavior is the spec and nobody wrote it down, and delivers no user value until the end while
the old system still needs maintenance.

| Evidence | Decision |
|---|---|
| Works, rarely changes, no pressure | Leave it alone, however old or inelegant |
| Painful to change but changeable; tests exist or can be added | Refactor in place, funded by the features that touch it |
| The foundation is the problem: unsupported platform, a data model that contradicts the product, a vendor going away | Replace incrementally with a strangler (below) |
| An existing product moving to a new language, such as a TypeScript app moving to Rust | Strangler by route or service: new work in Rust, old slices move when their turn is scheduled or when they need real change; never a frozen big-bang port |
| Small enough to rebuild in days and fully understood (a script, one service, a prototype) | Rewrite; the risk is bounded |
| Prototype that found product-market fit on throwaway code | Rewrite or replace in slices is legitimate, since it was built to learn. Keep the data model migration explicit |
| "It is ugly", "I did not write it" | Not reasons. These predict the same complaints about the rewrite in two years |

Questions that decide it: what cannot be done today, and what does that cost per month? Would
replacing one part fix it? Is there a full list of what the old system does, including what
nobody remembers? Can the rewrite ship in slices? If not, it is a big-bang rewrite: do not start.

## Strangler migration

Replace a system piece by piece behind a stable front, with both running, until the old one
has no traffic and is deleted.

1. **Put a facade in front.** A routing layer the team controls: path rules in the reverse
   proxy or load balancer, or the new Axum app with a fallback that forwards unmigrated paths
   to the old app. At first it sends everything to the old system.
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
migration (same cookie name, format and signing key, or a shared session store), or users are
signed out at each boundary.

Traps: **the migration stalls at 80%**, and two systems cost more than either, forever: list
all slices, set a finish date, schedule the hard ones (reports, admin tools, batch jobs,
integrations) early. **Feature work continues in the old system**: freeze each area as its
slice begins. **The facade grows logic**: keep it to routing. **No comparison step** (replay or
shadowing): then customers find the differences.

## Ask the user

- **What change is this code blocking, and how often is it touched?** Decides whether
  refactoring pays at all. Assume: refactor only what the current task touches.
- **Is any behavior here relied on by customers or integrations, even if it looks wrong?**
  Decides whether an odd behavior is preserved or fixed. Assume preserve, and flag it.
- **How long may the toolchain or a core crate stay behind the current release?** Sets the
  upgrade cadence. Assume: toolchain bumped every one to three releases, crate majors within a
  few months once their neighbors support them.
- **For a proposed rewrite or port: what is the monthly cost of the current system's limits,
  and can delivery be sliced?** Assume no big-bang rewrite; slices that ship independently.
- **How long must a retired route, field or job be kept before deletion?** Contracts and
  external clients set this. Assume one full billing cycle of zero traffic for internal use,
  and the published deprecation period for public APIs (`0x:api-design`).
