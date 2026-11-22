# Rendering and runtime performance

Read this when: the page is slow after it has loaded: scrolling or typing is janky, clicks feel
late, animations stutter, or a long page gets slower as it grows.

## Reproduce on the device the user has

A development laptop is several times faster per core than a mid-range phone and has no thermal
limit worth mentioning. Jank that users report is routinely invisible locally. Set up the
measurement so the problem appears:

1. **Production build.** React and most frameworks run several times slower in development
   mode (extra checks, double-invoked effects, no minification). Never profile `next dev`.
2. **Clean profile.** Incognito or a profile with no extensions; extensions inject scripts and
   show up as mystery long tasks.
3. **CPU throttling** in the DevTools Performance panel: 4x slowdown approximates a mid-range
   phone on a fast laptop, 6x or more a low-end one. Recent Chrome versions can calibrate presets
   for the machine. Add network throttling only when loading is part of the problem.
4. **A real phone when it matters.** Throttling slows the CPU but does not reproduce small
   memory, slow storage, GPU limits or thermal throttling. Connect an Android phone by USB, open
   `chrome://inspect` on the desktop and profile the phone's tab from desktop DevTools. For iOS,
   use Safari's Web Inspector from a Mac.
5. **Realistic data.** A list with 12 seeded rows hides what 3,000 rows do. Load the account
   with the most data.

Record one interaction at a time: start recording, perform the slow action once, stop. Short
traces are readable; a 30-second recording is not.

## Reading the Performance panel

| Track or view | What to look for |
|---|---|
| Interactions | Each input with its duration, split into input delay, processing and presentation; long ones are flagged |
| Main thread flame chart | Tasks over 50 ms are marked; width is time, depth is call stack. Find the wide blocks under the slow interaction |
| Frames | Dropped or partially presented frames during scroll and animation |
| Layout shifts | Each shift, with the nodes that moved |
| Bottom-up tab (select a time range) | Self time grouped by function or by URL: answers "which code", including third parties |
| Summary tab | Scripting versus rendering versus painting for the selection: answers "which kind of work" |

The Summary split decides the next step. Mostly scripting: it is a JavaScript problem (handler
cost, framework re-rendering). Mostly rendering: style and layout. Mostly painting: paint area
and effects. Guessing between these wastes the most time; read the split first.

### The pipeline and what each stage costs

Each frame runs JavaScript → style → layout → paint → composite. At 60 Hz a frame has 16.7 ms,
of which the page gets roughly 10 ms after browser overhead.

| Stage | Purple or green block in the trace | Gets expensive when | Fix |
|---|---|---|---|
| Style ("Recalculate Style") | Purple | Many elements affected by one class change; huge DOM; broad selectors re-matched; CSS variable changed at the root | Change classes as low in the tree as possible; reduce DOM; scope custom-property updates to the subtree |
| Layout | Purple | Geometry changes high in the tree; deep flex or grid nesting; tables with auto layout; reading geometry after writing | Limit layout scope with `contain: layout` or `content-visibility`; batch reads and writes |
| Paint | Green | Large areas repainted; `box-shadow`, `filter: blur`, `backdrop-filter` over big regions; fixed backgrounds | Smaller painted area; cheaper effects on phones; promote the moving element to its own layer |
| Composite | Green | Too many layers, very large layers | Remove stray `will-change`; avoid promoting hundreds of elements |

Animation rule: animate only `transform` and `opacity`. They run on the compositor and stay
smooth even when the main thread is busy. Animating `height`, `width`, `top`, `left` or
`margin` runs layout every frame; replace with a transform, or with `grid-template-rows`
transitions for expand and collapse where a real size change is needed. Use `will-change` only
on elements about to animate and remove it after; set permanently on many elements it costs
memory and makes things slower.

To see paint and layer problems directly, use the Rendering drawer: paint flashing, layout
shift regions, and the frame rendering stats overlay.

## Layout thrashing and forced reflow

The browser defers layout until the frame. Reading geometry forces it to compute layout
immediately if anything is dirty. Doing write, read, write, read in a loop computes layout on
every iteration: a handful of milliseconds each, hundreds in total.

