# Layer 7: Design & accessibility

Read this when: the user asks what there is to know about design & accessibility, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

Can every person see it, understand it and finish the task?

Competencies: 93 (44 ● / 40 ◐ / 9 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## ui-ux-design

Design interfaces people understand and enjoy: visual design, design tokens and component systems, UX flows, information architecture, usability testing, microcopy, motion and dark mode.

**Visual design: type, color, spacing and layout** (`references/visual-design.md`)

- ● Establish visual hierarchy so each screen has one clear primary action
- ● Set a type scale, line length and vertical rhythm
- ● Build a color palette with semantic roles and accessible contrast
- ● Use a spacing scale and grid for consistent layout
- ● Define a minimal brand kit: logo, palette, type and imagery rules
- ● Critique a screen and name exactly what makes it look amateur
- ◐ Choose and pair typefaces that fit the brand and render well on screens
- ◐ Design data-dense screens: tables, filters and dashboards
- ◐ Choose one icon set and imagery style and write the rules for using them

**Design tokens and component systems** (`references/design-systems.md`)

- ● Define design tokens for color, type, space, radius and shadow
- ● Decide when to adopt an existing component kit versus designing custom
- ● Specify every component state: hover, focus, active, disabled, loading, error
- ● Inventory the components a product needs before designing screens
- ◐ Structure tokens in primitive, semantic and component tiers
- ○ Keep design files and coded components in sync from one source
- ○ Govern a design system: contribution, versioning and deprecation

**UX flows and screen states** (`references/ux-flows.md`)

- ● Map the user journey from first visit to repeated value
- ● Sketch low-fidelity wireframes for every screen before styling
- ● Design empty, loading, error and success states for every screen
- ● Cut a flow's steps, decisions and fields to the minimum
- ● Decide what changes between phone, tablet and desktop layouts
- ● Design first-run onboarding screens that lead to first value
- ● Design undo, confirmation and forgiveness for destructive actions
- ◐ Design settings, permissions and team flows that scale
- ◐ Prototype a flow in Figma or code before building it

**Information architecture and navigation** (`references/information-architecture.md`)

- ● Name things in the user's vocabulary and keep the object model consistent
- ● Choose navigation patterns: sidebar, tabs, breadcrumbs or command palette
- ◐ Design navigation that survives ten times more features
- ◐ Design search, filtering and sorting for large collections
- ◐ Structure URLs to mirror the information architecture
- ◐ Design a home screen that answers what the user needs next
- ○ Validate structure with card sorting and tree testing

**Usability testing and design review** (`references/usability-testing.md`)

- ● Run a five-user usability test and rank the issues found
- ● Write task scenarios that do not lead the participant
- ● Run a heuristic review against established usability principles
- ◐ Recruit representative test participants quickly and cheaply
- ◐ Use session replays to locate where users struggle
- ◐ Run a design critique that ends in decisions, not opinions
- ○ Run unmoderated remote tests and first-click tests

**Microcopy and interface writing** (`references/microcopy.md`)

- ● Write labels, buttons and confirmations in plain language
- ● Write error messages that say what happened and what to do
- ● Label dialog actions with specific verbs, not Yes and No
- ● Write empty states and hints that teach the next action
- ◐ Set a voice and tone guide with a word list and examples
- ◐ Name features and plans so users understand them without explanation
- ◐ Write copy that translates cleanly and reads well aloud

**Motion design** (`references/motion-design.md`)

- ● Use motion to explain change, not to decorate
- ● Design loading feedback: skeletons, spinners, progress and optimistic updates
- ◐ Set durations and easing by distance and purpose
- ◐ Choreograph page and element transitions consistently
- ◐ Design micro-interactions for success, error and drag moments
- ◐ Define motion tokens and their reduced-motion variants

**Dark mode and theming** (`references/dark-mode-theming.md`)

- ◐ Decide whether to offer a theme switcher and default to the system setting
- ◐ Map every color use to a semantic token so themes swap cleanly
- ◐ Design dark surfaces, elevation and contrast instead of inverting colors
- ◐ Adapt images, shadows, charts and brand colors for dark surfaces
- ○ Support high-contrast and forced-colors modes
- ○ Offer per-customer branded themes through tokens

## accessibility

Make the product usable by people with disabilities and meet WCAG 2.2 AA: names, roles and ARIA, keyboard and focus, accessible forms, visual and cognitive access, and testing and audits.

**Names, roles, states and ARIA** (`references/names-roles-aria.md`)

- ● Give every control an accessible name, role and state
- ● Write alt text that conveys purpose, and hide decorative images
- ● Remove redundant, conflicting or invalid ARIA from existing markup
- ◐ Apply ARIA patterns correctly for tabs, menus, comboboxes and dialogs
- ◐ Announce dynamic changes with live regions
- ◐ Replace an inaccessible custom widget with a tested primitive
- ◐ Make data tables understandable without sight: headers, scope and captions

**Keyboard, focus and pointer access** (`references/keyboard-focus.md`)

- ● Make every flow keyboard-operable with visible focus
- ● Provide skip links and a logical tab order
- ● Size and space touch targets to WCAG 2.2 minimums
- ● Manage focus on route changes and dynamically inserted content
- ● Trap focus in modals and restore it on close
- ◐ Offer alternatives to drag, hover and gesture-only interactions
- ○ Support switch and voice-control users through standard semantics

**Accessible forms and authentication** (`references/accessible-forms.md`)

- ● Label every field and associate hints and errors programmatically
- ● Announce validation errors and move focus to the first one
- ◐ Make sign-in accessible: allow paste and password managers, no cognitive tests
- ◐ Warn before session timeouts and let users extend them
- ◐ Make multi-step and payment flows completable by screen reader
- ◐ Avoid redundant entry and let users review before submitting

**Visual, media and cognitive access** (`references/visual-cognitive.md`)

- ● Meet contrast minimums for text, icons and focus indicators
- ● Support 200% zoom, text resizing and reflow at 320px
- ● Never convey meaning by color alone
- ◐ Caption video and provide transcripts for audio
- ◐ Avoid flashing, autoplay and motion that triggers vestibular problems
- ◐ Write content in plain language with clear structure
- ◐ Reduce cognitive load with consistent navigation and no time pressure

**Accessibility testing and audits** (`references/testing-audits.md`)

- ● Run automated accessibility checks with axe in CI
- ● Test key flows with a screen reader (VoiceOver, NVDA)
- ● Run a keyboard-only, zoom and high-contrast pass on every feature
- ◐ Run a manual WCAG 2.2 AA audit and prioritize findings
- ◐ Fix accessibility failures in order of user impact
- ◐ Build accessibility into the definition of done and the component library
- ○ Include disabled users in usability testing
- ○ Produce a VPAT or conformance report for enterprise buyers
