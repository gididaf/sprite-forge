# Follow-through

After a fast motion, parts **overshoot** their final position and settle back. The body doesn't stop on a dime — momentum carries it past the target.

## When to apply

- After any **strike, swing, throw, slash, kick** — the weapon/limb overshoots and rebounds.
- After **landing from a jump** — knees flex past their normal bend, then return.
- After **stopping a run** — body leans forward, then back to upright.
- **Loose/secondary parts** (capes, hair, ears, tails, weapon tassels) always follow through; see `secondary-motion.md`.

## How to express in SMIL `values`

The overshoot is an extra keyframe past the target, then a settle.

**Without follow-through (looks mechanical):**
```
values="0; 60; 0"
```

**With follow-through:**
```
values="0; 60; 70; 55; 60; 0"
```
Result: ramp to 60° → overshoot to 70° → recoil to 55° → settle at 60° → return.

A simpler 4-keyframe version:
```
values="0; 60; 70; 0"
```
The overshoot adds one frame of "the swing went a bit too far" before the return.

## Magnitude rule

- Overshoot is **10–25% beyond** the target.
- The recoil after the overshoot is half the overshoot's magnitude (e.g. overshoot to +70°, settle back to +60°).
- Heavier objects overshoot less (rigid); lighter/looser objects overshoot more (cloth, hair, tails).

## Example: weapon swing

```xml
<g id="weapon-arm" transform="translate(29,25)">
  <animateTransform attributeName="transform" type="rotate"
                    values="0; -20; 80; 95; 75; 0"
                    dur="0.6s" repeatCount="indefinite" additive="sum"/>
  <!-- 0: rest | -20: anticipation | 80: contact/peak | 95: overshoot | 75: recoil | 0: return -->
</g>
```

This combines anticipation + main motion + follow-through. The two principles almost always travel together.