Properties that force layout when read after a write: `offsetWidth`/`offsetHeight`/`offsetTop`,
`clientWidth`/`clientHeight`, `scrollTop`/`scrollHeight`, `getBoundingClientRect()`,
`getComputedStyle()` for layout-dependent values, `innerText`, and calling `focus()` or
`scrollIntoView()`.

```ts
// Thrashes: each iteration invalidates layout, then forces it
for (const el of items) el.style.height = el.scrollHeight + 'px';

// Batched: all reads, then all writes
const heights = items.map((el) => el.scrollHeight);
items.forEach((el, i) => { el.style.height = heights[i] + 'px'; });
```

Find it: the trace marks layout events triggered from script as forced, with the stack of the
call that caused them, and the panel's insights list forced reflows by function. In field
data, Long Animation Frames entries report `forcedStyleAndLayoutDuration` per script
(`core-web-vitals.md`).

Fix patterns:

- Read first, write second, within one task. Schedule writes in `requestAnimationFrame` when
  they come from several places.
- Replace geometry polling with observers: `ResizeObserver` for size, `IntersectionObserver`
  for visibility. Both deliver measurements without forcing layout.
- Replace measurement with CSS where possible: `position: sticky`, `aspect-ratio`, container
  queries, `min-content`/`fit-content`, anchor positioning where supported.
- In React, measuring in `useLayoutEffect` and then setting state forces layout and a second
  synchronous render. Keep it to the one element that needs it, not every list row. Auto-resizing
  textareas, tooltip positioners and "equal height" scripts are the usual offenders.
- A third-party script reading geometry on every scroll event is common; attribute it by URL in
  the bottom-up view before blaming own code.

## DOM size and long pages

Style, layout and memory costs grow with node count, and so does every framework reconciliation
pass. Rules of thumb: a page under about 1,500 nodes rarely has DOM-size problems; several
thousand nodes make every interaction's presentation delay visible on phones. Count with
`document.querySelectorAll('*').length`.

| Situation | Approach | Trade-off |
|---|---|---|
| Long list or table, hundreds of rows or more | Paginate, or "load more" | Simplest; keeps find-in-page and accessibility intact for what is shown |
| List must scroll continuously with thousands of rows | Virtualize (TanStack Virtual or similar): render only visible rows | Breaks find-in-page and anchor links for unrendered rows; needs stable row heights or measurement; test with a screen reader |
| Long article or feed of heavy sections | `content-visibility: auto` on each section | Content stays in the DOM and searchable; rendering work is skipped while off-screen |
| Hidden UI kept mounted (all tabs, all modals, all accordion panels) | Mount on demand, or `content-visibility: hidden` to keep state without rendering cost | First open pays the mount |
| Deep wrapper nesting from component libraries | Flatten; use fragments; avoid a wrapper `div` per layout concern | Tedious, do it for repeated rows first: one saved node per row times 1,000 rows |
| Large inline SVG, many icons | Sprite with `<use>`, or `<img>` | See `images-fonts.md` |

```css
.feed-section {
  content-visibility: auto;
  contain-intrinsic-size: auto 600px;   /* placeholder height; "auto" remembers the real one once rendered */
}
```

Traps with `content-visibility: auto`: without `contain-intrinsic-size` each section has zero
height until rendered and the scrollbar jumps while scrolling; it applies size containment to
skipped elements, so content that overflows its box by design (dropdowns, tooltips escaping
the section) is clipped; applying it to hundreds of tiny elements costs more than it saves, so
use it on a few dozen large sections.

## Respond to input within 100 ms

About 100 ms is the limit at which a response feels caused by the action. The response does not
need to be the result; it needs to be visible acknowledgment.

| Time since input | What the user must see |
|---|---|
| Under 100 ms | Something changed: pressed state, toggle flipped, item appears, focus moved |
| 100 ms to 1 s | Nothing extra; a spinner here flickers and makes fast operations feel slow |
| Over ~1 s | Progress indication: skeleton or spinner, shown after a short delay (a few hundred ms) |
| Over ~10 s | Progress with an estimate, and a way to leave and come back; make it a background job |

**Optimistic updates**: apply the result locally before the server confirms, roll back on
failure.

