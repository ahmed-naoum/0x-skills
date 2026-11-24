# Build tooling, WASM size and deployment

Read this when: setting up or debugging cargo-leptos, wasm-bindgen, wasm-opt or the Tailwind CLI;
the build fails on the WASM side or with both features on; the WASM is too big or rebuilds are
slow; environment variables are missing or leaked; or deploying the server binary and its site
assets.

## One app crate, two builds

cargo-leptos compiles the same crate twice: the library for `wasm32-unknown-unknown` with the
`hydrate` feature, and the binary for the server with `ssr`. Server-only crates are optional and
enabled only by `ssr`, so the WASM build never sees them. Start from the official
`start-axum` template (`cargo leptos new --git https://github.com/leptos-rs/start-axum`) and
change as little as possible; a workspace version of the template splits app, frontend and server
crates when the app grows.

```toml
[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
leptos = "0.8"
leptos_router = "0.8"
leptos_meta = "0.8"
leptos_axum = { version = "0.8", optional = true }
axum = { version = "0.8", optional = true }
tokio = { version = "1", features = ["rt-multi-thread", "macros"], optional = true }
tower-http = { version = "0.7", features = ["limit"], optional = true }
sqlx = { version = "0.9", default-features = false, features = ["runtime-tokio", "tls-rustls", "postgres", "macros", "uuid", "time"], optional = true }
wasm-bindgen = { version = "0.2", optional = true }
console_error_panic_hook = { version = "0.1", optional = true }
web-sys = { version = "0.3", features = ["Storage"] } # browser APIs used in components: not optional

[features]
hydrate = ["leptos/hydrate", "dep:wasm-bindgen", "dep:console_error_panic_hook"]
ssr = ["leptos/ssr", "leptos_meta/ssr", "leptos_router/ssr", "dep:leptos_axum", "dep:axum", "dep:tokio", "dep:tower-http", "dep:sqlx"]

[profile.wasm-release]
inherits = "release"
opt-level = "z"
lto = true
codegen-units = 1
panic = "abort"

[package.metadata.leptos]
output-name = "app"
site-root = "target/site"
site-pkg-dir = "pkg"
tailwind-input-file = "style/tailwind.css"
assets-dir = "public"
site-addr = "127.0.0.1:3000"
reload-port = 3001
bin-features = ["ssr"]
bin-default-features = false
lib-features = ["hydrate"]
lib-default-features = false
lib-profile-release = "wasm-release"
hash-files = true
```

- No `default` features. `default = ["ssr"]` turns `ssr` on in the WASM build too.
- `hash-files = true` puts a content hash in the WASM, JS and CSS file names, so those files can be
  cached forever and a page never loads another build's WASM.
- `cargo leptos watch` for development, `cargo leptos build --release` for production,
  `cargo leptos end-to-end` for browser tests against a running build. It runs `end2end-cmd`,
  which the template sets to `npx playwright test`; point it at a Rust WebDriver test crate
  (thirtyfour) unless the founder accepted Playwright and its Node toolchain.

The server entry, called from `main`:

```rust
use axum::Router;
use leptos::config::get_configuration;
use leptos_axum::{generate_route_list, LeptosRoutes};
use tower_http::limit::RequestBodyLimitLayer;

pub async fn serve(cfg: Config) -> anyhow::Result<()> {
    let leptos_options = get_configuration(None)?.leptos_options;
    let addr = leptos_options.site_addr;
    let pool = sqlx::postgres::PgPoolOptions::new().max_connections(10).connect(&cfg.database_url).await?;
    let routes = generate_route_list(App);
    let app = Router::new()
        .leptos_routes_with_context(
            &leptos_options,
            routes,
            { let pool = pool.clone(); move || provide_context(pool.clone()) }, // server functions get it
            { let options = leptos_options.clone(); move || shell(options.clone()) },
        )
        .fallback(leptos_axum::file_and_error_handler(shell)) // serves target/site files
        // server functions read the raw body: DefaultBodyLimit would not cap them, this does
        .layer(RequestBodyLimitLayer::new(256 * 1024))
        // ... plus the session, same-origin, timeout and catch-panic layers (server-functions.md)
        .with_state(leptos_options);
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?; // add .with_graceful_shutdown(...) for rolling deploys
    Ok(())
}

pub fn shell(options: LeptosOptions) -> impl IntoView {
    view! {
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                <AutoReload options=options.clone()/>
                <HydrationScripts options=options.clone()/>
                <leptos_meta::HashedStylesheet options id="leptos"/> // hashed name from hash.txt
                <leptos_meta::MetaTags/>
            </head>
            <body><App/></body>
        </html>
    }
}
```

The hydrate entry (`#[wasm_bindgen] pub fn hydrate()` with the panic hook) is in `hydration.md`.
Context given to `leptos_routes_with_context` reaches components and the server functions it
registers; a server function route registered separately needs `handle_server_fns_with_context`
with the same context.

## Environment variables: build time and runtime

