# Static analysis, lints, types and unsafe policy

Read this when: setting up or tightening clippy, rustfmt, workspace lints or pre-commit hooks;
deciding the unsafe policy; designing types so invalid states do not compile; finding unused
dependencies and dead code; making query or API drift fail the build; enforcing crate
boundaries.

## What each check is for

Assign each defect class to the earliest tool that can reject it, and do not duplicate.

| Tool | Catches | Runs |
|---|---|---|
| rustc (`cargo check`) | Types, ownership and lifetimes, non-exhaustive `match`, futures that are not `Send` across `.await`, ignored `Result` and futures (`#[must_use]`), dead private code | Editor (rust-analyzer), CI |
| clippy | Panicking patterns, lossy casts, locks held across `.await`, suspicious code the compiler accepts | Editor, CI with warnings denied |
| rustfmt | Nothing; it removes style from review and diffs | On save, pre-commit, CI in check mode |
| SQLx macros (`query!`, `query_as!`) | SQL that does not match the schema: wrong column, type or nullability | Every build, offline in CI |
| Unused-dependency tools, `cargo tree` | Dependencies and features nothing uses, duplicate crate versions | CI |
| The crate graph and visibility | Architecture violations | Every build |

Enforcement lives in CI as required checks (`0x:ci-cd-release`); editors and hooks only give
faster feedback. `cargo deny` for licenses and advisories is in `0x:web-security`.

## The CI gate

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
```

Traps:

- **`--all-targets` or tests rot.** Without it, clippy skips tests, examples and benches.
- **Code behind a feature or target is not checked at all** unless that configuration is
  built. A Leptos app has two: lint the server (`--features ssr`) and the client
  (`--features hydrate --target wasm32-unknown-unknown`) separately, since `--all-features`
  turns both on at once and a native build never sees the WASM-only code. Libraries with many
  features: `cargo hack check --each-feature`.
- **Deny warnings on the command line, not in `RUSTFLAGS`.** `RUSTFLAGS="-D warnings"`
  changes the compiler flags for every dependency, invalidates the build cache and rebuilds
  the world; arguments after `--` apply only to the workspace.
- **A new toolchain brings new lints.** With `-D warnings`, an unpinned toolchain breaks CI on
  release day. Pin it in `rust-toolchain.toml` and bump it deliberately (refactoring.md).
- **Keep lint levels at `warn` in the config and deny in CI.** A half-finished edit still
  compiles and its tests still run locally; main stays at zero warnings.

## Workspace lints, one place

```toml
# Cargo.toml at the workspace root. Every member crate adds:  [lints] workspace = true
[workspace.lints.rust]
unsafe_code = "forbid"
unused_must_use = "deny"

