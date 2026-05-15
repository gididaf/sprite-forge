# Squash & Stretch

Objects deform on impact and acceleration. A bouncing ball flattens (squashes) on landing and elongates (stretches) at the apex of its jump. Living tissue does this constantly; rigid metal does not.

## When to apply

- **Bouncing** (slimes, balls, springy creatures).
- **Jumping / landing** — squash on take-off and landing; stretch in mid-air.
- **Heavy impacts** — character squashes when hit hard.
- **Breathing / idle** — subtle vertical squash/stretch on torso.

## When NOT to apply

- Rigid armor, weapons, machines, stone, metal.
- Skeletons (bone doesn't deform).
- Anything the user wants to look "stiff" or "mechanical."

## Rule: volume conservation

A squashing shape **widens as it shortens**. A stretching shape **narrows as it elongates**. Pixel area stays roughly the same — otherwise it looks like the character is shrinking/growing instead of deforming.

For a 14×10 ellipse squashed to 14×6 → widen to 18×6. For a 14×10 stretched to 14×16 → narrow to 12×16.

## SMIL implementation

The simplest is `<animateTransform type="scale">` on the deforming element:

```xml
<g id="body">
  <animateTransform attributeName="transform" type="scale"
                    values="1,1; 1.2,0.7; 1,1; 0.85,1.25; 1,1"
                    dur="0.6s" repeatCount="indefinite"/>
  <!-- 1,1: rest | 1.2,0.7: squash on landing | 1,1: pass | 0.85,1.25: stretch at apex | back to rest -->
</g>
```

Note that scale changes affect children too — useful, but watch for the visual centre shifting. If the body squashes at the bottom (landing) you may want to add a small Y translate to keep the feet on the ground.

## Example: slime bounce

```xml
<svg ...>
  <animateTransform attributeName="transform" type="translate"
                    values="0,0; 0,-6; 0,-10; 0,-6; 0,0"
                    dur="0.6s" repeatCount="indefinite"/>
  <g id="body">
    <animateTransform attributeName="transform" type="scale"
                      values="1,1; 0.9,1.1; 0.85,1.15; 0.9,1.1; 1.3,0.65; 1,1"
                      dur="0.6s" repeatCount="indefinite"/>
    <!-- mid-air stretch | landing squash | settle -->
  </g>
</svg>
```

## Stretch as a hint of speed

Fast-moving projectiles and dash-attacks can stretch along their motion axis to imply velocity. An arrow flying left can be `scale="1.4,0.8"` to look like it's moving fast.
