# Smoke tests

End-to-end smoke battery for the `/sprite-forge` skill. Each case runs a **fresh
headless `claude -p` session** and exercises one capability:

| Case | Capability |
|------|-----------|
| A2 | side-scroller set (`left` drawn + `right` flipped) |
| A7 | modify mode (edit in place) |
| A8 | template mode (new file, source preserved) |
| A3 | top-down 4-way set |
| A4 | top-down 8-way set (5 drawn + 3 mirror-derived) |
| A5 | ambiguous request (headless: degrades to a sensible default) |
| A6 | handedness / mirror-asymmetry caveat |
| A9 | batch of distinct subjects |

## Requirements
- `claude` CLI on PATH, signed in.
- The `/sprite-forge` skill installed (see repo root `install.sh`).
- `sprite-forge` CLI on PATH, `Pillow` + `rsvg-convert` available.

## Run
```bash
SF_SMOKE_ROOT=/tmp/sf_smoke ./run_batch.sh      # ~60-120 min, spawns real sessions
SF_SMOKE_ROOT=/tmp/sf_smoke python3 evaluate.py  # structural verdicts
```
`run_batch.sh` uses `--dangerously-skip-permissions` so the nested sessions can
run the converter unattended — only run it in a throwaway working dir.

## What `evaluate.py` checks
- Correct filename suffixes per perspective (none for non-directional).
- Drawn directions have `.svg` sources; mirror-derived directions do **not**.
- Per-frame flip correctness (`right` == per-frame mirror of `left`, etc.).
- `_set.json` manifests are valid and reference real files.
- No stray `_mirror.png`, and **no clobbered deliverables** (a `_spritesheet.png`
  must be a wide N-frame strip, never square — guards the inspection-render
  clobber bug).
- Surfaces each session's own FAIL/UNCLEAR/caveat lines.

Verdicts are structural. For animation/visual quality, review the GIFs (or spawn
a fresh-eyes vision subagent per the skill's review conventions).
