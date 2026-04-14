# Sprite Forge

Generate 2D game sprite sheets from text descriptions using [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

Describe a character ("skeleton warrior walking left"), and Sprite Forge generates an animated SVG, bakes the animation frames, and outputs a game-ready PNG sprite sheet with mirroring and metadata.

## How it works

```
You: /sprite-forge "goblin warrior walking left with a spear"

Claude: generates SVG → saves goblin_warrior_walk_left.svg → runs pipeline

Output:
  goblin_warrior_walk_left.svg                  ← animated source (editable)
  goblin_warrior_walk_left_spritesheet.png      ← 8-frame horizontal strip
  goblin_warrior_walk_left_spritesheet_mirror.png  ← right-facing version
  goblin_warrior_walk_left_spritesheet.json     ← frame count, size, fps, etc.
```

The SVG is the source of truth. Sprite sheets can always be regenerated from it.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash
```

This clones the repo, installs dependencies, and sets up both the CLI tool and the Claude Code skill.

### Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (for the `/sprite-forge` skill)
- Python 3.10+
- [Pillow](https://pillow.readthedocs.io/) (`pip3 install Pillow`)
- [librsvg](https://wiki.gnome.org/Projects/LibRsvg) (`brew install librsvg` on macOS, `apt install librsvg2-bin` on Linux)

## Usage

### Generate sprites (via Claude Code)

Start a Claude Code session anywhere and use the skill:

```
# Generate a new sprite from a text description
/sprite-forge "skeleton warrior walking left"

# Modify an existing SVG in place
/sprite-forge "make the eyes glow red" --modify skeleton_walk_left.svg

# Create a new sprite using an existing one as reference
/sprite-forge "now make it run" --template skeleton_walk_left.svg
```

Claude generates the SVG directly — no subprocess calls, no API keys beyond your Claude Code subscription.

### Convert SVGs (standalone CLI)

If you already have an animated SVG, convert it directly:

```bash
# Default: 8 frames, 64x64, with mirror + metadata
sprite-forge hero_walk_left.svg

# Custom settings
sprite-forge hero_walk_left.svg --frames 12 --size 128 --preview

# Minimal output
sprite-forge hero_walk_left.svg --no-mirror --no-meta
```

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--frames N` | 8 | Number of animation frames to extract |
| `--size N` | 64 | Frame size in pixels (square) |
| `--output PATH` | auto | Output PNG path |
| `--mirror/--no-mirror` | on | Generate a horizontally-flipped sprite sheet |
| `--meta/--no-meta` | on | Generate JSON metadata file |
| `--preview/--no-preview` | off | Generate HTML preview with animated playback |
| `--keep-frames` | off | Keep individual frame PNGs |
| `--duration SECS` | auto | Override animation duration |

## SVG conventions

Sprite Forge uses specific SVG conventions that Claude follows when generating sprites. These matter if you're hand-editing SVGs or building your own:

- **Facing**: side-view characters face LEFT. Use `--mirror` for the right-facing version.
- **ViewBox**: `0 0 64 64` for standard characters, `0 0 80 64` for wider ones.
- **Animation**: SMIL only (`<animate>`, `<animateTransform>`). No CSS animations — the baking engine interpolates SMIL keyframes.
- **Layering**: back limbs (darker) → body → front limbs, for depth.
- **Walk cycle**: 0.4s–0.8s duration, `repeatCount="indefinite"`.
- **Body bob**: subtle `translate(0,0; 0,-1; 0,0)` on the root `<svg>`.
- **Shadow**: `<ellipse>` at feet with `fill="rgba(0,0,0,0.15)"`.

## How the pipeline works

1. **Parse** the SVG and detect the animation duration
2. **Bake** each frame: evaluate SMIL `<animate>`/`<animateTransform>` at evenly-spaced time points, replacing animation elements with static attribute values
3. **Render** each baked SVG to PNG via `rsvg-convert`
4. **Stitch** frames into a horizontal sprite sheet
5. **Mirror** each frame individually for the flipped version
6. **Output** metadata JSON and optional HTML preview

## License

MIT
