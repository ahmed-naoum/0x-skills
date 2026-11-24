# Server functions, actions and forms

Read this when: the browser must call the server or change data; writing or reviewing a
`#[server]` function, an `ActionForm` or an action; showing pending, error or optimistic states;
the page is stale after a save; reading cookies or headers in a server function; or a server-only
crate or secret reached the WASM.

Contents: a server function is a public endpoint; limits, cross-site requests and safe errors;
server code and secrets out of the WASM; forms before the WASM loads; pending, error and
optimistic states; refetch after a write; cookies, headers and redirects; encodings and
streaming; shared types without server-only fields; ask the user.

Snippets assume `use leptos::prelude::*;`, `serde::{Deserialize, Serialize}` and `uuid::Uuid`.

## A server function is a public endpoint

`#[server]` turns an async function into a POST endpoint under `/api/` (the function name plus a
hash of the crate path and module) and, in the WASM build, into a client stub that calls it. Anyone
can call that URL with any arguments. A `ProtectedRoute`, a hidden button or a check in the page
protects nothing. Every function runs the same six steps:

```rust
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize, thiserror::Error)]
pub enum AppError {
    #[error("please sign in")] Unauthorized,
    #[error("not found")] NotFound,
    #[error("{message}")] Invalid { field: String, message: String },
    #[error("something went wrong, please try again")] Internal,
    #[error("the request failed, please try again")] Transport(String), // network, decoding
}

impl FromServerFnError for AppError {
    type Encoder = server_fn::codec::JsonEncoding;
    fn from_server_fn_error(e: ServerFnErrorErr) -> Self { AppError::Transport(e.to_string()) }
}

#[cfg(feature = "ssr")]
impl From<sqlx::Error> for AppError {
    fn from(e: sqlx::Error) -> Self {
        tracing::error!(error = %e, "database error"); // the detail goes to the log only
        AppError::Internal
    }
}

#[server]
pub async fn rename_post(id: Uuid, title: String) -> Result<(), AppError> {
    let user = require_user().await?;                                // 1. who is calling
    let title = Title::parse(&title)                                 // 2. what did they send
        .map_err(|e| AppError::Invalid { field: "title".into(), message: e.to_string() })?;
    let pool = use_context::<sqlx::PgPool>().ok_or(AppError::Internal)?;
    let done = sqlx::query("UPDATE posts SET title = $1 WHERE id = $2 AND author_id = $3")
        .bind(title.as_str()).bind(id).bind(user.0)                  // 3. their row only, and
        .execute(&pool).await?;                                      // 4. the write
    if done.rows_affected() == 0 {
        return Err(AppError::NotFound); // someone else's post looks the same as a missing one
    }
    if let Some(cache) = use_context::<PostCache>() {
        cache.invalidate(&id).await;                                 // 5. invalidate
    }
    Ok(())                                                           // 6. minimal result
}
```

With `query!` in the project, the same SQL is checked at compile time. `Title` is a newtype whose
only constructor validates (garde at the boundary, then the type proves it), and `require_user`
reads the session (below).

- Arguments, hidden inputs and IDs are attacker-controlled. Re-check ownership against the session
  on every call, in the query itself where possible.
- Expected failures (validation, conflict, not allowed) are `AppError` variants the UI renders.
  `ServerFnError::new(e.to_string())` on a database error sends its text, including table and
  constraint names, to the browser.
- For another tenant's resource answer "not found", not "forbidden": a 403 confirms the ID exists.
- Callers that are not this app's browser code (mobile app, webhook, cron) get an Axum JSON route
  over the same data function, with a contract of its own.

## Limits, cross-site requests and safe errors

- **Cross-site requests.** The default input encoding is a URL-encoded POST, which a page on any
  other site can send with a plain HTML form, and Leptos does not check the origin. Set session
  cookies `SameSite=Lax` (or `Strict`) and reject cross-site POSTs in a middleware:

```rust
use axum::{extract::{Request, State}, http::{header, Method, StatusCode}, middleware::Next, response::Response};

#[derive(Clone)]
pub struct PublicOrigin(pub String); // "https://app.example.com", from the typed config

pub async fn same_origin_posts(State(origin): State<PublicOrigin>, req: Request, next: Next) -> Result<Response, StatusCode> {
    if req.method() == Method::GET || req.method() == Method::HEAD {
        return Ok(next.run(req).await);
    }
    let h = req.headers();
    let allowed = match h.get("sec-fetch-site").and_then(|v| v.to_str().ok()) {
        Some(site) => site == "same-origin",
        None => h.get(header::ORIGIN).and_then(|v| v.to_str().ok()) == Some(origin.0.as_str()), // older browsers
    };
    if allowed { Ok(next.run(req).await) } else { Err(StatusCode::FORBIDDEN) }
}
```

  Layer it with `axum::middleware::from_fn_with_state` on the router for pages and server functions;
  webhooks arrive cross-site by design, so merge their router after the layer, signature-checked.
- **Body size and rate.** leptos_axum hands server functions the raw request body, which they
  collect without a limit, and Axum's `DefaultBodyLimit` only binds extractors such as `Bytes` or
  `Json`, so it does not cap them. Put tower-http's `RequestBodyLimitLayer` (its `limit`
  feature) on the router (`build-deploy.md`), sized to the largest form; it answers 413 instead of
  buffering an attacker's gigabyte. Send files to object storage through a presigned URL
  (`0x:backend-architecture`). Rate-limit functions that send
  email, cost money or write in bulk with `tower_governor` (`0x:api-design`).
- **Panics.** Axum does not catch them: a panic in a server function drops the connection and the
  client sees a network error. Add tower-http's `CatchPanicLayer` (its `catch-panic` feature) as a
  backstop, and keep `unwrap()`, `expect()` and `expect_context` out of request paths;
  `use_context` returns an `Option` to map to `AppError::Internal`.
- **Blocking and `Send`.** The function runs on Tokio. Password hashing, image work and other CPU
  work go in `tokio::task::spawn_blocking`. A `std::sync::MutexGuard` held across an `.await` makes
  the future `!Send` and fails to compile; drop the guard before awaiting or use `tokio::sync::Mutex`.

## Keep server code and secrets out of the WASM

The body of a `#[server]` function is compiled only with `ssr`; the hydrate build gets a stub. The
rest of the module is compiled for both, so:

- Server-only crates (sqlx, argon2, reqwest with secrets, tokio) are optional dependencies enabled
  by the `ssr` feature (`build-deploy.md`). Import them inside the function body or in a
  `#[cfg(feature = "ssr")]` module; a top-level `use sqlx::PgPool;` breaks the WASM build.
- Secrets are read at runtime on the server into the typed config and provided as context. Never
  `env!` or `option_env!` in shared code: the value is compiled into whichever binary uses it,
  including the WASM.
- Data-layer modules carry `#[cfg(feature = "ssr")]` on the module declaration, so a client import
  fails to compile instead of shipping.
- Check the output: `grep -c "$SECRET_VALUE" target/site/pkg/*.wasm` prints 0 for each secret.

## Forms that work before the WASM loads

`ActionForm` renders a real `<form method="post">` pointing at the server function. Before the
WASM loads it submits as a normal form: the server runs the function and redirects back to the
`Referer`, and the page renders again with fresh data. After hydration the same form submits
without a page load and the action's signals update.

```rust
#[component]
pub fn RenameForm(id: Uuid, title: String) -> impl IntoView {
    let rename = ServerAction::<RenamePost>::new();
    let error = move || rename.value().get().and_then(|r| r.err()).map(|e| e.to_string());
    view! {
        <ActionForm action=rename>
            <input type="hidden" name="id" value=id.to_string()/>
            <label for="title">"Title"</label>
            <input id="title" name="title" value=title required maxlength="120"
                aria-invalid=move || error().is_some().to_string() aria-describedby="title-error"/>
            <p id="title-error" role="alert">{error}</p>
            <button type="submit" disabled=move || rename.pending().get()>
                {move || if rename.pending().get() { "Saving..." } else { "Save" }}
            </button>
        </ActionForm>
    }
}
```

