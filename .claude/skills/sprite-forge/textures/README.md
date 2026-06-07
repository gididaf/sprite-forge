# Textures

Seam-correct, tileable surface templates — the texture equivalent of `../rigs/`.
Each is a static SVG that has already solved the hard part of a texture: **seamless
tiling**. Start from one, recolour with a `../styles/` palette, tune the pattern,
then bake with `sprite-forge <file>.svg --tileable`.

All use `viewBox="0 0 64 64"` and a neutral-ish palette so they restyle freely.

## Index

| Template | Use for | Surface |
|----------|---------|---------|
| `brick.svg` | Brick walls, masonry | opaque |
| `stone_block.svg` | Castle/dungeon ashlar, big cut stone | opaque |
| `cobblestone.svg` | Streets, paths, packed rounded stones | opaque |
| `wood_planks.svg` | Floors, crates, doors, decking | opaque |
| `metal_plate.svg` | Riveted hull/floor plating, industrial | opaque |
| `tile_checker.svg` | Tiled floors, bathrooms, temples | opaque |
| `fabric.svg` | Banners, cloth, tapestry, woven cloth | opaque |
| `scifi_panel.svg` | Tech walls, hull panels, reactors (glow strip) | opaque |
| `dirt_ground.svg` | Earth, paths, terrain | opaque |
| `concrete.svg` | Concrete, plaster, bunkers | opaque |
| `organic.svg` | Moss / rust / marble — generic mottled surface | opaque |
| `liquid.svg` | Water / lava — **animated** (scrolling caustics); bakes static at t=0 too | opaque |
| `forcefield.svg` | Energy barrier / force field — **animated** (pulsing grid + nodes) | decal (transparent) |

## The one rule: seamlessness comes from GEOMETRY, not noise

librsvg's `feTurbulence stitchTiles="stitch"` is **not pixel-perfect** — full-strength
noise as the dominant signal leaves visible seams (measured mean ~43/255). So:

- **Make the structure tile by construction.** Two patterns guarantee matching edges:
  1. **Edge-straddle** — position a gap/feature so it is split across the tile edge
     (half above, half below). See `brick.svg`: a mortar gap straddles each edge, so
     the opposite edge pixels are identical. Offset rows draw bricks at `x=-14` and
     `x=50` that run off one edge and re-enter the other.
  2. **Inset border** — keep every feature inside a uniform border (e.g. a frame or
     grout that straddles the edges). See `metal_plate.svg` / `tile_checker.svg`:
     each tile is one framed panel, so all four edges are the same seam colour.
- **Noise is a LOW-OPACITY overlay only.** `feTurbulence` (stitched, with the filter
  region pinned to `0 0 64 64` via `filterUnits="userSpaceOnUse"`) adds grit on top of
  a solid base at low opacity (~0.2–0.4). At that strength the residual seam stays
  well under the seamless threshold. See `dirt_ground.svg` / `organic.svg`.

The baker self-checks every render: `seam_error` measures opposite-edge difference and
the `--tileable` run prints `[seam] ... (seamless | SEAM VISIBLE)`. Flat-geometry
templates measure ~0; tuned noise overlays ~1–3; a broken wrap measures ~20+.

## Opaque surfaces vs alpha decals

These templates paint a full-bleed background rect → **opaque** walls/floors. For an
alpha **decal** (grate, vines, cracks, blood, sign) that sits *on top* of another
surface, simply omit the background rect — the pipeline renders RGBA and the baker
auto-detects transparency (`hasAlpha`/`surface: decal` in the metadata).

## Animating a texture

Bake with `--tileable --animated` to produce a looping texture (flipbook sheet per
size + GIF + an animated 3×3 seam-check GIF). An animated texture must be seamless on
**two axes**:

- **Space** — the static edge-wrap rule above, checked per frame.
- **Time** — the loop must return to its start. Author **cyclic SMIL** whose `values`
  end where they begin, ideally translating by exactly one tile/wavelength so the last
  frame flows back into the first. `liquid.svg` scrolls caustic crests one wavelength
  (`values="0 0; -32 0"`, wavelength 32) — a clean loop (`loopError.ratio≈1`).

**Make the motion visible:** scrolling a feature that is uniform along the scroll axis
(e.g. a full-width horizontal band scrolled sideways) shows nothing. Give the moving
feature structure across the scroll direction — wavy crests, dashes, blobs.

You can animate any template by adding cyclic SMIL (e.g. pulse `scifi_panel.svg`'s glow
strip opacity). The bake prints `[loop] … ratio=R (loops cleanly | LOOP POPS)`.
