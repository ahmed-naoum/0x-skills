# Animation on the web

Read this when: adding a transition, enter/exit effect, page transition or scroll effect in CSS or JavaScript; choosing whether
a library is needed; or an animation stutters. What should move and why is a design question (`0x:ui-ux-design`); this file is
how to build it so it is smooth, interruptible and safe.

## Keep motion on the compositor

Animate `transform` (and the individual `translate`, `scale`, `rotate` properties) and `opacity`. These can be applied by the
compositor to an already-painted layer, so they skip layout and paint and keep running while the main thread is busy. Animating
anything that affects geometry runs layout every frame.

| Wanted effect | Do not animate | Animate instead |
|---|---|---|
| Move | `top`, `left`, `margin` | `translate` |
| Grow or shrink | `width`, `height` | `scale` (children distort: see FLIP below), or a grid-track or `clip-path` reveal |
| Expand to content height | `height` from a guess, `max-height: 999px` | The techniques under "Enter, exit and auto height" |
| Shadow on hover | `box-shadow` | `opacity` of a pseudo-element that carries the larger shadow |
| Fade | `visibility`, `display` alone | `opacity`, with the discrete properties switched at the end |
| Blur or tint change | Large-area `filter: blur()` or `backdrop-filter` on scroll | A pre-blurred image or a cross-fade between two layers |

- Compositor-only holds only when the browser runs the animation: CSS transitions and animations, the Web Animations API, and
  scroll-driven animations. A `requestAnimationFrame` loop that sets `style.transform` each frame is still main-thread work and
  stutters whenever JavaScript is busy.
- `will-change: transform` promotes an element to its own layer ahead of time. Each layer costs GPU memory proportional to its
  pixel area times the device pixel ratio squared; too many crash mobile tabs. Add it just before a known animation (on hover
  intent, on mount of a drawer), remove it afterwards, and never put it in a blanket rule.
- Colors and backgrounds repaint but do not lay out; animating them on small elements is fine.
- A custom property animates smoothly only if registered with `@property` (so the browser knows its type), and then runs on the
  main thread.
- Timing as rules of thumb: 100–200 ms for feedback on a control, 200–300 ms for panels and overlays, up to about 500 ms for
  large or full-screen moves; exits faster than entrances. Ease-out for things entering, ease-in for things leaving, ease-in-out
  for moves within the screen, linear only for continuous progress. The CSS `linear()` function expresses springs and bounces as
  a sampled curve without JavaScript.
- Prefer transitions for state changes: reversing mid-flight is automatic. A keyframe animation restarted mid-flight jumps.

## CSS, Web Animations API or a library

| The effect | Tool |
|---|---|
| A to B on a state change (hover, open, selected, theme) | CSS `transition` |
| Self-running or looping keyframes (spinner, skeleton shimmer, attention pulse) | CSS `@keyframes` |
| Values known only at runtime, or the code must await, pause, reverse or seek | Web Animations API: `el.animate(keyframes, options)` |
| Element entering or leaving the DOM | CSS `@starting-style` and discrete transitions; in React, the component library's presence handling |
| Layout change (reorder, expand, shared element between views) | View Transitions, or a layout-animation library |
| Drag, swipe-to-dismiss, springs that carry gesture velocity | A motion library (Motion for React is the usual choice) |
| Long choreographed sequences, scroll-pinned storytelling | A timeline library (GSAP), or scroll-driven CSS for simple cases |
| Illustrations animated by a designer | Lottie or Rive player, loaded lazily |

Default: CSS until it stops being enough, and CSS only at Prototype. Bring in a library when the effect needs two or more of: interruption that preserves
velocity, exit animations of unmounting components, layout animation, gestures, or orchestration across many elements. One
library per project; check its bundle cost and whether it can be loaded only on the routes that use it (`0x:web-performance`).
Check the license terms of commercial animation libraries before adopting them in a product.

Web Animations API essentials:

```js
const anim = el.animate(
  [{ opacity: 0, translate: '0 8px' }, { opacity: 1, translate: '0 0' }],
  { duration: 200, easing: 'ease-out' }
);
await anim.finished;      // rejects with AbortError if cancelled
```

