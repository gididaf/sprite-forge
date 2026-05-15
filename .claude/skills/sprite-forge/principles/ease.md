# Ease (in / out)

Motion accelerates and decelerates — it doesn't move at constant speed. The lerper used by the bake engine is **linear between keyframes**, so ease has to be expressed by **clustering keyframes near the extremes** (slow) and **spreading them in the middle** (fast).

## When to apply

- Always, for any cycle motion. Linear motion is the #1 reason sprites look "robotic."
- Especially important on **bouncing, swinging, breathing, idle hovering** — anything with a natural rest/peak.

## Linear vs eased keyframes

**Linear (robotic):**
```
values="0; 30; 60; 30; 0"
```
Equal jumps between values → constant velocity → mechanical feel.

**Ease-out (fast start, slow finish):**
```
values="0; 30; 50; 58; 60; 58; 50; 30; 0"
```
Big jumps early (0→30→50), small jumps near the peak (50→58→60). Motion decelerates as it reaches the extreme — natural for an arc reaching its apex.

**Ease-in-out (slow at both ends, fast in middle):**
```
values="0; 5; 20; 45; 55; 60; 55; 45; 20; 5; 0"
```
Small jumps at start and end, big jumps in middle. Reads as a smooth, natural cycle.

## Rule of thumb: 5–7 keyframes minimum

For an 8-frame sprite over 0.6s:
- 2 keyframes (start/end) = perfectly linear → robotic.
- 3 keyframes (start/peak/end) = triangular → still mechanical.
- **5–7 keyframes with values clustered near the peak = eased** → natural.

The bake engine renders 8 frames; the lerper picks values between keyframes. More keyframes = more anchor points = smoother apparent motion.

## Example: body bob with ease

```xml
<svg ...>
  <!-- Linear (bad) -->
  <animateTransform type="translate" values="0,0; 0,-2; 0,0" dur="0.6s" repeatCount="indefinite"/>

  <!-- Eased (good) -->
  <animateTransform type="translate"
                    values="0,0; 0,-0.5; 0,-1.5; 0,-2; 0,-1.5; 0,-0.5; 0,0"
                    dur="0.6s" repeatCount="indefinite"/>
</svg>
```

The eased version slows as the body reaches the apex of the bob, then accelerates back down — like a real bounce.

## When NOT to ease

- **Impact contact frame** — should be sharp, not eased. If you smooth out the moment of impact, the hit loses its punch.
- **Strikes and slashes**: anticipation eases in, the strike itself is fast and linear, follow-through eases out.
