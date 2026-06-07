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

### Perspective & direction-set detection

Sprite Forge is **orientation-aware**. There is no universal "always face left" rule. Before drawing, classify the request into ONE perspective, which determines how many directions you produce and which are drawn fresh vs. mirror-derived:

| Perspective | Directions in the set | Drawn fresh | Mirror-derived (via `--flip-to`) | Filename suffixes |
|---|---|---|---|---|
| **Side-scroller** | left, right | `left` | `right` = flip(left) | `_left`, `_right` |
| **Top-down 4-way** | down, up, left, right | `down`, `up`, `left` | `right` = flip(left) | `_down`, `_up`, `_left`, `_right` |
| **Top-down 8-way** | down, up, left, right, downleft, downright, upleft, upright | `down`, `up`, `left`, `downleft`, `upleft` | `right`=flip(left), `downright`=flip(downleft), `upright`=flip(upleft) | the 8 direction names |
| **Single / non-directional** | one sprite | the single pose | none | **no suffix** |

**How to choose:**
- **Side-scroller** — platformers, side-view combat, anything that moves along a horizontal floor and only ever faces left or right. This is the old default.
- **Top-down 4-way / 8-way** — RPG / roguelike / twin-stick views where the character walks toward the camera (down), away (up), and sideways. `down` = facing the camera (front view), `up` = back view.
- **Single / non-directional** — objects (chest, torch, gem), UI, projectiles with one travel direction, front-only portraits, radially-symmetric creatures (slime, fire elemental). No mirror, no suffix.

If the user named a perspective ("top-down", "platformer", "8-direction"), use it. If the subject strongly implies one (a treasure chest is non-directional; a "side-scroller hero" is side-scroller), infer it and **state your choice in the report**. If genuinely ambiguous (e.g. just "a goblin walking"), ask the user which perspective with `AskUserQuestion` before drawing — it changes how many sprites you produce.

**Mirror-derivation is the default** for the flippable directions: `right` is produced by horizontally flipping `left` (and the diagonals likewise) using the CLI's `--flip-to` flag — no redrawing. This is fast and pixel-consistent. Caveat: asymmetric details flip sides (a sword held in the left hand becomes the right hand, text reverses). If the subject has strong handedness or readable text that must not flip, note it in the report and offer to draw that direction fresh instead.

---

## Pick your pipeline depth (complexity tier)

Not every sprite needs the full six phases. After choosing the perspective, classify the subject into one tier and run the matching pipeline. **Default to the tier the subject implies; if the user says "quick / just make it", force Lite; if they say "make it good / be thorough", force Full.**

**Lite tier — abbreviated pipeline.** Subjects with no directional physics and a simple, mostly-symmetric form:
- Static / idle objects: chest, torch, gem, coin, potion, crate, lever, sign, banner.
- Non-directional symmetric creatures with a gentle idle: slime, fire/water elemental, floating orb, eyeball.
- Anything you classified as **single/non-directional** in the perspective table almost always lands here.

Run only **Phase 1 (compact)** → **Phase 2 (rest pose)** → **Phase 5 (animation)** → **Phase 7 (report)**. Skip the silhouette phase (3), peak-pose phase (4), and separate secondary-motion phase (6) — fold any light polish (shadow, subtle bob, glint) into Phase 5. Skip the fresh-eyes subagent. Iteration cap **2** per phase. Compact Phase 1 to ~3 subject anchors + the single motion; skip the three-moment key-pose plan (a chest opening has no "peak readability" stress test).

**Full tier — all six phases.** Anything with directional physics, weight transfer, multi-part interaction, or that gets mirrored into a set:
- Walk / run cycles, jumps, dodges (weight + foot contact matter).
- Combat: attacks, archer draws, caster channels, weapon swings (action mechanics + directional correctness).
- Multi-part / articulated: riders+mounts, multi-segment creatures, wing-flappers, quadrupeds.
- Any **side-scroller / top-down** directional set (the spec is amortized across directions, so the rigor is cheap per sprite).

Run phases 1→7 with the fresh-eyes subagent where its triggers apply.

Tiers control *pipeline depth, not the quality ceiling* — a Lite chest must still pass its spec checks; it just skips silhouette-vs-peak contrast analysis and counter-motion layering it would never use. State the tier you chose in the Phase 7 report.

---

## The 6-phase pipeline

