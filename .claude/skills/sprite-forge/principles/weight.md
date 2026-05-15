# Weight

The character has mass. Heavy things move slowly, with momentum, and settle reluctantly. Light things flicker, snap, and stop instantly. The "feel" of a sprite is mostly determined by weight cues.

## Cues that communicate weight

| Cue | Heavy | Light |
|-----|-------|-------|
| **Motion duration** | Slow (1.0s+ cycles) | Fast (0.3–0.5s cycles) |
| **Anticipation** | Long, deep wind-up | Brief, shallow or none |
| **Follow-through** | Large overshoot, slow settle | Small overshoot, fast settle |
| **Vertical bob** | Small (1–2px) | Large (3–5px) |
| **Squash on landing** | Significant deformation | Minimal |
| **Stance** | Wide, planted, hunched | Narrow, upright |
| **Limb thickness** | Thick (7–8px) | Thin (5–6px) |
| **Foot drag** | Feet stay on ground longer | Feet leave ground quickly |

## SMIL implementation

### Heavy creature walk

```xml
<svg ...>
  <!-- Slow cycle, small bob, feet stay grounded longer -->
  <animateTransform type="translate" values="0,0; 0,-1; 0,0" dur="1.2s" repeatCount="indefinite"/>

  <g id="front-leg" transform="translate(36,42)">
    <animateTransform attributeName="transform" type="rotate"
                      values="-15; -10; 0; 10; 15; 10; 0; -10; -15"
                      dur="1.2s" repeatCount="indefinite" additive="sum"/>
    <!-- Smaller swing range (-15 to 15) + slow + long ground contact -->
  </g>
</svg>
```

### Light creature walk

```xml
<svg ...>
  <!-- Fast cycle, large bob, feet leave ground -->
  <animateTransform type="translate" values="0,0; 0,-3; 0,0" dur="0.4s" repeatCount="indefinite"/>

  <g id="front-leg" transform="translate(30,42)">
    <animateTransform attributeName="transform" type="rotate"
                      values="-35; 35; -35" dur="0.4s" repeatCount="indefinite" additive="sum"/>
    <!-- Large swing range, fast cycle -->
  </g>
</svg>
```

## The hands-and-feet rule

Heavy creatures rest weight on their feet — their feet stay on the ground 50–70% of the cycle. Light creatures push off quickly — feet on the ground only 20–30% of the cycle.

In SMIL terms: the foot's bottom edge stays at the same Y for many consecutive keyframes for a heavy gait; only briefly for a light one.

## Combining with other principles

- Heavy + ease: heavy creatures have very pronounced ease-out (slow finish to motions). Use 7+ keyframes clustered near the peak.
- Heavy + squash: significant squash on landing. The deformation is part of how we read weight.
- Light + follow-through: lots of overshoot, especially on hair/ears (they fly around when the head turns).
- Light + secondary motion: bigger lag amplitudes — capes flap wildly behind a sprinting elf.

## Checking weight from the GIF

When reviewing in phase 5 or 6, ask: "If I covered the silhouette and only watched the rhythm — fast or slow? Heavy thumps or light steps?" If the rhythm doesn't match the subject (a dragon that hops like a sparrow, a fairy that lumbers like an ogre), the weight principle has failed.
