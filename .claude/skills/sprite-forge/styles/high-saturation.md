# High Saturation

Bright, friendly, JRPG-style palette. High saturation, mid-to-high value. Suits heroes, friendly NPCs, magical creatures, mascot characters. Avoid muddy greys.

## Palette template

| Role | Hex | Notes |
|------|-----|-------|
| Primary (body) | `#3a9aea` | Pick from the saturated end of the wheel |
| Primary dark | `#1a5aaa` | For depth |
| Primary light | `#8acaff` | Highlights |
| Secondary | `#ffd000` | Hair / cape / mascot accent — high-contrast hue away from primary |
| Skin | `#ffd8b0` | Anime-style warm pale |
| Skin shadow | `#d8a070` |  |
| Outline (optional) | `#1a1830` | Dark navy reads warmer than pure black |
| White / sparkle | `#ffffff` | Eye highlights, sparkles, magic |

**Suggested combos:**
- Hero knight: primary `#3a9aea` + secondary `#ffd000` (gold trim) + cape `#c01030`
- Forest druid: primary `#3aa050` + secondary `#a06030` (wood/leather)
- Fire mage: primary `#ea4030` + secondary `#ffaa00` + skin `#ffd8b0`

## Conventions

- **Saturation ≥ 60%** for primary and secondary colours.
- **Use complementary or split-complementary pairs** for the primary + secondary (e.g. blue + yellow-orange, green + red-violet). Mascot characters need two colours that pop.
- **Three values per body part** is fine: base, dark, light. Don't be afraid of the highlight here.
- **Big eyes.** Anime convention — eyes occupy ~25% of the head height. Pupil + iris + white + 1–2 sparkle dots.
- **No gritty outlines.** Either skip outlines or use a saturated dark navy `#1a1830`, never pure black.

## Snippet

```xml
<!-- Hero head with anime eye -->
<g id="head" transform="translate(32,16)">
  <circle cx="0" cy="0" r="6" fill="#ffd8b0"/>
  <!-- Eye -->
  <ellipse cx="-3.5" cy="-0.5" rx="1.4" ry="1.8" fill="#ffffff"/>
  <ellipse cx="-3.5" cy="0" rx="1" ry="1.4" fill="#3a9aea"/>
  <circle cx="-3.5" cy="0.3" r="0.5" fill="#1a1830"/>
  <circle cx="-3" cy="-0.5" r="0.3" fill="#ffffff"/>
  <!-- Hair (secondary) -->
  <path d="M -6,-5 Q 0,-9 6,-5 L 5,-2 L -5,-2 Z" fill="#ffd000"/>
</g>
```
