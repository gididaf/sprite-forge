# Dark Fantasy

Muted, desaturated palette with deep blacks and bone/rust accents. Good for skeletons, undead, gothic knights, cursed creatures. Avoid pure saturated colours — they break the mood.

## Palette template

| Role | Hex | Notes |
|------|-----|-------|
| Bone / pale | `#d8d0b8` | Skulls, claws, exposed bone |
| Bone shadow | `#8a8068` |  |
| Rust / iron | `#6a4a3a` | Armor, weapons |
| Rust dark | `#3a2418` |  |
| Cloth (dark) | `#3a2a3a` | Cloaks, robes |
| Cloth highlight | `#5a4a5a` |  |
| Eye glow | `#c00020` or `#00c0a0` | One per character — red or sickly green |
| Deep shadow | `#0a0810` | The void inside hoods, eye sockets |
| Blood / accent | `#7a1a1a` | Sparingly |

## Conventions

- **Saturation < 40%** for everything except the eye glow and any blood accent.
- **Value range is the wide one**: deep blacks all the way to bone-white, with most material in the middle.
- **Hoods / cloaks > skin.** Cover most of the figure in cloth; let the dramatic silhouette do the work.
- **One bright accent** per character (a glowing eye, a magical rune, a rust-bleed on a blade). Don't add two — the focus is lost.
- **Outline**: optional. If used, `#0a0810` at 0.5–0.8px, only on the outermost silhouette.
- **Drop shadow** on the ground: darker than default, `fill="rgba(0,0,0,0.35)"`.

## Snippet

```xml
<!-- Skeletal arm -->
<rect x="-2.5" y="0" width="5" height="12" fill="#d8d0b8"/>
<rect x="-2.5" y="3" width="5" height="0.6" fill="#8a8068"/>   <!-- joint shading -->
<rect x="-2.5" y="7" width="5" height="0.6" fill="#8a8068"/>
<!-- Glowing eye socket -->
<ellipse cx="-3" cy="-1" rx="1.6" ry="1.8" fill="#0a0810"/>
<circle cx="-3" cy="-1" r="0.5" fill="#c00020"/>
```
