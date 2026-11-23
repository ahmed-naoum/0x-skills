# Accessibility testing and audits

Read this when: adding automated accessibility checks to CI, fixing what axe or Lighthouse
reports, testing a flow with a screen reader or keyboard, running a WCAG 2.2 AA audit and ranking
the findings, making accessibility part of the definition of done, testing with disabled users,
or producing a VPAT or conformance report for a buyer.

## What each kind of testing can prove

| Layer | Finds | Cannot find | Cost |
|---|---|---|---|
| Lint (`eslint-plugin-jsx-a11y`, or Biome's a11y rules) | Missing alt, label-less inputs, invalid ARIA, click handlers on non-interactive elements, at author time | Anything about rendered output | Seconds |
| axe on rendered pages | Missing names, contrast of plain text, duplicate ids, invalid role structure, missing `lang`, some target sizes | Whether a name is correct, focus order, keyboard operability, focus management, announcement quality, reflow, whether alt text is meaningful | Minutes in CI |
| Keyboard, zoom and forced-colors pass | Operability, focus loss, traps, clipping, color-only cues | How it sounds | About 15 minutes per feature |
| Screen-reader pass | Wrong or missing announcements, confusing order, silent updates | Problems of users with other disabilities | 20 to 40 minutes per flow |
| Audit against every criterion | Conformance gaps, systematically | Real-world usability | Days |
| Sessions with disabled users | Whether people can actually finish tasks | Coverage of every criterion | Recruiting plus sessions |

Automated tools can fully test only a minority of the success criteria. By issue count they
find more (around half in one tool vendor's own data), because a few detectable failures such as
low contrast are very frequent. A clean axe run or a Lighthouse accessibility score of 100 means
"no machine-detectable failures", never "accessible" and never "conforms". Lighthouse runs a
subset of axe rules; use axe directly for full coverage.

Accessibility overlay widgets (a script that claims to make a site compliant) do not produce
conformance, frequently interfere with users' own assistive technology, and have not protected
their customers from legal claims. Do not install one; fix the source.

## Automated checks in CI

Default stack for the house setup: the JSX accessibility lint plugin in ESLint, and axe run
inside the existing Playwright end-to-end tests with `@axe-core/playwright`. Setting up
Playwright itself belongs to `0x:code-quality`.

```ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const tags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

test("checkout has no detectable WCAG A or AA violations", async ({ page }) => {
  await page.goto("/checkout");
  const results = await new AxeBuilder({ page }).withTags(tags).analyze();
  expect(results.violations).toEqual([]);
});
```

What makes the difference between a check that runs and one that protects:

- **Scan states, not just URLs.** axe sees only the DOM at the moment `analyze()` runs. Call it
  again after opening each dialog and menu, after submitting an invalid form, in the empty,
  loading-finished and error states, and for signed-in pages. Most violations live in states a
  crawl never reaches.
- **Scan both themes.** Run with `page.emulateMedia({ colorScheme: "dark" })` as well; contrast
  failures are theme-specific.
- **Wait for the page to settle** (assert on a visible heading first). Scanning mid-transition
  yields flaky contrast results because of animated opacity.
- **Tags.** The list above is WCAG 2.2 A and AA. Keep `"wcag22aa"` in it: axe-core leaves its
  WCAG 2.2 rules, target size among them, off unless that tag or the rule is requested. Confirm
  once that `target-size` appears somewhere in the results object. Add `"best-practice"` (landmark
  and heading structure) once the baseline is clean; those rules are advice, not conformance.
- **Adopting on an existing product.** Do not start with hundreds of red tests or a blanket
  disable. Sequence: run across key pages, fix the rules that fail in shared components first,
  then for what remains use `.disableRules([...])` or `.exclude(selector)` with a tracked issue
  per exclusion, and fail CI on anything new. Tighten until the lists are empty.
- **Third-party embeds** (chat, payment iframes, video) can be excluded from the gating scan
  with `.exclude()`, but that hides the problem from CI only. The product is still responsible
  for the embed; record it in the audit and the vendor review.
- **Component level.** axe in a jsdom unit test catches missing names and invalid ARIA, but jsdom
  does no layout, so contrast and visibility-dependent rules do not run. A supplement only.
- **Assert behavior too.** Keyboard and focus are testable in Playwright: press `Tab`, `Enter`
  and `Escape` with `page.keyboard.press()` and assert with `expect(locator).toBeFocused()`.
  Locating elements with `getByRole(role, { name })` makes every functional test also check role
  and name. One keyboard-only test of the main flow catches the regressions axe cannot.

Fixing a report from axe or Lighthouse: group findings by rule and by component, not by page. A
"button has no accessible name" count of 40 is usually one icon-button component. Fix the
component, rerun, and only then look at page-specific leftovers. For each "needs review" or
"incomplete" item (typically contrast over images or gradients), check by hand; do not dismiss.

## Screen-reader pass

Behavior differs by screen reader and browser, so test the pairs people use:

| Screen reader | Pair with | Platform | Note |
|---|---|---|---|
| NVDA | Chrome or Firefox | Windows | Free; the most useful single desktop check alongside VoiceOver |
| JAWS | Chrome or Edge | Windows | Commercial; common in enterprise and public-sector settings |
| VoiceOver | Safari | macOS | Built in; test in Safari, since other browsers pair less well with it |
| VoiceOver | Safari | iOS | Built in; the dominant mobile screen reader |
| TalkBack | Chrome | Android | Built in |

Default for a solo developer: VoiceOver with Safari on the development Mac for every feature, and
NVDA on Windows (a spare machine or a virtual machine) plus VoiceOver on a real iPhone before
Launch and for each major flow change. One engine is not enough for custom widgets; they diverge
most on comboboxes, live regions and dialogs.

Enough commands to run a pass:

| Action | VoiceOver (macOS); VO is Control+Option | NVDA; the NVDA key is Insert |
|---|---|---|
| Start or stop | Command+F5, or hold Command and triple-press Touch ID | Control+Alt+N to start, NVDA+Q to quit |
| Next / previous item | VO+Right / VO+Left | Down / Up arrow |
| Activate | VO+Space | Enter or Space |
| Lists of headings, links, landmarks | VO+U (rotor) | NVDA+F7 |
| Jump by type | Via rotor, or quick-nav keys | `H` heading, `D` landmark, `F` form field, `B` button, `K` link, `T` table |
| Stop speech | Control | Control |
| Type into a field | Just type | NVDA switches to focus mode on form fields; NVDA+Space toggles it |

On iOS: swipe right and left to move, double-tap to activate, and rotate two fingers for the
rotor. Turn on the on-screen speech text (the caption panel in VoiceOver, the Speech Viewer in
NVDA) so the output can be read, copied into bug reports and compared before and after a fix.

Script for one flow, with the screen off or eyes away from it where possible:

1. Load the page. Is the title announced, and is it specific?
2. Open the headings list. Does it read as an outline of the page? Open landmarks: one `main`,
   named navigation regions.
3. Read through with next-item commands. Is the order sensible, is anything read twice, is
   decoration announced, is anything visible never read?
4. Tab through the controls. Each one: name, role, state. Would the name make sense on a list
   out of context?
5. Operate each widget. Are open, closed, selected and checked states announced as they change?
6. Trigger every dynamic change: validation errors, saving, loading results, toasts, a route
   change. Is each announced once, and does focus land somewhere sensible?
7. Complete the task and confirm the success state is announced.

Do not test only with Tab. Screen-reader users read with browse commands: check static text,
headings and cells with next-item navigation, and never give text `tabindex="0"` to "make it read".

## The manual pass for every feature

Run before merge on anything with UI. It needs no assistive technology and catches what
automation cannot.

| Check | How | Pass |
|---|---|---|
| Keyboard only | Put the mouse away; Tab, Shift+Tab, Enter, Space, arrows, Esc | Everything reachable and operable, focus always visible and in a logical order, overlays close and return focus, no trap |
| 200% zoom | Browser zoom at desktop width | Nothing clipped, overlapped or lost |
| Reflow | 1280 px window at 400% | Single-column, vertical scroll only, sticky elements leave room |
| Text spacing | Apply the 1.4.12 overrides | No cut-off text |
| Forced colors | DevTools rendering emulation of `forced-colors: active`, or a Windows contrast theme | Controls have visible boundaries, focus visible, icons present, states distinguishable |
| Grayscale | DevTools vision-deficiency emulation | No meaning carried by hue alone |
| Reduced motion | OS setting or DevTools emulation | Large movement removed |
| Pointer | Touch emulation at phone width | Targets large enough, nothing hover-only |

Once a feature has regressed twice, assert these in Playwright with screenshots under
`page.emulateMedia({ forcedColors: "active" })` and `{ reducedMotion: "reduce" }`.

## Running a WCAG 2.2 AA audit

WCAG 2.2 at level AA is 55 success criteria (levels A and AA together). An audit states, for a
defined scope, whether each is met. Laws and contracts cite different versions (2.0, 2.1 or 2.2,
often through Section 508 or EN 301 549). Content that meets 2.2 AA also meets 2.1 and 2.0 AA,
so audit against 2.2 and state the result against the version the buyer or regulator names.

1. **Scope.** List every page template, every shared component, and the key flows end to end:
   sign-up, sign-in and recovery, the core task, settings, billing or checkout, help. Add states
   (errors, empty, modals) and both themes. A sample of representative pages plus all flows is
   the accepted method; auditing every URL is not needed.
2. **Environment.** Record browsers, screen readers, versions, viewport sizes and date. Results
   are only meaningful against a stated environment.
3. **Automated sweep** over the sample to clear the machine-detectable issues and find patterns.
4. **Manual evaluation, criterion by criterion**, per template and flow: the manual pass above,
   then the screen-reader script, then content checks (alt quality, headings, link text,
   captions, error wording). Work through a WCAG 2.2 AA checklist so that nothing is skipped; the
   criteria added in 2.2 are the ones older checklists miss: Focus Not Obscured (2.4.11),
   Dragging Movements (2.5.7), Target Size Minimum (2.5.8), Consistent Help (3.2.6), Redundant
   Entry (3.3.7) and Accessible Authentication (3.3.8).
5. **Record each finding** with: location (page, component, state), the success criterion, what
   happens and for whom, steps to reproduce, severity, and the recommended fix. A finding
   without a criterion and a reproduction is not actionable.
6. **Deduplicate by root cause.** Fifty instances of one component bug are one finding with a
   list of locations.
7. **Retest** after fixes, and date the result.

Severity scale:

| Severity | Meaning | Example |
|---|---|---|
| Blocker | A group of users cannot complete a core task at all | Keyboard trap in checkout; sign-in button with no name; CAPTCHA with no alternative |
| Serious | Task possible only with great difficulty or a workaround | Errors not announced; focus lost after modal closes; body text at 3:1 |
| Moderate | Friction, or failure outside core tasks | Heading levels skipped; redundant announcements; a small target with a larger alternative nearby |
| Minor | Technical failure with little user effect | Redundant ARIA; a decorative image with verbose alt |

## Fixing in order of user impact

Priority is severity times reach, with shared code first:

1. Blockers in core flows: unreachable or unnamed controls, traps, inaccessible authentication.
2. Issues in shared components and layout (button, input, dialog, navigation, color tokens):
   one fix repairs every page, so these often outrank a worse bug on a rare page.
3. Serious issues in core flows: form errors, focus management, announcements.
4. Global visual issues: contrast tokens, focus ring, reflow of the main templates.
5. Structure and content: headings, landmarks, alt text, link text, captions.
6. Everything else, by frequency of the page.

Large-scale scans of the public web are dominated by six failures: low-contrast text, missing
alt text, missing form labels, empty links, empty buttons and missing page language. Clearing
them is the right first day's work on an untested product, not the definition of fixed.

Fix the component or token, not the instance, and add a regression test with each fix (an axe
scan of that state, or a keyboard assertion) so that it stays fixed.

## Definition of done and the component library

| Stage | What to have in place |
|---|---|
| Prototype | Headless accessible primitives for every overlay and composite, semantic HTML, the lint plugin on. Costs nothing now and is expensive to retrofit |
| Launch | axe in CI on key flows and their states, the manual pass on each feature, a screen-reader pass on sign-up, sign-in, core task and payment, contrast-tested tokens |
| Scale | A full audit on a schedule and after redesigns, a conformance report, sessions with disabled users, an accessibility contact and a triage rule for reported barriers |

Make the library carry the load; rules that rely on each author remembering do not hold:

- Components make the wrong thing hard to write. An `IconButton` whose TypeScript props require
  `label`; a `Dialog` that requires a title; a `Field` that renders label, hint and error and
  wires the ids, so no page hand-wires `aria-describedby`; an `Image` wrapper with required
  `alt`.
- Color tokens exist only as tested foreground and background pairs.
- Focus ring, target-size minimums and reduced-motion handling live in the base styles.
- Each component has a test for keyboard interaction and an axe scan of its states.
- The pull-request checklist for UI changes has four lines: keyboard pass done, zoom to 400%
  checked, names and states verified, automated scan green.
- Acceptance criteria for a feature name the accessible behavior ("focus moves to the dialog
  heading on open, returns to the Edit button on close") so that it is built, not retrofitted.

## Testing with disabled users

Conformance and usability differ; a flow can pass every criterion and still take a screen-reader
user ten minutes. Sessions with disabled people find that. Skip until Launch has settled; at
Scale, or earlier if the customer base includes many assistive-technology users, run them
alongside ordinary usability testing (method in `0x:ui-ux-design`, `usability-testing.md`).

- Fix known blockers first. Paying a participant to hit an unlabeled button found by axe wastes
  the session.
- Recruit across kinds of access need, not just blindness: screen reader, screen magnification,
  keyboard or switch, voice control, cognitive and learning disabilities, Deaf users for media.
  Three to five sessions per round is a workable rule of thumb. Sources: specialist recruiting
  panels, disability organizations, existing customers.
- Participants use their own device, assistive technology and settings, since that setup is
  what is being tested. Remote sessions with screen and audio sharing work well.
- Give tasks ("change the billing email"), not an audit request: participants are users, not auditors.
- Pay at least the rate of any other research participant, allow longer sessions, and make the
  recruitment form, consent form and scheduling tool themselves accessible.
- Record the barrier and the workaround observed, then map each to a fix; individual preference
  is not a finding, repeated failure is.

## VPAT and conformance reports

An enterprise, government or education buyer asking for "a VPAT" wants an Accessibility
Conformance Report (ACR): the Voluntary Product Accessibility Template, published by the
Information Technology Industry Council, filled in for a specific product version.

- **Edition.** The template comes in editions: WCAG, Section 508 (US federal), EU (EN 301 549)
  and INT (all of them). Ask the buyer which they need; default to the WCAG edition, the 508
  edition for US public sector, INT when selling on both sides of the Atlantic. Download the
  current template from ITI instead of reusing an old file: the template and the standards
  behind it are revised (EN 301 549's 2026 revision moves its web baseline from WCAG 2.1 to 2.2,
  and legal recognition of a new version lags its publication).
- **Basis.** The report must rest on an actual audit as described above. It lists evaluation
  methods, product version, date and a contact.
- **Terms.** For each criterion: Supports, Partially Supports, Does Not Support, Not Applicable.
  "Not Evaluated" is permitted only for AAA criteria. Every answer other than Supports needs a
  remark saying what fails and where.
- **Honesty.** "Partially Supports" with specific remarks is normal and buyers expect it; a
  report claiming full support everywhere is read as unaudited. The document becomes part of the
  procurement record, so an overstated claim is a contractual and legal exposure. Have counsel
  review wording when a contract references it.
- **Who writes it.** Self-authored reports are accepted by many buyers; some public-sector and
  higher-education buyers require or strongly prefer a third-party audit. Ask before paying for
  one.
- **Scope.** Cover the product the buyer will use, including the admin area, documentation and
  support channels if the edition asks for them, and name third-party components relied on.
- **Upkeep.** Reissue on major releases and at least yearly; a stale date is the first thing a
  procurement reviewer checks. Keep a short roadmap of known gaps with target dates to hand over
  with it.

Legal obligations, public accessibility statements and handling complaints or demand letters
are covered by `0x:privacy-compliance` (`sector-consumer-rules.md`).

## Ask the user

- **What target and deadline apply: WCAG 2.2 AA everywhere, or core flows first?** It sets audit
  scope and fix order. Default: AA as the standard, core flows blocker-free before Launch, the
  rest on a dated plan.
- **Should CI fail the build on accessibility violations?** Gating stops regressions but can
  block releases at first. Default: yes for new violations on key flows, with a tracked
  exclusion list for existing ones.
- **Is there a Windows machine or VM and a real phone for screen-reader testing?** Without them
  only one engine is tested. Default: VoiceOver on the Mac and iPhone now, NVDA before Launch.
- **Has a buyer asked for a VPAT, which edition, and do they require a third-party audit?** It
  decides between a self-authored report and a paid audit. Default: self-authored WCAG edition
  based on an internal audit, upgraded when a deal requires it.
- **Is there budget to pay disabled participants for usability sessions?** It is the only way to
  measure real usability. Default: not before Launch; a first round of three to five sessions at
  Scale.
