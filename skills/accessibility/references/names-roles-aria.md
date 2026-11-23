# Names, roles, states and ARIA

Read this when: a control, image, region or table must be understood by a screen reader or voice
control, markup carries ARIA that may be wrong, or a custom widget (tabs, menu, combobox, dialog)
is being built or replaced.

## The contract every interactive element must meet

Assistive technology reads the accessibility tree, not the pixels. Each interactive element needs
three things there (WCAG 4.1.2), and a native element supplies all three for free:

| Part | Question it answers | Native source | ARIA fallback |
|---|---|---|---|
| Role | What is it? | `<button>`, `<a href>`, `<input type>`, `<select>` | `role="..."` |
| Name | Which one? | text content, `<label>`, `alt`, `<legend>`, `<caption>` | `aria-labelledby`, `aria-label` |
| State/value | What is it doing now? | `checked`, `disabled`, `open`, `required` | `aria-expanded`, `aria-pressed`, `aria-selected`, `aria-checked`, `aria-current`, `aria-invalid` |

Decision order: native element, then a tested primitive that wraps ARIA, then hand-written ARIA.
Hand-written ARIA is a promise about keyboard behavior that the code must then keep; a
`role="button"` on a `div` announces "button" and does nothing on Enter or Space until both are
coded.

By stage: at Prototype, native elements, primitives and correct names are the whole job. At
Launch add live regions for every asynchronous status, the ARIA sweep below and a required alt
field wherever images are uploaded. Hand-built patterns that no primitive covers wait for Scale,
when testing on two screen-reader engines is affordable.

### How the name is computed

The first source that yields text wins, so a later source is silently ignored:

1. `aria-labelledby` (ids, space-separated; can reference hidden elements and the element itself)
2. `aria-label`
3. Native labeling: `<label>`, `alt`, `<legend>`, `<caption>`, or the element's text content
4. `title` or `placeholder` (last resort; do not rely on either)

Consequences that cause most real bugs:

- `aria-label` on a button replaces its visible text. If they differ, voice-control users who say
  the visible words get nothing (WCAG 2.5.3 Label in Name). Rule: the accessible name contains the
  visible label, word for word, preferably at the start. Add context after it
  (`aria-label="Delete invoice 1042"` on a button that shows "Delete").
- `aria-label` and `aria-labelledby` are ignored or unreliable on elements with no role (`div`,
  `span`, `p`). Naming is defined for interactive elements, landmarks, images and widgets.
- `aria-label` text is not translated by some browser translation tools and is invisible to
  sighted users. Prefer visible text, then `aria-labelledby` pointing at visible text.
- `aria-describedby` adds a description read after the name and role, often after a pause, and
  some users turn descriptions off. Never put the only identifying text there.
- Icon-only button: name goes on the button, the icon is hidden.

```tsx
<button type="button" aria-label="Close dialog">
  <XIcon aria-hidden="true" />
</button>
```

An equivalent that survives translation is visually hidden text inside the button (Tailwind
`sr-only`). Repeated controls in lists ("Edit", "Edit", "Edit") need distinguishing names; a list
of links or buttons is often read out of context.

### States that must be kept in sync

| Situation | Attribute | Trap |
|---|---|---|
| Button shows or hides content | `aria-expanded` set to `true` or `false` on the button | Putting it on the panel; omitting it when collapsed |
| Toggle button | `aria-pressed` | Also changing the label ("Mute" to "Unmute"): pick one, state or label |
| On/off setting | `role="switch"` + `aria-checked`, or a native checkbox | |
| Current page or step in nav | `aria-current="page"` or `"step"` | Using `aria-selected`, which belongs to tabs, options, grid cells |
| Unavailable control | `disabled` (not focusable, not announced in tab order) or `aria-disabled="true"` (stays focusable, the click handler must refuse) | `aria-disabled` alone does not block activation |
| Content loading | `aria-busy="true"` on the region being replaced | Leaving it true after an error |

State must change in the same render as the visual change. A React component that toggles a class
but not `aria-expanded` is the most common cause of "the screen reader says collapsed when it is
open".

## Alt text

Write the alt by what the image does in context, not by what it shows:

| Image | Alt |
|---|---|
| Decorative, or repeats adjacent text | `alt=""` (empty, attribute present) |
| Informative (photo, illustration carrying content) | The information a sighted user takes from it, one sentence |
| Functional (inside a link or button with no other text) | The destination or action: "Home", "Download report" |
| Image of text (logo) | The text: "Acme" |
| Chart, diagram, screenshot with data | Short alt naming it, plus the data or conclusion in nearby text or a table |
| User-uploaded | Ask for alt at upload; fall back to a neutral name ("Photo uploaded by Dana"), never the file name |

Rules that differ from generalist habit:

- A missing `alt` can make screen readers read the file name or URL; `alt=""` makes them skip the
  image. Both are deliberate choices; only the missing attribute is always wrong.
- Do not start with "Image of" or "Picture of"; the role is already announced.
- An image link whose image has `alt=""` and no text is an empty link, one of the most common
  failures on the web.
- Inline SVG: decorative gets `aria-hidden="true"`; meaningful gets `role="img"` plus
  `aria-label` (or a `<title>` referenced with `aria-labelledby`). Icon fonts and CSS background
  images have no alt; pair them with real text.
- Do not hide content from assistive technology with `aria-hidden="true"` if it contains or is a
  focusable element: focus lands on something that is announced as nothing. Use `inert` or
  `hidden` to remove a subtree from both focus and the tree.
- Emoji used as an icon gets `role="img"` and `aria-label`, or `aria-hidden="true"` next to text.
- Alt for model-generated or CMS images is content: keep it in the CMS schema as a required
  field with an explicit "decorative" checkbox, so empty is a decision and not an omission.

## Cleaning up existing ARIA

Bad ARIA is worse than none because it overrides correct native semantics. Sweep in this order:

| Find | Why it is wrong | Fix |
|---|---|---|
| `role="button"` on `<button>`, `role="navigation"` on `<nav>`, `role="list"` on `<ul>` | Redundant noise (one exception: `role="list"` restores list semantics Safari drops when `list-style: none`) | Delete |
| `<div onClick>` or `<span onClick>` | No role, no focus, no keyboard | `<button type="button">`, or `<a href>` if it navigates |
| `<a>` without `href`, or `<a href="#">` used as a button | Not focusable, or wrong role | `<button>` |
| `aria-label` that repeats or contradicts visible text | Overrides the text, breaks voice control | Delete, or make it start with the visible text |
| `aria-hidden="true"` on or around focusable elements | Ghost tab stops | Remove, or use `inert` |
| `role="presentation"`/`"none"` on a focusable element | Browsers ignore it; intent unclear | Remove |
| `role="menu"` on site navigation | Promises arrow-key menu behavior, puts screen readers in a mode where links misbehave | Plain list of links in `<nav>`; disclosure button for dropdowns |
| `aria-labelledby`/`aria-describedby`/`aria-controls` pointing at ids that do not exist or repeat | Silent failure | Generate ids with `useId`; check they render |
| Interactive inside interactive (`<a><button>`, clickable card containing links) | Role and focus are undefined | One control per element; stretch a link with a pseudo-element for card clicks |
| Children without the required parent (`role="tab"` outside `tablist`, `option` outside `listbox`) | Browsers ignore the role or expose it without its set, so announcements break | Complete the pattern or remove it |
| `role="application"` | Turns off screen-reader browse commands | Remove unless the region is a true canvas-style app |
| `aria-live` on large or many containers | Constant chatter | One or two dedicated regions |
| `title` as the only name or as a tooltip | Not shown on touch or keyboard | Visible text or a real tooltip |
| `tabindex` greater than 0 | Jumps the tab order | Remove; fix DOM order |

Check with the browser DevTools accessibility pane: select the element and read its computed
role and name. Empty name on an interactive role is a bug every time. In tests, Playwright's
`getByRole('button', { name: 'Save' })` passes only when role and name are both right, which makes
role-based locators a free regression check.

## Widget patterns

Do not hand-build these when a primitive exists (see the next section). When reviewing or fixing
one, hold it to this table. The keyboard half of each pattern is not optional: the role tells the
user which keys to expect.

