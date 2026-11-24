# Rendering modes, framework choice and content sources

Read this when: choosing between Leptos, server templates with htmx and Dioxus, deciding how a
route is rendered, streamed, prerendered or cached, making pages readable by crawlers and link
previews, or deciding where editable content lives and how a publish reaches the page.

## Read the project before deciding anything

```bash
grep -A1 '^name = "leptos"$' Cargo.lock                # the installed line: 0.6, 0.7 or 0.8
sed -n '/metadata.leptos\]/,/^\[/p' Cargo.toml         # cargo-leptos settings
grep -rnE 'SsrMode::|#\[island|StaticRoute' src/       # rendering choices already made
```

Read the docs for the installed line (docs.rs at that version, the Leptos book) before writing
against an API from memory. Snippets here are for Leptos 0.8 with Axum 0.8 and assume
`use leptos::prelude::*;`, `leptos_router::hooks::*`, serde's derives and `uuid::Uuid` in scope.

## Choosing the UI approach

Follow the project. For a new one:

| Building | Choose | Why, and the catch |
|---|---|---|
| Public pages and an interactive app behind login | Leptos full-stack: SSR with hydration | One Rust codebase, typed server functions, an SSR mode per route, fine-grained updates. The catch: two builds, a WASM payload, hydration discipline |
| Forms, tables, lists and content; every interaction can wait a round trip | Axum with askama or maud, plus htmx | No WASM, no hydration, no client state; HTML is the API. Below |
| Content site with a few interactive widgets | Leptos with islands | Only the widgets ship and hydrate |
| The same UI must also ship as a desktop or mobile app | Dioxus | One component model and server functions for web, desktop and mobile. The catches: desktop and mobile builds render in a system webview and call server functions over HTTP, so they need the deployed server's URL configured, and every server function becomes an API that installed app versions you cannot force-update keep calling; `web_sys` code runs only in the web build. Check the current release's fullstack support before relying on it for SEO pages |
| Internal tool behind login, no SEO | Leptos client-side only | Nothing to hydrate; first paint waits for the WASM |
| A React or template frontend that works | Keep it; move route by route only for a reason (`routing-data.md`) | A framework migration never fixes a caching or configuration bug |

**Server templates with htmx** win when all of these hold: the UI is forms, tables, navigation and
fragment swaps; nothing must work offline; no long-lived client state. They lose when any holds:
editors, boards, canvases or multi-step optimistic flows; interactions that cannot wait a round
trip; a native app that needs a JSON API anyway. Use askama (templates in files, checked at
compile time) when designers edit HTML, maud (HTML as a Rust macro) when only developers do.
Never let htmx swap nodes inside a Leptos-hydrated region: two systems then own the same DOM.

```rust
use axum::{extract::Form, http::HeaderMap, response::{Html, IntoResponse, Redirect, Response}};
use maud::{html, Markup};

#[derive(serde::Deserialize)]
pub struct NewTodo { title: String }

fn todo_item(title: &str) -> Markup { html! { li { (title) } } } // maud escapes interpolations

pub fn todo_form() -> Markup {
    html! {
        // works as a plain POST without JavaScript; htmx turns it into a fragment swap
        form method="post" action="/todos" hx-post="/todos" hx-target="#todos" hx-swap="beforeend" {
            input name="title" required maxlength="120";
            button { "Add" }
        }
    }
}

pub async fn add_todo(headers: HeaderMap, Form(todo): Form<NewTodo>) -> Response {
    // ... identify, validate, authorize and insert, exactly as in server-functions.md
    if headers.contains_key("hx-request") {
        Html(todo_item(&todo.title).into_string()).into_response()
    } else {
        Redirect::to("/todos").into_response() // 303: post, redirect, get
    }
}
```

The handler is a public endpoint like any server function: same validation, authorization and
cross-site checks (`server-functions.md`).

## Rendering: decide per route

Four questions settle it: is the response the same for every visitor; how stale may it be; must a
crawler or link preview read it without running WASM; is it behind login.