- Input `name`s are the function's argument names. A struct argument uses `input[field]` names.
- Only the default `PostUrl` input encoding works with `ActionForm`; a function with `Json` input
  needs `action.dispatch(...)` from code.
- HTML constraints (`required`, `maxlength`, `type="email"`) give instant feedback without WASM;
  the server function validates again, because the attributes are advice.
- Without the WASM, a failed call redirects back to the `Referer` with the encoded error in the
  query (`__path` and `__err`). The router reads it during the next server render and
  `ServerAction::new()` for that function starts with the error as its `value()`, so the markup
  above shows it with no WASM. The error therefore lands in the URL, browser history and access
  logs: keep personal data out of `AppError` messages. A successful call redirects to the clean `Referer`; send the user
  elsewhere with `leptos_axum::redirect`.
- Disable the button while pending and make the write idempotent: a double submit makes one record.

## Pending, error and optimistic states

| Signal on `ServerAction` | Gives | Use for |
|---|---|---|
| `pending()` | `true` while a call is in flight | Disabling the button, a spinner on the pressed control |
| `value()` | The last result, `None` before the first | Field errors and success messages |
| `input()` | The submitted arguments while pending, then `None` | Optimistic display |
| `version()` | A counter that increments when a call completes | Refetching resources |

Optimistic UI is for actions that nearly always succeed and whose result the client can compute:
toggle, rename, reorder, add to a list. Not for payments or anything the server calculates.

```rust
let shown_title = move || {
    rename.input().with(|pending| pending.as_ref().map(|p| p.title.clone())) // while in flight
        .unwrap_or_else(|| saved_title.get())                                // after it settles
};
```

When the call fails, `input()` returns to `None` and the saved value shows again, so a failure
reverts by itself; show the error from `value()`. For concurrent submissions (adding todos),
`ServerMultiAction` with `MultiActionForm` keeps one submission per call: render pending items
from `submissions()`, each with a client-generated UUID the server keeps as the real ID. The
server inserts it with `ON CONFLICT (id) DO NOTHING`, never an upsert, so a replayed or forged ID
cannot overwrite another row. `Uuid::new_v4()` in the WASM needs uuid's `v4` and `js` features;
without `js` the hydrate build fails to compile on getrandom.

## After a write, refetch what shows it

Leptos does not know which resources a server function changed; tie them to the action's version:

```rust
let rename = ServerAction::<RenamePost>::new();
let post = Resource::new(move || (id.get(), rename.version().get()), |(id, _)| get_post(id));
let posts = Resource::new(move || rename.version().get(), |_| list_posts());
```

Create the action where every resource showing the changed data can see it (the route component,
or context for app-wide actions). When a successful write leaves the screen stale, check:

1. No resource includes the action's `version` in its source, or the detail does and the list
   does not. Tie both.
2. The action was created in a child component, so another part of the page has its own copy.
3. A server-side cache (moka, CDN) still holds the old value: the function did not invalidate it
   (step 5), or each instance holds its own moka cache and only one was invalidated.
4. Another tab or user wrote it. Invalidation cannot reach them: refetch on focus, poll, or push
   (`routing-data.md`).

## Cookies, headers and responses inside server functions

`leptos_axum::extract()` runs any Axum extractor against the current request. `ResponseOptions`
from context sets status and headers, and `leptos_axum::redirect` sets a redirect that works for
both plain form posts and enhanced calls.

