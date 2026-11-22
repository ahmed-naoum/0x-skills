# JavaScript bundles

Read this when: the app ships too much JavaScript, a bundle report needs reading, a dependency
looks oversized, code needs splitting, or bundle size should be held by CI.

## Why bytes of JavaScript cost more than other bytes

An image costs download time. JavaScript costs download, then parse, compile and execution on
the main thread, on the user's CPU. A mid-range phone runs the same script several times slower
than a development laptop, so a bundle that feels instant locally produces seconds of blocked
main thread in the field, which shows up as poor INP and delayed hydration.

Measure two sizes and say which one is meant:

- **Compressed transfer size** (Brotli or gzip): what the network carries. Budgets are stated
  in this.
- **Uncompressed size**: what the engine parses. Roughly three to five times the compressed
  size for minified JS; this drives CPU cost.

Rule of thumb for a budget: the JavaScript needed to make a landing page interactive should
stay around 150 to 200 KB compressed on a content or commerce page; an authenticated app screen
can carry more because the user is committed and chunks are cached. The real test is field INP
and main-thread time on a throttled profile, not the number itself.

## Analyze before cutting

| Build tool | How to see what is in the bundle |
|---|---|
| Next.js with Turbopack (the default bundler from Next.js 16) | The built-in analyzer: `pnpm next analyze` in current releases, introduced as `next experimental-analyze` in 16.1. The webpack plugin does not apply |
| Next.js with webpack (older versions, or a build that opts into webpack) | `@next/bundle-analyzer`, run the build with `ANALYZE=true` |
| Vite or Rollup | `rollup-plugin-visualizer` (treemap of the output) |
| esbuild | `--metafile=meta.json`, then esbuild's bundle analyzer |
| Anything with source maps | `source-map-explorer 'dist/**/*.js'` |

Current Next.js no longer prints per-route JavaScript sizes in the `next build` output, so the
analyzer is the place to look.

Read the treemap in this order:

1. **The shared chunk loaded on every route.** Anything here is paid by every visitor. A
   charting library or an editor in the shared chunk is the most common large finding.
2. **Duplicates.** The same library twice in different versions, or once as ESM and once as
   CommonJS. Confirm with `pnpm why <package>`; fix with `pnpm dedupe`, aligning version ranges,
   or an override when a transitive dependency pins an old major. Where overrides live depends
   on the pnpm version: `overrides` in `pnpm-workspace.yaml` for current pnpm, which no longer
   reads the `pnpm` field of `package.json` that older versions used. An override in the wrong
   place is ignored, so confirm with `pnpm why` afterward.
3. **Oversized single dependencies.** Compare the size against what the product uses from it.
4. **Own code that is unexpectedly big.** Usually generated code, a large JSON or locale file
   imported statically, or inlined base64 assets.
5. **Polyfills.** A stale browser target ships transforms and `core-js` for browsers nobody
   uses. Set the target to current evergreen browsers unless analytics say otherwise.

Usual suspects and their replacements:

| Finding | Replacement |
|---|---|
| `moment` (large, not tree-shakable, locales bundled) | `Intl.DateTimeFormat` and `Intl.RelativeTimeFormat` for display; `date-fns` for arithmetic |
| `lodash` whole-package import | Native array and object methods, `structuredClone`; `lodash-es` with named imports for the rest |
| Icon library imported whole | Per-icon imports, or an SVG sprite (`images-fonts.md`) |
| Charting, rich-text editor, code highlighter, PDF, map, 3D | Lazy-load on the route or interaction that needs it; render highlighting and Markdown on the server |
| Validation schemas and ORM types pulled into the client | Import types with `import type`; keep server modules out of client files |
| Cloud SDK or full Firebase client | Call the service from the server; use modular imports if the client is unavoidable |
| Animation library for two transitions | CSS transitions, the Web Animations API, View Transitions |
| All locale files | Load the active locale dynamically |

Before adding any dependency, check its compressed size and whether it ships ES modules. A
dependency is a recurring cost for every visitor, weighed against the hours it saves once.

## Ship less by not shipping

The largest reductions come from moving work, not from minifying.

**Render on the server.** With React Server Components, a component that does not need state,
effects or browser APIs sends HTML and no component code. Rules:

- `"use client"` marks a boundary: that file and everything it imports goes to the browser.
  Put the directive on the smallest interactive leaf (the button, the form), not on the page or
  layout. One directive at the top of a page file turns the route into a client app.
- Pass server-rendered content into client components as `children` instead of importing it
  inside them; children stay server-rendered.