| Route | Strategy |
|---|---|
| Marketing, pricing, blog, docs, changelog | Server-rendered (`Async`, or `Static`), cached at the CDN, purged on publish |
| Catalog or listing whose shared data changes through the day | Server-rendered with a short `s-maxage`, plus purge on write |
| Shared page with a per-user piece (cart count, account menu) | The page is cacheable; the per-user piece loads in the browser (`LocalResource`) so the cached HTML is the same for everyone |
| Dashboard, settings, anything per user | Out-of-order streaming, `Cache-Control: private, no-store` |
| Heavy tool behind login (editor, canvas, map) | Server-rendered frame, client-only body (`hydration.md`) |
| Search and filtered lists | Rendered on the server from the URL query; a GET form (`routing-data.md`) |
| Internal admin tool | Client-side only is acceptable |

Client-only rendering of public content gives up crawlers and first paint; keep it behind login.
Leptos sets no caching headers on pages, so the decision is explicit. Set them in the page
component, which runs before the first byte is sent:

```rust
#[cfg(feature = "ssr")]
pub fn cache_publicly(seconds: u32) {
    use axum::http::{header, HeaderValue};
    if let Some(res) = use_context::<leptos_axum::ResponseOptions>() {
        let value = format!("public, max-age=0, s-maxage={seconds}, stale-while-revalidate=60");
        if let Ok(value) = HeaderValue::from_str(&value) {
            res.insert_header(header::CACHE_CONTROL, value); // the CDN keeps it, browsers recheck
        }
    }
}
```

A page that reads the session anywhere in its tree, including an account menu in the root layout,
must never get this header: the CDN would serve one user's menu to everyone. Check with `curl -sI`.
HTTP and CDN caching mechanics: `0x:web-networking`.

## SSR mode per route

The mode is the `ssr` prop on a `Route`. The default is out-of-order streaming.

| Mode | What the server sends | Head, meta and status from async data | Use for |
|---|---|---|---|
| `OutOfOrder` (default) | The shell at once with `Suspense` fallbacks, then each region as it resolves | No, unless the resource is blocking | Pages behind login, dashboards |
| `InOrder` | HTML in document order, pausing at each `Suspense` until it resolves | Only data resolved before the first `Suspense` | Pages that must read top to bottom without JavaScript but can stream |
| `PartiallyBlocked` | Out-of-order, but regions of blocking resources are filled in on the server | Yes, for blocking resources | Pages where some content must be in the HTML and the rest can stream |
| `Async` | Nothing until every resource resolved, then the whole page | Yes | Public content: blog, docs, product pages, whose title, meta tags and 404 depend on data |
| `Static(StaticRoute)` | A file rendered at startup or on regeneration | Yes | Pages that change only on publish |

```rust
<Routes fallback=NotFound>
    <Route path=path!("/") view=Home/>
    <Route path=path!("/blog/:slug") view=BlogPost ssr=SsrMode::Async/>
    <Route path=path!("/app/projects") view=Projects/> // streams out of order
</Routes>
```

- In a streaming mode the status and headers leave with the shell, so a `NotFound` rendered later
  inside `Suspense` is a soft 404 with status 200. For a real 404 use `Async`, or a blocking
  resource (`Resource::new_blocking`), which holds the head of the response until it resolves.
- Out-of-order streaming needs the small inline script Leptos sends to move resolved regions into
  place. Without JavaScript the reader sees fallbacks; crawlers that run no scripts index them.
- A reverse proxy or compression layer that buffers removes streaming. Check with
  `curl -sN -o /dev/null -w '%{time_starttransfer} %{time_total}\n' "$URL"`: equal numbers on a
  page with a slow region mean something buffers.

## Islands

With the `islands` feature on `leptos`, the app renders as HTML and only components marked
`#[island]` ship WASM and hydrate. It suits content sites with a few widgets: the WASM shrinks to
the islands and what they use.

```rust
#[island]
pub fn LikeButton(post_id: uuid::Uuid, initial: u32) -> impl IntoView {
    let (likes, set_likes) = signal(initial);
    let like = move |_| set_likes.update(|n| *n += 1); // ... and call a server function with post_id
    view! { <button on:click=like>{likes}" likes"</button> }
}
```

