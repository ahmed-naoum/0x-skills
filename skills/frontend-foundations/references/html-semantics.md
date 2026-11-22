# HTML semantics and document structure

Read this when: choosing elements for a page or component, building an overlay (modal, menu, tooltip),
setting `<head>` metadata, embedding media or third-party frames, or deciding whether a platform
feature is safe to use yet.

## Element choice: the rule that prevents most rework

Pick the element by what it *does*, then style it. A native element brings focus, keyboard
behavior, form participation and an accessibility role for free; a `div` with a click handler
brings none, and re-creating them is where bugs and audit findings come from.

| The thing | Use | Not | Trap |
|---|---|---|---|
| Goes to a URL (new page, anchor, download) | `<a href>` | `<button onClick={router.push}>` | No middle-click, no "copy link", no prefetch, nothing before JS loads |
| Does something on this page | `<button type="button">` | `<a href="#">`, `<div onClick>` | Inside a `<form>`, a button without `type` is `submit` |
| Show/hide a block | `<details><summary>` | Custom accordion | Same `name` on several `<details>` gives an exclusive accordion; content is found by find-in-page |
| Modal that blocks the page | `<dialog>` + `showModal()` | `div` + focus-trap library | Setting the `open` attribute yourself gives a non-modal dialog: no backdrop, no inertness |
| Menu, tooltip, toast, picker panel | `popover` attribute | Absolutely positioned div + z-index | A popover is not modal: the rest of the page stays interactive |
| One choice of a short fixed list | `<select>` or radio group | Custom dropdown | A custom listbox is weeks of keyboard and mobile work |
| On/off setting | `<input type="checkbox">` (styled as a switch) | `div role="switch"` | Needs a `<label>`; clicking the label must toggle |
| Progress, meter | `<progress>`, `<meter>` | Nested divs | |
| Date or time | `<time datetime="2026-11-22">` | Bare text | Machine-readable value for parsers and translation tools |

Reach for a custom widget only when the native one cannot express the interaction (async
combobox, date range, drag-reorder). Then take it from a headless primitive library, not from
scratch; ARIA and keyboard patterns are owned by `0x:accessibility`.

## Page structure

- One `<main>` per page. `<header>`, `<nav>`, `<footer>`, `<aside>` at the top level become
  landmarks; the same elements nested inside `<article>` or `<section>` do not. Two `<nav>`
  elements need distinguishing labels (`aria-label="Primary"`, `"Footer"`).
- `<section>` is a landmark only when it has an accessible name (`aria-labelledby` pointing at its
  heading). Without one it is a `div` with intent. Use `<article>` for something that makes sense
  lifted out of the page: a post, a product card, a comment.
- Headings describe the outline, not the size. One `<h1>` naming the page, then no skipped levels.
  Browsers never implemented the "document outline" where `<h1>` inside nested sections demotes
  itself; every `<h1>` is level 1 to assistive technology. Choose the level from the structure and
  the size from a class.
- In a reusable component, take the heading level as a prop (`as="h3"`) rather than hard-coding
  it; the right level depends on where the component is placed.
- Lists: `<ul>` for a set, `<ol>` where order carries meaning (steps, rankings), `<dl>` for
  name/value pairs (order summaries, metadata, specs). Navigation is a `<ul>` inside `<nav>`.
  Removing list markers with `list-style: none` drops list semantics in Safari's screen reader;
  add `role="list"` where the count matters to the reader.
- A clickable card: one real `<a>` on the title, stretched with a pseudo-element
  (`a::after { content: ""; position: absolute; inset: 0 }` on a `position: relative` card).
  Wrapping the whole card in `<a>` makes the entire content the link name, and nested interactive
  elements inside a link are invalid.

Check: with CSS disabled (or in reader mode) the page still reads in a sensible order; the heading
list in the DevTools accessibility tree reads like a table of contents.

## Overlays: dialog, popover and anchor positioning

Both `<dialog>` opened with `showModal()` and open popovers render in the **top layer**: above
everything, regardless of `z-index`, `overflow: hidden` or transformed ancestors. That removes the
reason portals and z-index scales existed for overlays.

| Need | Build | What the platform gives |
|---|---|---|
| Confirm, form in a modal, lightbox | `<dialog>` + `dialog.showModal()` | Focus moves in and is contained, the rest of the page is inert, Esc closes, `::backdrop`, focus returns to the opener on close |
| Dropdown menu, popover panel, date panel | `<div popover id="m">` + `<button popovertarget="m">` | Light dismiss (outside click, Esc), one `auto` popover open at a time, toggling with no JS |
| Toast, non-dismissing notice | `popover="manual"` + `showPopover()` | Top layer only; open and close are yours |
| Tooltip | A popover shown on hover and focus, described by `aria-describedby` | Hover-triggered declarative popovers are still arriving; check Baseline before relying on them |

Rules that are easy to get wrong:

- Close a dialog with `<form method="dialog">` or `dialog.close(value)`; read `dialog.returnValue`
  in the `close` event. The `cancel` event fires on Esc and can be prevented while saving.
