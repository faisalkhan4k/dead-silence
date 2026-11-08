# Dead Silence landing page: prompts (v4, matched to your real skills)

How your skills actually work (read from their SKILL.md):
- vibe-dev-pipeline: brain-dump + pasted code -> VIBE_SPEC.md -> /ponytail builds -> tsc + eslint (3 self-heal loops) -> HALTS at Stage 4 ("open localhost:3000, reply Approve or type visual feedback") -> /ponytail:debt cleanup. Built for the web marketing site. This is the main builder.
- quick-fixer: ONE-file tweaks, 1 self-correct. Not for features.
- bug-hunter: read-only 2-3 sentence diagnosis, then routes to quick-fixer. Use only when a gate fails.
- copy-chief: swaps placeholder text in one target file, matching its length.
- auto-dev-pipeline: heavy (graphify, claude-mem, full security audit). Skip tonight; once before Vultr.
- NOT used: data-seeder (no database), ui-ux-pipeline (does not exist).

Panes: LEFT = chief-of-staff (Opus), RIGHT-TOP = sonnet-worker, RIGHT-BOTTOM = haiku-worker.
Every prompt: only inside landing/ on branch landing/ah7, never main, never git init, small diffs.

## 0. Repo safety (once, left pane)
Use the version already sent. If prompt 0 was already run, run 0b instead.

## 0b. Refresh rules into the repo (only if prompt 0 already ran)
```text
Copy CLAUDE.md and PROMPTS.md from "$HOME/Downloads/Projects/Dead Silence" over landing/CLAUDE.md and landing/PROMPTS.md (quote the path). Branch must be landing/ah7. git add landing; commit "landing: update rules"; git push origin landing/ah7. Report in 2 lines.
```

## 1. Run 1: shell + breath demo (left pane)
```text
Invoke vibe-dev-pipeline. Rough thoughts: landing page for "Dead Silence", a survival-horror game where the page is a house you scroll through. THIS RUN is only the 2D shell and the breath demo; no 3D yet. Pure web. Work only in landing/ on branch landing/ah7 (never main, never merge, rebase or pull, never git init). Source material: landing/reference/index.html (copy and the working demo logic) and landing/DESIGN.md (tokens). Build: Next.js App Router + TypeScript + Tailwind via create-next-app --no-git, next.config output:'export' and images.unoptimized; install three, @react-three/fiber, @react-three/drei, gsap, framer-motion at versions compatible with the installed React (R3F v9 for React 19), unused for now; landing/.gitignore covers node_modules, .next, out. DESIGN.md tokens (soil, wood, plank, dust, bone, lamp, breath, alarm) as the Tailwind theme; fonts Fraunces, IBM Plex Mono, Caveat via next/font. Six full-height sections with ids exterior, kitchen, hall, greenhouse, workshop, launchpad using the prototype's copy; the prototype's rooms card grid becomes room sections. Anti-slop: no card grids, no gradients, no uniform rounded cards, no accenting a single word in headlines; left-aligned text with a thin plank-colour rule. Port the demo to src/components/BreathDemo.tsx with hooks, no logic change: "use client", clear timers on unmount, props onBreath(symbol, level), keys 1/2 and buttons, 800 ms letter gap, 2000 ms word gap, 3-word cap, 70% noise line, lung ring, letter table, reset; mount in the hall. 360 px no horizontal scroll; prefers-reduced-motion respected. Stage 3 gate: tsc, eslint AND `npm run build` (must pass). Start `npm run dev` in the background before the Stage 4 halt and tell me to open localhost:3000. After I reply Approve: run Stage 5, then check branch is landing/ah7, `git add landing` (never VIBE_SPEC.md), commit "landing: draft shell and breath demo", `git push origin landing/ah7`. Report in 5 lines.
```
At the halt: open http://localhost:3000. Reply `Approve`, or type rough visual feedback (the pipeline loops back and rebuilds).

## 2. Run 2: 3D house + scroll camera (RIGHT-TOP pane, after Run 1 is pushed)
```text
Invoke vibe-dev-pipeline. Rough thoughts: add the 3D layer to the existing landing/ app (Run 1 is done). Work only in landing/ on branch landing/ah7; never main, never merge, rebase or pull. Files in landing/src/scene/: House.tsx (cutaway of six connected rooms from boxes and planes, flat palette colours, fog to #140E0C, one warm kitchen point light with slow flicker, faint cold fill); Rings.tsx (expanding #5FA8A0 floor rings via ping(x,z); hero pings slowly; BreathDemo's onBreath pings near the hall); CameraRig.tsx (CatmullRomCurve3 through six room waypoints; GSAP ScrollTrigger, registered client-side only, scrubs a 0 to 1 progress; useFrame reads it to set camera position and lookAt; a hold per section; ScrollTrigger.refresh after mount). Use /advisor if the camera or curve math gets awkward. One fixed Canvas: "use client", next/dynamic with ssr:false, dpr max 1.5, pointer-events none, page readable before it loads. prefers-reduced-motion: no scrub, jump to still frames. Width < 768 or no WebGL: skip the Canvas and show a static CSS/SVG house poster taken from the reference file. The villain is never drawn. Stage 3 gate: tsc, eslint AND `npm run build`. Start `npm run dev` before the Stage 4 halt and tell me to open localhost:3000 and scroll. After I reply Approve: Stage 5, branch check, `git add landing`, commit "landing: 3D house and scroll camera", `git push origin landing/ah7`. Report in 5 lines.
```

## 3. If a gate fails 3 times (RIGHT-BOTTOM pane)
```text
Invoke bug-hunter. The build of landing/ is failing: <paste the last 20 lines of the error>. Read-only. Diagnose in 2 to 3 sentences and say whether quick-fixer can handle it.
```
Then, in the RIGHT-TOP pane: `Invoke quick-fixer: <the fix bug-hunter named, with the file>`.

## 4. Small tweaks (after approval, RIGHT-TOP pane)
One file, one change:
```text
Invoke quick-fixer. In landing/<file>: <change>. Then checkpoint: branch check, git add landing, commit "landing: <what>", git push origin landing/ah7.
```
Bigger visual changes: type them at the vibe-dev-pipeline halt instead.

## 5. Copy polish (tomorrow, one file at a time)
```text
Invoke copy-chief on landing/src/sections/<Section>.tsx. Voice: plain, tense, no hype; keep each text node within its original length.
```

## 6. Later: Vultr deploy (plan only, left pane)
```text
Invoke auto-dev-pipeline, scoped to landing/ only (skip graphify). Plan, do not run: deploy landing/out to a Vultr VM behind Caddy (or Vultr Object Storage static site). List exact commands, DNS/IP needs and the access I need from whoever holds the team's Vultr account. Nothing may touch main or folders outside landing/.
```
