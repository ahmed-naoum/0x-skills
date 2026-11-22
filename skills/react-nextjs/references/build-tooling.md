# Build tooling

Read this when: setting up or debugging the bundler, TypeScript config or path aliases; an
environment variable is undefined or leaked; assets (fonts, images, SVG, CSS) need wiring; a
build fails or is slow; choosing browser targets; pinning versions; or upgrading the framework.

## Bundler: use the framework's, configure little

| Project | Bundler | Notes |
|---|---|---|
| Next.js 16 | Turbopack, the default for `next dev` and `next build` | A custom `webpack()` function in the config makes `next build` fail until it is migrated or the script passes `--webpack` |
| Everything else (React Router, TanStack Start, Astro, SvelteKit, a plain SPA) | Vite | Vite 8 bundles with Rolldown and transforms with Oxc |
| A library published to npm | A library bundler (tsdown or similar) | App bundlers are for apps |

Do not write Webpack config for a new project. For an existing `webpack()` customization, list
what it does and translate each item:

| Webpack customization | Turbopack or Vite equivalent |
|---|---|
| `resolve.alias` | `paths` in tsconfig (both read it), or `turbopack.resolveAlias` |
| A loader (SVGR, raw, YAML, GraphQL) | `turbopack.rules`, which runs most webpack loaders; a Vite plugin |
| `DefinePlugin` | Public env variables |
| `resolve.fallback` for `fs`, `path` | Remove the server import from client code. The fallback hid a bug |
| A plugin (bundle analyzer, error-tracker upload, module federation) | No plugin API in Turbopack. Use the built-in analyzer (`next experimental-analyze` when it shipped in 16.1; `next --help` shows the current name; a Rollup-style visualizer plugin in Vite) or the vendor's current integration; stay on `--webpack` only if neither exists |

