# Component architecture

Read this when: building or restyling UI components, designing a component's props, deciding
where to split a component, extracting a hook, setting up a component workshop, rendering a long
list, or reviewing a frontend pull request.

## Headless primitives, styles you own

Behavior comes from an accessible headless library (Radix, Base UI, React Aria, Ark). Styles are
the project's own, in files the project owns. The shadcn model copies component source into
`components/ui/` instead of installing a styled dependency: the code is yours to edit, and
updates arrive as diffs you choose to take (`npx shadcn@latest add button --diff`).

- Never hand-build a dialog, menu, combobox, select, tooltip, popover or tabs from `<div>`s.
  Focus trapping, dismissal, typeahead, roving focus and screen-reader semantics are most of the
  work and the part that gets skipped. Details: `0x:accessibility`.
- Reach for the platform first when it is enough: `<button>`, `<a>`, `<details>`, `<dialog>`, the
  `popover` attribute, a native `<select>` on mobile.
- One primitive library per project. Two means two focus-management systems and two portal
  layers fighting over the same screen.
- Wrap each primitive once in `components/ui/` and import only from there. A
  `no-restricted-imports` rule on the primitive package holds the line, so a styling or behavior
  fix happens in one file.
- Edit the copied file to change a component. Do not wrap it in a second component that overrides
  classes from outside.
- Every `ui/` component spreads remaining props onto its root element, accepts `className` and
  merges it last, and passes `ref` through (a plain prop since React 19; no `forwardRef`). A
  wrapper that drops these breaks tooltips, form libraries and tests that depend on them.
- Polymorphism goes through the library's mechanism (`asChild` in Radix, `render` in Base UI),
  so a `Button` can render as a link without an `as` prop that defeats type checking.
- Style states from the attributes the primitive sets (`data-state="open"`, `data-disabled`,
  `aria-invalid`), not from parallel React state.

Three layers keep the system legible: `components/ui/` (primitives, no data, no product words),
`components/` (product components composed from them, such as `InvoiceTable`), and
`app/**/_components/` (used by one route). Code moves down a layer on its second real use.

## Typed variants from tokens

Tokens are CSS variables with semantic names (`--color-primary`, not `--blue-500`), declared once
(`@theme` in Tailwind 4). Variants map a closed set of names onto token-based classes. Choosing
the tokens themselves: `0x:ui-ux-design`.

```tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { ComponentProps } from 'react'

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))

const button = cva(
  'inline-flex items-center justify-center rounded-md font-medium focus-visible:outline-2 disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive: 'bg-destructive text-white hover:bg-destructive/90',
        ghost: 'hover:bg-accent',
      },
      size: { sm: 'h-8 px-3 text-sm', md: 'h-10 px-4', lg: 'h-12 px-6 text-lg' },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

type ButtonProps = ComponentProps<'button'> & VariantProps<typeof button>

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(button({ variant, size }), className)} {...props} />
}
```

- The variant type is derived from the definition, so `<Button variant="pink">` is a compile
  error and adding a variant is one edit.
- Variants are a closed set. A `color` prop that accepts any string, or a class built by
  interpolation (`bg-${color}-500`), is invisible to Tailwind's scanner and produces no CSS. Map
  names to complete class strings.
- `tailwind-merge` resolves conflicts so a caller's `className="px-2"` wins over the variant's
  `px-4` instead of depending on stylesheet order.
- Use `compoundVariants` for combinations such as destructive plus ghost; do not branch in JSX.
- Past roughly five variants and four sizes, or when variants start to exclude each other, it is
  two components.

## Component APIs

**Composition over configuration.** A prop that only carries content to a fixed place should be
`children` or a named slot. Three or more booleans that interact (`hasHeader`, `showFooter`,
`compact`) mean the component is hiding a layout decision. Hand it back to the caller:

```tsx
<Card>
  <CardHeader><CardTitle>Usage</CardTitle></CardHeader>
  <CardContent>...</CardContent>
</Card>
```

