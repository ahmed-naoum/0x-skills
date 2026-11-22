# The browser: rendering pipeline, DOM, events and DevTools

Read this when: writing code that touches the DOM, events, browser storage or device APIs
directly; moving work off the main thread; or a bug must be found in a real browser or on a real
phone.

## Finding a bug in DevTools

Work in the browser first and change the source only once the live edit proves the fix.

| Question | Where |
|---|---|
| Which rule sets this value, and what lost? | Elements → Computed, expand the property |
| Why is this box this size? | Box model diagram; `flex`/`grid`/`scroll` badges in the DOM tree draw overlays |
| What does it look like hovered, focused, invalid? | Styles → `:hov` to force element state |
| What changed this node? | Right-click the node → Break on → subtree modifications / attribute modifications |
| Which handler runs on click? | Event Listeners pane (untick "Ancestors" to narrow); `monitorEvents($0, ['pointerdown', 'click'])` in the console |
| The menu closes when DevTools is clicked | Rendering → Emulate a focused page; or run `setTimeout(() => { debugger }, 3000)`, open the menu, wait for the pause |
| What did I change while experimenting? | Changes drawer shows a diff of live edits |
| Does it work with reduced motion, dark mode, no hover? | Rendering → emulate CSS media features |
| What repaints or shifts? | Rendering → Paint flashing, Layout shift regions |
| Is the response what the code expects? | Network → the request → Preview/Response; "Disable cache"; throttling |
| What is stored on this origin? | Application → Storage, Cookies, Service workers, Cache storage |

Console helpers: `$0` is the selected element, `$$('sel')` returns an array of matches,
`getEventListeners($0)` lists listeners, `copy(obj)` puts JSON on the clipboard, `debug(fn)`
breaks when `fn` is called. Use conditional breakpoints and logpoints instead of adding
`console.log` and rebuilding.

Device mode in desktop DevTools changes viewport size, pixel ratio and user-agent string. It is
still the desktop engine: no mobile browser bars, no on-screen keyboard, no safe areas, no real
touch latency, no memory limits, and on iOS a different engine entirely. A bug reported "on
iPhone" is reproduced on an iPhone.

## Debugging a real phone

**Android (Chrome):** enable Developer options and USB debugging on the phone, connect by USB,
accept the prompt, open `chrome://inspect/#devices` on the desktop and click *inspect* under the
tab. Full DevTools, including Performance, runs against the phone. To reach a dev server on the
computer, either use the port-forwarding dialog on that page or run `adb reverse tcp:3000 tcp:3000`
and open `http://localhost:3000` on the phone; `localhost` also keeps secure-context APIs working.

**iPhone (Safari):** on the phone, Settings → Apps → Safari → Advanced → Web Inspector (older iOS
versions: Settings → Safari → Advanced). On the Mac, Safari → Settings → Advanced → show
features for web developers; connect the phone, then
Develop menu → the device → the page. This needs a Mac. Without one: a cloud real-device service,
or as a last resort an in-page console injected for the session. Xcode's iOS Simulator is
inspected the same way and covers most layout and engine bugs, but not real-keyboard, camera,
performance or memory behavior.

Facts that save time:

- Browsers on iOS have historically all been WebKit under their own UI, so "Chrome on iPhone"
  bugs are Safari bugs. Old iPhones run old Safari because it updates with the OS.
- A webview inside an app is only inspectable if the app allows it (debug builds; on iOS the
  web view must be marked inspectable). In-app browsers of social apps are not inspectable at
  all; see `pwa-mobile.md`.
- Reaching the dev server over Wi-Fi: bind it to all interfaces (for example
  `next dev -H 0.0.0.0`) and open the computer's LAN IP. Current Next.js blocks dev-only assets
  requested from another host until that host is listed in `allowedDevOrigins` (symptom: blocked
  `/_next/` requests, a page that never becomes interactive). Service workers, clipboard, camera,
  geolocation and `crypto.randomUUID` need a secure context, and a LAN IP over HTTP is not one;
  use a tunnel that provides HTTPS, or the dev server's HTTPS option.
- Mobile-only classics to check first: `100vh` cut off by browser bars; zoom on focusing an
  input under 16px; fixed elements under the keyboard; hover styles stuck after a tap; autoplay
  video without `muted playsinline`; audio or clipboard calls that are not inside a user
  gesture; storage that vanished (below); state lost because the OS discarded the background
  tab; a page restored from the back/forward cache without re-running scripts (handle the
  `pageshow` event and check `event.persisted`).

## Events

