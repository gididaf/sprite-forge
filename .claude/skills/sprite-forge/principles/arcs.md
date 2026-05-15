# Arcs

Natural motion follows **curves, not straight lines**. A swinging arm traces an arc around the shoulder; a falling object follows a parabola; a head bobs in a small ellipse, not a straight line.

## Why it matters

When motion follows a straight line, it reads as mechanical or floating. Even a small arc on translate-based motion (like a body bob) makes the sprite feel weighted and natural.

## Two ways to produce arcs

### 1. Rotation around a joint (automatic arc)

`<animateTransform type="rotate">` around a fixed joint **naturally produces an arc** for everything inside the group. This is why all the rigs in `../rigs/` use joint-pivoted groups: arms rotate around shoulders, legs around hips, everything traces an arc by construction.

```xml
<g id="arm" transform="translate(29,25)">
  <!-- Anything in here rotates around (0,0) which IS the joint, so the hand traces an arc. -->
  <animateTransform attributeName="transform" type="rotate"
                    values="0; 60; 0" dur="0.6s" repeatCount="indefinite" additive="sum"/>
  <rect x="-2" y="0" width="5" height="12" fill="..."/>
  <circle cx="0" cy="13" r="2" fill="..."/>  <!-- this hand traces an arc -->
</g>
```

### 2. Translate along a curve (manual arc)

For translation that should follow a curve (head bob, character hop), don't use 2-point values like `0,0; 0,-2; 0,0` — that's a straight line. Use intermediate points that trace a parabola or ellipse:

**Straight (bad):**
```
values="0,0; 0,-4; 0,0"
```

**Arc'd (good — small horizontal sway adds the arc):**
```
values="0,0; -0.5,-2; 0,-4; 0.5,-2; 0,0"
```
The small X-offsets at the mid-points trace a tiny ellipse, giving the bob a natural curve.

## When to add arcs explicitly

- **Head bob**: add ±0.5 X-sway as the head goes up/down.
- **Hop / jump**: the character's centre traces a parabola — X stays roughly constant (in-place hop) but Y is a clear parabola; for a moving jump, X goes one way and Y is the parabola.
- **Cape sway / tail wiggle**: not a straight wag but a wave traveling along the length — see `secondary-motion.md`.

## Counter-arc rule

When two parts move in opposite phase (arms and legs in a walk cycle), their arcs should mirror each other. If the front leg traces an arc forward-up-back-down, the front arm traces an arc back-up-forward-down. Same shape, opposite phase. Walking sprites feel right when this is balanced.
