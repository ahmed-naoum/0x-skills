# Routing and navigation

Read this when: laying out routes and layouts, protecting pages, adding loading, error and
not-found states, building a modal or tab that has a URL, writing redirects or middleware,
fixing Back-button behavior, or moving routes from one router or framework to another.

## Structure routes around the product's navigation

Write the URL map before the folders. URLs are nouns with stable IDs, and their hierarchy matches
what the user sees as nesting: if the sidebar stays while the content changes, that is a layout
with child routes.

```
app/
  (marketing)/layout.tsx     site header and footer        /  /pricing  /blog/[slug]
  (app)/layout.tsx           app shell: sidebar, account    /dashboard
  (app)/projects/[projectId]/layout.tsx       project tabs
  (app)/projects/[projectId]/page.tsx                        /projects/p_123
  (app)/projects/[projectId]/settings/page.tsx               /projects/p_123/settings
  (auth)/login/page.tsx                                      /login
  api/webhooks/stripe/route.ts
```

- Route groups `(name)` give sections different shells without changing URLs. With several root
  layouts, moving between them is a full page load, so prefer one root layout holding `<html>` and
  group layouts beneath it.
- A layout persists across navigation between its children and does not re-render. It holds
  chrome and nothing per page. It cannot read `searchParams`, and it is the wrong place for an
  auth check (below). Use `template.tsx` when the wrapper must remount on each navigation.
- Is a tab a route or state? It is a route when it has its own data or should be linkable; it is
  a search param when it only filters what is already loaded.
- Dynamic segments are `[id]`, catch-all `[...slug]`, optional catch-all `[[...slug]]`. Params
  are strings from the URL and untrusted: validate, and call `notFound()` on failure.
- Components used by one route live in a private `_components/` folder beside it. Shared ones
  live outside `app/`.
- A segment has either `page.tsx` or `route.ts`, not both.
- Three to four levels of nested layouts is the practical limit. Past that, nobody can say which
  layout owns which piece of the screen.

## Protect routes on the server, in three layers

| Layer | Where | What it does | What it cannot do |
|---|---|---|---|
| 1. Optimistic redirect | `proxy.ts` (called `middleware.ts` before Next 16) | Sends visitors without a session cookie to login before anything renders. No database call | Prove anything. Matchers have gaps, and server functions POST to whichever page uses them |
| 2. Session check | A `verifySession()` in the data access layer, called by every page, server function and route handler that needs a user | The real authentication check | Decide access to a specific record |
| 3. Authorization | Inside each data function: does this user, in this tenant, own this row | The real access decision | Nothing; this is the layer that must not be missing |

```ts
// lib/dal.ts
import 'server-only'
import { cache } from 'react'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export const verifySession = cache(async () => { // one lookup per request, however many callers
  const session = await decrypt((await cookies()).get('session')?.value)
  if (!session) redirect('/login')
  return session
})
```

- Not in a layout. Layouts do not re-run on client navigation, and they do not gate what renders
  beneath them: pages and parallel slots render regardless, and their output is in the response.
- Not on the client. A `useEffect` that redirects runs after the protected markup and its data
  have reached the browser.
- Not in `proxy` alone. In March 2025 a single spoofed header skipped Next.js middleware
  entirely (CVE-2025-29927). Apps whose only check lived there were open; apps with layer 2 were
  not.
- For another tenant's resource return "not found", not "forbidden". A 403 confirms the ID exists.
- A `?next=` return path is accepted only when it is a relative path on this origin. Anything
  else is an open redirect.
- A statically cached page is identical for everyone. Per-user content on it goes in a dynamic
  hole or the route is not cached.
- `forbidden()` and `unauthorized()` are still behind an experimental flag. Use `redirect()` and
  `notFound()`.

Session mechanics and permission models: `0x:auth-identity`.

## Loading, error and not-found per segment

| File | Purpose | Notes |
|---|---|---|
| `loading.tsx` | Instant fallback while the segment's page loads | A Suspense boundary around the page. Size it like the content |
| `error.tsx` | Replaces the segment when rendering throws | Client component. Receives `error` and `reset`. Does not catch errors from the same segment's `layout.tsx`: the parent's boundary does |
| `global-error.tsx` | Catches errors in the root layout | Must render its own `<html>` and `<body>` |
| `not-found.tsx` | UI for `notFound()` and unmatched URLs | One at the root; add one per section that deserves a tailored message |
| `default.tsx` | Fallback for a parallel slot with no match | Required for every named slot since Next 16 |