- Outside-click-to-close for a modal dialog is not default behavior. The `closedby="any"`
  attribute provides it where supported; otherwise listen for `click` on the dialog and close
  when `event.target === dialog` (the backdrop reports the dialog itself as target), with the
  content in an inner wrapper that carries the padding.
- A modal dialog does not lock page scroll. Add
  `html:has(dialog:modal) { overflow: hidden; scrollbar-gutter: stable; }`.
- Put `autofocus` on the element that should receive focus (the least destructive action in a
  confirm dialog). Do not conditionally render the `<dialog>` element in React and then call
  `showModal()` in the same tick without a ref check; keep the element mounted and toggle it.
- A popover is centered in the viewport by the browser's default styles (`inset: 0; margin: auto`).
  To attach it to its trigger, reset those and use anchor positioning:

```css
.trigger { anchor-name: --menu; }
.menu {
  position-anchor: --menu;
  inset: auto;
  margin: 0;
  position-area: block-end span-inline-end;
  position-try-fallbacks: flip-block, flip-inline;
}
```

- Anchor positioning reached all engines recently. Check its Baseline status; where the audience
  includes older browsers, guard with `@supports (anchor-name: --a)` and fall back to a
  positioning library (Floating UI) or to a centered popover, which is acceptable on phones.
- An element cannot be both a dialog opened modally and a popover at once; pick by whether the
  page behind must be blocked.

The house default in React projects is a headless primitive library; current versions sit on the
same concepts. Prefer native `<dialog>` and `popover` directly for content sites, small projects
and anything that must work before hydration.

## Document metadata

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Invoice INV-204 · Acme Billing</title>
  <meta name="description" content="One sentence that would make sense as a search result.">
  <link rel="canonical" href="https://example.com/invoices/204">
  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link rel="icon" href="/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta property="og:title" content="Invoice INV-204">
  <meta property="og:description" content="...">
  <meta property="og:image" content="https://example.com/og/invoice-204.png">
  <meta property="og:url" content="https://example.com/invoices/204">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
</head>
```

- `charset` must be within the first 1024 bytes; keep it first.
- Viewport: never add `user-scalable=no` or `maximum-scale=1`; they block zoom for people who
  need it. Add `viewport-fit=cover` only when the design handles safe-area insets (see
  `css-layout.md`).
- `lang` is a BCP 47 tag on `<html>` (`en`, `pt-BR`), and on any element whose content is in
  another language. It drives hyphenation, font selection, quote marks, spell-check, translation
  prompts and screen-reader pronunciation. Add `dir="rtl"` for right-to-left locales.
- `<title>`: unique per page, most specific part first, site name last. It is the tab label, the
  history entry, the bookmark name and the default share text. A single-page app must update it on
  every route change.
- Icons: the four files above cover practice. `favicon.ico` at the site root is still requested
  blindly by some clients; the Apple touch icon is 180×180 with no transparency. Installable apps
  add manifest icons (see `pwa-mobile.md`).
- Social cards: `og:image` must be an absolute HTTPS URL, publicly fetchable without cookies, at a
  1.91:1 ratio (1200×630 is the common size). Crawlers do not run JavaScript, so these tags must
  be in the server-rendered HTML. Platforms cache the card; after changing it, use each
  platform's card debugger to refetch.
- `<meta name="color-scheme" content="light dark">` lets the browser paint the right canvas color
  before any CSS arrives; pair it with the CSS in `css-layout.md`.
- In Next.js these come from the Metadata API (`metadata` export, `generateMetadata`, file
  conventions such as `app/icon.svg` and `opengraph-image`), not hand-written tags; see
  `0x:react-nextjs`. Search-specific tags and structured data belong to `0x:growth-marketing`.

Check: `curl -s https://site/page | grep -iE '<title|og:|canonical|viewport'` shows the tags
without running JavaScript.

## Tables, figures and code

