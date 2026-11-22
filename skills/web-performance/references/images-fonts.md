# Images, video and fonts

Read this when: media or web fonts dominate page weight, the hero image is the LCP element,
text flashes or jumps when fonts load, or video and icons need delivering efficiently.

## Images: the four decisions

Every image needs the right **format**, the right **pixel size for the slot**, the right
**priority**, and **reserved space**. Most slow pages get the second one wrong: a 3000 px
photo in a 400 px card costs more than any format choice saves.

### Format

| Content | Format | Notes |
|---|---|---|
| Photos, complex images | AVIF first, WebP fallback | AVIF is clearly smaller at low and medium quality; encoding is slow, so encode once and cache |
| Photos when AVIF encoding cost or support is a problem | WebP | Supported in all current browsers |
| Logos, icons, simple illustrations | SVG | Run through SVGO; see icons below |
| Screenshots, flat graphics with text | Lossless WebP or PNG, or lossy AVIF at high quality | Check text edges by eye |
| Animation | Video (`<video muted autoplay loop playsinline>`), not GIF | GIF is many times larger than the same clip as video |

Quality settings are a rule of thumb, not a standard: AVIF around 50 to 60 and WebP around 75
to 80 look fine for photos; go higher for product detail shots, lower for backgrounds. Decide by
eye at 2x zoom on a phone, not by metric.

Two ways to serve the modern format: `<picture>` with typed sources, or one URL where the image
service negotiates on the `Accept` header (then the response must carry `Vary: Accept`, and the
CDN cache must key on it). The second is what image CDNs and framework loaders do.

```html
<picture>
  <source type="image/avif" srcset="/img/card-400.avif 400w, /img/card-800.avif 800w" sizes="(min-width: 768px) 33vw, 100vw">
  <source type="image/webp" srcset="/img/card-400.webp 400w, /img/card-800.webp 800w" sizes="(min-width: 768px) 33vw, 100vw">
  <img src="/img/card-800.jpg" width="800" height="600" alt="…" loading="lazy" decoding="async">
</picture>
```

### Responsive sizing: `srcset` and `sizes`

- Use width descriptors (`400w`) with `sizes`. The browser picks using the slot width and the
  device pixel ratio. Density descriptors (`2x`) are only for fixed-size images such as avatars.
- `sizes` describes the **rendered width of the slot**, not the image. If it is missing, the
  browser assumes `100vw` and downloads a full-viewport image for a thumbnail. If it is wrong,
  every other optimization is undone. Derive it from the layout CSS: a three-column grid above
  768 px is `(min-width: 768px) 33vw, 100vw`.
- Generate widths in steps of roughly 1.5x from the smallest slot to twice the largest (for
  example 320, 480, 720, 1080, 1600, 2400). More steps add cache entries, not quality.
- Cap at 2x density. Serving 3x to high-density phones roughly doubles bytes with no visible gain.
- Check: in DevTools, hover the image `src` in the Elements panel to compare intrinsic and
  rendered size, and read `currentSrc`. Lighthouse flags images much larger than their slot.

### Priority and reserved space

| Image | Attributes |
|---|---|
| The LCP image (usually the hero; one per page) | `fetchpriority="high"`, no `loading="lazy"`, present in server HTML, `width` and `height` set |
| Other images in the first viewport | Eager (the default), dimensions set |
| Everything below the fold | `loading="lazy"`, `decoding="async"`, dimensions set |
| Off-screen carousel slides | `loading="lazy"`, optionally `fetchpriority="low"` |

`width` and `height` attributes give the browser the aspect ratio before the file arrives; with
`height: auto` in CSS the image stays fluid and nothing shifts. For images filling a container,
set `aspect-ratio` on the container. Art-directed crops that change ratio by breakpoint need
`width` and `height` on each `<source>`.

Do not lazy-load the LCP image, and do not hide it behind a JS-driven fade-in or a carousel that
renders after hydration; both are the usual reason a small hero still has a slow LCP. The
priority mechanics and the preload fallback are in `core-web-vitals.md`.

Placeholders (blurred thumbnail, dominant color) improve perceived loading but do not improve
LCP, which is timed on the full image. Keep an inlined placeholder to a few hundred bytes.

### Resize on demand: image CDN or framework loader

Hand-exporting variants does not survive the first content editor. Default: let a service
resize, convert and cache per request.

| Option | Use when | Watch |
|---|---|---|
| Framework loader (`next/image` with the built-in optimizer) | The project is on Next.js and image volume is modest | Optimization may be metered by the host; check the plan. Self-hosted, optimized files are cached on local disk, which does not survive across instances without a CDN in front |
| Image CDN (Cloudflare Images, imgix, Cloudinary, ImageKit and similar) | Many user-uploaded or CMS images, several front ends, or optimizer cost on the host is high | Pricing models differ (per transformation, per stored image, per bandwidth); model with real numbers |
| Build-time generation | Small fixed set of images in the repository | Build time grows with image count |

