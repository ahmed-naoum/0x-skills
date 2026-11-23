# Layer 6: Frontend

Read this when: the user asks what there is to know about frontend, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

What runs in the user's browser, on any device?

Competencies: 131 (62 ● / 60 ◐ / 9 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## frontend-foundations

Build on the web platform itself: semantic HTML, CSS layout and responsive design, JavaScript and TypeScript, the browser's rendering and events, forms, animation, internationalization, and PWA and mobile packaging.

**HTML semantics and document structure** (`references/html-semantics.md`)

- ● Write semantic HTML with correct landmarks, headings and lists
- ● Choose native elements (button, a, details, dialog) before custom widgets
- ● Set document metadata: title, viewport, lang, icons and social cards
- ● Mark up tables, figures and code for structure, not layout
- ● Target Baseline feature availability instead of browser-version lists
- ● Build overlays with native dialog, popover and anchor positioning
- ◐ Use progressive enhancement so core content works before JavaScript loads
- ◐ Embed media and iframes with dimensions, lazy loading and sandboxing

**CSS layout and responsive design** (`references/css-layout.md`)

- ● Lay out responsive pages mobile-first with grid, flexbox and container queries
- ● Debug layout using the cascade, specificity and box model
- ● Style with Tailwind or CSS modules driven by design tokens
- ● Handle safe areas, the virtual keyboard and dynamic viewport units
- ● Prevent overflow, stacking-context and z-index bugs systematically
- ◐ Use native nesting, cascade layers and :has() without a preprocessor
- ◐ Build fluid type and spacing with clamp() instead of breakpoint ladders
- ◐ Align nested components with subgrid and intrinsic sizing
- ◐ Implement themes with color-scheme, light-dark() and OKLCH custom properties, without a load flash
- ◐ Keep a growing stylesheet maintainable: scoping, naming and dead-style removal

**JavaScript and TypeScript** (`references/javascript-typescript.md`)

- ● Fix async ordering bugs by reasoning about the event loop and microtasks
- ● Start every project in strict TypeScript, including config and scripts
- ● Model states with discriminated unions so invalid states cannot compile
- ● Narrow unknown data at boundaries instead of casting with as or any
- ● Handle errors, cancellation and timeouts in async code with AbortController
- ● Use generics, inference and utility types without unreadable type gymnastics
- ◐ Use ES modules, package exports and CommonJS interop correctly
- ◐ Use Baseline built-ins (structuredClone, Intl, iterator helpers, Temporal when Baseline) instead of libraries
- ◐ Find and fix leaks from listeners, timers and detached DOM nodes

**The browser: rendering pipeline, DOM, events and DevTools** (`references/browser-dom.md`)

- ● Inspect and live-edit DOM, computed styles and layout in DevTools to find a bug
- ● Debug a real phone remotely with Chrome DevTools or Safari Web Inspector
- ● Handle pointer, keyboard and touch events with delegation and passive listeners
- ● Choose client storage: cookies, localStorage, IndexedDB, Cache API or OPFS
- ◐ Predict whether a change triggers layout, paint or only compositing before making it
- ◐ Use Intersection, Resize and Mutation observers instead of polling
- ◐ Move heavy work off the main thread with web workers
- ◐ Use platform APIs (clipboard, share, file, fullscreen) with permission and fallback
- ○ Build framework-free widgets with custom elements where they fit

**Forms** (`references/forms.md`)

- ● Write semantic HTML forms that work before JavaScript loads
- ● Set input types, autocomplete and inputmode for autofill and the right keyboard
- ● Validate inline and on the server, showing each error beside its field
- ● Block double submits and show pending state on submit
- ● Share one validation schema between client and server
- ◐ Preserve form state across reload, back navigation and app switch
- ◐ Prevent lost work with autosave, drafts and unsaved-changes warnings
- ◐ Build multi-step forms with per-step validation and resumable progress
- ◐ Build date, combobox and file-drop inputs from accessible primitives

**Animation on the web** (`references/animation.md`)

- ● Animate transform and opacity so motion stays on the compositor
- ● Choose CSS transitions, the Web Animations API or a library for an effect
- ● Honor prefers-reduced-motion with meaningful alternatives
- ◐ Animate navigations with View Transitions
- ◐ Build scroll-driven animations with CSS timelines instead of scroll listeners
- ◐ Animate elements entering and leaving, including display and auto height
- ◐ Animate layout changes with FLIP or a layout-animation library
- ◐ Profile janky animation and fix dropped frames
- ○ Sequence complex timelines and decide when to move to canvas or WebGL

**Internationalization** (`references/internationalization.md`)

- ● Format dates, numbers and currencies with Intl for the user's locale
- ● Design layouts that survive text expansion and long words
- ● Externalize strings as ICU messages with plurals and interpolation
- ◐ Route and detect locales with URLs and a user override
- ◐ Support right-to-left layouts with logical CSS properties
- ◐ Run a translation workflow: extraction, context, AI drafts and human review
- ◐ Display and accept times correctly for users in different time zones
- ○ Localize names, addresses, phone numbers and sort order

**PWA, offline and the native boundary** (`references/pwa-mobile.md`)

- ● Decide between responsive web, installable PWA, cross-platform and native apps
- ● Detect offline state and queue or block actions honestly
- ◐ Ship an installable PWA with manifest, service worker and offline shell
- ◐ Version and update a service worker without serving stale or private responses
- ◐ Wrap the web app with Capacitor or build with Expo, reusing the API
- ◐ Open emailed and shared URLs in the installed app with universal and app links
- ◐ Fix in-app webviews that break cookies, redirects and wallets
- ◐ Pass App Store and Play review (privacy labels, account deletion) and appeal rejections
- ○ Implement in-app purchases and follow store billing rules per region
- ○ Run staged rollouts, crash reporting and forced upgrades of old app versions

## react-nextjs

Build the application layer of the frontend with React and a meta-framework: rendering strategy per route, where editable content lives, server components and server functions, data and state, routing, component architecture and build tooling.

**Framework, rendering strategy and content sources** (`references/rendering-strategies.md`)

- ● Choose per route between static, server-rendered, streamed and client rendering
- ● Choose a meta-framework: Next.js, React Router, TanStack Start, Astro, SvelteKit or Nuxt
- ● Render useful HTML for crawlers and link previews
- ● Control framework caching with explicit tags and revalidation
- ● Choose where content lives: repo MDX, a headless CMS or a site builder
- ◐ Ship static shells with dynamic holes via partial prerendering or islands
- ◐ Decide when HTML-over-the-wire (htmx, Hotwire) beats a JavaScript framework
- ◐ Model content types and wire draft preview and publish-time revalidation
- ○ Self-host Next.js and know what a managed platform was doing for you

**Server components, server functions and hydration** (`references/server-components.md`)

- ● Build with React Server Components, keeping client components at the leaves
- ● Mutate data with server functions that validate and authorize every call
- ● Mark server-only modules so importing them from client code fails the build
- ● Stream HTML through Suspense boundaries with designed loading states
- ● Avoid request waterfalls by fetching in parallel and preloading
- ● Diagnose and fix a hydration mismatch
- ◐ Cut hydration cost by shrinking client boundaries and serialized props

**Data fetching and state** (`references/data-state.md`)

- ● Keep server data in a query cache, not a global store
- ● Put view state in the URL so pages are shareable
- ● Choose local state, context or an external store for client state
- ● Fetch data where it is used and deduplicate requests across components
- ● Invalidate and optimistically update cached server data after mutations
- ● Wire forms to mutations with pending, error and optimistic states
- ◐ Compute derived values during render instead of syncing state in effects
- ◐ Merge realtime updates into cached data without flicker or duplicates
- ◐ Let the React Compiler memoize instead of hand-written useMemo

**Routing and navigation** (`references/routing-navigation.md`)

- ● Structure routes, layouts and nested segments around the product's navigation
- ● Protect routes with server-side checks, not client redirects
- ● Add loading, error and not-found boundaries to each route segment
- ◐ Restore scroll, focus and state on back and forward navigation
- ◐ Build modal and parallel routes that deep-link correctly
- ◐ Handle redirects, rewrites and locale or tenant routing in middleware
- ◐ Type links and route params so broken routes fail at compile time
- ○ Migrate routes incrementally between routers or frameworks

**Component architecture** (`references/components.md`)

- ● Compose accessible headless primitives with owned styles, shadcn-style
- ● Write custom hooks that encapsulate one concern and are testable
- ◐ Design component APIs: composition over configuration, controlled versus uncontrolled
- ◐ Split components at server, client and data boundaries, not by file size
- ◐ Build typed component variants from design tokens
- ◐ Develop and document components in isolation with a component workshop
- ◐ Render long lists with virtualization and stable keys
- ◐ Review a frontend pull request for component boundaries and render cost

**Build tooling** (`references/build-tooling.md`)

- ● Bundle with Vite or Turbopack instead of hand-written Webpack config
- ● Configure TypeScript, path aliases and module resolution for the framework
- ● Manage environment variables and their public or private exposure at build time
- ● Process fonts, images, SVG and CSS through the build pipeline
- ◐ Debug build failures from module resolution and ESM or CommonJS mismatches
- ◐ Set browser targets, polyfills and transpilation from Baseline data
- ◐ Speed up dev-server startup, hot reload and production builds
- ◐ Pin toolchain versions so builds are identical on laptops and CI

## 3dui

Build live 3D product websites with three.js and Next.js: the object is code, lit like a photo studio and directed by the scroll.

**Live 3D product sites**

- ● Drive all motion from one shared clock
- ● Adapt render quality to phones to hold frame rate
- ◐ Lathe-turn round parts from a profile curve
- ◐ Author physical metal and glass materials with brushed anisotropic finishes
- ◐ Light the product with a PMREM studio environment rotated by the cursor
- ◐ Direct a scroll-driven camera cue list that frames objects by size
- ◐ Stagger exploded views with two-column callouts and a blueprint edges-only mode
- ◐ Apply film-style post: MSAA HDR, bloom, ACES tone mapping and grain
- ○ Build procedural geometry in millimeters: SDF shapes, marching-squares trace, beveled extrude
- ○ Synthesize sound with Web Audio; unlock audio and tilt with one hold-to-act gesture
