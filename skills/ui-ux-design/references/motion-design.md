# Motion design

Read this when: deciding what should move, how fast and why; designing loading feedback; specifying transitions between pages or states; designing success, error and drag feedback; defining motion tokens and reduced-motion behavior.

## Motion must earn its place

Every animation in a product has to do one of four jobs. If it does none, remove it.

| Job | Example | Without it |
|---|---|---|
| Feedback | Button presses, a toggle slides, a row highlights after saving | The user is unsure the input registered and repeats it |
| Continuity | A panel slides in from the side it will return to; a list item expands into its detail | The user loses where they are or where the thing went |
| Attention | A new item fades in at the top of a list; a field shakes on error | A change elsewhere on the screen is missed |
| Status | Progress bar, skeleton, upload indicator | Waiting feels broken |

Rules that decide most cases:

- **Frequency sets the budget.** Something seen a hundred times a day (opening a menu, switching a tab, typing) gets 100 to 150ms or no animation at all. Something seen once (first-run completion) can take half a second. The same flourish that delights on first use is friction on the fiftieth.
- **Never make the user wait for an animation to finish.** Input is accepted during transitions; animations are interruptible and reverse from their current position.
- **Keyboard-driven actions are instant or nearly so.** A command palette that eases in over 300ms feels slow to exactly the users who chose the keyboard for speed.
- **Animate the cause, near the cause.** The thing the user touched responds first; consequences follow.
- **One thing moves at a time for attention.** Two simultaneous attention-seeking animations cancel each other.
- **No looping or autoplaying motion beside content.** Anything that moves by itself for more than five seconds alongside other content needs a way to pause or stop it (a WCAG Level A requirement), and nothing may flash more than three times per second.
- **Marketing pages and product UI have different budgets.** Scroll-driven effects and large entrances can suit a landing page; inside the app they slow work.

At Prototype, the kit's built-in transitions plus correct loading feedback are enough. Define motion tokens at Launch. Choreographed page transitions are optional at every stage.

## Loading feedback

Choose by expected wait and by whether the shape of the result is known.

| Expected wait | Feedback |
|---|---|
| Under about 100ms | None. Feels instantaneous; an indicator would only flicker |
| 100ms to 1s | Usually none on the content; show the pressed or busy state on the control. If an indicator is used, delay it by 200 to 300ms so fast responses never show it |
| 1 to 10s | Skeleton (known layout) or spinner (unknown or small region); keep the rest of the page usable |
| Over 10s | Determinate progress with a count or steps ("240 of 1,800 imported"), the ability to leave and come back, and a notification on completion |
| Minutes or more | Background job with a visible status entry, not a blocking screen; email or in-app notice when done |

The thresholds follow long-standing response-time research: about 0.1s feels instant, about 1s keeps the user's flow of thought, about 10s is the limit of attention on one task.

| Pattern | Use when | Rules |
|---|---|---|
| Skeleton | First load of a page or panel whose layout is known | Match the real layout's blocks closely, or the swap causes a jump. Subtle shimmer or pulse, slow (1.5 to 2s cycle). Never for an action's result, and not for waits under about 300ms |
| Spinner | Small regions, buttons, unknown layout, short waits | Inside the control or region that is busy, never full-page except initial app boot. Add text after a few seconds |
| Determinate progress bar | Duration or step count is known: uploads, imports, multi-step jobs | Must never go backward. If the estimate is rough, show steps rather than a percentage |
| Indeterminate bar (top of page) | Route changes of unknown length | Thin, unobtrusive; delayed start |
| Optimistic update | The action nearly always succeeds and is cheap to reverse: toggle, like, rename, reorder, add to list, mark done | Apply at once; on failure, roll back visibly and say why with a retry. Not for payments, sends, deletes without undo, or anything another system must confirm |
| Stale-while-revalidate | Returning to a list or dashboard already seen | Show cached content immediately, refresh in the background, indicate updating subtly; do not replace content under the user's cursor |
| Streaming | Server-rendered sections or generated text arriving progressively | Reserve space; reveal in reading order; see `0x:ai-features` for model output |

Traps:

- **Flash of loading state**: a spinner that appears for 80ms is worse than nothing. Delay its appearance, and once shown keep it for a minimum (about 300 to 500ms) so it does not blink.
- **Layout shift on arrival**: content that pushes other content down as it loads makes users click the wrong thing. Reserve the space.
- **Skeleton everywhere**: skeletons for a button action, or skeletons that do not resemble the result, read as a slower page.
- **Blocking the whole screen** for one slow region. Load regions independently.
- **Button loading**: keep the width, show a spinner with the label or a progressive label ("Saving..."), block double submission, and restore the label with the result.
- **Fake progress** that stalls at 99% destroys trust; prefer honest indeterminate feedback plus text.
- A real speed problem is not solved by animation; measuring and fixing latency belongs to the performance skills.

## Duration and easing

Duration scales with the distance traveled and the size of the element; easing depends on whether the element enters, leaves or moves.

| Kind of change | Duration |
|---|---|
| Hover, press, focus ring, color or opacity change | 80 to 150ms |
| Small elements: tooltip, checkbox, switch, menu, popover | 120 to 200ms |
| Medium: dropdown panel, toast, accordion section, card expand | 200 to 300ms |
| Large: dialog, side sheet, full-height drawer | 250 to 400ms |
| Full-screen or page-level transition | 300 to 500ms |
| Anything in product UI | Rarely over 500ms |

- **Exits are faster than entrances**, by roughly a quarter to a third: the user has decided, so get out of the way.
- **Phones use the stated values; large desktop distances can take slightly longer; small watch-size surfaces shorter.** The eye judges speed, not time.
- **Opacity and color need less time than movement.**

| Movement | Easing | Why |
|---|---|---|
| Entering the screen | Ease-out (fast start, gentle stop) | Responds immediately, settles calmly |
| Leaving the screen | Ease-in (gentle start, fast end) | Accelerates away; the end is off-screen anyway |
| Moving or resizing on screen | Ease-in-out | Natural start and stop |
| Opacity, color | Linear or gentle ease-out | No spatial movement to shape |
| Direct manipulation (drag, swipe release, pull) | Spring that inherits the gesture's velocity | A fixed curve ignores how fast the finger moved |
| Progress, spinners | Linear | Constant rate reads as steady work |

Default `ease` and symmetric `ease-in-out` on entrances feel sluggish because they start slowly; an ease-out curve is the single most effective change to interface that feels slow to respond. Bounce and overshoot belong to playful brands and rare moments; in a work tool they read as toy-like when repeated.

## Choreography

Consistency of direction and order is what makes motion explain structure.

- **Spatial model.** Decide where things live and keep it: side sheets come from the edge they dock to and leave the same way; dialogs scale and fade from the center or from their trigger; dropdowns grow from the trigger; toasts enter from the edge they stack on. Enter and exit are mirror images.
- **Navigation direction.** Going deeper moves forward (new content from the right or rising), going back reverses it; sibling tabs slide horizontally in the order of the tabs or simply cross-fade. If the direction cannot be kept consistent, use a fade.
- **Shared elements.** When an item in a list becomes the header of its detail page, moving that element between the two positions gives continuity that no fade can. Use it for the one or two core transitions, not everywhere. The browser's View Transitions API covers this for same-document navigations; check current browser support before relying on cross-document transitions, and treat the transition as an enhancement that can be absent.
- **Stagger.** Lists may enter with a small per-item delay (20 to 40ms), capped so the whole sequence stays under about 300 to 400ms, and only on first appearance, never on every filter change.
- **Order.** The container first, then its content; the outgoing element fades before or while the incoming appears, never a long gap of emptiness.
- **Layout changes.** Animate items to their new positions when a list reorders or an item is removed, so the user can follow; snap when many items change at once.
- **Do not animate between routes by default.** Fast, instant navigation with stable layout usually beats a transition. Add page transitions only where they explain a relationship.
- **Performance constraint on design**: prefer changes of transform and opacity; animating size and position properties that trigger layout causes dropped frames on modest devices. Techniques belong to `0x:frontend-foundations`.

## Micro-interactions

