# Server components, server functions and hydration

Read this when: writing or reviewing React Server Components or server functions (Server Actions),
placing Suspense boundaries and loading states, fixing a page made slow by sequential fetches, or
chasing a hydration error or heavy hydration.

## Where the client boundary goes

`'use client'` marks a boundary in the module graph, not a component: that file and everything it
imports ships to the browser. It does not mean "renders only in the browser"; client components
are still rendered to HTML on the server and then hydrated.

| The component needs | It is |
|---|---|
| State, effects, event handlers, refs, browser APIs, context | A client component, as small as possible |
| Data access, secrets, heavy formatting libraries (markdown, syntax highlighting, date locales) | A server component |
| Both | A server parent that fetches, and a client leaf that receives the fields it renders |

- Push the directive down to the interactive leaf: `LikeButton`, not `PostPage`.
- Pass server-rendered content through client components as `children`. A client `Dialog`, `Tabs`
  or provider can wrap server components without turning them into client code.
- A third-party component that uses hooks but lacks the directive gets re-exported from one small
  `'use client'` file of your own.
- Props crossing the boundary are serialized into the HTML. They must be serializable (no
  functions except server functions, no class instances) and they are public. Passing a whole
  database row ships every column to the browser; pass the fields that are rendered.
- Adding `'use client'` to a page or layout to silence an error moves the whole subtree to the
  browser. Find the leaf that needs it instead.

```bash
find app src \( -name 'page.tsx' -o -name 'layout.tsx' \) -exec grep -l "use client" {} + 2>/dev/null
```

Every file this prints needs a reason.

## Server-only modules

Put `import 'server-only'` on the first line of the database client, the data access layer, the
session code, the server env module and anything holding an API key. A client import then fails
the build with `You're importing a module that depends on "server-only"` followed by import
traces; the trace labeled `[Client Component Browser]` is the offending chain.

Without the marker the bundler includes the module without complaint. Server environment variables
are `undefined` in the browser, so the result is a runtime bug at best and a leaked secret at
worst (someone "fixes" it with a public prefix).

- Keep data access in one server-only folder (`lib/dal/` or `server/`). Its functions verify the
  session, authorize, and return plain objects holding only what the UI needs. Components never
  import the database client; a `no-restricted-imports` lint rule holds that line.
- Use `import type` when client code needs only a type from a server module.
- `client-only` is the mirror, for modules that touch `window` at import time.
- Outside Next.js, install the `server-only` package; it works through the `react-server` export
  condition in any bundler that supports server components.

## Server functions

A server function is a public POST endpoint whose URL the framework hides. Anyone can call it
with any arguments. A check in the page that renders the form, or in `proxy`, does not protect it.
Every function runs the same six steps:

```ts
'use server'
import { updateTag } from 'next/cache'
import { z } from 'zod'
import { verifySession } from '@/lib/dal'

const Input = z.object({ id: z.string().min(1), title: z.string().trim().min(1).max(120) })

export async function renamePost(_prev: RenameState, formData: FormData): Promise<RenameState> {
  const session = await verifySession()                          // 1. who is calling
  const parsed = Input.safeParse(Object.fromEntries(formData))   // 2. what did they send
  if (!parsed.success) {
    return { ok: false, fieldErrors: z.flattenError(parsed.error).fieldErrors }
  }
  const post = await db.post.findById(parsed.data.id)            // 3. may they touch this row
  if (!post || post.authorId !== session.userId) return { ok: false, message: 'Not found' }
  await db.post.rename(post.id, parsed.data.title)               // 4. write
  updateTag(`post:${post.slug}`)                                 // 5. expire what displays it
  return { ok: true }                                            // 6. minimal result
}
```

- A `'use server'` file exports only async functions meant to be called from the browser. Every
  export is an endpoint, including the helper that was never meant to be one.
