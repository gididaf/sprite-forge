# Animation Principles

Seven principles to consult during phases 5 and 6 of the pipeline. Each doc explains the principle, when it applies, and how to express it in SMIL `values=` lists for this engine.

## Index

| Principle | One-line |
|-----------|----------|
| [anticipation](anticipation.md) | Wind-up before the action so the eye can follow it |
| [follow-through](follow-through.md) | Overshoot past the target, then settle back |
| [ease](ease.md) | Cluster keyframes near extremes to slow in/out — combats robotic linear motion |
| [squash-stretch](squash-stretch.md) | Deform on impact and acceleration (volume-conserving) |
| [arcs](arcs.md) | Motion follows curves, not straight lines |
| [secondary-motion](secondary-motion.md) | Loose parts (hair, cape, tail) lag the primary motion |
| [weight](weight.md) | Cues that communicate mass — duration, anticipation depth, bob, stance |

## When to consult

- **Phase 1 (spec)**: name which principles apply to this subject in the third layer of the spec.
- **Phase 5 (primary animation)**: anticipation, follow-through, arcs, ease all live in the primary motion.
- **Phase 6 (polish)**: secondary motion, weight refinement, ease refinement, squash-stretch detail.

## Common combinations

| Subject | Principles to focus on |
|---------|------------------------|
| Walking character | arcs, secondary-motion, weight, ease |
| Striking warrior | anticipation, follow-through, ease (on contact frame: skip ease) |
| Bouncing slime | squash-stretch, ease, weight (light) |
| Flying dragon | arcs (wing-tip path), follow-through (tail), weight (heavy = slow wings) |
| Casting wizard | anticipation (hand pull-back), arcs (spell trajectory), secondary-motion (robe) |
| Idle character | ease (subtle), secondary-motion (cloth/hair sway), weight (breath rate) |

## The principle test for review

After phase 6, walk through your phase-1 principle list and check each:

- **Does the anticipation read?** (Cover frames 1–3; can you tell what's about to happen?)
- **Does follow-through read?** (Cover the strike frame; do the trailing frames show overshoot?)
- **Does the motion feel eased?** (Mentally tap to the rhythm — does it pulse or tick?)
- **Are arcs present?** (Trace a hand or foot across frames — curve or line?)
- **Do secondary parts trail?** (Does the cape move with the body, or after it?)
- **Does the weight match the subject?** (See `weight.md` review tip.)

Any FAIL is a phase-6 fix.
