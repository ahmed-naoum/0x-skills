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

Owners elsewhere: decision records in `0x:engineering-leadership`; runbooks and postmortems in
`0x:site-reliability`; public API reference and developer portal in `0x:api-design`; agent
instruction files in depth in `0x:ai-coding-agents`; customer help content in
`0x:sales-support`.

## README and quickstart

The README answers, in this order, for someone who has never seen the project: what is this,
how do I run it, how do I change it safely, where is everything else. Target: clone to a
running app with seeded data in under 10 minutes, with no question asked of the author.

```markdown
# <Name>
One or two sentences: what it does and for whom. Link to production and staging.

## Quickstart
Prerequisites: Node (version from .nvmrc), pnpm, Docker.
    cp .env.example .env
    pnpm install
    pnpm dev:setup      # starts Postgres, migrates, seeds
    pnpm dev            # http://localhost:3000, sign in as admin@example.test / printed password

## Common tasks
Test, lint, type check, add a migration, run one test, reset the database: one command each.

## Project layout
Five to ten lines: top-level directories and what belongs in each.

## Deploy
How a change reaches production, how to roll back. Link to details.

## More
Links: architecture, decisions, runbooks, contributing.
```

Rules that make it work:

- **Commands are copy-pasteable and complete.** No "configure your database" steps: give the
  command. Every step a human must do by hand is a step that will fail for the next person
  and for an agent.
- **Collapse setup into one script** (`pnpm dev:setup` or `make setup`), idempotent, that
  starts dependencies, migrates and seeds. The README then documents one command, and the
  script is the tested source of truth.
- **`.env.example` is complete**: every variable, with a safe local default or a comment
  saying where to obtain the value. Validate env at startup so a missing one fails with its
  name. Secrets never go in the README or the example file.
- **State versions by reference** (`.nvmrc`, `engines`, the lockfile), not by number in prose
  that goes stale.
- **Show the expected result**: the URL, the login, what success looks like, and the two or
  three most common setup failures with their fix.
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
- Docs are then versioned with the code: checking out an old release shows its docs, and
  `git blame` explains a paragraph.
- Agents and search find them. A wiki or a shared drive is invisible to a coding agent and
  drifts, because updating it is a separate chore after the work is "done".
- Layout that scales to a small team: `README.md` at the root; `docs/architecture.md`;
  `docs/decisions/` for decision records; `docs/how-to/` for task guides; `docs/runbooks/`; a
  README in a package or module only when it has its own setup or rules.
- One home per fact. If the same instruction appears in the README, a wiki page and a
  comment, two of the three will be wrong within months. Link instead of copying.
- What belongs outside the repo: secrets (a secrets manager), customer-facing help, and
  company matters that are not about the code.

A docs site generator is worth adding only when external developers read the docs. Until
then, Markdown rendered by the code host is enough.

## Comments: why, not what

The code already says what it does; a comment that repeats it will be wrong after the next
edit. A comment earns its place when it carries information the code cannot:

| Write a comment for | Example |
|---|---|
| Why this approach and not the obvious one | `// Sequential on purpose: the provider rate-limits to 2 requests per second per key.` |
| A constraint or invariant from outside the code | `// Amounts are integer cents. Stripe rejects fractional minor units.` |
| A workaround, with its exit condition | `// Works around <library> issue #1234 (double fire on iOS). Remove when on >= 3.2.` |
| A non-obvious consequence | `// Order matters: revoking sessions before the password write leaves a window for reuse.` |
| A warning to the next editor | `// Called from the billing webhook too. Do not add user-context assumptions here.` |
| The unit, range or format of a value when the type cannot say | `timeoutMs`, or `// ISO 4217 code, upper case` |

Rules:

- Prefer making the code say it: a better name, an extracted function, a narrower type or a
  constant beats a comment explaining a confusing line. Comment what remains.
- No commented-out code, no change logs or author names in comments (version control holds
  those), no banner separators, no restating the function name.
- `TODO` comments carry an issue reference or an owner and a condition; a bare `TODO` is a
  wish. Lint for the format if they accumulate.
- Doc comments (TSDoc) on exported functions of shared modules and public packages: one line
  of purpose, then only what the signature does not show (units, errors thrown, side effects,
  idempotency, an example for anything tricky). Skip them on internal code whose signature is
  self-explanatory.
- When changing code, update or delete the comment above it in the same edit. A stale comment
  is a bug.
- Commit messages hold the why of a change; comments hold the why of the code as it stands.

## Architecture notes: map, flows, constraints

One document, `docs/architecture.md`, readable in 15 minutes, that lets a newcomer predict
where a change goes and what it might break. Three parts:

1. **Map.** The system's parts and what talks to what: the web app, database, queue and
   workers, cache, object storage, each third party, and where each runs. One diagram at the
   level of deployable units and external systems, kept as text in the repo (Mermaid renders
   on the common code hosts) so it is diffable. Then the code map: top-level directories or
   modules, the responsibility of each in one line, and the dependency direction between them.
2. **Key flows.** Three to six traces through the system for the paths that matter and are
   not obvious from the map: a request from browser to database and back, sign-in and
   session, checkout through webhook to entitlement, a background job's life, a deploy. Each
   as a numbered sequence naming the files or modules involved. Flows are what people
   actually need when debugging.
3. **Constraints and invariants.** The rules that are true everywhere and that code review
   must protect: every query is tenant-scoped through one helper; money is integer minor
   units; all third-party calls go through wrappers; webhook handlers are idempotent;
   migrations are backward compatible with the previous release. Add what is deliberately
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

For an internal codebase the useful mix is mostly how-to guides and explanation
(architecture, decisions), with reference generated from code. Tutorials matter when external
developers adopt the product; the quickstart is the one tutorial every project needs. Common
failure: a how-to that stops to explain concepts (link to the explanation instead), or
reference written as narrative that cannot be scanned.

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
- **Complete, runnable examples** with imports and realistic values; fragments get assembled
  wrongly.
- **An agent instruction file at the repository root** (`CLAUDE.md`, or `AGENTS.md` for other
  tools): the commands to build, test and lint, the invariants from the architecture notes,
  conventions that differ from defaults, and pointers to deeper docs. Short and current, since
  it is read in every session; put detail in linked files. Depth is in `0x:ai-coding-agents`.
- **For public docs**, serve clean Markdown or plain HTML that works without JavaScript, keep
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
  checkout; a broken quickstart then breaks the build. Keep code samples in real files that
  are compiled or executed by the test suite and included into the docs, or type-check the
  fenced blocks, so samples cannot drift from the API.
- **Generated reference.** API reference from the OpenAPI document or schema, CLI help from
  the command definitions, env variable tables from the env schema. Regenerate in CI and fail
  on a diff.
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
- **Use the docs.** Onboard each new person or agent from the docs alone and have them fix
  what failed them as their first change. Answer questions by writing or fixing the doc and
  sending the link; a question asked twice is a missing page.

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
