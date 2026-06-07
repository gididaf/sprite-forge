#!/usr/bin/env python3
"""Structural evaluator for the sprite-forge smoke battery (see run_batch.sh).

For each case dir: classify outputs by direction, verify drawn-vs-flip,
validate the set manifest, check metadata, ensure no stray _mirror files and
no clobbered deliverables (a _spritesheet.png must be a wide N-frame strip, not
square), and verify per-frame flip correctness for mirrored direction pairs.
Also surfaces FAIL/UNCLEAR/caveat lines from each session's own report.

Usage:  SF_SMOKE_ROOT=/tmp/sf_smoke python3 evaluate.py [case ...]
"""
import json, os, glob, sys
from PIL import Image, ImageChops, ImageOps

ROOT = os.environ.get("SF_SMOKE_ROOT", "/tmp/sf_smoke")
MIRROR_SRC = {"right": "left", "downright": "downleft", "upright": "upleft"}
DIRS = ["down","up","left","right","downleft","downright","upleft","upright"]

# (perspective, drawn dirs, flipped dirs)  None = freeform
EXPECT = {
    "canary_potion":          ("non-directional", [], []),
    "A2_knight_sidescroller": ("side-scroller", ["left"], ["right"]),
    "A7_modify":              ("modify-inplace", None, None),
    "A8_template":            ("template", None, None),
    "A3_hero_top4":           ("top-down-4", ["down","up","left"], ["right"]),
    "A4_hero_top8":           ("top-down-8", ["down","up","left","downleft","upleft"],
                                              ["right","downright","upright"]),
    "A5_goblin_ambiguous":    ("ambiguous-default", None, None),
    "A6_knight_sword_rh":     ("side-scroller+caveat", ["left"], ["right"]),
    "A9_batch_monsters":      ("batch", None, None),
}

def subj_dir(stem):
    for d in DIRS:
        if stem.endswith("_"+d):
            return stem[:-(len(d)+1)], d
    return stem, None

def case_files(d):
    return {os.path.basename(p) for p in glob.glob(os.path.join(d,"*"))
            if os.path.basename(p) not in ("result.json","err.log")}

def per_frame_flip_ok(left_png, right_png):
    try:
        l = Image.open(left_png).convert("RGB"); r = Image.open(right_png).convert("RGB")
    except Exception as e:
        return None, "open fail: %s"%e
    if l.size != r.size:
        return False, "size mismatch %s vs %s"%(l.size, r.size)
    n = l.width // l.height
    for i in range(n):
        lf = l.crop((i*l.height,0,(i+1)*l.height,l.height))
        rf = r.crop((i*l.height,0,(i+1)*l.height,l.height))
        if ImageChops.difference(ImageOps.mirror(lf), rf).getbbox() is not None:
            return False, "frame %d != mirror(left)"%i
    return True, "%d frames match"%n

def report_flags(result_json):
    try:
        txt = json.load(open(result_json)).get("result","") or ""
    except Exception:
        return []
    out=[]
    for line in txt.splitlines():
        low=line.lower()
        if any(k in low for k in ["fail","unclear","caveat","handedness","asymmetr","mirror","warn"]):
            s=line.strip()
            if s: out.append(s[:160])
    return out[:8]

def evaluate(case):
    d = os.path.join(ROOT, case)
    if not os.path.isdir(d): return None
    files = case_files(d)
    svgs = {subj_dir(f[:-4])[1] for f in files if f.endswith(".svg")}
    sheets = {subj_dir(f[:-len("_spritesheet.png")])[1] for f in files if f.endswith("_spritesheet.png")}
    subjects = {subj_dir(f[:-4])[0] for f in files if f.endswith(".svg")}
    findings=[]; level=["PASS"]
    def fail(m): level[0]="FAIL"; findings.append("FAIL: "+m)
    def warn(m):
        if level[0]!="FAIL": level[0]="WARN"
        findings.append("WARN: "+m)

    persp, drawn_exp, flip_exp = EXPECT.get(case,(None,None,None))

    if any("_spritesheet_mirror.png" in f for f in files):
        fail("stray _spritesheet_mirror.png present (should use --flip-to naming)")

    # clobbered-deliverable check: every final sheet must be a wide strip, not square
    for png in [f for f in files if f.endswith("_spritesheet.png")]:
        try:
            im=Image.open(os.path.join(d,png))
            if im.width <= im.height:
                fail("deliverable %s is %dx%d (square) — looks like a clobbered single-frame render"%(png,im.width,im.height))
        except Exception as e:
            fail("cannot open %s: %s"%(png,e))

    if drawn_exp is not None:
        for dd in drawn_exp:
            if dd not in svgs: fail("expected DRAWN dir '%s' has no .svg source"%dd)
        for fd in flip_exp:
            if fd not in sheets: fail("expected FLIPPED dir '%s' missing sheet"%fd)
            if fd in svgs: warn("flipped dir '%s' has an .svg — should be mirror-derived"%fd)
            src = MIRROR_SRC.get(fd); subj = list(subjects)[0] if subjects else None
            if subj:
                lp = os.path.join(d, "%s_%s_spritesheet.png"%(subj,src))
                rp = os.path.join(d, "%s_%s_spritesheet.png"%(subj,fd))
                if os.path.exists(lp) and os.path.exists(rp):
                    ok,msg = per_frame_flip_ok(lp,rp)
                    if ok is False: fail("flip '%s' not a per-frame mirror of '%s': %s"%(fd,src,msg))
                    elif ok: findings.append("ok: flip %s == mirror(%s) [%s]"%(fd,src,msg))

    manifests=[f for f in files if f.endswith("_set.json")]
    if (drawn_exp or flip_exp) and not manifests:
        warn("no _set.json manifest for a directional set")
    for mf in manifests:
        try:
            man=json.load(open(os.path.join(d,mf))); mdirs=man.get("directions",{})
            for dd,info in mdirs.items():
                sheet=info.get("sheet")
                if sheet and sheet not in files: fail("manifest %s lists sheet '%s' not on disk"%(mf,sheet))
            findings.append("ok: %s lists %s"%(mf,list(mdirs)))
        except Exception as e:
            fail("manifest %s invalid JSON: %s"%(mf,e))

    if case=="A8_template" and "knight_walk_left.svg" not in files:
        fail("template mode: source knight_walk_left.svg not preserved")
    if case=="A6_knight_sword_rh":
        if not any(("hand" in f.lower() or "asymmetr" in f.lower() or "caveat" in f.lower())
                   for f in report_flags(os.path.join(d,"result.json"))):
            warn("handedness caveat not clearly mentioned in report")

    return {"case":case,"expect":persp,"level":level[0],"subjects":sorted(subjects),
            "svgs":sorted(x for x in svgs if x),"sheets":sorted(x for x in sheets if x),
            "findings":findings,"report_flags":report_flags(os.path.join(d,"result.json"))}

if __name__=="__main__":
    cases = sys.argv[1:] or list(EXPECT)
    overall="PASS"
    for c in cases:
        r=evaluate(c)
        if r is None: print("\n### %s: (not run yet)"%c); continue
        if r["level"]=="FAIL": overall="FAIL"
        elif r["level"]=="WARN" and overall!="FAIL": overall="WARN"
        print("\n### %s  [%s]  expect=%s"%(c,r["level"],r["expect"]))
        print("   subjects=%s drawn(svg)=%s sheets=%s"%(r["subjects"],r["svgs"],r["sheets"]))
        for f in r["findings"]: print("   -",f)
        for f in r["report_flags"][:6]: print("     •",f)
    print("\n===== OVERALL: %s ====="%overall)