```rust
#[cfg(feature = "ssr")]
pub async fn require_user() -> Result<UserId, AppError> {
    let session: tower_sessions::Session = leptos_axum::extract().await.map_err(|_| AppError::Internal)?;
    session.get::<UserId>("user_id").await.map_err(|_| AppError::Internal)?.ok_or(AppError::Unauthorized)
}

#[server]
pub async fn set_theme(theme: Theme) -> Result<(), AppError> {
    use axum::http::{header, HeaderValue};
    let res = use_context::<leptos_axum::ResponseOptions>().ok_or(AppError::Internal)?;
    let cookie = format!("theme={}; Path=/; Max-Age=31536000; SameSite=Lax; Secure", theme.as_str());
    let cookie = HeaderValue::from_str(&cookie).map_err(|_| AppError::Internal)?;
    res.append_header(header::SET_COOKIE, cookie);
    leptos_axum::redirect("/settings");
    Ok(())
}
```

Shared state (pool, config, caches) is provided as context with `leptos_routes_with_context`
(`build-deploy.md`) or taken from Axum state with `leptos_axum::extract_with_state`. Session and
cookie mechanics: `0x:auth-identity`.

## Encodings and streaming

| Need | Set | Note |
|---|---|---|
| Forms and most calls | Default: `PostUrl` input, `Json` output | Works with `ActionForm` |
| Idempotent reads a CDN or browser may cache | `#[server(input = GetUrl)]` | Arguments land in URLs and logs: no personal data |
| Nested or large structured input | `#[server(input = Json)]` | Not usable from `ActionForm` |
| Large binary payloads | `Cbor` or `Rkyv` (feature flags on `leptos`) | Measure before switching; JSON is easiest to debug |
| Text or bytes produced over time (LLM output, exports) | `#[server(output = StreamingText)]` returning a `TextStream` | Proxies must not buffer the response |
| File uploads | `MultipartFormData` (the `multipart` feature) only for small files | Larger files go to object storage directly |
| A stable URL for callers outside this build | `#[server(endpoint = "...")]` | Default URLs change when the function moves module |

```rust
#[server(output = server_fn::codec::StreamingText)]
pub async fn export_csv(project: Uuid) -> Result<server_fn::codec::TextStream<AppError>, AppError> {
    let user = require_user().await?; // ... and check that `project` belongs to `user`, as above
    let lines = vec![Ok("id,name\n".to_string())]; // ... rows from a paginated query, not one big Vec
    Ok(server_fn::codec::TextStream::new(futures::stream::iter(lines)))
}
```

A streaming function is an endpoint like the others: identify and authorize before the first
byte, because once the stream has started an error can no longer change the status.

## Share types without exposing server-only fields

Types that cross the wire live in the shared crate and derive `Serialize` and `Deserialize`. The
database row is a different type that exists only with `ssr`, and a `From` impl is the one place
that decides what leaves the server.

```rust
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PostView { pub id: Uuid, pub title: String, pub published: bool }

#[cfg(feature = "ssr")]
pub mod db {
    #[derive(sqlx::FromRow)]
    pub struct PostRow {
        pub id: uuid::Uuid,
        pub title: String,
        pub published_at: Option<time::OffsetDateTime>,
        pub author_email: String,             // never leaves the server
        pub moderation_notes: Option<String>, // never leaves the server
    }

    impl From<PostRow> for super::PostView {
        fn from(r: PostRow) -> Self { Self { id: r.id, title: r.title, published: r.published_at.is_some() } }
    }
}
```

`#[serde(skip)]` on one shared struct is not a boundary: the next derive or a hand-written impl
sends the field. Because the server function's argument struct is public too, never accept a type
with fields the caller must not set (owner, role, price); take IDs and look the rest up.

## Ask the user

- **Who may perform this action?** Authorization is a business rule code cannot reveal. Default:
  only the owner of the resource, or members of its tenant with a write role; everyone else gets
  "not found".
- **Must this form work before the WASM loads?** Default: yes for sign-in, checkout and contact
  forms; no for editors and other rich tools.
- **Should this action look instant, with the risk of visibly undoing it on failure?** Default:
  optimistic for toggles, renames and reorders; wait for the server for money, deletion and
  anything irreversible.
- **Will anything other than this web app call these endpoints?** Default: no; a mobile app or
  partner gets a versioned JSON API instead (`0x:api-design`).
