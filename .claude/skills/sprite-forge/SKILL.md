---
name: sprite-forge
description: Generate animated SVG game sprites and convert them to PNG sprite sheets
user_invocable: true
---

# Sprite Forge

Generate animated SVG game sprites and convert them to PNG sprite sheets.

## Usage

The user describes what they want in natural language:

- `skeleton warrior walking left` — generate from scratch
- `make it red, modify hero.svg` — modify an existing SVG in place
- `add a shield, based on hero.svg` — create a new SVG using an existing one as reference

## Library available to you

Three directories ship inside this skill. Read from them whenever they help.

- `rigs/` — pre-wired rest-pose SVGs for common archetypes (humanoid, quadruped, wing-flapper, caster, archer, brute, serpent, multi-leg, blob, levitator, static-object, rider, projectile, vehicle). `additive="sum"` is already set on shoulder/elbow/hip groups; limb thickness and torso width already pass the conventions below. **Default behaviour: start from a rig when one fits, then restyle.** Never re-derive a humanoid skeleton from scratch when `rigs/humanoid.svg` exists.
- `styles/` — style packs (palette + line conventions) you can pick from or combine: `pixel-chunky`, `cel-shaded`, `dark-fantasy`, `high-saturation`, `monochrome`. Use one unless the user specifies otherwise.
- `principles/` — one doc per animation principle (anticipation, follow-through, ease, squash-stretch, arcs, secondary-motion, weight) with inline SVG snippets you can adapt. Consult before phases 5 and 6.

## Your workflow

### Phase 0 — Dependency check (first run only)

Verify `sprite-forge` is on PATH:

```bash
command -v sprite-forge
```

If NOT found, install:

```bash
curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash
```

If `curl` is unavailable, install manually:
1. `pip3 install Pillow`
2. `brew install librsvg` (macOS) or `sudo apt-get install -y librsvg2-bin` (Linux)
3. `git clone https://github.com/gididaf/sprite-forge.git ~/.sprite-forge`
4. `ln -sf ~/.sprite-forge/sprite-forge.py ~/.local/bin/sprite-forge && chmod +x ~/.sprite-forge/sprite-forge.py`

Verify with `sprite-forge --help`. Skip this phase on subsequent runs.

### Mode detection

Classify the user's request before starting:
- **Generate**: no existing SVG referenced — create from scratch (start from a rig when one fits).
- **Modify**: user references an SVG and wants to change it ("modify X", "update X", "change X") — read it, apply changes, overwrite it.
- **Template**: user references an SVG as starting point ("based on X", "like X but...") — read it, create a new SVG inspired by it.

In Modify mode, skip phases that don't apply (e.g. if the change is colour-only, you can jump from spec straight to phase 6 polish). In all other cases, run all six phases below in order.

---

## The 6-phase pipeline

Each phase produces or modifies a single artifact and is reviewed against the prior phase before continuing. **Iteration cap: 3 per phase**, not global — you may iterate up to 3 times inside any phase before reporting remaining issues to the user.

### Phase 1 — Spec + key-pose plan (text only)

Before drawing anything, commit in writing to:

**1a. Three-layer correctness spec.** Write 3–5 items under each layer:

- **Subject anchors** — identity facts that distinguish this subject from similar ones. Example for a kobold: "small, bipedal, dragon-like snout (not pig-like), reddish-brown scales, short tail, simple cloth garments — NOT a goblin (green, larger ears) or a lizardman (taller, no snout)."
- **Action mechanics** — the physics of the verb. Example for archer drawing: "bowstring is pulled back into a V shape with the centre toward the archer; bow is in front of the body relative to facing direction; arrow nocked to string, parallel to ground, pointing in facing direction; back arm rotates at shoulder + flexes at elbow while drawing; front arm extends straight, locked."
- **Animation principles** — which of the seven principles apply and how. Consult `principles/`. Example: "anticipation: micro-crouch before the bounce; follow-through: ears/cloth lag behind the body; ease-out: the bounce decelerates at apex; secondary motion: tail wiggles a quarter-cycle behind the body."

**1b. Key-pose plan.** Describe the silhouette at THREE specific moments in plain language:

- **Rest** — the default neutral pose.
- **Peak/Extreme** — the most extreme moment of the action (arm fully drawn, leg fully forward, jaws fully open). This is the readability stress test.
- **Contact/Impact** — the moment of force transfer (foot plant, projectile release, hit landed), if applicable.

For each, describe what makes the silhouette unambiguous — what about the outline alone reads as "archer drawing bow" or "ogre swinging club"?

Do not draw yet. The spec and pose plan stay in your working context for all later phases — you grade against them in every review.

### Phase 2 — Rest pose

Generate a static SVG at the **rest pose only** (no `<animate>` elements yet).

