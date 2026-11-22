---
name: frontend-foundations
description: "Builds and debugs on the web platform itself: semantic HTML, CSS layout and responsive design, JavaScript and TypeScript, DOM events and browser storage, forms, animation, translation and right-to-left support, offline PWAs and app-store packaging. Use when a layout breaks on mobile, z-index or specificity misbehaves, async code races, TypeScript rejects types, or the question is native app versus PWA."
---

# Frontend foundations: HTML, CSS, TypeScript and the browser

## Stance

Frameworks change every few years; the platform underneath only gains features. Most frontend
bugs that cost a day are platform bugs seen through a framework: a flex item that will not
shrink, a stacking context, a continuation that resumed after the state changed, a phone
keyboard covering the button. Work from the platform's model first, reach for a library when
the model says the platform cannot do it, and prove fixes in a real browser.

1. **Native element before custom widget.** `<button>`, `<a href>`, `<form>`, `<dialog>`,
   `popover`, `<details>`, `<input type>` carry focus, keyboard, autofill and accessibility that
   a `div` must have rebuilt by hand, usually incompletely.
2. **HTML that works before JavaScript arrives.** Links navigate, forms submit, content is in
   the response. On a slow phone the gap before hydration is seconds, and it is where sign-up
   and checkout lose people.
3. **Let content size the layout.** Fixed widths and heights on anything holding text are
   future overflow bugs: translation, long names and small screens all break them. Use
   intrinsic sizing, `min-width: 0`, wrapping and container queries.
4. **Diagnose in DevTools before editing code.** The Computed pane names the winning rule and
   the box model names the wrong box; guessing with `!important`, `z-index: 9999` or
   `overflow: hidden` hides the cause and creates the next bug.
5. **Types describe assumptions; parsing verifies them.** Everything crossing into the program
   is `unknown` until a schema has parsed it. `as`, `!` and `any` move the failure to runtime
   with a misleading stack trace.
6. **After every `await`, the world may have changed.** Async code needs cancellation, a
   timeout and a re-check of what it captured, or it races.
7. **Feature-detect against Baseline, never sniff browsers.** Support data is the
   fastest-changing fact in this area: look it up at the time of use and ship new features as
   enhancements with a working fallback.
8. **Animate only what the compositor can move, and respect reduced motion.** Transform and
   opacity stay smooth under load; geometry does not.
9. **A real phone is the test.** Emulation has no browser bars, keyboard, safe areas, in-app
   browsers or mobile memory limits. Say plainly when a mobile fix is unverified on a device.

## Route

| If the task is… | Read |
|---|---|
| Choosing elements, structuring a page, building a modal, menu or tooltip, setting title, icons or social cards, embedding video or iframes, or deciding whether a new platform feature is safe to use | `references/html-semantics.md` |
| A layout that overflows, will not center, breaks on mobile or behind the keyboard; z-index, sticky or specificity problems; responsive grids, fluid type, dark mode, Tailwind tokens, cleaning up CSS | `references/css-layout.md` |
| Async code in the wrong order or racing, TypeScript errors or type design, tsconfig, import/export and CommonJS trouble, timeouts and cancellation, a memory leak | `references/javascript-typescript.md` |
| Something only happens in the browser or on a real iPhone or Android; event handling, touch and drag; choosing localStorage, cookies or IndexedDB; observers, web workers, clipboard, share or file APIs; a framework-free widget | `references/browser-dom.md` |
| Any form: fields and mobile keyboards, autofill, validation and error display, double submits, drafts and unsaved-changes protection, multi-step flows, date pickers, comboboxes, file drop | `references/forms.md` |
| Adding a transition, enter or exit animation, page transition or scroll effect; choosing an animation library; fixing jank | `references/animation.md` |
| Translating the app, formatting dates, numbers or money, time zones, locale URLs, right-to-left languages, names, addresses and phone numbers | `references/internationalization.md` |
| "Do we need an app?", offline support, installable PWA, service worker updates, Capacitor or Expo, links that open the app, breakage inside Instagram or other in-app browsers, store review, in-app purchases, app rollouts | `references/pwa-mobile.md` |

## Defaults at a glance

Follow what the project already uses; these apply to greenfield choices.

