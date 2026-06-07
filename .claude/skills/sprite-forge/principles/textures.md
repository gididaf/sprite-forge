# Texture Principles

The seven animation principles do **not** apply to static tileable textures. These four do. Consult them when authoring a texture (Texture mode, step 2) and when seam-checking (step 3).

| Principle | One-line |
|-----------|----------|
| Edge-wrapping | Seamlessness is built by geometry; opposite edges must be identical |
| Noise-as-overlay | `feTurbulence` is grit on top, never the load-bearing tiling mechanism |
| Tiling rhythm | Break up the repeat so a wall of tiles doesn't scream "grid" |
| Light direction | One consistent light angle across every bevel and cast shadow |
| Temporal loop | (animated only) the loop must return to its start without a jump |

---

## 1. Edge-wrapping

A texture tiles seamlessly only when its **opposite edges are identical**: the right column must equal the left column, and the bottom row must equal the top row, so that copies placed side-by-side show no break. This is a property you *construct*, not one you hope for.

Two reliable constructions:

- **Edge-straddle** — place a gap or feature so it is split across the tile boundary, half on each side. A mortar gap centred on the edge means both edge columns are mortar → identical. Features that run off one edge are re-drawn entering the opposite edge (a brick at `x=-14` is the same brick as the one at `x=50`). The seam then falls *mid-feature* and is invisible.

  *Brick example:* module 32px wide (tile = 2 modules), pitch 16px (4 rows, ABAB offset). Even rows put a mortar gap on the edge; odd rows draw a brick straddling it at `x=-14` and `x=50`.

- **Inset border** — keep every feature strictly inside the tile, surrounded by a uniform border (frame, grout, seam) that straddles all four edges. Every edge is then the same border colour → identical. This reads as a grid of framed panels/tiles, which is exactly right for metal plating, floor tiles, and sci-fi hull panels.

The pipeline measures this for you: `seam_error` compares opposite edges and prints `[seam] edge-wrap error mean=N`. Flat edge-wrapped geometry → ~0. **If it reports SEAM VISIBLE (~20+), the geometry doesn't wrap — fix the edges. Do not try to hide a geometric seam with noise.**

### Watch out
- A pattern can *tile* (be periodic) yet still fail the edge-identity check when the period boundary lands on a feature transition (e.g. brick row at the top, mortar at the bottom). The fix is always to shift the pattern so a uniform band straddles the edge.
- Align coordinates to even/4px values. At a 256px render a 64px tile scales 4×; sub-pixel edges get anti-aliased and leak a small seam.

## 2. Noise-as-overlay (never load-bearing)

`feTurbulence` is the only practical way to get organic grain in vector SVG, but **librsvg's `stitchTiles="stitch"` is not pixel-perfect**. Measured residual seam error (0–255 scale):

- Full-strength turbulence as the dominant signal → mean ~43 (visible seams).
- Turbulence as a ~0.6-opacity overlay on a solid base → mean ~11.
- Turbulence at ~0.2–0.3 opacity → mean ~1–3 (imperceptible).

So noise is **garnish on top of a solid/geometric base**, always low opacity. Rules:

- Pin the filter region to the tile: `filterUnits="userSpaceOnUse"` with `x/y/width/height` equal to the viewBox, and `stitchTiles="stitch"`.
- Give each `feTurbulence` an explicit `seed` (reproducible) and a `baseFrequency` that suits the grain (coarse mottle ~0.05–0.1, fine grit ~0.3–0.5).
- Tint via `feColorMatrix` and keep the alpha row low (e.g. `… 0 0 0 0.3 0`).
- Layering two stitched octaves (coarse + fine) at low opacity reads richer than one strong one — and stays under the seam threshold.

## 3. Tiling rhythm — break the repeat

Even a perfectly seamless tile betrays itself if a single eye-catching feature repeats on a grid. A wall is many copies; the eye finds the pattern fast.

- **No loud singletons.** A bright crack, a unique stain, or a high-contrast knot placed once will pepper the wall in a regular lattice. Either omit it from the base tile (scatter it later as a separate decal) or distribute several so no single one anchors the grid.
- **Distribute wear non-uniformly** *within* the tile (corners vs centre) so the repeat is harder to lock onto.
- **Use offset/running-bond** layouts (brick, cobble, stone) rather than a plain grid where possible — the half-step offset hides the vertical seam line.
- Judge this on the `_tilecheck.png` 3×3 grid, not the single tile: a feature that looks fine alone may form an obvious constellation when tiled.

## 4. Light direction

Pick one light direction (conventionally top, or top-left) and keep it consistent across **every** bevel, highlight, and cast shadow in the tile — and across sibling textures meant to sit together (a wall and its floor).

- Bevels: lighter band on the top/left edge of a raised feature, darker on the bottom/right.
- Mortar/grout recesses: a thin dark line on the top-inner edge of the recess reads as depth.
- Inconsistent light (one brick lit from the left, its neighbour from the right) flattens the whole surface and looks wrong even when the tiling is flawless.

## 5. Temporal loop (animated textures only)

An animated texture (water, lava, scrolling glow) must loop in **time** as well as tile in **space**. The cycle has to return exactly to its starting state so the last frame flows back into the first with no visible jump.

- **Author cyclic SMIL.** The `values` must end where they begin. The cleanest motion translates by exactly one tile or one wavelength: `values="0 0; -32 0"` scrolls a 32px-wavelength pattern one full wavelength, so frame N == frame 0. (The baker samples `t = i/N · duration`; because the SMIL is cyclic, the wrap step `frame[N-1] → frame[0]` matches the interior steps.)
- **Make the motion visible.** Scrolling a feature that is *uniform along the scroll axis* shows nothing — a full-width horizontal band scrolled horizontally looks frozen. Give the moving feature structure across the scroll direction: wavy crests, dashes, blobs. (This was the original `liquid.svg` bug — flat bands → zero motion.)
- **The pipeline measures it.** `temporal_loop_error` compares the wrap step against the average inter-frame step and prints `[loop] … ratio=R`. `ratio≈1` loops cleanly; `ratio` ≫ 1 (threshold 2.5) means the loop pops — make the SMIL cyclic. The animated `_tilecheck.gif` (the 3×3 grid in motion) is the best single visual check of both space and time.

---

## The texture test for review (step 3, Pass B)

- **Does it wrap?** `seamError.mean` low AND no hard line in the 3×3 grid.
- **Does the repeat hide?** Scan the grid — is there an obvious lattice of one feature?
- **Does it read as the material** at the smallest size (64px), not just at 256px?
- **Is the light consistent** across every bevel and shadow?
- **Right surface type?** Opaque has a full-bleed background; a decal has a transparent one (`hasAlpha: true`).
- **(Animated) does it loop?** `loopError.ratio≈1` AND the animated `_tilecheck.gif` shows motion that wraps without a pop.