- Arguments, values bound with `.bind`, and hidden inputs are all attacker-controlled. An ID from
  the client is re-checked against the session on every call (step 3).
- An inline function that closes over variables sends them to the client and back, encrypted.
  Do not close over secrets. Pass an ID and look the rest up.
- Expected failures (validation, conflict, not allowed) are return values in a typed result. A
  thrown error is for bugs: it reaches the error boundary, with its message stripped in
  production.
- `redirect()` and `notFound()` work by throwing. Call them outside `try`/`catch`.
- Next.js runs one server function at a time per client. They are for mutations. Reads belong in
  server components or route handlers, where they run in parallel.
- The request body limit defaults to 1 MB. Files go from the browser to object storage through a
  presigned URL (`0x:backend-architecture`, file uploads), and the function receives the key.
- Callers that are not this app's browser code (mobile app, webhook, cron) get a route handler.
  Both call the same data-layer function.
- Rate-limit functions that send email, cost money or write in bulk (`0x:api-design`).
- The wire protocol is attack surface: December 2025 brought an unauthenticated remote code
  execution in React Server Components (CVE-2025-55182). A security release of `react`, the
  `react-server-dom-*` packages or the framework is deployed the day it lands.

## Streaming and loading states

A `<Suspense>` boundary lets the server send everything outside it now and the inside when it is
ready, in the same response. `loading.tsx` is a boundary around the page of its segment; the
segment's own layout stays outside it.

- One boundary per region that loads independently, not per component. Content that should appear
  together shares a boundary. More than two or three reveals above the fold reads as flicker.
- The fallback reserves the final size: a skeleton with the real dimensions, not a spinner in a
  collapsed box. Otherwise every reveal shifts the layout.
- The largest element of the first screen (headline, hero image, primary content) is not behind a
  boundary waiting on slow data. Cache that data or make it part of the shell.
- Existence, permission and redirect decisions happen before the first boundary. After the first
  byte the status code is fixed.
- Pair each boundary with an error boundary. A failure inside a streamed region should replace
  that region, not the page.
- Recommendations, activity feeds and analytics panels always stream; they never hold up the
  primary content.
- During a client-side navigation the current page stays visible while the next one loads. Show
  pending feedback on the control that was pressed (`useLinkStatus`, `useTransition`).
- To stream data into a client component, pass the unawaited promise as a prop and read it with
  `use()` inside a boundary.

```bash
curl -sN -o /dev/null -w 'first byte %{time_starttransfer}s, done %{time_total}s\n' "$URL"
```

If the two numbers are equal on a page with a slow region, something between the server and the
client is buffering (reverse proxy, compression middleware, a serverless adapter).

## Request waterfalls

A waterfall is a request that could not start until an unrelated one finished.

| Shape | Fix |
|---|---|
| Consecutive `await`s in one component for independent data | `Promise.all`, or start every promise first and await afterwards |
| Parent awaits, then renders a child that fetches something independent | Make them siblings in separate boundaries, or preload the child's data in the parent |
| One query per row in a list | One query for the whole list in the parent, or a batching loader |
| Client fetch in an effect, then a child fetches in its own effect | Fetch on the server, or hoist into one query or a route loader |
| The second fetch truly depends on the first | Keep the order; cache the first; often it is one joined query |

```tsx
export default async function Page(props: PageProps<'/items/[id]'>) {
  const { id } = await props.params
  void getItem(id)                           // starts now; getItem is wrapped in React.cache
  if (!(await canView(id))) notFound()       // the check runs while the query is in flight
  const [item, related] = await Promise.all([getItem(id), getRelated(id)]) // same getItem promise
  return <ItemView item={item} related={related} />
}
```

`React.cache` deduplicates within one request and matches arguments by identity, so pass
primitives, not fresh objects. Find waterfalls instead of guessing: set `logging: { fetches: {
fullUrl: true } }` in `next.config.ts` and read the order and duration of server fetches in the
dev log, or read the spans in a trace (`0x:site-reliability`).

