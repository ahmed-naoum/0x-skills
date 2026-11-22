# JavaScript and TypeScript

Read this when: the problem is in the language rather than the framework: async code runs in the
wrong order or races, TypeScript rejects (or wrongly accepts) something, a module will not import,
errors and timeouts are unhandled, or memory grows.

## Async ordering: the model

One loop per thread: run one **task** (a timer, an event, a network callback) to completion → run
**all** queued microtasks (promise reactions, `queueMicrotask`, the continuation after each
`await`) until the queue is empty → the browser may render → next task. Consequences:

- Code after `await` never runs synchronously, even if the awaited value is already resolved.
  Anything can have changed by the time it resumes.
- Promise callbacks run before any `setTimeout(..., 0)` queued earlier in the same task.
- A long chain of microtasks blocks rendering and input exactly like a synchronous loop. To let
  the page paint, yield to a new *task* (`await new Promise(r => setTimeout(r))`, or
  `scheduler.yield()` where available).
- In Node, `process.nextTick` callbacks run before promise microtasks, and `setImmediate` runs
  after I/O callbacks; do not use `nextTick` for ordinary deferral.

| Bug | Why | Fix |
|---|---|---|
| Search results or a detail panel show an older response | Two requests in flight; the slower, earlier one resolves last | Abort the previous request when starting a new one (below), or keep a request counter and ignore stale results |
| Check-then-act goes wrong (`if (!cache[k]) cache[k] = await load(k)` loads twice) | State read before `await`, written after | Store the *promise* synchronously: `cache[k] ??= load(k)` |
| `array.forEach(async ...)` finishes "before" its work | `forEach` ignores returned promises | `for...of` with `await` for sequential; `await Promise.all(items.map(...))` for parallel |
| Slow page of independent calls | `await` in a loop runs them one after another | `Promise.all`, with a concurrency limit when the list is unbounded |
| Unhandled rejection crashes Node | A promise was created, then another `await` came first; it rejected with no handler attached | Start them together and `await Promise.all([a, b])`; never leave a promise unawaited without `.catch` |
| State update after unmount, or on the wrong record | Continuation resumes after the user navigated | Abort on cleanup; re-check identity after every `await` |
| Double-click runs the handler twice | Second click arrives while the first is awaiting | Guard with an in-flight flag set synchronously, plus server idempotency |

Combinators: `Promise.all` fails fast (the others keep running; abort them), `allSettled` when
every outcome matters, `race` for first to settle, `any` for first success.

## Strict TypeScript from the first commit

Turning strictness on later means fixing hundreds of errors at once; starting strict is free.

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "target": "es2022",
    "module": "preserve",
    "moduleResolution": "bundler",
    "noEmit": true
  },
  "include": ["src", "scripts", "*.config.ts"]
}
```

- `noUncheckedIndexedAccess` makes `arr[i]` and `record[key]` include `undefined`, which is the
  truth; it catches the most common runtime error strictness otherwise misses.
- `module: "preserve"` with `moduleResolution: "bundler"` is for code a bundler or framework
  builds. For code Node runs directly, or a published library, use `"module": "nodenext"`.
  A framework's generated tsconfig already sets these; add the strict flags to it rather than
  replacing it.
- `exactOptionalPropertyTypes` is worth adding to new codebases; it sometimes conflicts with
  library types, so drop it if it costs more than it finds.
- Config files, build scripts, seed scripts and tests are code: keep them `.ts` and inside
  `include` (or a second `tsconfig` that covers them). Run scripts with a TypeScript runner (`tsx`)
  or Node's built-in type stripping where the installed Node supports it; stripping only erases
  types, so `enum`, `namespace` and constructor parameter properties fail there (the
  `erasableSyntaxOnly` compiler option rejects them up front). Prefer `as const` objects to `enum`.
- Bundlers and runners strip types without checking them. The only type check is `tsc --noEmit`;
  it must run in CI (`0x:code-quality` owns that policy).
- Compiler defaults change between TypeScript majors: 6.0 turned `strict` on and stopped loading
  every `@types` package automatically (Node globals now need `"types": ["node"]`). State options
  explicitly and read the release notes before bumping the major.
- Never fix an error with `// @ts-ignore`. If suppression is truly needed use
  `// @ts-expect-error` with a reason: it fails when the error disappears.