```tsx
'use client'
import { startTransition } from 'react'
import { useRouter } from 'next/navigation'

type Props = { error: Error & { digest?: string }; reset: () => void }

export default function ProjectError({ error, reset }: Props) {
  const router = useRouter()
  const retry = () =>
    startTransition(() => {
      router.refresh() // refetch the server data that failed
      reset()          // then re-render what the boundary replaced
    })
  return (
    <div role="alert">
      <p>Something went wrong{error.digest ? ` (ref ${error.digest})` : ''}.</p>
      <button onClick={retry}>Try again</button>
    </div>
  )
}
```

- `reset()` alone re-renders the boundary with the same failed server result. Pair it with
  `router.refresh()` in one transition, as above. Where the installed version's docs list a retry
  function among the error props that does both, use that.
- Every segment that loads its own data gets `loading.tsx` or Suspense boundaries, and the app
  has more than a root `error.tsx`. With only a root boundary, one failed widget blanks the whole
  shell.
- In production, messages of errors thrown on the server are replaced by a generic text and a
  `digest`. Show the digest, log it on the server, and report through the error tracker in
  `instrumentation.ts` (`onRequestError`). Never render `error.message` from a server error.
- Expected failures (validation, empty results, no permission) are rendered states or return
  values, not thrown errors.
- A true 404 status needs `notFound()` before anything streams (`rendering-strategies.md`).
- Check each state by hand once: throttle the network for loading, throw in a data function for
  error, request an unknown ID for not-found.

## Back, forward, scroll and focus

Back must return the user to the screen they left: same scroll position, same filters, same
loaded items, typed input intact.

- State kept in the URL is restored for free. That is the main reason filters, tabs and
  pagination live there (`data-state.md`).
- The router restores scroll position on back and forward and scrolls to the new page's top on
  a push. `scroll={false}` on a link is for in-place changes such as tabs and filters.
- Infinite lists: Back lands at the top unless the loaded pages are still in a cache. Keep them
  in the query cache, or put the page or cursor in the URL. For virtualized lists also restore the
  scroll offset.
- With Cache Components, Next.js keeps recently visited routes mounted but hidden (`<Activity>`),
  so component state and form drafts survive Back without extra work. State that should reset on
  each visit now needs a `key`, and effects must clean up properly because they are torn down
  while hidden. After sign-out do a full page load so no previous user's state survives.
- Full page loads are restored from the browser's back/forward cache unless the page opts out
  with `unload` handlers and similar (`0x:web-performance`).
- Focus: after a client navigation a screen-reader user needs to know the page changed. Next.js
  announces the new document title, then the `<h1>`, so every route has a unique title and one
  `<h1>`. Elsewhere, move focus to the main heading on navigation. Closing a dialog returns focus
  to the control that opened it (`0x:accessibility`).
- Sticky headers hide anchor targets. Set `scroll-margin-top` on headings.

## Modals and parallel routes that deep-link

Give a modal a URL only when it should survive reload or be shared: a photo, an item's detail,
a create form with a draft. A confirmation dialog is local state.

```
app/
  layout.tsx                     renders {children} and {modal}
  @modal/default.tsx             returns null
  @modal/(.)photo/[id]/page.tsx  the photo inside a dialog   (client navigation)
  @modal/[...catchAll]/page.tsx  returns null                (closes it on any other navigation)
  photo/[id]/page.tsx            the full page               (direct visit, reload, shared link)
```

- Both pages render one shared `<Photo id>` component. The interception adds only the dialog
  frame.
- Close with `router.back()`, so Back and the close button do the same thing.
- `(.)` matches the same level, `(..)` one level up, `(...)` the app root. Levels count route
  segments. Slots (`@modal`) and groups (`(app)`) are not segments.
- A slot without `default.tsx` fails the build in Next 16; before that it returned 404 on reload.
- Do not add a root `app/default.tsx` beside a slot catch-all. Together they match every URL, and
  unknown paths render an empty page with status 200 instead of 404.
- A layout that shows one of two slots still renders both on the server. Authorize inside each.
- Slots at one level are all static or all dynamic.

Verify four things: a click opens the dialog and changes the URL; Back closes it; reload shows the
full page; and `curl -s -o /dev/null -w '%{http_code}' "$ORIGIN/no-such-page"` still prints 404.

## Redirects, rewrites and middleware

| Need | Put it in |
|---|---|
| A known, fixed set of moved URLs | `redirects` in `next.config`, or the CDN |
| More than about a thousand redirects, or redirects edited without a deploy | A lookup in `proxy` against a generated map, or the CDN's redirect rules |
| A decision per request: session cookie, locale, tenant hostname, experiment bucket | `proxy` |
| After a mutation | `redirect()` in the server function |
| Another origin serving a path prefix | `rewrites` in `next.config` |

Order: `headers` and `redirects` from the config run first, then `proxy`, then filesystem routes
and `rewrites`. A path the config redirects never reaches `proxy`.