[workspace.lints.clippy]
unwrap_used = "warn"
expect_used = "warn"
indexing_slicing = "warn"
panic = "warn"
todo = "warn"
unimplemented = "warn"
dbg_macro = "warn"
cast_possible_truncation = "warn"
cast_sign_loss = "warn"
cast_possible_wrap = "warn"
let_underscore_must_use = "warn"
let_underscore_future = "warn"
wildcard_enum_match_arm = "warn"
allow_attributes = "warn"
allow_attributes_without_reason = "warn"
undocumented_unsafe_blocks = "warn"
await_holding_lock = "deny"
```

```toml
# clippy.toml at the workspace root: tests may unwrap, index and panic
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-indexing-slicing-in-tests = true
allow-panic-in-tests = true
allow-dbg-in-tests = true
```

A member crate without `[lints] workspace = true` silently gets none of this; check for the
line in CI with a grep over the members' `Cargo.toml` files. Lint groups such as
`clippy::pedantic` need `priority = -1` (`pedantic = { level = "warn", priority = -1 }`) so
single lints can override the group; pedantic suits greenfield code, with noisy members allowed.

## The lints that prevent real defects

Most lints are taste. These correspond to production bugs.

| Pattern | Why it bites | Lint or remedy |
|---|---|---|
| `unwrap()` or `expect()` in a request path | The panic kills that request's task; the client sees a dropped connection or, with tower-http's `CatchPanicLayer`, a 500; with `panic = "abort"` the whole server dies | `unwrap_used`, `expect_used`; return an error mapped once to a status |
| Indexing and slicing (`v[i]`, `&s[..n]`) | Panics out of range; slicing a `str` panics mid-character | `indexing_slicing`, `string_slice`; use `get` |
| `as` between integer types | Silently truncates or flips sign: `-1_i64 as u64` is 18446744073709551615 | `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap`; use `try_from` |
| Integer overflow in money math | Panics in debug builds, wraps silently in release | `checked_*` methods, `overflow-checks = true` in `[profile.release]`, `arithmetic_side_effects` on money modules |
| A discarded `Result` or future | `let _ = send_receipt()` drops the error; a future never awaited never runs | `unused_must_use` (rustc), `let_underscore_must_use`, `let_underscore_future` |
| A `std::sync::Mutex` guard held across `.await` | Deadlock, or a future that is not `Send` and will not spawn | `await_holding_lock`; drop the guard before awaiting, or use the async mutex |
| `_ =>` over the project's own enum | A new variant falls into the default arm without a compiler error | `wildcard_enum_match_arm` |
| `todo!()`, `unimplemented!()`, `dbg!` shipped | A panic or stderr noise in production | `todo`, `unimplemented`, `dbg_macro` |
| `#[allow]` that outlives its reason | Hides the next real warning on that item | `allow_attributes`, `allow_attributes_without_reason`; use `#[expect]` |
| Blocking calls in async code (`std::fs`, `std::thread::sleep`, sync clients, heavy CPU) | Stalls every task on that runtime worker | No reliable lint; review, and tokio-console (debugging.md); `spawn_blocking` |

Where a panic is the right answer (startup config that must exist, an invariant the code just
checked), say so at the site with `#[expect]`, which also warns once the lint no longer fires,
so suppressions cannot go stale. `expect("DATABASE_URL must be set")` in `main` is correct;
the same call in a handler is a bug:

```rust
pub fn first_word(words: &[String]) -> &str {
    if words.is_empty() {
        return "";
    }
    #[expect(clippy::indexing_slicing, reason = "emptiness checked above")]
    &words[0]
}
```

## Types that make invalid states fail to compile

A check the compiler performs never needs a test and never regresses. Two tools carry most of
the weight:

```rust
/// The field is private: the only way to get an `Email` is `parse`, so every one is valid.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(try_from = "String")]
pub struct Email(String);

#[derive(Debug, thiserror::Error)]
#[error("invalid email address")]
pub struct InvalidEmail;

impl Email {
    pub fn parse(raw: &str) -> Result<Self, InvalidEmail> {
        let s = raw.trim().to_lowercase();
        match s.split_once('@') {
            Some((local, domain)) if !local.is_empty() && domain.contains('.') => Ok(Self(s)),
            _ => Err(InvalidEmail),
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for Email {
    type Error = InvalidEmail;
    fn try_from(s: String) -> Result<Self, Self::Error> {
        Self::parse(&s)
    }
}

/// Each state carries only the data that exists in it: an active plan has no `canceled_at`.
pub enum Subscription {
    Trialing { trial_ends: OffsetDateTime },
    Active { price_cents: u64, period_end: OffsetDateTime },
    PastDue { since: OffsetDateTime, attempts: u8 },
    Canceled { at: OffsetDateTime },
}
```

- **Newtypes with a private field and one constructor** for IDs, money, emails, slugs and
  anything validated. `#[serde(try_from = ...)]` makes deserialization go through the same
  constructor, so a request body cannot smuggle in an invalid value. Validate structure at the
  boundary with garde, then convert into newtypes: parse once, do not validate twice.
- **Enums whose variants carry their own data** instead of a struct of `Option` fields and a
  status string. Matching forces every caller to handle each state.
