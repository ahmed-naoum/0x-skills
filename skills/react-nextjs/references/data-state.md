# Data fetching and state

Read this when: deciding where a piece of state lives, setting up client data fetching and
caching, wiring a form to a mutation, or debugging UI that is stale, flickers or disagrees with
the server.

## Classify the state before choosing a tool

| Kind | Owner | Lives in |
|---|---|---|
| Server data: anything in the database or behind an API | The server | Server components and the framework cache; on the client, a query cache (TanStack Query, SWR) |
| View state worth restoring or sharing: filters, sort, page, tab, search text, selected item | The URL | Search params and path segments |
| Ephemeral UI state: text being typed, hover, an open menu | One component | `useState`, `useReducer` |
| Client state shared by distant components: theme, sidebar, a draft cart, a wizard | The app | Context when it changes rarely, a store when it changes often |
| Form state | The form | Uncontrolled inputs and `FormData`; a form library when it is large and dynamic |
| Derived values | Nobody | Computed during render |

Most state bugs are a misfiling: server data copied into `useState` or a store (row 1 treated as
row 3 or 4), or a derived value stored as state and synced by an effect (row 6 treated as row 3).

## Server data belongs in a cache that knows it can go stale

In an app built on server components the default needs no client library: server components
read, server functions write, and tag invalidation refreshes what is on screen. Add a client
query cache when one of these appears: infinite scroll or client-side pagination, polling or
realtime, type-ahead search, optimistic edits on lists, offline use, or an SPA with no server
components.

Never copy fetched data into `useState`, context, Zustand or Redux. A copy has no invalidation and
is wrong as soon as anything else writes. The one exception is a form draft seeded from server
data through `defaultValue`.

TanStack Query settings to decide on the first day:

- `staleTime` defaults to 0: every mount and every window focus refetches, and data hydrated from
  the server is refetched at once. Set a client-wide default (30 to 60 seconds is a reasonable
  start) and override per query.
- On the server, create the `QueryClient` per request, never at module scope. A module-level
  client is shared by every request the process serves, which leaks one user's data to another.
- Build keys with `queryOptions()` factories and keep them hierarchical (`['todos', listId,
  filters]`), so invalidating `['todos']` covers every variant.
- `retry` defaults to 3 attempts with backoff, for 4xx responses as well. Retry only network
  failures and 5xx.
- `gcTime` defaults to 5 minutes; that is what makes Back instant. Do not lower it without cause.
- Prefetch on the server and hydrate (`HydrationBoundary`); do not fetch on mount what the server
  could have sent.

## Fetch where the data is used

Each component calls the data function it needs. Fetching everything in a layout or a page-level
loader and drilling it down couples every child to the parent and breaks when the tree moves.
Deduplication is what makes co-location cheap:

- Server: wrap data functions in `React.cache`. `getCurrentUser()` called from the layout, the
  page and three components is one query per request. Identical `fetch` GETs are deduplicated per
  render without help. `'use cache'` extends reuse across requests.
- Client: the same query key means one request and one shared result.
- No deduplication happens when arguments are fresh objects (identity differs), when key shapes
  differ between call sites, across separate requests, or in route handlers (each call runs).
- Fetching the same data on the server and again in a client effect is the most common
  duplicate. The server result goes down as props or hydrated cache.

Co-location causes a waterfall only when a parent awaits before rendering a child that fetches;
the fixes are in `server-components.md`.

## View state goes in the URL

Put there anything the user expects to survive reload, Back, or a pasted link.

- The server reads `searchParams` and renders from it. The client writes with `<Link>`, the
  router, or a typed helper such as nuqs.
- Push or replace: would the user expect Back to undo it? Pagination, a tab, an opened item:
  push. Each keystroke in a search box or each step of a slider: replace, debounced around 300 ms.
- The URL is user input. Parse with defaults and never throw: an unknown sort becomes the
  default, `page=-3` becomes 1.
- Leave defaults out of the URL so there is one URL per view. Changing a filter resets `page`.
- State the server queries by takes a server round trip, inside a transition so the control can
  show pending. State only the client uses (which panel is open) updates shallowly.
- `useSearchParams()` needs a `<Suspense>` boundary above it. Without one a prerendered route
  fails the build, because everything up to the nearest boundary would render only on the client.
- Keep out of the URL: secrets, personal data, large blobs, hover and focus.

```ts
'use client'
import { parseAsInteger, parseAsStringLiteral, useQueryStates } from 'nuqs'

const sortOptions = ['newest', 'price'] as const

export function useListParams() {
  return useQueryStates(
    { page: parseAsInteger.withDefault(1), sort: parseAsStringLiteral(sortOptions).withDefault('newest') },
    { history: 'push', shallow: false }, // Back undoes it; the server re-renders with the new params
  )
}
```

