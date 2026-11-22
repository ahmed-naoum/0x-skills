# Design tokens and component systems

Read this when: defining tokens for color, type, space, radius and shadow; deciding whether to adopt a component kit or design custom; listing the components a product needs; specifying how a component looks and behaves in each state; keeping design files and code aligned or setting rules for changing the system.

## Kit or custom: the first decision

For a solo founder the answer is almost always: adopt accessible headless primitives plus a copy-in styled layer, and restyle through tokens. Menus, comboboxes, dialogs, date pickers and focus management take weeks to get right and nobody pays for them.

| Situation | Choose | Why |
|---|---|---|
| Product UI, any stage, Tailwind project | Headless primitives (Base UI, Radix or React Aria) with a copy-in component set (shadcn/ui style) | Behavior and accessibility solved; the code lives in the repository, so every pixel is editable |
| Internal tool or admin, speed over identity | A full styled kit (Mantine, MUI, Ant Design) | Largest inventory out of the box; accept its look |
| Brand is the product (consumer, design-led marketing) | Custom visuals on headless primitives | Custom skin, borrowed behavior |
| A component no kit offers (timeline editor, canvas, spreadsheet grid) | Custom, scoped to that component | Build only the part that differentiates |
| The project already has a kit | Stay on it | Two kits in one product is worse than either |

Traps:

- **Fighting a styled kit.** If more than a few components need deep visual overrides, the kit is the wrong tier; move to headless plus own styles instead of stacking overrides.
- **Unthemed defaults.** A copy-in kit left on its default tokens makes the product look like every other product built that month. Changing the neutral tint, accent, radius, font and density takes an hour and removes the resemblance.
- **Custom behavior for standard controls.** A hand-built select or modal that lacks typeahead, escape handling, focus return and screen-reader semantics is a regression users feel. Custom is for looks, not for interaction contracts.
- **Kit sprawl.** Adding a second library for one component (a date picker, a table) is acceptable; record it and wrap it so the import does not spread.
- **Two primitive libraries.** Copy-in kits let the primitive library be chosen at setup, and their default changes over time (shadcn/ui made Base UI the default for new projects in 2026 and still supports Radix). Keep what the project has; for a new project take the kit's current default. Mixing two gives overlays whose focus trapping, portals and layering disagree.
- **Copy-in means owning the updates.** Copied component files do not improve when a package is bumped; only the primitives underneath do. When a copied component misbehaves, compare it with the kit's current version before patching by hand.
- **Paid tiers.** Several kits keep the data grid, date-range picker, scheduler or charts under a commercial license priced per developer (MUI X and AG Grid are examples). Read the license and the current price before designing a screen around such a component.

## Inventory before screens

List the components before designing any screen; the list exposes scope and stops each screen from inventing its own variant.

1. Walk every flow (see `ux-flows.md`) and write down each distinct piece of UI on each screen, including its states.
2. Merge near-duplicates. Three slightly different cards become one card with a variant, or the difference is removed.
3. Mark each: from the kit as is, from the kit restyled, or custom.
4. Build in dependency order: tokens, then primitives, then composites, then page patterns.

A typical SaaS product at Launch needs roughly this set, and little else:

| Group | Components |
|---|---|
| Actions | Button (primary, secondary, ghost, destructive; with icon; loading), icon button, link, dropdown menu |
| Inputs | Text field, textarea, select, combobox, checkbox, radio group, switch, date picker, file upload; the field wrapper (label, hint, error) |
| Feedback | Toast, inline alert or banner, dialog, confirmation dialog, tooltip, progress, spinner, skeleton |
| Navigation | Sidebar or top bar, tabs, breadcrumbs, pagination, command palette (later) |
| Data display | Table, card, list item, badge or status pill, avatar, empty state, stat tile |
| Layout | Page shell, page header (title, description, actions), section, stack and grid helpers, sheet or drawer |

The field wrapper, page header and empty state are the three patterns most often left undesigned and therefore different on every screen. Define them first.

For an existing product, run an interface inventory instead: screenshot every button, input, card and heading style in use, group them, and count. The count (for example, nine button styles) is the argument for consolidation and the to-do list.

## Tokens

Tokens are named design decisions. The value of a token system is that a component never contains a raw value, so a change of theme, density or brand is a change of values in one place.

### Three tiers

| Tier | Example name | Holds | Who may reference it |
|---|---|---|---|
| Primitive | `blue-600`, `gray-100`, `space-4`, `radius-md` | Every raw value the system allows | Semantic tokens only |
| Semantic | `color-bg-surface`, `color-text-muted`, `color-border-default`, `color-primary`, `color-on-primary`, `color-danger` | Purpose: what the value is for | Components and screens |
| Component | `button-primary-bg`, `input-border-focus` | An exception for one component | That component |

Rules:

- **Components use semantic tokens.** A component that uses `gray-100` directly breaks in dark mode and under a customer theme. This is the rule that makes theming a values swap (see `dark-mode-theming.md`).
- **Start with two tiers.** Add a component token only when a component must diverge from the semantic value, or when a customer theme must reach that one property. A full component tier written up front triples the token count and nobody maintains it.
- **Name by role, not by look.** `color-danger`, not `color-red`; `color-bg-surface-raised`, not `color-gray-50`. A role name survives a rebrand and a dark theme.
- **Pair every fill with its on-color**: `primary` and `on-primary`, `danger` and `on-danger`. Contrast is then checked once per pair instead of once per component.
- **Keep the set small.** A workable semantic color set is 15 to 25 tokens. If two tokens always hold the same value in every theme, they are one token.

### What to define

| Category | Semantic tokens to define |
|---|---|
| Color | Backgrounds: page, surface, raised, sunken or subtle, overlay scrim. Text: default, muted, disabled, link, on-primary. Borders: default, strong, focus ring. Fills: primary and its hover and active, secondary, danger, success, warning, info, each with a subtle background variant and an on-color |
| Type | Family (sans, mono), size steps, line heights paired to sizes, weights, letter-spacing for display and caps; then composite text styles (body, body-small, label, heading-1 to 3, caption) |
| Space | The 4px-based scale; optionally aliases such as control padding, card padding, page gutter |
| Radius | Small, medium, large, full; one of them named as the control radius |
| Shadow | Two to four elevation levels plus the focus ring; shadows are theme-dependent values |
| Border | Width (1px, 2px for focus) |
| Motion | Durations and easings (see `motion-design.md`) |
| Layering | A named z-index scale: dropdown, sticky, overlay, modal, toast, tooltip |

### Where tokens live

Tokens live in code as CSS custom properties, exposed to the styling layer. With Tailwind v4 the theme is declared in CSS and each theme variable also generates utilities:

```css
@import "tailwindcss";

:root {
  --bg-surface: oklch(1 0 0);
  --text-default: oklch(0.21 0.02 260);
  --primary: oklch(0.55 0.2 260);
  --on-primary: oklch(0.99 0 0);
}

@theme inline {
  --color-surface: var(--bg-surface);
  --color-foreground: var(--text-default);
  --color-primary: var(--primary);
  --color-on-primary: var(--on-primary);
}
```

This yields `bg-surface`, `text-foreground`, `bg-primary`, `text-on-primary`. Restrict the palette utilities that components may use to the semantic ones; a lint rule or review check for raw palette classes (`bg-blue-600`) and arbitrary values (`p-[13px]`) inside components keeps the system honest.
If the project uses an older Tailwind with a JavaScript config, or another styling approach, keep the same structure: custom properties for values, the framework's theme pointing at them. Mechanics belong to `0x:frontend-foundations`.

## Component states

A component is specified when every state below has a defined look and behavior. Missing states are the main source of "it looked fine in the mockup".

| State | What must be defined | Common mistake |
|---|---|---|
| Default | Resting look; the affordance must be visible without hover | Controls that only look clickable on hover fail on touch |
| Hover | Subtle change: one step of background or border | Hover as the only way to reveal an action; touch devices have no hover |
| Focus-visible | A ring at least 2px thick with 3:1 contrast against adjacent colors, offset from the control, on every interactive element | Removing the outline; a ring that vanishes on colored backgrounds |
| Active or pressed | Immediate change within 100ms: darker step or slight scale | No press feedback, so users click twice |
| Selected, checked, current | Distinct from hover and from focus; not color alone | Selected and hover looking identical |
| Disabled | Reduced contrast, no hover, not focusable for native disabled; reason available nearby | Disabling the submit button with no explanation of what is missing |
| Loading | Control keeps its width; label replaced or joined by a spinner; repeat activation blocked | Button resizes or the form can be submitted twice. Blocking the button is a courtesy, not protection: anything that creates a record or charges money also needs the server to reject the duplicate (`0x:api-design`) |
| Error or invalid | Border and icon plus a text message tied to the field; shown after blur or submit, not on first keystroke | Red border only; message far from the field |
| Read-only | Looks like text, not a faded input; still selectable and focusable | Using disabled for read-only, which blocks copying |
| Empty and overflow | Placeholder or empty look; truncation, wrapping or scrolling for long content | Designed only with ideal-length text |

Decisions that recur:

- **Disabled versus enabled with validation.** Prefer keeping the submit button enabled and showing what is wrong on submit. A disabled button gives no clue and its low contrast is hard to see. Disable only when the action is impossible for a reason stated next to it.
- **Focus ring**: one ring style for the whole product, built from a token, drawn with `outline` so it survives forced-colors mode. Show it on keyboard focus (`:focus-visible`), not on mouse click, except for text inputs, which show focus always.
- **Hover is an enhancement.** Anything revealed on hover (row actions, tooltips with essential content) needs an equivalent that is always visible or reachable by focus and by tap.
- **Variants are a budget.** Every component gets size (usually two or three) and intent variants; every further variant must replace a real duplication. A button with fourteen props is a sign that two components are sharing one name.
- **State matrix as the test.** Render every variant in every state on one page (a Storybook story or a plain route) in light and dark. That page is the specification and the visual regression target.

Keyboard, ARIA and screen-reader behavior for each state belongs to `0x:accessibility`; building the components belongs to `0x:react-nextjs`.

## One source of truth for design and code

Two sources drift within weeks. Decide which one is authoritative and generate or check the other from it.

| Team shape | Source of truth | The other side |
|---|---|---|
| Solo developer, no designer (Prototype, Launch) | Code: token CSS plus the coded components | No maintained design file. Explore in a throwaway file or in code, then discard. A component gallery route or Storybook is the catalog |
| Developer plus a designer | Tokens as data (JSON in the repository), transformed to CSS and synced to design-tool variables | Design-tool library mirrors coded components by the same names and props |
| Several products or platforms (Scale) | Token package in the Design Tokens Community Group format, built with a transformer such as Style Dictionary into CSS, native and design-tool outputs | Versioned package consumed by each product |

Practices that keep the two aligned at any size:

- **Same names on both sides.** The design component is called what the code component is called, with the same variant names. Translation tables rot.
- **Tokens flow one way.** Never edit a generated file; change the source and rebuild.
- **The coded component is the truth for behavior**; a design file cannot express focus order, loading or overflow. Review real components in the browser, not pictures of them.
- **Visual regression on the state-matrix page** catches unintended changes; set it up at Launch if the UI changes weekly, otherwise at Scale. Test setup belongs to `0x:code-quality`.

The Design Tokens Community Group format has had a stable version since late 2025, but how completely each transformer and design tool reads and writes it still varies; check the current documentation of the tools in use before building a pipeline. For one developer the pipeline is not worth building.

## Governance

Until there is a second contributor, governance is three habits: no raw values in components, no new component without checking the inventory, and delete what is unused. The rest applies from Scale, or as soon as two products share the system.

- **Contribution rule (rule of three).** A pattern enters the shared system once it is needed in three places. Before that it lives with the feature. Proposals state the use cases, the existing component that does not fit and why.
- **Definition of done for a system component**: all states above, both themes, keyboard operable, responsive, documented with one usage example and one misuse example, covered by the state-matrix page.
- **Versioning.** If the system is a package, use semantic versioning: removing or renaming a token or prop, or a visible change that can break layouts (size, spacing), is a major change; new components and tokens are minor; fixes are patch. Inside a single repository, the changelog entry and a codemod replace the version number.
- **Deprecation sequence.** Announce with the replacement named; mark the old API deprecated so editors warn; provide a codemod or search-and-replace recipe; add a lint rule that blocks new uses; remove after usage reaches zero or after one announced release cycle. Never leave two blessed ways to do the same thing indefinitely.
- **One owner.** A named person decides additions. Committees produce variants.
- **Measure adoption crudely**: count raw color and spacing values and one-off components in the codebase. A rising count means the system is missing something people need; ask what.

## Checks

- A search of component code finds no hex, rgb or oklch literals and no primitive palette classes; only semantic tokens.
- Every fill token has an on-color and the pair passes 4.5:1 for text.
- The state-matrix page exists and shows each component in every state, in each theme.
- Tab through a screen: the focus ring is visible on every interactive element, on every background.
- Each interactive component works by touch with no hover.
- The component inventory lists the source (kit, restyled, custom) for each component, and no screen uses a component outside it.
- Changing the accent and radius tokens restyles the whole product with no component edits.

## Ask the user

- **Does a brand identity already exist, or should the kit's look be re-themed from scratch?** Decides how far tokens depart from kit defaults. Default: keep the kit's structure, change neutral tint, accent, radius and font.
- **Will customers ever need their own branding inside the product (white label)?** If yes, the semantic tier must be designed for it now. Default: no; single brand, light and dark.
- **Is a designer working in a design tool, now or soon?** Decides whether a token sync pipeline is worth building. Default: code is the only source of truth.
- **Will more than one product or platform (web, native, email) share these tokens?** If yes, keep tokens as platform-neutral data. Default: one web product; CSS custom properties are enough.
- **How dense should the interface be?** Sets control heights and spacing tokens for everything. Default: 36 to 40px controls on desktop, 44px or more on touch layouts.
- **Is a paid component license acceptable (a commercial data grid, scheduler or chart tier)?** It is a recurring per-developer cost and a dependency on one vendor. Default: no; open-source components only, and simplify the screen before buying a grid.
