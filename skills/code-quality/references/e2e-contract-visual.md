# End-to-end, contract and visual tests

Read this when: testing whole user journeys in a browser, setting up Playwright, a browser test
fails only in CI, guarding an API contract between systems, or catching visual regressions.

## How few end-to-end tests are enough

An end-to-end test is the most expensive kind: slowest, most moving parts, hardest to diagnose.
It earns its place only where nothing cheaper proves the pieces work together for a user.

Selection rule: list the journeys where a silent break costs revenue or locks users out. One
test per journey for the happy path, plus one for the most important failure in it (card
declined, wrong password). Everything else (validation permutations, edge cases, role
variants) goes to integration or component tests.

| Stage | Suite |
|---|---|
| Prototype | One smoke test: the app loads, a user signs in, the core action works |
| Launch | 5 to 15 tests: sign up, sign in, password reset, core action, checkout, upgrade or downgrade, cancel, invite a teammate, one permission boundary |
| Scale | Still tens, not hundreds. Growth goes into lower layers; add a post-deploy production smoke subset |

Budget: the whole suite under about 10 minutes in CI on pull requests, and under 5 for the
subset run after deploy. When a new test is proposed, ask which lower-level test would catch
the same defect; add the end-to-end test only if none can.

## Playwright setup that stays stable

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['github']] : 'list',
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'pnpm build && pnpm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

Decisions behind it:

- **Run against a production build**, not the dev server. Dev mode compiles on demand (first
  hits time out), double-invokes effects, and hides caching and hydration bugs.
- **Retries in CI only, with trace on first retry.** A test that passes on retry is reported
  as flaky; treat that report as a defect list (test-data-flaky.md), not as green.
- **Each test owns its data.** Create the user and records the test needs through an API call
  or direct database seed in a fixture, with unique emails (`e2e+${crypto.randomUUID()}@...`).
  Tests that depend on a previous test's leftovers cannot run in parallel or alone.
- **Set up through the back door, assert through the front.** Only the behavior under test is
  driven through the UI. Signing in through the form in every test wastes minutes and couples
  everything to the login page.
- **Reuse authentication.** Sign in once in a setup project, save
  `page.context().storageState({ path })`, and point other projects at it with
  `storageState` and `dependencies: ['setup']`. Keep one file per role. Tests that mutate
  account-level state need their own user, or they race in parallel.
- **No fixed sleeps.** `page.waitForTimeout()` is the main cause of slow and flaky suites. Use
  web-first assertions, which retry until the timeout: `await expect(locator).toBeVisible()`,
  `toHaveText`, `toHaveURL`. For non-DOM conditions use `expect.poll(...)`.
- **Wait for the app, not the network.** Wait on the visible result of an action. If an action
  needs hydration first, assert on a state the app exposes when interactive (the button is
  enabled) before clicking. A click that lands before hydration does nothing and the test then
  times out later; this is the most common CI-only failure in server-rendered React apps.
- **Stub third parties the journey does not own** with `page.route()` (analytics, chat
  widgets, maps) so their outages and latency do not fail the suite.

## Selecting elements

Select the way a user and a screen reader find things. Priority:

1. `page.getByRole('button', { name: 'Create project' })`: role plus accessible name.
2. `page.getByLabel('Email')` for form fields.
3. `page.getByText(...)` for non-interactive content.
4. `page.getByTestId('invoice-row')` for things with no stable role or text: repeated rows,
   canvas, icon-only controls that lack a label (and then add the label).

Never CSS paths, generated class names, `nth-child`, or XPath: they encode layout and break on
every restyle. Scope instead of indexing:
`page.getByRole('row', { name: 'Acme Inc' }).getByRole('button', { name: 'Delete' })`.

Locators are strict: an action on a locator matching several elements throws. Fix by scoping
or `{ exact: true }`, not `.first()`, unless order is the behavior. If the UI is localized or
copy changes often, select by role with test IDs for containers, and run the suite in one fixed
locale. A control that cannot be selected by role and name is usually an accessibility defect
(`0x:accessibility`).

## Cross-browser and mobile viewports in CI

