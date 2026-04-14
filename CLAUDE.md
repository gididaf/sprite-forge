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

- **Side-view characters**: draw facing LEFT first. Use `--mirror` flag to auto-generate the right-facing version
- **ViewBox**: use `viewBox="0 0 64 64"` for standard characters, `viewBox="0 0 80 64"` for wider ones (spiders, etc.)
- **Animations**: use SMIL elements (`<animate>`, `<animateTransform>`) with `dur` and `values` attributes. Avoid CSS animations — the baking engine only handles SMIL
- **Walk cycle duration**: 0.4s-0.8s is typical. Use `repeatCount="indefinite"` for looping
- **Layering**: draw back limbs first (further from viewer, darker color), then body, then front limbs. This creates depth
- **Animation transforms**: put `<animateTransform>` as a direct child of the element being animated, not in a wrapper `<g>`. The baking engine expects parent-child relationship
- **Body bob**: add a subtle `translate(0,0; 0,-1; 0,0)` animateTransform on the root `<svg>` for natural walking bounce
- **Shadows**: use an `<ellipse>` with `fill="rgba(0,0,0,0.15)"` at the character's feet
- **Mirroring**: do NOT use `scale(-1,1)` transforms to create right-facing versions — it breaks in SVG. Always use the `--mirror` flag on the script instead

## Usage

### Via Claude Code skill (recommended)

```
/sprite-forge "skeleton warrior walking left"
/sprite-forge "make it red" --modify hero_walk_left.svg
/sprite-forge "add a shield" --template hero_walk_left.svg
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
  --mirror         Generate a horizontally-flipped sprite sheet (default: on, --no-mirror to disable)
  --meta           Generate a JSON metadata file (default: on, --no-meta to disable)
  --keep-frames    Keep individual frame PNGs in INPUT_frames/ directory
  --duration SECS  Override auto-detected animation duration
  --preview        Generate preview HTML (default: off)
```

### Output files

For an input `hero_walk_left.svg`, the script produces:
- `hero_walk_left_spritesheet.png` — horizontal sprite sheet
- `hero_walk_left_spritesheet_mirror.png` — flipped version (on by default, `--no-mirror` to skip)
- `hero_walk_left_spritesheet.json` — metadata (on by default, `--no-meta` to skip)
- `hero_walk_left_preview.html` — visual preview with animated playback (off by default, `--preview` to enable)
- `hero_walk_left_frames/` — individual PNGs (if `--keep-frames`)

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
