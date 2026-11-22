# Visual design: type, color, spacing and layout

Read this when: a screen has to look right or currently looks amateur; when choosing type, color, spacing, icons or a brand kit; when laying out tables, filters and dashboards.

## What actually makes a screen look amateur

Amateur screens are rarely ugly in one place. They are inconsistent everywhere. Critique in this order, because earlier items cause most of the damage and later items cannot rescue them.

| # | Symptom to name | Fix |
|---|---|---|
| 1 | Everything has the same weight; no element wins | Pick one primary action and one focal point per screen; demote the rest |
| 2 | Spacing is arbitrary (13px here, 22px there); related things are no closer than unrelated things | Snap to the spacing scale; space inside a group must be smaller than space between groups |
| 3 | More than about four text sizes or three weights on one screen | Collapse to the type scale; use color and weight for hierarchy before size |
| 4 | Edges almost line up | Put everything on shared left edges and a column grid; "almost aligned" reads as broken |
| 5 | Pure black text on pure white, gray text on colored backgrounds | Near-black text; on a colored background use a tint of that hue, not gray |
| 6 | Borders around everything, boxes inside boxes | Separate with space first, then background tint, then a hairline border; rarely all three |
| 7 | Many accent colors, saturated everywhere | One accent used only for the primary action, links and selection; everything else neutral |
| 8 | Mixed radii, mixed shadow styles, mixed icon sets | One radius scale, one shadow scale with one light direction, one icon set |
| 9 | Lines of text run the full width of a wide screen | Cap prose at 45 to 75 characters |
| 10 | Centered paragraphs, justified text, ALL CAPS sentences | Left-align anything longer than two lines; caps only for short labels with added letter spacing |
| 11 | Labels shout, data whispers | Labels small and muted, values larger and darker |
| 12 | Stock illustrations and gradients fill the gaps | Remove; let type, spacing and real content carry the screen |

When reporting a critique, name the element, the rule it breaks and the token it should use ("card padding is 14px; use space-4, 16px"). "Feels cluttered" is not a finding.

By stage: at Prototype, keep the kit's look, set the tokens once and fix only rows 1 to 4, which carry most of the effect. At Launch, run the whole table on every screen between signup and first value and write the one-page brand kit. Custom typefaces, illustration and a density toggle wait for Scale.

## Hierarchy: one primary action

- **Squint test.** Blur the screen or view it at 25% zoom. The thing that still stands out must be the thing the user came to do. If two things stand out, one must be demoted.
- **Button ladder.** One filled (primary) button per view or per dialog. Secondary actions are outlined or tinted, tertiary are text-only. Destructive actions are not primary by default: a red filled button belongs only in the confirmation step, not on the list row.
- **Three text emphasis levels are enough**: primary (near-black), secondary (a mid gray that still passes 4.5:1 on every surface it sits on), and tertiary for disabled text and decoration only. Add a level only when a real screen needs it.
- **De-emphasize instead of emphasizing.** When the important item does not stand out, make its neighbors quieter rather than making it louder. Loudness escalates; quiet does not.
- **Order of tools**: position and size of the region, then weight, then color, then font size. Bigger text is the last resort.
- **Semantics are separate from looks.** An `h2` can be visually small; choose the heading level by document structure and the size by hierarchy.

## Type: scale, measure, rhythm

Default scale for product UI, in px on a 16px root: **12, 14, 16, 18, 20, 24, 30, 36, 48**. A product screen normally uses four of these: 12 for captions and meta, 14 for dense UI text, 16 for body and inputs, 20 to 24 for the page title. Marketing pages reach for 36 and above; app screens almost never should.

