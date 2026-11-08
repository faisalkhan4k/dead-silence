# Dead Silence landing page (branch work only)

## HARD RULES: git (read first, every session)
The backend teammate works on `main`. Never touch it.
- Work ONLY on branch `landing/ah7`. Run `git branch --show-current` before every commit and push. If it is not `landing/ah7`, stop.
- NEVER: checkout/switch to main and edit, merge (either direction), rebase, cherry-pick onto main, `git pull` into main, push to main, force-push (`-f`, `--force`, `--force-with-lease`), delete branches, open or merge a PR, edit anything outside `landing/`.
- Allowed: commit on `landing/ah7`, `git push -u origin landing/ah7`, read-only inspection of main (`git fetch origin main`, `git show origin/main:<path>`, `git diff origin/main --stat`).
- All files live under `landing/`. Do not edit root files, lockfiles, CI, or other folders. If a change outside `landing/` seems needed, stop and ask.
- Small commits, one concern each. Message format: `landing: <what>`.

## Project
Landing page for **Dead Silence**, a survival-horror game (UB Hacking 2026, "Into the Hackosmos"). Premise, palette and breath code are in `DESIGN.md`. The shared Ideas doc still describes the older Mars-house idea. The real game is a native 3D app built by a teammate; the page only advertises it.

## Design is a template, not a contract
The concept, palette, type and layout in this file and `DESIGN.md` are a starting point. The owner will change them after looking at references and early builds. Do not defend the current look. When told to change direction: (1) update `DESIGN.md` in a small edit, (2) apply the change in code, (3) keep the quality floor below. Ask once before big changes (new stack, dropping the 3D scene); small visual changes just do.

## Concept: the page is the ship (v2, Nov 7 change, may change again)
Game premise: you are the last person alive on a spaceship; an unknown entity killed the crew and hunts by sound; Earth Command is on a call with you; every door needs a code entered by breath (sniff = 1, puff = 2). Entity close: breath only. Entity far: voice allowed. Noise near it means instant death. Open every door and exit.
Look: Doom Eternal energy (heavy condensed type, hot orange on black, chamfered HUD panels), original assets only. Full spec in `DESIGN.md`.
One fixed WebGL scene (a ship interior of six compartments). Scrolling moves a camera through it. Each compartment is a section:
| Scroll | Section id | Content |
| --- | --- | --- |
| 0 | hull | Title, tagline, one-line premise |
| 1 | comms | Earth Command call, crew is dead |
| 2 | corridor | **Breath-code demo** (press 1/2) |
| 3 | reactor | The entity, near vs far rules, belief-map bars |
| 4 | cargo | The doors, rules |
| 5 | airlock | Team, source link, demo video slot |
The earlier Mars-house concept is retired. `reference/index.html` is the old prototype: use it only for the breath-demo logic and copy that still fits.

## Stack
Next.js (App Router, `output: 'export'`, no server features), Tailwind, React Three Fiber + drei, GSAP + ScrollTrigger (scroll-linked camera), Framer Motion for small UI. No Spline, no hosted 3D blobs. Aceternity components only as hidden utilities, never as visible stock layouts.
Static export so it deploys to a Vultr VM (Caddy/nginx) or object storage unchanged.

## Token budget rules
- Never rewrite a whole file for a small change; use targeted edits.
- One component per task. Keep files under ~250 lines; split if larger.
- Builds and visual changes go through `vibe-dev-pipeline` (its Stage 3 self-heals tsc/eslint up to 3 times; add `npm run build` as an extra gate because we ship a static export). It halts at Stage 4 for a visual check: reply `Approve` or type visual feedback.
- `bug-hunter` is read-only diagnosis: use it only when a gate fails 3 times; it names the cause and routes to `quick-fixer`.
- `quick-fixer` is for one-file tweaks only, never a feature build.
- `auto-dev-pipeline` is heavy (graphify, claude-mem, security audit). Not for tonight; run it once, on landing/ only, before the Vultr deploy.
- Never commit `VIBE_SPEC.md` or `FACTORY_SPEC.md`.
- Do not re-read DESIGN.md every task; read it once per session.

## Quality floor
- Works at 360 px wide, no horizontal scroll. Mobile gets a lighter scene (lower DPR, no post effects).
- `prefers-reduced-motion`: static poster of the scene, no camera scrubbing, no rings animation.
- Keyboard operable demo, visible focus, AA contrast (Alarm only large text/icons).
- Canvas lazy-loaded; page readable before it loads. Total JS target under ~400 KB gzipped.
- Original art only. No Granny or A Quiet Place assets, names or logos.
- Real game footage is not available yet: use clearly labeled placeholder frames in one `media/` map so they can be swapped in one commit.