- Distinct ID types (`OrgId(Uuid)`, `UserId(Uuid)`) stop the swapped-argument bug in
  `find_invoice(user_id, org_id)` at compile time; it is the cheapest tenant-isolation check
  there is.
- Skip typestate generics and phantom types in application code until misuse has happened;
  they cost readability everywhere.

## Unsafe policy

Application crates contain no `unsafe`: `unsafe_code = "forbid"` above, and `forbid` cannot be
re-allowed further down. Web products almost never need it, and every `unsafe` block is code
the compiler stops checking.

When a reviewed need exists (FFI to a C library, a measured hot path): put the `unsafe` code in
one small dedicated crate. That crate cannot inherit the workspace lints (a `forbid` cannot be
lifted), so it carries its own `[lints]` table with `unsafe_code = "deny"` and
`undocumented_unsafe_blocks`, every block carries a `// SAFETY:` comment stating the invariant
it relies on, the crate has an owner in CODEOWNERS, and CI runs its tests under Miri
(`cargo +nightly miri test -p <crate>`) where Miri supports the code (it cannot run FFI calls).
Dependencies use `unsafe` internally; choose widely used, maintained crates, and treat a new
dependency with heavy `unsafe` as a review item (supply chain in `0x:web-security`). Edition
2024 made `std::env::set_var` and `remove_var` `unsafe`, because other threads may read the
environment concurrently; application code that needs them is setting configuration the
wrong way.

## Pre-commit hooks that stay on

A hook that takes more than a few seconds gets bypassed with `--no-verify`, and then it
protects nothing. Budget: under about 3 seconds for a typical commit.

- Run `cargo fmt --all --check` (fast; it does not compile) and a secret scanner on staged
  changes: a leaked key is the one mistake that cannot be fixed after push (`0x:web-security`).
- Do not run clippy or tests in pre-commit. Both compile; a cold clippy run takes minutes. If a
  local gate is wanted, put `cargo clippy` and the changed crate's tests on pre-push.
- Install without Node: hooks committed in `.githooks/` and `git config core.hooksPath
  .githooks` in the setup script, or a standalone hook manager (lefthook). Clones and agent
  sessions that skip setup run without hooks, so CI repeats every hook check.

## Tightening lints in a legacy codebase

Turning on the table above in an old codebase produces hundreds of warnings. Fixing them in one
branch stalls; make the count a ratchet that only goes down.

| Approach | How | Use when |
|---|---|---|
| Lint by lint | Enable one lint, fix (`cargo clippy --fix` handles the machine-applicable ones), merge, next. Order: `unwrap_used` and `indexing_slicing` in request paths, then casts, then the rest | Few hundred sites per lint |
| Crate by crate | New and cleaned crates opt into the strict table; legacy crates keep a looser `[lints]` table until cleaned | A workspace with several crates |
| Suppress and burn down | Enable the lints, put `#[expect(lint, reason = "legacy, ticket 123")]` on each existing site by script, remove them over time; `#[expect]` warns when its lint no longer fires, so fixed sites cannot keep a stale suppression | Want one config today |

Rules for all three: new code is strict from day one; never loosen a lint once on; track the
count of `#[expect(` and `#[allow(` with a grep in CI and fail if it rises; fix by module,
starting with money, auth and data access, where a panic or a wrapped integer costs most.

## Unused dependencies, features and dead code

- **Dead code:** rustc's `dead_code` warning covers private items only. `pub` in a library
  crate counts as used, so default to `pub(crate)`, and enable the `unreachable_pub` lint on
  library crates to find items marked `pub` that nothing outside reaches.
- **Unused dependencies:** cargo-machete is fast and works on stable but reads source text, so
  crates used only through macros or renamed show as false positives; list them under
  `[package.metadata.cargo-machete] ignored`. cargo-udeps is precise but needs nightly and a
  full build; run it occasionally. Never remove a dependency on the tool's word without a build.
