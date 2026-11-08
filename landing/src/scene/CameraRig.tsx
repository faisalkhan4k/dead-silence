"use client";

import { useEffect, useMemo, useRef } from "react";
import { invalidate, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

// One waypoint per room: exterior, kitchen, hall, greenhouse, workshop, pad.
const POS: [number, number, number][] = [
  [-4, 2.4, 10.5],
  [6, 2.2, 7.4],
  [12, 2.0, 7.2],
  [18, 2.3, 7.6],
  [24, 2.1, 7.4],
  [30, 3.0, 10],
];
const LOOK: [number, number, number][] = [
  [4, 1.6, 0],
  [6, 1.4, 0],
  [12, 1.3, 0],
  [18, 1.2, 0],
  [24, 1.2, 0],
  [30, 2.2, -1],
];
const N = POS.length;
const HOLD = 0.55; // share of each section where the camera stays put

const smooth = (t: number) => t * t * (3 - 2 * t);

// Scroll progress 0..1 to curve parameter 0..1, with a hold per section.
export function holdMap(p: number) {
  const s = Math.min(Math.max(p, 0), 1) * N;
  const i = Math.min(Math.floor(s), N - 1);
  const f = s - i;
  const move = f <= HOLD ? 0 : smooth((f - HOLD) / (1 - HOLD));
  return Math.min((i + (i === N - 1 ? 0 : move)) / (N - 1), 1);
}

export default function CameraRig({ still }: { still: boolean }) {
  const u = useRef(0);
  const camera = useThree((s) => s.camera);
  const curves = useMemo(
    () => ({
      pos: new THREE.CatmullRomCurve3(POS.map((v) => new THREE.Vector3(...v))),
      look: new THREE.CatmullRomCurve3(LOOK.map((v) => new THREE.Vector3(...v))),
    }),
    [],
  );
  const tmp = useMemo(() => new THREE.Vector3(), []);

  const place = () => {
    camera.position.copy(curves.pos.getPoint(u.current));
    camera.lookAt(curves.look.getPoint(u.current, tmp));
  };

  useEffect(() => {
    let dead = false;
    let cleanup = () => {};
    (async () => {
      const [{ gsap }, { ScrollTrigger }] = await Promise.all([
        import("gsap"),
        import("gsap/ScrollTrigger"),
      ]);
      if (dead) return;
      gsap.registerPlugin(ScrollTrigger);
      const made: ScrollTrigger[] = [];
      if (still) {
        // Reduced motion: no scrub, jump to the still frame of the room in view.
        document.querySelectorAll<HTMLElement>("main > *").forEach((el, i) => {
          made.push(
            ScrollTrigger.create({
              trigger: el,
              start: "top 55%",
              end: "bottom 55%",
              onToggle: (self) => {
                if (!self.isActive) return;
                u.current = i / (N - 1);
                place();
                invalidate();
              },
            }),
          );
        });
      } else {
        made.push(
          ScrollTrigger.create({
            trigger: "main",
            start: "top top",
            end: "bottom bottom",
            scrub: 0.8,
            onUpdate: (self) => {
              u.current = holdMap(self.progress);
            },
          }),
        );
      }
      requestAnimationFrame(() => ScrollTrigger.refresh());
      cleanup = () => made.forEach((t) => t.kill());
    })();
    return () => {
      dead = true;
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- place is stable per curves/camera
  }, [still]);

  useEffect(() => {
    place();
    invalidate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curves, camera]);

  useFrame(() => {
    if (!still) place();
  });

  return null;
}