```ts
// proxy.ts (project root, or src/)
import { NextResponse, type NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (pathname.startsWith('/dashboard') && !request.cookies.has('session')) {
    const login = new URL('/login', request.url)
    login.searchParams.set('next', pathname)
    return NextResponse.redirect(login)
  }
  return NextResponse.next()
}

export const config = {
  // skip build assets, the image optimizer and any path that ends in a file extension
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.[\\w]+$).*)'],
}
```

- `proxy` runs for every matched request, prefetches included. No database or network call per
  request: read cookies and headers and decide. `proxy.ts` runs on the Node.js runtime; code that
  needs the edge runtime stays in the deprecated `middleware.ts`.
- Pass facts to the app as request headers, and delete any incoming header of the same name
  first, or a client can forge it.
- Permanent redirects (308, 301) are cached by browsers for a long time. Ship as 307, confirm,
  then make it permanent. `redirect()` answers 307, `permanentRedirect()` 308, and a form posted
  without JavaScript gets 303.
- Locale: a `[locale]` segment and prefixed URLs (`/de/pricing`). Negotiate from
  `Accept-Language` only for a first visit to an unprefixed URL, remember the choice in a cookie,
  and never redirect a URL that already carries a locale. Message catalogs and formatting:
  `0x:frontend-foundations`. `hreflang`: `seo-aeo-geo-ultimate`.
- Tenant by hostname: `proxy` rewrites `acme.example.com/x` to an internal `/t/acme/x`. Validate
  the hostname against known tenants, with a cached lookup. Put the tenant in every cache tag and
  every cached function's arguments, or one tenant is served another's page. Data isolation:
  `0x:backend-architecture`.

## Typed links and params

- `typedRoutes: true` in `next.config.ts` makes `<Link href>`, `router.push` and `redirect`
  reject paths that do not exist. Template literals check too (`/blog/${slug}`); a computed string
  needs `as Route`.
- `next typegen` writes the route types without a dev server or a build. CI runs `next typegen &&
  tsc --noEmit`. It also provides `PageProps<'/blog/[slug]'>`, `LayoutProps` and `RouteContext`,
  so params are typed from the folder name.
- Types say a param is a `string`. They do not say it is a valid ID. Parse it with Zod at the
  top of the page.
- Keep one `routes.ts` with builder functions (`routes.project(id)`) for dynamic paths, so a
  rename is one edit and navigation data can be typed as `Route`.
- `searchParams` values are `string | string[] | undefined`. Parse them through a schema once
  per page, not ad hoc in components.
- Where typed search params are central (dense filter UIs), TanStack Router types them end to
  end. Its file-based route generation is the equivalent of `next typegen`.

## Migrating routes between routers or frameworks

Move route by route behind a router that decides which system serves each path. A rewrite in one
go loses to schedule and regressions.

| From, to | Mechanism |
|---|---|
| Next.js Pages Router to App Router | `pages/` and `app/` coexist in one app. Move leaf routes first and the shared shell last. Crossing between routers is a full page load |
| Vite or CRA single-page app to Next.js | Mount the whole SPA in one client-only optional catch-all route, then peel routes off into real pages |
| Between frameworks, or splitting one app in two | A reverse proxy or `rewrites` sends each path prefix to exactly one app. The second app sets `assetPrefix` so its assets do not collide |

1. Inventory routes with traffic and revenue per route. Write a test that requests every public
   URL and asserts its status, redirect target and canonical tag. That file is the contract.
2. Move one low-risk route end to end, with auth, analytics, error reporting and deploy, to prove
   the plumbing.
3. Share the session through a cookie on the parent domain and the design through a package.
4. Links that cross systems are plain `<a href>`. A framework `<Link>` prefetches and
   soft-navigates into a route it does not own.
5. After each move, compare error rate, conversion and search impressions with the week before.
6. Switch back by flipping the routing rule. Delete old code only when its route has been dark
   for a release.

Traps: trailing-slash policy differing between the two systems (redirect loops and duplicate
URLs); a service worker still serving the old shell; analytics counting a cross-system navigation
twice; global CSS loaded by both shells; a cookie scoped to the old path or host.

## Ask the user

- **Which pages are public, which need sign-in, and which need a role?** Access rules are product
  decisions. Default: marketing and auth pages public, everything else signed-in, admin by role.
- **Should this dialog or tab have its own link?** Default: yes when it shows a specific item or
  holds work in progress; no for confirmations and menus.
- **Do old URLs have inbound links or search traffic?** If so every changed URL needs a permanent
  redirect and a test. Default: assume yes for anything that was public.
- **Which languages and regions, and do tenants get their own subdomain or domain?** Both shape
  the URL scheme, which is expensive to change later. Default: one locale without a prefix, and
  tenants as a path segment.
- **For a migration: is a period with two systems acceptable?** It is the safe path and costs
  duplicated shell work. Default: yes, route by route.
