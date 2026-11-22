---
name: react-nextjs
description: Builds the React and Next.js application layer of a web product, covering rendering and caching per route, content sources, server components and functions, data and state, routing, component design and build tooling. Use when choosing a framework, CMS or blog setup, fixing stale data, hydration errors, request waterfalls or undefined environment variables, or structuring routes, layouts and components.
---

# React and Next.js application architecture

## Stance

The server is the default place for code. A page starts as HTML rendered from data on the
server; browser JavaScript, client state and request-time work are each added for a reason that
can be named. Most frontend trouble in a small product has one of three causes: a cache nobody
declared, a copy of server data held in client state, or a client boundary set too high in the
tree. Look for those three before anything more exotic.

1. **Follow the project, then the installed version.** Read `next.config`, the lockfile and the
   docs bundled with the installed package before writing against an API. Next.js changes caching
   and routing between majors, and an API remembered from another major fails or misbehaves.
2. **Rendering is decided per route, static first.** A static page cannot be slow under load and
   survives a database outage. Go to request time only for per-user or must-be-fresh data, and
   stream that part instead of making the whole route dynamic.
3. **Every cache has a stated lifetime and a tag, and every write invalidates.** A cache nobody
   declared and a write that tells no cache are the same stale-data bug. Per-user data never
   enters a shared cache.
4. **Client components are leaves.** `'use client'` ships the file and everything it imports, and
   serializes its props into the HTML where anyone can read them. Put the directive on the
   interactive element and pass server-rendered content through as `children`.
5. **A server function is a public endpoint.** On every call it identifies the caller, parses the
   input, authorizes against the specific row, writes, and invalidates. A check in the page, a
   layout or `proxy` does not protect it.
6. **Each piece of state has one owner.** Server data lives in the server render or a query
   cache, view state in the URL, ephemeral state in one component, and derived values are computed
   during render. A copy has no invalidation and goes wrong on the next write.
7. **Public pages are complete in the first HTML response.** Link-preview bots and most AI
   crawlers run no JavaScript, and the status code is fixed once streaming starts.
8. **Split components at server, data, update-rate and failure boundaries**, not by line count,
   and build interactive widgets from one headless primitive library, because focus and keyboard
   behavior are the part hand-built widgets skip.
9. **Use the framework's bundler and its defaults.** Custom build configuration is maintained by
   one person forever, and a public env prefix publishes the value to every visitor.

## Route

| If the task is | Read |
|---|---|
| Picking a framework; deciding whether a page is static, server-rendered, streamed or client-side; a page serves old content or turned dynamic; adding a blog, docs or a CMS; preview and publish webhooks; link previews or crawlers see an empty page; moving Next.js off a managed host | `references/rendering-strategies.md` |
| Server component or client component; writing a server action; a database or secret import reached the browser; Suspense and loading skeletons; a page slow from sequential fetches; a hydration error; too much JavaScript hydrating | `references/server-components.md` |
| Where a piece of state should live; setting up a query cache; filters, tabs or pagination in the URL; the UI is stale after a save; optimistic updates; form pending and error states; an effect that syncs state; merging realtime events; `useMemo` versus the React Compiler | `references/data-state.md` |
| Laying out routes and layouts; protecting pages; loading, error and not-found pages; Back button, scroll or focus problems; a modal with its own URL; redirects, locale prefixes or tenant subdomains; typed links; moving off the Pages Router, a single-page app or another framework | `references/routing-navigation.md` |
| Building or restyling a UI component; shadcn-style setup; designing props; splitting a large component; writing a custom hook; variants; Storybook; a long or slow list; reviewing a frontend pull request | `references/components.md` |
| The build fails or is slow; Turbopack, Vite or Webpack configuration; tsconfig and path aliases; an environment variable is undefined in the browser or leaked; fonts, images, SVG or CSS wiring; ESM and CommonJS errors; browser targets; pinning versions and upgrading the framework | `references/build-tooling.md` |

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Framework | Next.js App Router | Content site with little interactivity: Astro. App wholly behind login with explicit loaders: React Router. Existing server-rendered backend with modest interactivity: HTML over the wire |
| Public pages | Static, regenerated by tag invalidation on publish | Shared data changing through the day: add a cache lifetime |
| Pages behind login | Rendered per request on the server and streamed, no shared cache | Heavy editor or canvas: server frame, client body with a query cache |
| Next.js caching model | The one the project is in (`cacheComponents` set or not), never mixed | Enabling the flag in an existing app is a planned migration |
| Content | MDX in the repo with validated frontmatter | A non-developer must publish without a pull request: git-based or headless CMS |
| Reads | Server components calling a server-only data layer, deduplicated per request | Infinite scroll, polling, type-ahead, optimistic lists: add TanStack Query |
| Writes | Server functions returning a typed result | Callers that are not this app's browser code: a route handler over the same data function |
| View state | URL search params, parsed with defaults | State nobody would share or restore: local state |
| Shared client state | Context for values that change rarely | Frequent updates or readers outside React: a small store, created per request |
| Forms | `<form action>` with `useActionState` and one Zod schema on both sides | Field arrays or per-keystroke validation: a form library |
| UI primitives | One headless library wrapped once in `components/ui/`, typed variants from tokens | A native element already does the job |
| Memoization | React Compiler on for new projects, no hand-written `useMemo` | Existing manual memoization stays until tests cover its removal |
| Access control | Session check in the data layer on every page, function and handler; `proxy` only redirects | No exception |
| Bundler | Turbopack in Next.js, Vite elsewhere | A Webpack plugin with no replacement |
| TypeScript | `strict`, `noUncheckedIndexedAccess`, `moduleResolution: "bundler"`, one alias | Code Node runs unbundled: `nodenext` |
| Toolchain | Node LTS and pnpm pinned to exact versions, frozen-lockfile installs | No exception |