## Hydration mismatches

React compares the server HTML with the first client render. A difference produces a console
error with a diff, and React 19 recovers by re-rendering the nearest Suspense boundary on the
client. That is extra work and a visible flash, not a harmless warning.

| Cause | Fix |
|---|---|
| Time, time zone or locale: `new Date()`, `toLocaleString()`, relative times | Format on the server in a fixed zone and locale, or render a stable value and enhance after mount |
| Randomness or counters: `Math.random()`, incrementing IDs | `useId` for IDs; generate values on the server and pass them down |
| Browser-only state in the first render: `localStorage`, `matchMedia`, `window.innerWidth` | `useSyncExternalStore` with a server snapshot, or CSS (media queries) instead of JS |
| `typeof window !== 'undefined'` branches in render | Same as above; never branch markup on environment |
| Theme class from stored preference | A small blocking inline script that sets the class on `<html>`, and `suppressHydrationWarning` on that one element |
| Invalid nesting the parser repairs: `<div>` in `<p>`, `<a>` in `<a>`, a table row without `<tbody>` | Fix the markup; the server sent it right and the browser rewrote it |
| Extensions and injected scripts rewriting the DOM | Confirm in a clean profile; nothing to fix beyond `suppressHydrationWarning` on `<html>` and `<body>` |
| CDN rewriting HTML (minification, email obfuscation, script deferral) | Turn the feature off for HTML routes |

Diagnose in this order: read the diff in the console, since it names the element; reproduce in a
private window with extensions off; compare `curl` output with the DOM to see whether the server
or the client is the odd one; then check for time zone and locale differences between server
(usually UTC, `en-US`) and browser.

`suppressHydrationWarning` applies one level deep and to text and attributes only. It is for
values that legitimately differ, such as a timestamp. `next/dynamic` with `ssr: false` works only
inside a client component and is for widgets that cannot render on the server at all; it removes
the content from the HTML.

## Hydration cost

The browser pays for every client component twice: it downloads the code, then re-runs the
render to attach handlers. The HTML carries the data twice too: once as markup, once as the
serialized payload (`self.__next_f.push(...)` script tags in Next.js) holding the server tree and
every prop passed to a client component.

- Move the directive down. A client page containing a static article hydrates the article; a
  server page with a client `LikeButton` hydrates one button.
- Pass children, not data. A client `Tabs` that receives server-rendered panels as children adds
  no props to the payload; one that receives `items={rows}` serializes every row.
- Trim props to the fields rendered. A 200-row list passed to a client table for the sake of one
  sortable header ships 200 rows twice. Sort on the server through the URL, or make only the
  header a client component.
- Load heavy client widgets (charts, editors, maps) on demand with `next/dynamic` or `React.lazy`,
  triggered by visibility or interaction.
- Sections inside Suspense boundaries hydrate independently, and the one the user touches first
  is hydrated first. One boundary around a heavy region keeps the rest responsive.
- Never fetch on the client what the server already rendered.

Look at what is sent: `curl -s "$URL" | wc -c` for the document size, then search the HTML for a
field that should not be there (an email address, an internal flag). Run the bundle analyzer
(`build-tooling.md`) for the client bundle by route. Budgets for bundle size and interaction
latency: `0x:web-performance`.

## Ask the user

- **Who may perform this action?** Authorization is a business rule that code cannot reveal.
  Default: only the owner of the resource, or members of its tenant with a write role; everyone
  else gets "not found".
- **Must this form work before JavaScript loads?** Form actions make it nearly free. Default: yes
  for sign-in, checkout and contact forms; no for editors and other rich tools.
- **What must be on screen first?** It decides what is in the shell and what streams. Default:
  heading and primary content first; secondary panels stream.
- **May this data be a little stale in exchange for an instant page?** Default: shared content
  yes, with a stated lifetime; a user's own data no.
