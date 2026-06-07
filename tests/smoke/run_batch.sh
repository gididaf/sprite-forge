#!/usr/bin/env bash
# Autonomous smoke-test battery for sprite-forge.
# Each case is a FRESH headless `claude -p` session in its own dir, exercising
# the /sprite-forge skill end-to-end (generate / modify / template / directional
# sets / batch). Requires the `claude` CLI on PATH and the skill installed.
#
# Usage:   SF_SMOKE_ROOT=/tmp/sf_smoke ./run_batch.sh
#          (defaults to /tmp/sf_smoke). Then: python3 evaluate.py
set -uo pipefail

ROOT="${SF_SMOKE_ROOT:-/tmp/sf_smoke}"
mkdir -p "$ROOT"
FLAGS=(--dangerously-skip-permissions --output-format json --max-turns 160)
SUMMARY="$ROOT/summary.tsv"
printf "case\tis_error\tduration_s\tcost_usd\tnum_turns\tfiles\n" > "$SUMMARY"

run() {
  local id="$1" dir="$2" to="$3" prompt="$4"
  mkdir -p "$dir"; cd "$dir" || return
  echo "[$(date +%H:%M:%S)] START $id :: $prompt"
  timeout "$to" claude -p "$prompt" "${FLAGS[@]}" < /dev/null > "$dir/result.json" 2> "$dir/err.log"
  local ec=$?
  python3 - "$dir/result.json" "$id" "$SUMMARY" "$ec" <<'PY'
import json,sys,os,glob
res,idv,summ,ec=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]
try: d=json.load(open(res))
except Exception as e: d={"is_error":True,"result":"PARSE_FAIL %s"%e,"duration_ms":0,"total_cost_usd":0,"num_turns":0}
dirn=os.path.dirname(res); skip={"result.json","err.log"}
files=",".join(sorted(os.path.basename(p) for p in glob.glob(dirn+"/*") if os.path.basename(p) not in skip))
dur=round((d.get("duration_ms") or 0)/1000,1)
open(summ,'a').write("%s\t%s\t%s\t%s\t%s\t%s\n"%(idv,d.get('is_error'),dur,d.get('total_cost_usd'),d.get('num_turns'),files))
print("  -> %s is_error=%s dur=%ss cost=%s turns=%s (exit %s)"%(idv,d.get('is_error'),dur,d.get('total_cost_usd'),d.get('num_turns'),ec))
PY
  echo "[$(date +%H:%M:%S)] END   $id"
}

# A2: side-scroller (anchor for modify/template tests)
run A2 "$ROOT/A2_knight_sidescroller" 1800 "/sprite-forge a side-scroller knight walking"

ANCHOR=$(ls -t "$ROOT/A2_knight_sidescroller"/*_left.svg 2>/dev/null | head -1)
[ -z "$ANCHOR" ] && ANCHOR=$(ls -t "$ROOT/A2_knight_sidescroller"/*.svg 2>/dev/null | grep -v _right | head -1)
if [ -n "$ANCHOR" ]; then
  BASE=$(basename "$ANCHOR")
  mkdir -p "$ROOT/A7_modify" "$ROOT/A8_template"
  cp "$ANCHOR" "$ROOT/A7_modify/"; cp "$ANCHOR" "$ROOT/A8_template/"
  run A7 "$ROOT/A7_modify"   1200 "/sprite-forge make it red, modify $BASE"          # modify in place
  run A8 "$ROOT/A8_template" 1800 "/sprite-forge a wizard, based on $BASE"            # template -> new file
else
  echo "[skip] A7/A8 skipped — A2 produced no anchor SVG" | tee -a "$SUMMARY"
fi

run A3 "$ROOT/A3_hero_top4"        2700 "/sprite-forge a top-down RPG hero walking, 4 directions"
run A4 "$ROOT/A4_hero_top8"        3300 "/sprite-forge a top-down hero walking, 8 directions"
run A5 "$ROOT/A5_goblin_ambiguous" 1800 "/sprite-forge a goblin walking"             # ambiguous (headless: defaults)
run A6 "$ROOT/A6_knight_sword_rh"  1800 "/sprite-forge a knight holding a sword in his right hand, side-scroller"
run A9 "$ROOT/A9_batch_monsters"   3600 "/sprite-forge make a goblin, an ogre, and an orc, all side-scroller"
run A10 "$ROOT/A10_texture_brick"  1800 "/sprite-forge a seamless brick wall texture"   # texture mode
run A11 "$ROOT/A11_texture_water_anim" 1800 "/sprite-forge a seamless flowing water texture, animated"  # animated texture

echo "[$(date +%H:%M:%S)] ===== BATCH COMPLETE ====="
cat "$SUMMARY"
