# Routing, data loading and state

Read this when: laying out routes and layouts, protecting pages, adding loading, error and
not-found states, fixing a page made slow by sequential loads, putting filters or pagination in the
URL, deciding where client state lives, fixing Back, scroll or focus behavior, merging realtime
updates, or moving a React or template-rendered app to Leptos.

Snippets assume `use leptos::prelude::*;`, `leptos_router::hooks::*`, `leptos_router::params::Params`,
`serde::{Deserialize, Serialize}` and `uuid::Uuid`.

## Structure routes around the product's navigation

Write the URL map before the components. URLs are nouns with stable IDs, and nesting in the URL
matches what the user sees as nesting: if the sidebar stays while the content changes, that is a
parent route with child routes.

```rust
use leptos_router::{components::{Outlet, ParentRoute, Route, Router, Routes, A}, path, SsrMode};

#[component]
pub fn App() -> impl IntoView {
    leptos_meta::provide_meta_context();
    view! {
        <Router>
            <Routes fallback=NotFound>
                <Route path=path!("/") view=Home/>
                <Route path=path!("/blog/:slug") view=BlogPost ssr=SsrMode::Async/>
                <ParentRoute path=path!("/app/projects/:id") view=ProjectLayout>
                    <Route path=path!("") view=ProjectOverview/>
                    <Route path=path!("settings") view=ProjectSettings/>
                </ParentRoute>
            </Routes>
        </Router>
    }
}

#[component]
fn ProjectLayout() -> impl IntoView {
    view! {
        <nav><A href="">"Overview"</A><A href="settings">"Settings"</A></nav> // relative links
        <main><Outlet/></main> // the matched child renders here; the layout stays mounted
    }
}

#[component]
pub fn NotFound() -> impl IntoView {
    #[cfg(feature = "ssr")]
    if let Some(res) = use_context::<leptos_axum::ResponseOptions>() {
        res.set_status(axum::http::StatusCode::NOT_FOUND); // effective only before the first byte
    }
    view! { <h1>"Page not found"</h1> }
}
```

- A parent route's view stays mounted while its children change. It holds chrome (navigation,
  tabs) and nothing per page, and it is the wrong place for an access check (below).
- A tab is a route when it has its own data or should be linkable, and a query parameter when it
  only filters what is loaded.
- Params are strings from the URL and untrusted: parse them (below) and render `NotFound` on
  failure.
- Three to four levels of nesting is the practical limit; past it nobody can say which layout owns
  which piece of the screen.
- `<A>` does client-side navigation after hydration and is a plain link before. Links to paths
  another system serves are plain `<a>` with `rel="external"`, or the router tries to handle them.

## Protect routes on the server, in three layers

| Layer | Where | What it does | What it cannot do |
|---|---|---|---|
| 1. Redirect before rendering | Axum middleware on the page router | Sends a full page load without a session to the login page. No database call beyond the session | Protect client-side navigation or server functions |
| 2. Session check | `require_user()` in every server function that needs a user (`server-functions.md`) | The real authentication check, on every call | Decide access to a specific row |
| 3. Authorization | Inside each data query: this user, in this tenant, owns this row | The real access decision | Nothing; this is the layer that must not be missing |

```rust
use axum::{extract::Request, middleware::Next, response::{IntoResponse, Redirect, Response}};
use tower_sessions::Session;

pub async fn app_pages_need_session(session: Session, req: Request, next: Next) -> Response {
    let protected = req.uri().path().starts_with("/app");
    if protected && !matches!(session.get::<UserId>("user_id").await, Ok(Some(_))) {
        return Redirect::to("/login").into_response();
    }
    next.run(req).await
}
```

- `ProtectedRoute` (a `condition` returning `Option<bool>` and a `redirect_path`) is user
  experience for client-side navigation: it hides a page and redirects, but the data still comes
  from server functions that must check on their own.
- During streaming SSR a redirect decided inside `Suspense` comes too late for the status code;
  that is why layer 1 is middleware.
- A return path (`?next=/app/billing`) is accepted only when it is a relative path on this origin.
  Anything else is an open redirect.
- After sign-out, do a full page load so no previous user's signals survive in memory.

Session mechanics and permission models: `0x:auth-identity`.

## Loading, error and not-found states per route

- Every region that loads its own data sits in `Suspense` (first load) or `Transition` (reloads),
  wrapped in an `ErrorBoundary`. With one boundary at the root, one failed widget blanks the shell.
- `Routes` takes a `fallback` for unmatched URLs; a matched route whose data does not exist renders
  the same `NotFound`, which sets 404 when it runs before the first byte (`SsrMode::Async` or a
  blocking resource; `rendering-strategies.md`).