| Widget | Roles and attributes | Keyboard | Common mistake |
|---|---|---|---|
| Disclosure (show/hide, nav dropdown, accordion) | `<button aria-expanded aria-controls>`; panel is plain content | Enter/Space toggles; Tab moves into content | Building it as a menu |
| Tabs | `role="tablist"` > `role="tab"` with `aria-selected`, `aria-controls`; `role="tabpanel"` with `aria-labelledby` | One tab stop for the list (roving `tabindex`); Left/Right move, Home/End; Tab goes into the panel | Every tab in the tab order; using tabs for navigation between URLs (that is a nav with `aria-current`) |
| Menu (actions) | Trigger `<button aria-haspopup="menu" aria-expanded>`; `role="menu"` > `role="menuitem"` / `menuitemcheckbox` / `menuitemradio` | Enter/Space/Down opens and focuses first item; Up/Down move; Esc closes and returns focus to trigger; Tab closes; type-ahead | Links, inputs or other content inside a menu |
| Combobox (autocomplete) | `<input role="combobox" aria-expanded aria-controls aria-autocomplete>`; popup `role="listbox"` > `role="option" aria-selected`; active option via `aria-activedescendant` | DOM focus stays in the input; Down/Up move the active option; Enter selects; Esc closes, then clears | Moving real focus into the list; not announcing result count; old ARIA 1.1 wrapper markup |
| Modal dialog | `<dialog>` opened with `showModal()`, or `role="dialog" aria-modal="true"`; name via `aria-labelledby` to the heading | Focus moves in, is contained, Esc closes, focus returns to the trigger | `aria-modal` without making the background inert; no name |
| Confirmation that interrupts | `role="alertdialog"` with `aria-describedby` to the message | As dialog; initial focus on the least destructive action | Using it for ordinary forms |
| Tooltip | Trigger has `aria-describedby` to an element with `role="tooltip"` | Appears on focus and hover; Esc dismisses; stays while hovered | Essential or interactive content in a tooltip; hover only |
| Listbox / custom select | `role="listbox"` > `role="option"` | Arrows, Home/End, type-ahead | Rebuilding `<select>` for styling alone |

Decision rules:

- Tabs activate on arrow focus when showing the panel is instant; require Enter/Space when the
  panel triggers a fetch, so arrowing across does not fire five requests.
- A tab panel with no focusable content gets `tabindex="0"` so keyboard users can reach and
  scroll it.
- A dropdown of links is a disclosure. Reserve `menu` for commands such as a row's "..." actions.
- Native `<dialog>` with `showModal()` supplies the top layer, background inertness, Esc and
  focus return. Use it or a primitive; a `div` with `role="dialog"` supplies none of that, and
  neither does a `<dialog>` opened with `show()` or the `open` attribute, which is non-modal.
- Native `<details>/<summary>` covers simple disclosures; the `popover` attribute covers
  non-modal overlays with light dismiss. Popover sets no role: add one that fits the content.

## Live regions

Use a live region when content changes without a page load and focus does not move there:
"Saved", "3 results", form-level errors, cart count, background job finished (WCAG 4.1.3).

| Need | Markup | Behavior |
|---|---|---|
| Routine status | `role="status"` (polite, atomic); `<output>` has this role natively | Waits for current speech to finish |
| Urgent, time-sensitive | `role="alert"` (assertive, atomic) | Interrupts; use for errors that block the user, session expiry |
| Chat or log | `role="log"` | Polite, appends |

Rules that make them work:

- The region must already be in the DOM, and exposed, before the text changes. Render an empty
  container at page load and write text into it later. A region inserted together with its text
  is announced unreliably; one under `display: none` is not announced at all.
- Change text, not structure. Screen readers announce text nodes; an icon swap says nothing.
- Setting the same string twice announces once. Clear the region, then set it on the next tick,
  when the same message can legitimately repeat.
- Debounce frequent updates (search-as-you-type result counts: announce after typing pauses).
  Never announce a countdown every second.
- Do not combine moving focus and a live announcement for the same event: the focus change
  interrupts the announcement. Pick one.
- One polite region and one assertive region mounted in the root layout, driven by an
  `announce(message)` helper, is enough for most applications.
- Toasts: `role="status"`, text that makes sense alone, and no action that exists only in the
  toast. If a toast carries "Undo", the same action must be reachable another way, and the toast
  must not disappear before a keyboard or screen-reader user can reach it.

```tsx
// Mounted once in the root layout; text is set later by the announce helper.
<div role="status" className="sr-only">{politeMessage}</div>
<div role="alert" className="sr-only">{assertiveMessage}</div>
```

## Replacing a custom widget with a tested primitive

Rebuilding focus management, type-ahead, dismissal and screen-reader quirks is weeks of work per
widget and regresses silently. Default: replace, do not repair, any hand-built dialog, menu,
combobox, select, tabs, popover, tooltip or slider.

