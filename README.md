# 🔥 Sprite Forge

**Generate animated 2D game sprites from plain English — powered by [Claude Code](https://docs.anthropic.com/en/docs/claude-code).**

Describe a character, get a game-ready sprite sheet.

```
/sprite-forge dragon flying left, breathing fire
```

→ animated SVG → baked frames → PNG sprite sheet + GIF + metadata, in any orientation (side-scroller, top-down, or a full directional set). Ready to drop into Unity, Godot, Phaser, LÖVE, or whatever engine you're using.

---

## 🎨 Showcase

Every sprite below was generated from a single text description. No art skills, no asset store, no subscription fees beyond Claude Code itself.

<table>
  <tr>
    <td align="center"><img src="showcase/skeleton_warrior_walk_left.svg" width="128"/><br/><sub><i>"skeleton warrior walking left"</i></sub></td>
    <td align="center"><img src="showcase/wizard_cast_left.svg" width="128"/><br/><sub><i>"wizard casting a spell"</i></sub></td>
    <td align="center"><img src="showcase/slime_bounce.svg" width="128"/><br/><sub><i>"slime bouncing"</i></sub></td>
    <td align="center"><img src="showcase/knight_attack_left.svg" width="128"/><br/><sub><i>"knight attacking with a sword"</i></sub></td>
    <td align="center"><img src="showcase/archer_draw_left.svg" width="128"/><br/><sub><i>"archer drawing a bow"</i></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="showcase/dragon_fly_left.svg" width="128"/><br/><sub><i>"dragon flying, breathing fire"</i></sub></td>
    <td align="center"><img src="showcase/spider_crawl_left.svg" width="128"/><br/><sub><i>"spider crawling"</i></sub></td>
    <td align="center"><img src="showcase/ninja_run_left.svg" width="128"/><br/><sub><i>"ninja running with a kunai"</i></sub></td>
    <td align="center"><img src="showcase/treasure_chest_open.svg" width="128"/><br/><sub><i>"treasure chest opening"</i></sub></td>
    <td align="center"><img src="showcase/fire_elemental_idle.svg" width="128"/><br/><sub><i>"fire elemental idle"</i></sub></td>
  </tr>
</table>

The sprites above are the *animated SVGs themselves*, rendered inline by your browser — no GIF conversion, no video player. Each source file is 1–3 KB, vector, infinitely scalable, and auto-plays without click-to-start controls. The pipeline also produces 64×64 PNG sprite sheets (JSON metadata, animated GIFs, and optional flipped/directional siblings via `--flip-to`) for game-engine import. Sources in [`showcase/`](showcase/) — tweak and re-run the pipeline.

---

## 🚀 Install

```bash
curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash
```

That's it. The installer sets up the CLI tool, the Claude Code skill, and all dependencies.

**Requirements:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Python 3.10+, Pillow, librsvg. The install script handles the last three.

---

## ⚡ Quick start

Open Claude Code in any directory and type:

```
/sprite-forge goblin warrior with a club, walking left
```

Claude generates the SVG, runs the conversion pipeline, and hands you:

```
goblin_warrior_walk_left.svg              ← animated source (editable)
goblin_warrior_walk_left_spritesheet.png  ← 8-frame horizontal strip
goblin_warrior_walk_left.gif              ← animated preview
goblin_warrior_walk_left_spritesheet.json ← frame data for your engine
```

Need the right-facing version too? One render produces both:

```
goblin_warrior_walk_right_spritesheet.png ← flipped sibling via --flip-to
goblin_warrior_walk_right.gif
goblin_warrior_walk_right_spritesheet.json
```

The SVG is the source of truth — tweak it and re-run the pipeline anytime.

---

## 🔄 Iterate naturally

No flags to memorize. Just describe what you want.

```
/sprite-forge make the eyes glow red, modify skeleton_walk_left.svg
/sprite-forge now make it run, based on skeleton_walk_left.svg
/sprite-forge add a shield, based on skeleton_walk_left.svg
```

Claude reads the existing SVG, applies your change, and regenerates the sprite sheet. No re-prompting from scratch.

---

## 🛠 Standalone CLI

Already have an animated SVG? Convert it directly:

```bash
# Default: 8 frames, 64×64, sprite sheet + GIF + metadata
sprite-forge hero_walk_left.svg

# Also emit a flipped right-facing sibling (sheet + gif + meta) in one render
sprite-forge hero_walk_left.svg --facing left --flip-to hero_walk_right

# Higher resolution, more frames, with HTML preview
sprite-forge hero_walk_left.svg --frames 12 --size 128 --preview
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--frames N` | 8 | Number of animation frames |
| `--size N` | 64 | Frame size in pixels (square) |
| `--output PATH` | auto | Output PNG path |
| `--flip-to NAME` | — | Emit a complete flipped sibling deliverable (sheet + gif + meta) named `NAME_*` — preferred for right-facing directions |
| `--facing LABEL` | — | Record facing (`left`, `down`, `up`, `downleft`, …) in the metadata |
| `--mirror` / `--no-mirror` | off | Generate a generic `_mirror.png` flipped sheet (legacy — prefer `--flip-to`) |
| `--meta` / `--no-meta` | on | Emit JSON metadata |
| `--gif` / `--no-gif` | on | Animated GIF (great for READMEs / Discord / wikis) |
| `--preview` | off | Generate animated HTML preview |
| `--silhouette` | off | Black-on-white silhouette of frame 0 (readability check) |
| `--keep-frames` | off | Keep individual frame PNGs |
| `--duration SECS` | auto | Override animation duration |

---

## 🧠 Why it works

Sprite Forge leans on Claude Code's native ability to generate SVG — no external APIs, no subscription on top of Claude Code, no training pipeline.

The pipeline:

1. **Parse** — read the SVG and auto-detect animation duration
2. **Bake** — sample `<animate>` / `<animateTransform>` values at N evenly-spaced time points, producing N static SVG snapshots
3. **Render** — rasterize each snapshot via `rsvg-convert`
4. **Stitch** — combine frames into a horizontal sprite sheet
5. **Flip** (`--flip-to`, optional) — flip each frame individually to derive the opposite-facing direction (preserving per-frame geometry, unlike a blanket `scale(-1,1)` transform)
6. **Emit** — metadata JSON + optional animated HTML preview

The `/sprite-forge` skill bundles a visual review loop: Claude reads its own generated sprite sheet, grades it against a correctness spec, and iterates until it looks right (hard cap: 3 iterations). For subjects involving directional physics (archers, casters) it can spawn a fresh-eyes subagent reviewer to catch blind spots.

---

## 📐 SVG conventions

If you're hand-editing SVGs or extending the skill:

- **Orientation**: the skill is orientation-aware — side-scroller (left/right), top-down 4-/8-way, or single/non-directional. Draw the non-flippable directions; derive the right-facing twins with `--flip-to`.
- **ViewBox**: `0 0 64 64` standard, `0 0 80 64` for wide characters (spiders, dragons).
- **Animation**: SMIL only (`<animate>`, `<animateTransform>`). CSS animations aren't baked.
- **Layering**: back limbs (darker) → body → front limbs for depth.
- **Body width in profile**: ≤ 7px — wider torsos read as front-facing regardless of head detail.
- **Limb thickness**: ≥ 5px — thinner disappears at 64×64.
- **Animation pitfalls**: keep rotation pivots constant across keyframes; don't nest more than one `additive="sum"` rotate per hierarchy branch (the frame baker doesn't resolve them cleanly).

---

## 🤝 Contributing

PRs welcome — especially new sprite archetypes for the showcase, or improvements to the baking engine. Keep SVGs small and hand-editable; no binary assets in the repo except the showcase PNGs.

## 📄 License

MIT