| Safe to be optimistic | Not safe |
|---|---|
| Toggles, likes, stars, read state | Payments, purchases, anything that moves money |
| Renaming, reordering, editing text the user owns | Destructive actions without undo |
| Adding an item to a list, sending a chat message (with a "sending" mark) | Actions whose validity only the server knows: stock, seat availability, permissions, unique names |
| Dismissing notifications | Anything another user or system acts on immediately |

Requirements when optimistic: a rollback path that restores the previous state and tells the
user what failed; temporary client ids reconciled with server ids; disabled or deduplicated
resubmission while pending; ordering preserved when two updates race (ignore responses older
than the latest request). In React, `useOptimistic` and `useTransition` cover the common case;
client query libraries have their own mutation hooks with rollback.

When not optimistic, still acknowledge instantly: set the pending state on the control in the
same frame as the click, then do the work.

## Typing and scrolling

**Typing.** The keystroke must appear in the input in the next frame. Everything derived from
it (filtering, validation, search requests, previews) can lag.

- Keep the input's state local to the input component. Lifting it into a global store or a
  context that re-renders the page on every key is the most common cause of typing lag.
- Derived work goes through `useDeferredValue` or `startTransition` (React keeps the input
  urgent and interrupts the slow render), or through a debounce for non-React work.
- Debounce network requests for search-as-you-type by 150 to 300 ms, and cancel the previous
  request with `AbortController` so stale responses cannot overwrite newer ones.
- Validate on blur or after a pause, not synchronously on each key, unless the check is trivial.
- A filtered list of thousands of items needs virtualization or a result cap as well; deferring
  alone only moves the long task.

**Scrolling.** Scrolling runs on the compositor and stays smooth unless the page ties
main-thread work to it.

- Do not do work in `scroll` handlers. Use `IntersectionObserver` for "is it visible",
  `position: sticky` for sticking, CSS scroll-driven animations where supported for
  scroll-linked effects. If a handler is unavoidable, do only a cheap read in it and apply
  changes in `requestAnimationFrame`, at most once per frame.
- `touchstart`, `touchmove` and `wheel` listeners that might call `preventDefault()` make the
  browser wait for them before scrolling. Register them with `{ passive: true }` unless
  cancelling the scroll is the point.
- Infinite scroll must remove or virtualize old items, or the DOM grows without limit and the
  page gets slower the longer the session.
- Images in scrolling lists need dimensions and `decoding="async"`; large images decoding on the
  main thread cause scroll hitches.

**Debounce, throttle, defer, batch: which one.**

| Tool | Meaning | Use for |
|---|---|---|
| Debounce | Run once after activity stops | Search requests, autosave, resize recalculation, validation |
| Throttle or `requestAnimationFrame` | Run at most once per interval or frame | Drag, pointer move, scroll-linked updates |
| Defer or transition | Run now at low priority, interruptible | Expensive rendering derived from input |
| Batch | Combine many updates into one render or one request | Many state updates in one handler (automatic in current React), many small API writes |
| Yield | Split one long task so input can be handled in between | Loops over large data (`core-web-vitals.md`) |

**React-specific causes** of slow interactions, in the order worth checking with the React
DevTools Profiler (record the interaction, read what rendered and why): a context value that
changes on every render and re-renders all consumers; state held too high so a small change
re-renders the page; unstable `key`s that remount rows; expensive computation in render without
memoization; one huge client component where a few small ones would isolate updates. Memoize
(`memo`, `useMemo`, or the React Compiler if the project has it enabled) after finding the
component in the profiler, not before.

## Ask the user

- **Which devices do the affected users have?** Decides the throttling level and whether a real
  device test is needed. Default: mid-range Android, 4x CPU throttle.
- **Is find-in-page or deep linking into long lists required?** Decides between virtualization
  and pagination or `content-visibility`. Default: paginate; virtualize only when continuous
  scroll is a product requirement.
- **Which actions may show success before the server confirms?** A wrong optimistic "saved" is a
  trust problem. Default: optimistic for reversible edits to the user's own data, confirmed-first
  for money, deletion and scarce resources.
- **Are heavy visual effects (blur, large shadows, parallax) a brand requirement?** They are the
  usual paint cost on phones. Default: keep on desktop, simplify under a small-viewport or
  `prefers-reduced-motion` media query.