## Client state: local, context or store

Climb only as far as needed: local state, then lift to the nearest common parent, then
composition (pass `children` so the middle layers do not carry props), then context, then a store.

| Use | When |
|---|---|
| `useState` | One component or a small subtree |
| `useReducer` | Several fields change together in response to named events |
| Context | Read by many, changes rarely: theme, locale, current user, flags. It is dependency injection, not a state manager |
| A store (Zustand, Jotai) | Distant components subscribe to different slices; updates are frequent (drag, selection, an editor); code outside React reads or writes it (shortcuts, socket handlers) |

- Every consumer of a context re-renders when its value changes. Split contexts by how often
  they change, and never put a fast-changing value beside slow ones.
- In a server-rendered app a module-level store is shared across requests on the server. Create
  the store inside a provider (`useState(() => createStore())`) so each request gets its own.
- A store persisted to `localStorage` and read during the first render causes a hydration
  mismatch. Render the default, then load the persisted value after mount.

## After a mutation, tell every cache

| The stale thing is | Refresh it with |
|---|---|
| A cached, tagged server function or component, seen by the person who wrote | `updateTag(tag)` in the server action; the response carries the re-rendered route |
| The same, shared with others, where a short lag is fine | `revalidateTag(tag, 'max')` |
| Uncached server-rendered data on the current page | `refresh()` in the action, or `router.refresh()` from the client |
| TanStack Query data | `invalidateQueries({ queryKey })` in `onSettled`, or `setQueryData` with the entity the mutation returned |
| Another tab or another user's screen | Refetch on focus, polling or realtime; invalidation alone cannot reach it |

When the screen is still stale after a successful write, check in this order:

1. Nothing invalidated. The write worked and no cache was told.
2. Tag or key mismatch: a typo, or a list key outside the invalidated prefix.
3. The detail was invalidated and the list was not, or the reverse. Invalidate entity and
   collection together.
4. `revalidateTag(tag, 'max')` in the action that the writer is waiting on. It marks stale but
   does not re-render the current page. Use `updateTag`.
5. The write went through a route handler or a direct `fetch`, not a server action. The client
   router keeps visited pages for minutes; call `router.refresh()`.
6. `redirect()` ran before the invalidation, or the invalidation sits in a `try` whose `catch`
   swallowed the redirect.
7. Self-hosted on several instances, or a CDN caching HTML (`rendering-strategies.md`).

**Optimistic updates** are for actions that nearly always succeed and whose result the client
can compute: toggle, rename, reorder, add to a list. Not for payments or anything the server
calculates. With server actions, `useOptimistic` shows the value during the transition and drops
it when the action settles, so a failure reverts by itself:

```tsx
const [optimisticLiked, setOptimisticLiked] = useOptimistic(liked)
const [, startTransition] = useTransition()
const toggle = () =>
  startTransition(async () => {
    setOptimisticLiked(!optimisticLiked)       // shown until the transition settles
    await setLiked(postId, !optimisticLiked)   // then the server's `liked` prop wins
  })
```

With a query cache the sequence is fixed: in `onMutate`, `cancelQueries` for the key (a refetch
in flight would overwrite the patch), snapshot the previous value, `setQueryData`, return the
snapshot; in `onError`, restore the snapshot; in `onSettled`, invalidate, and only when no other
mutation for that key is still running (`queryClient.isMutating() === 1`), or an early refetch
undoes a later optimistic change. Give new items a client-generated UUID that the server accepts
as the real ID. A temporary ID swapped on success changes the React key and remounts the row.

## Forms and mutations

```tsx
'use client'
export function RenameForm({ id, title }: { id: string; title: string }) {
  const [state, formAction, pending] = useActionState(renamePost, null)
  const failed = state && !state.ok ? state : null
  return (
    <form action={formAction}>
      <input type="hidden" name="id" value={id} />
      <label htmlFor="title">Title</label>
      <input
        id="title"
        name="title"
        defaultValue={failed?.values?.title ?? title} // React resets the form after every action
        aria-invalid={!!failed?.fieldErrors?.title}
        aria-describedby="title-error"
      />
      <p id="title-error">{failed?.fieldErrors?.title?.[0]}</p>
      {failed?.message && <p role="alert">{failed.message}</p>}
      <button type="submit" disabled={pending}>{pending ? 'Saving...' : 'Save'}</button>
    </form>
  )
}
```

- The action returns a typed result: `{ ok: true }`, or `{ ok: false, message, fieldErrors,
  values }`. Return the submitted `values`: React resets uncontrolled fields when an action
  finishes, including one that returned a validation error, and the user's input vanishes unless
  `defaultValue` is fed from the result.
- Pending state comes from `useActionState`, or from `useFormStatus` in a child of the form (it
  does not work in the component that renders the `<form>`).