By stage:

- **Prototype**: a managed platform, MDX content, no client query cache until a trigger above
  appears, no Storybook, no virtualization, a root error boundary plus one per app section. Do
  not self-host on several instances and do not migrate caching models.
- **Launch**: row-level authorization in every server function; cache tags built by functions in
  one file; loading, error and not-found states per data segment; the error tracker wired through
  `instrumentation.ts`; environment variables validated at startup; a test that requests every
  public URL; React and framework security releases deployed the day they ship.
- **Scale**: a shared cache handler across instances, typed routes with a route-builder module,
  a component workshop whose stories run in CI, browser targets taken from analytics, and bundle
  budgets from `0x:web-performance`.

## Before you call it done

1. The route table printed by `next build` shows each route with the rendering intended. No
   public page became dynamic through a cookie or header read in a layout.
2. `curl -s` of each public page contains the title, the `<h1>`, the main text, the canonical
   link and the Open Graph tags, and an unknown slug answers 404 on the first and second request.
3. Every cached function states a lifetime and tags. Every mutation invalidates the entity and
   its collection (tags or query keys). Proven by writing and seeing the new value in the list
   and the detail view without a reload.
4. Every server function identifies the caller, parses input with a schema, checks ownership of
   the row and returns a typed result. No `'use server'` file exports a helper.
5. Data-layer, session and env modules start with `import 'server-only'`. Each `'use client'` on
   a page or layout has a stated reason.
6. Props passed to client components hold only rendered fields. The page HTML contains no field
   that should be private (search it for an email address or an internal flag).
7. Independent fetches run in parallel. Each streamed region has a fallback of the final size
   and its own error boundary, and the largest above-the-fold element is not behind a boundary.
8. The console shows no hydration warning in a private window with extensions off.
9. No server data copied into `useState` or a store, and no effect that only sets state.
   Filters, tabs and pagination survive reload, a pasted link and Back.
10. Forms show pending state and field errors, keep the user's input after a failed validation,
    and a double submit creates one record.
11. Signed-out and wrong-tenant requests to protected pages and to their server functions
    return a redirect or "not found", never content. Tested with `curl`, not by clicking.
12. `next typegen && tsc --noEmit` and the linter pass, and a fresh clone builds after
    `pnpm install --frozen-lockfile` with no other steps.
13. `grep -rlE "sk_live|SECRET|PRIVATE KEY" .next/static` prints nothing, and every
    public-prefixed variable is a value meant to be public.
14. Interactive widgets come from the primitive library and list keys are stable IDs from the
    data.

## Not this skill

- Plain HTML, CSS, TypeScript language questions, form field design and animation →
  `0x:frontend-foundations`
- Bundle size, Core Web Vitals, image formats and font loading strategy → `0x:web-performance`
- Design tokens, visual design and UX flows → `0x:ui-ux-design`
- three.js scenes and 3D product pages → `0x:3dui`
- API contracts the frontend consumes, idempotency and rate limits → `0x:api-design`
- Search rankings, metadata strategy and AI-search visibility → `seo-aeo-geo-ultimate`
- Session mechanics, sign-in flows and permission models → `0x:auth-identity`
- Keyboard, focus and screen-reader requirements for components → `0x:accessibility`
