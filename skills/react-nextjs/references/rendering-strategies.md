# Framework, rendering strategy and content sources

Read this when: choosing a framework, deciding how a route is rendered, cached and revalidated,
making pages readable by crawlers and link previews, deciding where editable content lives, or
moving a Next.js app off a managed platform.

## Read the project before deciding anything

```bash
node -p "require('next/package.json').version"     # the installed version, not the remembered one
grep -nE "cacheComponents|output:|experimental|webpack" next.config.*
ls node_modules/next/dist/docs 2>/dev/null          # docs for exactly this version (16.2 and later)
```

Next.js changes caching and routing APIs between majors and sometimes minors. When
`node_modules/next/dist/docs/` exists, read the matching page there before writing against an
API from memory: it is the only description guaranteed to match the installed code. Apply the
same habit to any meta-framework: installed version first, then its docs.

## Rendering: decide per route

Four questions settle it: is the response the same for every visitor; how stale may it be; must a
crawler or link preview read it without running JavaScript; is it behind login.

| Route | Strategy |
|---|---|
| Marketing, pricing, blog, docs, changelog | Static, regenerated when content is published (tag invalidation) |
| Catalog or listing whose shared data changes through the day | Static with a cache lifetime, plus on-demand invalidation |
| Mostly shared page with a per-user piece (cart count, account menu) | Static shell, per-user piece streamed into a hole |
| Dashboard, settings, anything per user behind login | Rendered per request on the server and streamed; no shared cache |
| Heavy interactive tool behind login (editor, canvas, map) | Server-rendered frame, client-rendered body with a client data cache |
| Search and filtered lists | Server-rendered from the URL query; cache the query function by its arguments |
| Internal admin tool or embeddable widget | A client-rendered SPA is acceptable |

- Rendering is a per-route and, with partial prerendering, per-component choice. "Is this app SSR
  or static?" is the wrong question.
- Default to static. A static page cannot be slow under load and survives a database outage. Move
  down the table only when a question above forces it.
- Client-only rendering of public content gives up crawlability and first paint. Keep it behind
  login.
- Per-user data never enters a shared cache. In practice: a cached function receives the user or
  tenant ID as an argument, or it is not cached.

Check the result in the route table `next build` prints: `○` static, `◐` partial prerender, `ƒ`
dynamic. A marketing page marked `ƒ` is a bug: something in its tree reads cookies, headers or
search params, usually an auth or theme lookup in the root layout.

## Next.js has two caching models

| | Cache Components (`cacheComponents: true`) | Previous model (flag absent) |
|---|---|---|
| Found in | Next 16 apps whose `next.config` sets the flag. Read the file; do not infer it from the version | Next 15 apps and most upgraded apps |
| Default | Nothing is cached; request-time work must sit in `<Suspense>` or be cached, and the dev overlay and build say so | `fetch` is uncached; a route is static unless it uses request APIs |
| Opt into caching | `'use cache'` with `cacheLife()` and `cacheTag()` in a function or component | `fetch(url, { next: { revalidate, tags } })`, `unstable_cache`, `export const revalidate` |
| Force request time | `await connection()`, or read `cookies()`/`headers()`, inside `<Suspense>` | `export const dynamic = 'force-dynamic'` |
| Segment config | `dynamic`, `revalidate` and `fetchCache` exports are rejected | Available |
| Partial prerendering | The default behavior | Not available |

Use the column the project is in and do not mix them. Turning the flag on in an existing app is a
migration, not a setting: every request-time read needs a boundary or a cache directive, and the
build names the routes that lack one. Do it on a branch, one route at a time, and not at all
during Prototype unless the app is new.

## Cache with explicit lifetimes and tags

```ts
// lib/posts.ts
import 'server-only'
import { cacheLife, cacheTag } from 'next/cache'

export async function getPost(slug: string) {
  'use cache'
  cacheTag('posts', `post:${slug}`) // collection tag and entity tag
  cacheLife('max')                  // changes only on publish; the webhook invalidates
  return db.post.findBySlug(slug)   // a null result is cached too, under the same tags
}
```

- **Tag scheme**: one tag per collection (`posts`), one per entity (`post:<slug>`), and the tenant
  in both for tenant data (`t:<id>:posts`). Build tags with functions in one file. A misspelled
  tag fails silently: nothing errors and nothing updates. Tags are case-sensitive, 256 characters
  at most.