| Value | Read when, by what | How |
|---|---|---|
| Server secrets and config (database URL, API keys, public origin) | Runtime, server | Parsed once at startup into a typed config struct that fails fast on a missing value; provided as context |
| `LEPTOS_SITE_ADDR`, `LEPTOS_SITE_ROOT`, `LEPTOS_ENV`, `LEPTOS_SITE_PKG_DIR`, `LEPTOS_HASH_FILES` | Runtime, `get_configuration` | Override `Cargo.toml` metadata; the container sets them because `Cargo.toml` is not in the image |
| `LEPTOS_OUTPUT_NAME` | Build time, compiled into the server with `option_env!` | Set by cargo-leptos. A binary built with plain `cargo build` lacks it and fails at startup |
| Public client values (analytics key, Stripe publishable key) | Build time if read with `env!` in shared code | Every value compiled into the WASM is public. To promote one image across environments, deliver them at runtime instead: a server function or a resource that reads server config |
| Anything secret in shared code | Never | `env!("STRIPE_SECRET")` in code the WASM build compiles puts the secret in the WASM |

Check after every release build, for each server secret's value and for well-known secret shapes:

```bash
grep -rlF -- "$DATABASE_URL" target/site; grep -rlaE "sk_live_|PRIVATE KEY" target/site   # both print nothing
```

Storing and rotating secrets: `0x:web-security`. Config per environment: `0x:ci-cd-release`.

## Tailwind without Node

cargo-leptos runs the Tailwind standalone CLI on `tailwind-input-file` and writes the result to
`/pkg/<output-name>.css`, downloading the binary on first use; there is no `package.json`.

```css
@import "tailwindcss";
@source "../src";

@theme {
  --color-primary: oklch(0.55 0.2 260);
  --color-primary-foreground: oklch(0.98 0 0);
}
```

- `@source` tells Tailwind 4 to scan the Rust files for class names. Classes assembled at runtime
  (`format!("bg-{c}-500")`) are never found; write complete class strings in code
  (`components-reactivity.md`).
- Pin the Tailwind version through cargo-leptos's documented environment variable
  (`LEPTOS_TAILWIND_VERSION`) in CI and the image, so a new major does not arrive with a rebuild.
- With `hash-files = true`, link the CSS through `HashedStylesheet` (the shell above), which reads
  the hashed name; a hard-coded `/pkg/app.css` returns 404.

## Deploy one binary and its site directory

The deployable unit is the server binary plus `target/site` (WASM, JS glue, CSS, assets). Image
conventions, static versus glibc builds and base images: `0x:cloud-infrastructure`. What is
specific to Leptos:

```dockerfile
FROM rust:1-bookworm AS build
ARG CARGO_LEPTOS_VERSION
WORKDIR /app
COPY rust-toolchain.toml .
RUN rustup toolchain install && cargo install cargo-leptos --locked --version "$CARGO_LEPTOS_VERSION"
COPY . .
RUN cargo leptos build --release

FROM gcr.io/distroless/cc-debian12:nonroot
WORKDIR /app
# the binary is named after the package (here `app`), not after output-name
COPY --from=build /app/target/release/app /app/app
COPY --from=build /app/target/release/hash.txt /app/hash.txt
COPY --from=build /app/target/site /app/site
ENV LEPTOS_SITE_ROOT=site LEPTOS_SITE_ADDR=0.0.0.0:8080 LEPTOS_ENV=PROD LEPTOS_HASH_FILES=true
EXPOSE 8080
CMD ["/app/app"]
```

- Build the server and the WASM in the same build, at the same path. The default server function
  URL hashes the crate's path and module, so a WASM built elsewhere calls URLs the server does not
  have ("Could not find a server function at the route"). `SERVER_FN_OVERRIDE_KEY` at build time
  replaces the path when the builds must differ.
- With `hash-files`, the server reads `hash.txt` from its own executable's directory, and only
  when `LEPTOS_HASH_FILES=true`. cargo-leptos sets that variable for `watch` and `serve`; the image
  must set it. Without the variable, pages link unhashed names that do not exist and nothing
  hydrates; without the file, rendering panics ("failed to read hash file").
- Hashed files under `/pkg` get `Cache-Control: public, max-age=31536000, immutable` (a tower-http
  `SetResponseHeader` layer, or the CDN); HTML gets the page's own policy
  (`rendering-strategies.md`).
- Rolling deploys: an open tab keeps its old WASM and calls the new server. Change server function
  arguments additively (new arguments with `#[server(default)]`), and keep the previous build's
  `/pkg` files reachable for a while through the CDN.
- Proxies in front must not buffer HTML, or streaming SSR stops streaming.
- Send SIGTERM and allow a 10 to 30 second drain with Axum's graceful shutdown, so in-flight
  responses and streams finish.

## A size-optimized WASM

Measure first, then cut:

```bash
cargo leptos build --release
ls -l target/site/pkg/*.wasm && gzip -9c target/site/pkg/*.wasm | wc -c   # what users download
```

- The `wasm-release` profile above (`opt-level = "z"`, LTO, one codegen unit, abort on panic) is
  the baseline; try `opt-level = "s"` too and keep whichever measures smaller for this app.
- cargo-leptos runs `wasm-opt` on release builds. Confirm it in the build log; a release build
  without it is noticeably larger.
