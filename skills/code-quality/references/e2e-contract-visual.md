# End-to-end, contract and visual tests

Read this when: testing whole user journeys in a browser, setting up thirtyfour, a browser test
fails only in CI, guarding an API or server-function contract between systems, catching visual
regressions, or deciding whether Playwright is worth a non-Rust suite.

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

## A thirtyfour suite that stays stable

Keep the journeys in their own test target (`tests/e2e.rs`) and mark them `#[ignore]`, so the
normal `cargo nextest run` skips them and the e2e job runs them with
`cargo test --test e2e -- --ignored`. The job builds the release binary, starts it with a test
configuration, waits for its health endpoint, then runs the tests against a WebDriver server.

```rust
use thirtyfour::prelude::*;
use thirtyfour::testing::run_browser_test;

/// Finds an input through its visible label; fails if the label is not linked (an a11y bug too).
pub async fn field_by_label(driver: &WebDriver, label: &str) -> WebDriverResult<WebElement> {
    let label = driver.query(By::Tag("label")).with_text(label.to_string()).single().await?;
    let id = label.attr("for").await?.ok_or_else(|| {
        WebDriverError::FatalError("label has no `for` attribute".into())
    })?;
    driver.find(By::Id(id)).await
}

#[tokio::test]
#[ignore = "needs the app and a browser; runs in the e2e job"]
async fn signup_reaches_the_dashboard() -> anyhow::Result<()> {
    let base = std::env::var("E2E_BASE_URL").unwrap_or_else(|_| "http://127.0.0.1:3000".into());
    let email = format!("e2e+{}@example.test", uuid::Uuid::new_v4());
    let mut caps = DesiredCapabilities::chrome();
    caps.set_headless()?;
    caps.add_arg("--window-size=1280,800")?;

    // Quits the browser even when the body returns an error or an assertion panics.
    run_browser_test(WebDriver::managed(caps), |driver| async move {
        driver.goto(format!("{base}/signup")).await?;
        driver.query(By::Css("body[data-hydrated]")).single().await?; // set by the app once interactive
        field_by_label(&driver, "Email").await?.send_keys(&email).await?;
        field_by_label(&driver, "Password").await?.send_keys("correct horse battery").await?;
        driver.query(By::Tag("button")).with_text("Create account").single().await?.click().await?;
        driver.query(By::Testid("dashboard-heading")).with_text("Welcome").single().await?;
        Ok::<_, WebDriverError>(())
    })
    .await?;
    Ok(())
}
```

Decisions behind it:

- **Run against a release build**, not `cargo leptos watch`: the watch server rebuilds on
  demand, runs a debug build and can hide caching and hydration bugs.
- **Quit the browser whatever happens.** `run_browser_test` awaits `quit` after an error or a
  panic; a test that panics before quitting leaks a browser and its driver session, and the
  next tests fail for lack of sessions.
- **Driver management.** `WebDriver::managed` downloads and starts a chromedriver matching the
  installed Chrome, which needs network access to the driver download host. Where CI has none,
  run chromedriver, geckodriver or a Selenium container as a service and connect with
  `WebDriver::new("http://localhost:4444", caps)`.
- **Waiting.** `query` polls until the element exists (20 seconds by default, every 500 ms),
  and `element.wait_until().clickable()` waits for state. Never `tokio::time::sleep`: it is
  the main cause of slow and flaky suites.
- **Wait for hydration, not the network.** A server-rendered Leptos page shows buttons before
  the WASM has loaded and hydrated; a click before that does nothing and the test times out
  later. Have the client entry set a marker such as `data-hydrated` on `<body>` right after
  hydration, and wait for it after every full page load. This is the most common CI-only
  failure in server-rendered apps (`0x:rust-frontend`, hydration.md).
- **Each test owns its data.** Unique emails per run (`e2e+<uuid>@example.test`); tests that
  depend on a previous test's leftovers cannot run in parallel or alone.
- **Set up through the back door, assert through the front.** Only the behavior under test is
  driven through the UI. Sign in through the form in one test; elsewhere create the user and
  a session row with the app's own code, open any page on the app's origin, then
  `driver.add_cookie(...)` (WebDriver sets cookies only for the current origin). Tests that
  mutate account-level state need their own user.
