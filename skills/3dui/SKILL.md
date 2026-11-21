---
name: 3dui
description: Build live 3D product websites with three.js and Next.js, where the object is procedural code (no video files, no downloaded models), lit like a photo studio and directed by the scroll. Use for a 3D hero or product page, a scroll-driven 3D story, an exploded view, realistic metal or glass in WebGL, or replacing a scroll-video with real-time 3D. Ships a tested engine to copy.
---

# 3dui: live 3D product sites

A scroll-video site plays back pixels someone else rendered. A live site renders them itself,
every frame, on the visitor's device, so it can react to cursor, tilt, scroll and touch, and it
ships in a few hundred kB instead of a 20 MB video.

Four layers, built in this order:

1. **Geometry**: every part built from code, in real millimetres.
2. **Materials**: physical metal and glass.
3. **Light**: a photo studio inside the scene.
4. **Direction**: the scroll moves the camera.

The method comes from the guide "Build 3D websites that run live" (Parallel Studios). The engine
in `assets/engine/` is a working implementation of it: type-checked against three r187 and
rendered in a browser at every scroll beat. **Copy it and replace the product; do not rewrite it
from memory.** It is about 155 kB gzipped including three.js.

## Start here

```bash
npx create-next-app@latest my-site   # TypeScript, App Router
npm i three && npm i -D @types/three
```

Copy `assets/engine/` to `app/engine/` and the three files in `assets/next/` to `app/`. Run it:
you get a brushed-metal demo object with all five scroll beats working. Then replace
`engine/product.ts` with the real object.

| File | What it owns |
|---|---|
| `engine/Engine.ts` | The one class you control: renderer, loop, resize, cursor, wiring |
| `engine/geometry.ts` | 2D signed-distance shapes → `traceLoops` (marching squares) → `extrudePart`; `lathePart` |
| `engine/look.ts` | `metal`, `faceAndEdge`, `glass`, `heatTint`, `lacquer`, `gem`, `brushMap`, `createStudio` |
| `engine/director.ts` | Camera cue list, scroll blending, framing by size |
| `engine/show.ts` | `explode`, `stack`, callouts, `blueprint`, scroll-driven text reveals |
| `engine/pulse.ts` | One clock (`Pulse`), Web Audio `Synth`, `holdTo`, `enableTilt` |
| `engine/post.ts` | MSAA HDR → bloom → ACES → grain, and the adaptive-quality `Governor` |
| `engine/product.ts` | **The part you replace**: the object and its cue list |
| `next/page.tsx`, `Scene.tsx`, `scene.css` | The page: one fixed canvas behind, HTML sections in front |

## The nine steps

### 1. Pick one object, give it one verb

The object is the star; the verb is the one thing the visitor does to it. Objects that work have
many parts and real materials (metal, glass, stone): camera lens, headphones, synth, engine,
fragrance bottle, lighter. Verbs that work are physical, one-thumb, and change the object: hold
to power up, twist, open, pull apart, tilt to light.

Before any code, write down:
- **Every part and its real size in millimetres.** Real units keep proportions honest. If the
  user has not given sizes, look up or estimate real ones and state them; do not invent a scale.
- **The one frame you would screenshot** for the thumbnail. That is the hero cue.
- **The scroll story in five beats**: hero, close-up, apart, around, back together.

### 2. One canvas behind, the story in front

Next.js for the page, plain three.js for the 3D (no React wrapper around the scene: one engine
class you fully control). One fixed full-screen canvas; normal HTML sections scroll over it.
Use `assets/next/` as is.

Rule: the page wrapper uses `overflow-x: clip`, never `hidden`. `hidden` turns the page into a
scroll box and every sticky section stops sticking.

### 3. Build every part from code

Sketch each flat part from simple 2D shapes, melt them together, trace the outline, extrude with
a polished edge:

```ts
const plate = subtract(
  smooth(1.2, circle(0, 0, 3), capsule(0, 0, 12, 4, 1.1), circle(12, 4, 2)), // 1.2 mm fillet
  circle(12, 4, 0.8),                                                        // a hole
);
const geo = extrudePart(plate, { depth: 2, bevel: 0.05 });
```

Rule: **a 0.05 mm bevel is the gap between CAD and luxury. Edges are where the light lives.**
`extrudePart` sets bevel size and thickness together and pulls the bevel inward, so the part's
outer dimension stays exactly what you drew. Round parts (knobs, barrels, necks) use
`lathePart([[radius, height], ...])`.

### 4. Metal is a mirror, finish is the brand

Use `MeshPhysicalMaterial` with `metalness: 1`. On metal, colour is only the tint of the
reflection; roughness decides polished or satin. Brushed finishes are anisotropy plus a
direction texture generated in code at boot (`brushMap`: `straight`, `concentric`, `sunburst`).

Rule: **two materials per part: the flat face and the edge.** `extrudePart` gives group 0 =
faces, group 1 = walls and bevel, so `new THREE.Mesh(geo, [...faceAndEdge({ brush: "straight" })])`
gives a satin face with a polished edge. That contrast is what reads as expensive.

Special surfaces: `heatTint` (iridescence) for heat-tinted steel, `lacquer` (clearcoat),
`gem` (IOR and transmission; costs an extra render pass, use on one part).

