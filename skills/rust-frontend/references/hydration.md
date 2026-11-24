# Hydration and server-client consistency

Read this when: the browser console shows a hydration error or a panic, the page renders but
nothing responds to clicks, the server and the client render different HTML, code needs `window`,
`localStorage` or the current time, or the same data is fetched on the server and again in the
browser.

Snippets assume `use leptos::prelude::*;`, `serde::{Deserialize, Serialize}` and `uuid::Uuid`.

## How Leptos hydrates, and why a mismatch is fatal

The server renders HTML with small marker comments. In the browser, the WASM runs the same
component tree once and, instead of creating nodes, walks the existing DOM in order and attaches
event handlers and reactive bindings to it. It expects exactly the nodes the server sent.

When the DOM holds something else, a debug build prints "A hydration error occurred while trying
to hydrate an element defined at" the source file and line of the component, then panics with
"Unrecoverable hydration error". A release build panics without that message unless it was built
with `--cfg leptos_debuginfo`. After the panic the WASM is dead: the HTML stays on screen, but no
button, form enhancement or signal works on that page. Treat every hydration error as a bug, not a
warning.

## Causes and fixes

| Cause | Fix |
|---|---|
| Time: `Utc::now()`, `OffsetDateTime::now_utc()`, relative times ("3 minutes ago"), local time zones | Format on the server in a fixed zone and pass the string; switch to local or relative time in an effect after hydration |
| Randomness or counters: `Uuid::new_v4()`, `rand`, an incrementing ID for `aria-controls` | IDs from the data (`format!("faq-{}", item.id)`) or generated on the server and passed down |
| Browser reads in the component body: `window().inner_width()`, `localStorage`, `matchMedia`, cookies read through `document` | Render a default that the server can also compute; read the browser value in an effect. Prefer CSS media queries over reading the width |
| Branches on the build: `cfg!(feature = "ssr")` or `#[cfg(feature = "hydrate")]` inside a view | Never branch markup on the feature. Branch on a `mounted` signal set by an effect (below) |
| Different data on each side: a server function called in an effect, a `LocalResource` rendered inside the same markup as server data | Load with `Resource::new` so the client reuses the server's result (last section) |
| Invalid nesting the browser repairs: `<div>` in `<p>`, `<a>` in `<a>`, `<form>` in `<form>`, `<tr>` directly in `<table>` without `<tbody>`, a `<button>` in a `<button>` | Fix the markup. The server sent it as written and the HTML parser rewrote it before the WASM looked |
| A theme class from a stored preference | Store the preference in a cookie, read it on the server and render the class; nothing to fix up later |
| Extensions, translation tools or injected scripts rewriting the DOM | Confirm in a clean profile. Keep the hydrated root to `<body>`; nothing else to fix in code |
| A CDN rewriting HTML (minification, email obfuscation, script deferral) | Turn those features off for HTML routes |
| Server and WASM built from different commits (a cached old WASM after a deploy) | Hashed asset names (`hash-files = true`, `build-deploy.md`) so a page always loads its own WASM |

The invalid-nesting row is the one people miss: `view! { <p><div>"x"</div></p> }` compiles,
renders on the server, and fails hydration because the browser closed the `<p>` before the `<div>`.
Validate the server HTML (`curl -s "$URL" > page.html`, then an HTML validator) when the error
names an element whose code looks right.

## Diagnose in this order

1. Read the console of a debug build (`cargo leptos watch`). The message names the component's
   source location, and the node logged after it shows what the DOM held instead.
2. Reproduce in a private window with extensions off.
3. Compare `curl -s "$URL"` with the DOM in the element inspector at the named location. If they
   differ, the browser or something in between rewrote the HTML; if they agree, the client
   rendered something different from the server.
4. Check the time zone and locale: the server usually runs in UTC with no locale, the browser in
   the user's.
5. Check what differs by build: a `cfg` inside a view, a feature enabled only on one side, or a
   dependency that behaves differently on `wasm32`.

## Browser-only code runs after hydration

Effects never run on the server and run in the browser after hydration, so they are the place for
anything that needs `window`, `document`, storage, the user's clock or a third-party script. For a
part of the page that cannot render on the server at all, render a placeholder on both sides and
swap after mount:

```rust
#[component]
pub fn ClientOnly(children: ChildrenFn, #[prop(optional, into)] fallback: ViewFn) -> impl IntoView {
    let mounted = RwSignal::new(false);
    Effect::new(move |_| mounted.set(true)); // never runs on the server
    view! { <Show when=move || mounted.get() fallback=fallback.clone()>{children()}</Show> }
}

#[component]
pub fn LocalTime(utc: String) -> impl IntoView {
    use leptos::wasm_bindgen::JsValue; // the re-export also compiles in the ssr build
    let shown = RwSignal::new(utc.clone()); // the server and the first client render agree
    let iso = utc.clone(); // the effect owns its copy; the view keeps `utc`
    Effect::new(move |_| {
        let date = js_sys::Date::new(&JsValue::from_str(&iso));
        shown.set(String::from(date.to_locale_string("default", &JsValue::UNDEFINED)));
    });
    view! { <time datetime=utc>{shown}</time> }
}
```

