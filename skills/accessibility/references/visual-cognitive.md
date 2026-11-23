# Visual, media and cognitive access

Read this when: checking color contrast, zoom, reflow or text resizing, removing reliance on
color, adding captions or transcripts, handling autoplay, flashing and motion, or making content
and navigation easier to read and follow for users with cognitive disabilities.

Choosing a palette and type scale belongs to `0x:ui-ux-design`; chart colors to `dataviz`. This
file is the set of thresholds those choices must clear and how to verify them.

By stage: at Prototype, choose token pairs that pass and never disable zoom; the rest can wait.
At Launch run the zoom, reflow, forced-colors and reduced-motion checks on core flows and caption
every published video. Live captioning and a plain-language review of help content are Scale
work unless a contract asks sooner.

## Contrast

| What | Minimum ratio | Criterion |
|---|---|---|
| Body text, and text in images | 4.5:1 | 1.4.3 (AA) |
| Large text: at least 24 CSS px, or at least 18.66 CSS px and bold (18 pt / 14 pt bold) | 3:1 | 1.4.3 |
| UI component boundaries and states needed to identify the control: input borders, checkbox outlines, toggle tracks, selected-state indicators | 3:1 against adjacent colors | 1.4.11 (AA) |
| Meaningful graphics: icons without text, chart lines and segments | 3:1 | 1.4.11 |
| Focus indicator | 3:1 against adjacent colors | 1.4.11 |
| Disabled controls, pure decoration, logos | Exempt | |

The ratio is `(L1 + 0.05) / (L2 + 0.05)` on relative luminance, from 1:1 to 21:1. On a white
background the lightest gray that reaches 4.5:1 is `#767676`; anything lighter fails for body
text. Do not round: 4.47:1 fails.

Where contrast fails in practice, in rough order of frequency:

- Placeholder text, helper text, timestamps and "muted" captions. They are text; 4.5:1 applies.
  In default utility palettes the 400-level grays on white fail; check the computed value of
  whatever token the project uses for muted text instead of assuming.
- Text on brand-colored buttons, especially white on mid-tone green, orange, yellow or light
  blue. Darken the fill or switch to dark text; do not shrink to "large text" to qualify.
- Text over photos, gradients and video. Measure against the lightest (or darkest) pixels the
  text can sit on, and add a solid or gradient scrim so the result does not depend on the image.
- Colors built from opacity (`text-black/50`, a disabled-looking but enabled state). The ratio
  depends on what is underneath; compute the composite color.
- Hover, active, visited, selected and error states; each state is its own pair.
- Dark mode. It is a second palette and needs a second pass; pure white on pure black passes but
  mid-gray borders and tinted surfaces commonly fail 3:1.
- Input borders. A text field whose only boundary is a light gray border fails 1.4.11; use a
  border of at least 3:1 or a clearly distinct fill.
- Links in body text distinguished only by color: see the color section.

Fix at the token level: define foreground and background tokens as tested pairs (`text-muted` on
`surface`, `on-primary` on `primary`), and never combine tokens outside those pairs. One token
fix clears hundreds of findings; per-component overrides come back.

Conformance is judged with the WCAG 2 ratio. Newer perceptual contrast models are useful design
input but are not part of WCAG 2.2; do not cite them in an audit or conformance report.

Automated tools compute contrast for plain text on solid backgrounds and report the rest as
"needs review": text over images, gradients, pseudo-elements and anything with opacity or blend
modes must be checked by hand with a color picker.

## Zoom, text resizing and reflow

| Requirement | Test | Criterion |
|---|---|---|
| Text can reach 200% with no loss of content or function | Browser zoom to 200% at a desktop width | 1.4.4 (AA) |
| Content reflows to a 320 CSS px wide viewport with no horizontal scrolling for reading | Window 1280 px wide, browser zoom 400% | 1.4.10 (AA) |
| Text spacing overrides do not clip or overlap: line height 1.5, paragraph spacing 2, letter spacing 0.12, word spacing 0.16 (times font size) | Apply those values with a user style or bookmarklet | 1.4.12 (AA) |
| Works in portrait and landscape | Rotate the device or emulator | 1.3.4 (AA) |
| Text is real text, not an image of text | Inspect | 1.4.5 (AA) |

