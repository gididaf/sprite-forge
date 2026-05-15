# Cel-Shaded

Flat base fills plus one explicit shadow layer per shape. Reads as drawn-by-hand anime/cartoon. Good for hero characters, hand-painted UI.

## Palette template

Each body part uses **three values**: base, shadow, optional rim-light.

| Role | Hex | Notes |
|------|-----|-------|
| Base | `#5a9ad0` | Mid-saturation, mid-value |
| Shadow | `#3a6090` | Always darker AND slightly more saturated |
| Rim | `#a8d8ff` | Lighter; use only on edges facing the light |
| Skin base | `#f0d4b0` |  |
| Skin shadow | `#c89878` |  |
| Outline | `#202028` | Always present, ~0.5–1px stroke |

## Conventions

- **Outline every shape.** Use `stroke="#202028" stroke-width="0.8"` or render shadow shapes that imply the line.
- **One light direction** for the whole sprite (top-left is the convention). All shadows on the bottom-right of each shape.
- **Shadows are shapes, not gradients.** Add a second polygon/rect/ellipse on top of the base in the shadow colour, clipped to the bottom-right half of the part.
- **Rim light is optional and rare.** A 1–2px sliver on the top-left edge of a few highlight shapes.
- **Eyes**: full-iris with white scleras, pupil + small highlight dot.

## Snippet (arm with shadow)

```xml
<g id="front-arm" transform="translate(29,25)">
  <!-- base -->
  <rect x="-2.5" y="0" width="5" height="12" fill="#5a9ad0" stroke="#202028" stroke-width="0.6"/>
  <!-- shadow shape: bottom-right half -->
  <polygon points="2.5,0 2.5,12 0,12 0,4" fill="#3a6090"/>
</g>
```