- Errors shown to users are `AppError` messages written for users. Log the detail on the server
  with a request ID and show that ID; never render a database message.
- Expected outcomes (empty results, validation, no permission) are rendered states, not errors.
- Check each state by hand once: throttle the network for loading, return an error from the server
  function for the error state, request an unknown ID for not-found.

## Start route data in parallel

A waterfall is a request that could not start until an unrelated one finished. Resources start
loading when they are created, on the server during SSR and in the browser on client navigation.

```rust
#[derive(Params, Clone, Debug, PartialEq)]
pub struct ProjectParams { pub id: Option<Uuid> }

#[component]
pub fn ProjectOverview() -> impl IntoView {
    let params = use_params::<ProjectParams>();
    let id = move || params.with(|p| p.as_ref().ok().and_then(|p| p.id)); // None for "abc"
    // both start now, in parallel; an invalid ID becomes NotFound instead of a panic
    let project = Resource::new(id, |id| async move { get_project(id.ok_or(AppError::NotFound)?).await });
    let activity = Resource::new(id, |id| async move { get_activity(id.ok_or(AppError::NotFound)?).await });
    view! {
        <Suspense fallback=|| view! { <p>"Loading..."</p> }>
            <ErrorBoundary fallback=|_| view! { <NotFound/> }>
                {move || Suspend::new(async move {
                    project.await.map(|p| view! { <h1>{p.name}</h1> })
                })}
            </ErrorBoundary>
        </Suspense>
        <Suspense fallback=|| view! { <p>"Loading activity..."</p> }>
            {move || Suspend::new(async move {
                activity.await.map(|a| view! { <p>{a.len()}" updates this week"</p> })
            })}
        </Suspense>
    }
}
```

| Shape | Fix |
|---|---|
| A resource created inside the `Suspend` of another, after its `.await` | Create both at the top of the route component |
| A child component creates its resource only after the parent's data rendered | Hoist the resource to the route component and pass it down, or pass the ID so the child starts at once |
| Independent queries awaited one after another inside a server function | `tokio::try_join!(load_project(&pool, id), load_members(&pool, id))` |
| One query per row in a list | One query for the list, or a batched query by IDs |
| The second load truly depends on the first | Keep the order; often it is one joined query |

Find waterfalls by reading the spans of one request in a trace (`0x:site-reliability`), not by
guessing.

## View state in the URL

Anything the user expects to survive reload, Back or a pasted link goes in the URL: filters, sort,
page, tab, search text, the selected item.

```rust
#[derive(Params, Clone, Debug, PartialEq)]
pub struct ListQuery { pub page: Option<u32>, pub sort: Option<Sort> }

#[component]
pub fn ProductList() -> impl IntoView {
    let query = use_query::<ListQuery>();
    let page = move || query.with(|q| q.as_ref().ok().and_then(|q| q.page)).filter(|p| *p >= 1).unwrap_or(1);
    let sort = move || query.with(|q| q.as_ref().ok().and_then(|q| q.sort)).unwrap_or_default();
    let products = Resource::new(move || (page(), sort()), |(page, sort)| list_products(page, sort));
    view! {
        <leptos_router::components::Form method="GET" action="">
            <select name="sort">
                <option value="newest" selected=move || sort() == Sort::Newest>"Newest"</option>
                <option value="price" selected=move || sort() == Sort::Price>"Price"</option>
            </select>
            <button type="submit">"Apply"</button>
        </leptos_router::components::Form>
        <Transition fallback=|| ()>
            {move || Suspend::new(async move { products.await.map(|items| view! { <ProductGrid items/> }) })}
        </Transition>
    }
}
```

- The URL is user input. Parse with defaults and never panic: an unknown sort becomes the default,
  `page=-3` becomes 1. One invalid field makes the whole `Params` struct an error, so read each
  field with its own fallback when partial garbage is common.
- `#[derive(Params)]` fields are `Option<T>` where `T: FromStr` and its error type implements
  `std::error::Error`; a `type Err = ()` does not compile.
- The router's `Form` with `method="GET"` is an ordinary form before hydration and a client-side
  navigation after, so filters work without WASM.
- Push or replace: would the user expect Back to undo it? Pagination, a tab, an opened item: push.
  Typing in a search box: `use_navigate()` with
  `NavigateOptions { replace: true, ..Default::default() }`, debounced around 300 ms.
- Leave defaults out of the URL so there is one URL per view. Changing a filter resets the page.
- Keep out of the URL: secrets, personal data, large blobs, hover and focus.