| Situation | Choose |
|---|---|
| The native element does the job (`<select>`, `<dialog>`, `<details>`, checkbox, radio, `<input type="date">`) | Native, styled |
| React project, own styling (house default) | Radix-style headless primitives; React Aria components where date pickers, comboboxes or internationalized input are needed |
| Project already has a component library | Its own primitive; do not add a second library |
| No primitive covers it (tree grid, canvas editor) | Follow the ARIA Authoring Practices pattern and budget screen-reader testing on at least two engines |

Procedure:

1. Inventory: search for `onClick` on non-interactive tags, `role=`, `tabIndex`, `aria-`, and
   hand-rolled `keydown` handlers. Each hit is a candidate.
2. Replace the highest-traffic and highest-severity widgets first: dialogs and menus in core
   flows before decorative tooltips.
3. Keep the primitive's parts intact. Radix-style dialogs expect a title part; if the design has
   no visible title, render it visually hidden instead of deleting it. Wrapping a trigger in a
   custom component requires that component to forward its ref and spread props to a real
   `<button>`, or the trigger loses role, state and keyboard handling.
4. Delete the old ARIA and key handlers rather than layering the primitive on top.
5. Verify with keyboard and one screen reader, then add a role-based end-to-end test.

A primitive guarantees the pattern, not the content: names, labels, heading text and contrast
remain the application's job.

## Data tables

Use `<table>` for anything with row and column relationships; screen readers then announce
headers as the user moves cell to cell and offer table navigation commands.

```html
<table>
  <caption>Invoices, March 2026</caption>
  <thead>
    <tr><th scope="col">Invoice</th><th scope="col">Status</th><th scope="col">Amount</th></tr>
  </thead>
  <tbody>
    <tr><th scope="row">1042</th><td>Paid</td><td>$120.00</td></tr>
  </tbody>
</table>
```

- `<caption>` names the table; a heading above it does not, unless tied with `aria-labelledby`.
- Column headers get `scope="col"`. The cell that identifies the row (name, id) is a
  `<th scope="row">`, which is the single change that most improves a table by ear.
- Tables with headers spanning two levels need `headers`/`id` associations; simplify the table
  into two tables first if possible, since support for complex associations is uneven.
- Sortable column: a `<button>` inside the `<th>`, and `aria-sort="ascending|descending"` on the
  currently sorted `<th>` only.
- Row actions need unique names ("Delete invoice 1042").
- Setting `display: block`, `flex` or `grid` on table elements for responsive layouts can strip
  table semantics in some browsers. Keep table display and wrap the table in a scroll container
  with `tabindex="0"`, `role="region"` and an `aria-label`, so keyboard users can scroll it.
- Virtualized or `div`-based tables need the full role set (`table`, `rowgroup`, `row`,
  `columnheader`, `rowheader`, `cell`) plus `aria-rowcount` and `aria-rowindex` when rows are
  not all in the DOM.
- `role="grid"` is for spreadsheet-like widgets with cell-by-cell arrow navigation. On a
  read-only table it removes normal reading commands and adds obligations; do not use it for
  styling or because a library defaults to it without the keyboard model.
- Never use a table for layout; if one exists, `role="presentation"` on it until it is removed.

## Checks

- Every interactive element shows a role and a non-empty name in the DevTools accessibility pane.
- Tabbing through the page with a screen reader on, each stop is announced as name, role, state,
  and the name matches the visible label.
- No `aria-hidden="true"` subtree contains a focusable element; every id referenced by ARIA
  exists exactly once.
- Each status change that does not move focus is spoken once, and only once.
- Tables announce column and row headers when moving between cells.

## Ask the user

- **Who writes alt text for content images?** It is editorial content, not code. Default: the
  person who uploads the image, enforced by a required field with a "decorative" option.
- **May a custom widget be replaced with a primitive even if it changes look or behavior
  slightly?** Replacement is cheaper and safer than repair. Default: yes, match the design as
  closely as the primitive allows and flag differences.
- **Which screen reader and browser pairs must work?** It sets how much quirk-chasing is
  justified. Default: VoiceOver with Safari and NVDA with a Chromium browser or Firefox.
- **Is user-generated content (uploads, rich text) in scope?** It decides whether to build alt
  prompts and heading controls into editors. Default: prompt for alt, do not block publishing.
