# Monorepos and shared code

Read this when: deciding whether apps and packages live in one repository or several, setting up pnpm workspaces and Turborepo, extracting shared code into an internal package, making CI build only what changed, publishing packages from a monorepo, or splitting or merging repositories without losing history.

## One repository or many

Default for a solo founder or small team: one repository for everything that ships together or shares code (web app, API, workers, marketing site, shared packages, infrastructure code).

The decisive benefit is the atomic change: a schema, its API handler, its client and its types change in one pull request, reviewed and reverted as a unit. Separate repositories turn that into coordinated releases across version boundaries, which is process overhead a small team cannot afford.

| Signal | Lean |
|---|---|
| Code is shared (types, UI, validation schemas, config) | One repository |
| Changes routinely touch more than one of the projects | One repository |
| Same people work on all of it | One repository |
| A part is open source while the rest is private | Separate repository for the public part |
| Contractors or partners must see only one part | Separate: repository hosts grant read access per repository, not per folder |
| Different language and toolchain, no shared code, different team, different release cadence (a native mobile app, an ML training codebase) | Separate is fine; nothing is gained by joining |
| A customer or compliance scope requires isolated access and audit | Separate |
| Repository is slow to clone or CI takes too long | Fix with caching, affected-only runs and sparse checkout before splitting |

A monorepo is a repository layout, not an architecture. One repository can hold several independently deployed apps, and a single modular app is not a monorepo problem. Do not introduce workspaces for a project with one app and no second consumer of any code; a `src/lib` folder is enough until then.

Avoid git submodules as the way to share code between repositories. They pin a commit that must be bumped by hand, every clone and CI job needs extra steps, and changes spanning both sides need two pull requests in the right order. If code must live elsewhere, publish it as a versioned package.

## pnpm workspaces and Turborepo

Layout:

```text
apps/web            apps/api            apps/worker
packages/ui         packages/db         packages/config-typescript
pnpm-workspace.yaml turbo.json          package.json (private, root scripts only)
```

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

```json
{ "dependencies": { "@acme/ui": "workspace:*" } }
```

- `workspace:*` links the local package and fails loudly if it is missing, instead of silently installing a same-named package from the registry.
- One lockfile at the root, committed. CI installs with `pnpm install --frozen-lockfile`.
- Run things through filters: `pnpm --filter web dev`, `pnpm --filter @acme/db add drizzle-orm`. Add dependencies to the package that imports them, not to the root; the root holds only repository tooling (turbo, the formatter).
- pnpm's strict `node_modules` means a package can import only what it declares. An import that works in one package and fails in another is an undeclared dependency, and the fix is to declare it, not to hoist.
- Keep one version of each external dependency across the workspace, especially React, TypeScript and the ORM; two copies of React produce runtime errors that look unrelated. pnpm catalogs (a version defined once in `pnpm-workspace.yaml` and referenced as `catalog:`) are the low-effort way to enforce this.
- Pin the package manager with the `packageManager` field in the root `package.json` so every machine and CI use the same pnpm.

Turborepo adds a task graph and a cache on top of the workspace:

```json
{
  "$schema": "./node_modules/turbo/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "!.next/cache/**", "dist/**"] },
    "typecheck": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["^build"] },
    "transit": { "dependsOn": ["^transit"] },
    "lint": { "dependsOn": ["transit"] },
    "dev": { "cache": false, "persistent": true }
  }
}
```

- The schema shipped inside the installed `turbo` package always matches its version. The hosted schema URL has moved between domains across releases; copy it from the current documentation if a URL is preferred.
- `^build` means "build my dependencies first". Without the caret it means the same package's own task.
- A task's cache key is a hash of its inputs: the package's source-controlled files, its `package.json` and the lockfile entries that affect it, the task configuration, the environment variables declared for it, and the hashes of the tasks it depends on. A cache hit replays the logs and restores the declared `outputs`.
- A change in an internal package reaches a consumer's cache key only through `dependsOn`. A task declared as `{}` keeps its cache hit when `@acme/ui` changes, which is wrong for typecheck and type-aware lint. `^build` fixes it but serializes the work; the `transit` task above matches no script, does nothing, and exists only to chain the hashes so `lint` stays parallel and still sees dependency changes.
- The two cache bugs that matter are both configuration omissions. An environment variable that affects the output but is not declared (`env` on the task, `globalEnv` for all) yields a cache hit carrying the value from another environment, such as a staging API URL baked into a production bundle.
- An output directory missing from `outputs` yields a "successful" cached build that restores nothing. After changing `turbo.json`, verify with a clean checkout: run twice, confirm the second run is a full cache hit and the artifacts exist.
- Never cache `dev` or any task with side effects (deploys, migrations): `"cache": false`.
- Remote caching shares the cache between CI and laptops and is the main reason to adopt Turborepo. Locally: `turbo login` and `turbo link`. In CI: set `TURBO_TOKEN` and `TURBO_TEAM` as secrets.
- The cache holds build output, so treat the token as a secret, and do not give write access to untrusted contributors' builds (fork pull requests), since a poisoned artifact would be restored into trusted builds. Enable artifact signing if the cache is shared beyond the team (`remoteCache.signature` in `turbo.json` plus a secret signing key supplied through the environment; unsigned or tampered artifacts are then treated as cache misses).
- Skip Turborepo while the workspace has one app and two packages and CI takes a couple of minutes; `pnpm -r run build` in dependency order is enough. Add it when CI time or repeated rebuilding hurts. Nx is the comparable alternative with more structure and code generation; keep whichever the project already has.