## Local signals, context or a store

| Use | When |
|---|---|
| A signal in the component | One component or a small subtree |
| A signal passed as a prop | A parent and a few children |
| Context (`provide_context`, `use_context`) | Read by many, changes rarely: theme, locale, current user, feature flags, a cart |
| A `reactive_stores` store (`#[derive(Store)]`) | Large nested state where distant components update and read different fields |

- Provide app-wide context inside `App`, so each server render (one per request) gets its own. A
  `static`, `LazyLock` or `thread_local!` holding a signal or user data in shared code is shared by
  every request the server handles: one user's cart rendered for another.
- `expect_context` panics when nothing was provided, and a panic in the WASM stops the page. Use it
  only for context provided at the root; elsewhere `use_context` with a fallback.
- Server data is not client state. The current user comes from a resource over a server function,
  provided as context; it is not a signal filled by hand.

## Back, forward, scroll and focus

Back must return the user to the screen they left: same filters, same loaded items, same scroll.

- State kept in the URL is restored for free; that is the main reason it lives there.
- Client-side navigation scrolls to the top of the new page and to `#fragment` targets. Check the
  installed router's behavior on Back for long pages; where the offset matters (feeds, long
  lists), store it in `sessionStorage` keyed by URL in an effect and restore it after the data
  rendered.
- `<A scroll=false>` for in-place changes such as tabs and filters.
- Focus: after a client navigation a screen-reader user needs to know the page changed. Give every
  route a unique `<Title>` and one `<h1>`, and move focus to the main heading in an effect keyed on
  `use_location().pathname`. Closing a dialog returns focus to its opener (`0x:accessibility`).
- Sticky headers hide anchor targets: set `scroll-margin-top` on headings.

## Realtime updates into reactive state

Transport and server fan-out: `0x:backend-architecture`. On the client, subscribe once per
resource at a stable level of the tree, in an effect that closes the socket on cleanup
(`on_cleanup`). Default to refetching: on an event, bump a version signal included in the
resource's source, throttled to about once a second. Patch state directly only when events are
frequent or carry the full entity, and then apply an event only if its version is newer.

```rust
/// Returns false for a duplicate, an out-of-order delivery or the echo of our own write.
pub fn merge(list: &mut Vec<Message>, incoming: Message) -> bool {
    match list.iter_mut().find(|m| m.id == incoming.id) {
        None => { list.push(incoming); true }
        Some(m) if m.version >= incoming.version => false,
        Some(m) => { *m = incoming; true }
    }
}
// on each event: messages.maybe_update(|list| merge(list, event)); notifies only on change
```

- On reconnect, refetch; events sent while the socket was down are gone.
- In a list the user is reading, do not insert at the top and push content down. Show an "N new"
  control unless the user is already at the top of a newest-first list.
- A channel from the socket task to the UI is bounded, or a slow tab grows memory without limit.

## Migrating a React or template app to Leptos

Move route by route behind a router that decides which system serves each path. A rewrite in one
go loses to schedule and regressions.

1. Inventory routes with traffic and revenue per route. Write a test that requests every public
   URL and asserts its status, redirect target and canonical tag; that file is the contract.
2. Put a reverse proxy or the Axum app in front: Leptos routes for migrated paths, everything else
   forwarded to the old app (an Axum `fallback` that proxies, or the CDN's path rules).
3. Move one low-risk route end to end, with auth, analytics, error reporting and deploy.
4. Share the session through a cookie on the parent domain, and the design through the same
   Tailwind tokens.
5. Links that cross systems are plain `<a>`; the Leptos router must not soft-navigate into a path
   it does not own.
6. After each move, compare error rate, conversion and search impressions with the week before.
   Switch back by flipping the rule; delete old code when its route has been dark for a release.

Traps: trailing-slash policy differing between systems (redirect loops, duplicate URLs); a service
worker still serving the old shell; analytics counting a cross-system navigation twice; global CSS
loaded by both shells; a cookie scoped to the old path or host.

## Ask the user

- **Which pages are public, which need sign-in, and which need a role?** Default: marketing and
  auth pages public, everything under `/app` signed-in, admin by role.
- **Should this view be shareable by link and survive reload?** Default: yes for filters, sort,
  pagination, tabs and the selected item.
- **Do other people's changes need to appear without a reload?** Realtime adds a connection to run
  and merge rules to maintain. Default: no, until users ask.
- **Do old URLs have inbound links or search traffic?** Every changed URL then needs a permanent
  redirect and a test. Default: assume yes for anything that was public.
- **For a migration, is a period with two systems acceptable?** Default: yes, route by route.
