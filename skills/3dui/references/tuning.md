# Tuning the look

Read this when a render looks wrong. Every entry was hit while testing the engine.

## A flat metal face renders black

A mirror shows one direction. A flat face seen from a camera at (polar, azimuth) reflects the
single direction at the same polar angle on the opposite side (azimuth + 180°). If nothing
bright sits there, the face is black, however good the material is.

- `createStudio(renderer, { hero: { polar, azimuth } })` places the key softbox in the hero
  camera's mirror direction, `offAxis` degrees to the side (default 30). `Engine` passes the
  first cue automatically, so the hero shot is lit by construction.
- Other beats use other camera angles. If a face goes black at a later cue, either move that
  cue's `polar`/`azimuth` toward the hero's, or add a second softbox in `createStudio` for it.
- The faint horizon glow in the studio exists so faces seen edge-on in side views keep a dim
  sheen. Raise its `0.09` peak if side views still look empty.

## A face blows out to flat white

The softbox is too bright or too uniform for that finish.

- The softbox has a centre-to-rim falloff on purpose: the face should show a gradient. If you
  replace it with a uniform panel, expect a white sheet.
- Lower the softbox peak (third argument of `softbox(...)`, default 2.6) before touching the
  material. What the camera sees is roughly `peak × metal colour`; steel `#a6a29c` is about 0.36
  in linear light, so a peak of 2.6 lands just under white.
- Global exposure: `renderer.toneMappingExposure` (default 1).

## The whole object glows

Bloom threshold is too low. Keep it at or above 1.0 in HDR (`createPost`), so only the strip
lights' reflections bloom. The strips are deliberately far brighter than the softbox (7 against
2.6) for exactly this reason: they are the glints.

## Brushed finish runs the wrong way

Highlights stretch across the grooves. If a finish looks rotated a quarter turn on your
geometry, set `material.anisotropyRotation = Math.PI / 2`. `brushMap` directions assume the
top-face UVs that `extrudePart` generates (0..1 across the part's bounds); geometry from another
source needs matching UVs or the `concentric` and `sunburst` maps will not be centred.

## Edges look like CAD

- Check the bevel exists: `bevel: 0.05` (mm) and at least 3 bevel segments.
- Check the part has two materials. One material on both groups removes the face/edge contrast.
- The edge material should be much smoother than the face: roughness about 0.06 against 0.3.
- An edge only lights up if a strip light is in its mirror direction. Rotate a strip, or the
  object, until the line appears along the edge you care about.

## Glass looks like grey plastic, or has a hot spot

`glass()` is black, additive and reflection-only: all you should see is the studio in it.
- Give it `renderOrder` above the opaque parts so it draws last.
- Remove any punctual light from the scene.
- For thick, refracting glass (a bottle body) use `gem()`-style transmission on that one part
  and accept the extra render pass; keep thin covers and lenses on `glass()`.

## Shapes look faceted or the page is slow to start

- `traceLoops` cell size is the sample spacing in mm (default 0.08). Halve it for small parts
  with tight curves; double it for big simple plates. Tracing cost grows with 1 / cell².
- Lathe segments: 96 to 128 is enough for hero parts.
- If start-up is slow, build heavy parts after the first frame (`requestIdleCallback`) and add
  them to the scene when ready.

## Phone-specific

- Pixel ratio is capped at 1.75 on coarse-pointer devices; do not raise it.
- The first tap on a touch screen unlocks audio and tilt on release, not on press: browsers only
  count `pointerup` as a user gesture for touch. `holdTo` handles this; do not move the unlock.
- iOS asks permission for tilt (`DeviceOrientationEvent.requestPermission`), and only inside a
  gesture. If the user declines, the cursor path simply stays idle; nothing else should break.