## Internal packages and boundaries

Extract a package when a second consumer exists or a boundary must be enforced (database access only through `@acme/db`). Extracting on speculation creates an abstraction with one caller and a build step.

| Style | How | Use when |
|---|---|---|
| Just-in-time (default) | `exports` points at TypeScript source; the consuming app's bundler compiles it (Next.js needs the package listed in `transpilePackages`) | Consumers are all apps in this repository with a bundler. No build step, instant edits |
| Compiled | The package builds to `dist/` with `tsc` or a bundler; `exports` points at the output | A consumer runs it without a bundler (a plain Node script), or build caching per package is wanted |
| Publishable | Compiled, versioned, published to a registry | Someone outside the repository installs it |

```json
{
  "name": "@acme/ui",
  "private": true,
  "type": "module",
  "exports": {
    ".": "./src/index.ts",
    "./button": "./src/button.tsx"
  }
}
```

Boundary rules:

- The `exports` map is the public API. Consumers import `@acme/ui/button`, never `@acme/ui/src/internal/x` and never a relative path that climbs out of their own package (`../../packages/ui/...`), which bypasses the dependency declaration and breaks caching.
- Dependencies point one way: apps depend on packages; packages depend on lower-level packages; nothing depends on an app; no cycles. A cycle between two packages means they are one package or a third is missing.
- Name packages by what they are (`db`, `ui`, `email`, `auth`), not `shared`, `common` or `utils`. A dumping-ground package ends up imported by everything and importing everything, which defeats affected-only builds because every change touches it.
- Keep server-only code (database client, secrets) out of packages imported by client bundles; split entry points (`@acme/auth/server`, `@acme/auth/client`) so the wrong import fails at build time.
- A barrel file re-exporting everything from one entry point makes bundlers and typecheckers load the whole package for one import; prefer several narrow entry points for large packages.
- Share configuration as packages too: a base `tsconfig`, the lint config. One place to change a rule.
- Enforce at Scale, when more people can violate the rules by accident: a lint rule on import paths or a dependency-graph checker in CI. Earlier, the `exports` map plus pnpm strictness catches most violations.
- Mark every internal package `"private": true` so it cannot be published by accident.

## Build and test only what changed

Three layers, cheapest first:

1. **Task cache.** With remote caching, unchanged packages are cache hits and cost seconds. For many small monorepos this alone is enough, and it is always correct because it is derived from content hashes.
2. **Affected filter.** Skip even the cache lookup and setup for unrelated work:
   ```bash
   turbo run lint typecheck test --affected
   turbo run test --filter='...[origin/main]'   # packages changed since origin/main, plus their dependents
   ```
   Both compare against a git ref, so CI needs that history. A default shallow checkout has one commit and no base to compare; fetch enough history (in GitHub Actions, `fetch-depth: 0` on the checkout step, or fetch the base ref explicitly). The symptom of getting this wrong is either "everything is affected" or an error about an unknown revision.
3. **Skipping deploys.** Each app deploys only when it or one of its dependencies changed. Use the platform's ignored-build setting or a graph-aware check for this; a hand-written list of path globs misses the shared package the app depends on.

Traps:

