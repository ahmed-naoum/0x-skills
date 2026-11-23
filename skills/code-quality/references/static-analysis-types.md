# Static analysis, linting and types

Read this when: setting up or tightening type checking, linting, formatting, pre-commit hooks
or generated types; a class of bug keeps reaching tests or production that a tool could have
rejected; or module boundaries need enforcing.

## What each check is for

Assign each defect class to the earliest tool that can reject it, and do not duplicate.

| Tool | Catches | Runs |
|---|---|---|
| Type checker | Wrong shapes, null and undefined, missing cases, drift from generated schemas | Editor, CI (first job), optionally pre-push |
| Linter, type-aware rules | Floating promises, `any` leaks, unsafe patterns the compiler permits | Editor, pre-commit on staged files, CI |
| Formatter | Nothing; it removes style from review and diffs | On save, pre-commit, CI in check mode |
| Unused-code and cycle tools | Dead exports, unused dependencies, circular imports | CI |
| Import-boundary rules | Architecture violations | Lint, CI |

Enforcement lives in CI as required checks; editor integration and hooks only give faster
feedback. Pipeline wiring is in `0x:ci-cd-release`.

## Type checking as the first test

Run the type checker as its own CI step before any test: it is faster than the suite and a
type error makes test results meaningless.

```bash
pnpm exec tsc --noEmit        # single project
pnpm exec tsc -b              # project references (monorepo)
```

Traps:

- **The bundler does not type check.** Vite, esbuild, SWC and most test runners strip types
  and run. A project can build, pass tests and deploy with type errors unless `tsc` runs
  explicitly. Vitest does not type check test files either.
- **Tests and scripts must be inside a checked project.** If `tsconfig.json` excludes test
  files or `scripts/`, they rot silently. Either include them or give them their own tsconfig
  and check that too.
- **Framework builds may check or may be configured to skip.** A setting such as
  `typescript.ignoreBuildErrors` in the framework config turns a red build green; search for
  it and remove it. Do not rely on the build for type checking: run `tsc` separately so it
  fails fast and in parallel with other jobs.
- **`skipLibCheck: true`** is the normal setting (errors inside dependencies' declaration
  files are not actionable), but it also skips the project's own hand-written `.d.ts` files.
  Keep those few and simple.
- Generated types must exist before `tsc` runs (framework route types, ORM client, API
  types): generate in the same job, first.
- **A TypeScript major can outrun the tools that read types.** Type-aware lint rules, codemod
  libraries and some transformers call the compiler API; before moving to a new major (the
  native compiler line in particular), check each tool's supported `typescript` range.

Greenfield `tsconfig.json` beyond the framework's preset:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "noEmit": true
  }
}
```

`noUncheckedIndexedAccess` is not part of `strict` and is the most valuable addition: `arr[i]`
and `record[key]` become `T | undefined`, which is what they are at run time.
`exactOptionalPropertyTypes` distinguishes a missing property from one set to `undefined`; it
is correct but conflicts with some libraries' types, so drop it first if it costs more than a
few hours. Type-level technique is in `0x:frontend-foundations`.

## Lint and format: pick one setup and stop discussing

Formatting has no right answer, only a consistent one. Take the tool's defaults, change at
most line width, and never review style by hand again.

| Choice | Take it when |
|---|---|
| Biome (one binary: formatter and linter) | Greenfield, or lint time is hurting. Fast, one config file, almost nothing to maintain. Its type-aware rules (`noFloatingPromises`, `noMisusedPromises`) run on Biome's own type inference, not the TypeScript compiler, and have shipped as nursery rules that miss cases; check the current rule docs, and if they are not stable, add ESLint with only the type-aware rules in CI from Launch. Check framework plugin coverage too. Not on its own for React with the React Compiler: the compiler's lint rules exist only in `eslint-plugin-react-hooks` (`0x:react-nextjs`, `data-state.md`), so use one of the rows below |
| ESLint flat config with typescript-eslint, plus Prettier for formatting | The project needs the full type-aware rule set, framework or accessibility plugins, or custom rules. Slower, larger ecosystem |
| Biome for formatting and fast lint, ESLint for type-aware and plugin rules only | A large codebase that wants both; costs two configs |

Follow what the project already has. Migrating linters is rarely worth a day unless speed or
maintenance is a real complaint.

Rules for either:

- One config at the repository root; per-directory overrides only for real differences
  (tests, scripts, generated code).
- Ignore generated and vendored files in the tool's config, not with inline comments.
- Warnings are noise. Every rule is `error` or `off`; in CI run with zero warnings allowed
  (`eslint --max-warnings 0`) so a rule cannot sit ignored at `warn` for a year.
- Every inline disable names the rule and gives a reason
  (`// eslint-disable-next-line <rule> -- reason`); report unused disable directives as errors.
