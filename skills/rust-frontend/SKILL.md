---
name: rust-frontend
description: Builds the Rust frontend with Leptos full-stack, covering rendering mode per route or server templates with htmx, components and signals, server functions and forms, routing and data loading, hydration, and cargo-leptos builds and deploys. Use when choosing Leptos, htmx or Dioxus, adding a blog or CMS, fixing hydration panics, stale data or request waterfalls, or when the WASM is huge or builds are slow.
---

# Rust frontend with Leptos full-stack

## Stance

The server is the default place for code. A page starts as HTML rendered on the server from data
the server loaded; WASM, client state and request-time work are each added for a reason that can
be named. Most frontend trouble in a small Leptos product has one of four causes: a cache nobody
declared, server data copied into a signal, server-only code compiled into the WASM, or a server
and a client that render different HTML. Look for those four before anything more exotic.

1. **Follow the project, then the installed version.** Read `Cargo.lock` and the docs for exactly
   that Leptos line before writing against an API. Leptos rewrote its reactive and view APIs
   between 0.6 and 0.7 (`create_signal` became `signal`, `create_resource` became
   `Resource::new`), so code remembered from another line fails to compile or behaves differently.
2. **Rendering is decided per route, server first.** Server-rendered HTML is what crawlers read and
   is never slow because a WASM file is. Pick the SSR mode per route; when the product is mostly
   forms and lists, server templates with htmx beat a WASM UI.
3. **Every cache has a stated lifetime and an invalidation.** Leptos keeps no data cache across
   requests: resources refetch when their source changes, and whatever sits in moka or a CDN is
   purged by the write that changed it. Per-user data never enters a shared cache.
4. **What compiles without `ssr` is public.** The hydrate build ships to every visitor, and every
   resource result is serialized into the HTML. Server-only crates are optional dependencies behind
   `ssr`, secrets are read at runtime on the server, and resources return view types that hold only
   rendered fields.
5. **A server function is a public endpoint.** On every call it identifies the caller, parses the
   input, authorizes against the specific row, writes, invalidates and returns a typed result. A
   `ProtectedRoute` or a check in the page does not protect it.
6. **Each piece of state has one owner.** Server data lives in resources keyed by their inputs,
   view state in the URL, ephemeral state in one component's signal, and derived values in closures
   or memos. A copy has no invalidation and goes wrong on the next write.
7. **Server and client render the same HTML.** No clocks, randomness or browser reads in a
   component body; browser-only work goes in effects, which never run on the server. A hydration
   error panics the WASM and leaves a page that no longer responds.
8. **Public pages are complete in the first HTML response**, with title, meta tags and the right
   status code. Link-preview bots and most AI crawlers run no WASM or JavaScript, and the status
   is fixed once streaming starts.
9. **Use cargo-leptos and the two-feature layout.** One build per target (`ssr` for the server
   binary, `hydrate` for the WASM), a size-optimized WASM profile, the Tailwind standalone CLI.
   Custom build scripts are maintained by one person forever.

## Route