Filename rules:
- **Generate mode**: pick descriptive `<subject>_<action>_left.svg`. Append `_2`, `_3` on collision.
- **Modify mode**: overwrite the source file.
- **Template mode**: pick a new name, never overwrite the template.

Apply SVG conventions:
- Side-view, facing LEFT.
- `viewBox="0 0 64 64"` standard, `"0 0 80 64"` for wider subjects.
- Side-view torso width ≤ 7px (at viewBox 64). Anything wider reads as front-facing.
- Limb thickness ≥ 5px. 4px renders as a thread at 64×64.
- Flat colours. No gradients unless essential.
- Layer back limbs first (darker), then body, then front limbs.
- Pick a palette from `styles/` unless the user has specified.

Render at 256×256:

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --no-mirror
```

This produces `<name>_spritesheet.png` containing only the rest pose at high resolution.

**Review (statics):**
- Pass A (adversarial): "If this rest pose is wrong, what are the 3 most likely problems?"
- Pass B (spec check): for each subject-anchor item, verdict PASS/FAIL/UNCLEAR. Cite which spec item.
- Check: proportions, palette consistency, facing direction (true side-view profile), layering depth, limb thickness ≥ 5px, torso width ≤ 7px.

Fix and re-render until rest pose passes, max 3 iterations.

### Phase 3 — Silhouette readability test

Render the rest pose as a black-on-white silhouette:

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --no-mirror --silhouette
```

This produces `<name>_silhouette.png`.

**Review (readability):**
Look at the silhouette alone — no colours, no detail. Ask:
- Can you tell from the silhouette alone what subject this is? (humanoid vs quadruped vs flying creature)
- Can you tell what it's doing or about to do?
- Is there a clear focal element (weapon, wings, tail) breaking the body outline, or does everything collapse into one blob?

If the answer to any is no, the silhouette has failed readability. Common fixes: widen weapon, separate limbs from torso, add hat/horn/feature that breaks the head outline, exaggerate the action limb. Update SVG and re-test.

Max 3 iterations.

### Phase 4 — Peak pose

Modify the SVG to show the **extreme of the action** (arm fully extended, bow fully drawn, leg fully forward, wings fully down-stroked, jaws fully open). The peak is the moment you wrote about in 1b — make the SVG show that pose now.

Render at 256×256 (regular and silhouette):

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --no-mirror --silhouette
```

**Review (extreme readability):**
- Does the peak silhouette read as the verb? (a peak archer silhouette must read as "drawing a bow", not "standing weirdly")
- Is the contrast with the rest pose dramatic enough? If peak and rest look identical in silhouette, the eventual animation will look stiff. The peak should be visibly different.
- Are limbs clipping into the body or each other at the extreme?

Max 3 iterations. **Save the peak-pose attribute values** (limb rotations, positions) before moving to phase 5 — you'll use them as animation keyframes.

### Phase 5 — Primary animation

Now write the animated SVG. The default static attributes describe the rest pose; `<animateTransform>` and `<animate>` elements interpolate toward (and back from) the peak pose you saved in phase 4.

**Add ONLY the primary motion in this phase:**
- For a walk: leg cycle.
- For a draw: back arm rotation + bowstring pullback.
- For a flap: wing rotation.
- For a swing: weapon arc.

Leave secondary motion (head bob, tail sway, cloth flutter, body bob) for phase 6. Resist the temptation to add everything at once — primary motion has to read cleanly on its own before secondary motion can complement it.

**Animation rules:**
- SMIL only (`<animate>`, `<animateTransform>`). No CSS, no JS.
- Duration 0.4s–0.8s for cycles, `repeatCount="indefinite"`.
- `<animateTransform>` is a direct child of the animated element, NOT inside a wrapper `<g>`.
- When a `<g>` has both a static `transform` AND an `<animateTransform>`, set `additive="sum"`. Without it, the static translate is lost and the element renders at the origin.
- Keep rotation pivot (cx, cy) constant across keyframes within one `<animateTransform>`.
- Prefer **5–7 keyframes** over 2–3. The lerper produces smoother motion with more anchor points. Example: `values="0; 8; 12; 10; 0; -8; -12; -10; 0"` reads as eased; `values="-12; 12; -12"` reads as triangle-wave robotic.

Bake and render the GIF:

```bash
sprite-forge <file>.svg
```

This produces the sprite sheet, mirror, JSON, and GIF (GIF is default on now).

**Review (dynamics — review the GIF, not the strip):**
- Pass A (adversarial): "If this motion is wrong, what are the 3 most likely problems?"
- Pass B (spec check): every action-mechanics item from phase 1a — PASS/FAIL/UNCLEAR.
- Look for: detached parts (something stays still when its parent moves), clipping, dead limbs (no movement when there should be), uneven timing, robotic linear motion, wrong direction (projectile fires the wrong way).

If you need detail, render a single suspect frame at high resolution:

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --no-mirror --duration <T>
```

where `<T>` makes frame 0 land at the suspect moment.