- With ESLint plus Prettier, do not run Prettier as an ESLint rule; run both tools and add
  `eslint-config-prettier` so formatting rules do not fight.
- Introduce the formatter to an existing codebase in one commit that touches nothing else,
  and list that commit in `.git-blame-ignore-revs`.
- CI runs check mode, never fix mode: `biome ci .`, or `prettier --check .` and `eslint .`.

## The rules that prevent real defects

Most lint rules are taste. These are the ones that correspond to production bugs; enable them
as errors from the start.

| Pattern | Why it bites | Rule (typescript-eslint unless noted) |
|---|---|---|
| A promise neither awaited nor handled | Errors vanish, work continues after the response, tests pass then flake, unhandled rejections crash the process | `no-floating-promises` |
| Async function passed where a sync callback is expected (`forEach`, event handlers, conditions) | Rejections unhandled; `if (asyncFn())` is always true | `no-misused-promises`, `await-thenable` |
| Explicit `any` | Switches the type checker off for everything the value touches | `no-explicit-any` |
| `any` arriving implicitly from `JSON.parse`, `response.json()`, untyped libraries | Same, with no visible keyword | `no-unsafe-assignment`, `no-unsafe-member-access`, `no-unsafe-call`, `no-unsafe-return`, `no-unsafe-argument` |
| Non-null assertion `!` and casts with `as` | An unverified claim to the compiler; fails at run time | `no-non-null-assertion`; allow `as const`; review other casts |
| Unchecked index and key access | `undefined` at run time typed as present | Compiler option `noUncheckedIndexedAccess` |
| Non-exhaustive `switch` over a union | A new status or plan falls through silently | `switch-exhaustiveness-check`, or a `never` assertion in `default` |
| `@ts-ignore` | Hides any future error on that line too | `ban-ts-comment`, allowing `@ts-expect-error` with a description |
| Throwing non-Error values | No stack trace | `only-throw-error` |

The promise and `no-unsafe-*` rules need type information, which is what makes ESLint slow;
that cost is worth paying in CI. Minimal flat config:

```js
// eslint.config.mjs
import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';

export default defineConfig(
  { ignores: ['dist/', '.next/', 'coverage/'] },
  js.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    linterOptions: { reportUnusedDisableDirectives: 'error' },
    rules: {
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
    },
  },
  // last: files in no tsconfig (this file, root scripts) would fail typed linting
  { files: ['**/*.{js,mjs,cjs}'], extends: [tseslint.configs.disableTypeChecked] },
);
```

Where `any` must enter (a parse result, a third-party payload), type it `unknown` and narrow
through a schema at the boundary; the `no-unsafe-*` rules then stay quiet because nothing
unsafe exists. A fire-and-forget promise that is intended is written `void doThing()` with an
error handler inside `doThing`, so the intent is visible.

## Pre-commit hooks that stay on

A hook that takes more than a few seconds gets bypassed with `--no-verify`, and then it
protects nothing. Budget: under about 3 seconds for a typical commit.