The compound form needs no new prop when a card wants two actions or none. The configured form
(`<Card title="Usage" actions={[...]} />`) grows a prop for every variation.

**Controlled and uncontrolled.** A stateful component supports both with one convention: `value`
with `onValueChange` (controlled), `defaultValue` (uncontrolled); likewise `open`, `onOpenChange`,
`defaultOpen`.

```ts
export function useControllableState<T>(opts: { value?: T; defaultValue: T; onChange?: (v: T) => void }) {
  const [internal, setInternal] = useState(opts.defaultValue)
  const controlled = opts.value !== undefined
  const value = controlled ? (opts.value as T) : internal
  const setValue = (next: T) => {
    if (!controlled) setInternal(next)
    opts.onChange?.(next)
  }
  return [value, setValue] as const
}
```

- A component never switches between the two modes during its life, and never copies a prop into
  state "to initialize" it.
- Callbacks report values (`onValueChange(value)`), not DOM events, for anything more complex
  than an input.
- Extend the native element's props (`ComponentProps<'button'>`) and use platform names
  (`disabled`, `open`, `onOpenChange`), so nothing has to be learned twice.
- Mutually exclusive props are a discriminated union, not optionals: `{ href: string } | {
  onClick: () => void }`.
- `className` is the styling escape hatch. A `style`, `sx` or `containerClassName` prop means the
  component's layers leak.
- Use a render prop only when the child must receive the component's internal state.

## Split at boundaries, not by size

Reasons that justify a new component:

| Boundary | Split so that |
|---|---|
| Server and client | The interactive leaf is the only client code |
| Data | A region with its own data becomes an async server component inside its own Suspense boundary |
| Update rate | State lives in the smallest subtree that changes; an expensive sibling stops re-rendering |
| Failure | A region that can fail gets its own error boundary |
| Reuse | A second real caller exists. Not "might" |

Line count is not on the list. A 250-line component that reads top to bottom beats five 50-line
ones threaded together by nine drilled props. Signs a split went wrong: props passed through
components that do not use them; an effect that reports child state up to the parent; a boolean
that tells the child which caller it has.

Two moves fix most trees. Move state down: the `useState` for an input lives in the input's
component, not the page. Lift content up: pass heavy subtrees as `children` to the stateful
wrapper, so its re-render does not re-render them.

## Custom hooks

- One concern per hook, named for what it gives (`useDebouncedValue`, `useMediaQuery`), not for
  where it is used (`useDashboardStuff`).
- A hook exists because it calls other hooks. Otherwise it is a plain function and should be one:
  easier to test, callable anywhere.
- Take primitives or a small options object, not the parent's props. Return a tuple for
  value-and-setter pairs and an object for three or more things.
- Subscriptions to browser state use `useSyncExternalStore` with a server snapshot. That is the
  SSR-safe form, with no effect-then-setState flash:

```ts
export function useMediaQuery(query: string, serverDefault = false) {
  return useSyncExternalStore(
    (onChange) => {
      const mql = window.matchMedia(query)
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    },
    () => window.matchMedia(query).matches, // client
    () => serverDefault,                    // server render and hydration
  )
}
```

- Every subscription, timer and listener has a cleanup. Strict Mode double-invokes effects in
  development to expose the missing ones.
- Do not write a data-fetching hook around `useEffect`. Wrap the query library
  (`useProjects(filters)` calling `useQuery` with a key factory).
- Test with `renderHook` from Testing Library under Vitest, and fake timers for time-based hooks.
  Test through a small component when the behavior is about the DOM. Testing practice:
  `0x:code-quality`.

## A component workshop

Storybook is the default (framework package `@storybook/nextjs-vite` for Next.js,
`@storybook/react-vite` otherwise). Skip it at Prototype, where the app is the workshop. Add it at
Launch once there are about twenty shared components or a second person touching the UI. A
cheaper first step is a `/dev/components` route that renders every `ui/` component and is
excluded from production.