| Area | Default | Changes when |
|---|---|---|
| Browser target | Baseline Widely available without fallback; Newly available as enhancement | Analytics show an older or narrower audience |
| Markup | Server-rendered semantic HTML, one `<main>`, one `<h1>`, native controls | Never for public pages; app-only screens may require JS |
| Overlays | `<dialog>` with `showModal()` for modals, `popover` for the rest, or the project's headless primitives | Anchor positioning unsupported for the audience: positioning library |
| Layout | Mobile-first, grid for structure, flex for rows, `gap` for spacing, container queries for reusable components | — |
| Full-height shells | `min-height: 100dvh`; safe-area padding with `env()` | Hero sections: `svh` |
| Styling | Tailwind with tokens as CSS variables; CSS modules as the alternative | Project already has another system |
| Theming | `color-scheme` plus `light-dark()` tokens in OKLCH; pre-paint inline script for a stored override | No dark mode planned: still use semantic tokens |
| TypeScript | `strict` plus `noUncheckedIndexedAccess`, including scripts and config; `tsc --noEmit` in CI | Legacy code: enable flag by flag |
| Boundaries | Zod schema parse at every entry point; types inferred from schemas | — |
| Network calls | `res.ok` check, `AbortSignal.timeout`, abort on supersede or unmount | — |
| Client storage | Server is truth; cookie for session, `localStorage` for small preferences, IndexedDB for offline data | Offline-first product: local store with sync |
| Forms | Real `<form>`, labels, `autocomplete` on every field, one shared schema, errors beside fields, idempotent creates | — |
| Motion | CSS transitions on transform and opacity, 150–300 ms, reduced-motion alternative per component | Gestures, exits or layout animation: one motion library |
| i18n | `Intl` formatting, logical CSS properties and externalizable strings from day one; locale in the URL path; ICU messages | — |
| Mobile | Prototype: responsive web. Launch: add PWA installability if repeat use is proven. Stores only for a named capability or channel | The app is the product: Expo |

Stage notes: at Prototype skip cascade layers, component tokens, translation tooling, service
workers and animation libraries. At Launch, forms, sign-up and checkout must be verified on real
phones and inside the in-app browsers of the acquisition channels. At Scale, add linting for raw
style values and physical CSS properties, visual regression tests and per-release device checks.

## Before you call it done

- No horizontal scroll at 320 px and 360 px width; verified in the browser, not by reading CSS.
- Primary flows checked on a real phone or a remote-debugged one, with the on-screen keyboard
  open; if not possible, stated as unverified.
- Every interactive thing is a native control or a library primitive; no click handlers on
  `div` or `span`; every button inside a form has an explicit `type`.
- The page has `lang`, a unique `<title>`, the viewport meta without zoom blocking, and images,
  videos and iframes have dimensions.
- No new `!important`, raw `z-index` number, `overflow-x: hidden` on the page, or `100vh`
  full-height layout.
- `tsc --noEmit` passes with no new `any`, `as` cast or `@ts-ignore`; external data goes
  through a schema.
- Every `fetch` checks `res.ok`, has a timeout, and is cancelled when superseded or unmounted;
  no promise is left without a handler.
- Listeners, timers, observers and subscriptions added by the change are removed on teardown.
- Form fields have labels, correct `type`/`inputmode`/`autocomplete`, 16 px or larger text,
  server validation with errors shown beside fields, and a double-submit guard; submitting with
  Enter works.
- Animations use transform or opacity, have a `prefers-reduced-motion` alternative, and no
  content is invisible when the animation or JavaScript does not run.
- Dates, numbers and money are formatted with `Intl` using an explicit locale and time zone; no
  user-facing string is assembled by concatenation.
- New CSS uses logical properties, and layouts were checked with long text (or a pseudo-locale).
- Any platform feature that is not Baseline Widely available is feature-detected with a
  fallback, and its status was checked now rather than remembered.
- A service worker change was tested for update (old tab open, new deploy) and for logout
  clearing user data; a kill-switch procedure exists.
- For app releases: forced-upgrade path, crash reporting with symbols, and account deletion are
  in place before store submission.

## Not this skill

- React components, server components, Next.js routing and data fetching → `0x:react-nextjs`
- Visual design choices, flows and design tokens → `0x:ui-ux-design`
- Screen readers, ARIA and keyboard access → `0x:accessibility`
- Core Web Vitals, bundle size, image and font loading → `0x:web-performance`
- three.js, WebGL scenes and 3D product pages → `0x:3dui`
- Linting, type-check policy and test setup → `0x:code-quality`