| Need | Use | Reason |
|---|---|---|
| Activate a control | `click` on a `<button>` or `<a>` | Fires for mouse, touch, keyboard and assistive tech. Do not activate on `pointerdown`/`touchstart`: it breaks scrolling past the control and keyboard use |
| Drag, draw, swipe, resize handle | Pointer events (`pointerdown`/`move`/`up`/`cancel`) | One model for mouse, touch and pen |
| Text entry | `input` (every change), `change` (commit), `beforeinput` to veto | `keydown` misses paste, autofill, voice and IME input |
| Keyboard shortcut | `keydown`, compare `event.key` | `event.code` is the physical key (use only for position-based controls such as WASD); `keyCode` is obsolete |
| Leaving the page | `visibilitychange` (state `hidden`) and `pagehide` | The last events that reliably fire on mobile. `unload` and `beforeunload` do not, and `unload` handlers disqualify the page from the back/forward cache |

Rules:

- **Custom gestures need `touch-action`.** Without it the browser claims the touch for scrolling
  and sends `pointercancel` after a few pixels. Set `touch-action: none` on a drag surface,
  `pan-y` on a horizontal carousel, and call `element.setPointerCapture(e.pointerId)` on
  `pointerdown` so moves keep arriving when the pointer leaves the element. Always handle
  `pointercancel`.
- **Passive listeners.** A `touchstart`, `touchmove` or `wheel` listener that might call
  `preventDefault()` forces the browser to wait for JavaScript before scrolling. Register them
  with `{ passive: true }` unless the handler really must block scrolling; then say
  `{ passive: false }` explicitly, because most browsers treat such listeners on `window`, `document`
  and `body` as passive by default and silently ignore `preventDefault()`. Prefer CSS
  (`touch-action`, `overscroll-behavior`) to blocking scroll in JS.
- **Delegation.** One listener on a stable container instead of one per row:

```js
list.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn || !list.contains(btn)) return;
  actions[btn.dataset.action]?.(btn.closest('[data-id]').dataset.id);
});
```

  It survives re-rendered children and costs one listener. `focus`, `blur`, `mouseenter`,
  `mouseleave` and element `scroll` do not bubble: use `focusin`/`focusout`, or pass
  `{ capture: true }`. React already delegates; this matters for vanilla code, widgets and
  third-party containers.
- **Keyboard.** Ignore `keydown` while `event.isComposing` is true: for Japanese, Chinese and
  Korean input, Enter confirms the composition, and a "submit on Enter" handler would send a
  half-typed message. Do not fire single-key shortcuts while focus is in an input, textarea,
  select or `contenteditable`. Do not override browser or screen-reader shortcuts; shortcut
  design is in `0x:accessibility`.
- **User activation.** Clipboard writes, share sheets, fullscreen, file pickers, popups and
  audio playback require a recent user gesture. The allowance is short-lived; calling the API
  after a slow `await` can fail, most readily in Safari. Start the gated call first, or prepare
  the data before the click.
- Remove listeners by lifetime: `{ signal }` from one `AbortController`, `{ once: true }` for
  one-shot handlers. Throttle work driven by `scroll`, `resize` and `pointermove` to one run per
  frame with `requestAnimationFrame`.

## Client storage

| Store | Capacity and shape | Use for | Do not use for |
|---|---|---|---|
| Cookie | About 4 KB each, sent with every request to the site | Session identifier (`HttpOnly; Secure; SameSite=Lax`), values the server needs before rendering (locale, theme) | Anything large; anything JavaScript should read if it is a credential |
| `localStorage` | Strings, a few MB per origin, **synchronous** | Small UI preferences, dismissed banners, a last-used value | Tokens or personal data (any injected script reads it), large or frequently written data (blocks the main thread), anything in a worker (not available) |
| `sessionStorage` | Same, per tab, survives reload | Form drafts and wizard state scoped to one tab | Cross-tab state |
| IndexedDB | Structured-cloneable values, blobs, indexes; large quota; async | Offline data, outbox queues, large caches | Simple key/value needs (use a small wrapper such as `idb` or `idb-keyval`; the raw API is callback-based) |
| Cache API | Request/response pairs | Assets and GET responses for offline use, normally from a service worker | Structured app data |
| OPFS (origin private file system) | Files; fast synchronous handles inside workers | Large binary or database files (SQLite compiled to WebAssembly), in-browser editors | Ordinary app state |

- The server is the source of truth; client storage is a cache or a queue. Browsers may evict an
  origin's storage under pressure, and Safari's tracking prevention deletes script-writable
  storage (`localStorage`, IndexedDB, caches, service worker registrations) after about a week
  of browser use without interaction with the site; installed home-screen web apps are exempt.
  `navigator.storage.persist()` requests protection from eviction; `navigator.storage.estimate()`
  reports usage and quota.