- The feature is app-wide: every ordinary component becomes server-only HTML, and the hydrate
  entry calls `leptos::mount::hydrate_islands()` instead of `hydrate_body`. Plan it per app.
- Island props are serialized into the HTML, so they must be serializable and are public. Pass IDs
  and rendered fields. Children passed to an island are rendered on the server and stay HTML.
- Context provided outside an island does not reach it in the browser. Each island reads what it
  needs through props or server functions.
- Navigation between pages is a full page load unless the experimental islands router is enabled.

## Prerender and regenerate

`SsrMode::Static` renders a route to a file at startup and serves the file afterward.
`prerender_params` lists the parameters to build; `regenerate` takes a function returning a stream,
each item of which rebuilds that page. The server starts with `generate_route_list_with_ssg` and
`StaticRouteGenerator::generate`, and the site directory must be writable in the container.

```rust
<Route
    path=path!("/docs/:slug")
    view=DocPage
    ssr=SsrMode::Static(StaticRoute::new().prerender_params(|| async move {
        [("slug".to_string(), doc_slugs().await)].into_iter().collect()
    }))
/>
```

Each instance renders and stores its own copy, and a regeneration signal must reach every
instance. For most products server rendering plus CDN caching with purge on publish gives the same
result with fewer moving parts; use static routes for docs-sized sets that change only on deploy.

## HTML that crawlers and link previews can read

Link-preview bots (Slack, X, WhatsApp, LinkedIn, iMessage) and most AI crawlers run no scripts.
Google renders later and on a budget. What to rank for and metadata wording are
`seo-aeo-geo-ultimate`'s. For every public page:

- The first response holds `<title>`, meta description, canonical URL, Open Graph tags, the
  `<h1>`, the main text, JSON-LD, and internal links as real `<a href>`.
- Nothing a reader came for is in a `LocalResource`, an effect or a client-only component.
- Title and meta tags come from `leptos_meta` components rendered from the same resource as the
  body, in a route whose mode puts them in the head (`Async` or a blocking resource).
- The Open Graph image is an absolute URL, 1200 by 630 by convention.

```rust
use leptos_meta::{Link, Meta, Title};

#[component]
pub fn BlogPost() -> impl IntoView {
    let params = use_params_map();
    let slug = move || params.with(|p| p.get("slug").unwrap_or_default());
    let post = Resource::new_blocking(slug, get_post_by_slug); // blocking: the head waits for it
    view! {
        <ErrorBoundary fallback=|_| view! { <p>"This post could not be loaded."</p> }>
            <Suspense fallback=|| ()>
                {move || Suspend::new(async move {
                    let Some(post) = post.await? else { return Ok(view! { <NotFound/> }.into_any()) };
                    Ok::<_, AppError>(view! {
                        <Title text=post.title.clone()/>
                        <Meta name="description" content=post.summary.clone()/>
                        <Meta property="og:title" content=post.title.clone()/>
                        <Link rel="canonical" href=format!("{SITE_URL}/blog/{}", post.slug)/>
                        <article><h1>{post.title}</h1><div inner_html=post.html></div></article>
                    }.into_any())
                })}
            </Suspense>
        </ErrorBoundary>
    }
}
```

`inner_html` inserts HTML unescaped. Render it on the server from Markdown you control, and
sanitize it (the `ammonia` crate) when a CMS lets editors write raw HTML.

```bash
curl -s "$URL" | grep -oE '<title>[^<]*|<h1[^>]*>[^<]*|rel="canonical"[^>]*'
curl -sA 'Twitterbot/1.0' "$URL" | grep -oE '<meta (property|name)="(og|twitter):[^>]*>'
curl -s -o /dev/null -w '%{http_code}\n' "$ORIGIN/blog/no-such-post"   # 404, run it twice
```

## Where content lives

