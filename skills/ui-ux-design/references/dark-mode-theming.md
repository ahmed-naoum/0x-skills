# Dark mode and theming

Read this when: adding a dark theme or a theme switcher; a dark theme looks washed out, muddy or glaring; adapting images, shadows, charts or brand colors for dark surfaces; supporting high-contrast or forced-colors modes; offering customer-branded themes.

## Whether to offer it, and how

| Stage or product | Decision |
|---|---|
| Prototype | Ship one theme. Use semantic tokens from the first component so a second theme stays cheap |
| Launch, general product | Light and dark, following the system setting by default, with a three-way choice: System, Light, Dark |
| Tools used for hours or at night (developer tools, editors, monitoring, media) | Dark is expected from day one and may be the default |
| Content or commerce sites with heavy photography, documents meant for print | Dark is optional; a poor dark theme is worse than none |
| Marketing site | May have a single fixed theme chosen for the brand; it need not match the app's switcher |

Rules for the switcher:

- **Default to System.** The user already expressed a preference at the operating-system level, and many systems switch automatically at sunset.
- **Three options, not a two-state toggle.** A toggle cannot express "follow the system", so a user who touches it once is pinned forever.
- **Persist the explicit choice** per user (in the account when signed in, so it follows across devices; locally otherwise). Place it in appearance settings and optionally in the account menu.
- **Do not half-ship.** If dark is offered, every screen, email-embedded view, chart, empty-state illustration and third-party embed must be checked. A product that is dark with one white page is worse than light-only.
- **Emails** are rendered by clients that apply their own dark transformations; design emails to survive inversion rather than trying to mirror the app theme. See `0x:email-notifications`.

Implementation points that are design decisions:

- **No flash of the wrong theme.** The theme must be resolved before first paint: a small blocking inline script in the document head that reads the stored choice and sets the attribute, or a cookie read on the server. A cookie can carry only an explicit Light or Dark choice; the server cannot see the system preference on most browsers, so "System" resolves in CSS (`prefers-color-scheme`) or in that inline script. Under a strict Content Security Policy the inline script needs a nonce or hash, or it is blocked silently and the flash returns (`0x:web-security`). A white flash on every load is the dark-mode defect users notice first. Helper libraries exist (`next-themes` is the long-standing one for Next.js); before adding one, check that it is still maintained and runs without warnings on the React version in use, because the whole job is about ten lines of script.
- **Tell the browser the scheme** so scrollbars, form controls and default backgrounds match:

```css
:root { color-scheme: light dark; }
:root[data-theme="light"] { color-scheme: light; }
:root[data-theme="dark"] { color-scheme: dark; }
```

- With Tailwind v4 the `dark:` variant follows the system preference by default; to drive it from a class or attribute, declare the variant (here with the same attribute as above; a kit that toggles a `.dark` class uses that selector in both places):

```css
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
```

  Once the variant is tied to the attribute it no longer follows the system by itself. In System mode the script must write the resolved value (`light` or `dark`) to the attribute and update it when the system setting changes; otherwise native controls go dark while `dark:` styles stay light.
- With `color-scheme` set per theme as above, `light-dark(lightValue, darkValue)` lets one token declaration carry both values; confirm it is supported by the oldest browser the product commits to.

Prefer tokens that change value per theme over `dark:` variants scattered through components; a component that needs `dark:` on most of its classes is using primitive colors. Mechanics belong to `0x:frontend-foundations`.

## Semantic tokens make themes swap

A theme is a set of values for the same semantic tokens (tiers in `design-systems.md`). The work of adding dark mode to an existing product is mostly replacing raw colors with roles.

Sequence for retrofitting:

1. **Inventory color uses**: search for hex, rgb, hsl and oklch literals, palette utility classes, `white` and `black`, inline SVG fills, shadows, borders, gradients, chart configuration and images with baked-in backgrounds.
2. **Assign each use a role**: page background, surface, raised surface, subtle fill, border, strong border, text, muted text, disabled text, primary, on-primary, status fills and their subtle variants, focus ring, overlay scrim, shadow.
3. **Replace values with tokens** in the light theme first, with no visual change. Verify by screenshot comparison.
4. **Define the dark values** for the same tokens.
5. **Review every screen and state** in dark, including hover, focus, selected, disabled, error and loading.

