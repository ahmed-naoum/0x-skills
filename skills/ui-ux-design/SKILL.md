---
name: ui-ux-design
description: Designs interfaces people understand and enjoy, covering visual hierarchy, type, color and spacing, design tokens and component states, UX flows and screen states, navigation, usability testing, microcopy, motion and dark mode. Use when a screen looks amateur, users get stuck or confused, a flow or onboarding needs designing before it is built, or tokens, button labels, error messages or a dark theme are needed.
---

# UI and UX design

## Stance

Design is a sequence of decisions about what the user is trying to do, made before pixels: the job, the objects and their names, the flow, the states of each screen, and only then the look.
Most screens that feel amateur or confusing fail early in that sequence, and no amount of styling repairs a flow with a missing state or an object with three names. For a solo founder the efficient path is constraint: a small set of tokens, a borrowed component kit, plain words, and cheap evidence from five users instead of opinion.

1. **One primary action per screen.** If two things compete, the user hesitates. Decide which wins and demote the rest; this resolves most hierarchy arguments.
2. **Systems beat taste.** A spacing scale, a type scale, a role-based palette and one icon set make an interface look professional even with ordinary taste, because consistency is what the eye reads as quality.
3. **States are the design.** Empty, loading, error, partial and success states are most of what users meet in the first week. A screen designed only for its ideal data is a third designed.
4. **Words are interface.** Labels, button text and error messages do more for comprehension than layout. Use the user's nouns, one name per object, verbs on buttons.
5. **Borrow behavior, own the look.** Menus, dialogs and comboboxes come from accessible primitives; identity comes from tokens. Custom interaction is reserved for what differentiates the product.
6. **Forgive instead of interrogating.** Undo and recoverable deletes beat confirmation dialogs, which users learn to dismiss without reading.
7. **Motion and color carry meaning or they go.** An animation must give feedback, continuity, attention or status; a color must be a role. Decoration costs speed and trust in a work tool.
8. **Watch behavior, not opinions.** What five people do with a prototype outranks what anyone, including the founder, thinks they will do. Disagreements about user behavior are settled by a test.
9. **Design for the extremes.** The longest name, zero items, ten thousand items, a phone, a slow network, a keyboard, dark mode and a user without permission. The middle takes care of itself.

Follow the project first: use the component kit, tokens and conventions already present, and extend them rather than introducing a parallel system.

## Route

| If the task is... | Read |
|---|---|
| "This screen looks amateur", choosing fonts, colors, spacing or icons, laying out a table or dashboard, making a brand kit | `references/visual-design.md` |
| Setting up design tokens, choosing a component kit, listing the components needed, deciding how a component looks in each state, keeping design and code aligned | `references/design-systems.md` |
| Designing a feature's screens before building: journey, wireframes, empty and error states, onboarding, settings and team flows, phone versus desktop, undo and confirmation | `references/ux-flows.md` |
| The navigation is getting messy, naming things, sidebar versus tabs, search and filters, URL structure, what goes on the home screen, card sorting | `references/information-architecture.md` |
| Users get stuck and the cause is unknown, running a usability test, writing test tasks, recruiting, reading session replays, heuristic review, design critique | `references/usability-testing.md` |
| Writing button labels, error messages, dialogs, empty states, a voice guide, feature or plan names, copy that must translate | `references/microcopy.md` |
| Deciding what animates and how fast, skeleton versus spinner, optimistic updates, page transitions, drag feedback, reduced motion | `references/motion-design.md` |
| Adding a dark theme or theme switcher, fixing a washed-out dark theme, high-contrast and forced-colors support, customer-branded themes | `references/dark-mode-theming.md` |

A request to design a whole feature usually needs `ux-flows.md` first, then `microcopy.md`, then `visual-design.md`. A request to fix a confusing screen starts with a heuristic pass from `usability-testing.md` before any restyling.

## Defaults at a glance

