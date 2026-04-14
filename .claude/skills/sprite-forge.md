---
name: sprite-forge
description: Generate animated SVG game sprites and convert them to PNG sprite sheets
user_invocable: true
---

# Sprite Forge

Generate animated SVG game sprites and convert them to PNG sprite sheets.

## Usage

The user will describe a character/sprite and optionally reference existing SVG files:

- `"skeleton warrior walking left"` — generate from scratch
- `"make it red" --modify hero.svg` — modify an existing SVG in place
- `"add a shield" --template hero.svg` — create a new SVG using an existing one as reference

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

Parse the user's input to determine the mode:
- **Generate**: no existing SVG referenced — create from scratch
- **Modify** (`--modify <file>`): read the existing SVG, apply the requested changes, overwrite it
- **Template** (`--template <file>`): read the existing SVG as reference, create a new SVG inspired by it

### Step 2: Generate the SVG

Create a complete, self-contained animated SVG following these conventions:

**Structure:**
- Side-view characters facing LEFT
- `viewBox="0 0 64 64"` for standard characters, `"0 0 80 64"` for wider ones (spiders, etc.)
- Keep shapes simple and game-appropriate (low detail, clear silhouettes)
- Use flat colors, no gradients unless essential for shading

**Animation (SMIL only):**
- Use `<animate>` and `<animateTransform>` with `dur` and `values` attributes
- NO CSS animations, NO JavaScript
- Walk cycle duration: 0.4s–0.8s with `repeatCount="indefinite"`
- Place `<animateTransform>` as a direct child of the animated element, NOT in a wrapper `<g>`

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

### Step 5: Report results

Tell the user what was generated and suggest next steps (e.g., "want me to adjust the walk cycle?" or "want a running version?").

## Important

- The SVG is the source of truth — PNGs can always be regenerated
- Always output a COMPLETE SVG — never use placeholders like `...` or `<!-- rest here -->`
- Every `<animate>` and `<animateTransform>` must have both `dur` and `values` attributes
- Test that the SVG is valid XML before saving