Rules:

- **Roles, not inverses.** There is no token called "white". Text on a primary button is `on-primary`, which may be white in both themes.
- **The number of roles is what matters.** Dark themes need distinctions light themes get free from shadows, typically two or three surface levels and two border strengths. If light used one gray for both a border and a subtle fill, dark will need them split.
- **Same token names in every theme, and no theme-conditional logic in components.** A component that asks "is it dark?" is a missing token.
- **Shadows, scrims and focus rings are tokens too**, with per-theme values.
- **Status colors come in sets per theme**: solid fill, subtle background, border, text. The light-theme subtle background (a pale tint) has no direct inverse; in dark it becomes a low-lightness, low-chroma tint of the hue with lighter text.

## Designing dark surfaces

Inverting the light theme produces the washed-out or glaring result. Dark themes follow different rules.

| Aspect | Light theme | Dark theme |
|---|---|---|
| Base background | White or near-white | Dark gray, not pure black: about #121212 to #242424 (roughly 7 to 14% HSL lightness, 0.18 to 0.26 OKLCH lightness), slightly tinted toward the brand hue |
| Elevation | Shadows; higher is the same color with a deeper shadow | Lightness; higher surfaces are lighter. Each level steps up a few percent |
| Text | Near-black on white | Off-white, not pure white: primary text around #E0E0E0 to #EDEDED (roughly 88 to 93% lightness); secondary dimmer but still 4.5:1 on the lightest raised surface |
| Borders | Light gray lines | Slightly lighter than the surface, low contrast; borders do more work because shadows do less |
| Accent and status colors | Mid-to-dark steps (600 to 700) | Lighter, less saturated steps (300 to 400) for text and icons; filled buttons may keep a mid step if the on-color passes |
| Shadows | Soft, visible | Nearly invisible on dark; make them darker and tighter, and rely on surface lightness and a hairline border |
| Overlay scrim | Black at about 40 to 50% | Black at a higher opacity, about 60 to 70%, since the page is already dark |

Why each matters:

- **Pure black backgrounds** make elevation impossible to show (nothing is darker), raise contrast with white text to a glaring maximum and cause smearing when scrolling on some OLED panels. A true-black theme is a separate, optional variant for OLED devices.
- **Pure white text on dark** vibrates (halation), especially for readers with astigmatism. Off-white reduces it while still passing contrast easily.
- **Saturated colors on dark** appear to glow and vibrate against the background and often fail contrast as text. Lower the chroma and raise the lightness. This is the usual cause of "washed out" complaints handled the wrong way: the fix is not more saturation everywhere, but a deeper base, clear surface steps and a properly chosen accent step.
- **"Washed out" diagnosis**: the base is too light (a mid gray), surfaces are too close together, or text is too dim. Deepen the base, keep at least a visible step between surface levels, and restore primary text contrast.
- **"Muddy" diagnosis**: a neutral ramp with no tint, or too many near-identical grays. Tint the neutrals slightly and reduce the number of surface levels to three.
- **Contrast is rechecked from scratch.** The same minimums apply (4.5:1 text, 3:1 large text and meaningful non-text elements). Typical dark failures: muted text on raised surfaces, placeholder text, disabled-looking-but-enabled controls, borders of inputs, focus rings that disappear, and link color on dark surfaces.
- **Font weight**: light text on dark looks slightly bolder; very thin weights break up and heavy weights glow. Keep regular weight for body; do not introduce a thin weight for dark.
- **Selected and hover states** are lighter overlays in dark, darker overlays in light. Define them as tokens so components do not hard-code direction.

Build the dark neutral ramp deliberately (the same perceptual approach as in `visual-design.md`), instead of reusing the light ramp upside down: the steps needed near the dark end are closer together than the steps a light theme uses near white.

## Images, shadows, charts and brand colors