Each phase produces or modifies a single artifact and is reviewed against the prior phase before continuing. **Iteration cap: 3 per phase** (2 in Lite tier), not global — you may iterate that many times inside any phase before reporting remaining issues to the user. **Lite tier runs only phases 1, 2, 5, 7** (see complexity tier above).

**How the pipeline maps onto a direction set:**
- Run the **full** 6-phase pipeline once for the **anchor** direction — `left` for side-scroller/top-down, `down` for a top-down set with no left (rare), or the single pose for non-directional.
- The phase-1a spec (all three layers), the chosen rig, and the style pack are **shared across the whole set** — write them once. Don't re-derive identity or style per direction.
- For each **additional fresh** direction (e.g. `up`, `down`, `downleft`), run an **abbreviated** pipeline reusing the shared spec: rest pose → silhouette → animation, with one review pass. You're re-posing the same character to a new viewing angle, not re-inventing it.
- **Inter-direction readability check (8-way especially):** when you draw a diagonal, render its rest silhouette next to the two cardinals it sits between (e.g. `upleft` beside `up` and `left`) and confirm it reads as a *distinct in-between angle*. If `upleft` is indistinguishable from `up`, it failed — apply the diagonal differentiation rules (torso turn, exposed side sliver, head offset) and re-render before animating. Back-diagonals are the usual offender.
- **Mirror-derived** directions (`right`, `downright`, `upright`) get **no pipeline** — they are produced by `--flip-to` in the same conversion call as their source (see phase 5). Just eyeball the flipped GIF once to confirm it reads correctly.

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
- **Generate mode**: `<subject>_<action>_<direction>.svg` for directional sets (e.g. `hero_walk_left.svg`, `hero_walk_down.svg`); `<subject>_<action>.svg` with **no suffix** for single/non-directional sprites (e.g. `treasure_chest_open.svg`). Append `_2`, `_3` on collision.
- **Modify mode**: overwrite the source file.
- **Template mode**: pick a new name, never overwrite the template.

You draw only the **fresh** directions (see the perspective table). The mirror-derived directions are produced by the CLI, not authored by hand.

Apply SVG conventions — these depend on the viewing angle:
- `viewBox="0 0 64 64"` standard, `"0 0 80 64"` for wider subjects.
- **Side view** (`left`, and the side-facing component of diagonals): true profile. Torso width ≤ 7px (at viewBox 64) — anything wider reads as front-facing. Layer back limbs first (darker), then body, then front limbs to create depth.
- **Front view** (`down` in top-down): symmetric, facing the camera. Torso may be wider; both arms/legs visible and roughly mirror-symmetric. Layer is back-to-front (far arm, body, near arm) but left/right symmetry dominates.
- **Back view** (`up` in top-down): symmetric, facing away. Show the back of the head/hair/cloak; hide the face.
- **Diagonals** (8-way): a true three-quarter view that must read as **distinct from BOTH neighbouring cardinals** (e.g. `upleft` must not look like `up` nor like `left`). A "slight asymmetry" is not enough — the back-diagonals in particular tend to collapse into the plain back view. Enforce all of:
  - **Turn the torso/shoulders ~30°** toward the travel direction — one shoulder comes forward and reads nearer/larger, the other recedes.
  - **Expose a sliver of the side profile**: show one side of the body that the pure front/back view hides (a bit of chest+one arm on front-diagonals; a bit of back+one shoulder blade on back-diagonals; a cape/hair edge peeking to one side).
  - **Offset the head** a few px toward the travel direction and shift facial features (front-diagonals) or hair/crest (back-diagonals) the same way, to suggest a head turn.
  - Front-diagonals (`downleft`) still show **some face**; back-diagonals (`upleft`) show **no face** but a clearly *angled* back, not a flat one.
  - The result should be visibly between the cardinal and the side view — if you laid `up`, `upleft`, `left` side by side, the middle one reads as the in-between angle.
- Limb thickness ≥ 5px. 4px renders as a thread at 64×64.
- Flat colours. No gradients unless essential.
- Pick a palette from `styles/` unless the user has specified — and reuse the **same** palette across every direction in the set.

