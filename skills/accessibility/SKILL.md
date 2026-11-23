---
name: accessibility
description: Makes web interfaces usable by people with disabilities and conformant with WCAG 2.2 AA, covering names and ARIA, keyboard and focus, forms and sign-in, contrast, zoom and media, and testing. Use when asked to make a page or component accessible, audit for WCAG, fix axe or Lighthouse accessibility errors, fix screen reader, keyboard or contrast problems, build an accessible modal, menu or combobox, or prepare a VPAT.
---

# Accessibility

## Stance

Accessibility is a property of how the interface is built, not a layer added afterwards. Most of
it comes free from native HTML and tested primitives, and most failures come from replacing those
with `div`s, removing focus styles, and trusting a green automated scan. The target is WCAG 2.2
level AA, judged by whether a person using a keyboard, a screen reader, zoom or voice control can
finish the product's core tasks.

- **Native element first, tested primitive second, hand-written ARIA last.** A `<button>` brings
  role, focus, keyboard and state; ARIA only changes what is announced and leaves the behavior to
  be coded. Wrong ARIA is worse than none because it overrides correct semantics.
- **Keyboard is the base layer.** Screen readers, switches and voice control all ride on focus
  and standard semantics. If a flow works by keyboard with visible focus, most of the rest
  follows; if it does not, nothing else matters.
- **Every control has a name, a role and a current state, and the name contains the visible
  label.** That one rule serves screen-reader and voice-control users at once.
- **Focus is state the application owns.** After a route change, a dialog, a delete or a step
  change, decide where focus goes. Focus falling back to `body` is a bug, like a lost scroll
  position but worse.
- **Automated checks are a floor.** They can test a minority of the criteria and none of the
  ones about order, operability or meaning. Passing axe means "nothing obviously broken", so pair it with a
  keyboard pass and a screen-reader pass.
- **Fix at the source: component and token, not page.** One repaired `Button`, `Field`, `Dialog`
  or color pair fixes every screen and stays fixed; per-page patches regress.
- **Never rely on one sense or one ability.** Not color alone, not hover alone, not drag alone,
  not sound alone, not memory alone, not a time limit the user cannot extend.
- **Prioritize by who is blocked.** A trap in sign-in outranks fifty redundant attributes. Core
  flows first, then shared components, then the long tail.
- **Follow the project's component library.** Use its dialog, menu and field; do not add a
  second primitive library or a compliance overlay script.

## Route

| If the task is... | Read |
|---|---|
| A screen reader says nothing, the wrong thing, or "clickable" for a control; writing alt text; cleaning up `role` and `aria-*`; building or replacing tabs, a menu, a combobox, a dialog or a tooltip; announcing "saved" or result counts; making a data table readable | `references/names-roles-aria.md` |
| Something cannot be reached or operated by keyboard; focus ring missing or hidden; focus lost after navigation, delete or closing a modal; skip link and tab order; touch target sizes; drag-and-drop, hover-only or swipe-only interactions | `references/keyboard-focus.md` |
| Form labels, hints and required fields; validation errors that are not announced; sign-in, password manager, one-time code or CAPTCHA barriers; session timeout warnings; checkout, onboarding and other multi-step flows | `references/accessible-forms.md` |
| Checking color contrast; zoom, reflow at 320 px and text resizing; meaning carried by color; captions and transcripts; autoplay, carousels, flashing and reduced motion; plain language, consistent navigation and time pressure | `references/visual-cognitive.md` |
| Adding axe to CI or fixing an axe or Lighthouse report; testing with VoiceOver or NVDA; a per-feature manual pass; a WCAG 2.2 AA audit and how to rank and fix findings; definition of done; testing with disabled users; a VPAT or conformance report | `references/testing-audits.md` |

A request to "make this accessible" with no further detail: start with the keyboard pass and
names (first two files), then forms if any, then the visual checks, then add the automated scan.

## Defaults at a glance