| Project | Catches | Run |
|---|---|---|
| Chromium desktop | Most functional regressions | Every pull request |
| WebKit desktop | Safari-family issues: date inputs, cookie and storage rules, flex and grid gaps, missing APIs | Every pull request for critical journeys, or at least on main |
| Firefox desktop | Occasional form, focus and scrollbar differences | On main or nightly |
| Mobile viewport (`devices['Pixel 5']`, `devices['iPhone 13']`) | Responsive breakage: hidden navigation, covered buttons, overflow, touch-only paths | Every pull request for critical journeys |

Mechanics: add projects to the config; tag the critical tests (`test('checkout @critical', ...)`)
and run the wider matrix with `--grep @critical` so the matrix multiplies a small set. Install
browsers in CI with `npx playwright install --with-deps`, or run inside the official Playwright
container image matching the installed package version; version mismatch between the package
and the browsers is a hard failure.

Limits to state plainly: device descriptors emulate viewport, user agent and touch on the
desktop engine. Playwright's WebKit is not iOS Safari: it lacks the real on-screen keyboard,
safe areas, autofill and iOS-specific bugs. Emulation does not replace the real-device pass in
the bug bash (test-strategy.md).

## Sign-in, payment and email flows

| Flow | Approach |
|---|---|
| Email and password | Real form in one test; saved `storageState` everywhere else |
| OAuth or social sign-in | Do not automate the provider's login page: bot detection, CAPTCHA and 2FA make it flaky and may violate terms. Test the callback handler in integration tests with a faked provider; for end to end, run a local mock OIDC provider or a test-only sign-in route that is compiled out or hard-disabled in production |
| Magic link, verification, reset email | Send to a test inbox the test can query: a local SMTP catcher (Mailpit) in dev and CI, or a hosted test-inbox API against staging. Poll the inbox API for the message to the unique address, extract the link, `page.goto` it |
| TOTP 2FA | Seed the user with a known TOTP secret and generate the code in the test |
| CAPTCHA | Use the vendor's documented test keys in non-production environments |
| Card payment | Provider test mode with test keys and documented test card numbers. With Stripe: `4242 4242 4242 4242` succeeds, `4000 0000 0000 0002` is declined, `4000 0025 0000 3155` requires 3D Secure; any future expiry and any CVC |
| Payment webhooks | The UI test asserts on the app's state after the webhook arrives. Forward events to the local or CI app with the provider's CLI (`stripe listen --forward-to localhost:3000/api/webhooks/stripe`), and poll the app for the entitlement instead of sleeping |
| Subscription renewal, trial end, dunning | Not through the browser. Use the provider's time-simulation feature (Stripe test clocks) in integration tests |

Traps: card fields usually live in a cross-origin iframe, so reach them with
`page.frameLocator(...)`; provider-hosted checkout pages change without notice and may resist
automation, so keep exactly one test through them and cover the rest at the webhook boundary.
Never put live keys in CI, and add a guard that refuses to start the suite when the key is not a
test key. Payment specifics are in `0x:payments-billing`.

## Debugging a failing test from its artifacts

Order of work when a test fails in CI:

1. Download the trace from the CI artifacts and open it: `npx playwright show-trace trace.zip`.
   Upload the report directory and `test-results/` as artifacts on failure, or nothing can be
   diagnosed.
2. Go to the failing action. Read, in this order: the error and the locator's call log (what it
   waited for and what it found), the DOM snapshot before and after the action, the console
   tab, the network tab.
3. Classify:

| What the trace shows | Cause | Fix |
|---|---|---|
| Element present in the snapshot but action timed out | Covered by an overlay, disabled, or animating | Wait for the overlay to go; assert enabled first |
| Click happened, nothing changed | Clicked before hydration or before a handler attached | Assert on an interactive-ready state before acting |
| Locator resolved to 2 or more elements | Strict mode violation after a UI change | Scope the locator |
| Request returned 401 or 403 | Expired or shared auth state, or parallel test signed the user out | Per-worker users; regenerate storage state |
| Request returned 5xx or never completed | Real backend defect or missing seed data | Read the server logs for that request ID; fix the app or the fixture |
| Expected text never appears, data from another test visible | Shared data between parallel tests | Unique data per test |
| Passes locally, fails in CI only | Slower machine exposes a race, different viewport, time zone or locale, missing env var | Reproduce with `--repeat-each=20 --workers=4` and CPU throttling; pin locale and time zone in config |

