#!/usr/bin/env bash
# sprite-forge — OPTIONAL reference-image generator.
#
# Generates N candidate concept-art references with a local FLUX model (mflux,
# Apple-MLX) so a sprite can be GROUNDED on real reference art. This is
# design-level grounding (palette / gear / silhouette / pose), NOT tracing and
# NOT a directional turnaround — base FLUX cannot produce clean per-angle views,
# so you generate ONE design reference and render the angles yourself.
#
# Usage:
#   gen-references.sh --prompt "PROMPT" [--count 3] [--out-dir ./_refs] \
#       [--seeds "11 22 33"] [--width 512] [--height 768] [--steps 4] [--stem ref]
#
# Prints one absolute PNG path per line on success.
# Exit codes:
#   0  ok — candidates written
#   2  bad usage (no prompt)
#   3  mflux not installed  -> caller MUST fall back to cold generation
set -euo pipefail

VENV="${SPRITE_FORGE_IMGGEN:-$HOME/.sprite-forge/imggen-venv}"
MODEL="${SPRITE_FORGE_FLUX_MODEL:-dhairyashil/FLUX.1-schnell-mflux-4bit}"
BASE_MODEL="${SPRITE_FORGE_FLUX_BASE:-schnell}"

PROMPT=""; COUNT=3; OUT_DIR="./_refs"; SEEDS=""
WIDTH=512; HEIGHT=768; STEPS=4; STEM="ref"

while [ $# -gt 0 ]; do
  case "$1" in
    --prompt)  PROMPT="$2"; shift 2;;
    --count)   COUNT="$2"; shift 2;;
    --out-dir) OUT_DIR="$2"; shift 2;;
    --seeds)   SEEDS="$2"; shift 2;;
    --width)   WIDTH="$2"; shift 2;;
    --height)  HEIGHT="$2"; shift 2;;
    --steps)   STEPS="$2"; shift 2;;
    --stem)    STEM="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [ -z "$PROMPT" ]; then
  echo "ERROR: --prompt is required" >&2
  exit 2
fi

# --- graceful dependency gate: caller falls back to cold generation on exit 3 ---
if [ ! -x "$VENV/bin/mflux-generate" ]; then
  {
    echo "mflux (local FLUX image model) is not installed — reference grounding unavailable."
    echo "Install it (one-time) with the sibling script:"
    echo "    bash \"$(cd "$(dirname "$0")" && pwd)/install.sh\""
    echo "Then the first generation downloads the model (~9.6GB, cached forever)."
  } >&2
  exit 3
fi

# default seeds: 11, 22, 33, ...  (deterministic so reruns are reproducible)
if [ -z "$SEEDS" ]; then
  s=""
  i=1
  while [ "$i" -le "$COUNT" ]; do s="$s $((i*11))"; i=$((i+1)); done
  SEEDS="$s"
fi

mkdir -p "$OUT_DIR"
OUT_ABS="$(cd "$OUT_DIR" && pwd)"

for SEED in $SEEDS; do
  OUT="$OUT_ABS/${STEM}_${SEED}.png"
  env HF_HUB_ENABLE_HF_TRANSFER=1 "$VENV/bin/mflux-generate" \
      --model "$MODEL" --base-model "$BASE_MODEL" \
      --steps "$STEPS" --width "$WIDTH" --height "$HEIGHT" --seed "$SEED" \
      --prompt "$PROMPT" --output "$OUT" >/dev/null 2>&1
  echo "$OUT"
done