- One story per state, not per prop: default, loading, empty, error, disabled, very long text,
  narrow container, right-to-left. Those are the states that break in production and never show
  up in the happy path.
- Stories are test fixtures. Run them as tests in CI (the Vitest addon), with the accessibility
  addon's automated checks, and interaction tests through `play` functions for components with
  behavior. Visual regression: `0x:code-quality`.
- Mock at the network layer (MSW), not by replacing modules, so the component under test is the
  real one.
- Keep `components/ui/` free of data fetching and router calls. Those components render in
  isolation unmodified; ones that fetch need mocks in every story.
- Each component's docs page states when to use it and when not to, with one correct example. A
  prop table alone answers no real question.

## Long lists

Rule-of-thumb thresholds:

| Rows on screen at once | Do |
|---|---|
| Up to about 100 simple rows | Render them all |
| Hundreds | Paginate on the server, or add `content-visibility: auto` with `contain-intrinsic-size` to rows |
| Thousands, or hundreds of heavy rows | Virtualize, and still page the data from the server. Never ship 10,000 rows to render 20 |

Keys are a stable ID from the data. The array index is wrong for any list that reorders, filters,
inserts or deletes: state and input values stay with the position, not the item. A random key
remounts every row on every render.

```tsx
const v = useVirtualizer({
  count: rows.length,
  getScrollElement: () => parentRef.current, // an element with a fixed height and overflow: auto
  estimateSize: () => 40,
  overscan: 8,
  getItemKey: (i) => rows[i]!.id,
})
// render v.getVirtualItems() absolutely positioned inside a spacer of height v.getTotalSize()
```

Virtualization has costs to plan for. Find-in-page cannot see unrendered rows. Screen readers
need `aria-rowcount` and `aria-rowindex` (or `aria-setsize` and `aria-posinset`). Rows of varying
height need `measureElement`. The scroll offset must be saved and restored for Back. The server
render contains at most the first window. If a filter and server pagination meet the need, prefer
them.

## Reviewing a frontend pull request

Read in this order; earlier items are costlier to fix after merge.

1. **Boundaries.** For each new `'use client'`: why, and could it be a smaller leaf? Are props
   crossing it minimal, serializable and free of private fields? Are new server modules marked
   `server-only`?
2. **Data.** Fetched on the server where possible? Any sequential awaits that could be parallel?
   The same data fetched twice? Does each new mutation validate, authorize and invalidate the
   right tags or keys?
3. **State.** Anything in `useState` that is derived, a copy of server data, or belongs in the
   URL? Any effect that only sets state?
4. **States.** Loading, empty, error and long-content cases present for each new data region?
5. **Render cost.** State held higher than the subtree that uses it; a context value carrying
   fast-changing data; a list without stable keys or with unbounded length; a heavy dependency
   imported into a client component (date, chart, editor and icon packages).
6. **API and accessibility.** Primitives from `ui/`, not hand-built; props follow the project's
   conventions; every interactive element reachable and labeled.

Measure instead of arguing: the React DevTools Profiler shows what re-rendered and why; the
bundle analyzer (`build-tooling.md`) shows what a client import added; the browser console
shows hydration warnings; the build's route table shows a route that turned dynamic. Line-level
bug hunting on the diff is the `code-review` skill; review etiquette and pull request size are
`0x:git-collaboration`.

## Ask the user

- **Is there a design system or brand to match, or is a clean default fine?** It decides how
  much of `ui/` is customized. Default: shadcn-style defaults with the project's tokens.
- **Who else will work on this UI in the next six months?** It decides whether a workshop and
  written component docs pay off now. Default: solo, so skip Storybook until the list above
  triggers.
- **How many items can this list realistically hold for the largest customer?** It decides
  between plain rendering, pagination and virtualization. Default: paginate on the server at 50
  per page.
- **Which browsers and devices matter for this component?** Touch, small screens and older
  browsers change the primitive choices. Default: current evergreen browsers, mobile first.
