"use client";

import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { cellX, livePings, ping } from "./ping";

const POOL = 12;
const LIFE = 3.2;
const REACH = 5;

// Expanding floor rings. Hero pings slowly from the lit kitchen window.
export default function Rings({ still }: { still: boolean }) {
  const meshes = useRef<(THREE.Mesh | null)[]>([]);
  const mats = useMemo(
    () =>
      Array.from(
        { length: POOL },
        () =>
          new THREE.MeshBasicMaterial({
            color: "#5FA8A0",
            transparent: true,
            depthWrite: false,
            side: THREE.DoubleSide,
          }),
      ),
    [],
  );

  useEffect(() => {
    if (still) return;
    const id = window.setInterval(() => ping(cellX(1), 1.5), 4500);
    ping(cellX(1), 1.5);
    return () => clearInterval(id);
  }, [still]);

  useFrame(() => {
    if (still) return;
    const now = performance.now() / 1000;
    const list = livePings();
    while (list.length && now - list[0].t > LIFE) list.shift();
    for (let i = 0; i < POOL; i++) {
      const m = meshes.current[i];
      if (!m) continue;
      const p = list[i];
      m.visible = !!p;
      if (!p) continue;
      const k = (now - p.t) / LIFE;
      m.position.set(p.x, 0.03, p.z);
      m.scale.setScalar(0.3 + k * REACH);
      (m.material as THREE.MeshBasicMaterial).opacity = 0.7 * (1 - k) * (1 - k);
    }
  });

  return (
    <group>
      {mats.map((mat, i) => (
        <mesh
          key={i}
          ref={(el) => {
            meshes.current[i] = el;
          }}
          rotation={[-Math.PI / 2, 0, 0]}
          material={mat}
          visible={false}
        >
          <ringGeometry args={[0.92, 1, 64]} />
        </mesh>
      ))}
    </group>
  );
}
