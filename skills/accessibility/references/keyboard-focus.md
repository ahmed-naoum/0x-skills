# Keyboard, focus and pointer access

Read this when: a flow must work without a mouse, focus disappears or lands in the wrong place
(route change, modal, deleted item), a focus ring or skip link is missing, or interactive targets
need sizing and drag, hover or gesture interactions need an alternative.

## The keyboard contract

Keyboard support is the base layer for screen readers, switch devices, voice control and power
users. Every action available by pointer must be available by keyboard (WCAG 2.1.1), focus must
never get stuck (2.1.2), the order must follow meaning (2.4.3), and the focused element must be
visible (2.4.7) and not hidden behind other content (2.4.11).

| Key | Expected effect |
|---|---|
| Tab / Shift+Tab | Next or previous interactive element; composite widgets are one stop |
| Enter | Activates links and buttons; submits a form from a text field |
| Space | Activates buttons, toggles checkboxes, opens selects; never scrolls when on a control |
| Arrow keys | Move inside a composite: radio group, tabs, menu, listbox, slider, grid |
| Esc | Closes the topmost overlay and returns focus to what opened it |
| Home / End | First or last item in a composite |

Tab moves between widgets, arrows move within them. Putting every menu item, tab or grid cell in
the tab order is the usual error; it turns a 10-stop page into a 60-stop page.

By stage: at Prototype, native elements, primitives and an untouched focus ring give most of this
for free. At Launch add the skip link, route-change focus, target sizes, drag and hover
alternatives, and a keyboard-only run of every core flow. Per-component keyboard tests are Scale
work.

Native elements implement this already. A `div` made clickable needs `role`, `tabindex="0"`, an
Enter handler, a Space handler with `preventDefault()` to stop page scroll, disabled handling and
focus styling. Use `<button type="button">` for actions and `<a href>` for navigation; the choice
matters because users expect Space on buttons and "open in new tab" on links.

Single-character shortcuts (press `s` to search) fire when a voice-control user dictates. If any
exist, they must be remappable, disableable, or active only while the relevant component has
focus (2.1.4). Default: require a modifier key, or skip single-key shortcuts until Scale.

## Visible focus

Never remove the outline without a replacement. The default for a design system:

```css
:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
```

- Use `:focus-visible`, not `:focus`: it shows the ring for keyboard use and for text fields, and
  not on mouse clicks of buttons, which removes the reason designers ask to delete rings.
- Prefer `outline` to `box-shadow`. Forced-colors (high-contrast) modes drop box shadows, so a
  shadow-only ring vanishes for exactly the users who need it. If the design uses a ring shadow,
  add `outline: 2px solid transparent`; the transparent outline becomes visible in forced colors.
- The indicator needs 3:1 contrast against the colors next to it (1.4.11). One ring color rarely
  works on both light and dark surfaces: use a two-tone ring (dark outline plus light offset gap)
  or theme tokens per surface.
- A ring 2 CSS px thick around the whole control, with 3:1 between focused and unfocused states,
  also meets the stricter AAA appearance criterion (2.4.13); adopt it as the house style since it
  costs nothing extra.
- `overflow: hidden` on a parent clips outlines. Use `outline-offset` with a negative value
  inside clipped containers, or pad the container.
- Focus not obscured (2.4.11, AA): sticky headers, cookie banners and chat widgets must not fully
  cover the focused element. Set `scroll-padding-top` (and bottom, if a sticky footer exists) on
  the scroll container to the height of the sticky bar, and make banners dismissible or
  non-overlapping.

## Tab order and skip links

Order comes from the DOM. Keep DOM order equal to visual reading order; fix order in markup, not
with `tabindex`.

| `tabindex` | Use |
|---|---|
| absent | Native interactive elements, already focusable |
| `0` | Custom widget that must be a tab stop; scrollable region with no focusable content |
| `-1` | Target of programmatic focus (headings, `main`, error summary), and inactive items of a roving-tabindex composite |
| positive | Do not use: it creates a second order ahead of the whole page and breaks with every new element |

Traps:

- CSS `order`, `flex-direction: row-reverse`, grid placement and absolute positioning change the
  visual order only. A sidebar rendered first in the DOM but shown on the right is tabbed first.
- Off-screen or collapsed content (closed drawers, hidden carousel slides, collapsed mobile menu)
  stays tabbable unless it is `display: none`, `hidden` or `inert`. Symptom: focus disappears for
  several Tab presses. Fix: `inert` on the closed container.
- Infinite scroll puts the footer out of reach. Offer a "Load more" button, or keep nothing
  important after the feed.
- Third-party embeds (chat, video, maps) add tab stops and sometimes traps. Test them; lazy-mount
  behind a button when they trap.

Skip link (2.4.1): the first focusable element on every page, hidden until focused, pointing at
the main region. Landmarks (`header`, `nav`, `main`, `footer`, labelled `aside`) serve
screen-reader users; the skip link serves sighted keyboard users, so both are needed.

```tsx
<a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4">
  Skip to main content
</a>
{/* ... header and navigation ... */}
<main id="main" tabIndex={-1}>{children}</main>
```