Avoid leaving animations parked with `fill: 'forwards'`: they keep overriding the element's styles and accumulate. Set the final
style in CSS or a class and let the animation end, or use `fill: 'forwards'` only until `finished`, then call
`anim.commitStyles()` and `anim.cancel()` (without a fill there is nothing left to commit).
`el.getAnimations()` lists what is running; cancel them on teardown.

## Reduced motion

`prefers-reduced-motion: reduce` is set by people for whom movement causes nausea, dizziness or distraction. Honoring it does
not mean removing all animation; it means removing *motion*.

| Remove or replace | Keep |
|---|---|
| Large translations, zooms, rotations, parallax, scroll-linked movement | Opacity fades and color changes |
| Auto-playing carousels, video backgrounds, looping decorative motion | Progress indicators and spinners (people need to know something is happening) |
| Page and shared-element transitions that slide or morph | A short cross-fade in their place |
| Bouncy springs, smooth-scroll jumps | Instant state change with a brief fade |

```css
.drawer { transition: translate 250ms ease-out, opacity 250ms ease-out; }
@media (prefers-reduced-motion: reduce) {
  .drawer { transition: opacity 150ms linear; }
  html { scroll-behavior: auto; }
}
```

- Write the alternative per component. The blanket "set every duration to near zero with `!important`" reset is a backstop that
  also kills useful fades and progress feedback, and it does nothing for JavaScript-driven motion.
- In JavaScript read `matchMedia('(prefers-reduced-motion: reduce)')` and listen for `change`. Motion libraries have a global
  setting for it (Motion: `<MotionConfig reducedMotion="user">`); turn it on at the app root, since it is not the default.
- Anything that moves for more than five seconds on its own needs a pause control regardless of this setting, and nothing may
  flash more than three times a second (`0x:accessibility`).
- Test with DevTools → Rendering → emulate `prefers-reduced-motion`.

## Page transitions with View Transitions

The browser snapshots the old state, runs a DOM update, snapshots the new state, and animates between them: a cross-fade by
default, and a position-and-size morph for elements that carry the same `view-transition-name` in both states.

```js
function navigate(update) {
  if (!document.startViewTransition) { update(); return; }
  document.startViewTransition(update);         // update must change the DOM synchronously or return a promise
}
```

```css
.product-image { view-transition-name: product-hero; }
::view-transition-group(product-hero) { animation-duration: 250ms; }
@media (prefers-reduced-motion: reduce) {
  ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none; }
}
```

- Same-document transitions (`document.startViewTransition`) are Baseline Newly available, not Widely: keep the feature check
  above. Cross-document transitions for ordinary multi-page navigation are opt-in from CSS on both pages
  (`@view-transition { navigation: auto; }`), same-origin only, and were missing from at least one engine at the time of
  writing; treat them as an enhancement, since unsupported browsers simply navigate.
- Each `view-transition-name` must be unique among rendered elements at capture time, or the whole transition is skipped. For
  lists, set the name only on the item being opened (inline style at click time), not on every card.
- The page does not respond to input while the transition runs, and rendering is paused while the update callback is pending.
  Fetch data *before* starting the transition, keep the callback to the DOM swap, and keep durations at or under about 300 ms.
- Snapshots are images. Text that changes size is stretched during the morph; animate only the group's position, or cross-fade,
  for elements whose aspect ratio changes.
- Fixed or sticky headers slide with the root snapshot unless given their own name.
- In React, a state update is not synchronous: wrap it with `flushSync` inside the callback, or use the framework's built-in
  view-transition support if the installed version provides it as stable (`0x:react-nextjs`).
- Direction-aware transitions: pass `types` (`startViewTransition({ update, types: ['back'] })`) and style with
  `:active-view-transition-type(back)`. Types shipped later than the base API, and an engine without them rejects the object
  argument: test `CSS.supports('selector(:active-view-transition-type(x))')` and fall back to the plain callback form.

## Scroll-driven animation

Link an animation's progress to scroll position in CSS; the browser can run it off the main thread, unlike a `scroll` listener
that measures and writes styles every frame.

