# Secondary Motion

Parts of the character that **don't drive the action** but **react to it**: hair, cloaks, tails, ears, cloth, weapon tassels, antennas. They lag behind the primary motion and trail it.

This is the principle that separates "moving" from "alive."

## When to apply

- Always, if the character has any of these parts.
- Phase 6 of the pipeline is specifically for this — primary motion is set up first, then secondary motion is added on top.

## The lag rule

Secondary parts move **a quarter to a half cycle behind** the part driving them. They don't move in phase with the body.

If the body bobs up at frame 2, the cape/tail trails it and bobs up at frame 3 or 4.

## How to express lag in SMIL

Two ways:

### 1. Same `dur`, **shifted values**

If the body uses `values="0,0; 0,-2; 0,0"` over 0.6s, the cape uses the same curve but **offset in the array**:

```
body:  values="0,0; 0,-1; 0,-2; 0,-1; 0,0"      <!-- peak at frame 2 -->
cape:  values="0,0; 0,0; 0,-1; 0,-2; 0,-1"      <!-- peak at frame 3 — 1 frame lag -->
```

### 2. Same `dur`, **`begin` attribute** (negative offset)

You can use `begin="-0.1s"` on the secondary animation so it starts a fraction-cycle later in its own loop relative to the primary:

```xml
<g id="cape">
  <animateTransform attributeName="transform" type="rotate"
                    values="0; 6; 0; -6; 0" dur="0.6s" begin="-0.15s" repeatCount="indefinite" additive="sum"/>
</g>
```

The bake engine respects `begin` only partially (treats `dur` as the cycle, `begin` doesn't shift in the lerper), so prefer method (1) — shifted values — for portability.

## Where secondary motion shows up

| Part | Driven by | Lag |
|------|-----------|-----|
| Hair | Head motion | 1–2 frames behind |
| Cloak / cape | Body bob + back motion | 2–3 frames behind |
| Tail | Body bob | 2–3 frames behind, can wag independently |
| Ears | Head | 1 frame behind |
| Weapon tassels | Weapon swing | 1–2 frames behind |
| Cloth fringe | Body Y motion | 2–3 frames behind |
| Antennae | Head | 1–2 frames behind |

## Example: walking character with cape

Body bobs up at frame 2 of an 8-frame cycle. Cape sways and trails:

```xml
<svg>
  <!-- body bob, peak at frame 2 -->
  <animateTransform type="translate" values="0,0; 0,-1; 0,-2; 0,-1; 0,0; 0,-1; 0,-2; 0,-1; 0,0"
                    dur="0.6s" repeatCount="indefinite"/>

  <g id="cape" transform="translate(35,22)">
    <!-- cape rotation, peak at frame 4 (1 frame lag) -->
    <animateTransform attributeName="transform" type="rotate"
                      values="0; 0; 3; 6; 8; 6; 3; 0; 0"
                      dur="0.6s" repeatCount="indefinite" additive="sum"/>
    <path d="M 0,0 L 6,18 L -6,18 Z" fill="..."/>
  </g>
</svg>
```

Without the lag, the cape looks **rigid** — like a board strapped to the back. With the lag, it looks like cloth.
