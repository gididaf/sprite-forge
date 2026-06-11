#!/usr/bin/env bash
# sprite-forge — OPTIONAL one-time setup for reference grounding.
# Creates an isolated venv and installs mflux (Apple-MLX FLUX). Apple Silicon
# only. The FLUX model itself is pulled on the first generation (~9.6GB, cached).
set -euo pipefail

VENV="${SPRITE_FORGE_IMGGEN:-$HOME/.sprite-forge/imggen-venv}"
PY="${PYTHON:-python3}"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "WARNING: mflux targets Apple Silicon (Metal/MLX). Non-macOS is unsupported." >&2
fi

echo "Creating venv at $VENV ..."
"$PY" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip >/dev/null
echo "Installing mflux (this pulls MLX + transformers, a few minutes) ..."
"$VENV/bin/python" -m pip install mflux

echo
echo "Done. mflux installed in $VENV"
echo "The FLUX model downloads on the first reference generation (~9.6GB, one-time)."
echo "Test:  bash \"$(cd "$(dirname "$0")" && pwd)/gen-references.sh\" --prompt 'a knight' --count 1"
