# Monochrome

Single-hue with carefully spaced values. Game Boy / 1-bit aesthetic, or a stylised "single-colour creature" (a shadow demon, a steel construct, an inkblot beast). Forces good silhouette work because all readability comes from value, not colour.

## Palette template

Pick **one hue** and use 4 values from it. Classic Game Boy uses green:

| Role | Hex | Notes |
|------|-----|-------|
| V1 (lightest) | `#cfe8b8` | Skin / highlight / paper-white substitute |
| V2 | `#86b066` | Mid-light — body base |
| V3 | `#386850` | Mid-dark — back-of-body, shadows |
| V4 (darkest) | `#0c2820` | Outlines, deep shadow, eye dots |

**Hue swaps** (keep the V1–V4 luminance steps the same; shift the hue):

- Blue (steel/ice): `#cee0f0` / `#7098c8` / `#385878` / `#0c1830`
- Red (blood/demon): `#f0c8c0` / `#c87060` / `#783028` / `#280c0c`
- Sepia (parchment/old): `#e8d0a8` / `#b89860` / `#785a30` / `#281808`
- Pure grey: `#e0e0e0` / `#909090` / `#404040` / `#080808`

## Conventions

- **Exactly 4 values.** Three is too flat, five starts approximating colour. The 4-value rule forces decisive shading.
- **V2 is your most-used.** Body, most limbs, most surfaces.
- **V4 is for emphasis only.** Eye dots, mouth interior, single weapon outline, deepest shadow under the chin. Don't outline everything.
- **V1 reads as light.** Use it on the top-facing surfaces and the eye-highlight dot.
- **No gradients or alpha shading.** Hard transitions between values is the whole point.
- **Silhouette test is critical** in this style — readability lives or dies by the outline shape (Phase 3 of the pipeline).

## Snippet

```xml
<!-- Body (V2) -->
<rect x="29" y="22" width="6" height="20" fill="#86b066"/>
<!-- Back arm (V3) -->
<rect x="-2.5" y="0" width="5" height="12" fill="#386850"/>
<!-- Top highlight (V1) — a 2px sliver -->
<rect x="29" y="22" width="6" height="2" fill="#cfe8b8"/>
<!-- Eye (V4 dot on V1 highlight square) -->
<rect x="27" y="14" width="2" height="2" fill="#cfe8b8"/>
<rect x="27" y="14" width="1" height="1" fill="#0c2820"/>
```