| Area | Default | Flips when |
|---|---|---|
| Components | Headless accessible primitives with a copy-in styled layer, re-themed through tokens | Internal tool: a full styled kit. Existing kit: keep it |
| Tokens | CSS custom properties in two tiers (primitive, semantic); components use semantic only | Add component tokens for customer theming or real exceptions |
| Type | One sans family, variable; sizes from 12, 14, 16, 18, 20, 24, 30, 36, 48; body line height about 1.5; prose capped near 65 characters | Second family only for a second job (display headings, code) |
| Mobile inputs | Input text at least 16px; touch targets 44px or more | |
| Spacing | 4px-based scale: 4, 8, 12, 16, 24, 32, 48, 64, 96; gaps inside a group at most half the gaps between groups | |
| Color | Tinted neutral ramp, one accent, four status hues, generated in a perceptual space; roles with paired on-colors | |
| Contrast | 4.5:1 text, 3:1 large text and meaningful non-text elements | |
| Icons | One set (Lucide with Radix-style kits), sizes 16, 20, 24, with labels | |
| Navigation | Sidebar listing objects, two levels deep, tabs inside objects; every view has a URL | Three to six fixed destinations: top bar. Phone: bottom tabs |
| Onboarding | Straight into the product with a strong first-use empty state, optional checklist; no tooltip tour | Setup required before value: short wizard |
| Destructive actions | Immediate with undo and soft delete; dialog with verb-labeled buttons only for irreversible actions; type-to-confirm for large blast radius | |
| Copy | Sentence case, verb plus object on buttons, errors state what happened and what to do | |
| Loading | Nothing under about 100ms, delayed indicator under 1s, skeleton or spinner to 10s, real progress or a background job beyond | |
| Motion | 80 to 150ms for small feedback, 200 to 300ms for panels, rarely over 500ms; ease-out to enter; tokens with reduced-motion variants | Expressive consumer brand: larger budget for rare moments |
| Theme | System, Light and Dark choice defaulting to System; dark base is dark gray with lighter raised surfaces | Prototype: one theme, but semantic tokens from the start |
| Validation of design | Heuristic pass on every flow; five-user moderated test on core flows | |

By stage:

- **Prototype**: adopt a kit, set tokens once, design the core flow with all its states, write real copy, one theme. Skip brand books, custom illustration, motion polish, design-file sync and governance.
- **Launch**: test signup through first value with five users and fix the blockers; complete empty, error and loading states everywhere; dark theme if the category expects it; motion tokens; a one-page brand kit and voice guide; glossary in the repository.
- **Scale**: navigation restructured around objects with saved views and a command palette; tree testing; visual regression on a component state page; system versioning, contribution and deprecation rules; forced-colors pass; customer theming if sold.

## Before you call it done

1. Each screen has exactly one visually dominant action, confirmed by a squint or blur test.
2. Every data view has designed first-use empty, no-results, loading, error and success states.
3. No raw color, spacing, radius, duration or font-size values in component code; only tokens from the scales.
4. No more than four text sizes and three weights on any one screen; prose lines stay under about 75 characters.
5. The lightest text on the darkest surface it sits on passes 4.5:1; input borders, meaningful icons and focus rings pass 3:1, in every theme.
6. Every interactive element shows hover, focus-visible, pressed, disabled and loading states, and works by touch without hover.
7. Every button is verb plus object; no dialog says "Yes", "No" or a bare "OK"; every error says what happened and what to do and keeps the user's input.
8. Each object has one name across navigation, titles, buttons, emails and URLs; each navigation label equals its page title.
9. Every tab, filter state and detail view survives pasting its URL into a new tab, refresh and the back button.
10. Each destructive action is classified by reversibility and blast radius and has the matching pattern (undo, dialog or type-to-confirm).
11. The flow was walked at 360px wide with touch, at a mid width, and at desktop width, with the longest realistic content, zero items and a no-permission user.
12. A new account reaches first value in the first session; the steps are counted and each field has a downstream use.
13. Fast responses show no loading flicker, slow ones show the right pattern with no layout shift, and optimistic updates roll back visibly on failure.
14. With the system's reduce-motion setting on, nothing slides, zooms or autoplays and state changes remain perceivable.
15. If a dark theme ships: no flash of the wrong theme on load, no pure black base, and logos, illustrations, charts and embeds were checked on dark.

## Not this skill

- Implementing layout, theming and animation in CSS → `0x:frontend-foundations`
- Building the React component library → `0x:react-nextjs`
- WCAG conformance, screen readers and keyboard access → `0x:accessibility`
- Customer interviews, problem validation and what to build → `0x:product-discovery`
- Chart and data-visualization design → `dataviz`
- Landing-page messaging and conversion copy → `0x:growth-marketing`