Render at 256×256 **to a scratch inspection file** (never the deliverable name — see the anti-clobber rule below):

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --output <file>_inspect.png
```

This produces `<file>_inspect.png` containing only the rest pose at high resolution. The real `<file>_spritesheet.png` deliverable is written later, only by the full bake in phase 5/6.

**Review (statics):**
- Pass A (adversarial): "If this rest pose is wrong, what are the 3 most likely problems?"
- Pass B (spec check): for each subject-anchor item, verdict PASS/FAIL/UNCLEAR. Cite which spec item.
- Check: proportions, palette consistency, facing direction (true side-view profile), layering depth, limb thickness ≥ 5px, torso width ≤ 7px.

Fix and re-render until rest pose passes, max 3 iterations.

### Phase 3 — Silhouette readability test

Render the rest pose as a black-on-white silhouette:

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --silhouette --output <file>_inspect.png
```

This produces `<file>_silhouette.png` (the scratch sheet goes to `<file>_inspect.png`, leaving the deliverable untouched).

**Review (readability):**
Look at the silhouette alone — no colours, no detail. Ask:
- Can you tell from the silhouette alone what subject this is? (humanoid vs quadruped vs flying creature)
- Can you tell what it's doing or about to do?
- Is there a clear focal element (weapon, wings, tail) breaking the body outline, or does everything collapse into one blob?

If the answer to any is no, the silhouette has failed readability. Common fixes: widen weapon, separate limbs from torso, add hat/horn/feature that breaks the head outline, exaggerate the action limb. Update SVG and re-test.

Max 3 iterations.

### Phase 4 — Peak pose

Modify the SVG to show the **extreme of the action** (arm fully extended, bow fully drawn, leg fully forward, wings fully down-stroked, jaws fully open). The peak is the moment you wrote about in 1b — make the SVG show that pose now.