`next/image` specifics that go wrong:

- With `fill` or a fluid layout, pass `sizes`; without it the generated `srcset` assumes the
  full viewport.
- Remote sources must be allowed in `images.remotePatterns`. Keep the patterns narrow: an open
  optimizer is a free resizing proxy for anyone.
- AVIF output is opt-in through `images.formats` (the default is WebP only); it costs more
  encode time on a cache miss and stores a second copy of each variant.
- The `quality` prop is checked against the `images.qualities` allowlist, which from Next.js 16
  defaults to a single value; a quality outside the list is coerced to the nearest allowed
  one. Add the values the design needs, or the lower AVIF quality suggested above never applies.
- Width and height are required for remote images unless `fill` is used; static imports get
  them automatically.
- SVG is served as-is, and the optimizer rejects it unless explicitly allowed because SVG can
  carry script. Animated images pass through unoptimized.

Rules for any on-demand service:

- Restrict the accepted widths and qualities to an allowlist (or sign URLs). Arbitrary
  `?w=` values let an attacker generate unlimited variants: cost and cache exhaustion.
- Cache transformed output for a long time under an immutable URL; change the URL when the
  source changes.
- Cap input dimensions and file size for user uploads before they reach the transformer;
  upload handling is in `0x:backend-architecture`.
- Strip metadata on output, which also removes location data from user photos. Apply the EXIF
  orientation first, or stripped photos come out sideways, and convert to sRGB or keep the
  color profile.

## Video

| Case | Delivery |
|---|---|
| Short decorative loop, under roughly ten seconds | Self-hosted MP4 (H.264) plus an AV1 or WebM source, `muted autoplay loop playsinline`, with `poster` |
| Product demo, a minute or more, user presses play | A video host (Mux, Cloudflare Stream, Bunny Stream, or an unlisted embed) with adaptive streaming; facade until click |
| User-uploaded video | Always a video service: transcoding, adaptive bitrates and storage are not a side project |
| Background hero video | Poster first; load the video only on wide viewports and when `Save-Data` is off |

Rules:

- Always set `poster`, sized and compressed like any hero image. The poster can be the LCP
  element; treat it as one (preload it if the video is the hero).
- `preload="none"` for click-to-play videos, `preload="metadata"` when duration or first frame
  is needed. With no attribute the choice is the browser's, and it may download a large part
  of a file nobody watches.
- Set `width` and `height` or `aspect-ratio`, as for images.
- Progressive MP4 must have its index at the front or playback waits for the whole file, and
  the server must support range requests (Safari requires them):

```bash
ffmpeg -i in.mov -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -movflags +faststart -an out.mp4
```

  `-an` drops audio for muted loops; remove it when sound is needed.
- Adaptive streaming (HLS or DASH) is what makes long video start fast and survive bad
  networks. Safari plays HLS natively and other browsers have been adding it; feature-detect
  with `video.canPlayType('application/vnd.apple.mpegurl')`, and where that fails load a
  player library (it is heavy) only when the user presses play.
- Below-the-fold autoplay loops: attach `src` when the element nears the viewport
  (IntersectionObserver) and pause when it leaves; decoding several videos at once is a battery
  and jank problem on phones.
- Third-party embeds are iframes with large scripts: `loading="lazy"` at minimum, a facade
  preferably (`javascript-bundles.md`).
- Respect `prefers-reduced-motion`: no autoplay for those users.

## Fonts: choose first, then load

### Choice

| Option | Cost | Choose when |
|---|---|---|
| System font stack (`font-family: system-ui, sans-serif`) | Zero bytes, zero shift | Prototype; app UI and dashboards; anywhere brand typography is not a requirement |
| One variable font file | One request covering all weights (and possibly italics on a second file) | Three or more weights or styles of the same family are used |
| One or two static files | Smallest when only regular and bold are needed | Simple marketing or content site |
| Several families, many weights | Hundreds of KB and several requests on the critical path | Avoid; each added family needs a reason |

Budget, as a rule of thumb: at most two families, and web fonts needed for the first viewport
under about 100 KB total. A subsetted Latin variable font is commonly well under that.

`system-ui` renders differently per platform, and for some scripts picks a font the design did
not expect; test on Windows and Android if the audience is international.

### Loading without flash or shift

1. **WOFF2 only.** Every current browser supports it; older formats are dead weight.
2. **Self-host** from the page's origin. A third-party font host adds a connection and, since
   browser caches are partitioned per site, gives no cross-site cache benefit. It also sends
   every visitor's IP address to that host, which has drawn privacy complaints in some
   jurisdictions (`0x:privacy-compliance`). Before self-hosting or subsetting a commercial
   font, read its license: some forbid modifying the file or meter page views.