- Do formatting, Markdown, syntax highlighting, sanitizing and data shaping on the server, so
  those libraries never reach the client.
- Props crossing the boundary are serialized into the HTML. Passing a whole database row where
  the component needs three fields bloats the document; select the fields.
- A provider at the root (theme, query client, auth) does not make its children client
  components, but every hook-heavy library imported there lands in the shared chunk.

Rendering strategy and hydration design belong to `0x:react-nextjs`.

**Use the platform.** Each of these replaces a library or a block of component code:

| Need | Platform feature |
|---|---|
| Modal, drawer | `<dialog>` with `showModal()` |
| Disclosure, accordion | `<details>` and `<summary>` |
| Menus, tooltips, popovers | The `popover` attribute; CSS anchor positioning where supported |
| Carousel, snapping | CSS scroll snap |
| Parent or state-based styling | `:has()`, container queries |
| Lazy media | `loading="lazy"` |
| Dates, numbers, plurals, lists, collation | `Intl.*` |
| Form validation basics | Constraint validation attributes, checked again on the server |
| Page and element transitions | View Transitions API, CSS transitions |
| Smooth scroll, sticky headers, scroll-linked effects | `scroll-behavior`, `position: sticky`, scroll-driven animations where supported |

Check browser support against the project's audience before relying on the newer ones, and
keep the accessible headless primitive when the native element cannot meet the interaction
requirements (`0x:accessibility`).

## Code-split by route, lazy-load the heavy parts

Frameworks with file-based routing split by route automatically. The work is keeping heavy,
rarely-used code out of the route's initial chunk.

| Candidate | Split it? | Trigger |
|---|---|---|
| Modal, drawer, command palette | Yes | On open; preload on hover or focus of the trigger |
| Editor, chart, map, video player below the fold | Yes | On visibility or interaction |
| Admin-only or role-only panels | Yes | On render for that role |
| Heavy library used in one handler (export to PDF, CSV parsing, image cropping) | Yes | `await import()` inside the handler |
| Anything visible in the first viewport | No | Splitting it adds a round trip to LCP and usually a layout shift |
| Small components (a few KB) | No | The request overhead and waterfall cost more than the bytes |

```tsx
import dynamic from 'next/dynamic';

const Chart = dynamic(() => import('./chart'), {
  loading: () => <div className="h-64 animate-pulse rounded bg-neutral-100" />,
});
```

```ts
async function onExport() {
  const { exportToPdf } = await import('./export-pdf');   // loaded on first use
  await exportToPdf(rows);
}
```

Traps:

- The loading placeholder must have the final dimensions, or the split creates CLS.
- A lazy component that fetches data on mount makes a waterfall: chunk, then data. Start the
  data request in parallel with the import, or fetch on the server and pass it down.
- A click that has to download a chunk first has poor INP on slow links unless feedback is
  shown immediately. Preload on intent (pointer enter, focus) so the chunk is usually there.
- `ssr: false` removes the component from server HTML. Use it only for code that cannot run on
  the server; in the App Router it is only allowed inside a client component.
- After a deploy, clients holding the old HTML request chunk files that no longer exist. Keep
  previous build assets available for a while or handle the chunk-load error with a reload.

## Make tree-shaking work

Tree-shaking removes unused exports only when the bundler can prove that dropping a module has
no effect. Four conditions decide it:

1. **ES modules end to end.** `import`/`export` are statically analyzable; `require` is not.
   A CommonJS dependency is usually included whole. Prefer packages whose `package.json` has an
   `exports` map with an `import` condition (or a `module` field).
2. **Side-effect flags.** `"sideEffects": false` in a package's `package.json` tells the
   bundler that unused modules can be dropped entirely. For own packages in a monorepo, set it,
   listing the exceptions: `"sideEffects": ["*.css", "./src/polyfills.ts"]`. Marking a file that
   does have side effects (global CSS, a polyfill, a registration call) as pure silently removes
   it in production builds only.
3. **No barrel-file traps.** An `index.ts` that re-exports everything makes one import touch
   every module behind it. With correct side-effect flags the bundler recovers, but in practice
   one impure module (a top-level call, a class with decorators, a CSS import) drags in its whole
   subtree, and dev builds and tests slow down regardless. Import from the specific module in
   application code; in Next.js, list offending libraries in `optimizePackageImports` (under
   `experimental` in the config at the time of writing; several common icon and utility
   libraries are on its default list already).
