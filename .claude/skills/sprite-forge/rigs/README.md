# Rigs

Rest-pose SVGs with pre-wired joint groups. Each `<g id="...">` is a joint pivot — just add `<animateTransform type="rotate" values="..." additive="sum" dur="..." repeatCount="indefinite"/>` inside it to animate.

All rigs use a neutral grey palette so they restyle freely. Pick one from `../styles/` to recolor.

## Index

| Rig | Use for |
|-----|---------|
| `humanoid.svg` | Generic warrior, hero, villager, knight, skeleton, zombie, peasant |
| `humanoid_caster.svg` | Wizard, sorcerer, witch, cultist, priest — has staff + casting hand |
| `humanoid_archer.svg` | Archer, ranger, hunter — bow + arrow + draw-pose anchors pre-set |
| `humanoid_brute.svg` | Ogre, troll, orc warlord, minotaur — wider viewBox, hunched, thick limbs |
| `quadruped.svg` | Horse, deer, cow, dog, generic four-legged — head held high |
| `quadruped_predator.svg` | Wolf, lion, panther, dire-wolf — low slung, fangs, tail curve |
| `wing_flapper_small.svg` | Bat, sprite, fairy, small bird, imp |
| `wing_flapper_large.svg` | Dragon, eagle, wyvern, gryphon — wider viewBox for wing extension |
| `serpent.svg` | Snake, worm, eel, naga, slug — segmented for slither animation |
| `multi_leg.svg` | Spider, crab, scorpion, insect — six legs in tripod gait |
| `blob.svg` | Slime, jelly, pudding, ooze — symmetric, idle bounce |
| `levitator.svg` | Ghost, wraith, fire elemental, will-o-wisp — no legs, floats |
| `static_object.svg` | Chest, torch, brazier, lever, gem — base + animated feature |
| `rider.svg` | Cavalry, knight on horse, goblin on warg — rider locked to mount |
| `projectile.svg` | Arrow, bullet, magic bolt, thrown axe — heads LEFT |
| `vehicle.svg` | Cart, wagon, cannon, carriage — wheels rotate, body bobs |

## Joint convention

Every `<g id="...">` with `transform="translate(jx, jy)"` is a joint at (jx, jy). Shapes inside are positioned relative to the joint. Add `<animateTransform>` as a direct child with `additive="sum"` to rotate around the joint without losing the translate.

Example — animate the front arm from -30° to +30°:

```xml
<g id="front-arm" transform="translate(29,25)">
  <animateTransform attributeName="transform" type="rotate"
                    values="-30 0 0; 30 0 0; -30 0 0"
                    dur="0.6s" repeatCount="indefinite" additive="sum"/>
  <rect x="-2" y="0" width="5" height="12" fill="..."/>
  <circle cx="-0.5" cy="13" r="2" fill="..."/>
</g>
```
