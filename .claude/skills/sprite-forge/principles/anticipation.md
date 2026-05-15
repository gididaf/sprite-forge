# Anticipation

A small backwards motion **before** the main action. The character "winds up" so the eye can follow the strike, jump, or throw. Without anticipation, action looks instantaneous and weightless.

## When to apply

- Any **strike, swing, punch, kick, slash, headbutt**.
- Any **jump, leap, lunge**.
- **Spell casting** — the hand pulls back before extending.
- **Bow draw** — micro-relaxation before pulling.
- **Crouch before standing**, lean-back before forward charge.

## How to express it in SMIL `values`

The lerper interpolates linearly between keyframes. Anticipation is a keyframe that goes the **opposite** way before the main motion.

**Wrong (no anticipation):**
```
values="0; 60; 0"
```
Result: arm at rest → snaps to 60° → snaps back. Reads as a glitch.

**Right (with anticipation):**
```
values="0; -15; 60; 30; 0"
```
Result: arm pulls back 15° (wind-up) → swings to 60° (strike) → recoils to 30° (follow-through, see `follow-through.md`) → returns. Reads as a deliberate strike.

## Keyframe-count rule of thumb

For a 1-cycle action animation (8 frames over 0.6s):
- Frame 0: rest
- Frame 1: anticipation extreme (small reverse)
- Frames 2–4: ramp into main action
- Frame 5: peak/extreme of action
- Frames 6–7: follow-through + return

The anticipation should be **10–25% of the main motion's magnitude** — small enough to read as a wind-up, not as a separate action.

## Example: archer drawing

Without anticipation, the bow draw starts from zero. With anticipation, the archer's draw-arm relaxes forward 5–10° before pulling back.

```xml
<g id="back-arm" transform="translate(33,26)">
  <animateTransform attributeName="transform" type="rotate"
                    values="0; 8; -45; -50; -45; 0"
                    dur="0.8s" repeatCount="indefinite" additive="sum"/>
  <!-- frame layout: rest, anticip (forward 8°), draw (back 45°), peak (50°), release ramp, return -->
</g>
```