- Wrap `localStorage` access in `try/catch`: it throws when storage is disabled or full, and it
  does not exist during server rendering.
- Version every stored shape (`{ v: 2, ... }`) and parse it with a schema on read; data written
  by an old release will be read by a new one.
- IndexedDB transactions commit as soon as no request is pending. Awaiting anything else inside
  one (`fetch`, a timer) ends it and the next call throws `TransactionInactiveError`: fetch
  first, then open the transaction.
- Storage inside a third-party iframe is partitioned by the top-level site.
- Cross-tab coordination: `BroadcastChannel` for messages (logout everywhere, cache
  invalidation), the `storage` event for `localStorage` changes, the Web Locks API when only one
  tab may do something (token refresh, sync).
- Session and token placement are owned by `0x:auth-identity`.

## What a change costs: layout, paint, composite

Each frame runs style → layout → paint → composite. How far down a change starts determines
its cost.

| Change | Triggers | Cost |
|---|---|---|
| `width`, `height`, `margin`, `padding`, `top`/`left`, `font-size`, `display`, adding or removing nodes, changing text | Layout, then paint and composite, for the affected subtree and often its siblings and ancestors | Highest; scales with DOM size |
| `color`, `background`, `box-shadow`, `border-radius`, `outline`, `visibility` | Paint, composite | Medium; scales with painted area |
| `transform`, `opacity` (and usually `filter`) on a composited layer | Composite only | Cheap, and can run off the main thread |

- **Forced synchronous layout.** Reading geometry (`offsetWidth`, `offsetTop`, `clientHeight`,
  `scrollTop`, `getBoundingClientRect()`, `getComputedStyle()`, `innerText`) after writing a
  style makes the browser run layout immediately. In a loop this is layout thrashing: one layout
  per iteration. Read everything first, then write everything; schedule writes in
  `requestAnimationFrame`.
- Limit the blast radius: `contain: content` on independent widgets;
  `content-visibility: auto` with `contain-intrinsic-size` on long off-screen sections, which
  skips their rendering while keeping them findable; virtualize lists once they reach the
  thousands of rows.
- Toggle a class on a container instead of setting styles on many children; hide with
  `display: none` when the subtree should cost nothing.
- Measuring an element's size is the job of `ResizeObserver`, which reports after layout without
  forcing one.
- The Performance panel marks forced reflow in the call stack. Field metrics and budgets are in
  `0x:web-performance`; animation specifics are in `animation.md`.

## Observers instead of polling

| Question | Use | Notes |
|---|---|---|
| Is this element in (or near) the viewport? | `IntersectionObserver` | Lazy loading, infinite-scroll sentinel, impression tracking, "stuck" state for sticky headers. `rootMargin: '200px'` to act early. Asynchronous and not per-frame: not for scroll-linked animation |
| Did this element's size change? | `ResizeObserver` | Charts, canvases, text fitting. Changing the observed element's size inside the callback causes the "ResizeObserver loop" error; write to a different element or defer one frame. For styling, a container query needs no JS |
| Did the DOM change under code that does not control it? | `MutationObserver` | Third-party widgets, user-generated HTML, browser extensions. Narrow it (`childList`, `subtree`, `attributeFilter`); a broad observer on `body` runs on every change in the app |
| Did a media condition change? | `matchMedia(q).addEventListener('change', ...)` | Instead of a `resize` listener that re-measures |
| Did the tab become hidden? | `visibilitychange` | Pause polling, timers and animation; flush pending saves with `fetch(url, { keepalive: true })` or `navigator.sendBeacon` |

Create observers once, observe many targets with the same instance, and `disconnect()` on
teardown. Before writing any observer, check whether CSS already does it: container queries,
`:has()`, `position: sticky`, scroll-driven animations, `loading="lazy"`.

## Web workers

Use a worker when a single piece of computation holds the main thread long enough to feel (as a
rule of thumb, tasks beyond about 50 ms that cannot be split): parsing or generating large files,
search indexing, image processing, diffing, syntax highlighting, cryptography, WebAssembly
modules.

Do not use one for: waiting on the network (already asynchronous), anything that needs the DOM
(workers have none), or small tasks, where startup and message copying exceed the work. Try in
order: do less, do it on the server, split the work into chunks that yield between them, then a
worker.

```ts
const worker = new Worker(new URL('./parse.worker.ts', import.meta.url), { type: 'module' });
worker.postMessage({ buffer }, [buffer]);          // transfer, do not copy
worker.onmessage = (e) => render(e.data);
worker.onerror = (e) => report(e.message);
```