4. Reproduce locally: `npx playwright test path/to/spec.ts --ui` for time-travel, or `--debug`
   to step. `--last-failed` reruns only failures. Record video only when a trace is not enough;
   traces carry more information for less cost.

## Visual regression

Use where appearance is the product risk: the design system's components, the landing and
pricing pages, emails, PDFs and invoices, charts. Skip pages with heavy live data.

```ts
await expect(page).toHaveScreenshot('pricing.png', {
  fullPage: true,
  mask: [page.getByTestId('relative-time')],
  maxDiffPixelRatio: 0.01,
});
```

Rules that keep it from becoming noise:

- **One rendering environment.** Font rendering and anti-aliasing differ by OS, so baselines
  made on a Mac will not match Linux CI. Generate and update baselines in the same container
  image CI uses, and commit them. Snapshot file names include the project and platform.
- **Remove nondeterminism:** fixed viewport and device scale factor, frozen clock, seeded
  data, animations disabled (the screenshot assertion does this by default), web fonts loaded
  before capture (`await page.evaluate(() => document.fonts.ready)`), masked regions for
  avatars, ads, maps and timestamps.
- **Prefer component or section screenshots** over full pages: smaller diffs, clearer cause.
- **Updating a baseline is a review act.** Update with `npx playwright test --update-snapshots`
  only for intended changes, and look at each image diff in the pull request. Blind updates
  make the suite worthless.
- **Tolerance small and explicit.** Start near zero and raise only for a named reason. A
  hosted visual-diff service adds a review UI and cross-browser rendering; it is worth paying
  for once there is a designer or a component library with many states (Scale, or earlier for
  design-led products).

## Contract tests

A contract test proves a provider still satisfies what its consumers rely on, without running
both together. Choose by who the consumers are:

| Situation | Guard |
|---|---|
| Frontend and backend in one TypeScript repo, deployed together | Shared types are the contract: one schema (Zod, tRPC router, or generated OpenAPI types) imported by both sides; the type check fails on drift. No separate contract tests |
| Same repo but deployed separately, or mobile apps and old clients in the field | Types are not enough: old clients keep calling the new server. Keep the OpenAPI document in the repo and fail CI on breaking changes with a spec diff tool (`oasdiff breaking old.yaml new.yaml`), and validate real responses against the spec in integration tests |
| Several services or teams, each deploying independently | Consumer-driven contracts (Pact): each consumer's tests record the requests it makes and the response fields it reads; the provider's CI replays them against the real provider. Needs a broker and a "can I deploy" check to be worth it |
| Third-party API consumed by the app | Recorded fixtures plus a scheduled check against the vendor's sandbox (unit-integration-tests.md) |
| Webhooks and events the app emits to customers | Versioned JSON Schema per event, validated in the emitter's tests; schema diff in CI |

What counts as breaking, to encode in the check: removing or renaming a field, changing a type,
making an optional request field required, adding a new enum value clients switch on, tightening
validation, changing status codes or error shapes, changing pagination defaults. Adding an
optional response field is safe only if consumers ignore unknown fields; make the consumer
parsers tolerant on purpose. Versioning policy lives in `0x:api-design`.

The main trap with consumer-driven contracts: consumers assert on whole response bodies with
exact values, so every provider change breaks every contract. A contract states only the
fields the consumer reads, with type matchers.

## Ask the user

- **Which journeys, if broken for a day, lose money or lock users out?** These are the
  end-to-end list. Assume sign up, sign in, the core action and checkout.
- **Is there a staging environment with third parties in test mode?** Decides whether
  end-to-end runs against a CI-local app or a deployed preview. Assume CI-local with fakes for
  anything without a test mode.
- **Who consumes the API besides this frontend (mobile apps, customers, partners)?** Any
  consumer that deploys on its own schedule makes a breaking-change check mandatory. Assume
  only the web app until told otherwise.
- **Does visual polish drive sales (design-led product, marketing site)?** If yes, add
  screenshot tests for key pages at Launch. Assume no visual tests until a visual regression
  ships once.
- **May test runs send real email or SMS to a test inbox provider?** Assume no: local SMTP
  catcher and faked SMS.