## Model state so invalid states cannot compile

Several optional fields and booleans (`isLoading`, `error?`, `data?`) allow combinations that
must never exist, and every consumer has to guess. A discriminated union lists only the legal
ones:

```ts
type Remote<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function view(r: Remote<User>): string {
  switch (r.status) {
    case 'idle':
    case 'loading': return 'Loading';
    case 'success': return r.data.name;      // data exists only here
    case 'error':   return r.error.message;
    default: { const unreachable: never = r; throw new Error(`Unhandled: ${unreachable}`); }
  }
}
```

- The `never` default is the payoff: adding a variant becomes a compile error at every `switch`.
- Use the same shape for expected failures instead of exceptions:
  `type Result<T, E> = { ok: true; value: T } | { ok: false; error: E }`. Throw for bugs and the
  unexpected; return for outcomes the caller must handle (validation, not found, declined).
- Signals that a union is needed: two booleans that are never both true; a field that is "only
  set when"; a `type` string compared in several places; comments explaining valid combinations.
- Distinguish ids with brands when mixing them up is costly:
  `type UserId = string & { readonly __brand: 'UserId' }`, created only in the parsing layer.
- `satisfies` checks a value against a type while keeping its precise inferred type:
  `const routes = { home: '/', user: '/u' } as const satisfies Record<string, string>`.

## Unknown data at the boundary

Types describe what the code assumes; they verify nothing at runtime. Every value that crosses
into the program is `unknown` until parsed: `JSON.parse`, `response.json()`, `localStorage`,
`process.env`, URL and form parameters, `postMessage`, webhooks, file contents, database JSON
columns, and the `e` in `catch (e)`.

```ts
// Zod 4; on Zod 3 the email check is z.string().email(). Follow the installed major.
const User = z.object({ id: z.string(), email: z.email(), plan: z.enum(['free', 'pro']) });
type User = z.infer<typeof User>;               // the type comes from the schema, not the reverse

const parsed = User.safeParse(await res.json());
if (!parsed.success) throw new Error('Unexpected /me response', { cause: parsed.error });
const user = parsed.data;                        // typed and verified
```

- Parse once at the edge, then pass typed values inward. Interior functions do not re-validate.
- `as T` and `!` are assertions the compiler does not check; each one is a place a runtime error
  can originate with a wrong stack trace. Acceptable uses: `as const`; immediately after a
  runtime check the compiler cannot follow, with a comment; test fixtures.
- `any` is contagious: it silently disables checking for everything it touches. `JSON.parse` and
  `res.json()` return `any`; assign them to `unknown` first. Lint against explicit `any`.
- A user-defined type guard (`x is User`) is also an unchecked claim: if its body is wrong the
  compiler believes it anyway. Keep guards trivial or generate them from the schema.
- `catch (e)`: narrow with `e instanceof Error` before reading `.message`; anything can be thrown.
- Environment variables: parse them through one schema at startup and export the typed object, so
  a missing variable fails the boot instead of a request.

## Errors, cancellation and timeouts

```ts
async function getJson(url: string, signal?: AbortSignal): Promise<unknown> {
  const timeout = AbortSignal.timeout(8_000);
  const res = await fetch(url, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout });
  if (!res.ok) throw new Error(`GET ${url} failed with ${res.status}`);
  return res.json();
}
```

- `fetch` rejects only on network failure; a 404 or 500 resolves. Check `res.ok` every time.
- Every network call has a timeout. Without one, a stalled connection leaves the UI pending
  forever. `AbortSignal.timeout()` rejects with a `TimeoutError`; a manual `controller.abort()`
  rejects with `AbortError`. Tell them apart by `err.name`: an abort caused by navigation or a
  newer request is not an error and should not be shown or reported; a timeout is.
- Thread one `signal` parameter through every async layer (component → hook → API client →
  `fetch`), the way a context is threaded elsewhere. Cancellation that stops at one layer leaves
  the work running.
- Latest-wins pattern: keep the previous `AbortController`, call `abort()` before starting the
  next request. In a React effect, abort in the cleanup function.
