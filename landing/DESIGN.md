# Dead Silence design system (landing page) v2: derelict ship, Doom Eternal energy

> **Status: starting template, not final.** The team changed the concept on Nov 7. Palette, fonts, 3D scene and layout can still change after a browser check. When direction changes, update this file first, then the code. Keep the quality floor (accessibility, mobile, reduced motion). Everything else is negotiable.
> **Originality rule:** inspired by the aggressive, heavy, high-contrast HUD look of Doom Eternal. No Doom logos, fonts, art, sounds or copied layouts.

## Concept
You are the last person alive on a spaceship. Something unknown killed the rest of the crew and it hunts by sound. Earth Command is on a call with you. Every door needs a code, and you enter it with your breath. Entity close: breath code only, silent. Entity far: you may use your voice. Make noise when it is near and it kills you instantly. Open every door and get out.

## Mood
Hostile, loud, mechanical. Hard edges, heavy type, hot orange against black, red when it is near. The only quiet thing on the page is the demo, and that is the point.

## Palette (replaces the Mars palette)
| Token | Hex | Use |
| --- | --- | --- |
| void | #0A0A0C | Page background |
| steel | #16171B | Panels, hull geometry |
| plate | #24262C | Raised plates, empty slots |
| rivet | #3A3D45 | Borders, rules |
| ash | #E6E3DC | Text |
| ember | #FF5A1F | Primary accent: buttons, focus, door strips, slashes |
| threat | #E3182D | The entity and danger only; large text and icons only (about 4:1 on void) |
| signal | #2FC4D6 | Player breath and the Earth Command call: rings, demo meter, comms text |

Contrast on void: ash 15:1, ember 6:1, signal 9:1.
One highlight at a time in view: ember by default, threat only when something is dangerous.

## Type
- Barlow Condensed 800 and 700, uppercase, tight, for titles and section heads. Set large.
- Barlow 400/500 for body, 17 px, lines under 64 characters.
- Share Tech Mono for HUD labels, codes, buttons and the comms transcript.

## Shapes and surfaces
- Chamfered panels: `clip-path` with 10 px cut corners (top-right and bottom-left), 2 px rivet border (use a 2 px inset outline since clip-path hides borders).
- Slash divider: a skewed ember bar (-12 deg), 6 px tall, used between sections and under headings.
- HUD corner brackets on the demo panel.
- Glow only on interactive or dangerous things: ember glow on focus and active buttons, threat glow when the noise meter is over the line.
- Comms strip: a signal-coloured transcript line styled as a call ("EARTH COMMAND: stay quiet. Four digits.").

## Symbols
Ring = 1 (inhale, sniff). Disc = 2 (exhale, puff). Used in the demo, the letter table and the door keypad bullets.

## 3D scene rules
- Ship interior built from boxes and planes in code, no imported assets: six compartments in a line with door frames between them (hull, comms bay, corridor, reactor, cargo, airlock).
- Flat-shaded steel, fog to void, ember strips on every door frame, slow ember emergency pulse, faint cold fill.
- Breath rings: expanding signal-coloured floor rings, triggered by demo key presses. If demo noise is over 70 percent, rings turn threat red and the scene lights flicker once.
- The entity is never shown: a red light under a door, a shadow crossing a gap.
- Camera on a spline through the compartments, scrubbed by scroll, with a hold per section.
- Budget: DPR cap 1.5 (1 on mobile), under 150 draw calls.

## Motion
- One orchestrated moment on load: door strips power on, one ring fires.
- Scroll camera is the main motion. Noise meter shakes when over the line (off under reduced motion).
- No fade-and-slide-up on every section.
- Reduced motion: scene frozen at each compartment's still frame.

## Layout
- Left-aligned text over the scene, big condensed uppercase headings, ember slash under each.
- Panels are chamfered plates, not rounded cards. No bento grid, no gradient washes, no identical rounded cards.
- Section map (ids): hull, comms, corridor, reactor, cargo, airlock.

## Copy
Short, plain, command voice. Buttons: "Try the breath code", "Watch the demo", "Read the source". Demo errors say what happened: "Too loud. It heard that."

## Section content
| id | Compartment | Content |
| --- | --- | --- |
| hull | Exterior / hull | Title, tagline "Don't breathe too loud.", one line of premise |
| comms | Comms bay | The call: you are alone, Earth Command is on the line, crew is dead |
| corridor | Corridor | **Breath-code demo** (keys 1 and 2), door keypad framing |
| reactor | Reactor | The entity: hears everything. Near means breath only. Far means voice. Noise near it means instant death. Belief-map bars |
| cargo | Cargo | The doors: open every one, then exit. Rules list |
| airlock | Airlock | Team, source link, demo video slot |

## Checklist before each visual commit
1. Does it still look like this game and not any generic sci-fi page? If not, rework.
2. One highlight colour in view at a time?
3. Any element animating without a user action or the camera? Cut it.
4. Text readable over the scene at 360 px?