- **Retries in CI only.** nextest's retries report a pass on retry as flaky; treat that list
  as a defect list (test-data-flaky.md), not as green.
- **Keep third parties the journey does not own out of the run** (analytics, chat widgets,
  maps) through the app's test configuration, so their outages do not fail the suite.

## Selecting elements

Select the way a user and a screen reader find things. WebDriver has no query by role and
accessible name (Playwright's main advantage here), so build two or three helpers like
`field_by_label` above and use them everywhere. Priority:

1. Form fields through their visible `<label>` (the helper fails when the label is not linked,
   which is an accessibility bug as well).
2. Buttons and links by tag and visible text: `query(By::Tag("button")).with_text("Save")`.
3. ARIA attributes, which are the accessibility contract: `By::Css("[role=dialog]")`.
4. `By::Testid("invoice-row")` (the `data-testid` attribute) for things with no stable role or
   text: repeated rows, canvas, icon-only controls that lack a label (and then add the label).

Never CSS paths, generated class names, `nth-child` or positional XPath: they encode layout and
break on every restyle. Scope instead of indexing: find the row by test ID or text, then query
inside it with `row.query(...)`. Use `.single()`, which fails unless exactly one element
matches, so an ambiguous selector fails loudly instead of clicking the wrong row. If copy
changes often or the UI is localized, run the suite in one fixed locale and use test IDs for
containers. A control that cannot be selected by label or text is usually an accessibility
defect (`0x:accessibility`).

## Cross-browser and mobile viewports in CI

| Target | Catches | Run |
|---|---|---|
| Chrome desktop (chromedriver) | Most functional regressions | Every pull request |
| Firefox desktop (geckodriver) | Form, focus and scrollbar differences | On main or nightly |
| Safari (safaridriver, macOS runner only) | Safari-family issues: date inputs, cookie and storage rules, missing APIs | Nightly or before release; real Safari, not an engine build |
| Mobile viewport (Chrome `mobileEmulation` via `add_experimental_option`, or a small window size) | Responsive breakage: hidden navigation, covered buttons, overflow | Every pull request for critical journeys |

Run the wider matrix on a small set: name the critical journeys with a common prefix
(`critical_checkout`) and filter on it. Limits to state plainly: emulation changes viewport,
user agent and touch on the desktop engine; it is not iOS Safari and lacks its keyboard, safe
areas and autofill. On Linux CI there is no practical WebKit target from WebDriver, which is
the second reason teams take Playwright (below). Emulation does not replace the real-device
pass in the bug bash (test-strategy.md).

## Sign-in, payment and email flows

| Flow | Approach |
|---|---|
| Email and password | Real form in one test; a seeded session cookie everywhere else |
| OAuth or social sign-in | Do not automate the provider's login page: bot detection, CAPTCHA and 2FA make it flaky and may violate terms. Test the callback handler in integration tests with a faked provider; for end to end, run a local mock OIDC provider, or a test-only sign-in route. That route is an authentication bypass if it ever ships: compile it only behind a Cargo feature the release build never enables, require a secret as well, and keep a test that it returns 404 on the release build |
| Magic link, verification, reset email | Send to a test inbox the test can query: a local SMTP catcher (Mailpit) in dev and CI, or a hosted test-inbox API against staging. Poll its HTTP API with reqwest for the message to the unique address, extract the link, `driver.goto` it |
| TOTP 2FA | Seed the user with a known TOTP secret and generate the code in the test (a TOTP crate such as totp-rs) |
| CAPTCHA | Use the vendor's documented test keys in non-production environments |
| Card payment | Provider test mode with test keys and documented test card numbers. With Stripe: `4242 4242 4242 4242` succeeds, `4000 0000 0000 0002` is declined, `4000 0025 0000 3155` requires 3D Secure; any future expiry and any CVC |
| Payment webhooks | The UI test asserts on the app's state after the webhook arrives. Forward events to the local or CI app with the provider's CLI (`stripe listen --forward-to localhost:3000/webhooks/stripe`), and poll the app for the entitlement instead of sleeping |
| Subscription renewal, trial end, dunning | Not through the browser. Use the provider's time-simulation feature (Stripe test clocks) in integration tests |

Traps: card fields usually live in a cross-origin iframe; find the `<iframe>` element, call
`enter_frame()` on it, and return with `driver.enter_default_frame()`. Provider-hosted checkout
pages change without notice and may resist automation, so keep exactly one test through them
and cover the rest at the webhook boundary. Never put live keys in CI, and make the suite
refuse to start when the configured key is not a test key. Payment specifics are in
`0x:payments-billing`.

## Debugging a failing test from its artifacts

WebDriver has no trace viewer: a failure shows only what the suite captured. Wrap each step so
a failure saves the evidence, and upload `target/e2e-artifacts` from CI on failure:

```rust
use std::path::Path;

use thirtyfour::prelude::*;

/// Wraps one journey step: on failure, saves a screenshot and the page HTML for the CI artifact.
pub async fn step<T>(
    driver: &WebDriver,
    name: &str,
    result: WebDriverResult<T>,
) -> anyhow::Result<T> {
    if let Err(err) = &result {
        let dir = Path::new("target/e2e-artifacts");
        std::fs::create_dir_all(dir)?;
        driver.screenshot(&dir.join(format!("{name}.png"))).await?;
        std::fs::write(dir.join(format!("{name}.html")), driver.source().await?)?;
        let url = driver.current_url().await?;
        tracing::error!(step = name, %url, error = %err, "e2e step failed");
    }
    Ok(result?)
}
```

Then read, in this order: the error and the selector that failed, the screenshot, the saved
HTML (was the element there, hidden, duplicated?), browser console errors (collect them through
the WebDriver BiDi or DevTools support in thirtyfour, or have the test build of the app mirror
console errors into the page), and the server's logs for that test's unique email or user ID.

| What the evidence shows | Cause | Fix |
|---|---|---|
| Element in the HTML but the click timed out or did nothing | Covered by an overlay, disabled, animating, or not yet hydrated | Wait for the hydration marker and `clickable()` |
| `.single()` failed with several matches | Ambiguous selector after a UI change | Scope the query |
| Request returned 401 or 403 | Expired or shared session, or a parallel test signed the user out | Per-test users; fresh session cookies |
| Request returned 5xx or never completed | Real backend defect or missing seed data | Read the server logs for that request; fix the app or the setup |
| Data from another test visible | Shared data between parallel tests | Unique data per test |
| Passes locally, fails in CI only | Slower machine exposes a race, different window size, time zone or locale, missing env var | Reproduce with a loop of 20 runs and two parallel threads; pin locale, zone and window size |

Reproduce locally without `set_headless` to watch the browser, with `--test-threads=1`.

## Visual regression

Use where appearance is the product risk: the design system's components, the landing and
pricing pages, emails, PDFs and invoices, charts. Skip pages with heavy live data.

The Rust stack has no built-in screenshot assertion. thirtyfour returns PNGs of the page or of
one element (`screenshot_as_png()`); comparing them needs an image-diff crate, a baseline
directory and an update workflow the team builds and maintains. A hosted visual-diff service,
or Playwright's screenshot assertion for this suite alone, are the alternatives; choose with
the next section. Whatever the tool, the rules that keep it from becoming noise:

- **One rendering environment.** Font rendering and anti-aliasing differ by OS, so baselines
  made on a Mac will not match Linux CI. Generate and update baselines in the same container
  image CI uses, and commit them.
- **Remove nondeterminism:** fixed window size and device scale factor, frozen clock, seeded
  data, animations disabled, web fonts loaded before capture, hidden regions for avatars,
  ads, maps and timestamps.
- **Prefer component or section screenshots** over full pages: smaller diffs, clearer cause.
- **Updating a baseline is a review act.** Update only for intended changes and look at each
  image diff in the pull request. Blind updates make the suite worthless.
- **Tolerance small and explicit.** Start near zero and raise only for a named reason. A
  hosted service adds a review UI and cross-browser rendering; it is worth paying for once
  there is a designer or a component library with many states (Scale, or earlier for
  design-led products).

## Whether Playwright justifies a non-Rust suite

Playwright is the stronger end-to-end tool: role and label locators, auto-waiting assertions,
a trace viewer with DOM snapshots per action, screenshot assertions, WebKit on Linux, mobile
device profiles, built-in sharding and flaky reporting. The cost is a Node toolchain in the
repository and CI, a second language, and tests that share no types with the app (they speak
HTTP and DOM either way).

| Situation | Choice |
|---|---|
| Up to about 15 journeys, Chrome and Firefox are enough, no screenshot suite | thirtyfour |
| Safari-family bugs are a real risk and no macOS runner is wanted | Playwright, for its WebKit target |
| CI-only flakes keep costing hours that a trace would have saved | Playwright |
| Visual regression is a product requirement | Playwright for that suite, or a hosted service |

Playwright is the one non-Rust exception worth accepting, and only with the founder's
agreement. Keep it isolated: an `e2e/` directory with its own lockfile, run only in the e2e
job, talking to the app over HTTP, with no build step of the app depending on it.

## Contract tests

A contract test proves a provider still satisfies what its consumers rely on, without running
both together. Choose by who the consumers are:

| Situation | Guard |
|---|---|
| Leptos client and server in one workspace, deployed together | Server functions share their argument and return types at compile time, so drift fails the build. One gap remains: an open tab keeps running the old WASM after a deploy, and a changed server-function signature breaks it. Change signatures additively (new fields with `#[serde(default)]`), or detect a version mismatch and reload |
| An HTTP API used by mobile apps, other teams or old clients in the field | Types are not enough: old clients keep calling the new server. Generate the OpenAPI document from the handlers (utoipa), commit it, regenerate in CI and fail on a diff, and fail on breaking changes with a spec diff tool (`oasdiff breaking old.yaml new.yaml --fail-on ERR`; without `--fail-on` it reports and still exits 0) |
| Several services or teams, each deploying independently | Consumer-driven contracts (Pact, which has a Rust implementation): each consumer's tests record the requests it makes and the fields it reads; the provider's CI replays them. Needs a broker and a "can I deploy" check to be worth it |
| Third-party API consumed by the app | Recorded fixtures plus a scheduled check against the vendor's sandbox (unit-integration-tests.md) |
| Webhooks and events the app emits to customers | Versioned JSON Schema per event generated from the Rust types (schemars), validated in the emitter's tests; schema diff in CI |

What counts as breaking: removing or renaming a field (including a serde `rename`), changing a
type, making an optional request field required, adding an enum value clients match on,
tightening validation, changing status codes or error shapes, changing pagination defaults.
Make Rust consumers tolerant on purpose: serde ignores unknown fields unless
`deny_unknown_fields` is set, so do not set it on types parsed from other systems; but an
unknown enum value fails the whole payload, so give such enums a `#[serde(other)]` fallback
variant. Versioning policy lives in `0x:api-design`. The main trap with consumer-driven
contracts: consumers asserting on whole bodies with exact values, so every provider change
breaks every contract. A contract states only the fields the consumer reads, with type matchers.

## Ask the user

- **Which journeys, if broken for a day, lose money or lock users out?** These are the
  end-to-end list. Assume sign up, sign in, the core action and checkout.
- **Is a Node toolchain acceptable in CI for the end-to-end suite only?** Decides thirtyfour
  versus Playwright. Assume no until WebKit coverage, traces or visual diffs are needed.
- **Is there a staging environment with third parties in test mode?** Decides whether
  end-to-end runs against a CI-local app or a deployed preview. Assume CI-local with fakes for
  anything without a test mode.
- **Who consumes the API besides this frontend (mobile apps, customers, partners)?** Any
  consumer that deploys on its own schedule makes a breaking-change check mandatory. Assume
  only the web app until told otherwise.
- **Does visual polish drive sales (design-led product, marketing site)?** If yes, add
  screenshot tests for key pages at Launch. Assume no visual tests until a visual regression
  ships once.
