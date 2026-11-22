# CSS layout and responsive design

Read this when: laying out a page or component, making it work from phone to desktop, organizing
styles and tokens, theming, or debugging overflow, centering, sticky, specificity or z-index.

## Layout defaults

- Write the narrow layout first as the unqualified styles (usually one column, in source order),
  then add `min-width` queries where the *content* stops looking right, not at device names.
  Projects on Tailwind use its breakpoint scale; do not add custom ones per component.
- Grid for anything two-dimensional or where the parent should dictate tracks (page shells, card
  grids, forms). Flexbox for a single row or column whose items size themselves (toolbars, tag
  lists, a button's icon and label). Space with `gap`, not margins on children.
- Let content drive sizes. Fixed `width`/`height` on anything containing text is a future overflow
  bug; use `max-width`, `min-height`, `aspect-ratio` and intrinsic keywords.
- A component that appears in different-width slots (sidebar and main, modal and page) responds
  to its container, not the viewport.

```css
/* Card grid with no media query: as many 16rem columns as fit, one column on phones */
.cards { display: grid; gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr)); }

/* Readable column with gutters, centered */
.wrap { width: min(100% - 2rem, 70rem); margin-inline: auto; }

/* Container query: the wrapper is the container, the child adapts */
.card-slot { container-type: inline-size; }
@container (min-width: 28rem) { .card { grid-template-columns: 10rem 1fr; } }
```

Container query traps: an element cannot query itself, so the container is a wrapper;
`container-type: inline-size` means the container's width can no longer come from its contents,
so a container inside a shrink-to-fit context (a flex item without `flex: 1`, an absolutely
positioned box) collapses to zero width. In Tailwind v4, `@container` on the wrapper and `@md:`
style variants on children are built in.

| Centering | Code |
|---|---|
| One child, both axes | Parent `display: grid; place-items: center` (give the parent a height) |
| Block horizontally | `margin-inline: auto` plus a `max-width` or `width: fit-content` |
| Overlay in its positioned parent | `position: absolute; inset: 0; margin: auto` plus an explicit size |
| Icon with text | `display: inline-flex; align-items: center; gap: .5em` |

## Debugging method

Do not edit CSS until DevTools has answered two questions: which declaration actually applies,
and which box is the wrong size.

1. Select the element. In the Computed pane, expand the property: it lists every competing
   declaration and the winner. A struck-through rule lost the cascade; a greyed-out declaration
   has no effect in this context (for example `width` on an inline element, `z-index` on a static
   one), and hovering it says why.
2. Read the box model diagram, then walk *up* the tree: layout bugs are usually caused by an
   ancestor (a flex parent, a missing height, an overflow container), not the element itself.
3. Toggle the `flex`/`grid` badges to draw tracks and gaps.

The cascade resolves in this order; stop at the first that differs: origin and `!important` →
inline `style` → cascade layer → specificity → source order. Specificity is counted as (ids,
classes/attributes/pseudo-classes, elements). `:where()` adds zero; `:is()`, `:not()` and `:has()`
take their most specific argument. Styles not in any layer beat every layered style, whatever
their specificity.

| Symptom | Cause | Fix |
|---|---|---|
| Flex or grid child overflows instead of shrinking; long text will not truncate | Items default to `min-width: auto`: they refuse to go below content width | `min-width: 0` on the item; grid tracks `minmax(0, 1fr)` instead of `1fr` |
| `height: 100%` does nothing | Percent height needs a definite height on the parent chain | `min-height: 100dvh` at the root and grid/flex stretch below it, not percent chains |
| Gap under an image | Inline element sitting on the text baseline | `display: block` on images |
| Margin "escapes" the parent or two margins merge | Vertical margin collapse in block flow | Use `gap` in flex/grid, or padding on the parent |
| Style ignored | Lower specificity, a later rule, or an unlayered rule beating a layered one | Read the Computed pane; lower the competing selector rather than adding `!important` |
| `position: sticky` does not stick | No `top`; an ancestor has `overflow: hidden/auto/scroll`; or the parent is no taller than the element | Add the inset; change the ancestor to `overflow: clip`; stick within a taller parent |
| `position: fixed` element moves with content or is clipped | An ancestor has `transform`, `filter`, `perspective`, `backdrop-filter` or `contain: paint`, making it the containing block | Move the element out of that subtree, or use the top layer (`popover`, `<dialog>`) |
| Flex children squashed | `flex-shrink: 1` default | `flex: none` on what must keep its size |
| Text overflows its box | Unbreakable string (URL, token, German compound) | `overflow-wrap: anywhere` on user content |

## Horizontal overflow

A sideways scroll on a phone has exactly one offender. Find it instead of hiding it:

```js
// Paste in the console at the broken width
for (const el of document.querySelectorAll('*')) {
  const r = el.getBoundingClientRect();
  if (r.right > document.documentElement.clientWidth + 1 || r.left < -1) console.log(el);
}
```

Usual offenders: `width: 100vw` (includes the scrollbar; use `100%`), fixed pixel widths, flex
items missing `min-width: 0`, `<pre>` and tables (give them their own `overflow-x: auto` wrapper),
images without `max-width: 100%`, negative margins, off-screen drawers positioned with `left`
instead of `translate`, long unbroken strings.

Do not paper over it with `overflow-x: hidden` on `body` or a wrapper: it hides content, turns
the wrapper into a scroll container (breaking sticky descendants) and leaves the page draggable
sideways on iOS. If decorative elements must bleed off-screen, use `overflow-x: clip` on their
own wrapper.

## Stacking contexts and z-index

`z-index` only orders elements *within the same stacking context*. A child with `z-index: 9999`
can never rise above a sibling of an ancestor that forms a lower context. When a z-index "does
nothing", find the ancestor that created a context.

A stacking context is created by: a positioned element with a `z-index` other than `auto`;
`position: fixed` or `sticky`; a flex or grid item with a `z-index`; `opacity` below 1;
`transform`, `filter`, `backdrop-filter`, `perspective`, `clip-path`, `mask`; `mix-blend-mode`;
`isolation: isolate`; `will-change` naming one of these; `contain: paint` or `layout`. Animations
that set transform or opacity create one for their duration, which is why a menu sometimes slips
behind a card only while it animates.

Systematic approach:

- Overlays (modals, menus, toasts, tooltips) go in the top layer via `<dialog>` and `popover`, or
  through the component library's portal. They then need no z-index at all.
- Keep a small named scale as tokens for what remains in the page (`--z-sticky`, `--z-header`,
  `--z-drawer`); no raw numbers in components, never 9999.
- Put `isolation: isolate` on the root of any component that uses z-index internally, so its
  layers cannot interleave with the page's.
- To diagnose: DevTools Layers panel or the 3D view shows the contexts; otherwise walk up the
  ancestors checking the property list above.

## Mobile viewport, safe areas and the keyboard

| Unit | Is | Use for |
|---|---|---|
| `100vh` | The largest viewport (browser bars retracted) on mobile | Avoid for full-height layouts: the bottom is cut off behind the toolbar |
| `100dvh` | Current visible height; changes as bars show and hide | App shells and full-height panels (`min-height: 100dvh`) |
| `100svh` | Height with bars showing | Heroes and anything that must not resize while scrolling |
| `100lvh` | Height with bars hidden | Backgrounds that should cover the largest case |

- Safe areas (notch, home indicator, rounded corners): insets are zero unless the viewport meta
  has `viewport-fit=cover`. Then pad fixed bars and full-bleed containers:
  `padding-bottom: max(1rem, env(safe-area-inset-bottom))`, and the left/right insets for
  landscape. Check an installed PWA and landscape orientation, where the insets are largest.
- The on-screen keyboard: on iOS it does not resize the layout viewport, only the *visual*
  viewport, so `position: fixed; bottom: 0` bars and the lower part of a full-height sheet sit
  under the keyboard, and `dvh` does not react. Options, in order: design so the focused field
  and its submit button are in normal flow and can scroll into view; use
  `<meta name="viewport" content="..., interactive-widget=resizes-content">` where supported
  (not Safari at the time of writing; verify); or listen to `window.visualViewport` `resize`
  and set a CSS variable with its height for the element that must stay above the keyboard.
- Inputs with a computed font size under 16px make iOS Safari zoom the page on focus. Keep form
  controls at 16px or larger rather than disabling zoom.
- Touch targets at least 44×44 CSS px with spacing; hover styles inside
  `@media (hover: hover)` so they do not stick after a tap; `overscroll-behavior: contain` on
  scrollable panels and modals so the page behind does not scroll or pull-to-refresh.
- Device emulation does not reproduce browser bars, the keyboard or safe areas. Verify on a real
  phone (remote debugging is in `browser-dom.md`).

## Tokens, Tailwind and CSS modules

Follow what the project has. Greenfield default: Tailwind with tokens defined once as CSS
variables; CSS modules are the alternative for teams that prefer authored CSS. Do not run both
as equals in one codebase.

```css
@import "tailwindcss";
@theme {
  --color-surface: light-dark(oklch(99% 0 0), oklch(18% 0.01 260));
  --color-brand: oklch(62% 0.19 255);
  --spacing-gutter: clamp(1rem, 0.5rem + 2.5vw, 2rem);
}
```

- Tokens are layered: raw values → semantic names (`surface`, `text-muted`, `danger`) →
  occasionally component tokens. Components reference semantic names only. Which values to
  choose belongs to `0x:ui-ux-design`.
- An arbitrary value (`p-[13px]`, `text-[#3a3a3a]`) appearing twice is a missing token.
- Tailwind finds classes by scanning source text: `bg-${color}-500` built at runtime is never
  generated. Map props to complete class strings in an object.
- Reuse by extracting a component, not with `@apply`. Merge conflicting classes passed from
  outside with a merge helper (the common `cn()` built on `clsx` and `tailwind-merge`).
- CSS modules: one module per component, class names by role (`.root`, `.title`), tokens as global
  custom properties on `:root`, no element selectors reaching into children it does not own.

## Modern CSS without a preprocessor

Nesting, layers and `:has()` are Baseline; a new project needs no Sass.

```css
@layer reset, vendor, base, components, utilities;   /* declared once; later layers win */
@import url("vendor.css") layer(vendor);         /* third-party CSS can no longer out-rank yours */

@layer components {
  .field {
    display: grid; gap: .25rem;
    &:has(:user-invalid) { color: var(--color-danger); }
    & > label { font-weight: 500; }
    @media (min-width: 40rem) { grid-template-columns: 12rem 1fr; }
  }
}
```

- Layer order, not specificity, decides between layers; unlayered styles beat all layers. For
  `!important` declarations the order reverses (earlier layers win), which is one more reason
  not to use it. `@import` rules with a layer must come before other rules.
- Keep nesting to one or two levels; deep nesting recreates the specificity problem.
- `:has()` replaces most "parent state" JavaScript: `.card:has(img)`, `form:has(:focus-visible)`,
  `html:has(dialog:modal)`. Anchor it to a specific element rather than `body:has(...)` with a
  broad argument, which forces wide style recalculation.
- `:user-invalid` instead of `:invalid` so fields are not red before the user has typed.
- `@scope` gives real lower-bound scoping in plain CSS; check its Baseline status before using it
  without a fallback.

## Fluid type and spacing

```css
h1 { font-size: clamp(1.75rem, 1.2rem + 2.4vw, 3rem); }
```

- Derive the middle term: slope = (max − min) / (maxViewport − minViewport), expressed in `vw`;
  intercept = min − slope × minViewport, in `rem`. Two or three fluid steps replace a ladder of
  breakpoint overrides.
- The preferred value must include a `rem` term. Pure `vw` font sizes do not respond to browser
  zoom or the user's font-size setting, which fails accessibility requirements. As a rule of
  thumb keep the max no more than 2.5× the min so zoom can still double the text.
- Use the same technique for section padding and gaps. Inside container-query components use
  `cqi` instead of `vw`.
- Body text stays at a fixed `1rem` (or slightly more); fluid sizing is for display type and
  large spacing. Never set the root font size in `px`.
- `text-wrap: balance` on headings and `text-wrap: pretty` on paragraphs as enhancements.

## Subgrid and intrinsic sizing

- Cards in a row whose titles, bodies and footers must align across cards: make each card span
  the parent's rows and adopt them.

```css
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.card  { display: grid; grid-row: span 3; grid-template-rows: subgrid; }
```

- Form rows whose labels share one column width: the form defines `grid-template-columns:
  max-content 1fr`, each row is `grid-column: 1 / -1; display: grid; grid-template-columns: subgrid`.
- Intrinsic keywords: `min-content` (narrowest without overflow), `max-content` (no wrapping),
  `fit-content` (shrink-wrap up to the available space). `grid-template-columns: auto 1fr auto`
  for bar layouts; `width: fit-content` for a button that should not stretch.
- `aspect-ratio` for media boxes and skeletons, so space is reserved before content loads.

## Themes without a flash

```css
:root { color-scheme: light dark; }               /* follow the OS by default */
:root[data-theme="light"] { color-scheme: light; } /* explicit user choice */
:root[data-theme="dark"]  { color-scheme: dark; }
:root {
  --surface: light-dark(oklch(99% 0 0), oklch(18% 0.01 260));
  --text:    light-dark(oklch(22% 0.01 260), oklch(94% 0.01 260));
  --brand-hover: oklch(from var(--color-brand) calc(l - 0.08) c h);
}
```

- `color-scheme` also themes form controls, scrollbars and the default canvas. `light-dark()`
  follows the element's `color-scheme`, so one declaration per token serves both themes and a
  subtree can be forced (`.promo { color-scheme: dark }`). It accepts colors only.
- OKLCH: lightness is perceptually even, so a scale built by stepping `l` looks even, and hue
  stays stable as lightness changes. Derive hover, border and subtle variants with relative color
  syntax or `color-mix(in oklch, ...)` rather than storing every shade. Contrast must still be
  measured per theme (`0x:accessibility`).
- The flash: with OS-only theming there is none, since CSS resolves before first paint. A stored
  user override is unknown to server-rendered HTML, so the page paints in the wrong theme and
  flips. Fix by setting the attribute before paint with a tiny inline script in `<head>`:

```html
<script>
  try { const t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; } catch {}
</script>
```

  or store the choice in a cookie and render the attribute on the server (this makes the page
  vary per user, which costs static caching). In React the server and client `<html>` attributes
  then differ; mark that element to suppress the hydration warning, or use a theme library that
  does exactly this.
- Offer three states: System, Light, Dark. "System" removes the attribute.

## Keeping a stylesheet maintainable

- One scoping mechanism for the codebase (utilities, modules or `@scope`), and styles live next to
  the component they style so deleting the component deletes its CSS.
- Flat specificity: single classes; `:where()` around reset and base selectors; ids and
  `!important` only for overriding third-party code, inside a comment that says so.
- Global CSS is limited to reset, tokens, base element styles and fonts. Anything else global is
  a component that has not been written yet.
- Dead styles: utility frameworks only emit what is used. For authored CSS, the DevTools Coverage
  panel shows unused rules *for the pages and states exercised*, so use it to find candidates,
  then search the codebase for the class before deleting. Classes assembled from strings defeat
  any automated search; do not build class names dynamically.
- Stage: at Prototype, skip layers and component tokens. At Launch, tokens and a z-index scale
  should exist. At Scale, add linting for raw values and visual regression tests
  (`0x:code-quality`).

## Ask the user

- **What is the smallest screen and the main device?** It decides what is designed first and
  where time goes. Default: 360px wide phones first, no horizontal scroll down to 320px.
- **Is dark mode required now?** Retrofitting is cheap only if colors are semantic tokens from
  the start. Default: build with `light-dark()` tokens, ship light plus system dark when the
  design has been checked in both.
- **Should a theme choice follow the account across devices?** That needs server storage and
  per-user rendering. Default: local to the browser.
- **Is a right-to-left language on the roadmap?** If so, use logical properties from day one
  (see `internationalization.md`). Default: use them anyway; they cost nothing.