3. **Subset.** Ship only the scripts the product uses, and split by `unicode-range` so other
   scripts download only when a page uses them:

```bash
pyftsubset Inter.ttf --unicodes="U+0000-00FF,U+2013,U+2014,U+2018-201D,U+2022,U+2026,U+20AC" \
  --layout-features='*' --flavor=woff2 --output-file=inter-latin.woff2
```

   (`pyftsubset` comes with the Python `fonttools` package; WOFF2 output needs `brotli`
   installed.) Check that currency symbols, quotes and any names in the customers' languages
   still render; a missing glyph falls back per character and looks broken.
4. **Preload only the one or two files used above the fold:**

```html
<link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
```

   `crossorigin` is required even for same-origin fonts; without it the file downloads twice.
   Preloading every weight starves the LCP image.
5. **Pick `font-display` on purpose:**

| Value | Behavior | Use for |
|---|---|---|
| `swap` | Fallback text immediately, swapped when the font arrives, however late | Body and headings, together with a metric-matched fallback |
| `optional` | Tiny block period; if the font is not there, the fallback stays for this page view | Zero layout shift guaranteed; good with preload. First visit on a slow link may never show the brand font |
| `fallback` | Short block, short swap window | Compromise between the two |
| `block` | Invisible text for up to seconds | Icon fonts only, which should be replaced anyway |

6. **Match the fallback's metrics** so the swap does not move text. Define a local fallback
   face with overrides and put it second in the stack:

```css
@font-face {
  font-family: "Inter Fallback";
  src: local("Arial");
  size-adjust: 107%; ascent-override: 90%; descent-override: 22%; line-gap-override: 0%;
}
body { font-family: "Inter", "Inter Fallback", sans-serif; }
```

   The numbers are specific to each font pair; treat the ones above as an illustration and
   generate real values with a tool (Fontaine, Capsize) or let the framework do it:
   `next/font` self-hosts, sets `font-display` (default `swap`), preloads and generates the
   adjusted fallback, and is the default in a Next.js project. `next/font/google` serves the
   subsets named in `subsets`; `next/font/local` serves the file as given, so subset a local
   font before handing it over.

Check: throttle to a slow profile, reload with cache disabled, and watch the first second.
Text should be visible immediately and should not move when the font arrives. Confirm in the
Network panel that each font file is requested once and only the faces used are requested.

Traps: a font declared in CSS but named differently in the stack downloads nothing and nobody
notices; faux bold or italic appears when a weight or style is used that was not loaded; icon
or emoji ranges inside a text font inflate it.

## Icons and SVG

- **Replace icon fonts.** They block or flash as text, ship every glyph for the few used, and
  fail for users who override fonts. Use SVG.
- **A few icons, critical to first paint:** inline `<svg>` in the HTML. No request, styleable
  with `currentColor`.
- **Many icons, reused across pages:** one external sprite of `<symbol>` elements, referenced
  with `<svg><use href="/icons.svg#check"></use></svg>`. Cached once, no JavaScript, and the
  markup stays small. The sprite must be same-origin.
- **Icons as JS components** (one React component per icon) are convenient but put SVG path
  data into the JavaScript bundle, where it is parsed as code and duplicated in server HTML and
  hydration payload. Fine for a dozen icons with per-icon imports; for hundreds, use a sprite.
- **Optimize every SVG** with SVGO: remove editor metadata, reduce path precision, keep
  `viewBox`. Exported design files are routinely several times larger than needed.
- **Heavy SVG** (illustrations with thousands of nodes, embedded bitmaps, filters) costs DOM and
  paint time when inlined. Load it as `<img src="…svg">`, or rasterize to AVIF or WebP when it
  is effectively a picture.
- Icon-only controls need an accessible name (`aria-label` on the button, `aria-hidden="true"`
  on the SVG); see `0x:accessibility`.

## Ask the user

- **Is the brand font a requirement, where, and is it licensed for self-hosted web use?**
  Decides between system fonts and web fonts, how many families, and whether the file may be
  subsetted. Default: system stack for app UI, one variable family for marketing pages, and
  an openly licensed font until the license of a commercial one is confirmed.
- **Which languages and scripts must render?** Decides subsetting and `unicode-range` splits.
  Default: Latin with common punctuation and currency symbols, other scripts in separate files.
- **Where do images come from and how many are there?** Decides between framework loader and an
  image CDN, and the cost model. Default: framework loader until the optimizer bill or
  user-uploaded volume says otherwise.
- **How important is the video, and must it autoplay?** Decides self-hosted loop versus a video
  service. Default: poster with click-to-play behind a facade; autoplay only for short muted
  loops.
- **What image quality is acceptable?** Product and portfolio sites tolerate less compression
  than blogs. Default: the mid-range settings above, reviewed by eye on the three most important
  pages.
