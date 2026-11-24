# Components and fine-grained reactivity

Read this when: writing, splitting or reviewing Leptos components, choosing between a signal, a
derived closure, a memo, an effect and a resource, placing `Suspense` and `Transition`, building
the project's own component library, rendering a long list, or reviewing a frontend pull request.

Snippets assume `use leptos::prelude::*;`, `serde::{Deserialize, Serialize}` and `uuid::Uuid`.

## Components, props and the view macro

A component is a function that runs once to build its view; afterward only the reactive closures
inside the view re-run. That is the main difference from React: there is no re-render, so code in
the body is setup, and anything that must update lives in a closure (`move || ...`) or a signal
passed straight into the view.

```rust
#[derive(Clone, Copy, Default, PartialEq)]
pub enum Variant { #[default] Primary, Secondary, Destructive, Ghost }

impl Variant {
    fn classes(self) -> &'static str {
        match self { // complete class strings, so the Tailwind scanner sees every one
            Variant::Primary => "bg-primary text-primary-foreground hover:bg-primary/90",
            Variant::Secondary => "bg-secondary text-secondary-foreground hover:bg-secondary/80",
            Variant::Destructive => "bg-destructive text-white hover:bg-destructive/90",
            Variant::Ghost => "hover:bg-accent",
        }
    }
}

#[component]
pub fn Button(
    #[prop(optional)] variant: Variant,
    #[prop(optional)] submit: bool,
    #[prop(optional, into)] disabled: Signal<bool>,
    #[prop(optional, into)] class: String, // layout only: margin, width, grid placement
    #[prop(optional)] on_click: Option<Callback<leptos::ev::MouseEvent>>,
    children: Children,
) -> impl IntoView {
    let class = format!("inline-flex h-10 items-center rounded-md px-4 font-medium focus-visible:outline-2 disabled:opacity-50 {} {class}", variant.classes());
    view! {
        <button
            type=if submit { "submit" } else { "button" }
            class=class
            disabled=disabled
            on:click=move |ev| if let Some(cb) = on_click { cb.run(ev) }
        >
            {children()}
        </button>
    }
}
```

- Props are typed function arguments. `#[prop(optional)]` uses `Default`; `#[prop(into)]` lets the
  caller pass a plain value or a signal for `Signal<T>`. Accept `Signal<T>` for anything that may
  change, so callers choose static or reactive without two components.
- `Children` renders once; `ChildrenFn` when the component renders its children more than once or
  inside `Show`. Named slots use `#[slot]`.
- Variants are a closed enum. A class built by interpolation (`format!("bg-{color}-500")`) is
  invisible to Tailwind's scanner and produces no CSS. Map names to complete strings.
- Rust has no maintained equivalent of tailwind-merge that the whole ecosystem uses, so keep the
  caller's `class` to layout utilities that cannot conflict with the variant's.
- Attributes written on a component with `{..}` (`<Button {..} aria-label="Close">`) are spread
  onto its root element.

## Signals, derived values and memos

| Need | Use | Note |
|---|---|---|
| A value that changes | `signal(v)` for a getter and setter pair, `RwSignal::new(v)` for one handle | Both are `Copy`; move them into closures freely |
| A value computed from others, cheap | A closure: `let total = move \|\| price.get() * qty.get();` | Runs on every read; no storage |
| A value computed from others, costly or read in many places | `Memo::new(move \|_\| ...)` | Runs once per change and notifies readers only when the result differs (needs `PartialEq`) |
| Async data from the server | A resource (below) | Never a signal filled by hand |
| A value from the outside world | An effect writing a signal, or a `LocalResource` | Browser only |

- `.get()` clones the value. For a large `Vec` read in a hot closure, use `.with(|v| v.len())` or
  `.read()` to borrow instead.
- Reading a signal in the component body (`let n = count.get();`) reads it once; the view never
  updates. Read inside the closure that renders it.
- Signals hold `Send + Sync` values by default. A browser handle such as a `web_sys` element or a
  `JsValue` fails to compile there: use `RwSignal::new_local`, `signal_local` or `LocalResource`.
- Never copy a resource's value into a signal "to edit it". Keep the resource as the source and
  hold only the user's draft in a signal.

## Resources, Suspense and Transition

A resource runs an async function when its source changes. `Resource::new` runs on the server
during SSR, serializes the result into the page and reuses it during hydration (`hydration.md`).