- Validate twice with one Zod schema: in the browser for speed, on the server for truth. Server
  errors map back to fields by name.
- A form with `action={serverFunction}` submits before hydration. Keep that property: do not
  build the submit path on `onClick`.
- A double click must not create two records. Disable while pending and make the write
  idempotent (`0x:api-design`).
- Reach for a form library (react-hook-form with a schema resolver) when the form has field
  arrays, conditional sections or validation on every keystroke. A five-field form does not need
  one.

Field design, native validation and input types: `0x:frontend-foundations`. Labels, error
announcement and focus on failure: `0x:accessibility`.

## Derive, do not sync

```tsx
const [query, setQuery] = useState('')
const [selectedId, setSelectedId] = useState<string | null>(null)
const visible = items.filter((i) => i.name.includes(query))       // derived: no state, no effect
const selected = items.find((i) => i.id === selectedId) ?? null   // survives refetch and reorder
```

| Urge | Do instead |
|---|---|
| `useEffect` that sets state computed from props or other state | Compute it during render |
| Store the selected object | Store its ID and look the object up during render |
| Reset state when a prop changes | Give the component a `key` built from that prop |
| An effect that reacts to "the form was submitted" | Put the logic in the event handler |
| Fetch in an effect | A query library or a server component; a bare effect has races and no cache |
| Effect A sets state that triggers effect B | One event handler computing both values |

An effect is for synchronizing with something outside React: a subscription, a browser API, a
non-React widget. The `react-hooks/set-state-in-effect` lint rule catches most of the first row.

## Realtime updates into cached data

Transport choice and server fan-out: `0x:backend-architecture`. On the client:

- Subscribe once per resource at a stable level of the tree, not in every component that shows
  the data.
- Default to invalidation: on an event, invalidate the affected keys and let the cache refetch,
  throttled to about once a second per key. Patch the cache directly only when events are frequent
  or carry the full entity.
- When patching, events carry an entity ID and a version or `updatedAt`. Apply an event only if
  its version is newer than the cached one. That one rule drops duplicates, out-of-order
  deliveries and the echo of the user's own optimistic write.

```ts
qc.setQueryData<Message[]>(['messages', roomId], (old = []) => {
  const i = old.findIndex((m) => m.id === incoming.id)
  if (i === -1) return [...old, incoming]                 // new
  if (old[i]!.version >= incoming.version) return old     // duplicate or out of order
  return old.map((m) => (m.id === incoming.id ? incoming : m))
})
```

- Cancel in-flight queries for the key before patching, or an older response lands on top.
- On reconnect, refetch. Events sent while the socket was down are gone.
- In a list the user is reading, do not insert at the top and push content down. Show a "3 new"
  control that inserts on demand, unless the user is at the top of a newest-first list.
- With server components, keep the live region a client component with its own query cache.
  `router.refresh()` on every event re-renders the whole route.

## The React Compiler replaces hand-written memoization

The compiler (1.0, stable since late 2025) memoizes components and hooks at build time. Turn it
on for new projects: in Next.js `reactCompiler: true` plus the `babel-plugin-react-compiler` dev
dependency; in Vite through `@vitejs/plugin-react` as its README describes for the installed
version. Builds get somewhat slower.

- New code: no `useMemo`, `useCallback` or `React.memo` by default. Write the plain version.
- Existing code: leave manual memoization in place. Removing it changes when effects fire where a
  memoized value is a dependency, so remove it only under tests.
- The compiler skips, silently, any component that breaks the Rules of React (mutating props or
  state, reading a ref during render, side effects in render). The app still works; that
  component is just not optimized. The `recommended` preset of `eslint-plugin-react-hooks` is how
  to find them (`purity`, `refs`, `immutability`, `incompatible-library`), so run it in CI.
- Adopting in an old codebase: lint rules first, fix violations, then enable, then run the
  end-to-end suite. `"use no memo"` at the top of a function opts it out while a bug is
  investigated.
- React DevTools marks compiled components with a Memo badge. Check a hot component there
  instead of assuming.
- It does not fix: a computation that is slow the first time, context consumers re-rendering
  when the context value really changed, thousands of DOM nodes in a list (virtualize), or
  unstable keys.

## Ask the user

- **Should this view be shareable by link and survive reload?** It decides URL state versus
  component state. Default: yes for filters, sort, pagination, tabs and the selected item.
- **How fresh must this data be on screen?** It sets `staleTime`, polling, or the need for
  realtime. Default: refetch on focus and after the user's own writes; no polling.
- **Do other people's changes need to appear without a reload?** Realtime adds a connection to
  run and merge rules to maintain. Default: no until users ask.
- **Should this action appear instant, with the risk of visibly undoing it on failure?** Default:
  optimistic for toggles, renames and reorders; wait for the server for money, deletion and
  anything irreversible.