- Find what is large with `twiggy top` on a build that kept names. The usual suspects, as a rule of
  thumb: `regex`, time-zone databases, large `serde` types, `Debug` derives and `format!` used
  only for logging, panic messages, and a dependency that belongs on the server.
- Every crate in the hydrate build ships. Check it on each new dependency:
  `cargo tree -e normal --target wasm32-unknown-unknown --no-default-features --features hydrate`.
- Leptos 0.8 can split the WASM by route: `#[lazy]` functions and lazy routes, built with
  `cargo leptos build --release --split`. Reach for it when one heavy route (an editor) inflates
  every page, after the cuts above.
- Budgets for WASM size and when to split: `0x:web-performance`.

## Build failures

| Symptom | Cause | Fix |
|---|---|---|
| Errors compiling `tokio`, `mio`, `socket2` or `sqlx` for `wasm32-unknown-unknown` | A server crate is not optional, or a shared crate enables it unconditionally | Make it optional and enable it from `ssr`; find the path with `cargo tree -i <crate> --target wasm32-unknown-unknown --no-default-features --features hydrate` |
| `getrandom` fails for `wasm32-unknown-unknown` | A crate needs randomness in the WASM | Enable the browser backend that getrandom's documentation names for the resolved version, or keep that crate server-only |
| `unresolved import` in the WASM build, inside or near a `#[server]` function | A server-only `use` at module level | Move it into the function body or a `#[cfg(feature = "ssr")]` module |
| Strange duplicate or conflicting definitions, both `ssr` and `hydrate` code compiled | `default = ["ssr"]`, a workspace crate enabling `leptos/ssr`, or rust-analyzer building with all features | No defaults; `cargo tree -e features -i leptos` for each target shows who enables what |
| wasm-bindgen reports a schema or version mismatch | The wasm-bindgen CLI differs from the `wasm-bindgen` crate in `Cargo.lock`. cargo-leptos downloads the CLI matching the lockfile only when none is installed; a `wasm-bindgen-cli` already on `PATH` is used as is | Remove the global CLI, or install the lockfile's version (`cargo install wasm-bindgen-cli --locked --version <version>`), or move the crate (`cargo update -p wasm-bindgen --precise <version>`); then pin both |
| Server starts and fails on `LEPTOS_OUTPUT_NAME` | Built with plain `cargo build` | Build with cargo-leptos |
| Release WASM works locally, the deployed page panics on hydration | Stale `/pkg` cached by a CDN or service worker without hashed names | `hash-files = true`; purge on deploy |

## Faster dev rebuilds

Measure a cold build, a one-line change in a component and a one-line change in a server function.

- `cargo leptos watch` rebuilds both targets on save and reloads the browser. `--hot-reload` patches
  `view!` markup without a rebuild, but it is marked beta and needs nightly; a convenience only.
- Linking dominates incremental builds. Since Rust 1.90, stable links with `rust-lld` by default
  on `x86_64-unknown-linux-gnu`; elsewhere, configure `lld` or `mold`. `debug = "line-tables-only"` in
  `[profile.dev]` shrinks what the linker writes.
- Split the workspace so the crate that changes most (the app) is small, and heavy, stable code
  (domain logic, SQL, generated types) lives in crates that rarely rebuild.
- Give rust-analyzer its own target directory and the `ssr` feature, so editor checks do not
  invalidate cargo-leptos builds.
- CI: cache `target/` and the cargo registry keyed on `Cargo.lock` and the toolchain (for example
  `Swatinem/rust-cache`), install cargo-leptos as a prebuilt binary rather than compiling it, and
  run clippy and tests in jobs parallel to the release build. Pipeline design: `0x:ci-cd-release`.

## The same toolchain everywhere

```toml
# rust-toolchain.toml
[toolchain]
channel = "1.97.0"
targets = ["wasm32-unknown-unknown"]
components = ["rustfmt", "clippy"]
```

- The toolchain file pins Rust and adds the WASM target on every laptop, in CI and in the image.
- Pin cargo-leptos to one exact version in one place (a file or CI variable) read by CI and the
  Dockerfile; `cargo install cargo-leptos --locked --version <x>`.
- Commit `Cargo.lock`. Leptos crates (`leptos`, `leptos_router`, `leptos_meta`, `leptos_axum`)
  move together in one change; `cargo update -p leptos` alone can leave them mismatched.
- Upgrade one Leptos minor at a time on a branch, read the release notes, run the end-to-end
  suite. Security releases are the exception to batching: apply them the day they ship.

## Ask the user

- **Is one image promoted across environments, or built per environment?** It decides whether
  public client config is compiled in or served at runtime. Default: one image, runtime config.
- **What WASM size is acceptable for the slowest device customers use?** Default: the budget from
  `0x:web-performance`; measure before splitting.
- **May this value be visible to anyone who opens DevTools?** Everything in the WASM is. Default:
  no, keep it on the server unless it is designed to be public.
- **When may Leptos upgrades happen?** Minor versions in the 0.x line can break APIs. Default:
  security fixes immediately, minors within a month, on a branch with the end-to-end suite.