Max 3 iterations.

### Phase 6 — Secondary motion + polish

Now layer in the secondary motion that makes the sprite feel alive:

- Body bob on the root `<svg>` (translate `0,0; 0,-1; 0,0` is the classic).
- Counter-motion: arms swing opposite to legs in a walk.
- Lag/follow-through: ears, cloth, tail, hair animate a quarter-cycle behind the body.
- Secondary part wobble: weapon sway, helmet jiggle, antenna flop.
- Ease shaping: if the primary motion still looks robotic, add intermediate keyframes near the extremes (slowing in/out) — consult `principles/ease.md`.
- Anticipation frames: a small reverse motion before the main strike — consult `principles/anticipation.md`.
- Shadow ellipse if missing: `<ellipse fill="rgba(0,0,0,0.15)">` at the character's feet.

Bake and re-render:

```bash
sprite-forge <file>.svg
```

**Review (full dynamics):**
- Pass A: 3 most likely remaining issues.
- Pass B: every spec item from phase 1a (all three layers) — PASS/FAIL/UNCLEAR.
- Animation principles check: does this sprite show anticipation? follow-through? ease? Any principle from phase 1a marked FAIL needs a fix here.

Max 3 iterations.

### Phase 7 — Report

Tell the user what was generated, summarise the spec checks (which items PASS, any UNCLEAR/FAIL left), and suggest next steps ("want a running version?", "want me to add idle frames?").

---

## Review conventions used in every phase

### Two passes, always in this order

- **Pass A — Adversarial.** Do NOT ask "does this look OK?" — that primes confirmation. Ask: "If this is wrong, what are the 3 most likely things wrong with it?" List them even if uncertain. You can dismiss after listing, but you must list first.
- **Pass B — Spec check.** Walk every spec item from phase 1a. State PASS / FAIL / UNCLEAR explicitly. Don't skip items.

### Statics vs dynamics — different views

- **Statics phases (2, 3, 4):** review a single high-res render. Look for proportions, palette, facing, silhouette, layering, limb thickness, clipping.
- **Dynamics phases (5, 6):** review the GIF. Animation problems live in time, not space. The 8-frame sprite-sheet strip is for game engines, not for you.

### Fresh-eyes subagent (recommended for complex subjects)

After your own phase 5 or 6 review passes, spawn a subagent (subagent_type: `general-purpose`) with the GIF. Triggers:
- Directional physics (archer, caster, projectile launcher).
- Multi-part interaction (rider+mount, character+weapon, multi-segment creature).
- Asymmetric/profile-dependent subjects where front vs side matters.

Skip for symmetric idle (slime, torch, gem, chest) and when the user opts out of quality for speed.

**Prompt the subagent to return structured JSON only**, like:

```
Read the GIF at <absolute-path>. User requested: "<original description>".
You have no other context — do NOT read the SVG source.

Return ONLY valid JSON in this schema:
{
  "summary": "<what you actually see, under 80 words>",
  "matches_request": true | false,
  "spec_checks": [
    {"item": "<one spec criterion you can evaluate from the GIF>",
     "verdict": "pass" | "fail" | "unclear",
     "severity": 1-5,
     "evidence": "<which frame or motion shows this>",
     "suggested_fix": "<concrete change to the SVG>"}
  ],
  "top_issues": ["<issue 1>", "<issue 2>", "<issue 3>"]
}
```

Hand it the spec from phase 1a so it can grade against your criteria, not just react. Any `verdict: "fail"` with `severity >= 3` is a real finding — fix it within the iteration cap. Do not dismiss the subagent's findings as "I already checked that" — its fresh eyes are the whole point.

---

## Batch requests

When the user asks for multiple sprites in one invocation (e.g. "generate 10 sprites" or "make a goblin, ogre, and orc"), run the full 6-phase pipeline **per sprite, sequentially**:

1. Sprite #1: phases 1 → 7. Carry forward any lessons (e.g. "4px limbs render too thin at 64×64 — bump all future sprites to 5px").
2. Sprite #2: phases 1 → 7, with prior lessons applied.
3. Continue for each.

Reviewing 10 sprites in one batch turns each review into a glance. Per-sprite review preserves quality.

Only skip per-sprite review when the user explicitly trades quality for speed ("just generate them all fast, I'll review").

---

## Mirroring

Do NOT use `scale(-1,1)` for right-facing versions inside the SVG — it breaks SMIL animation. The pipeline produces a `_mirror.png` flipped sprite sheet automatically (`--no-mirror` to disable).

## Important

- The SVG is the source of truth — PNGs always regenerable.
- Output COMPLETE SVGs — never `...` or `<!-- rest here -->`.
- Every `<animate>` / `<animateTransform>` needs both `dur` and `values`.
- Validate the SVG is well-formed XML before saving.
- A single SVG file is built up across phases 2 → 6 — don't fragment into multiple files unless explicitly asked.