| Moment | Design |
|---|---|
| Press | Visible within 100ms: darker step or scale to about 0.97; release restores |
| Toggle, checkbox | Thumb or mark animates in 120 to 160ms; state change is immediate in data |
| Success, routine | In place and brief: check mark replaces spinner, label changes to "Saved", row highlight fades over about 1s. No modal, no confetti |
| Success, milestone | One celebratory moment for rare achievements (first invoice paid, setup complete); skippable, never repeated for routine actions |
| Error, field | Message appears with a short fade; optional single small horizontal shake (under 400ms) on a rejected submit; focus moves to the first error. Color plus icon plus text, never motion alone |
| Error, action | Optimistic change rolls back visibly; toast or inline message explains; retry offered |
| Copy to clipboard | Icon swaps to a check and label to "Copied" for about 1.5 to 2s, then reverts |
| Delete with undo | Item collapses and fades (about 200ms); toast with Undo; on undo the item returns to its original position |
| Drag: pick up | Item lifts (slight scale and shadow) within 100ms; cursor changes; original position shows a placeholder |
| Drag: move | Item follows the pointer exactly, with no easing lag; other items shift to show the drop position; valid drop targets highlight, invalid ones do not |
| Drag: drop | Item settles into place with a short spring (150 to 250ms); cancel returns it to origin |
| New content arriving | Fades or slides in at its position; if the user has scrolled away, show a "New items" pill instead of moving the page |
| Number changes | Update instantly for values users read precisely; a brief count animation only on dashboards and with tabular figures |

Every drag interaction needs a non-drag alternative (move up and down controls or a menu); this is a WCAG 2.2 requirement and also serves touch and keyboard users. Details belong to `0x:accessibility`.

Sound and haptics: off by default in web products; haptics only in packaged mobile apps and only for confirmations.

## Motion tokens and reduced motion

Tokens keep timing consistent and give one place to switch motion down.

```css
:root {
  --duration-instant: 80ms;
  --duration-fast: 150ms;
  --duration-base: 220ms;
  --duration-slow: 350ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-fast: 0.01ms;
    --duration-base: 0.01ms;
    --duration-slow: 0.01ms;
  }
}
```

- **Three or four durations and three easings** cover a product. Name them by role (fast, base, slow; enter, exit, move), and use only tokens in components. If a JavaScript animation library is used, feed it the same values from one module so CSS and script agree.
- **Reduced motion means reduce, not remove.** The preference exists mainly for people who get dizzy or nauseous from movement. What to change:

| With motion | Reduced-motion variant |
|---|---|
| Slides, scales, zooms, parallax, large position changes | Replace with a short cross-fade or an instant change |
| Scroll-triggered and scroll-linked animation, smooth scrolling | Disable; jump directly |
| Auto-playing video, animated backgrounds, carousels that advance | Paused until the user starts them |
| Spring and bounce | Remove overshoot |
| Opacity fades, color changes, focus ring | Keep |
| Progress indicators and spinners | Keep; they convey status. Simplify a shimmering skeleton to a static block |

- The near-zero duration in the example makes token-driven transitions effectively instant; for the patterns in the left column, prefer an explicit alternative (a fade) written under the media query over simply zeroing time, so state changes stay perceivable.
- Do not blanket-disable every animation and transition with a universal selector when scripts wait for animation end events; components that depend on those events can hang. Test each overlay in reduced-motion mode.
- An in-app "reduce motion" setting is worth adding only for motion-heavy products; otherwise follow the system preference.
- Essential motion (a progress bar's advance, a video the user played) is unaffected by the preference.

## Checks

- Each animation maps to one of the four jobs; decorative loops are gone.
- Every control shows a response within 100ms of press.
- With the network throttled to a slow profile, each screen shows the right loading pattern, without flicker on fast responses and without layout shift on arrival.
- Optimistic updates were tested with a forced failure: the rollback is visible and explained.
- No component uses a raw duration or curve; only motion tokens.
- With the operating system's reduce-motion setting on, no element slides, zooms or parallaxes, nothing autoplays, and every state change is still perceivable.
- Rapidly opening and closing a menu or dialog never leaves it stuck, and typing or clicking during a transition works.
- On a mid-range phone, transitions do not stutter.
- Every drag interaction has a keyboard and single-pointer alternative.

## Ask the user

- **Is the product a calm work tool or an expressive consumer experience?** Sets the whole motion budget. Default: work tool; fast, subtle, functional motion only.
- **Which one or two moments deserve celebration?** Limits delight to where it has value. Default: completing setup and the first core success.
- **Which actions can safely be optimistic?** A wrong optimistic update on money or messages is a trust problem. Default: toggles, renames, reorders and list additions only.
- **How long do the slowest operations take (imports, reports, generation)?** Decides between inline progress and background jobs with notification. Default: anything over about 10 seconds becomes a background job with status.
- **Are low-end devices or slow networks common among users?** Shifts effort from transitions to loading states. Default: yes; design loading states first and treat transitions as optional.