Reflow exempts content that needs two dimensions: data tables, maps, diagrams, video, games and
toolbars. The page around them must still reflow, and the exempt part scrolls inside its own
container. A whole page that scrolls sideways because of one wide table fails.

Build rules that prevent most failures:

- Never ship `user-scalable=no` or `maximum-scale=1` in the viewport meta. The correct tag is
  `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Font sizes in `rem`, so the user's browser default font size is honored; `px` font sizes ignore
  it. Tailwind's type scale is already `rem`.
- No fixed heights on anything that contains text (buttons, cards, table rows, nav bars). Use
  `min-height` and padding. Fixed height plus `overflow: hidden` is the cause of clipped text
  under zoom and under text-spacing overrides.
- Truncation with ellipsis hides content at larger sizes; allow wrapping, or give a way to see
  the full text that is not hover-only.
- Sticky headers, footers and side panels consume the whole screen at 400%, where the viewport
  is 320 by about 256 CSS px. Un-stick them below a height or width breakpoint.
- Modals and drawers must scroll internally and keep their close button reachable at 400%.
- A responsive layout that is good at 320 px on a phone mostly passes reflow. The differences
  on desktop zoom: hover-dependent UI, the landscape aspect ratio, and "mobile" layouts that
  key off user-agent or touch capability instead of width.
- Horizontal carousels and tab strips must be scrollable by keyboard and not hide items without
  an indicator.

## Never color alone

Color may reinforce meaning; it may not be the only carrier (1.4.1, A). Color-vision deficiency
is common (a widely cited estimate is about 1 in 12 men and 1 in 200 women, varying by
population), and forced-colors modes replace author colors entirely.

| Pattern | Non-color cue to add |
|---|---|
| Links inside body text | Underline (default). Removing it requires 3:1 against surrounding text plus a non-color change on hover and focus; keeping the underline is simpler and safer |
| Form errors | Message text and an icon, not only a red border |
| Required fields | Text "(required)" or an explained asterisk |
| Status badges (green/yellow/red) | The status word, or a distinct icon shape per status |
| Selected tab, active nav item, toggled button | Underline, weight, fill-versus-outline or an icon, plus the ARIA state |
| Charts and legends | Direct labels, patterns or markers; see `dataviz` |
| Diffs, price up/down, stock | Plus/minus signs, arrows, words |
| Availability in calendars or seat maps | Shape, strike-through or text |

Checks: view the page in grayscale (DevTools vision-deficiency emulation offers achromatopsia)
and confirm every state is still distinguishable; then emulate forced colors.

Forced-colors mode (Windows contrast themes) rules: backgrounds, text and borders are replaced
with system colors; box shadows and gradient backgrounds are removed, while `url()` background
images stay. So: convey boundaries
with borders (a `border: 1px solid transparent` becomes visible), draw focus with `outline`, use
`currentColor` for SVG icon fills, and adjust the rare breakage inside
`@media (forced-colors: active)` using system color keywords such as `CanvasText`, `Canvas`,
`LinkText`, `ButtonText` and `Highlight`. Do not opt out with `forced-color-adjust: none` except
for content where color is the data, such as a color swatch.

## Captions, transcripts and audio description

| Media | Level A | Level AA |
|---|---|---|
| Prerecorded audio only (podcast) | Transcript (1.2.1) | |
| Prerecorded video with no audio | Text or audio alternative describing it (1.2.1) | |
| Prerecorded video with audio | Captions (1.2.2); audio description or a full text alternative (1.2.3) | Audio description (1.2.5) |
| Live video with audio (webinar, stream) | | Live captions (1.2.4) |

Practical defaults for a small team:

- Captions: generate with speech recognition, then edit. Unedited automatic captions do not meet
  the criterion when they are wrong about names, product terms, numbers and negations, which is
  where they are wrong. The edit pass adds speaker labels and meaningful non-speech sounds
  ("[applause]", "[error chime]").
- Captions differ from subtitles: captions are for viewers who cannot hear and include
  non-speech information.
- Deliver as a WebVTT file and a `<track>`, or the hosting platform's caption upload. Burned-in
  captions cannot be resized, restyled, searched or translated; use them only for social clips
  that autoplay muted.

```html
<video controls preload="metadata">
  <source src="/demo.mp4" type="video/mp4" />
  <track kind="captions" src="/demo.en.vtt" srclang="en" label="English" default />