| Asset | Adaptation |
|---|---|
| Logo | A dark-surface version (light wordmark). Never place the standard logo on a white plate in a dark header |
| Icons | Inline SVG using `currentColor` adapts automatically; raster or hard-coded-fill icons need replacing |
| Photos | Usually unchanged. Very bright images in a dark page may be dimmed slightly; do not dim content the user uploaded for accuracy (product photos, design work) |
| Illustrations with baked-in light backgrounds | Provide a dark variant, make the background transparent, or put them on a deliberate light card with a radius. Empty-state illustrations are the usual offenders |
| Screenshots of the product (docs, marketing, onboarding) | Capture both themes, or frame the screenshot so its theme reads as intentional |
| Transparent PNGs with dark content (signatures, diagrams, customer logos) | Disappear on dark; give them a light plate |
| Embedded third-party content (maps, video players, widgets, payment fields) | Check whether the provider offers a dark option; otherwise contain it in a card |
| Shadows | Reduce reliance; pair elevation with a lighter surface and a hairline border |
| Charts | Separate palette per theme: lighter, less saturated series colors on dark; gridlines and axes much subtler than text; recheck that series are distinguishable. Palette method belongs to the `dataviz` skill |
| Brand color | Keep the hue, shift lightness and chroma per theme. The brand primary as a button fill may stay close to the original if its on-color passes; as text or icon on dark it needs a lighter step |
| Code blocks and syntax highlighting | A dark syntax theme with checked contrast, not the light one inverted |
| Favicon and browser chrome | A favicon that is visible on both light and dark tab bars; theme color for the browser UI per scheme |

Selecting theme-specific image sources can be done in markup with a `media="(prefers-color-scheme: dark)"` source, but that follows the system setting, not an in-app override; with a switcher, choose assets from the active theme class or use CSS that reads the theme tokens. Avoid blanket CSS filters that invert or dim all images; they corrupt photos and brand marks.

## High contrast and forced colors

Two different mechanisms, often confused:

| Mechanism | What happens | Design response |
|---|---|---|
| `prefers-contrast: more` | The user asks for more contrast; the page keeps its own colors | Optional enhanced theme: stronger borders, darker muted text, no low-contrast placeholder text, solid instead of translucent surfaces |
| Forced colors (Windows contrast themes; `forced-colors: active`) | The browser replaces author colors with a small user-chosen palette; backgrounds, text, borders and shadows are overridden | Do not fight it. Make sure the interface still works when author colors and shadows are gone |

What breaks in forced-colors mode, and the fix:

- **Anything distinguished only by background color or shadow disappears**: cards, buttons without borders, selected rows, toggles, custom checkboxes, focus rings drawn with `box-shadow`. Give controls a real border and focus a real outline. A transparent border or outline costs nothing visually in normal mode and becomes visible when colors are forced:

```css
.button { border: 1px solid transparent; }
.button:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }
```

- **State shown only by fill** (selected tab, active toggle, progress fill) needs a non-color cue: a border, an underline, a check mark, a text label.
- **Icons**: SVG using `currentColor` follows the forced text color; hard-coded fills may vanish against the forced background.
- **Custom adjustments** use system color keywords inside the media query, so they follow the user's palette:

```css
@media (forced-colors: active) {
  .tab[aria-selected="true"] { border-bottom: 2px solid Highlight; }
  .badge { border: 1px solid CanvasText; }
}
```

  The useful keywords are `Canvas`, `CanvasText`, `LinkText`, `ButtonFace`, `ButtonText`, `Highlight`, `HighlightText`, `GrayText`, `Field` and `FieldText`.
- **`forced-color-adjust: none`** opts an element out; reserve it for content where color is the information (a color swatch, a chart with another accessible alternative), never for whole components.
- **Test** by emulating forced colors in browser developer tools (the rendering emulation settings in Chromium-based browsers) and, before a claim of support, on Windows with a contrast theme enabled.

Stage: using real borders and outlines costs nothing and should be the habit from Prototype. A full forced-colors pass belongs at Launch for products sold to the public sector, education or large enterprises, and at Scale otherwise. For those buyers accessibility is often a legal or procurement requirement rather than a preference, and which rules apply depends on the market. A dedicated high-contrast theme is optional when the default themes already meet AA. Conformance scope belongs to `0x:accessibility`.

## Per-customer branded themes