- **Lifetime**: every cached scope calls `cacheLife` so the choice is visible. Profiles `minutes`,
  `hours`, `days`, `weeks`, `max` regenerate after 1 minute to 30 days. Content that changes only
  when someone publishes gets `max` plus a tag. The `seconds` profile, or an `expire` under 5
  minutes, is too short to prerender and becomes a dynamic hole.
- **Cache key**: arguments, closed-over values and the build ID. So pass IDs, not request-shaped
  objects; a deploy starts with an empty cache; and a cached scope cannot call `cookies()` or
  `headers()`. Read them outside and pass the value in.
- **Cached misses**: a cached not-found sticks for the whole lifetime. Creating content at that
  slug later needs the collection tag invalidated, which is why the publish webhook revalidates
  both tags.

| Call | Callable from | Effect | Use for |
|---|---|---|---|
| `updateTag(tag)` | Server Actions | Expires now; the next read waits for fresh data | The user's own write must be visible at once |
| `revalidateTag(tag, 'max')` | Actions, route handlers | Marks stale; the next request is served stale and triggers regeneration | Publish webhooks, shared content |
| `revalidateTag(tag, { expire: 0 })` | Actions, route handlers | The next request blocks on fresh data | Webhooks where stale must never be served again (price, legal text) |
| `revalidatePath(path)` | Actions, route handlers | Invalidates one route | Only when no tag exists |
| `refresh()` | Server Actions | Re-renders the uncached parts of the current route | A write that touched only uncached data |

The one-argument `revalidateTag(tag)` is deprecated in 16. Regeneration is triggered by the next
request, not by the call, so with `'max'` the first visitor after a publish still sees the old
page. Runtime entries live in memory per instance; on serverless they rarely survive between
requests, and `'use cache: remote'` moves them to a shared handler when the hit rate justifies a
network round trip.

## Static shell, dynamic holes

Partial prerendering sends a shell built ahead of time (static markup, cached results and
`<Suspense>` fallbacks), then streams the holes in the same response.

- The deeper a request-time read sits, the larger the shell. One `cookies()` call in the root
  layout shrinks the shell to a fallback. Move the read into the leaf that needs it, inside
  `<Suspense>`; pass the `params` promise down and await it in the child.
- A route with any hole is answered with a private, uncacheable `Cache-Control`. A plain CDN in
  front of a self-hosted server caches only fully static routes; the shell of a partial route
  still comes from the origin. Platforms with partial-prerender support serve the shell from the
  edge.
- A param not returned by `generateStaticParams` can receive the generic shell with status 200
  before the page has decided the item exists. A later `notFound()` then arrives in the stream as
  the not-found UI plus `<meta name="robots" content="noindex">`. Where the status matters (a
  public catalog), decide existence before anything suspends, and test an unknown slug with the
  `curl` check below, twice, because the first response and later ones can differ.
- Islands are the same idea from the other direction. In Astro the page is static HTML and each
  interactive component hydrates alone (`client:visible`, `client:idle`); `server:defer` adds a
  per-request server island.

## HTML that crawlers and link previews can read

Link-preview bots (Slack, X, WhatsApp, LinkedIn, iMessage) and most AI crawlers do not run
JavaScript. Google does, later and on a budget. So for every public page:

- The first HTML response holds `<title>`, meta description, canonical URL, Open Graph tags, the
  `<h1>`, the main text, JSON-LD, and internal links as real `<a href>`.
- Nothing a reader came for is fetched in `useEffect` or rendered with `ssr: false`.
- Metadata comes from `generateMetadata` calling the same cached data function as the page. Next
  streams metadata to browsers and blocks on it for bots it recognizes as HTML-limited by user
  agent, so test with a bot user agent.
- Status is decided before anything suspends. Once streaming starts the status is 200: a late
  `notFound()` becomes not-found UI plus `noindex`, and a late `redirect()` becomes a client-side
  redirect.
- The Open Graph image is an absolute URL, 1200 by 630, per page (`opengraph-image.tsx`) or static.

```bash
curl -s "$URL" | grep -oE '<title>[^<]*|<h1[^>]*>[^<]*|rel="canonical"[^>]*'
curl -sA 'Twitterbot/1.0' "$URL" | grep -oE '<meta (property|name)="(og|twitter):[^>]*>'
curl -s -o /dev/null -w '%{http_code}\n' "$ORIGIN/blog/no-such-post"   # run it twice
```