| Setting | Value | Reason |
|---|---|---|
| Body size | 16px for reading; 14px acceptable for dense app UI on desktop | Smaller text tires readers and excludes low-vision users; keep 12px for short secondary labels, never for sentences |
| Input text on mobile | At least 16px | iOS Safari zooms the page when a focused input has a smaller font size |
| Line length | 45 to 75 characters; `max-width: 65ch` on prose | Longer lines lose the reader on the return sweep |
| Line height | About 1.5 for body, 1.2 to 1.3 for 20 to 30px, 1.05 to 1.15 for display sizes | Line height shrinks as size grows |
| Paragraph spacing | 0.75 to 1 times the body line height | Smaller looks like a line break, larger breaks the block |
| Heading spacing | More space above than below (about 2:1) | A heading must attach to the text it introduces |
| Letter spacing | Slightly negative on large headings, slightly positive (0.04 to 0.08em) on small all-caps labels | Default tracking is tuned for body sizes |
| Weights | Two, sometimes three: 400, 500 or 600, and 700 only for large headings | Below 400 fails on low-density screens |
| Numbers in columns | `font-variant-numeric: tabular-nums` | Digits align and do not jitter when values update |

Vertical rhythm on screens is practical, not typographic: make every line height and every vertical gap a multiple of 4px. A full baseline grid is not worth the effort in product UI.

Sizes are specified in `rem` so user font-size settings scale the interface. Fluid type with `clamp()` suits marketing headings; keep app UI on fixed steps so density is predictable. Implementation belongs to `0x:frontend-foundations`.

### Choosing and pairing typefaces

- **Default: one sans family** with a wide weight range, ideally variable. Proven screen faces: Inter, Geist, IBM Plex Sans, Source Sans 3, or the platform stack via `system-ui`. The system stack costs zero bytes and looks native, but looks different on each OS; pick it for tools and admin, pick a web font when brand consistency matters.
- **What to check before committing**: a tall x-height (legible at 12 to 14px); distinguishable `I l 1` and `O 0`; tabular figures available; at least 400, 500 or 600, and 700; the character sets for every language the product ships in; a license that covers web embedding and, if needed, app embedding and self-hosting (the faces named above are openly licensed; read the license of any other before shipping it).
- **Self-host the font files.** Loading them from a third-party font host sends every visitor's IP address to that host, which has drawn privacy claims in the EU, and adds a connection before text can render. Loading strategy belongs to `0x:web-performance`.
- **Pairing rule**: a second family is justified only by a second job. Common jobs: a display or serif face for marketing headings; a monospace for code, IDs and keys. Pair by contrast (serif with sans, or text face with a distinct display face), never two similar sans faces. Three families is a mistake.
- **Personality comes from the heading face, weight and tracking**, not from the body face. Body text must be boring.
- Test candidates on the real screen, at real sizes, on a low-density Windows monitor as well as a Retina display. Thin weights that look elegant on a Mac break up on standard-density screens.

## Color: palette, roles, contrast

Build the palette in this order:

1. **Neutrals first**: one gray ramp of 10 to 12 steps, tinted very slightly toward the brand hue (cool for blue or purple brands, warm for orange or red). This ramp is 90% of the interface.
2. **One brand or accent ramp** of the same number of steps. The accent appears on the primary button, links, focus rings and selected states, and nowhere else.
3. **Four status hues**: success (green), warning (amber), danger (red), info (blue). Each needs at least a subtle background, a border and a text or icon step.
4. **Map ramps to roles** (background, surface, border, text, text-muted, primary, on-primary, danger and so on) and use only roles in components. See `design-systems.md` for the tiers.