| Who edits, how often | Put it in | Flip when |
|---|---|---|
| Developer or founder: docs, changelog, legal, a blog of up to a few hundred posts | Markdown in the repo with typed frontmatter, rendered on the server (`pulldown-cmark` or `comrak`) | A non-developer must publish without a pull request |
| Non-developer, occasionally, small site | Git-based CMS (Decap, TinaCMS, Keystatic): an editing UI that commits to the repo | Scheduling, roles, localization or many relations are needed |
| Non-developers weekly; structured content reused across pages | Headless CMS (Sanity, Contentful, Storyblok, DatoCMS) read over its HTTP API with `reqwest` | |
| A marketer owns the marketing site and redesigns it weekly | Site builder (Webflow, Framer) on the marketing hostname, the app on its own | Shared auth, shared components or programmatic pages |

- What users create is product data in the database; content is what the team writes. Splitting
  site builder and app is a hostname decision with search consequences (`seo-aeo-geo-ultimate`).
- Repo Markdown: parse frontmatter with serde into a struct with required fields, at startup or
  in a test, so a missing field fails CI instead of rendering an empty title.

**Content model.** Model by meaning (`post`, `author`, `doc`, `landing_page`), not by layout, and
reference instead of copying. Every routable type has a unique `slug` (changing it writes a
redirect record), title, description, published and updated times, status, and SEO overrides
(title, description, image, noindex). The body is structured rich text or Markdown, never an HTML
blob. A page-builder type is an ordered list from a closed set of about ten blocks, which maps to a
Rust enum with one component per variant. Images carry required alt text and dimensions. Parse CMS
responses into those types with serde at the fetch boundary, so a renamed field fails loudly.

**Publish and preview wiring**, in this order:

1. Reads go through a cache keyed by slug (moka on one instance; Redis or a short TTL across
   several), and public pages carry an `s-maxage`. Nothing regenerates on a timer.
2. The CMS webhook for publish, unpublish and delete hits an Axum route that verifies the
   signature over the raw body and invalidates the entity and every list showing it. Header name
   and encoding below are placeholders: use the scheme the CMS documents.

```rust
use axum::{body::Bytes, extract::State, http::{HeaderMap, StatusCode}};
use hmac::{Hmac, KeyInit, Mac};
use sha2::Sha256;

pub async fn cms_webhook(State(app): State<AppState>, headers: HeaderMap, body: Bytes) -> StatusCode {
    let given = headers.get("x-signature").and_then(|v| v.to_str().ok()).and_then(|s| hex::decode(s).ok());
    let Some(given) = given else { return StatusCode::UNAUTHORIZED };
    let Ok(mut mac) = Hmac::<Sha256>::new_from_slice(app.cms_secret.as_bytes()) else {
        return StatusCode::INTERNAL_SERVER_ERROR;
    };
    mac.update(&body);
    if mac.verify_slice(&given).is_err() { return StatusCode::UNAUTHORIZED } // constant time
    let Ok(event) = serde_json::from_slice::<CmsEvent>(&body) else { return StatusCode::BAD_REQUEST };
    app.posts.invalidate(&event.slug).await; // the entity
    app.post_lists.invalidate_all();         // and every list that shows it
    // ... purge the CDN for /blog/{slug} and /blog
    StatusCode::NO_CONTENT
}
```

3. Preview: the CMS opens `/preview?token=...&slug=...`. The handler checks the token in constant
   time, resolves the slug to real content, marks the session as previewing, and redirects to the
   path of the content it found. Preview responses read the draft API, bypass every cache and send
   `Cache-Control: private, no-store`. Exit with a POST and show editors a banner.

Traps: the webhook can arrive before the CMS read API serves the new version, so the page
re-caches old content (read the uncached endpoint after a webhook). An unsigned webhook route lets
anyone flush the cache. A preview handler that redirects to the raw `slug` parameter is an open
redirect. Unpublish must purge the lists, and the removed URL needs a redirect or a 404.

## Ask the user

- **Who edits content, and how often?** It decides repo, CMS or site builder. Default: the
  developer edits, so Markdown in the repo.
- **How stale may public pages be after an edit?** It sets `s-maxage` and whether a webhook is
  needed. Default: updated within a minute of publishing, by purge.
- **Do search engines, social previews or AI assistants need to read these pages?** Default: yes
  for everything public, no behind login.
- **Will this UI ever ship as a desktop or mobile app from the same code?** Yes favors Dioxus;
  default: no, a responsive web app, packaged later if needed (`0x:frontend-foundations`).
