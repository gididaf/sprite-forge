# Sprite Forge

A tool for generating 2D game sprite sheets — and seamless tileable surface textures — using Claude Code + SVG.

## Architecture

- **`/sprite-forge` skill** — Claude generates SVGs directly (no subprocess CLI calls). Two artifact kinds, routed by intent: **sprites** (generate / modify / template modes; animated, directional) and **textures** (tileable surfaces; static). See `.claude/skills/sprite-forge/SKILL.md` ("Artifact routing" + "Texture mode").
- **`sprite-forge.py`** — Conversion pipeline only. No AI code. Two entry points: `run_pipeline` (animated SVG → PNG sprite sheet) and `run_texture_pipeline` (static SVG → seamless texture tiles + a seam-check grid + texture metadata, via `--tileable`).
- **Reference grounding (optional)** — `.claude/skills/sprite-forge/reference/` generates concept-art reference images with a local FLUX model (`mflux`, Apple-MLX) so a sprite can be *grounded* on real reference art before Claude draws. **Off by default**, intent-triggered (see SKILL.md "Reference grounding"), with graceful fallback to cold generation when `mflux` is absent. Design-level grounding only — Claude draws fresh from the reference, never traces it; one design reference per subject, Claude renders the directions itself (base FLUX can't do per-angle turnarounds). The image model is *not* Claude — shelling out to `mflux` is fine; the "no subprocess CLI" rule is specifically about not calling the `claude` CLI for AI work.

## Workflow

1. User invokes `/sprite-forge "skeleton warrior walking left"`
2. Claude generates an animated SVG following the conventions below
3. Claude saves the SVG and runs `sprite-forge <file>.svg` to convert
4. User reviews output and iterates

## SVG conventions

When generating animated SVGs for this project:

- **Orientation-aware**: there is no universal "face left" rule. Pick a perspective per request — **side-scroller** (left/right), **top-down 4-way** (down/up/left/right), **top-down 8-way** (+diagonals), or **single/non-directional** (objects, projectiles, symmetric creatures). The skill drives this; see `.claude/skills/sprite-forge/SKILL.md`
- **Draw fresh vs. mirror**: only draw the non-flippable directions by hand (left, down=front, up=back, and the left-side diagonals). Derive the right-facing twins with `--flip-to` — never redraw them
- **ViewBox**: use `viewBox="0 0 64 64"` for standard characters, `viewBox="0 0 80 64"` for wider ones (spiders, etc.)
- **Animations**: use SMIL elements (`<animate>`, `<animateTransform>`) with `dur` and `values` attributes. Avoid CSS animations — the baking engine only handles SMIL
- **Walk cycle duration**: 0.4s-0.8s is typical. Use `repeatCount="indefinite"` for looping
- **Layering**: draw back limbs first (further from viewer, darker color), then body, then front limbs. This creates depth
- **Animation transforms**: put `<animateTransform>` as a direct child of the element being animated, not in a wrapper `<g>`. The baking engine expects parent-child relationship
- **Body bob**: add a subtle `translate(0,0; 0,-1; 0,0)` animateTransform on the root `<svg>` for natural walking bounce
- **Shadows**: use an `<ellipse>` with `fill="rgba(0,0,0,0.15)"` at the character's feet
- **Mirroring**: do NOT use `scale(-1,1)` transforms to create flipped versions — it breaks in SVG. Use the `--flip-to NAME` flag instead, which emits a complete flipped sibling deliverable (sheet + gif + meta) under a directional name. Mirroring is off by default

## Texture conventions

When generating tileable surface textures (Texture mode — see the skill):

- **Seamlessness is built by geometry, not noise.** librsvg's `feTurbulence stitchTiles="stitch"` is not pixel-perfect, so noise is only ever a low-opacity (~0.2–0.4) overlay on a solid/geometric base. Make opposite edges identical via **edge-straddling** (a gap/feature split across the tile edge; features that exit one edge re-enter the other) or an **inset border** (every feature inside a uniform frame/grout that straddles the edges)
- **Start from a template.** `.claude/skills/sprite-forge/textures/` ships 13 seam-correct templates (brick, stone_block, cobblestone, wood_planks, metal_plate, tile_checker, fabric, scifi_panel, dirt_ground, concrete, organic, plus the animated `liquid` and `forcefield`) — the texture equivalent of `rigs/`
- **ViewBox**: `viewBox="0 0 64 64"`. Pin any filter region to the tile with `filterUnits="userSpaceOnUse"` and `x/y/width/height` = the viewBox
- **The baker self-checks seams.** `run_texture_pipeline` measures opposite-edge difference (`seam_error`) and prints `[seam] edge-wrap error mean=N (seamless | SEAM VISIBLE)`. Flat geometry ≈ 0, tuned noise ≈ 1–3, broken wrap ≈ 20+ (threshold 8.0). Also eyeball the `_tilecheck.png` grid
- **Opaque vs decal**: paint a full-bleed background rect for opaque walls/floors; omit it for a transparent decal overlay (grate, vines, cracks). Transparency is auto-detected into the metadata
- **No facing, no direction set** for textures. Textures are usually static; **looping animated textures** (water, lava, scrolling glow) are supported via `--tileable --animated` — author **cyclic SMIL** (values return to start, e.g. translate by one wavelength) and give the moving feature structure across the scroll axis (a flat band scrolled sideways shows no motion). The bake checks both axes: spatial seam (per frame) + temporal `loopError.ratio` (≈1 = clean loop). `textures/liquid.svg` is the reference animated template

## Usage

### Via Claude Code skill (recommended)

```
/sprite-forge skeleton warrior walking left
/sprite-forge make it red, modify hero_walk_left.svg
/sprite-forge add a shield, based on hero_walk_left.svg
/sprite-forge a seamless mossy brick wall texture
/sprite-forge a Byzantine cataphract, use a reference
```

For the last one, Claude generates a few FLUX reference images, you pick one, and it grounds the sprite on your pick (optional — see SKILL.md "Reference grounding"; needs the optional `mflux` dependency).

### Direct conversion (standalone)

```bash
sprite-forge hero_walk_left.svg
sprite-forge hero_walk_left.svg --frames 6 --size 128
sprite-forge hero_walk_left.svg --preview --keep-frames

# Texture mode
sprite-forge brick_wall_texture.svg --tileable --material brick
sprite-forge brick_wall_texture.svg --tileable --sizes 128,256 --tile-grid 4
```

### Conversion options

```
Options:
  --frames N       Number of frames to extract (default: 8)
  --size N         Frame size in pixels, square (default: 64)
  --output PATH    Output PNG path (default: INPUT_spritesheet.png)
  --flip-to NAME   Also emit a complete horizontally-flipped sibling deliverable
                   (sheet + gif + meta) named NAME_* — e.g. --flip-to hero_walk_right.
                   This is the preferred way to derive a right-facing direction.
  --facing LABEL   Record this facing label (left, down, up, downleft, ...) in the metadata
  --mirror         Generate a generic INPUT_spritesheet_mirror.png (default: off; legacy — prefer --flip-to)
  --meta           Generate a JSON metadata file (default: on, --no-meta to disable)
  --gif            Generate animated GIF (default: on, --no-gif to disable)
  --keep-frames    Keep individual frame PNGs in INPUT_frames/ directory
  --duration SECS  Override auto-detected animation duration
  --preview        Generate preview HTML (default: off)
  --silhouette     Generate a black-on-white silhouette of frame 0 for readability checks (default: off)

Texture mode (with --tileable):
  --tileable       Render a seamlessly tiling surface texture instead of a sprite sheet
  --sizes A,B,C    Comma-separated power-of-two sizes to emit (default: 64,128,256; supersedes --size)
  --tile-grid N    Emit an NxN tiled seam-check PNG (default: 3, 0 disables)
  --material NAME  Material label recorded in the texture metadata
  --animated       Bake a looping animated texture from the SVG's cyclic SMIL
                   (flipbook sheet per size + GIF + animated NxN seam-check)
```

### Output files

For an input `hero_walk_left.svg`, the script produces:
- `hero_walk_left_spritesheet.png` — horizontal sprite sheet
- `hero_walk_left_spritesheet.json` — metadata (on by default, `--no-meta` to skip)
- `hero_walk_left.gif` — animated GIF (on by default, `--no-gif` to skip)
- `hero_walk_left_spritesheet_mirror.png` — generic flipped sheet (off by default, `--mirror` to enable; legacy)
- `hero_walk_left_silhouette.png` — black-on-white silhouette of frame 0 (off by default, `--silhouette` to enable)
- `hero_walk_left_preview.html` — visual preview with animated playback (off by default, `--preview` to enable)
- `hero_walk_left_frames/` — individual PNGs (if `--keep-frames`)

With `--flip-to hero_walk_right`, it additionally produces a flipped sibling set:
- `hero_walk_right_spritesheet.png`, `hero_walk_right.gif`, `hero_walk_right_spritesheet.json` (metadata stamped `mirrorOf`)

For a multi-direction set, the skill also writes a combined `<subject>_<action>_set.json` manifest listing every direction and whether it was drawn or mirror-derived.

In **texture mode** (`--tileable`), for an input `brick_wall_texture.svg` the script instead produces (suffixes are disjoint from the sprite ones, so the two never collide):
- `brick_wall_texture_64.png`, `_128.png`, `_256.png` — the tile at each `--sizes` variant
- `brick_wall_texture_tilecheck.png` — an N×N tiling for visual seam inspection (off with `--tile-grid 0`)
- `brick_wall_texture_texture.json` — texture metadata (`type: texture`, material, sizes, `seamError`, `seamless`, `hasAlpha`, `surface`)
- `brick_wall_texture_texture_preview.html` — variants + seam grid (off by default, `--preview` to enable)

With `--animated`, the per-size outputs are **flipbook sheets** instead and a looping GIF + animated seam-check are added — for `water_texture.svg`:
- `water_texture_64_sheet.png`, `_128_sheet.png`, `_256_sheet.png` — N-frame horizontal flipbook per size
- `water_texture.gif` — looping single-tile preview
- `water_texture_tilecheck.png` (frame 0) + `water_texture_tilecheck.gif` (the N×N grid in motion — checks spatial seams AND the temporal loop at once)
- `water_texture_texture.json` — adds `animated`, `frameCount`, `animationDuration`, `fps`, `loopError`, `loops`

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash
```

## Dependencies

- Python 3.10+
- Pillow (`pip3 install Pillow`) — for PNG stitching and mirroring
- `rsvg-convert` (`brew install librsvg`) — for SVG to PNG rendering
- Claude Code — for the `/sprite-forge` skill
- **Optional, for reference grounding only:** `mflux` (Apple Silicon / MLX) in an isolated venv — install via `.claude/skills/sprite-forge/reference/install.sh`. The FLUX model (~9.6 GB) is pulled on first use and cached. Not required for normal sprite/texture generation.

## File organization

SVGs and their outputs are kept together in the same directory. The SVG is the source of truth — PNGs can always be regenerated from it.
