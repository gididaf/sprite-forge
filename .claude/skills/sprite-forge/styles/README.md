# Styles

Style packs define palette + shading conventions. Pick ONE per sprite (or per batch — a coherent batch shares a style).

## Picking a style

| If the user wants… | Pick |
|--------------------|------|
| Retro arcade, NES/SNES feel | `pixel-chunky` |
| Anime / hand-painted hero | `cel-shaded` |
| Undead, gothic, horror, gritty | `dark-fantasy` |
| Bright JRPG, mascot, friendly | `high-saturation` |
| Game Boy / 1-bit / single-creature aesthetic | `monochrome` |

If the user doesn't specify, **default to `pixel-chunky`** — it's the most forgiving at 64×64 and the most game-ready.

## Style + rig

Styles compose with any rig. The rig provides structure (joints, proportions); the style provides palette and shading. Workflow:

1. Pick rig (e.g. `humanoid_archer.svg`).
2. Pick style (e.g. `dark-fantasy.md`).
3. Replace the rig's neutral greys with the style's palette.
4. Apply the style's shading conventions (outlines, shadow shapes, etc.).
5. Proceed with phases 3–6.