| If the task is | Read |
|---|---|
| Leptos, htmx templates or Dioxus; whether a page is server-rendered, streamed, an island, client-only or prerendered; a page serves old content; adding a blog, docs or a CMS; preview and publish webhooks; link previews or crawlers see an empty page | `references/rendering-strategies.md` |
| Writing or splitting a component; props and children; signal, memo, effect or resource; Suspense and Transition; a button or dialog for the component library; a long list; reviewing a frontend pull request | `references/components-reactivity.md` |
| Writing a server function; a form that must work before the WASM loads; pending, error or optimistic states; the UI is stale after a save; cookies, headers or redirects from a server function; a server crate or secret reached the WASM; encodings, streaming or uploads | `references/server-functions.md` |
| Laying out routes and layouts; protecting pages; loading, error and not-found states; a page slow from sequential loads; filters or pagination in the URL; context or a global store; Back, scroll or focus problems; realtime updates; moving a React or template app to Leptos | `references/routing-data.md` |
| A hydration error or panic in the browser console; server and client render differently; code that needs `window` or `localStorage`; the same data fetched twice | `references/hydration.md` |
| `cargo leptos build` fails or is slow; wasm-bindgen version errors; ssr and hydrate features collide; the WASM is too big; Tailwind setup; environment variables; Docker image and deploy; pinning the toolchain | `references/build-deploy.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| UI approach | Leptos full-stack: SSR with hydration, server functions, cargo-leptos, Axum through leptos_axum | Mostly forms, lists and content: askama or maud with htmx. Same code must ship to desktop or mobile: Dioxus |
| Public content pages | `SsrMode::Async`, cached at the CDN with `s-maxage`, purged on publish | Changes only on publish and fits on disk: `SsrMode::Static`. Mostly static with a few widgets: islands |
| Pages behind login | Out-of-order streaming (the default mode), `Cache-Control: private, no-store` | Heavy editor or canvas: server frame, client-only body |
| Content | Markdown in the repo with typed, validated frontmatter | A non-developer must publish without a pull request: git-based or headless CMS |
| Reads | Resources calling server functions, keyed by source signals | Data only the browser can fetch: `LocalResource` |
| Writes | Server functions returning `Result<T, AppError>`, submitted through `ActionForm` | Callers other than this app's browser code: an Axum JSON route over the same data function |
| View state | URL query parsed through a `Params` struct with defaults | State nobody would share or restore: a local signal |
| Shared client state | Context provided in `App`, so each request gets its own | Large nested state with fine-grained updates: a `reactive_stores` store |
| UI primitives | An owned `components/ui` module on native elements and WAI-ARIA patterns, Tailwind tokens | A maintained component crate that passes `0x:accessibility` checks |
| Access control | Session and row checks inside every server function; page middleware only redirects | No exception |
| Toolchain | `rust-toolchain.toml` with the `wasm32-unknown-unknown` target; cargo-leptos pinned to one version | No exception |

By stage:

- **Prototype**: one crate with `ssr` and `hydrate` features from the official start template,
  Markdown content, default SSR mode everywhere, no islands, no static generation, no component
  workshop. One container on a PaaS.
- **Launch**: row-level authorization and an origin check on every server function; `AppError`
  with no internal text; loading, error and not-found states per data region with a real 404
  status; a size-optimized WASM profile; a panic hook in the hydrate entry; a test that requests
  every public URL; the cargo-leptos version and toolchain pinned in CI and the image.
- **Scale**: a workspace split so the app crate rebuilds fast; shared cache invalidation across
  instances; explicit server function endpoints for APIs that outlive one deploy; WASM budgets from
  `0x:web-performance` enforced in CI.

## Before you call it done

1. A fresh clone builds with `cargo leptos build --release` and nothing else, on the pinned
   toolchain and cargo-leptos version.
2. Clippy passes for both feature sets: `--features ssr`, and `--features hydrate --target
   wasm32-unknown-unknown`, each with `-D warnings`.
3. `curl -s` of each public page shows the title, the `<h1>`, the main text, the canonical link
   and the Open Graph tags; an unknown slug answers 404, checked twice.
4. Every server function identifies the caller, validates input into typed values, checks the row
   belongs to the caller, invalidates what shows the row, and returns `AppError` values that carry
   no database or internal text.
5. A POST to a server function with `Origin: https://evil.example` is rejected, and a signed-out
   or wrong-tenant call returns an error or "not found", never data. Tested with `curl`.
6. No server-only crate is in the WASM build (`cargo tree -i sqlx` for the hydrate target finds
   no match), and no server secret value appears in `target/site/pkg`.
7. Resources return view types with only rendered fields; the page HTML contains no private field
   (search it for an email address or an internal flag).
8. Independent resources are created together at the top of the route; independent queries inside
   one server function run with `tokio::try_join!`.
9. The console of a debug build shows no hydration error in a private window with extensions off.
10. No resource value copied into a signal; filters, tabs and pagination survive reload, a pasted
    link and Back.
11. Forms submit and update the page with JavaScript disabled, show pending state and field errors
    with it, and a double submit creates one record.
12. The gzip size of the release WASM is measured and within the budget from `0x:web-performance`.
13. No `unwrap()` or `expect()` in component bodies, server functions or handlers.
14. Interactive widgets work by keyboard and are labeled; list keys are IDs from the data.
15. The production image runs with `LEPTOS_HASH_FILES=true` and `hash.txt` beside the binary, and
    the served page links hashed `/pkg` files that answer 200.

## Not this skill

- Plain HTML, CSS, browser APIs, Rust-to-WASM interop, forms and animation →
  `0x:frontend-foundations`
- WASM payload budgets, Core Web Vitals and image and font loading → `0x:web-performance`
- Design tokens, visual design and UX flows → `0x:ui-ux-design`
- three.js scenes and 3D product pages → `0x:3dui`
- API contracts the frontend consumes, idempotency and rate limits → `0x:api-design`
- Search rankings, metadata strategy and AI-search visibility → `seo-aeo-geo-ultimate`
- Session mechanics, sign-in flows and permission models → `0x:auth-identity`
- Keyboard, focus and screen-reader requirements for components → `0x:accessibility`