- A table is for data with two axes. Use `<caption>` (the table's name), `<thead>`/`<tbody>`,
  `<th scope="col">` for column headers and `<th scope="row">` for the cell that names each row.
  Never use a table for layout, and never build a data table from divs: the row and column
  relationships are the point.
- Wide tables on phones: wrap in a container with `overflow-x: auto`, and make that container
  focusable and named (`tabindex="0" role="region" aria-labelledby="caption-id"`) so keyboard
  users can scroll it. Changing `display` on table elements to restack them as cards can strip
  table semantics in some browsers; if cards are the mobile design, render different markup.
- Numeric columns: `text-align: end` and `font-variant-numeric: tabular-nums` so digits align.
- `<figure>` with `<figcaption>` groups an image, chart, code sample or quote with its caption.
  The caption does not replace `alt`: `alt` says what the image shows, the caption says why it
  is there.
- Code: `<pre><code class="language-ts">` for blocks, `<code>` inline, `<kbd>` for keys the user
  presses, `<samp>` for program output. Escape `<` and `&`. Add `translate="no"` so page
  translators leave code alone, and give long lines `overflow-x: auto` on the `<pre>`, not
  wrapping, with `tabindex="0"`.

## Baseline instead of browser lists

Baseline answers "can this be used?" per feature, which a list of browser versions cannot.

| Status | Meaning | Policy |
|---|---|---|
| Widely available | Interoperable in Chrome, Edge, Firefox and Safari (desktop and mobile) for 30 months | Use without a fallback |
| Newly available | Works in the latest version of all of them | Use as an enhancement: the page must remain usable where it is missing |
| Limited availability | Missing from at least one engine | Only behind feature detection with a designed fallback, or not at all |

- Look the feature up (MDN's Baseline banner, webstatus.dev, caniuse) at the time of use. Do not
  rely on remembered support data; this is the fastest-moving fact in frontend work.
- Detect features, never browsers: `@supports (anchor-name: --a) { ... }`,
  `CSS.supports('selector(:has(a))')`, `'popover' in HTMLElement.prototype`,
  `if (!document.startViewTransition) { update(); return; }`.
- Make the build agree with the policy: Browserslist accepts Baseline queries, and linters can
  flag CSS and HTML features outside the chosen Baseline target. Set the target once in the
  project config rather than per file.
- Shift the default only on evidence: check the product's own analytics for the browser and OS
  mix. B2B desktop tools can usually sit at Newly available; consumer products with a long tail of
  old phones should stay at Widely available. iOS browsers are all WebKit and update with the OS,
  so old iPhones pin old Safari.
- Polyfill only what blocks core function. A missing animation or anchor placement is a degraded
  experience, not a bug.

## Progressive enhancement

The baseline experience is server-rendered HTML that works before, and without, JavaScript; then
JavaScript improves it. On a slow phone the gap between "HTML painted" and "JS ready" is seconds,
and everything a user taps in that gap either works or looks broken.

- Navigation is `<a href>`. Mutations are `<form method="post" action>` with a submit button; a
  framework's server-function forms keep this property. Detail in `forms.md`.
- Content that matters (text, prices, links) is in the initial HTML, not fetched after mount.
- Disclosure, dialogs and popovers use the native elements above, so they function unhydrated.
- A control that cannot work without JS should be rendered disabled or absent until it can,
  rather than present and dead.
- `<script type="module">` and `defer` scripts do not block parsing; a plain `<script>` in the
  head does. Inline blocking scripts are justified only for tiny pre-paint work such as applying
  a stored theme.
- Test: in DevTools, block the main JS bundle (Network → right-click → Block request URL) or
  throttle to "Slow 4G" and try the primary action during load. Disabling JS entirely is a cruder
  version of the same test.

Skip the no-JS path at Prototype for app screens behind a login whose whole purpose is
interactive (editors, dashboards). Do not skip it for landing pages, content, sign-up, login and
checkout: those meet the slowest devices and the widest range of browsers.

## Media and iframes

- Every `<img>` and `<video>` gets `width` and `height` attributes (the intrinsic pixel size);
  the browser derives the aspect ratio and reserves space, with `height: auto` in CSS keeping it
  responsive. Missing dimensions are the main cause of layout shift.
- `loading="lazy"` on images and iframes below the fold; never on the hero image or anything
  likely to be the largest element in the first viewport. Image formats, `srcset`/`sizes` and
  fetch priority are owned by `0x:web-performance`.
- `alt` is required: a description when the image carries information, `alt=""` when decorative.
- Video that autoplays must be `muted` and, on iPhone, `playsinline`, or it will not start or
  will go fullscreen: `<video autoplay muted loop playsinline poster="...">`. Use
  `preload="metadata"` (or `none` with a poster) so a page of videos does not download them all.
  Provide captions with `<track kind="captions">` for spoken content.
- Iframes: always a `title`, explicit `width`/`height` or an `aspect-ratio` wrapper, and
  `loading="lazy"` below the fold.
- Sandbox anything not fully trusted: `<iframe sandbox="allow-scripts allow-forms">`. An empty
  `sandbox` is the most restrictive. `allow-scripts` together with `allow-same-origin` on content
  from the page's own origin lets the frame remove its own sandbox; serve user content from a
  separate origin instead. Grant capabilities explicitly with `allow="fullscreen; clipboard-write"`
  and set `referrerpolicy`. Header-level framing rules and CSP are in `0x:web-security`.
- Heavy third-party embeds (video players, maps, chat widgets): render a static facade (thumbnail
  plus play button) and create the iframe on click. This also keeps third-party cookies and
  consent questions out of the initial load.

## Ask the user

- **Which browsers and devices must work?** It sets the Baseline target and whether fallbacks are
  built. Default: Baseline Widely available for everything required, Newly available as
  enhancement; confirm against analytics once there is traffic.
- **Must sign-up, login and checkout work when JavaScript fails or is slow?** It costs some
  design constraint. Default: yes for those flows and for public content; no for authenticated
  app screens.
- **What should a shared link look like?** Title, description and image per page type are brand
  decisions. Default: page title, first-paragraph description, one generic branded 1200×630 image
  until per-page images are worth generating.
- **Are third-party embeds acceptable on first load?** They bring tracking and weight. Default:
  click-to-load facades.