- Run only on staged files: format, then lint with autofix. Use lint-staged with a hook
  manager (husky or lefthook), or the linter's own staged mode.
- Do not run the type checker or the test suite in pre-commit. Both are whole-project
  operations and too slow. If a local gate is wanted, put `tsc --noEmit` and the changed-file
  tests on pre-push.
- Add a secret scanner on staged changes here: a leaked key is the one mistake that cannot be
  fixed after push (`0x:web-security`).
- Hooks must install themselves on `pnpm install` (a `prepare` script), or new clones and
  agent sessions run without them.
- CI repeats every hook check. Hooks are optional by design; CI is the gate.

## Tightening strictness in a legacy codebase

Turning on `strict` in an old codebase produces hundreds or thousands of errors. Fixing them
in one branch stalls; the working approaches all make the error count a ratchet that can only
go down.

| Approach | How | Use when |
|---|---|---|
| Flag by flag | Enable one strict-family flag, fix, merge, next. Easy ones first (`noImplicitThis`, `alwaysStrict`, `strictBindCallApply`), then `noImplicitAny`, and `strictNullChecks` last because it is the largest | Few hundred errors per flag |
| Strict for a growing set of files | A second `tsconfig.strict.json` extending the base with `strict: true` and an `include` list; CI checks both; every new file and every touched file joins the list. Trap: `tsc` also checks every file the listed ones import, so add leaf modules first, or filter the reported errors to the listed paths with a script or a plugin built for per-file strictness | Thousands of errors; want strict on all new code today |
| Suppress and burn down | Enable the flag, insert `@ts-expect-error` with a tracking tag on each existing error by script, and remove them over time. Unlike `@ts-ignore`, an expect-error fails when the error is gone, so fixed lines cannot keep a stale suppression | Want one config; accept noisy files for a while |

Rules for all three: new code is strict from day one; never loosen a flag once on; track the
count (suppressions, or files outside the strict list) and fail CI if it rises; fix by
directory, starting with money, auth and data access, where a null error costs most. The
same ratchet works for new lint rules: record existing violations in a baseline and block
only new ones (ESLint 9.24 and later: `eslint --suppress-all` writes
`eslint-suppressions.json`, and `--prune-suppressions` drops entries once they are fixed).

During `strictNullChecks` cleanup, resist `!` and `as`: each one converts a compile error
into a possible run-time one. Narrow, default, or change the type so the absent case is
handled. For a JavaScript codebase, set `allowJs` and `checkJs`, rename files to `.ts` leaf
modules first, and type the module boundaries before the insides.

## Dead exports, unused dependencies, circular imports

- **Unused files, exports and dependencies:** Knip (`pnpm dlx knip`) builds the import graph
  from entry points and reports files nothing imports, exports nothing uses, dependencies not
  referenced, and referenced packages missing from `package.json`. Configure entry points for
  anything it cannot infer (scripts, config files, dynamically imported modules) until the
  report is clean, then run it in CI so it stays clean.
- **False positives** come from dynamic references: string-built imports, framework file
  conventions it does not know, names used only from templates or the database. Add those as
  entries or ignores with a comment; do not delete on the tool's word alone for anything
  reachable from outside the repository.
- **Circular imports:** `pnpm dlx madge --circular --extensions ts,tsx src`, or
  dependency-cruiser, or a lint rule such as `import/no-cycle` (accurate but slow; run it in
  CI only). Symptoms of a cycle at run time: an import that is `undefined` at module
  evaluation, "cannot access before initialization" errors, behavior that depends on import
  order, a test that passes alone and fails in the suite. Fix by moving the shared piece to a
  third module that both import, or by inverting one dependency; type-only cycles are
  harmless when written as `import type`.
- **Barrel files** (`index.ts` re-exporting a directory) create most accidental cycles and
  slow tests and builds by pulling in whole directories. Keep a barrel only as the public
  entry of a package or feature module; import concrete files inside it.

## Generated types: make drift a build failure