`tabIndex={-1}` on the target makes focus actually move there in every browser, not only the
scroll position. Put the link and the `main` wrapper in the root layout so no page can omit them.
Applications with a long sidebar benefit from a second link ("Skip to navigation" or "Skip to
results") but one is the requirement.

## Target size and spacing

| Rule | Size | Status |
|---|---|---|
| WCAG 2.5.8 Target Size (Minimum) | 24 by 24 CSS px, or smaller with enough spacing | AA in WCAG 2.2: the floor |
| WCAG 2.5.5 Target Size (Enhanced) | 44 by 44 CSS px | AAA; the house default for touch |
| Platform guidance | About 44 pt (iOS) and 48 dp (Android) | What mobile users are used to |

Default: primary and touch-reachable controls 44 by 44 CSS px; dense desktop UI (table row
actions, toolbars) no smaller than 24 by 24 with spacing. In Tailwind's default spacing scale
that is `min-h-11 min-w-11` and `min-h-6 min-w-6` (old Tailwind versions lack these utilities).

How 2.5.8 is measured, since audits argue about it:

- The target is the clickable area, not the icon. A 16 px icon inside a button with padding to
  24 px passes.
- Spacing exception: an undersized target passes if a 24 px diameter circle centered on it does
  not intersect another target or another undersized target's circle. Two 20 px icons need at
  least 4 px between them.
- Other exceptions: links inside a sentence or block of text, controls whose size the browser
  sets (unstyled native controls), targets where another control on the page does the same thing
  at full size, and cases where the size is essential (map pins).

Enlarge without changing the visual design by padding or a pseudo-element:

```css
.icon-button { position: relative; }
.icon-button::after { content: ""; position: absolute; inset: -10px; }
```

Check that enlarged hit areas do not overlap neighbors; overlapping invisible areas cause the
wrong control to fire. Common failures: close "x" buttons, pagination numbers, checkbox and radio
inputs without a clickable label, icon rows in tables, tag-remove buttons, carousel dots.

## Focus after route changes and content changes

A full page load resets focus to the top and the screen reader announces the new title. Client
routing does neither by itself: the user hears nothing and focus stays on a link that may no
longer exist.

On every client-side navigation, three things must happen:

1. `document.title` changes to a unique, specific title (2.4.2), front-loaded: "Billing -
   Settings - Acme", not "Acme | Settings | Billing".
2. The change is announced, by a live region or by moving focus.
3. Focus lands somewhere sensible at the top of the new content, so the next Tab goes into the
   new page, not the old navigation's remains.

Frameworks differ in how much they do. Next.js ships a route announcer (it reads the title, then
the `<h1>`) and resets scroll, but where focus ends up has varied by router and version. Do not
assume, test it: navigate by keyboard with a screen reader on, confirm the page is announced
once, and that the next Tab lands in the new content. If the framework does not handle it, the
default is to focus the page's `<h1 tabIndex={-1}>` after
navigation (a heading announces the page name and puts the reading position at the start of
content). Do not focus the `body` or the first link.

For content inserted or removed without navigation:

| Event | Where focus goes |
|---|---|
| Disclosure opens inline | Stays on the trigger; content follows it in the DOM |
| Modal or drawer opens | Into it (see below) |
| "Load more" appends items | First new item, or stay on the button with a status announcement of the count |
| Item deleted from a list | Next item, else previous item, else the list heading or an empty-state message |
| Inline edit saved or cancelled | Back to the element that started the edit |
| Step of a wizard changes | The new step's heading |
| Background update (toast, new message) | Does not move; announce with a live region |
| Filter or sort applied | Stays on the control; announce the result count |

When the focused element is removed from the DOM, hidden or disabled, focus is lost: browsers
reset it to `body` (some leave it on the dead element), the next Tab starts from the top of the
page, and a screen-reader user is lost. This is the
most common focus bug in React applications, typically after delete, after a button swaps for a
spinner, or when a list re-renders with new keys. Detect it while reproducing:

```js
document.addEventListener("focusin", (e) => console.log("focus:", e.target));
// When lost: document.activeElement === document.body
```

Move focus in an effect after the DOM has updated, not in the click handler before render.
Keep stable `key`s so React does not remount the focused node. A button that becomes "loading"
keeps focus if it uses `aria-disabled` instead of `disabled`.

## Modals: contain focus, then give it back

A modal must do five things: move focus in on open, keep Tab and Shift+Tab inside, hide the rest
of the page from assistive technology, close on Esc, and return focus to the trigger on close.
Native `<dialog>` opened with `showModal()` and Radix-style dialog primitives do all five; use
one. `aria-modal="true"` alone does none of the focus work.

Decisions the primitive leaves open:

- **Initial focus.** Default is the first focusable element. Override for: destructive
  confirmations (focus Cancel, so Enter does not delete), long content (focus the heading or the
  dialog container with `tabindex="-1"`, so reading starts at the top, not at a footer button),
  and forms (first field).
- **Return target.** The trigger. If the trigger no longer exists (the dialog deleted its row),
  send focus to the logical neighbor, per the table above.
- **Background.** Hand-built overlays must set `inert` on everything outside. A focus trap
  implemented only with Tab key listeners still lets screen-reader browse commands and touch
  exploration reach the page behind.
- **Close affordances.** A visible, named close button plus Esc. Clicking the backdrop is extra,
  never the only way.
- **Scroll.** Lock background scroll; the dialog itself must scroll when content exceeds the
  viewport at 200% zoom.
- **Stacking.** A dialog opened from a dialog returns focus, on close, to the control inside
  the first dialog that opened it. Avoid more than two levels.

Non-modal overlays (popovers, dropdowns, comboboxes, toasts) do not trap focus. They close on Esc
and when focus leaves, and tabbing out continues from the trigger's position. Trapping focus in a
non-modal popover is as wrong as not trapping it in a modal. Cookie banners should not be modal
unless a choice is truly required before use; if non-modal, place them first in the DOM so
keyboard users meet them early.

## Alternatives to drag, hover and gestures

| Interaction | Requirement | Alternative to ship |
|---|---|---|
| Drag and drop (reorder, kanban, file drop) | 2.5.7 Dragging Movements (AA): a single-pointer way without dragging; 2.1.1: a keyboard way | "Move up/down" buttons or a "Move to..." menu on each item; a file `<input>` beside the drop zone |
| Slider | Same | Clickable track, arrow keys via native `<input type="range">`, and a number field for precision |
| Swipe, pinch, multi-finger (carousel, map) | 2.5.1 Pointer Gestures: single tap or click alternative | Previous/next and zoom buttons |
| Shake or tilt | 2.5.4 Motion Actuation | A button; a setting to turn motion off |
| Hover or focus reveals content (tooltip, submenu, card preview) | 1.4.13: dismissible without moving the pointer (Esc), hoverable (pointer can move onto it), persistent until dismissed | Open on focus as well as hover; never the only place information lives |
| Row actions that appear on hover | Keyboard and touch cannot hover | Show on `:focus-within` and always under `@media (hover: none)`, or keep them visible |
| Action on press | 2.5.2 Pointer Cancellation | Act on `click` (up event), so sliding off cancels; `mousedown`/`pointerdown` actions only when essential |

A keyboard drag mode (Space to lift, arrows to move, Space to drop, Esc to cancel, each step
announced through a live region) satisfies the keyboard requirement and is what drag libraries
with a keyboard sensor provide. It does not satisfy 2.5.7 for a pointer user who cannot drag,
which is why explicit move buttons or a menu are the default: one alternative covers both.

## Switch and voice-control users

Neither group needs special code; both are served, or locked out, by ordinary semantics.

- **Switch access** scans focusable elements one at a time and activates with a single switch.
  Every unnecessary tab stop costs seconds. Keep composites to one stop, provide skip links, keep
  destructive actions away from the default scan path, and never require holding, double
  activation or timing. Time limits are the main blocker (see `accessible-forms.md`).
- **Voice control** (Dragon, Voice Control on Apple platforms, Voice Access on Android and
  Windows) activates controls by spoken name ("click Save") or by numbered overlays drawn on
  elements the accessibility tree marks as interactive. A clickable `div` gets no number and no
  name. Requirements: real buttons and links, an accessible name that contains the visible label
  (2.5.3), icon-only buttons named with the word a user would guess ("Search", not "Magnifier"),
  unique names among nearby controls, and no single-key shortcuts that dictation can trigger.
- Both groups rely on a pointer-cancellation-safe `click` and on nothing depending on hover.

Main trap at the expert level: an `aria-label` that improves the screen-reader phrase while
dropping the visible word ("Submit" shown, `aria-label="Send application form"`). The screen
reader is fine and voice control stops working.

## Checks

- Unplug the mouse: complete sign-up, the core task, and checkout or upgrade using only the
  keyboard. Every control reachable, every overlay closable with Esc, no dead ends.
- The focus ring is visible at every stop, on every background, in light and dark themes, and is
  never hidden behind a sticky header or banner.
- First Tab on each page reveals the skip link, and activating it puts the next Tab inside main.
- After each route change, delete, modal close and wizard step, `document.activeElement` is not
  `body`.
- No interactive target is under 24 by 24 CSS px without spacing; primary touch targets are 44.
- Each drag, swipe and hover interaction has a click or tap alternative that does the same job.
- An end-to-end test presses Tab through one core flow and asserts focus with `toBeFocused()`.

## Ask the user

- **May focus rings be restyled but not removed?** Designers often ask to remove them. Default:
  keep a 2 px ring with 3:1 contrast, shown with `:focus-visible` so mouse clicks stay clean.
- **Is 44 px the target size for touch, or only the 24 px WCAG AA floor?** Larger targets cost
  density. Default: 44 for primary and mobile controls, 24 with spacing in dense desktop tables.
- **Are keyboard shortcuts wanted?** They help power users and can hurt voice users. Default:
  none with a single character; modifier-based shortcuts with a visible list when added.
- **Which alternative to drag fits the product: move buttons or a "Move to" menu?** It is a
  design decision with layout cost. Default: a menu on each item, since it scales to long lists.
