# Pixel Chunky

Bold, blocky shapes with thick limbs and saturated flat fills. Reads cleanly at small sizes. Best for arcade / retro-platformer aesthetics.

## Palette template

Pick one **primary** + the matching **dark/light** pair for shading. Add **accent** for highlights (eyes, gems, blood, magic).

| Role | Hex | Notes |
|------|-----|-------|
| Primary (body) | `#c14b3a` | Saturated, mid-value |
| Primary dark | `#7a2a1a` | For back-of-body shading + outlines |
| Primary light | `#e88a5a` | For highlights (sparingly) |
| Skin / accent | `#f0c898` | Faces, hands |
| Skin dark | `#a06840` | Back faces, shadow |
| Outline (optional) | `#1a1010` | Use sparingly — chunky shapes already read |
| Metal | `#9aa0b0` |  |
| Metal dark | `#4a5060` |  |

**Suggested palette swaps:**
- Skeleton: primary `#e8e0c8` / dark `#9a8870` / accent `#c00020` (eye glow)
- Goblin: primary `#5a8a3a` / dark `#2a4a1a` / accent `#c8a000`
- Demon: primary `#aa2020` / dark `#5a0a0a` / accent `#ffaa00`

## Conventions

- **Limb thickness**: 6–7px (top of skill convention range — chunky reads chunky).
- **Torso width**: 6–7px side-view.
- **No gradients.** Flat fills only.
- **Two tones per body part** is the maximum: primary + primary-dark for back-facing surfaces.
- **Eyes**: single dot, `r="1"` to `r="1.5"`, near-black or accent colour.
- **Outlines**: usually skip. If used, only on the silhouette edge, never on interior shape boundaries.

## Snippet

```xml
<rect x="-3" y="0" width="6" height="14" fill="#c14b3a"/>     <!-- front leg -->
<rect x="-3" y="0" width="6" height="14" fill="#7a2a1a"/>     <!-- back leg -->
<rect x="-4" y="13" width="8" height="3" fill="#1a1010"/>     <!-- boot -->
```