- For a custom long-running function, call `signal.throwIfAborted()` between steps and listen
  for the `abort` event to release resources.
- `Promise.race` against a timer does not cancel the loser; it keeps running and holding its
  connection. Use the signal.
- Wrap, do not swallow: `throw new Error('Could not load invoice', { cause: err })` keeps the
  original for the error tracker. An empty `catch` is a bug report that will never arrive.
- Reset pending state in `finally`, so a thrown error cannot leave a spinner on screen.
- Retry only idempotent operations, with backoff and a cap; policy details are in
  `0x:backend-architecture` (`integrations-resilience.md`).
- Register a last-resort handler (`unhandledrejection` and `error` in the browser,
  `process.on('unhandledRejection')` in Node) that reports to the error tracker.

## Generics and utility types, readable

Rules that keep type-level code maintainable in an application:

- A type parameter should relate two things (an argument to the return type, or two arguments).
  One that appears once is a disguised cast: `function get<T>(key: string): T` lets the caller
  assert any type. Return `unknown` and parse instead.
- Let inference work. If call sites need explicit `<...>` arguments, the signature is wrong.
  Constrain with `extends` so inference has something to hold on to, and use `NoInfer<T>` to stop
  a parameter from widening the inferred type.
- Derive types from one source of truth rather than restating them: `z.infer<typeof Schema>`,
  `typeof config`, `keyof typeof map`, `(typeof ROLES)[number]`, `ReturnType<typeof fn>`,
  `Awaited<ReturnType<typeof load>>`, `Parameters<typeof fn>[0]`.
- Everyday utilities: `Pick`, `Omit`, `Partial`, `Required`, `Readonly`, `Record`, `Extract`,
  `Exclude`, `NonNullable`. Trap: `Omit` and `Pick` on a union collapse it to the shared keys and
  lose the discrimination; apply them per member with a distributive helper
  (`type DOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never`).
- Annotate exported function return types and public interfaces; let locals infer. Explicit
  boundaries make errors appear at the definition instead of fifty call sites.
- Stop rule: when a type needs recursion, more than one `infer`, or a template-literal parser,
  and it is not library code, write two overloads or duplicate a few lines instead. The test is
  whether the hover tooltip at the call site is something a person can read.

## Modules: ESM, `exports` and CommonJS interop

- New packages and apps: `"type": "module"` in `package.json`, ESM syntax everywhere.
- Node's ESM resolver requires full relative specifiers (`./util.js`, including the extension and
  `/index.js`). Bundler resolution does not, which is why code works in the app and fails in a
  script.
- `__dirname` and `__filename` do not exist in ESM; use `import.meta.dirname` and
  `import.meta.filename`, or `new URL('./file', import.meta.url)`.
- Importing CommonJS from ESM: the default import is the whole `module.exports`. Named imports
  work only when Node can detect the export names statically; when it cannot,
  `import pkg from 'pkg'; const { thing } = pkg;`.
- Importing ESM from CommonJS: `await import()` always works; synchronous `require()` of an ESM
  module works on current Node LTS only when that module graph has no top-level `await`.
- `verbatimModuleSyntax` forces `import type { T }` for types, so the emitted import list is
  exactly what was written. Type-only imports also break accidental circular dependencies.
- Circular imports surface as `undefined` or "Cannot access before initialization" at startup.
  Move the shared piece into a third module.
- Publishing a library: ESM-only unless consumers demand otherwise; a dual build can load twice
  and produce two copies of its state. Describe entry points with `exports`, with the `types`
  condition first and `default` last, since conditions match in order:

```json
{
  "type": "module",
  "exports": { ".": { "types": "./dist/index.d.ts", "default": "./dist/index.js" } },
  "files": ["dist"],
  "sideEffects": false
}
```

  Once `exports` exists, any path not listed is unreachable for consumers. Check the packed
  result with `npx publint` and `npx @arethetypeswrong/cli --pack` before publishing.
- Import JSON with an attribute: `import data from './data.json' with { type: 'json' }`.
- Barrel files (`index.ts` re-exporting a directory) slow dev servers and can defeat tree shaking;
  import from the defining module in application code. Bundle effects: `0x:web-performance`.

