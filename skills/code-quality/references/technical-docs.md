# Technical documentation

Read this when: writing or restructuring a README, setup instructions, architecture notes,
code comments, developer guides or a handover package, or when existing docs are stale,
unfindable or giving wrong answers to people and AI assistants.

## What to write, by stage

Documentation is a product with a maintenance cost. Write the smallest set that removes a
real, recurring question, and delete what nobody maintains: a wrong doc is worse than none,
because it is trusted.

| Stage | Write | Skip |
|---|---|---|
| Prototype | README with what it is and how to run it; `.env.example` | Everything else |
| Launch | README and quickstart that work from a clean machine; architecture notes (one page); how to deploy and roll back; decision records for choices that are expensive to reverse; an agent instruction file | Exhaustive reference, diagrams of everything, a docs site |
| Scale | The above plus how-to guides for recurring tasks, onboarding path, ownership map, runbooks | Documenting what the code and types already say |

What never needs prose: anything a tool can generate or enforce from the source (API reference
from the schema, types, lint rules, the list of scripts). Generate it or link to the source.

Owners elsewhere: decision records in `0x:engineering-leadership`; runbooks in
`0x:site-reliability`; public API reference in `0x:api-design`; agent instruction files in
depth in `0x:ai-coding-agents`; customer help content in `0x:sales-support`.

## README and quickstart

The README answers, in this order, for someone who has never seen the project: what is this,
how do I run it, how do I change it safely, where is everything else. Target: clone to a
running app with seeded data in under 10 minutes, with no question asked of the author.

```markdown
# <Name>
One or two sentences: what it does and for whom. Link to production and staging.

## Quickstart
Prerequisites: rustup (the toolchain in rust-toolchain.toml installs itself), Docker,
sqlx-cli and cargo-leptos (`cargo install --locked sqlx-cli cargo-leptos`).
    cp .env.example .env
    ./scripts/setup         # starts Postgres, runs migrations, seeds
    cargo leptos watch      # http://127.0.0.1:3000, sign in as admin@example.test / printed password

## Common tasks
Test, lint, format, add a migration, run one test, reset the database: one command each.

## Project layout
Five to ten lines: top-level directories and what belongs in each.

## Deploy
How a change reaches production, how to roll back. Link to details.

## More
Links: architecture, decisions, runbooks, contributing.
```

Rules that make it work:

- **Commands are copy-pasteable and complete.** No "configure your database": give the
  command. Every manual step will fail for the next person and for an agent.
- **Collapse setup into one script** (`./scripts/setup`, a `just` recipe, or a
  `cargo xtask setup` command written in Rust), idempotent, that starts dependencies, migrates,
  seeds and sets `core.hooksPath`. The README then documents one command, and the script is the
  tested source of truth.
- **`.env.example` is complete**: every variable, with a safe local default or a comment
  saying where to obtain the value. Parse env into the typed config struct at startup so a
  missing one fails with its name. Secrets never go in the README or the example file.
- **State versions by reference** (`rust-toolchain.toml`, `Cargo.lock`, the Compose file's
  Postgres image), not by number in prose that goes stale.
- **Show the expected result**: the URL, the login, what success looks like (and that the
  first cold build takes minutes), and the most common setup failures with their fix.
- **Keep it short.** Past roughly 150 lines, move sections into `docs/` and link. Marketing
  copy, badges walls and history do not belong.
- **Test it**: follow it on a clean machine or container before calling it done, and run the
  setup script in CI (see "Stopping rot").

## Docs live in the repository

Default: Markdown in the repo, next to the code, changed in the same pull request as the
behavior it describes.