- The `new URL(..., import.meta.url)` form is what bundlers recognize to build the worker file.
- Messages are structured-cloned: large objects are copied on every post. Transfer
  `ArrayBuffer`, `ImageBitmap`, `OffscreenCanvas` and streams in the second argument; the sender
  loses access. Send ids and small results, not whole datasets back and forth.
- Give every request an id, or wrap the worker with an RPC helper such as Comlink, so responses
  match requests. Support cancellation with a message, or `worker.terminate()` and recreate.
- Create the worker lazily on first use and keep it; one worker is enough for most products.
- `SharedArrayBuffer` requires cross-origin isolation headers, which break many third-party
  embeds. Avoid unless a library demands it.

## Platform APIs: gesture, permission, fallback

Every device API gets the same three-part treatment: feature-detect, call only from a user
gesture, and handle refusal as a normal outcome.

| API | Call | Fallback and traps |
|---|---|---|
| Copy | `await navigator.clipboard.writeText(text)` | Secure context and gesture required. Confirm visibly ("Copied"). On failure, show the text selected in a read-only field |
| Paste / read clipboard | `navigator.clipboard.readText()` | Prompts or shows a paste bubble; prefer handling the `paste` event on a focused field, which needs no permission |
| Share | `if (navigator.share) await navigator.share({ title, url })` | Not on every desktop browser: fall back to copy-link. Rejection with `AbortError` means the user closed the sheet; do not report it. Check `navigator.canShare({ files })` before sharing files |
| Pick a file | `<input type="file" accept="image/*" multiple>` | Works everywhere, including camera and photo library on phones. `showOpenFilePicker()` and writing back to disk are not Baseline: detect and fall back to the input, and to a Blob URL on `<a download>` for saving (revoke the URL afterwards) |
| Fullscreen | `await el.requestFullscreen()` | Check `document.fullscreenEnabled`. iPhone support for arbitrary elements has been limited to video; offer a CSS "expanded" layout instead of depending on it. Always provide a visible exit |
| Camera, microphone, location, notifications | The API's own request | Ask at the moment of use, after the user taps something that explains why. A browser-level denial cannot be re-prompted: detect it and show how to re-enable in settings. Never request on page load |

Inside an iframe these APIs need the embedding page's `allow` attribute. Third-party code can be
denied them with a `Permissions-Policy` response header (`0x:web-security`).

## Custom elements, where they fit

| Fits | Does not fit |
|---|---|
| A widget embedded in pages the team does not control (customer sites, CMS content, docs) | Composing the screens of a React app: use components |
| Leaf UI shared across several frameworks or server-rendered templates | Content that must be in server HTML for search or first paint and relies on shadow DOM |
| Enhancing server-rendered HTML on a mostly static site with a few interactive islands | Anything needing rich data passed down many levels |

Rules for the ones worth building:

- Light DOM by default: the element enhances the children it is given, global styles and forms
  keep working, and the content exists before the script loads. Add shadow DOM only when style
  isolation is the requirement (third-party embeds). Shadow styles do not leak in or out, but
  inherited properties and custom properties cross the boundary, which is how to theme it;
  expose internals with `::part`.
- Set up in `connectedCallback` (it can run more than once: when moved, it disconnects and
  reconnects) and tear down in `disconnectedCallback`. Do not touch attributes or children in
  the constructor.
- Strings in via attributes (`static observedAttributes` + `attributeChangedCallback`), rich data
  via properties, output via events:
  `this.dispatchEvent(new CustomEvent('change', { detail, bubbles: true, composed: true }))`;
  `composed` lets it cross a shadow boundary.
- Guard registration: `if (!customElements.get('x-rating')) customElements.define('x-rating', XRating)`;
  defining a name twice throws, which happens when two bundles include the element.
- Avoid a flash of unstyled content: reserve space with `x-rating:not(:defined) { ... }`.
- A custom form control must participate in forms: `static formAssociated = true` and
  `attachInternals()` to set its value and validity. ARIA id references do not cross shadow
  roots, which limits labeling; see `0x:accessibility`.
- More than a handful of elements justifies a small base library (Lit) rather than hand-written
  lifecycle code.

## Ask the user

- **Which real devices matter most, and is one available to test on?** Mobile bugs cannot be
  confirmed fixed otherwise. Default: one recent iPhone and one mid-range Android; if none is
  at hand, say so plainly and mark the fix unverified.
- **May data be kept on the user's device, and should it survive logout?** Shared computers
  and privacy rules make this a risk choice. Default: preferences only; clear everything
  user-specific on logout.
- **Is it acceptable to ask for this permission, and what happens for users who refuse?**
  Default: the feature works without the permission in a reduced form; ask only after an
  explicit tap.
- **Must this widget run on sites outside the product?** That decides custom element with shadow
  DOM versus a normal component. Default: normal component.
