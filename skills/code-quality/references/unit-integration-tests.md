# Unit and integration tests

Read this when: writing tests for business logic, SQLx queries, Axum routes or Leptos
components, deciding what to fake, covering failure paths, or the suite has become slow to run
or to compile.

## Unit tests for business logic

A unit test here means: no I/O, no clock, no randomness, runs in milliseconds, fails only when
behavior changes; if the code cannot meet that, restructure it (test-strategy.md) instead of
faking around it. It lives in a `#[cfg(test)] mod tests` beside the code; reaching private
items there is a convenience, not an invitation to test private helpers one by one.

- **Test behavior through the public function, one behavior per test.** Name the test as a
  rule of the domain: `prorates_mid_cycle_upgrade_by_remaining_days`, not `test_calculate`.
- **Table-driven cases for rules.** Edges get one row each: zero, one, boundary, boundary + 1,
  maximum, empty, duplicate, Unicode, DST change, month end, leap day. Put the input in the
  assertion message so a failing row names itself:

```rust
#[test]
fn volume_tier_starts_at_seat_eleven() {
    let cases = [(0, 0), (1, 1_200), (10, 12_000), (11, 12_000 + 1_000)];
    for (seats, expected) in cases {
        assert_eq!(seat_price_cents(seats), expected, "seats = {seats}");
    }
}
```

- **Assert on values, not interactions.** `assert_eq!` on a returned value survives
  refactoring; mock expectations on call order rarely do. Reserve interaction checks for
  effects that are the behavior (an email was requested exactly once).
- **No logic in tests.** No loops computing the expected value with the same formula as the
  code; write the expected literal.
- **Money in integer minor units** (`i64` or `u64` cents), never `f64`, with `checked_*`
  arithmetic: overflow panics in debug and wraps silently in release (static-analysis-types.md).
- **Snapshots only for small, stable, reviewed output** (an error message, a generated SQL
  fragment): insta, reviewed with `cargo insta review`; in CI it fails instead of writing.

## Integration tests against a real database

Mocking the database tests the mock. The defects that matter (wrong join, missing tenant
filter, constraint violation, transaction that does not roll back, migration drift, N+1) only
appear against the real engine, of the same major version as production; SQLite standing in
for Postgres hides differences in types, constraints, locking, JSON and time zones.

Setup that works for one developer and CI alike: Postgres started once per run (a Compose
service, a CI service container, or the `testcontainers` crate); `DATABASE_URL` pointing at it
with a role allowed to create databases; and `#[sqlx::test]`, which gives each test a fresh
database with the crate's `migrations/` applied (so the production migrations are tested on
every run) and a `PgPool` to it. Migrations kept in another crate are named with
`#[sqlx::test(migrator = "db::MIGRATOR")]`. Each test creates the rows it needs (factories,
test-data-flaky.md); SQL fixture files are the shared-fixture trap in another form. Here
`find_invoice(pool, org_id, id)` is the code under test, filtering on both columns:

```rust
#[sqlx::test] // a fresh database for this test, with ./migrations applied
async fn invoice_of_another_tenant_is_not_found(pool: PgPool) -> sqlx::Result<()> {
    let (org_a, org_b) = (Uuid::new_v4(), Uuid::new_v4());
    sqlx::query("INSERT INTO orgs (id, name) VALUES ($1, 'a'), ($2, 'b')")
        .bind(org_a)
        .bind(org_b)
        .execute(&pool)
        .await?;
    let invoice_b: Uuid = sqlx::query_scalar(
        "INSERT INTO invoices (org_id, amount_cents) VALUES ($1, 4900) RETURNING id",
    )
    .bind(org_b)
    .fetch_one(&pool)
    .await?;

    assert_eq!(find_invoice(&pool, org_a, invoice_b).await?, None);
    assert_eq!(find_invoice(&pool, org_b, invoice_b).await?, Some(4900));
    Ok(())
}
```

Assert at this layer: the row state after the operation, that constraints reject bad writes,
that a failure midway leaves nothing behind, that a query scoped to tenant A returns nothing of
tenant B, and that list queries keep a constant statement count as rows grow (capture SQLx's
per-statement tracing events to catch N+1). Speed levers before mocks: one Postgres server per
run; `fsync=off` on a throwaway test server only; and since every test applies every
migration, squash old migrations once there are hundreds.

## Axum routes through the router

Test the route as a client sees it: method, path, headers, cookies, body in; status, headers,
body out. Calling the service function directly skips the parts that break: extractors,
middleware, auth, validation, serialization, error mapping. An Axum `Router` with its layers
is a tower `Service`, so `oneshot` drives a request through all of it in process, no port:

```rust
use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode, header};
use sqlx::PgPool;
use tower::ServiceExt; // `oneshot`: tower with the "util" feature in dev-dependencies

#[sqlx::test]
async fn invoice_routes_enforce_session_and_tenant(pool: PgPool) {
    let app = router(AppState::for_tests(pool.clone()));
    let (user_a, invoice_b) = test_support::tenant_a_user_and_tenant_b_invoice(&pool).await;

    // No session: 401.
    let req = Request::get("/api/invoices").body(Body::empty()).unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::UNAUTHORIZED);

    // Tenant A's session asking for tenant B's invoice: 404, and no internals in the body.
    let cookie = test_support::session_cookie(&pool, user_a).await;
    let req = Request::get(format!("/api/invoices/{invoice_b}"))
        .header(header::COOKIE, cookie)
        .body(Body::empty())
        .unwrap();
    let res = app.clone().oneshot(req).await.unwrap();
    assert_eq!(res.status(), StatusCode::NOT_FOUND);
    let body = to_bytes(res.into_body(), 64 * 1024).await.unwrap();
    assert!(!String::from_utf8_lossy(&body).contains("SELECT"));
}
```

`router`, `AppState` and `test_support` are the app's own code; build the router with the
function `main` uses, so the test sees the production layers. Traps: `oneshot` consumes the
service, so clone the router per request (cheap); a handler using `ConnectInfo` fails unless
the test adds a `MockConnectInfo` layer; what happens outside the router (TLS, the proxy,
`axum::serve` settings) needs one smoke test against the running binary. Create sessions
through the app's own session code; do not stub the auth layer, it is the thing under test.
Leptos server functions are routes too: test them through the same router.

Per route, the matrix that catches real defects:

| Case | Expect |
|---|---|
| Valid request, owner | 2xx, body deserializes into the documented response type |
| No credentials | 401, no data in body |
| Valid user, wrong role | 403 |
| Valid user, another tenant's resource ID | 404 (or 403), and the row is unchanged |
| Invalid body, missing field, wrong type, oversized payload | 400, 413 or 422 with the standard error shape; nothing written |
| Not found | 404 with the error shape |
| Conflict or repeat with the same idempotency key | 409, or the original response replayed |
| Dependency failure (faked) | 5xx or 503 with a generic message, no SQL, error text or panic message in body |

Assert the database state after mutating calls, not only the response. A 200 that wrote
nothing, or a 500 that wrote half, are the bugs.

## What to fake

Fake at the boundary of the system, not inside it. Inside the boundary, use the real thing.

| Dependency | In tests use | Why |
|---|---|---|
| Own modules, services, repositories | The real code | Faking them freezes the design and hides integration bugs |
| Clock, randomness, ID generation | Injected or paused (test-data-flaky.md) | Determinism |
| Third-party HTTP APIs (payments, email, LLM, maps) | A local fake HTTP server (wiremock) returning recorded responses | The app's real client code, serialization and error handling run |
| Queue, cache | The real one if cheap to start (Postgres-backed queue, Redis container); otherwise an in-memory implementation of the app's own trait | |
| Filesystem, object storage | A temp directory; an S3-compatible container or the app's storage trait in memory | |

The vendor client takes its base URL from config, so the test points it at a wiremock server.
Fragment: `MailClient` builds a reqwest client with timeouts and calls `error_for_status()`, so
a request the fake does not match, which wiremock answers with 404, fails instead of passing:

```rust
#[tokio::test]
async fn receipt_is_sent_once_to_the_customer() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/send"))
        .and(header("authorization", "Bearer test-key"))
        .and(body_partial_json(json!({ "to": "a@example.test" })))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({ "id": "msg_1" })))
        .expect(1) // checked when `server` drops: zero calls or two calls fail the test
        .mount(&server)
        .await;

    let mail = MailClient::new(server.uri(), "test-key".into()).unwrap();
    assert_eq!(mail.send_receipt("a@example.test").await.unwrap(), "msg_1");
}
```

Recorded responses: capture real responses from the vendor's sandbox once, strip secrets and
personal data, commit them as JSON fixtures with the capture date and API version. Fakes
drift: a scheduled job (weekly) calls the real sandbox with the same requests and checks the
responses still deserialize. Sign webhook fixtures with a test secret through the app's own
verification code. A mocking crate (mockall) is for a trait boundary with no wire to fake.

## Leptos components

Test what a user can perceive and do, at two layers. Server rendering, in a plain `#[test]`:
`view! { <InvoiceStatus paid=false/> }.to_html()` returns the HTML string; assert that it
contains the text, roles and attributes (`role="status"`, "Payment due"). Native, no browser.

Interaction (clicks, signals, effects), with wasm-bindgen-test in a headless browser; imports
and the `Counter` component are left out:

```rust
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
async fn click_updates_the_label() {
    // Every test in the binary shares one page: mount into a fresh container and keep
    // the handle, which unmounts the view when it drops at the end of the test.
    let container: HtmlElement = document().create_element("div").unwrap().unchecked_into();
    document().body().unwrap().append_child(&container).unwrap();
    let _view = mount_to(container.clone(), Counter);

    let button: HtmlElement = container.query_selector("button").unwrap().unwrap().unchecked_into();
    button.click();
    leptos::task::tick().await; // let the reactive system flush before reading the DOM
    assert_eq!(button.text_content().as_deref(), Some("Clicked 1"));
}
```