### 5. Light it like a photographer

Metal is only as good as what it reflects. `createStudio` builds a tiny studio (dark room, one
off-axis softbox, two strip lights), bakes it into the environment with `PMREMGenerator`, and
the engine rotates it with the cursor every frame. **The environment is the only light. Add no
`DirectionalLight` or `PointLight`.**

Rule: glass reflects the studio only. `glass()` is a black, additive, reflection-only material;
a direct light on it makes a fake hot spot in the middle.

Read `references/tuning.md` when a face renders black, blows out to white, or looks flat.

### 6. Let the scroll direct the camera

Write a camera script: a list of cues pinned to page sections. The engine blends between the
two nearest cues by scroll position, then eases toward the result every frame.

```ts
{ id: "hero",  at: 0,   shot: { frame: 52, polar: 14, offsetX: 0.17 } },
{ id: "close", at: 0.4, shot: { frame: 12, timeScale: 1 / 12 } },
{ id: "apart", at: 0.9, shot: { frame: 80, polar: 60, explode: 1 } },
```

Rule: **frame by size, not distance.** `frame: 52` means "fit 52 mm on screen", so the same cue
works on a phone and a monitor. A cue inherits everything it does not set from the cue before
it. `<section data-cue="hero">` pins that cue to the section's top; `at` is the fallback.

### 7. Take it apart on camera

The exploded view is the money shot. Every part gets a lift and an order: top parts leave first
and come back last (`explode(parts, e)`; `stack(objects, gap, labels)` builds the part records
from a vertical stack). Callouts project each part to the screen every frame and stack the
labels in two clean columns with leader lines. `engine.toggleBlueprint()` swaps every surface
for its edges: instant proof it is geometry, not a video.

### 8. Give it a pulse

Do not keyframe it; simulate it. One clock (`Pulse`) drives every moving part through
`product.pose(time)`, so motion stays connected and nothing drifts. Slow motion is one multiply:
`timeScale: 1 / 12` in the close-up cue. Events fire on the beat (`pulse.onBeat`).

Sound is synthesized with Web Audio (`Synth`: filtered noise bursts for ticks, taps and thunks),
so there are zero audio files. The hold-to gesture (`holdTo`) drives a progress ring, and its
first tap also unlocks audio and phone tilt, which browsers gate behind a user gesture.

### 9. Finish it like film, ship it light

`createPost` runs scene → MSAA HDR → bloom → ACES tone mapping → grain. Bloom has a high
threshold so only glints bloom, never the whole object. The `Governor` caps pixel ratio at 1.75
on phones and, if the frame rate drops under 40, steps resolution down and then turns bloom off.
`Engine.start` compiles every shader behind the loader (`compileAsync`) so the first scroll does
not hitch.

## Five bugs that cost hours

| Symptom | Cause and fix |
|---|---|
| Sticky sections stopped sticking | `overflow-x: hidden` on the page wrapper. Use `clip`. |
| Round parts rendered inside out | Lathe profile drawn clockwise. Faces point to the right of the path; `lathePart` rewinds closed profiles for you, open profiles must run bottom to top for an outer wall. |
| A hot spot in the middle of the glass | A direct light hit it. Glass reflects the environment only, blended additively on top. |
| Text reveals randomly missed | `IntersectionObserver` skips beats on heavy GPU frames. Drive reveals from scroll position in the render loop (`scrollReveals`, `data-reveal`). |
| Screenshots lied | Headless browsers render WebGL at about 1 fps. Screenshots are for composition and lighting only; judge motion on a real phone. |

## Checking your work

Screenshot every section and fix what looks off; do not report a 3D page as done unseen.

- Scroll to each `data-cue` section, wait about two seconds, then capture. In a headless browser
  set `engine.director.damping = 1e4` first so the camera snaps to the cue instead of easing at
  1 fps, and launch Chromium with `--use-angle=swiftshader --enable-unsafe-swiftshader`.
- Capture a phone viewport (390 × 844) as well as desktop: check the object still fits and the
  callout labels stay on screen.
- In a headless run the `Governor` will see the low frame rate and switch bloom off after a few
  seconds. That is correct behaviour, not a bug; capture the hero first if you want bloom in it.
- Say plainly what screenshots cannot show: motion smoothness, sound, tilt and real-device frame
  rate still need a person with a phone.

## The director's brief

When starting from a blank repo or handing the build to another agent, brief it like a director:

> Build a Next.js page with one fixed three.js canvas behind the content. The hero is a
> **[OBJECT]**, built entirely from procedural geometry: 2D signed-distance shapes, traced and
> extruded with 0.05 mm polished bevels, in real millimetres.
>
> Materials: MeshPhysicalMaterial, metalness 1, anisotropic finishes generated as textures,
> satin faces with polished edges.
>
> Light it with a PMREM studio: dark room, one off-axis softbox, two strip lights. Rotate the
> environment with the cursor.
>
> Drive the camera from a scroll cue list. Add a staggered exploded view, two-column callouts, a
> blueprint toggle, a hold-to-**[VERB]** interaction with Web Audio sound, and post: bloom,
> ACES, grain. Screenshot every section and fix what looks off.