- The pull request is the enforcement point. Add a checklist line ("docs updated or not
  needed") and, when reviewing a change to setup, env variables, commands, architecture or
  public behavior, treat a missing doc change as a defect in the change.
- Docs are versioned with the code: an old release shows its docs, `git blame` explains them.
- Agents and search find them. A wiki or a shared drive is invisible to a coding agent and
  drifts, because updating it is a separate chore after the work is "done".
- Layout that scales to a small team: `README.md` at the root; `docs/architecture.md`;
  `docs/decisions/` for decision records; `docs/how-to/` for task guides; `docs/runbooks/`; a
  README in a package or module only when it has its own setup or rules.
- One home per fact. If the same instruction appears in the README, a wiki page and a
  comment, two of the three will be wrong within months. Link instead of copying.
- Outside the repo: secrets (a secrets manager), customer-facing help, non-code matters.

Add a docs site generator only once external developers read the docs.

## Comments: why, not what

The code already says what it does; a comment that repeats it will be wrong after the next
edit. A comment earns its place when it carries information the code cannot:

| Write a comment for | Example |
|---|---|
| Why this approach and not the obvious one | `// Sequential on purpose: the provider rate-limits to 2 requests per second per key.` |
| A constraint or invariant from outside the code | `// Amounts are integer cents. Stripe rejects fractional minor units.` |
| A workaround, with its exit condition | `// Works around <crate> issue #1234 (double fire on iOS). Remove when on >= 3.2.` |
| Why an `unsafe` block is sound (required) | `// SAFETY: len was checked against the buffer above; the pointer is valid for len bytes.` |
| A non-obvious consequence | `// Order matters: revoking sessions before the password write leaves a window for reuse.` |
| A warning to the next editor | `// Called from the billing webhook too. Do not add user-context assumptions here.` |
| The unit, range or format of a value when the type cannot say | `timeout: Duration` beats a comment; else `// ISO 4217 code, upper case` |

Rules:

- Prefer making the code say it: a better name, an extracted function, a narrower type or a
  constant beats a comment explaining a confusing line. Comment what remains.
- No commented-out code, no change logs or author names in comments (version control holds
  those), no banner separators, no restating the function name.
- `TODO` comments carry an issue reference or an owner and a condition; a bare `TODO` is a
  wish. Lint for the format if they accumulate.
- Doc comments (`///` on items, `//!` for a crate or module's purpose) on the `pub` API of
  shared crates: one line of purpose, then only what the signature does not show, in rustdoc's
  conventional sections: `# Errors` (when it returns `Err`), `# Panics`, side effects and
  idempotency, and `# Examples`. Examples are doctests: `cargo test --doc` compiles and runs
  them, so they cannot drift from the API (cargo-nextest skips doctests; run both). Skip doc
  comments on internal code whose signature is self-explanatory.

```rust
/// Splits an amount into `parts` shares that differ by at most one cent; the first
/// `cents % parts` shares carry the extra cent, so the result is stable across calls.
///
/// # Panics
///
/// Panics if `parts` is zero.
///
/// # Examples
///
/// ```
/// assert_eq!(billing::split_evenly(1_000, 3), vec![334, 333, 333]);
/// ```
pub fn split_evenly(cents: u64, parts: u32) -> Vec<u64> {
    let parts = u64::from(parts);
    let (base, remainder) = (cents / parts, cents % parts);
    (0..parts).map(|i| base + u64::from(i < remainder)).collect()
}
```

- `cargo doc --no-deps` with `RUSTDOCFLAGS="-D warnings"` in CI fails on broken intra-doc
  links; pedantic clippy's `missing_errors_doc` and `missing_panics_doc` enforce the sections.
- When changing code, update or delete the comment above it in the same edit. A stale comment
  is a bug.
- Commit messages hold the why of a change; comments hold the why of the code as it stands.

## Architecture notes: map, flows, constraints

One document, `docs/architecture.md`, readable in 15 minutes, that lets a newcomer predict
where a change goes and what it might break. Three parts:

1. **Map.** The system's parts and what talks to what: the web app, database, queue and
   workers, cache, object storage, each third party, and where each runs. One diagram at the
   level of deployable units and external systems, kept as text in the repo (Mermaid renders
   on the common code hosts) so it is diffable. Then the code map: the workspace's crates and
   top-level modules, the responsibility of each in one line, and the dependency direction
   between them (the crate graph enforces it; static-analysis-types.md).
2. **Key flows.** Three to six traces through the system for the paths that matter and are
   not obvious from the map: a request from browser to database and back, sign-in and
   session, a server function from the WASM client to the database, checkout through webhook
   to entitlement, a background job's life, a deploy. Each as a numbered sequence naming the
   crates, modules or files involved. Flows are what people
   actually need when debugging.
3. **Constraints and invariants.** The rules that are true everywhere and that code review
   must protect: every query is tenant-scoped through one helper; money is integer minor
   units; all third-party calls go through wrappers; webhook handlers are idempotent; no
   `unwrap` in request paths; no `unsafe` outside the one crate that needs it; migrations are
   backward compatible with the previous release. Add what is deliberately
   absent ("no service calls between modules except through X"), since absences cannot be
   seen in code. Add known weak points and planned changes.

Keep out: anything that changes weekly, class-level detail, generated listings, and the
history of how it got here (that is in decision records; link them where a constraint needs
its reason). Write it for stability: a good architecture note needs editing a few times a
year. Where a constraint can be enforced by a lint rule or test, do that and mention the rule
(static-analysis-types.md).

## Four kinds of documentation

A page that tries to teach, instruct, list and explain at once serves none of the readers.
Keep the four kinds on separate pages (the Diátaxis framework) and decide which one is being
written before starting.

| Kind | Reader's state | Form | Test |
|---|---|---|---|
| Tutorial | New, learning by doing | One guided path to a working result, no choices, no digressions | A beginner finishes it without getting stuck |
| How-to guide | Competent, has a specific task | Numbered steps for one goal, starting from stated preconditions; title begins with the task ("Add a database migration") | The task gets done; nothing but the task is covered |
| Reference | Working, needs a fact | Complete, consistent, dry: every option, endpoint, variable, error code; structured like the thing it describes | The fact is found in seconds and is correct |
| Explanation | Wants to understand why | Prose: background, trade-offs, alternatives rejected | The reader can make a good decision the doc did not foresee |

Internally the useful mix is how-to guides and explanation, with reference generated from code
(`cargo doc`); the quickstart is the one tutorial every project needs. Common failure: a how-to
that stops to explain concepts (link instead), or reference written as unscannable narrative.

## Docs that people, search and AI assistants can retrieve from

Readers arrive by search or by an assistant pulling one section out of context, not by
reading from the top. Write each section to survive that.

- **Self-contained sections.** A section states its subject by name and does not depend on
  "as described above". Repeat the noun instead of "it" or "this" across section boundaries.
- **Headings are the question or task in the reader's words**: "Rotate the webhook signing
  secret", not "Secrets (cont.)" or "Miscellaneous". Use the exact strings people search
  for: error messages verbatim, command names, config keys, in code formatting.
- **One topic per page, one name per thing.** If the code says `workspace`, the docs do not
  alternate between workspace, team and organization. Keep a short glossary when the domain
  has its own vocabulary.
- **Text, not pictures of text.** Commands, config and errors as code blocks; diagrams as
  text source with a prose summary of what they show; tables for option lists.
- **State versions and scope** where behavior differs ("applies from v2 of the API"), and
  mark deprecated material at the top of the page, or delete it. Stale pages are retrieved
  with the same confidence as current ones, so contradiction between two pages is the worst
  defect: remove the older.
- **Complete, runnable examples** with `use` lines and realistic values; fragments get
  assembled wrongly.
- **An agent instruction file at the repository root** (`CLAUDE.md`, or `AGENTS.md` for other
  tools): the commands to build, test and lint, the invariants from the architecture notes,
  conventions that differ from defaults, and pointers to deeper docs. Short and current, since
  it is read in every session; put detail in linked files. Depth is in `0x:ai-coding-agents`.
- **For public docs**, serve clean Markdown or plain HTML that works without JavaScript or
  WASM, keep
  stable URLs with redirects when pages move, and consider publishing an index of the docs in
  a machine-readable form such as the `llms.txt` convention. Check what assistants actually
  answer about the product by asking them the top ten support questions, and fix the pages
  that produce wrong answers.

## Handover

A handover is done when the receiver has made and deployed a change alone, not when a
document was sent. Package:

1. **Setup script and verified quickstart**: the receiver runs it on their own machine,
   unaided, while the author watches and fixes every stumble in the docs.
2. **Architecture notes** as above, with the weak points stated honestly: the fragile
   module, the manual step, the thing that pages at night.
3. **Ownership and access map**: every external account and system (code host, hosting,
   database, DNS and domain registrar, payment provider, email, error tracker, analytics, app
   stores), who owns it, how access is granted, where credentials live, what is billed to
   whom and when it renews. Transfer ownership to company accounts, not personal ones, and
   rotate shared secrets after the handover (`0x:web-security`).
4. **Operations**: how to deploy and roll back, scheduled jobs and what they do, backups and
   how to restore, alerts and what each means, recurring manual tasks with their calendar
   (certificate, key and domain renewals; tax or billing runs).
5. **State of the work**: open bugs by severity, known debt, in-flight changes, flags
   currently on and their intent, decisions pending, promises made to customers.
6. **The unwritten knowledge**: a recorded walkthrough of the key flows and a list of "things
   that surprised me". An hour of recording captures what nobody will write.

Verify with a real task: a small change taken from ticket to production by the receiver,
then a simulated incident (roll back a deploy, restore to a scratch database). For a
contractor handing back to a founder, the same list is the acceptance checklist; put it in
the contract before work starts (`0x:sales-support` covers the contract side when the founder
is the contractor). Receiving the repository is not the same as owning the code: in many
jurisdictions a contractor keeps the copyright unless a written agreement assigns it, and the
rules differ by country, so have the assignment clause checked by a lawyer
(`0x:company-building`). List third-party licenses in the package (`0x:privacy-compliance`).

## Stopping rot

Docs decay because nothing fails when they are wrong. Make something fail.

- **Tested examples.** Run the setup script and the README's test command in CI from a clean
  checkout; a broken quickstart then breaks the build. Rust examples in rustdoc are doctests,
  run by `cargo test --doc`. A library crate can make its README a doctest too, with
  `#![doc = include_str!("../README.md")]` at the crate root: every `rust` block in the README
  then compiles in CI (tag shell blocks `bash` and fragments `rust,ignore`, or they fail).
- **Generated reference.** `cargo doc` from the doc comments, the API reference from the
  generated OpenAPI document, CLI help from the clap definitions, env variable tables from the
  config struct. Regenerate in CI and fail on a diff.
- **Link checking** on a schedule and in pull requests that touch docs; internal links by
  relative path, so they resolve on every branch and the checker can verify them offline.
- **An owner per document.** Put docs paths in the code-owners file so changes request the
  right reviewer, and so every page has someone to ask. Unowned pages are deleted or adopted.
- **A review date on pages that cannot be tested** (architecture, runbooks, handover,
  onboarding): a "last reviewed" line at the top and a recurring reminder, quarterly at
  Launch stage. Review means reading it against reality, not bumping the date. Runbooks are
  also reviewed after every incident that used one.
- **Delete aggressively.** For each stale page choose: fix now, delete, or mark at the top as
  historical with a pointer to the current source. Never leave it looking current.
- **Use the docs.** Onboard each new person or agent from the docs alone; their first change
  fixes what failed them. A question asked twice is a missing page: write it, send the link.

## Ask the user

- **Who will read this: future self, a new hire, a contractor, outside developers, a buyer in
  due diligence?** Sets depth and which of the four kinds to write. Assume a competent
  developer new to the project, and a coding agent.
- **Is a handover, hire or sale expected in the next months?** If so, the ownership map and
  operations notes move up. Assume no; keep README, architecture notes and agent file current.
- **Which accounts and systems are in personal names?** Only the user knows; it is the most
  common handover failure. Assume some are, and ask for the list.
- **May the docs be public?** Public docs help adoption and expose architecture details and
  internal names. Assume repository docs are private and only API and product docs are public.
- **How much time is acceptable for docs per change?** Assume minutes: update what the change
  made false, add a how-to only when a question has come up twice.