Hand-written types that mirror a database or an API drift, and the compiler then vouches for
a shape that no longer exists. Each external shape gets one source of truth, and every other
representation is derived from it by a tool.

| Shape | Source of truth | Derived |
|---|---|---|
| Database tables (schema-in-code ORM such as Drizzle) | The schema file | Row types inferred (`typeof users.$inferSelect`); migrations generated from the schema |
| Database tables (migrations-first or external database) | The migrated database | Types generated by introspection, committed or generated in CI |
| Own HTTP API | The route's validation schema (Zod) or the OpenAPI document | Client types (`z.infer`, or `openapi-typescript`), docs |
| Third-party API | The vendor's OpenAPI document or official SDK types | Client types; never hand-typed response interfaces |
| GraphQL | The schema | Typed operations by codegen |
| Environment variables | One schema parsed at startup | `env` object type; a missing variable fails at boot, not at first use |

The enforcement step, in CI, is the same for all: regenerate and fail if anything changed (a
generator that stops at a prompt, such as a rename question, counts as changed).

```bash
pnpm exec openapi-typescript ./openapi.yaml -o ./src/api/schema.d.ts
pnpm exec drizzle-kit generate          # must produce no new migration
test -z "$(git status --porcelain)" || { git status --short; exit 1; }
```

Decide per artifact whether to commit generated output. Commit it when reviewers benefit from
seeing the diff (API types, migrations); generate it at install or build when it is large or
environment-specific (ORM clients). Either way the generation command is one script, run by
`postinstall` or the build, and generated files are excluded from lint and format.

A generated type describes what was promised, not what arrived. Keep run-time validation at
trust boundaries: external responses, webhooks, form input, anything read from JSON columns.

## Architecture boundaries as import rules

Layering that exists only in a diagram erodes one convenient import at a time. Encode the few
rules that matter as lint errors; skip this at Prototype, add it at Launch when the module
structure has settled.

Rules worth enforcing in a typical web product:

- Client components and shared UI do not import database, secrets or server-only modules.
- Feature modules import each other only through the public entry file, never deep paths.
- Domain logic does not import the web framework or the ORM's query builder (keeps it
  testable without them).
- Nothing outside one module imports a vendor SDK directly (one wrapper per third party).

```js
// in eslint.config.mjs, as one more config object
{
  files: ['src/components/**', 'src/app/**/*.client.tsx'],
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [{ group: ['@/db/*', '@/server/*'], message: 'UI must not import server code.' }],
    }],
  },
}
```

Options beyond the built-in rule: eslint-plugin-boundaries (declare element types and allowed
directions), dependency-cruiser (rules over the whole graph, also draws it), and in a
monorepo, package boundaries with an `exports` map so deep imports fail to resolve
(`0x:git-collaboration`). In Next.js, `import 'server-only'` at the top of a module makes the
build fail when a client component imports it.

Traps: start with two or three rules that reflect how the code is already organized, since a
rule set describing an aspirational architecture fails on day one and gets disabled; adopt
with a baseline of existing violations and block new ones; path aliases must resolve
identically in the linter, the compiler and the test runner or rules silently match nothing;
a later config object's `no-restricted-imports` replaces an earlier one for the same file, it
does not merge. Prove each rule by writing a violating import once and seeing the error.

## Ask the user

- **Is there an existing style or lint setup the team is attached to?** Changing it costs
  churn in every open branch. Assume keep what exists; on greenfield take tool defaults.
- **How much time can go to strictness cleanup in an old codebase?** Decides flag-by-flag
  versus strict-for-new-files. Assume none up front: strict for new and touched files, ratchet
  in CI.
- **Should a failing lint or type check block merging and deploys, with no override?** It
  must for the checks to mean anything; the cost is an occasional blocked hotfix. Assume yes,
  with rollback as the emergency path instead of bypass.
- **Who else consumes the API or database schema (mobile app, partners, analytics)?** Decides
  where generated types and drift checks are needed. Assume only this repository.
