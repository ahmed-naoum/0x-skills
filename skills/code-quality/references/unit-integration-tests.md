# Unit and integration tests

Read this when: writing tests for business logic, database code, API routes or UI components,
deciding what to mock, covering failure paths, or the suite has become slow.

## Unit tests for business logic

A unit test here means: no I/O, no clock, no randomness, runs in milliseconds, fails only when
behavior changes. If the code under test cannot meet that, restructure it (see "Design for
testability" in test-strategy.md) rather than mocking around it.

Rules that separate useful unit tests from noise:

- **Test behavior through the public function, one behavior per test.** Name the test as a
  rule of the domain: `prorates a mid-cycle upgrade by remaining days`, not `calls calculate`.
- **Table-driven cases for rules.** Edges get one row each: zero, one, boundary, boundary + 1,
  negative, maximum, empty, duplicate, Unicode, DST change, month end, leap day.

```ts
import { describe, expect, it } from 'vitest';

describe('seatPriceCents', () => {
  it.each([
    { seats: 1, expected: 1200 },
    { seats: 10, expected: 12000 },
    { seats: 11, expected: 12000 + 1000 }, // volume tier starts at seat 11
    { seats: 0, expected: 0 },
  ])('$seats seats cost $expected', ({ seats, expected }) => {
    expect(seatPriceCents(seats)).toBe(expected);
  });
});
```

- **Assert on values, not interactions.** `expect(result).toEqual(...)` survives refactoring;
  `expect(mock).toHaveBeenCalledWith(...)` rarely does. Reserve interaction assertions for
  effects that are the behavior (an email was requested exactly once).
- **No logic in tests.** No loops computing the expected value with the same formula as the
  code; write the expected literal.
- **Money in integer minor units** in code and assertions. Floating-point equality on currency
  is a bug in both.
- **Inline snapshots only for small, stable, reviewed output** (an error message, a generated
  SQL fragment). Never snapshot a whole object with timestamps or IDs.

## Integration tests against a real database

Mocking the database or ORM tests the mock. The defects that matter (wrong join, missing
tenant filter, constraint violation, transaction that does not roll back, migration drift,
N+1) only appear against the real engine. Use the same engine and major version as production:
SQLite or an in-memory substitute standing in for Postgres hides differences in types,
constraints, locking, JSON and time zone behavior.

Setup that works for one developer and CI alike:

1. Start Postgres once per run: a Compose service or CI service container, or Testcontainers
   started from the test runner's global setup so `pnpm test` needs no manual step.
2. Apply the project's real migrations to it, the same way production does. This tests the
   migrations on every run.
3. Isolate tests from each other (per-test transaction, or a database per worker; the
   trade-offs are in test-data-flaky.md).
4. Each test creates the rows it needs through factories and asserts on rows it reads back.

```ts
// global setup sketch with Testcontainers
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import type { TestProject } from 'vitest/node';

export default async function setup(project: TestProject) {
  const pg = await new PostgreSqlContainer('postgres:17').start(); // match production's major
  // run migrations here, against pg.getConnectionUri()
  project.provide('databaseUrl', pg.getConnectionUri());
  return async () => { await pg.stop(); };
}
```

Global setup runs outside the test workers, so do not rely on `process.env` set there reaching
the tests. Read the value with `inject('databaseUrl')` from `vitest` in a setup file and
assign `process.env.DATABASE_URL` there, before the app's database module is imported;
declare the key by augmenting `ProvidedContext` so it is typed.

What to assert at this layer: the row state after the operation, that constraints reject bad
writes (unique, foreign key, check), that a failure midway leaves nothing behind, that a query
scoped to tenant A returns nothing of tenant B, and that list queries keep a constant number of
statements as rows grow (count queries with a logging hook to catch N+1).

Speed levers before reaching for mocks: one container per run, not per file; migrations once,
then a template database or transactions; on a throwaway test container only, `fsync=off`
removes most write cost.

## API routes through the HTTP layer

Test the route as a client sees it: method, path, headers, cookies, body in; status, headers,
body out. Calling the service function directly skips the parts that break: middleware, auth,
validation, serialization, error mapping.

Mechanics by stack:

- Frameworks with an in-process request helper (Hono `app.request()`, Fastify `inject()`,
  Express with supertest): use it; no port needed.
- Next.js route handlers are functions of a standard `Request`: import the handler and call it
  with `new Request(url, { method, headers, body })`. This skips the framework's routing and
  its middleware (named proxy in newer versions), and a handler that calls `cookies()` or
  `headers()` from `next/headers` throws outside a real request. Cover those, and redirects
  or auth gating done in middleware, with tests against the running app: Playwright's
  `request` fixture or `fetch` against a started server.
- Authenticate the way real clients do: create a session row or signed cookie through a test
  helper that uses the app's own session code. Do not stub the auth check out; that is the
  thing under test.

Per route, the matrix that catches real defects:

| Case | Expect |
|---|---|
| Valid request, owner | 2xx, body matches the documented schema (parse it with the same Zod schema or the OpenAPI type) |
| No credentials | 401, no data in body |
| Valid user, wrong role | 403 |
| Valid user, another tenant's resource ID | 404 (or 403), and the row is unchanged |
| Invalid body, missing field, wrong type, extra large payload | 400 or 422 with the standard error shape; nothing written |
| Not found | 404 with the error shape |
| Conflict or repeat with the same idempotency key | 409, or the original response replayed |
| Dependency failure (faked) | 5xx or 503 with a generic message, no stack trace or SQL in body |

Assert the database state after mutating calls, not only the response. A 200 that wrote
nothing, or a 500 that wrote half, are the bugs.

## What to mock

Mock at the boundary of the system, not inside it. Inside the boundary, use the real thing.

| Dependency | In tests use | Why |
|---|---|---|
| Own modules, services, repositories | The real code | Mocking them freezes the design and hides integration bugs |
| Database | The real engine | See above |
| Clock, randomness, ID generation | Injected or fake (see test-data-flaky.md) | Determinism |
| Third-party HTTP APIs (payments, email, LLM, maps) | Network-level fake returning recorded responses | The app's real client code, serialization and error handling run |
| Queue, cache | The real one if it is cheap to start (Postgres-backed queue, Redis container); an in-memory implementation of the app's own interface otherwise | |
| Filesystem, object storage | Temp directory; an S3-compatible container or the app's storage interface in memory | |

For third parties, intercept at the network level with MSW so nothing in the application is
replaced, and fail on anything unexpected:

```ts
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const server = setupServer(
  http.post('https://api.example-mail.com/send', () => HttpResponse.json({ id: 'msg_1' })),
);
// in the test setup file:
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

`onUnhandledRequest: 'error'` is the important line: a test that silently reaches the real
network is slow, flaky and may send real email or charges.

Recorded responses: capture real responses from the vendor's sandbox once, strip secrets and
personal data, commit them as fixtures, and note the capture date and API version in the file.
Fakes drift: run a small scheduled job (weekly is enough) that calls the real sandbox with the
same requests and compares shapes, so a vendor change fails that job and not production.
Verifying webhook signatures in tests: sign the fixture payload with a test secret using the
vendor library's own helper where one exists, so signature code stays under test.

## UI components

Test what a user can perceive and do. With Testing Library: find by role and accessible name,
act with `userEvent`, assert on visible text, state and calls to the boundary.

```tsx
const user = userEvent.setup();
render(<InviteForm onInvite={onInvite} />);
await user.type(screen.getByLabelText('Email'), 'a@example.com');
await user.click(screen.getByRole('button', { name: 'Send invite' }));
expect(await screen.findByText('Invitation sent')).toBeVisible();
```

- Query priority: `getByRole` with name, then `getByLabelText`, then `getByText`;
  `getByTestId` last. A component that cannot be found by role usually has an accessibility
  defect; fix the component.
- Do not assert on state variables, hook internals, class names, or component instance
  methods, and do not shallow-render. Those tests break on refactors and pass on real bugs.
- Use `findBy*` (which waits) for anything asynchronous; never sleep.
- Worth a component test: conditional rendering with real logic, form validation and
  submission, keyboard interaction, loading, empty and error states. Not worth one: static
  layout, styling, wrappers around a library component.
- Async React Server Components have not been renderable in jsdom component tests (check the
  framework's testing docs for the current state); cover them with end-to-end tests and
  unit-test the data functions they call.
- jsdom has no layout: nothing about size, position, scrolling, or real focus order can be
  trusted there. Use Vitest browser mode or Playwright for those.

## Failure paths

Happy paths are where the tests are; production incidents are in the other paths. For each
operation that crosses a boundary, write these:

| Path | How to force it | Assert |
|---|---|---|
| Timeout | Fake returns after the client timeout (use fake timers) or never | The call gives up at the configured time; user sees a retryable error; nothing half-written |
| Retry | Fake fails twice with 503, then succeeds | Exactly three attempts, backoff respected, a single side effect downstream (idempotency key sent and identical on each attempt) |
| Non-retryable error | Fake returns 400 or 402 | No retry; error mapped to a domain error |
| Partial write | Make the second of two writes throw | Transaction rolled back, or the compensating step ran; state is consistent on re-read |
| Duplicate delivery | Deliver the same webhook or job twice | State changes once |
| Out-of-order delivery | Deliver event 2 before event 1 | Final state is correct, stale event ignored |
| Concurrency | `await Promise.all([op(), op()])` against the real database | Invariant holds: one winner, no oversell, no duplicate row. Run each such test in a loop of 20 or more to give the race a chance |
| Crash between steps | Throw after the external call, before the local commit | Re-running the operation converges and does not double-charge |

Concurrency tests need real separate connections and committed transactions, so they cannot
run inside a per-test rollback wrapper; give them a truncate-based or separate-database
isolation mode.

## Keeping the suite fast

Targets: single test file feedback in under 2 seconds in watch mode; whole unit and integration
suite in a few minutes in CI. Past that, people stop running it.

- Measure first: the runner's verbose or JSON reporter shows per-file time. Usually a few
  files and the setup phase dominate.
- Expensive setup once per worker or run, not per test: container start, migrations, app
  construction.
- Keep imports light. A test that imports the whole app to test one function pays the
  transform and module-evaluation cost per file; barrel files (`index.ts` re-exporting
  everything) are the usual cause.
- Use the node environment by default and jsdom only for files that render components; jsdom
  setup costs noticeably per file.
- No real waiting: fake timers for delays, backoff and debounce.
- Locally run only what changed (`vitest --changed`, watch mode); CI runs everything, sharded
  when wall-clock passes about 10 minutes.
- Split by tag or project when needed: `unit` on every save, `integration` on pre-push and CI.

## Property-based tests

Use when the input space is large and a rule holds for all inputs: parsers and serializers,
money arithmetic, date ranges, sorting and pagination, permission lattices, state machines,
anything with an encode and a decode. The framework (fast-check) generates inputs, finds a
failure and shrinks it to a minimal case.

```ts
import fc from 'fast-check';

it('splitting an amount never loses or creates cents', () => {
  fc.assert(
    fc.property(fc.integer({ min: 0, max: 10_000_000 }), fc.integer({ min: 1, max: 50 }), (cents, parts) => {
      const shares = splitEvenly(cents, parts);
      expect(shares.reduce((a, b) => a + b, 0)).toBe(cents);
      expect(Math.max(...shares) - Math.min(...shares)).toBeLessThanOrEqual(1);
    }),
  );
});
```

Property shapes that find bugs: round trip (`parse(format(x))` equals `x`), invariants (sum
preserved, never negative, sorted stays sorted), idempotence (`f(f(x))` equals `f(x)`),
comparison with a slow obvious implementation, and "no input throws anything but a validation
error". The trap: generators that are too narrow never reach the bug, and ones that are too
wide spend the budget on rejected inputs. When a property fails, copy the shrunk counterexample
into a normal example test so it stays covered permanently, and record the printed seed to
replay.

## Mutation testing

A mutation tool (Stryker for JavaScript and TypeScript) changes the code (`>` to `>=`, removes a
statement, flips a boolean) and reruns the tests; a mutant that survives marks behavior no test
checks. It answers what coverage cannot: are the assertions strong.

- Scope it to the critical modules only (pricing, permissions, proration, ledger). Whole-repo
  runs are slow and mostly noise.
- Run on demand or nightly, not on every push. Use the incremental mode on large modules.
- Read survivors one at a time: add a boundary case, add a missing assertion, or accept the
  mutant as equivalent (some mutations do not change behavior) and move on.
- Do not chase 100%. A rule of thumb: on money and permission modules, investigate anything
  under about 80% and every surviving boundary mutant.

## Ask the user

- **May tests call any third party's sandbox, or must they be fully offline?** Offline is
  faster and deterministic. Assume offline with recorded fakes, plus a scheduled drift check.
- **Is Docker available locally and in CI?** Decides Testcontainers versus a CI service
  container or a hosted branch database. Assume Docker is available.
- **Which operations must never run twice or half-run?** These get the full failure-path table.
  Assume charging, sending email, provisioning and deleting.
- **Is there a multi-tenant or role model?** If yes, the cross-tenant and wrong-role rows are
  mandatory for every route. Assume yes when any row carries an owner or organization ID.
