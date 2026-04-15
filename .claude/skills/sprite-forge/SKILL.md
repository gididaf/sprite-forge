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

## Your workflow

### Step 0: Check dependencies (first run only)

Before doing anything else, check if `sprite-forge` is available:

```bash
command -v sprite-forge
```

If NOT found, install everything automatically:

```bash
curl -fsSL https://raw.githubusercontent.com/gididaf/sprite-forge/main/install.sh | bash
```

If the install script fails or `curl` is unavailable, install manually:
1. `pip3 install Pillow`
2. `brew install librsvg` (macOS) or `sudo apt-get install -y librsvg2-bin` (Linux)
3. `git clone https://github.com/gididaf/sprite-forge.git ~/.sprite-forge`
4. `ln -sf ~/.sprite-forge/sprite-forge.py ~/.local/bin/sprite-forge && chmod +x ~/.sprite-forge/sprite-forge.py`

After installing, verify with `sprite-forge --help`. Skip this step on subsequent runs if `sprite-forge` is already on PATH.

### Step 1: Understand the request

Determine the mode from the user's natural language:
- **Generate**: no existing SVG mentioned — create from scratch
- **Modify**: user references an SVG and wants to change it ("modify X", "update X", "change X") — read it, apply changes, overwrite it
- **Template**: user references an SVG as a starting point ("based on X", "like X but...", "use X as reference") — read it, create a new SVG inspired by it

### Step 1.5: Write a correctness spec BEFORE generating

Before you draw anything, write out 3–5 domain-specific correctness checks for *this particular subject* and keep them in your working context. These are facts about what makes the subject recognizable and physically/anatomically correct — not generic animation hygiene.

Examples:
- **Archer drawing bow**: bow is in front of body (toward facing direction); bowstring forms a V-shape when drawn (center pulled back, tips anchored); arrow points toward the target (away from archer); arrow fires in the facing direction; back arm rotates/flexes during draw, not just translates.
- **Walking character**: feet alternate ground contact; back leg pushes off while front leg reaches forward; arms swing opposite to legs.
- **Wizard casting**: casting hand extends outward; spell effect appears at the hand, not the body; staff (if any) is held, not floating.
- **Dragon flying**: wings move through a full down-stroke (power) and up-stroke (recovery), not just a small wiggle; body rises on down-stroke.

Write this spec explicitly before Step 2. You will grade against it in Step 5. The point is to commit to correctness criteria *before* you become invested in the specific SVG you produced.

### Step 2: Generate the SVG

Create a complete, self-contained animated SVG following these conventions:

**Structure:**
- Side-view characters facing LEFT
- `viewBox="0 0 64 64"` for standard characters, `"0 0 80 64"` for wider ones (spiders, etc.)
- Keep shapes simple and game-appropriate (low detail, clear silhouettes)
- Use flat colors, no gradients unless essential for shading
- **Side-view torso width ≤ 7px** (at viewBox 64). A 12px-wide body reads as front-facing no matter how much profile detail you put on the head. True side-view = narrow torso.
- **Limb thickness ≥ 5px.** 4px limbs render as threads at 64x64 and disappear. Width 5–6 reads cleanly.

**Animation (SMIL only):**
- Use `<animate>` and `<animateTransform>` with `dur` and `values` attributes
- NO CSS animations, NO JavaScript
- Walk cycle duration: 0.4s–0.8s with `repeatCount="indefinite"`
- Place `<animateTransform>` as a direct child of the animated element, NOT in a wrapper `<g>`

**Composing transforms correctly:**
- When a `<g>` has a static `transform` attribute AND an `<animateTransform>`, set `additive="sum"` on the animation so the rotation composes with the translate instead of replacing it. Example: `<g transform="translate(34,42)"><animateTransform type="rotate" values="-25 0 0; 25 0 0; -25 0 0" additive="sum"/>`. Without `additive="sum"` the base translate is lost and the element renders at the origin.
- Keep the rotation pivot (cx, cy in `angle cx cy`) constant across all keyframes within a single `<animateTransform>` unless you explicitly want the pivot to slide — mixing pivots produces physically odd motion (the element orbits around different anchor points mid-animation).
- Nested rotating groups (shoulder rotate → elbow rotate inside) work correctly as long as each level uses `additive="sum"`.

**Layering & depth:**
- Draw back limbs first (further from viewer, darker color)
- Then body/torso
- Then front limbs
- This creates depth

**Standard elements:**
- Body bob: add `<animateTransform type="translate" values="0,0; 0,-1; 0,0">` on the root `<svg>` for natural walking bounce
- Shadow: add `<ellipse>` with `fill="rgba(0,0,0,0.15)"` at the character's feet
- Do NOT use `scale(-1,1)` transforms for mirroring — the pipeline handles that

### Step 3: Save the SVG

Choose a descriptive filename based on the subject (e.g., `skeleton_warrior_walk_left.svg`, not `create_a_skeleton.svg`).

- **Generate mode**: pick a new name, never overwrite existing files. If the name collides, append `_2`, `_3`, etc.
- **Modify mode**: overwrite the source file
- **Template mode**: pick a new name, never overwrite existing files or the template

Use the Write tool to save the SVG file.

### Step 4: Convert to sprite sheet

Run the conversion pipeline:

```bash
sprite-forge <svg_file>.svg
```

This produces:
- `<name>_spritesheet.png` — horizontal sprite sheet (8 frames, 64x64)
- `<name>_spritesheet_mirror.png` — flipped version
- `<name>_spritesheet.json` — metadata