4. **Pure top-level code.** Top-level function calls and `Object.assign` on exports keep
   modules alive. A TypeScript `enum` compiles to an immediately invoked function that some
   bundlers cannot drop; prefer `as const` objects over enums in shared packages.

Also: `import * as lib` is fine when members are accessed statically (`lib.x`), and defeats
shaking when the namespace object is passed around or indexed dynamically. `import type` is
erased entirely and is the safe way to share types between server and client.

Check: build, then search the output for a string that exists only in the code expected to be
removed. The analyzer treemap shows the same thing more slowly.

## Enforce a budget in CI

Without a check, bundle size only grows: each addition is individually reasonable. Enforce at
Launch; at Prototype, a look at the analyzer before release is enough.

`size-limit` works with any build output:

```json
{
  "scripts": { "size": "size-limit" },
  "size-limit": [
    { "name": "client js", "path": ".next/static/chunks/**/*.js", "limit": "400 kB" },
    { "name": "css", "path": ".next/static/css/*.css", "limit": "30 kB" }
  ]
}
```

Install `size-limit` with the `@size-limit/file` plugin for plain file-size checks. Run it
after the build in the pull-request workflow; a non-zero exit fails the job. The plugin
measures Brotli-compressed size unless an entry sets `"gzip": true` or `"brotli": false`.

The glob above sums the chunks of every route, so its limit is a whole-app ceiling, not the
per-page figure from the top of this file; add an entry for the shared chunk or the landing
route once the file names are known. Output layout differs between bundlers and versions
(Turbopack builds may emit CSS next to the JS chunks instead of in `static/css`): list the
build directory and make sure every `path` matches real files, because a pattern that matches
nothing guards nothing.

Rules that keep the budget useful:

- Set the first limit just above today's size, then ratchet down after each reduction. A budget
  far above reality catches nothing; one below reality gets disabled the same day.
- Budget the total and, separately, the shared chunk or the landing route. A total can hide a
  doubling of the one chunk every visitor loads.
- Show the delta against the base branch in the pull request. A visible "+38 kB from this
  change" prevents more regressions than the hard limit does.
- Raising the limit is allowed, as a deliberate reviewed change to the config in the same pull
  request, with the reason in the description.
- Bytes are deterministic, so this check can hard-fail. Timing checks in CI are noisy and
  belong in `performance-budgets.md`.

## Third-party widgets: facades and workers

A chat widget, video embed or map commonly costs more JavaScript than the whole first-party
page, and most visitors never use it.

**Facade**: render a lightweight stand-in that looks like the widget and load the real one on
interaction.

| Widget | Facade |
|---|---|
| Video embed | Poster image and play button; inject the player iframe on click (`lite-youtube-embed` and similar) |
| Chat | A plain button styled as the launcher; load the vendor script on click, or on idle after a delay |
| Map | Static map image; load the interactive map on click or on visibility |
| Social embeds | Server-rendered static card with a link |

Facade rules: same dimensions as the real widget; a real `<button>` or link so keyboard users
can trigger it; preconnect to the vendor origin on hover so the click feels immediate; if the
vendor exposes an "open on load" call, invoke it after loading so the user does not click twice.
On touch devices a video facade can need two taps because autoplay after an injected iframe is
not always honored; test it.

**Workers**: two different uses.

- Own heavy computation (parsing a large file, search indexing, image processing, diffing):
  move it to a Web Worker, with a small RPC helper such as Comlink. Data crossing the boundary
  is copied unless transferred, so pass large buffers as transferables.
- Third-party tags in a worker (Partytown-style): the library proxies DOM access from a worker
  back to the main thread. It can remove analytics and pixel cost from the main thread, but it
  breaks tags that expect synchronous DOM access or measure the page themselves, and debugging
  moves to a place vendors do not support. Use it only for tags that just collect and send, and
  only after deferral and facades were not enough. Check framework support before choosing it.

## Ask the user

- **Which browsers must be supported?** Decides polyfills, transpilation target and which
  platform features can replace libraries. Default: current evergreen browsers, last two
  versions, no legacy bundle.
- **Which third-party widgets must be live at page load?** A chat that opens itself for sales
  reasons cannot be a facade. Default: everything behind a facade or idle load, with the measured
  cost shown.
- **Is a hard-failing bundle budget acceptable to the team?** It will block merges. Default:
  hard fail on the total, report-only delta comment per pull request.
- **May a heavy dependency be replaced?** Swapping an editor or chart library changes features
  and behavior. Default: lazy-load first; propose replacement only with the size and effort
  stated.