</video>
```

- Transcript: publish on the same page or one link away. It also serves search and users who
  prefer reading; for podcasts it is the whole requirement.
- Audio description: avoid needing a separate track by writing the script so that the narration
  says what the screen shows ("click Export in the top right" instead of "click here"). A
  screen recording with silent on-screen steps needs description or a text alternative that
  lists the steps; the second is cheaper and satisfies level A, the first is what AA asks for.
- The player counts: controls keyboard-operable, named, with visible focus and a captions
  toggle. Verify an embedded third-party player the same way as first-party UI.
- Purely decorative background video with no information needs no captions, but it does need the
  motion rules below.

## Flashing, autoplay and motion

| Rule | Threshold | Criterion |
|---|---|---|
| No flashing | Nothing flashes more than 3 times in any one second | 2.3.1 (A) |
| Audio that starts by itself | If longer than 3 seconds: a pause/stop or independent volume control | 1.4.2 (A) |
| Moving, blinking or scrolling content that starts by itself, runs longer than 5 seconds, beside other content | A way to pause, stop or hide it | 2.2.2 (A) |
| Auto-updating content (tickers, live feeds) | Pause, stop, hide, or control frequency | 2.2.2 (A) |
| Motion triggered by interaction (parallax, scroll effects) | Can be disabled | 2.3.3 (AAA; do it anyway) |

Defaults:

- Never autoplay sound. Autoplay video only muted, with a visible pause button that is reachable
  early in the tab order, and do not loop indefinitely without that control.
- Auto-advancing carousels: avoid. If required, add a pause button, stop on hover and on focus,
  and never advance while focus is inside.
- Animated GIFs cannot be paused; serve them as muted `<video>` with controls or a play button.
- Honor `prefers-reduced-motion: reduce`. Under it, remove parallax, scroll-linked transforms,
  large-area zooms and slides, auto-playing background video and looping decoration; keep
  opacity fades and small state transitions, which carry meaning without triggering vestibular
  symptoms (dizziness, nausea). Replace movement with a cross-fade instead of deleting feedback.
- What triggers symptoms is size and relation to scrolling, not duration: a full-viewport
  parallax is worse than a small spinner. Scroll-jacking is a problem under any setting.
- JavaScript-driven animation must check the media query too
  (`window.matchMedia("(prefers-reduced-motion: reduce)")`); a CSS-only guard misses it.
- Flash risk in practice comes from video content, strobing hover effects and rapid error
  blinking. If a video might exceed the threshold, do not publish it without an analysis tool
  pass.

Animation implementation patterns are in `0x:frontend-foundations` (`animation.md`).

## Plain language and structure

Structure requirements that are testable: page language set with `<html lang>` (3.1.1) and
`lang` on passages in another language (3.1.2); a unique, descriptive `<title>` (2.4.2);
headings and labels that describe their content (2.4.6); link text that makes sense with its
surrounding sentence, and preferably alone (2.4.4).

Writing rules (rules of thumb; reading level itself is AAA):

- One `<h1>` naming the page, then headings in order without skipping levels. Screen-reader
  users navigate by heading list; a page with no headings or with styled `div`s is a wall.
- Lead with the point; one idea per paragraph; sentences mostly under 25 words.
- Use the common word, define unavoidable jargon and abbreviations on first use, and use the
  same word for the same thing everywhere.
- Steps as numbered lists, options as bulleted lists, comparisons as tables.
- Link text names the destination: "Download the March invoice", not "click here" or a bare URL.
  Screen readers list links out of context, and voice users speak them.
- Left-align text; avoid justified text, long passages in capitals or italics, and lines much
  beyond about 80 characters. Line height near 1.5 for body text.
- Numbers, dates and amounts in unambiguous formats; write the month as a word where locales
  differ.
- Error and empty states say what happened and what to do next.

Interface wording in general is covered by `0x:ui-ux-design` (`microcopy.md`).

## Cognitive load, consistency and time

| Requirement | What it means in the product | Criterion |
|---|---|---|
| Consistent navigation | Repeated nav appears in the same relative order on every page | 3.2.3 (AA) |
| Consistent identification | The same function has the same name and icon everywhere ("Search" is not "Find" elsewhere) | 3.2.4 (AA) |
| Consistent help | Help mechanisms (contact link, chat, help page) appear in the same relative place on each page where they exist | 3.2.6 (A, new in 2.2) |
| No change on focus or input | Focusing or changing a field does not navigate, submit or open a window without warning | 3.2.1, 3.2.2 (A) |
| Time limits adjustable | See `accessible-forms.md` | 2.2.1 (A) |

Beyond the criteria, the defaults that reduce load most:

- No time pressure that is not real. Countdown timers and "2 people are viewing this" banners
  harm users with anxiety and cognitive disabilities and are a deceptive-design risk as well.
- Do not put information the user needs into a toast that disappears. Auto-dismissing messages
  are for confirmations of things visible elsewhere; errors and anything actionable persist
  until dismissed.
- Autosave, undo and drafts beat confirmation dialogs; recovery is cheaper than vigilance.
- One primary action per screen; secondary actions visually quieter but still labelled.
- Do not rely on memory across steps: show what was chosen earlier, keep context visible.
- Icons carry text labels unless universally known; an unlabeled icon row is a guessing game.
- Open new tabs rarely, and say so in the link text when doing it.
- Keep layouts stable: content that shifts under the pointer or under a magnified viewport
  causes wrong activations.

## Checks

- Every text and background token pair is measured: 4.5:1 for text, 3:1 for large text, control
  boundaries, icons and focus rings; in light and dark themes.
- At 1280 px width and 400% zoom the main flows work with vertical scrolling only, nothing is
  clipped, and sticky elements leave room to read.
- With the text-spacing overrides applied, no text is cut off or overlapping.
- In grayscale and in forced colors, every state, error and status is still identifiable.
- Each video has edited captions and a transcript or description; nothing with sound autoplays;
  every moving element can be paused.
- With reduced motion enabled at the OS level, large movement is gone and the UI still gives
  feedback.
- The heading outline reads as a table of contents; the list of link texts makes sense alone.

## Ask the user

- **May brand colors be adjusted where they fail contrast?** A failing brand color on buttons or
  text cannot be fixed by code alone. Default: keep the brand hue, darken or lighten the shade
  used for text and fills until the pair passes, and keep the original for decoration.
- **Who edits captions and writes transcripts, and for which videos?** It is recurring editorial
  work. Default: every published product and marketing video gets edited captions; transcripts
  for anything over a minute.
- **Is an auto-playing hero video or carousel a requirement?** Both bring pause-control and
  motion obligations. Default: a static image, or muted video with a visible pause button that
  stays off under reduced motion.
- **What reading level is the audience?** It sets how hard to push on plain language. Default:
  write for a general adult audience, roughly lower-secondary reading level, for interface and
  help text.
- **Are urgency devices (countdowns, scarcity banners) part of the marketing plan?** They work
  against cognitive accessibility, and fake urgency can breach consumer-protection rules in many
  jurisdictions (`0x:privacy-compliance`). Default: none unless the deadline is real, and then
  with the limit stated in text.