A minimal Vite config is the whole setup:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { tsconfigPaths: true }, // aliases come from tsconfig "paths": one source of truth
})
```

## TypeScript configuration

Bundlers strip types without checking them. The type check is a separate step and CI must run it:
`tsc --noEmit`, preceded in Next.js by `next typegen` so the route types exist.

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "isolatedModules": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "noEmit": true,
    "incremental": true,
    "types": ["node"],
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts", ".next/dev/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- `moduleResolution: "bundler"` for anything a bundler builds. `"nodenext"` is for code Node runs
  directly with no bundler (scripts, a published library); it requires file extensions in
  relative imports.
- `noUncheckedIndexedAccess` makes `rows[0]` possibly `undefined`. Turn it on at the start;
  retrofitting it means hundreds of errors.
- TypeScript 6 changed defaults and 7 (the native compiler, about ten times faster) removed old
  options. `baseUrl` is gone: write `paths` targets relative to the tsconfig with a leading `./`.
  `moduleResolution: "node"` is gone. `types` defaults to an empty list, so globals such as
  `process` vanish until `"types": ["node"]` is added (for Vite, `"vite/client"`). Go through 6
  before 7 and fix deprecations there.
- The native compiler does not expose the JavaScript compiler API that earlier versions did.
  Before upgrading to 7, check every tool that imports the `typescript` package (the framework's
  build-time check, lint rules that use type information, code generators, doc tools).
- One alias, declared once in `paths`. Next.js reads it; Vite reads it with
  `resolve.tsconfigPaths`; Vitest inherits the Vite config. For code that Node also runs
  unbundled, use the `imports` field of `package.json` (`"#*": "./src/*"`), which Node, TypeScript
  and bundlers all resolve.
- In a monorepo, shared packages expose entry points through `exports`. A package consumed as
  TypeScript source is listed in `transpilePackages` in Next.js. Workspace layout:
  `0x:git-collaboration`.

Stricter flags, lint rules and type-level practice: `0x:code-quality`.

## Environment variables

| Fact | Consequence |
|---|---|
| A public prefix (`NEXT_PUBLIC_`, `VITE_`, `PUBLIC_`) puts the value in the JavaScript sent to every visitor | Only values that could go on a billboard get the prefix. A secret that was ever prefixed is leaked: rotate it |
| Public values are inlined as text at build time | Changing one means rebuilding. An image built once and promoted from staging to production carries staging's public values |
| Only the literal `process.env.NEXT_PUBLIC_X` is replaced | `process.env[name]` and `const { NEXT_PUBLIC_X } = process.env` are `undefined` in the browser |
| Unprefixed variables do not exist in client code | `undefined` there is correct behavior. The fix is to read on the server and pass the result, never to add the prefix |
| Server values read while prerendering or inside a cached function are frozen into the output | Runtime-varying config is read at request time (in Next.js after `await connection()` or another request API) |
| Next.js looks each variable up in the real environment, then `.env.[mode].local`, `.env.local`, `.env.[mode]`, `.env`, and stops at the first hit; `.env.local` is skipped under `NODE_ENV=test` | A variable that works on the laptop and not in CI is missing from the CI environment at build time, not at run time |

- Validate once at startup. A server-only `env.ts` parses `process.env` with Zod and exports a
  typed object, and a second small module does the same for the public values. A missing variable
  then fails the deploy with its name, instead of a request failing later.
- For one image across environments: keep public config out of the bundle. Read it on the
  server and render it into the page, or serve it from a small endpoint.
- Commit `.env.example` with names and dummy values, never `.env*.local`.

```bash
grep -rlE "sk_live|SECRET|PRIVATE KEY" .next/static dist/assets 2>/dev/null   # must print nothing
```

Storing and rotating secrets: `0x:web-security`. Config per environment: `0x:ci-cd-release`.

## Fonts, images, SVG and CSS

- **Fonts**: self-host through the build. `next/font` downloads at build time, serves from your
  origin, subsets, and generates a size-adjusted fallback so text does not shift when the font
  loads. Elsewhere, a variable `.woff2` from a Fontsource package or a local file, `font-display:
  swap`, and a preload for the one font used above the fold. A `<link>` to a font CDN adds a
  third-party connection to every first visit.
- **Images**: import local images so the bundler emits a hashed file and knows the dimensions.
  With `next/image`, set `sizes` whenever the image is not a fixed pixel width; allow remote
  hosts explicitly in `images.remotePatterns`; mark the one above-the-fold hero with `preload`
  (named `priority` before 16) or `fetchPriority="high"`. In Vite an import returns the URL, and
  resizing needs an image CDN or a build plugin. Format and loading strategy: `0x:web-performance`.
- **SVG**: three options with different costs. As a file (`<img>` or CSS): cacheable, not
  styleable. As a React component through SVGR: styleable with `currentColor`, but every icon is
  JavaScript that ships and hydrates, so reserve it for icons that change color or animate. As a
  sprite referenced with `<use href>`: best for dozens of icons. Import icon packages one icon at
  a time.
- **CSS**: Tailwind 4 is configured in CSS (`@import "tailwindcss"`, tokens in `@theme`) and
  wired by one plugin for the bundler (`@tailwindcss/vite`, `@tailwindcss/postcss`, or the loader
  the Next.js scaffold generated). Keep whichever the project already has. Import global CSS once
  from the root layout. Turbopack orders CSS Modules by import order, so two modules styling the
  same property need an explicit relationship, not luck. Lightning CSS handles prefixes and
  syntax lowering from the browser targets. Do not add autoprefixer on top.

## Build failures from module resolution

Method: reproduce from clean (`rm -rf node_modules .next dist && pnpm install --frozen-lockfile`).
Read the first error, not the last. Find the import chain that pulls the module in. Open the
failing package's `package.json` and read its `exports`, `type` and `main`.

| Message | Cause | Fix |
|---|---|---|
| `Module not found: Can't resolve 'fs'` (or `net`, `tls`, `child_process`) | A server-only package reached the client bundle | Follow the import trace to the client file; move the import behind the server boundary; mark the module `server-only` |
| `window is not defined`, `document is not defined` during build | A browser-only library runs at import time on the server | Import it inside an effect, or `next/dynamic` with `ssr: false` from a client component |
| `ERR_REQUIRE_ESM`, `require() of ES Module` | CommonJS code requiring an ESM-only package on a Node too old to allow it, or the package uses top-level await | Current Node LTS can `require()` synchronous ESM; otherwise `await import()` or make the caller ESM |
| `Cannot use import statement outside a module`, `Unexpected token 'export'` | A dependency ships ESM syntax without declaring it, and was loaded unbundled | Bundle it: `transpilePackages` (Next.js), `ssr.noExternal` (Vite), `server.deps.inline` (Vitest) |
| `Named export 'x' not found. The requested module is a CommonJS module` | ESM importing names from CommonJS that Node cannot detect statically | `import pkg from 'x'; const { x } = pkg` |
| `Cannot find module 'x' or its corresponding type declarations`, yet it runs | The package's `exports` has no usable `types` for this `moduleResolution` | Use `"bundler"`; diagnose with `npx @arethetypeswrong/cli --from-npm x` |
| `Invalid hook call`, a context that is `undefined`, `instanceof` that fails | Two copies of a package (React, a store, a UI kit) in the graph | `pnpm why react`; align versions; make the library a `peerDependency`; `pnpm dedupe`; `resolve.dedupe` in Vite |
| A native module fails to load in the container (`sharp`, database drivers, `bcrypt`) | Binary for another OS, CPU or libc; or the bundler tried to bundle it | Install inside the target image (glibc and musl differ); `serverExternalPackages` in Next.js; approve its install script |
| Passes in dev, fails in `build` | Type errors (dev does not block on them), a prerender reading request data, a variable missing at build time, or filename case (`./Button` and `button.tsx` match on macOS and not on Linux) | Read which phase failed; rename case with `git mv` |

## Browser targets and polyfills

Baseline is the shared vocabulary. "Newly available" means supported in the current version of
every major engine. "Widely available" means it has been so for 30 months. Target Baseline Widely
Available unless analytics say otherwise.

- Vite 8's default `build.target` is `'baseline-widely-available'`, pinned per Vite major (Chrome
  and Edge 111, Firefox 114, Safari 16.4 for Vite 8). Next.js 16 supports Chrome 111, Edge 111,
  Firefox 111, Safari 16.4 and newer. Leave the defaults.