Generate ramps in a perceptually uniform space (OKLCH) so that step 600 of every hue has similar visual lightness; ramps built in HSL have a yellow that glows and a blue that sinks at the same nominal lightness. Lower chroma toward both ends of a ramp. Starting from an existing library (Radix Colors, Tailwind's default palette) is the fastest correct route.

Proportion, as a rule of thumb: roughly 60% background neutrals, 30% surface and text neutrals, 10% or less accent. If the accent covers more than that, it has stopped signaling anything.

### Contrast numbers (WCAG 2.x AA)

| Element | Minimum contrast against its background |
|---|---|
| Body text, labels, placeholder text that conveys information | 4.5:1 |
| Large text: at least 24px regular, or about 18.66px bold | 3:1 |
| Borders of inputs, icons that carry meaning, focus indicators, chart marks | 3:1 against adjacent colors |
| Disabled controls, decoration, logos | No requirement |

Traps:

- **Muted text is where contrast fails.** Check the lightest gray used for text on the darkest background it sits on (table stripes, hover rows, tinted cards), not on white. In a dark theme the pair to check is the dimmest text on the lightest raised surface.
- **White on brand color.** Mid-lightness brand hues (orange, light green, cyan, yellow) fail with white text. Either darken the button step until white passes, or use dark text on it. Decide once and record it as `on-primary`.
- **Color is never the only signal.** Status needs an icon or text as well as a hue; red-green color deficiency is common (the usual estimate is about one man in twelve, and far fewer women). Links inside body text need an underline or another non-color cue.
- **Text on photos** needs a scrim or a solid plate; contrast over an image cannot be guaranteed otherwise.
- **Translucent text and surfaces** are measured after blending: text set with opacity, or sitting on a semi-transparent layer, has the contrast of the composited result, which a check of the token values does not see.
- Checking: browser DevTools shows the ratio in the color picker; automated audits catch plain text but not text over gradients or images. Full conformance work belongs to `0x:accessibility`.

## Spacing and grid

Scale on a 4px base: **4, 8, 12, 16, 24, 32, 48, 64, 96**. No value outside the scale without a written reason. Half steps (2px, 6px) are for icon-to-text gaps and inside compact controls only.

- **Proximity rule**: the gap inside a group is at most half the gap between groups. Label to input 4 to 8px; field to field 16 to 24px; section to section 32 to 48px. This single rule does most of the work of making forms and cards readable.
- **Padding scales with the container**: controls 8 to 12px vertical; cards 16 to 24px; page gutters 16px on phones, 24 to 32px on desktop.
- **Control heights**: 32px compact, 36 to 40px default, 44 to 48px for touch-first. All controls in a row share a height. WCAG 2.2 AA asks for pointer targets of at least 24 by 24 CSS px, or smaller ones spaced so that 24px circles centered on them do not overlap (links inside sentences are exempt); design touch targets at 44px or more.
- **Grid**: 12 columns on desktop with 16 to 24px gutters, collapsing to 4 columns on phones. Constrain the content: about 1200 to 1280px for app content, about 640 to 720px for forms and prose. A form stretched across a 1440px screen is a classic amateur tell.
- **Optical alignment beats mathematical alignment**: align text by its left edge, not the edge of its padding box; nudge icons to look centered in buttons.
- **Radius**: pick a scale such as 4, 8, 12 and full. Nested radii follow inner radius = outer radius minus padding; otherwise corners look pinched.
- **Shadows**: two to four levels, all with the same light direction (downward), low opacity and large blur. Use elevation only for things that float (menus, dialogs, toasts), not as decoration for cards.

## Data-dense screens: tables, filters, dashboards

Dense is not the same as cramped. Density comes from removing chrome and decoration, not from shrinking text below 12px.

**Tables**

- Left-align text, right-align numbers with tabular figures and a fixed number of decimals, units in the header. Never center data columns.
- Row height: 32 to 40px compact, 44 to 52px comfortable. Offer a density toggle only once users ask.
- Separate rows with hairlines or generous spacing; zebra stripes only for very wide tables. No vertical rules.
- Sticky header; the identifying column is first and stays frozen when scrolling sideways.
- One primary click target per row (the name opens the record); secondary actions in a trailing overflow menu; bulk actions appear in a bar when rows are selected.
- Truncate with an ellipsis and expose the full value on hover and focus; never truncate numbers or the identifying column.
- Every table needs designed empty, loading, error and "no results for this filter" states; the last one must offer "clear filters".
- On phones, do not shrink the table. Turn each row into a stacked card showing the two or three fields that matter, or allow horizontal scroll with the first column frozen.

**Filters**: show the two to four most-used filters inline above the table; put the rest behind "Filters". Display applied filters as removable chips with a "Clear all". Show the result count. Persist filter state in the URL (see `information-architecture.md`).

**Dashboards**: lead with the three to five numbers the user acts on, each with a comparison (previous period or target) because a number alone carries no meaning. Top-left is the most important slot. One time-range control governs the whole page. Every tile links to the detail behind it. Chart form, color and legend rules belong to the `dataviz` skill.

## Icons and imagery

- **One icon set** for the whole product. Lucide is the default with Radix-style kits; Heroicons, Phosphor and Tabler are sound alternatives. Mixing sets shows immediately as mismatched stroke weight and corner style. Those four are open source; for any other icon set, font, photo or illustration, stock or generated, confirm that the license allows commercial use and record any attribution duty in the brand kit.
- Rules to write down: outline or filled (use filled only to mark the active state); stroke width (1.5 or 2px, constant); sizes 16, 20 and 24px only; color inherits `currentColor`; icon-to-label gap 6 to 8px.
- **Icons need labels.** Only a handful are understood without text (search, close, plus, settings gear, trash, home, menu). Icon-only buttons need a tooltip and an accessible name. An icon next to every menu item adds noise unless users scan by icon.
- Do not use emoji as interface icons: they render differently on every platform and cannot take the theme color.
- **Imagery**: choose one style and reject the rest: real product screenshots, or one illustration style, or one photography treatment. For a B2B tool, real screenshots with realistic data beat illustration. Write down aspect ratios (16:9, 4:3, 1:1), corner radius and whether images carry a border.

## Minimal brand kit

A solo founder needs one page, not a brand book. It must contain:

| Item | Minimum |
|---|---|
| Logo | Wordmark plus a square mark that survives at 16px (favicon, app icon, avatar); light and dark versions; SVG source; clear space equal to the mark's height; a minimum size |
| Palette | Neutral ramp, accent ramp, four status hues, with role mapping and the on-color for each filled color |
| Type | Family or families, the scale, weights, and where the files and license live |
| Shape | Radius scale, border weight, shadow levels |
| Icons and imagery | The chosen set and the rules above |
| Voice | Three or four traits with examples (see `microcopy.md`) |
| Do and do not | Six to ten side-by-side examples; these prevent more drift than any rule text |

Store the kit in the repository next to the tokens so the product, the marketing site, emails and social images draw from the same values. Skip custom illustration, a mascot and motion branding until Scale.

A name or mark that resembles one already used in the same field is a trademark risk that no design rule catches. Search before the logo goes on everything; a real doubt is a question for a professional, and a forced rename after Launch costs far more than one before.

## Checks

- Squint test passes: exactly one element dominates each screen.
- A search of the stylesheet or class names finds no spacing, size, radius or color value outside the scales.
- No more than four text sizes and three weights on any one screen.
- The lowest-contrast text and surface pair in use (usually muted text on a tinted, striped or hovered surface) passes 4.5:1; input borders and meaningful icons pass 3:1.
- Prose never exceeds about 75 characters per line at any viewport width.
- The screen still reads correctly in grayscale (hierarchy does not depend on hue).
- Checked with real content: the longest realistic name, a zero value, a seven-digit number, a missing avatar.

## Ask the user

- **Is there an existing brand (logo, colors, fonts) that must be respected?** It constrains every choice. Default: none; choose a neutral palette with one accent and one sans family.
- **Who uses this and for how long per day?** A tool used eight hours a day wants density and calm; a consumer product used for two minutes wants space and personality. Default: B2B tool, medium density, 14px UI text.
- **Three products whose look they admire, and one they dislike?** Faster and more reliable than adjectives. Default: restrained, neutral, one accent.
- **Is a paid typeface acceptable?** Licenses are priced per traffic or per seat and add an asset to manage. Default: an open-license family or the system stack.
- **Which languages and scripts will the product ship in?** The typeface must cover them and layouts must absorb longer strings. Default: Latin script only, with room for 30 to 40% text expansion.