What to rank for, metadata wording and structured-data strategy: `seo-aeo-geo-ultimate`.

## Choosing a framework

Follow the project. For a new one:

| Building | Choose | Why, and the catch |
|---|---|---|
| Product with public pages and an app behind login | Next.js App Router | One codebase, server components, per-route rendering, the largest ecosystem. Off its home platform, hosting takes work (last section) |
| Content site with little interactivity | Astro | No JavaScript by default, islands where needed, typed content collections. Switch to Next when site and app must share components and session |
| App entirely behind login, explicit loaders and actions preferred | React Router, framework mode | Simple request and response model on Vite, runs on any Node host. Its server components support is still experimental |
| Client-heavy app that wants typed routes and search params end to end | TanStack Start | The typed router is the reason to pick it. 1.0 is recent, the ecosystem is smaller, server components are experimental |
| Team already fluent in Svelte or Vue | SvelteKit or Nuxt | The UI library decides. All of these render static, on the server and streamed |
| Internal tool over an existing API, no SEO | Vite SPA with a router and a query cache | No server to run |
| Existing Rails, Django, Laravel or Go app with modest interactivity | HTML over the wire | Below |

Do not migrate frameworks to fix what is a caching or configuration problem. A migration costs
weeks and belongs in `routing-navigation.md`, done route by route.

**HTML over the wire** (htmx, Hotwire, Livewire, LiveView) wins when all of these hold: the
backend already renders templates the team is fluent in; the UI is forms, tables, navigation and
fragment swaps; nothing must work offline. The result is one codebase with no JSON API layer,
client state or hydration. It loses when any of these hold: long-lived client state across many
interactions (editors, boards, canvases, multi-step optimistic flows); interactions that cannot
wait a round trip; a native app that needs the JSON API anyway; a design system that exists as
React components. Never mix it into a React-rendered page, because two systems then own the same
DOM. A React island mounted on one element of a server-rendered page is fine. In a TypeScript
stack the equivalent is server components plus form actions that work before hydration.

## Where content lives

| Who edits, how often | Put it in | Flip when |
|---|---|---|
| Developer or founder; docs, changelog, legal, a blog of up to a few hundred posts | MDX or Markdown in the repo, schema-validated frontmatter, built static | A non-developer must publish without a pull request |
| Non-developer, occasionally, small site | Git-based CMS (Keystatic, Decap, TinaCMS): an editing UI that commits to the repo | Scheduling, roles, localization workflow or many relations are needed |
| Non-developers weekly; structured content reused across pages | Headless CMS, hosted (Sanity, Contentful, Storyblok, DatoCMS) or inside the app (Payload) | |
| A marketer owns the whole marketing site and changes its design weekly | Site builder (Webflow, Framer) on the marketing hostname, the app on its own | Shared auth, shared components or programmatic pages are needed |

- What users create is product data and lives in the database. Content is what the team writes.
- Prototype: MDX in the repo ships today, with review, history, rollback and preview deploys for
  free. A hosted CMS adds a vendor, a webhook path, preview wiring and a per-seat bill; a
  self-hosted one adds an admin surface to secure.
- Splitting the site builder from the app is a hostname decision with search consequences
  (`seo-aeo-geo-ultimate`); routing a path prefix to another origin is in `routing-navigation.md`.

**Content model.** Model by meaning (`post`, `author`, `doc`, `landingPage`), not by page layout,
and reference instead of copying. Every routable type has `slug` (unique; changing it writes a
redirect record), `title`, `description`, `publishedAt`, `updatedAt`, status, and SEO overrides
(title, description, image, noindex). The body is structured rich text or MDX, never an HTML blob,
which cannot be restyled, validated or rendered elsewhere. A page-builder type is an ordered list
drawn from a closed set of about ten blocks, each a component with a schema. Images carry alt text
as a required field, and dimensions. Parse CMS responses with Zod at the fetch boundary so a
renamed field fails the build instead of rendering `undefined`.

**Preview and publish wiring**, in this order:

1. Data functions are cached with `cacheLife('max')` and tagged. Nothing regenerates on a timer.
2. The CMS webhook for publish, unpublish and delete calls a route handler that verifies the
   signature and invalidates the tags:

```ts
// app/api/revalidate/route.ts
import { revalidateTag } from 'next/cache'
import { createHmac, timingSafeEqual } from 'node:crypto'

export async function POST(request: Request) {
  const body = await request.text()
  const given = Buffer.from(request.headers.get('x-signature') ?? '')
  const want = Buffer.from(
    createHmac('sha256', process.env.CMS_WEBHOOK_SECRET!).update(body).digest('hex'),
  )
  if (given.length !== want.length || !timingSafeEqual(given, want)) {
    return new Response('bad signature', { status: 401 })
  }
  const { type, slug } = JSON.parse(body) as { type: string; slug?: string }
  if (type === 'post') {
    revalidateTag('posts', 'max')
    if (slug) revalidateTag(`post:${slug}`, 'max')
  }
  return Response.json({ revalidated: true })
}
```

3. Preview: the CMS opens `/api/draft?secret=...&slug=...`. The handler checks the secret,
   resolves the slug to real content, calls `(await draftMode()).enable()` and redirects to the
   path of the content it found. In draft mode cached functions run on every request and the
   response is private. Exit with a form POST and show editors a banner.

Traps: the webhook fires before the CMS read API shows the new version, so the page regenerates
with old content and caches it for the full lifetime (read from the uncached endpoint during
revalidation). An unsigned revalidation endpoint lets anyone flush the cache. A draft handler that
redirects to the raw `slug` parameter is an open redirect. A `<Link>` to a GET exit-preview route
is prefetched and ends the preview on its own. Unpublish must invalidate the collection tag, and
the removed URL needs a redirect or a 404.

## Self-hosting Next.js: what the platform was doing

One `next start` process on one machine with a persistent disk supports every feature. Stay there,
behind a CDN, as long as possible. Each row is something a managed platform did silently:

| Concern | Do |
|---|---|
| Build output | `output: 'standalone'`; copy `public/` and `.next/static/` beside `server.js`; set `HOSTNAME=0.0.0.0` and `PORT` in a container |
| Static assets | `/_next/static/*` is content-hashed: cache it forever at the CDN. Honor the `Cache-Control` and `Vary` Next sends for HTML, and never give HTML and RSC responses different TTLs |
| Streaming | Proxies buffer by default, which removes streaming. nginx: `proxy_buffering off` or an `X-Accel-Buffering: no` response header. Check the load balancer, then verify with `curl -N` |
| Images | Optimization runs in the Node process with sharp and costs CPU and memory. Acceptable when small; otherwise a custom `loader` pointing at an image CDN |
| More than one instance | Each instance has its own cache and `revalidateTag` reaches only one. Shared `cacheHandler` (ISR, `fetch`) and `cacheHandlers` (`use cache`) on Redis, tag sync, `cacheMaxMemorySize: 0` |
| Server functions | Instances built separately need the same `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` at build time, or calls fail with "Failed to find Server Action" |
| Rolling deploys | Set `deploymentId` so a client from the old build reloads instead of failing; keep the previous build's static assets reachable |
| Environment | `NEXT_PUBLIC_*` values are frozen at build: one build per environment, or read on the server at request time (`build-tooling.md`) |
| Shutdown | Send SIGTERM and allow a 10 to 30 second drain so in-flight streams and `after()` callbacks finish |
| No longer included | Preview deploy per pull request, instant rollback, cron, WAF, log drains: `0x:ci-cd-release`, `0x:cloud-infrastructure` |

Other targets go through the Deployment Adapter API. Before choosing a workers or edge runtime,
check the provider's current support list for the features in use (partial prerendering, `use
cache`, image optimization, `proxy`). Multi-instance self-hosting is a Scale concern; at Prototype
and Launch run on a platform that supports Next natively, or one container on a PaaS.

## Ask the user

- **Who edits content, and how often?** It decides repo versus CMS versus site builder. Default:
  the developer edits, so MDX in the repo.
- **How stale may public pages be after an edit?** It sets cache lifetimes and whether a webhook
  is needed. Default: updated within a minute of publishing, by tag invalidation.
- **Do search engines, social previews or AI assistants need to read these pages?** Default: yes
  for everything public, no behind login.
- **Must this run on your own servers or cloud account?** Compliance and cost can force it, and it
  adds the work in the last section. Default: a managed platform until Scale.
- **Does a marketer need to change the marketing site without engineering?** That is the case for
  a site builder on a separate hostname. Default: no, the site lives in the app's codebase.