- To state a target explicitly, put it in `package.json`, where Next.js, Lightning CSS and
  related tools read it: `"browserslist": ["baseline widely available"]`.
- Bundlers lower syntax. They do not add missing APIs. Whether an API such as a new `Intl`,
  `Array` or `Promise` method is safe is a Baseline lookup (MDN shows the status on each page),
  enforced by `eslint-plugin-compat` or a Baseline-aware lint rule so it is checked on every
  change.
- Polyfill one feature at a time, from your own bundle, for a measured audience. A blanket
  polyfill bundle taxes every modern browser. A third-party polyfill script is a supply-chain
  risk: the polyfill.io domain served malware in 2024.
- Lowering the target to be safe makes every visitor's bundle larger and slower. Look at the
  browser versions in product analytics first. In-app browsers on iOS use the system WebKit, so
  the OS version matters, not the app.
- New CSS that is not yet Baseline goes behind `@supports`, with a working fallback.

## Faster dev server and builds

Measure before changing anything: time a cold start, a hot update, and a production build.

- Stay current. Each minor of the bundlers brings real speedups, and Turbopack's on-disk cache
  makes restarts cheap. Keep `.next/` on a fast local disk.
- Import narrowly. Icon and utility packages re-exported through barrel files can pull thousands
  of modules into the graph. Import the icon's own path, avoid internal barrel `index.ts` files,
  and stick to one icon set.
- Run the dev server natively. Bind-mounting the project into Docker on macOS or Windows, or
  keeping it on the Windows filesystem under WSL, makes file watching and reads many times
  slower. Exclude the project folder from antivirus scanning.
- Tailwind 4 detects sources automatically. If it scans build output or a huge folder, exclude
  it with `@source not`.
- Type checking: `incremental` on, or the native TypeScript 7 compiler. Lint only changed files
  locally (lint-staged) and everything in CI.
- CI: restore `.next/cache` between runs, keyed on the lockfile hash plus a source hash with a
  lockfile-only fallback; cache the pnpm store; run type check, lint and tests as jobs parallel to
  the build, not in front of it. Pipeline design: `0x:ci-cd-release`.
- Prerendering thousands of pages at build is slow and usually pointless. Return the most
  visited from `generateStaticParams` and let the rest generate on first request.
- A build that runs out of memory: raise `NODE_OPTIONS=--max-old-space-size`, then find the cause
  (usually a giant dependency or generated file in the graph).
- The React Compiler adds build time. That is expected, not a regression to chase.

## Identical builds on every machine

- **Node**: one version in `.nvmrc` or `.node-version`, read by `actions/setup-node`
  (`node-version-file`) and matched by the Docker base image tag, plus an `engines.node` range in
  `package.json`. Use the current LTS line and avoid odd-numbered releases.
- **Package manager**: the `packageManager` field with an exact version. pnpm reads it and
  switches itself to that version, and `pnpm/action-setup` reads it in CI. Do not rely on
  Corepack: Node stopped bundling it in version 25.
- **Dependencies**: commit the lockfile. CI and Docker install with `pnpm install
  --frozen-lockfile`, which fails on drift instead of resolving new versions. `react`, `react-dom`
  and their type packages move together; `next` and `eslint-config-next` share a version.
- **Install scripts**: pnpm 10 and later run a dependency's install script only when the package
  is allow-listed in the workspace config (`pnpm approve-builds`). A native package that was not
  approved installs without its binary and fails at run time. pnpm can also hold back versions
  published within a set window (`minimumReleaseAge`), and recent majors may turn that on by
  default; when a just-published fix will not install, that setting is the cause.
- **Platform binaries**: Rolldown, Turbopack, Lightning CSS and sharp ship per-platform optional
  packages. Build inside the target image so the right ones install.
- **Upgrades**: one framework major at a time, on a branch with a preview deploy. Read the
  upgrade guide, run the official codemod (`npx @next/codemod@canary upgrade latest`), then fix
  what it reports. Security releases of the framework are the exception to batching: apply them
  the day they ship. Automated update pull requests, grouped by ecosystem: `0x:web-security`.

Check: the Node and pnpm versions printed at the top of the CI log equal `node -v` and `pnpm -v`
locally, and a fresh clone builds with the frozen-lockfile install and no other steps.

## Ask the user

- **Which browsers and devices do your customers really use?** It sets the target. Default:
  Baseline Widely Available; look at analytics before going lower.
- **Is one build promoted across environments, or built per environment?** It decides how public
  configuration is delivered. Default: build per environment on a PaaS; runtime config when a
  single Docker image is promoted.
- **May this value be visible to anyone who opens DevTools?** Every public-prefixed variable is.
  Default: no, keep it on the server, unless it is an ID designed to be public (analytics key,
  publishable payment key).
- **Is there a reason to stay on Webpack?** A plugin with no replacement is the only good one.
  Default: move to the framework's bundler.
- **When may framework upgrades happen?** Majors bring breaking changes and need a test pass.
  Default: security patches immediately, minors monthly, majors within a quarter of release.
