# Reference grounding (optional)

An **optional** subsystem that generates concept-art reference images with a
local FLUX model (`mflux`, Apple-MLX) so a sprite can be **grounded** on real
reference art instead of drawn purely from priors. Off by default — see the
"Reference grounding" section in `SKILL.md` for *when* to use it.

## What it is (and isn't)

- **Design-level grounding, not tracing.** You *look at* the reference and lift
  its palette (hex), gear, proportions, silhouette, and pose into the Phase-1a
  spec — then draw a fresh, clean, animatable SVG. You never vectorise/trace the
  raster; tracing destroys the limb separation the animation pipeline needs.
- **One design reference, you render the angles.** Base FLUX **cannot** produce
  clean per-direction turnarounds (identity drifts; no true back/side/top-down
  views; wrong perspective). Verified empirically. So for a directional set you
  ground ONE design reference and render the 8/4 viewpoints yourself + mirror —
  exactly how a studio works from one concept sheet. Do **not** try to generate
  a turnaround per direction.
- **Take the good, fix the artifact.** Generators fumble details (e.g. "sword
  and shield" → two shields). Keep the design, fix the mistake when you draw.

## Files

- `gen-references.sh` — generate N candidates for a prompt. Prints one absolute
  PNG path per line. Exit `3` = mflux not installed (caller falls back to cold).
- `install.sh` — one-time setup: venv + `mflux`. Apple Silicon only. The model
  downloads on first generation (~9.6 GB, cached).

## Usage

```bash
# one-time (optional)
bash install.sh

# generate a batch to pick from (default 3, seeds 11/22/33)
bash gen-references.sh --prompt "full body knight with sword and shield, \
  front view, game character concept art, plain light gray background" \
  --out-dir ./_refs --count 3 --stem knight
```

Then show the candidates (`open <path>` on macOS), let the user pick one, and
feed its visual brief into Phase 1.

### Prompt recipe

`full body <subject>, <view>, game character concept art, plain light gray
background, clear silhouette[, colorful]`

- `<view>`: `side view` for side-scroller; `front view` for top-down design
  grounding (you render the other angles).
- Plain background + "clear silhouette" keep the design readable to lift.

### Knobs (env / flags)

- `--count`, `--seeds "a b c"`, `--width`, `--height`, `--steps`, `--stem`,
  `--out-dir`.
- `SPRITE_FORGE_IMGGEN` — venv path (default `~/.sprite-forge/imggen-venv`).
- `SPRITE_FORGE_FLUX_MODEL` — HF repo (default a pre-quantized 4-bit schnell).

## Cost

~10–25 s per 512×768 image on Apple Silicon (M-series), after the one-time
model download. A 3-candidate batch is ~1 min. That is the *only* real cost —
it buys design accuracy, so it is opt-in, never forced.