| Decision | Default | Flips when |
|---|---|---|
| Conformance target | WCAG 2.2 AA | A contract or regulator names another version or level (2.2 AA content also meets 2.1 and 2.0 AA; report against the version they cite) |
| Interactive elements | `<button>`, `<a href>`, native inputs | No native element exists for the pattern |
| Overlays and composites | Native `<dialog>`, or Radix-style headless primitives | The project already has a component library with its own |
| Naming | Visible text, then `<label>`, then `aria-labelledby`, then `aria-label` | Icon-only control: `aria-label` or hidden text |
| Focus ring | `:focus-visible`, 2 px `outline`, 3:1 contrast, 2 px offset | Never removed, only restyled |
| Target size | 44 by 44 CSS px for primary and touch; 24 by 24 floor with spacing | Inline text links are exempt |
| Text contrast | 4.5:1; 3:1 for large text, control boundaries, icons, focus | |
| Links in body text | Underlined | |
| Errors | Inline text tied with `aria-describedby`, `aria-invalid`, focus to first error or to a summary | Long forms use the summary |
| Status messages | One polite and one assertive live region in the root layout | |
| Route change | Unique title, announced, focus at the start of new content; verify what the framework does | |
| Sign-in | Paste and password managers always work; one memory-free method; no puzzle CAPTCHA | |
| Time limits | Sliding session, warning dialog, one-action extension, work preserved | Real-time or essential limits |
| Motion | Honor `prefers-reduced-motion`; nothing with sound autoplays; anything moving can be paused | |
| Media | Edited captions on every video with speech; transcript for audio | |
| Drag interactions | Always paired with a click or menu alternative | |

By stage:

| Stage | Do | Skip for now |
|---|---|---|
| Prototype | Semantic HTML, headless primitives, labels, the JSX accessibility lint plugin, focus ring left on | Audits, screen-reader matrix, conformance reports |
| Launch | axe in CI on key flows and their states, keyboard and zoom pass per feature, screen-reader pass on sign-up, sign-in, core task and payment, contrast-tested tokens, captions | Third-party audit, user sessions |
| Scale | Scheduled full audit, conformance report (VPAT), sessions with disabled users, accessibility in component-library tests and the PR checklist | |

## Before you call it done

1. The whole flow works with the keyboard alone: every control reachable, operable with the
   expected keys, and every overlay closes with Esc.
2. Focus is visible at every stop, is not hidden behind sticky content, and
   `document.activeElement` is never `body` after navigation, modal close or deletion.
3. Every interactive element shows a role and a non-empty name in the DevTools accessibility
   pane, and the name contains the visible label.
4. No clickable `div` or `span`, no positive `tabindex`, no `aria-hidden` subtree containing a
   focusable element, no ARIA id reference to a missing element.
5. Every form field has a visible, associated label; errors are text, tied to the field, and
   announced on submit with focus moved to the first one.
6. Images have purposeful `alt` or `alt=""`; icon-only buttons have names.
7. Text contrast is at least 4.5:1 and control boundaries, icons and focus rings at least 3:1, in
   every theme.
8. At 1280 px width and 400% zoom the page is single-column with no clipped content, and pinch
   zoom is not disabled.
9. No state, error or status is conveyed by color alone; the page is still usable in forced
   colors and grayscale.
10. Interactive targets are at least 24 by 24 CSS px or adequately spaced; primary touch targets
    are 44.
11. Dynamic updates (saved, loaded, errors, result counts) are announced once through a live
    region or a focus move, not both.
12. Nothing autoplays with sound, moving content can be paused, and large motion is removed under
    `prefers-reduced-motion`.
13. An axe scan of each changed page and state, with WCAG 2.2 A and AA tags, reports no
    violations, and "needs review" items were checked by hand.
14. The changed flow was listened to once with a screen reader, and what was not tested is stated
    in the hand-off instead of implied as covered.

## Not this skill

- Accessibility law, statements and responding to legal complaints → `0x:privacy-compliance`
- General HTML structure, forms, CSS and reduced-motion animation code → `0x:frontend-foundations`
- Visual design, color palettes and usability testing in general → `0x:ui-ux-design`
- Accessible charts and data-visualization design → `dataviz`
- Setting up the end-to-end test runner that hosts axe checks → `0x:code-quality`