- `ClientOnly` removes its content from the HTML. Use it for widgets that cannot render on the
  server (maps, charts drawing to a canvas, editors), never for what a reader or crawler came for.
- `NodeRef` gives the element after it is mounted; read it inside an effect, where it is filled.
- Code that touches `web_sys` at the top level of a module runs when the module loads, not inside
  an effect. Keep it in functions called from effects or event handlers.
- Browser crates used in components (`js-sys`, and `web-sys` with one Cargo feature per API, such
  as `Storage`) are regular dependencies, not `hydrate`-only: the component compiles in both
  builds, and the effect that calls them never runs on the server. Leptos re-exports
  `wasm_bindgen` and `web_sys`.
- `spawn_local` starts browser-side async work from an event handler; tie long-lived work to the
  component with `on_cleanup` so it stops when the component goes away.
- The browser platform APIs themselves, and `wasm-bindgen` and `web-sys` interop:
  `0x:frontend-foundations`.

## Debugging panics in the browser

A panic in the WASM prints only `unreachable` unless a panic hook is installed. Every hydrate entry
installs one before anything else runs:

```rust
#[cfg(feature = "hydrate")]
#[wasm_bindgen::prelude::wasm_bindgen]
pub fn hydrate() {
    console_error_panic_hook::set_once(); // the panic message and location in the console
    leptos::mount::hydrate_body(App);
}
```

- Debug builds (`cargo leptos watch`, `cargo leptos build` without `--release`) keep the
  hydration diagnostics. To investigate a problem that appears only in release, build once with
  `RUSTFLAGS="--cfg leptos_debuginfo" cargo leptos build --release`.
- `wasm-opt` and the release profile strip function names, so stack traces become numbers. Keep a
  debug build for reading traces.
- For logs from the browser, add a `tracing` subscriber that writes to the console in the hydrate
  entry, at `warn` or above in release; each log line format string adds to the WASM.
- Report panics from real users: a panic hook that also sends the message to the error tracker
  (`0x:site-reliability`), sampled, without user data.
- `unwrap()` in a component, an event handler or an effect is a panic waiting for a user; a panic
  in the WASM stops every handler on the page, not only the one that failed. Map to a rendered
  error state instead.

## Pass server data to the client through resources

| Loader | Runs on the server during SSR | Result in the page | On hydration |
|---|---|---|---|
| `Resource::new(source, fetcher)` | Yes | Serialized into the HTML | Reuses the serialized value; no second request |
| `Resource::new_blocking` | Yes, and holds the head of the response | Serialized | Reuses it |
| `OnceResource::new(future)` | Yes | Serialized | Reuses it; for data with no source signal |
| `LocalResource::new(fetcher)` | No; the fallback is rendered | Nothing | Fetches in the browser |
| A server function called in an effect | No | Nothing | Fetches after hydration: a second request and a flash |

```rust
let plan = OnceResource::new(current_plan()); // rendered by the server, reused by the client
let rates = LocalResource::new(fetch_exchange_rates); // browser only: shows the fallback in the HTML
```

- Every resource result is in the HTML twice: once as markup and once as serialized data. Return
  view types with the fields the page renders; a 200-row table with 30 columns where 5 are shown
  ships the other 25 to every visitor and is readable by anyone who views the source.
- Resource outputs must serialize the same way on both sides. Types with custom serde impls that
  depend on the target, or floats formatted differently, show up as hydration errors.
- A resource whose source depends on a browser-only value (window size, storage) runs with one
  value on the server and another in the browser, then refetches. Keep sources to route params,
  the query and server-known state.

## Hydration cost

The whole page hydrates in a full Leptos app: the browser downloads and compiles the WASM, then
runs every component once before any handler works. The time between first paint and the first
working click is that work.

- Keep the WASM small (`build-deploy.md`); size is the largest share of the delay on slow phones.
- For mostly static pages, islands hydrate only the interactive parts (`rendering-strategies.md`).
- Forms built with `ActionForm` and links built with `<A>` work before hydration, so a slow WASM
  delays enhancements, not the basic action.
- Budgets for WASM size and interaction latency: `0x:web-performance`.

## Ask the user

- **Must this page work before the WASM loads, or without it?** It decides how much rides on
  plain forms and links. Default: reading and the primary form work without it; rich tools need it.
- **Should times show in the reader's time zone, or in one fixed zone?** Local time needs a
  post-hydration update. Default: the user's local time, rendered after mount, with UTC in the HTML.
- **May real-user panics be reported to the error tracker?** It sends browser data to a vendor
  (`0x:privacy-compliance`). Default: yes, without user identifiers.