- **Features and duplicates:** `cargo tree -e features -i <crate>` shows who turns a feature
  on; `cargo tree -d` lists crates present in two versions, which cost compile time and can
  cause type mismatches (refactoring.md).
- **Cycles:** Cargo forbids cycles between crates (dev-dependencies aside), and modules inside
  a crate have no load order, so the run-time cycle bugs of module systems with import-time
  evaluation do not exist. A tangle of modules is still a design smell; split it by crate.

## Compile-time checked queries and schemas

Hand-written types that mirror a database or an API drift, and the compiler then vouches for a
shape that no longer exists. Each external shape gets one source of truth.

| Shape | Source of truth | Derived and checked |
|---|---|---|
| Database tables | The migrations in the repository | SQLx `query!` and `query_as!` check every statement against the migrated schema at compile time; `.sqlx/` offline data lets CI build without a database |
| Own HTTP API | The handler types | The OpenAPI document generated from them (utoipa), committed |
| Leptos server functions | The function signature | Shared by client and server in the same workspace; nothing to generate |
| Third-party API | The vendor's OpenAPI document or documented payloads | Generated client types (progenitor) or serde structs from recorded responses; never trusted without run-time parsing |
| Environment variables | One config struct parsed at startup | A missing or malformed variable fails at boot, not at first use |

The enforcement step in CI: regenerate and fail if anything changed.

```bash
cargo sqlx prepare --workspace --check    # queries or schema changed without regenerating .sqlx/
cargo run --quiet --bin gen-openapi > openapi.json && git diff --exit-code openapi.json
```

Traps: `sqlx::query(...)` the function is not checked, only the macros are; keep the function
for genuinely dynamic SQL. Set `SQLX_OFFLINE=true` in CI so a stray `DATABASE_URL` cannot make
the build depend on a live database. A generated type describes what was promised, not what
arrived: keep run-time validation at trust boundaries (external responses, webhooks, form
input, JSON columns).

## Architecture boundaries as crate dependencies

Layering that exists only in a diagram erodes one convenient import at a time. In Rust the
crate graph is the enforcement: a crate cannot use what its `Cargo.toml` does not list. Skip
this at Prototype (one crate is fine); split at Launch when compile times or boundaries hurt.
Separate crates also compile in parallel and rebuild independently.

Rules worth enforcing in a typical web product:

- The domain crate depends on no web framework, database or HTTP client crate, which keeps it
  testable without them.
- Server-only dependencies (SQLx, secrets, vendor clients) are optional and enabled only by the
  `ssr` feature, with the code using them behind `#[cfg(feature = "ssr")]` or inside server
  function bodies, so the WASM client cannot link them; one that leaks in either fails to build
  for `wasm32` or bloats the bundle (`0x:rust-frontend`).
- Only one crate depends on each vendor SDK or client (one wrapper per third party).
- Inside a crate, modules expose a small `pub` surface; the rest is private or `pub(crate)`.

Check the graph in CI: `cargo tree -e normal -i sqlx` must list only the allowed dependents.
Start with two or three rules that match how the code is already organized; a rule set
describing an aspirational architecture fails on day one and gets disabled. Prove each rule
by adding a violating dependency once and seeing the check fail.

## Ask the user

- **Is there an existing lint or format setup the team is attached to?** Changing it costs
  churn in every open branch. Assume keep what exists; on greenfield take the table above.
- **How much time can go to lint cleanup in an old codebase?** Decides lint-by-lint versus
  suppress-and-burn-down. Assume none up front: strict for new crates, ratchet in CI.
- **Should a failing lint or check block merging and deploys, with no override?** It must for
  the checks to mean anything. Assume yes, with rollback as the emergency path, not bypass.
- **Is there a reviewed need for `unsafe` (a C library, a measured hot path)?** Assume no.
- **Who else consumes the API or database schema (mobile app, partners, analytics)?** Decides
  where generated documents and drift checks are needed. Assume only this repository.
