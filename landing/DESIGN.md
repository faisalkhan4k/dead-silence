# Dead Silence design system (landing page)

> **Status: starting template, not final.** Everything below is a working direction. The palette, fonts, 3D "page is the house" concept, layout and motion rules can all change as the owner explores references and sees it in the browser. When a direction changes, update this file first, then the code. Keep the anti-slop checklist and the quality floor (accessibility, mobile, reduced motion); everything else is negotiable.

## Mood
A lived-in house that is wrong. Warm lamp light in a cold dark. Quiet. Sound made visible. Dread comes from restraint, not gore.

## Palette
| Token | Hex | Use |
| --- | --- | --- |
| soil | #140E0C | Page background, deep shadow |
| wood | #2A1B15 | Panels, floors |
| plank | #3B2A22 | Borders, empty slots |
| dust | #C8643B | Mars terrain and sky glow only, never UI accents |
| bone | #E8DCC4 | Text |
| lamp | #E7B65C | The single UI accent: buttons, focus, lit windows |
| breath | #5FA8A0 | Player sound only: rings, demo meter |
| alarm | #D93A2B | Danger only; large text/icons (4.6:1 on soil) |

Contrast on soil: bone 14:1, lamp 10:1, breath 7:1.

## Type
- Fraunces (700, opsz 144) for titles. Large, tight tracking, set low on the page.
- IBM Plex Mono (400/500) for HUD, code, subtitles, buttons.
- Caveat (500) for handwritten notes on walls. Max one per room.
- Body 17-18 px serif, line length under 62 characters, line-height 1.65.

## Symbols
Ring = 1 (inhale). Disc = 2 (exhale). Used in the demo, the letter table and as bullets in the puzzles list.

## 3D scene rules
- Cutaway house built from boxes and planes in code. No imported assets for v1.
- Flat-shaded, low-key: one warm point light in the occupied room, faint cold fill, fog to soil.
- Sound rings: expanding flat rings on the floor (shader or scaled torus), breath colour, fade out. Triggered by the demo's key presses and slowly in the hero.
- The villain is never shown. It is a light that dims, a shadow that crosses a door, a footstep sound the user can enable.
- Camera moves along a spline between rooms, scrubbed by scroll. Hold on each room while its text is on screen.
- Dust particles: a few hundred points, very slow.
- Budget: under 150 draw calls, DPR capped at 1.5 (1 on mobile).

## Motion
- One orchestrated moment: hero load (window lights, rings begin).
- Scroll camera is the main motion. Everything else answers user input only.
- No fade-and-slide-up on every section, no hover transitions on every card.
- Reduced motion: scene frozen at each room's still frame.

## Layout
- Left-aligned text blocks sit over the dark half of each room; the lit half stays clear.
- Text panels have no card chrome: a thin plank rule on the left and nothing else.
- No bento grid, no gradient washes, no identical rounded cards, no all-caps eyebrow labels.

## Copy
Short, plain, sentence case. Verbs for buttons: "Try the breath code", "Watch the demo", "Read the source". Errors in the demo say what happened: "Too loud. It heard that."

## Anti-slop checklist (run before each commit that changes visuals)
1. Would this section look the same with another game's name on it? If yes, rework.
2. Any stock Aceternity layout visible? Remove or restyle.
3. More than one accent colour in view? Cut to lamp.
4. Any element animating without a user action or the camera? Cut it.
5. Is the lit window the brightest thing in the first screen? Keep it that way.