```css
@keyframes fade-up { from { opacity: 0; translate: 0 2rem; } }

@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .reveal {
      animation: fade-up linear both;
      animation-timeline: view();
      animation-range: entry 0% entry 80%;
    }
  }
}
```

- `scroll()` ties progress to a scroller's position (reading-progress bars, shrinking headers); `view()` ties it to an element's
  passage through the viewport (reveals, parallax).
- `animation-timeline` must come after the `animation` shorthand, which resets it.
- Support reached the last major engine only recently (Baseline Newly available at best), so many browsers in use lack it:
  keep the `@supports` guard. Because the animation's keyframes define the hidden state, an unsupported browser shows the
  element in its normal, visible state. Never put `opacity: 0` in the base style waiting for an animation to reveal it:
  without support, or with JavaScript failing, the content stays invisible.
- For "animate once when it enters" (not scrubbed with scroll), use an `IntersectionObserver` that adds a class and unobserves;
  with the visible state as default and the hidden start state applied only once JS has run.
- Carousels: CSS scroll snap (`scroll-snap-type`, `scroll-snap-align`) on a native scroller, not transform-based sliders that
  reimplement scrolling. Never hijack the page's scroll speed or direction.
- Pinned, multi-stage scroll scenes that must behave identically everywhere are the case for a scroll library; budget for it as
  a marketing-page feature, not an app feature.

## Enter, exit and auto height

Entering: an element that goes from `display: none` (or not in the DOM) to visible has no "before" style to transition from.
`@starting-style` supplies it. Exiting: `display` and the top-layer `overlay` property switch instantly unless told to wait with
`transition-behavior: allow-discrete`.

```css
[popover] {
  opacity: 0; translate: 0 0.5rem;
  transition: opacity 200ms, translate 200ms,
              display 200ms allow-discrete, overlay 200ms allow-discrete;
}
[popover]:popover-open { opacity: 1; translate: 0 0; }
@starting-style { [popover]:popover-open { opacity: 0; translate: 0 0.5rem; } }
```

- The same pattern works for `<dialog>` (`dialog[open]`, and `::backdrop`). Where a browser lacks these features the element
  appears and disappears instantly, which is an acceptable fallback.
- React removes an unmounting component immediately, so there is nothing left to animate. Use the primitive library's presence
  support (Radix-style components keep the node mounted and expose `data-state="open|closed"` until the CSS animation ends), a
  motion library's presence wrapper, or keep the element mounted and toggle a class.
- Height to and from `auto`:
  - Cross-browser today: wrap the content and animate a grid track.

    ```css
    .collapsible { display: grid; grid-template-rows: 0fr; transition: grid-template-rows 250ms ease-out; }
    .collapsible[data-open] { grid-template-rows: 1fr; }
    .collapsible > div { overflow: hidden; min-height: 0; }
    ```

  - Where supported, `interpolate-size: allow-keywords` on `:root` lets `height: 0` transition to `height: auto` directly. Use
    it as an enhancement after checking Baseline.
  - Both animate layout, so keep the content small and the duration short; for long lists, cross-fade instead.
- Collapsed content must also be unreachable: `inert` or `visibility: hidden` at the end of the exit, so hidden links do not
  take focus.

## Layout changes: FLIP

When an element's position or size changes because the layout changed (reorder, filter, expand), animate the *difference* with
transforms: First (measure), Last (apply the change and measure again), Invert (transform it back to where it was), Play
(animate the transform to none).

```js
const first = el.getBoundingClientRect();
applyChange();                                    // DOM or class update, synchronous
const last = el.getBoundingClientRect();
el.animate(
  [{ transformOrigin: 'top left',
     transform: `translate(${first.left - last.left}px, ${first.top - last.top}px) ` +
                `scale(${first.width / last.width}, ${first.height / last.height})` },
   { transformOrigin: 'top left', transform: 'none' }],
  { duration: 250, easing: 'ease-out' }
);
```

- Measure all elements before changing anything, then apply, then measure all again: mixing reads and writes per element
  thrashes layout.
- Scaling distorts children, text and border radius. For boxes containing text, animate only the translation and let the size
  change instantly or cross-fade; libraries correct the distortion by counter-scaling children.