## Built-ins before libraries

Check Baseline status for the target (see `html-semantics.md`), then prefer the platform: no
bundle weight, no upgrades, no supply-chain exposure.

| Need | Built-in | Notes |
|---|---|---|
| Deep copy | `structuredClone(value)` | Handles `Date`, `Map`, `Set`, cycles; throws on functions and DOM nodes; drops class prototypes |
| Format dates, numbers, money, lists, relative time | `Intl.*` | See `internationalization.md` |
| Unique id | `crypto.randomUUID()` | Secure contexts only (HTTPS or localhost) |
| Group, last item, non-mutating sort | `Object.groupBy`, `arr.at(-1)`, `toSorted`, `toReversed`, `with` | |
| Lazy pipelines over iterators | Iterator helpers: `map.values().filter(f).take(10).toArray()` | No intermediate arrays |
| Set algebra | `a.union(b)`, `intersection`, `difference`, `isSubsetOf` | |
| Deferred promise | `Promise.withResolvers()` | |
| URLs and queries | `URL`, `URLSearchParams`, `URL.canParse()` | Never build query strings by concatenation |
| Text segmentation, grapheme-safe truncation | `Intl.Segmenter` | |
| Date and time arithmetic, time zones | `Temporal`, once it is Baseline for the target | Until then: keep instants as ISO strings or epoch milliseconds, format with `Intl`, and use a small date library or a Temporal polyfill for arithmetic. Avoid `Date` math across DST |

Still worth a dependency: schema validation, deep equality, complex date math before Temporal,
and anything security-sensitive (sanitizing HTML, parsing untrusted formats).

## Memory leaks

A leak is something still reachable that should not be. The usual holders:

| Holder | Fix |
|---|---|
| Listeners on `window`, `document` or a long-lived emitter, added per component or per request | `addEventListener(type, fn, { signal })` with one `AbortController` per lifetime; `abort()` on teardown removes them all |
| `setInterval`, recurring timers, animation loops | Clear on teardown; pause when `document.hidden` |
| Observers and subscriptions (`ResizeObserver`, sockets, store subscriptions) | `disconnect()` / unsubscribe in cleanup |
| Module-level `Map` or array used as a cache | Bound it (LRU, TTL), or key by object in a `WeakMap` |
| Detached DOM: removed nodes still referenced from a variable, closure or array | Drop the reference when removing the node |
| Closures capturing a large object for a small need | Copy out the field needed before creating the closure |
| Node servers: per-request data pushed to module scope; listeners added per request | Keep request state in locals; a `MaxListenersExceededWarning` is a leak report |

Finding one in the browser:

1. DevTools → Performance monitor: watch JS heap size, DOM nodes and JS event listeners while
   repeating the suspect action (open and close the modal, navigate there and back) ten times.
   A staircase that never comes down after garbage collection confirms it.
2. Memory → heap snapshot before; repeat the action a known number of times; force GC (the trash
   icon); snapshot after. In the Comparison view sort by delta: objects whose count grew by
   exactly the number of repetitions are the leak. Filter for "Detached" to find DOM held by JS.
3. Select an instance and read the Retainers pane from the bottom: it is the reference chain
   keeping it alive, and names the listener, closure or map to fix.

In Node, attach DevTools with `node --inspect` and take the same snapshots, or start the process
with `--heapsnapshot-signal=SIGUSR2` and send the signal twice under load. Use a production
build: development modes retain extra references and give false positives.

## Ask the user

- **How strict may the type check be on an existing codebase?** Turning on `strict` in a large
  loose project is days of work. Default: strict for new projects; for existing ones, enable
  flags one at a time and fix as files are touched.
- **What should the user see when a request times out or fails?** Retry silently, show an error
  with a retry button, or fall back to stale data is a product choice. Default: one automatic
  retry for reads, then a visible error with a retry action; never retry writes automatically
  without idempotency.
- **Which runtimes must the code support (Node versions, older browsers)?** It decides which
  built-ins are available without polyfills. Default: current Node LTS and Baseline Widely
  available.
- **Is this package published for others, or internal?** Published packages need `exports`,
  type declarations and compatibility care; internal code does not. Default: internal.