Run it with `cargo test --target wasm32-unknown-unknown` and `wasm-bindgen-test-runner` as the
target's runner. Traps: `wasm-bindgen-cli` must be the exact `wasm-bindgen` version in
`Cargo.lock`; without `run_in_browser` the tests run in Node; the runner needs chromedriver or
geckodriver; gate the file with `#![cfg(target_arch = "wasm32")]` so native `cargo test` skips
it. Assert on text, roles and labels, not signal values or class names. Worth a test: real
conditional logic, form validation, keyboard interaction, loading, empty and error states;
layout, focus order and hydration belong to end-to-end tests (`0x:rust-frontend`).

## Failure paths

Happy paths are where the tests are; production incidents are in the other paths. For each
operation that crosses a boundary, write these:

| Path | How to force it | Assert |
|---|---|---|
| Timeout | wiremock `ResponseTemplate::set_delay` beyond the client timeout | Gives up at the configured time; retryable error to the user; nothing half-written |
| Retry | A 503 mock with `.up_to_n_times(2)` mounted before the success mock | Exactly three attempts, backoff respected (paused Tokio time, test-data-flaky.md), the same idempotency key each time |
| Non-retryable error | Fake returns 400 or 402 | No retry; mapped to a domain error variant |
| Partial write | Make the second of two writes fail | Transaction rolled back, or the compensating step ran; consistent on re-read |
| Duplicate delivery | Deliver the same webhook or job twice | State changes once |
| Out-of-order delivery | Deliver event 2 before event 1 | Final state correct, stale event ignored |
| Concurrency | A `JoinSet` of 20 calls against the real database (debugging.md) | One winner, no oversell, no duplicate row; run it 20 times or more |
| Crash between steps | Return an error or panic after the external call, before the local commit | Re-running converges and does not double-charge |
| Cancellation | Drop the future mid-way (`tokio::time::timeout` around it) | Nothing half-written: a dropped future stops at its current `.await` |

`#[tokio::test]` and `#[sqlx::test]` run on a single-threaded runtime: database races across
connections still show, but in-process races between tasks need
`#[tokio::test(flavor = "multi_thread", worker_threads = 4)]`.

## Keeping the suite fast

Targets: one test re-run in seconds; the unit and integration suite in a few minutes in CI,
compile included. In Rust, compiling and linking usually cost more than running.

- **One integration-test binary.** Each file in `tests/` links as its own binary; put them in
  `tests/it/main.rs` with modules beside it, and twenty links become one.
- **cargo-nextest** runs each test in its own process, in parallel, and reports slow and flaky
  tests. It skips doctests, so CI also runs `cargo test --doc`.
- **Cheaper debug builds:** `debug = "line-tables-only"` in `[profile.dev]` and a fast linker
  (lld or mold) cut link time. Code that is slow unoptimized (argon2, image work) gets cheap
  parameters in test config, or `opt-level = 3` for that one package in the dev profile.
- **Few dev-dependencies**: each compiles into every test build.
- **Run what changed locally** (`cargo nextest run -p billing`, or a name filter); CI runs
  everything, sharded past about 10 minutes (test-data-flaky.md), with a build cache
  (`0x:ci-cd-release`). No real waiting anywhere: paused Tokio time for delays and backoff.

## Property-based tests

Use when the input space is large and a rule holds for all inputs: parsers and serializers,
money arithmetic, date ranges, sorting and pagination, permission lattices, state machines,
anything with an encode and a decode. proptest generates inputs from strategies, finds a
failure and shrinks it: in `proptest! { #[test] fn split_keeps_cents(cents in 0u64..10_000_000,
parts in 1u32..50) { ... } }`, `prop_assert_eq!` that the shares sum to `cents`.

Property shapes that find bugs: round trip (`parse(format(x)) == x`), invariants (sum
preserved, never negative, sorted stays sorted), idempotence, comparison with a slow obvious
implementation, and "no input panics". Generators too narrow never reach the bug; too wide
spend the budget on rejected inputs. Commit the `proptest-regressions/` files proptest writes,
and copy the shrunk case into an example test. Parsers of untrusted input deserve fuzzing too
(cargo-fuzz, which needs a nightly toolchain).

## Mutation testing

cargo-mutants changes the code (a function body replaced by a default value, a comparison or
arithmetic operator swapped, a `!` deleted) and reruns the tests; a mutant nobody catches is
behavior no assertion checks, which coverage cannot show. Scope it to critical modules with
`--file`, since every mutant needs a build; run it on demand or nightly, `--in-diff` for
changed code only. Per missed mutant: add a boundary case or assertion, or accept it as
equivalent. Do not chase 100%; on money and permissions, chase every missed operator mutant.

## Ask the user

- **May tests call any third party's sandbox, or must they be fully offline?** Offline is
  faster and deterministic. Assume offline with recorded fakes, plus a scheduled drift check.
- **Is Docker available locally and in CI?** Decides testcontainers versus a CI service
  container or a hosted branch database. Assume Docker is available.
- **Which operations must never run twice or half-run?** These get the full failure-path table.
  Assume charging, sending email, provisioning and deleting.
- **Is there a multi-tenant or role model?** If yes, the cross-tenant and wrong-role rows are
  mandatory for every route. Assume yes when any row carries an owner or organization ID.