- Use View Transitions as the native version when the change is a discrete state swap. Use a layout-animation library (Motion's
  `layout` and `layoutId`, or a drop-in list animator) when the animation must be interruptible, continuous with gestures, or
  scoped to a component in a busy page.

## Profiling jank

At 60 Hz a frame has 16.7 ms, at 120 Hz 8.3 ms, and the browser needs part of that. Profile on the slow device, not the
development machine.

1. Performance panel, CPU throttled 4–6×, record while triggering the animation. Remote-debug a mid-range Android phone for the
   real answer.
2. Read the Frames track for dropped or partially presented frames, then the Main track beneath those frames: long purple blocks
   are style and layout, green is paint, yellow is script.
3. Rendering drawer: Paint flashing (what repaints each frame), Layer borders, the frame-rate meter. Layers panel: how many
   layers exist, their memory, and why each was created.

| Symptom | Cause | Fix |
|---|---|---|
| Layout in every frame | Animating a geometry property, or JS reading layout in the loop | Switch to transform/opacity; batch reads before writes |
| Smooth alone, stutters while data loads or the app renders | Animation driven from the main thread | Move it to CSS or the Web Animations API with compositor properties; break up long tasks |
| Hitch on the first frame only | Layer creation, image decode or font load at start | Promote with `will-change` just beforehand; `await img.decode()`; have assets ready before starting |
| Fine on desktop, bad on phones | Too many or too large layers; big blurs, shadows and `backdrop-filter` | Reduce layer count and area; replace live blur with a static image |
| Whole screen flashes in paint flashing | A paint-triggering property on a large ancestor, or the animated element is not isolated | Move the effect to a small element on its own layer |
| Scroll stutters | Non-passive touch or wheel listeners; work in `scroll` handlers | Passive listeners; scroll-driven CSS or observers |
| Jank appears only with many items | Per-element animations and layers scale linearly | Animate one container; stagger fewer items; consider canvas |

## Sequencing and leaving the DOM

- Two or three steps: chain `await anim.finished`, or use `animation-delay`/`transition-delay`. Stagger lists with an index
  custom property (`transition-delay: calc(var(--i) * 40ms)`) and cap the total at roughly 300–400 ms by staggering only the
  first several items.
- Beyond that, use a timeline (GSAP timelines, Motion's sequence API): steps are positioned relative to each other, so changing
  one duration does not require recomputing every delay. Drive it from application state (a small state machine), make it
  killable, and kill it on unmount; nested `setTimeout` chains cannot be cancelled or reversed and leak.
- Keep durations and easings as tokens shared with CSS, so sequences and simple transitions feel like one product.
- Move from DOM to canvas when the count of simultaneously animated elements reaches the hundreds to low thousands, or the
  effect is per-pixel: particles, dense data visualization, physics, fluid or shader effects. Canvas 2D handles thousands of
  simple sprites; WebGL or WebGPU handles far more and anything shader-based (`0x:3dui` owns 3D scenes).
- What canvas costs: no accessibility tree, text selection, layout, responsive reflow or find-in-page. Keep text and controls in
  the DOM above a decorative canvas marked `aria-hidden="true"`, with a static fallback for reduced motion.
- Canvas hygiene: size the backing store to `cssSize × devicePixelRatio` (capped at about 2, a rule of thumb), stop the loop when the canvas is
  off-screen (`IntersectionObserver`) or the tab is hidden, and consider `OffscreenCanvas` in a worker for heavy drawing.
- A pre-rendered video is often the right answer for a complex non-interactive hero animation.

## Ask the user

- **Is this motion functional or decorative?** Functional motion (showing where something went) is worth engineering effort;
  decorative motion is the first thing to cut for performance. Default: build functional motion in CSS; treat decorative motion
  as optional enhancement.
- **Is an animation library acceptable in the bundle?** It adds weight and a dependency. Default: no library until an effect
  needs gestures, exits or layout animation.
- **How must it behave on low-end phones?** Decides whether heavy effects are disabled by device capability. Default: effects
  must hold frame rate on a mid-range Android phone or be simplified there.
- **Are scroll-driven storytelling sections worth their cost?** They take disproportionate time to build and test. Default:
  simple reveal-on-enter only, until Launch-stage marketing pages justify more.