- Changes to root files (lockfile, base `tsconfig`, `turbo.json`, CI config) affect everything, and should. Do not try to exclude the lockfile from hashing to save time.
- Path filters on CI workflows combined with required status checks: a workflow that does not run never reports, and the required check stays pending forever. Run the workflow always and let the task runner decide what to skip, or use a single always-running summary job as the required check (`0x:ci-cd-release`).
- "Affected" covers code dependencies only. A database migration, an environment variable or an API contract consumed over HTTP by another app is not in the graph. End-to-end tests for the deployed whole should run on every change to `main` regardless of the filter.
- Run the full, unfiltered suite on `main` on a schedule (nightly) as a backstop against cache or graph misconfiguration.

## Versioning and publishing from a monorepo

Most packages in a product monorepo are private and need no version at all: they ship inside the apps that bundle them. Leave them at `0.0.0` and do not write changelogs for them.

Versioning starts when a package is published for outside consumers (an SDK, a CLI, a component library). Default tool: Changesets.

```bash
pnpm changeset            # contributor records: which packages, bump type, summary
pnpm changeset version    # release step: bumps versions, updates dependents, writes CHANGELOG.md files
pnpm changeset publish    # publishes packages whose version is not yet on the registry, tags them
```

- The changeset file is written in the pull request by the person who knows whether the change is breaking, and reviewed with the code. That beats inferring it from commit messages when one commit touches several packages.
- `changeset publish` creates the tags locally. Push them (`git push --follow-tags`) unless the release action does it.
- In CI, the usual flow is a bot-maintained "version packages" pull request that accumulates changesets; merging it publishes. Publishing credentials and provenance are covered in `0x:ci-cd-release`.
- Independent versions (each package has its own number) are the default and suit unrelated packages. Fixed or linked versions (a group shares one number) suit a family that users install together and expect to match.
- pnpm rewrites `workspace:*` to the real version range in the published manifest. Publishing with a tool that does not understand the workspace protocol ships a broken `package.json`; publish through pnpm or Changesets.
- A published package cannot depend on a private internal package: the consumer cannot install it. Either publish the dependency too or bundle it into the published output.
- Test what will be published, not the workspace link: `pnpm pack` the package and install the tarball in a scratch project. Missing `files` entries and wrong `exports` paths only show up there.
- Tag format in a monorepo is per package (`@acme/sdk@1.4.0`), so tooling that expects a single `v1.4.0` tag for the repository needs configuring.

Semver rules and changelog writing are in `versioning-releases.md`.

## Splitting and merging repositories with history

Use `git filter-repo` (installed separately from git) in a fresh clone for both directions; it rewrites history, so never run it in a working clone with unpushed work.

Merging repository B into monorepo A under `apps/b`:

```bash
git clone <url-of-B> b-import && cd b-import
git filter-repo --to-subdirectory-filter apps/b --tag-rename '':'b-'
cd ../A
git remote add b-import ../b-import && git fetch b-import --tags
git merge --allow-unrelated-histories b-import/main
git remote remove b-import
```

Rewriting B's paths first means `git log` and `git blame` on `apps/b/...` work normally afterward. The simpler `git subtree add --prefix=apps/b <url> main` also keeps the commits, but with their original paths, so file history across the import boundary needs extra effort to follow. Rename tags on the way in, or B's `v1.0.0` collides with A's.

Splitting `packages/sdk` out of a monorepo:

```bash
git clone <url-of-A> sdk && cd sdk
git filter-repo --subdirectory-filter packages/sdk
git remote add origin <url-of-new-repo> && git push -u origin main --tags
```

Then, in the monorepo, delete the directory in a normal commit and depend on the published package. Do not rewrite the monorepo's history to remove the old copy unless the content must be gone.

What does not move in either direction: issues, pull requests and their numbers (commit messages saying `#123` now point at the wrong thing or nothing), CI configuration and secrets, branch rules, webhooks and deploy integrations.

Sequence the move: freeze merges in the source, migrate, set up CI and protections in the destination, verify a build and deploy from the new location, then archive the old repository read-only with a pointer in its README rather than deleting it.

## Ask the user

- **Does anyone outside the core team need access to only part of the code?** Access is per repository, so this forces a split. Default: no, keep one repository.
- **Will any package be installed by people outside this repository?** Decides whether versioning and publishing machinery is needed. Default: no; all packages private and unversioned.
- **Is a hosted remote cache acceptable, given that build output leaves the company's machines and the vendor may charge?** Default: use the task runner vendor's hosted cache; self-host only on a stated requirement.
- **Is the mobile app, data science code or other different-toolchain project changed together with the web product?** Default when unknown: keep it separate until a concrete shared-code need appears.
- **During a repository merge or split, can merges be frozen for a few hours?** Default: yes, schedule a freeze; migrating while changes keep landing means doing it twice.
