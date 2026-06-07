# Sprite Forge

A tool for generating 2D game sprite sheets using Claude Code + SVG.

## Architecture

- **`/sprite-forge` skill** — Claude generates animated SVGs directly (no subprocess CLI calls). Handles generate, modify, and template modes.
- **`sprite-forge.py`** — Conversion pipeline only. Takes an animated SVG and produces PNG sprite sheets. No AI code.

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

## Usage

### Via Claude Code skill (recommended)

```
/sprite-forge skeleton warrior walking left
/sprite-forge make it red, modify hero_walk_left.svg
/sprite-forge add a shield, based on hero_walk_left.svg
```

### Direct conversion (standalone)

```bash
sprite-forge hero_walk_left.svg
sprite-forge hero_walk_left.svg --frames 6 --size 128
sprite-forge hero_walk_left.svg --preview --keep-frames
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

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash
```

## Dependencies

- Python 3.10+
- Pillow (`pip3 install Pillow`) — for PNG stitching and mirroring
- `rsvg-convert` (`brew install librsvg`) — for SVG to PNG rendering
- Claude Code — for the `/sprite-forge` skill

## File organization

SVGs and their outputs are kept together in the same directory. The SVG is the source of truth — PNGs can always be regenerated from it.