```rust
#[component]
pub fn ProjectHeader(#[prop(into)] id: Signal<Uuid>) -> impl IntoView {
    let project = Resource::new(move || id.get(), get_project); // refetches when id changes
    view! {
        <Transition fallback=|| view! { <div class="h-16 animate-pulse rounded bg-muted"></div> }>
            <ErrorBoundary fallback=|_| view! { <p role="alert">"Could not load the project."</p> }>
                {move || Suspend::new(async move {
                    project.await.map(|p| view! { <h1 class="text-2xl">{p.name}</h1> })
                })}
            </ErrorBoundary>
        </Transition>
    }
}
```

- `Suspense` shows its fallback whenever a resource read inside it is loading. `Transition` shows
  the fallback only the first time and keeps the old content while it reloads: use it for tabs,
  pagination and refetches after an action, where blanking the region reads as flicker.
- One boundary per region that loads independently. The fallback reserves the final size, or every
  reveal shifts the layout.
- Pair each boundary with an `ErrorBoundary`, so a failed region replaces itself, not the page.
- A resource read outside any `Suspense` still works on the server but renders without a
  fallback, and the HTML may arrive empty for that part.

## Effects only for the outside world

`Effect::new` runs in the browser after hydration and again when what it reads changes. It never
runs on the server. Use it to synchronize with something outside Leptos: `localStorage`, a
third-party widget, focus, analytics, a canvas.

```rust
#[component]
pub fn DraftEditor() -> impl IntoView {
    let draft = RwSignal::new(String::new());
    Effect::new(move |_| {
        let text = draft.get(); // tracked: the effect re-runs when the draft changes
        if let Ok(Some(storage)) = window().local_storage() {
            let _ = storage.set_item("draft", &text); // a failure here is not worth a panic
        }
    });
    view! { <textarea bind:value=draft></textarea> }
}
```

`local_storage()` exists only with the `Storage` feature of `web-sys` in the app's `Cargo.toml`:
web-sys gates each browser API behind a Cargo feature, and a missing one fails as "no method named".

| Urge | Do instead |
|---|---|
| An effect that sets a signal computed from other signals | A closure or `Memo` |
| An effect that reads and writes the same signal | It loops. Compute in the event handler |
| Store the selected object | Store its ID and look it up in a closure; survives refetch and reorder |
| Fetch in an effect | A resource; an effect has no serialization, races and fetches twice |
| React to "the form was submitted" | The action's `version` or `value` (`server-functions.md`) |

Read a signal without subscribing with `.get_untracked()`, for a value the effect needs but should
not re-run for. A missing subscription is the other bug: a value read through `get_untracked` by
mistake never updates.

## The component library

Behavior comes from native elements first: `<button>`, `<a>`, `<details>`, `<dialog>`, the
`popover` attribute, a native `<select>` on mobile. The Rust ecosystem has no headless primitive
library as complete as Radix or React Aria, so dialogs, menus, comboboxes and tabs that native
elements cannot cover are built once, to the WAI-ARIA Authoring Practices pattern, in
`components/ui/`. Focus trapping, dismissal, typeahead and roving focus are most of that work.
Requirements and tests: `0x:accessibility`.

- One module, `components/ui/`, holds primitives with no data access and no product words;
  `components/` holds product components composed from them; route-only components sit beside
  the route. Code moves down a layer on its second real use.
- Tokens are CSS variables with semantic names declared once in the Tailwind input file (`@theme`
  in Tailwind 4); choosing them is `0x:ui-ux-design`. Style states from attributes the markup
  already carries (`aria-expanded`, `aria-invalid`, `data-state`), not parallel signals.
- A third-party Leptos component crate is acceptable when it is maintained for the installed
  Leptos line and passes the accessibility checks; wrap it once in `ui/`.
- A component workshop is optional: at Launch, a `/dev/components` route excluded from production
  that renders every `ui/` component in each state (default, loading, empty, error, disabled, very
  long text, narrow container) catches most regressions.

## Component APIs

**Composition over configuration.** Content goes in `children` or slots. Three interacting
booleans (`has_header`, `show_footer`, `compact`) mean a layout decision is hidden in the component;
give it back to the caller as `<Card><CardHeader>...</CardHeader><CardBody>...</CardBody></Card>`.

**Controlled and uncontrolled.** A stateful component accepts the state from its parent or owns it,
with one convention across the library:

```rust
#[component]
pub fn Disclosure(
    #[prop(into)] label: String,
    #[prop(into)] id: String, // from the data: generated IDs differ between server and client
    #[prop(optional)] open: Option<RwSignal<bool>>, // controlled: the parent owns the state
    #[prop(optional)] default_open: bool,           // uncontrolled: the initial state
    children: ChildrenFn,
) -> impl IntoView {
    let open = open.unwrap_or_else(|| RwSignal::new(default_open));
    view! {
        <button aria-expanded=move || open.get().to_string() aria-controls=id.clone()
            on:click=move |_| open.update(|o| *o = !*o)>
            {label}
        </button>
        <div id=id hidden=move || !open.get()>{children()}</div>
    }
}
```

- A component never switches between the two modes during its life, and never copies a prop into
  its own signal "to initialize" it while also reading the prop.
- Callbacks report values (`Callback<String>`), not DOM events, for anything more complex than an
  input. Mutually exclusive props are an enum, not two `Option`s.

## Split at boundaries, not by size

| Boundary | Split so that |
|---|---|
| Data | A region with its own resource gets its own component and `Suspense` |
| Update rate | Fast-changing state lives in the smallest component that shows it |
| Failure | A region that can fail gets its own `ErrorBoundary` |
| WASM | With islands, the interactive leaf is the island and the rest stays HTML |
| Reuse | A second real caller exists. Not "might" |

Line count is not on the list. Signs a split went wrong: props passed through components that do
not use them; an effect that reports child state to the parent; a boolean that tells the child
which caller it has.

## Long lists

| Rows on screen at once | Do |
|---|---|
| Up to about 100 simple rows | Render them all with `For` |
| Hundreds | Paginate on the server, or `content-visibility: auto` with `contain-intrinsic-size` on rows |
| Thousands, or hundreds of heavy rows | Window the list and still page the data from the server |

These thresholds are rules of thumb; measure on the slowest target device.

```rust
view! {
    <ul>
        <For each=move || rows.get() key=|row| row.id children=move |row: InvoiceRow| view! {
            <li>{row.number}" "{row.total}</li>
        }/>
    </ul>
}
```

- The key is the row's ID from the data. An index key keeps state with the position when rows
  reorder, filter or delete; a random key rebuilds every row on each change.
- `For` diffs by key and moves existing DOM nodes, so rows keep their focus and input values.
- Windowing renders only the rows in view from the scroll offset and a fixed row height. Plan for
  its costs: find-in-page cannot see unrendered rows, screen readers need `aria-rowcount` and
  `aria-rowindex`, Back must restore the offset, and the server render holds only the first window.
  Prefer a filter and server pagination when they meet the need.

## Reviewing a frontend pull request

Read in this order; earlier items cost more to fix after merge.

1. **Server and WASM boundary.** New dependencies in the hydrate build, and why
   (`cargo tree -e normal --target wasm32-unknown-unknown --no-default-features --features hydrate`).
   Server-only code behind `ssr`. Resource and island payloads limited to rendered fields.
2. **Data.** Reads in resources, writes in server functions that validate, authorize and
   invalidate. Independent resources created together. No resource copied into a signal.
3. **Reactivity.** Values that should update are read inside closures. Effects only for the
   outside world, none that loop. `.get()` on large collections in hot paths.
4. **States.** Loading, empty, error and long-content cases for each new data region.
5. **Panics.** No `unwrap()` or `expect()` in component code: a panic in the WASM stops every
   handler on the page, and a panic during hydration leaves dead HTML.
6. **API and accessibility.** Primitives from `ui/`; props follow the library's conventions; every
   interactive element reachable by keyboard and labeled.

Measure instead of arguing: the WASM size before and after (`build-deploy.md`), the console of a
debug build for hydration errors, and the browser profiler for what updates. Line-level review is
the `code-review` skill; review etiquette is `0x:git-collaboration`.

## Ask the user

- **Is there a design system or brand to match, or is a clean default fine?** It decides how much
  of `ui/` is custom. Default: native elements styled with the project's tokens.
- **How many items can this list hold for the largest customer?** It decides plain rendering,
  pagination or windowing. Default: paginate on the server at 50 per page.
- **Which browsers and devices matter?** Touch, small screens and older WebKit change primitive
  choices. Default: current evergreen browsers, mobile first.
- **Who else will work on this UI in the next six months?** It decides whether a component route
  and written docs pay off now. Default: solo, so skip them until about twenty shared components.