Optional flags: `--frames N`, `--size N`, `--preview`, `--keep-frames`, `--no-mirror`, `--no-meta`

### Step 5: Visual review & fix loop

Read the generated sprite sheet PNG using the Read tool (it will display visually since you are multimodal). Review in two passes:

**Pass A — Adversarial critique (do this first).** Do NOT ask "does this look OK?" — that primes you to confirm. Instead, assume the sprite has problems and force yourself to answer:

> "If this sprite is wrong, what are the 3 things most likely wrong with it? List them, even if you're not sure."

This adversarial framing catches issues that passive scanning misses. You can dismiss items after listing them, but you must list them first.

**Pass B — Spec check.** Go through the correctness spec you wrote in Step 1.5 and verify each item against the sprite sheet. For each spec item, state explicitly: PASS, FAIL, or UNCLEAR. Do not skip items.

**Then check these generic problems:**
- **Detached parts**: elements that don't move with their parent (e.g., weapon spikes staying in place while the weapon swings). Fix: ensure ALL child elements are inside the animated `<g>` group.
- **Clipping/overlap**: limbs or feet passing through the ground or body. Fix: adjust pivot points or animation value ranges.
- **Wrong facing direction**: character should be in side-view profile facing LEFT, not front-facing. Fix: reposition facial features for profile view.
- **Stiff animation**: limbs barely moving, or all frames looking identical. Fix: increase rotation/translation ranges in animation values.
- **Floating parts**: gaps between limbs and body. Fix: adjust element positions to connect properly.
- **Missing animation**: some parts should move but don't (e.g., arms during a walk cycle). Fix: add `<animateTransform>` to those elements.
- **Proportions**: character too small in the viewBox, or parts disproportionately large/small.

**If ANY issues are found:**
1. Read the current SVG source
2. Fix the identified problems
3. Save the corrected SVG (overwrite the same file)
4. Re-run `sprite-forge <file>.svg` to regenerate the sprite sheet
5. Read the new sprite sheet PNG and review again (Pass A + Pass B)
6. Repeat until the sprite sheet looks correct (**hard max: 3 iterations** — do NOT exceed this; further loops show diminishing returns and risk over-editing. If still not right after 3, report the remaining issues to the user and let them decide.)

Do NOT use a percentage threshold ("looks 95% perfect") as a stop condition — you cannot reliably self-score. Stop when Pass A yields no real issues AND every Pass B spec item is PASS.

### Step 6: Report results

Tell the user what was generated and suggest next steps (e.g., "want me to adjust the walk cycle?" or "want a running version?").

## Batch requests (multiple sprites in one invocation)

When the user asks for multiple sprites at once (e.g. "generate 10 sprites" or "make a goblin, ogre, and orc"), do NOT batch-generate everything and review at the end. Instead, run the full Step 2 → Step 5 loop **per sprite, sequentially**:

1. Generate sprite #1 → save → convert → review → fix if needed
2. Then move on to sprite #2, carrying forward any lessons learned
3. Repeat for each sprite

**Why this matters:**
- **Fresh attention per sprite**: reviewing 10 sprite sheets in one batch means each gets a glance — subtle issues (thin limbs, stiff animation, wrong proportions) slip through. Reviewing one at a time gives each its own focused inspection.
- **Cross-sprite learning**: if sprite #1 reveals that 4px-wide limbs render too thin at 64x64, you apply that fix to sprites #2–N before generating them, instead of baking the same mistake into all of them.
- **Cheaper fixes**: catching an issue on sprite #1 is one fix; catching the same issue on all 10 at the end is ten fixes.

Only skip per-sprite review if the user explicitly asks for speed over quality ("just generate them all fast, I'll review").

### Fresh-eyes subagent review (recommended for complex subjects)

Your self-review has a known blind spot: you "know what you meant" and unconsciously fill in gaps the viewer cannot. A fresh subagent reviewing the PNG alone catches directional/physics errors that Pass A + Pass B can miss.

**When to spawn one** (trigger heuristics):
- Subject involves **directional physics**: archers firing arrows, casters aiming spells, catapults, projectile launchers. Your self-review is most likely to miss "arrow/projectile fires the wrong way" errors.
- Subject involves **multi-part interaction**: e.g. two parts that must stay synchronized (bow + arrow + string, character + weapon, rider + mount).
- Subject is **asymmetric/profile-dependent**: anything where front-view vs. side-view matters and you're not 100% sure the profile reads.

**When to skip it:**
- Symmetric idle animations (slime, fire, torch, gem, chest) — your self-review is usually sufficient and the subagent won't find more.
- The user explicitly asks for speed.

For each sprite, after your own Step 5 passes, invoke the Agent tool (subagent_type: `general-purpose`) with a prompt like:

> "Read the PNG at `<path>`. The user requested: `<original description, e.g. 'archer drawing a bow, facing left'>`. You have no other context — do not read the SVG source. Answer in under 150 words: (1) what do you actually see in this sprite sheet? (2) does it match the request? (3) list the 3 most likely issues, even if minor."

If the subagent flags an issue you missed, treat it as a real finding and fix it (still within the 3-iteration cap). The subagent's fresh eyes are the whole point — don't dismiss its feedback as "I already checked that."

Skip the subagent review only for single-sprite requests (your own review is usually sufficient) or when the user explicitly opts out.

## Important

- The SVG is the source of truth — PNGs can always be regenerated
- Always output a COMPLETE SVG — never use placeholders like `...` or `<!-- rest here -->`
- Every `<animate>` and `<animateTransform>` must have both `dur` and `values` attributes
- Test that the SVG is valid XML before saving