Render at 256×256 (regular and silhouette) to the scratch inspection file:

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --silhouette --output <file>_inspect.png
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
sprite-forge <file>.svg --facing <direction>
```

This produces the sprite sheet, JSON (stamped with `facing`), and GIF. **No mirror file is produced by default.**

If this direction has a mirror-derived twin (`left`→`right`, `downleft`→`downright`, `upleft`→`upright`), add `--flip-to` to emit the flipped sibling deliverable in the same call — one render, two directions:

```bash
sprite-forge hero_walk_left.svg --facing left --flip-to hero_walk_right
```

This additionally writes `hero_walk_right_spritesheet.png`, `hero_walk_right.gif`, and `hero_walk_right_spritesheet.json` (the latter stamped `mirrorOf`). For non-directional sprites, omit both `--facing` and `--flip-to`.

**Review (dynamics — review the GIF, not the strip):**
- Pass A (adversarial): "If this motion is wrong, what are the 3 most likely problems?"
- Pass B (spec check): every action-mechanics item from phase 1a — PASS/FAIL/UNCLEAR.
- Look for: detached parts (something stays still when its parent moves), clipping, dead limbs (no movement when there should be), uneven timing, robotic linear motion, wrong direction (projectile fires the wrong way).

If you need detail, render a single suspect frame at high resolution (to the scratch file, never the deliverable):

```bash
sprite-forge <file>.svg --frames 1 --size 256 --no-gif --no-meta --duration <T> --output <file>_inspect.png
```

where `<T>` makes frame 0 land at the suspect moment.

Max 3 iterations.

### Phase 6 — Secondary motion + polish

Now layer in the secondary motion that makes the sprite feel alive:

- Body bob on the root `<svg>` (translate `0,0; 0,-1; 0,0` is the classic).
- Counter-motion: arms swing opposite to legs in a walk — and make it **visible**, not token. A walk where only the legs move reads as half-dead. Keep a 1–2px gap (outline/shadow) between arm and torso so the arm doesn't fuse into the body, and give it a real counter-swing (rotate ≈ ±12–18° at the shoulder, opposite phase to the same-side leg). On front/back views where a full swing would clip, at least bob the hands and shift the shoulder line.
- Lag/follow-through: ears, cloth, tail, hair animate a quarter-cycle behind the body.
- Secondary part wobble: weapon sway, helmet jiggle, antenna flop.
- Ease shaping: if the primary motion still looks robotic, add intermediate keyframes near the extremes (slowing in/out) — consult `principles/ease.md`.
- Anticipation frames: a small reverse motion before the main strike — consult `principles/anticipation.md`.
- Shadow ellipse if missing: `<ellipse fill="rgba(0,0,0,0.15)">` at the character's feet.

Bake and re-render (same flags as phase 5 — include `--facing` and any `--flip-to` twin):

```bash
sprite-forge <file>.svg --facing <direction> [--flip-to <twin>]
```

**Review (full dynamics):**
- Pass A: 3 most likely remaining issues.
- Pass B: every spec item from phase 1a (all three layers) — PASS/FAIL/UNCLEAR.
- Animation principles check: does this sprite show anticipation? follow-through? ease? Any principle from phase 1a marked FAIL needs a fix here.

Max 3 iterations.

### Phase 7 — Set assembly + report

For a **multi-direction set**, once every direction (fresh + mirror-derived) is rendered, write a combined manifest so a game engine can load the whole set. Name it `<subject>_<action>_set.json`:

```json
{
  "subject": "hero_walk",
  "perspective": "top-down-4",
  "frameWidth": 64, "frameHeight": 64,
  "directions": {
    "down":  { "sheet": "hero_walk_down_spritesheet.png",  "gif": "hero_walk_down.gif",  "origin": "drawn" },
    "up":    { "sheet": "hero_walk_up_spritesheet.png",    "gif": "hero_walk_up.gif",    "origin": "drawn" },
    "left":  { "sheet": "hero_walk_left_spritesheet.png",  "gif": "hero_walk_left.gif",  "origin": "drawn" },
    "right": { "sheet": "hero_walk_right_spritesheet.png", "gif": "hero_walk_right.gif", "origin": "mirror", "mirrorOf": "left" }
  }
}
```

Single/non-directional sprites need no manifest.

Then report: state the **perspective** and **complexity tier** you chose (and why, if inferred), list every direction produced and whether it was drawn or mirror-derived, summarise the spec checks (PASS / any UNCLEAR/FAIL left), flag any handedness/text-asymmetry caveats from mirroring, and suggest next steps ("want an attack set in the same directions?", "want me to draw `right` fresh instead of mirroring?").

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

A **direction set** (one subject in several directions) is NOT a batch — it shares a single spec/rig/style and is handled by the pipeline reuse described above (full pipeline for the anchor, abbreviated for other fresh directions, `--flip-to` for mirror twins).

A **batch** is several *distinct subjects*. When the user asks for multiple sprites in one invocation (e.g. "generate 10 sprites" or "make a goblin, ogre, and orc"), run the full 6-phase pipeline **per sprite, sequentially**:

1. Sprite #1: phases 1 → 7. Carry forward any lessons (e.g. "4px limbs render too thin at 64×64 — bump all future sprites to 5px").
2. Sprite #2: phases 1 → 7, with prior lessons applied.
3. Continue for each.

Reviewing 10 sprites in one batch turns each review into a glance. Per-sprite review preserves quality.

Only skip per-sprite review when the user explicitly trades quality for speed ("just generate them all fast, I'll review").

---

## Mirroring

Do NOT use `scale(-1,1)` for flipped versions inside the SVG — it breaks SMIL animation. Mirroring is a **pixel operation done by the CLI**, never an SVG transform.

- Mirroring is **off by default** — a bare `sprite-forge <file>.svg` produces no flipped file.
- To derive a flipped direction as a first-class, correctly-named deliverable, use **`--flip-to <name>`** (preferred): it emits `<name>_spritesheet.png` + `<name>.gif` + `<name>_spritesheet.json` flipped from the source. This is the right way to make `right` from `left`.
- The legacy `--mirror` flag still exists and emits a generic `<stem>_spritesheet_mirror.png` (off by default). Prefer `--flip-to` so the output carries its real direction name instead of `_mirror`.

## Important

- The SVG is the source of truth — PNGs always regenerable.
- Output COMPLETE SVGs — never `...` or `<!-- rest here -->`.
- Every `<animate>` / `<animateTransform>` needs both `dur` and `values`.
- Validate the SVG is well-formed XML before saving.
- A single SVG file is built up across phases 2 → 6 — don't fragment into multiple files unless explicitly asked.
- **Never clobber the deliverable.** The final `<file>_spritesheet.png` / `.gif` is written ONLY by the full bake (`sprite-forge <file>.svg --facing …`). Every inspection render (`--frames 1`, high-res, silhouette, suspect-frame) MUST use `--output <file>_inspect.png` — otherwise it overwrites the real sprite sheet with a single static frame. Symptom of getting this wrong: a `_spritesheet.png` that is square (e.g. 256×256) instead of a wide N-frame strip.
- **Mirror-derive last, and keep twins fresh.** Run `--flip-to <twin>` only *after* a direction's final full bake, as the last action for that direction. If you later re-edit a drawn direction (e.g. fix its pose), you MUST re-run its `--flip-to` twin — otherwise the mirrored sibling is a stale flip of the old version and won't match.