Customer branding (white label, branded portals, embedded widgets) is a values swap at the semantic tier, scoped to the tenant.

Decide the level before building:

| Level | Customer controls | Cost and risk |
|---|---|---|
| 1. Logo and one accent color | Logo, primary color | Low. The right default for almost every product |
| 2. Small brand set | Logo, primary, optional secondary, radius choice, font from an approved list | Moderate. Needs a preview and guardrails |
| 3. Full theme | Every semantic token, custom fonts, custom CSS | High. Unbounded testing surface, accessibility failures, support burden, and security exposure if arbitrary CSS is allowed. Enterprise contracts only |

Rules:

- **Customers set inputs; the system derives the rest.** From one accent color, generate the hover and active steps, the subtle background, the focus ring and the on-color, for both light and dark themes. Do not ask customers for twelve colors.
- **Guarantee contrast automatically.** Compute the on-color (dark or light text) from the accent's contrast, and adjust the accent's lightness per theme when it fails against the surface. A customer's pale yellow must not produce white text on yellow buttons. Warn in the theme editor and show the corrected result.
- **Keep status colors out of customer control.** Danger stays red, success green, regardless of brand; a brand red as primary must still be distinguishable from destructive actions (for example by keeping destructive buttons outlined plus an icon).
- **Neutrals stay the product's.** Tinting the gray ramp per customer multiplies testing for little visible gain.
- **Apply at the root, scoped by tenant**: emit the tenant's token values as custom properties on the root element from the server, so the first paint is branded and there is no flash of the default brand. Cache the generated values with the tenant record.
- **Treat theme values as untrusted input.** Validate each as a color (or as a value from an allowed list) before writing it into a style block; never interpolate free text into CSS, and do not accept arbitrary customer CSS or remote font URLs without a review path. Injection risks belong to `0x:web-security`.
- **A customer's logo is an upload, with an upload's risks.** SVG files can carry script: accept raster formats, or sanitize the SVG and serve it from a separate origin, and render it as an image, never inline. Fix the dimensions and the file size. Upload handling belongs to `0x:web-security`.
- **Both schemes.** Either derive a dark variant from the same inputs or state that branded spaces are light-only; do not leave dark mode showing the default brand.
- **Where the brand appears**: logo slot with fixed bounding box and padding, primary actions, links, selection, emails and public or customer-facing pages. Internal admin screens can stay in the product's own theme.
- **Give a live preview** on real screens (a form, a table, a dialog), not on a swatch.
- Component tokens earn their place here: when a customer must reach one specific property, add that single token instead of opening the whole tier.

## Checks

- A search of component code finds no color literals, no `white` or `black`, and few or no theme-conditional classes.
- Loading the app with the system in dark mode shows no light flash, on a hard reload and on a slow connection.
- The theme setting offers System, Light and Dark; changing the system setting while on System updates the app live.
- Every screen and every component state was reviewed in dark, including dialogs, toasts, empty states, charts, code blocks and embeds.
- In dark: muted text on the raised surface passes 4.5:1; input borders and focus rings pass 3:1; three surface levels are distinguishable.
- No pure black page background and no pure white body text, unless a true-black variant was chosen deliberately.
- Logos, illustrations and transparent images are visible on dark surfaces.
- With forced colors emulated, every control has a visible boundary, focus is visible, and selected states are distinguishable.
- For branded themes: a very light, a very dark and a highly saturated accent each produce passing contrast in both schemes.

## Ask the user

- **Do users expect dark mode in this category, and do they work at night or for long sessions?** Decides whether it is Launch scope or later. Default: follow the system from Launch for tools; defer for content-led sites.
- **Should the marketing site follow the visitor's theme or keep one brand look?** A brand and effort choice. Default: one fixed look for marketing, system-following in the app.
- **Will customers need their own branding, and how far?** Sets the theming level and its cost. Default: logo plus one accent color.
- **Are public-sector, education or enterprise buyers in scope?** They commonly require accessibility evidence that includes contrast modes. Default: not yet; keep real borders and outlines so the later pass is small.
- **Is a true-black (OLED) variant wanted?** A third theme to maintain. Default: no.
