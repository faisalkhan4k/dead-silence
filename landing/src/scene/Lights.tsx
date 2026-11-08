"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Environment, Lightformer } from "@react-three/drei";
import * as THREE from "three";
import { P } from "./palette";
import { CELL, cellX, flickerGain } from "./ping";

const DOORS = [1, 2, 3, 4, 5];

// Code-made reflections for the metal. No HDR download.
export function Reflections() {
  return (
    <Environment resolution={64} frames={1} environmentIntensity={0.8}>
      <Lightformer form="rect" intensity={4} color={P.ember} position={[-8, 2, -2]} rotation-y={Math.PI / 2} scale={[8, 3, 1]} />
      <Lightformer form="rect" intensity={3} color={P.signal} position={[4, 5, 8]} scale={[12, 2, 1]} />
      <Lightformer form="ring" intensity={2.5} color="#ffffff" position={[0, 7, 0]} rotation-x={Math.PI / 2} scale={6} />
    </Environment>
  );
}

// Cold key and rim lights, ember pulses at each door, one threat glow.
export function ShipLights({ still }: { still: boolean }) {
  const doors = useRef<(THREE.PointLight | null)[]>([]);
  const key = useRef<THREE.DirectionalLight>(null);
  useFrame(({ clock }) => {
    if (still) return;
    const t = clock.elapsedTime;
    const g = flickerGain(performance.now() / 1000);
    doors.current.forEach((l, i) => {
      if (l) l.intensity = 9 * (0.65 + 0.35 * Math.sin(t * 0.9 + i * 0.8)) * g;
    });
    if (key.current) key.current.intensity = 1.5 * g;
  });
  return (
    <>
      <hemisphereLight args={["#7088B0", "#1A0F0A", 0.9]} />
      <directionalLight ref={key} position={[6, 10, 12]} intensity={1.5} color="#BCD8FF" />
      <directionalLight position={[-8, 5, -10]} intensity={1.1} color={P.signal} />
      <directionalLight position={[26, 4, -10]} intensity={0.8} color={P.ember} />
      {DOORS.map((d, i) => (
        <pointLight
          key={d}
          ref={(el) => { doors.current[i] = el; }}
          position={[cellX(d) - CELL / 2 + 0.7, 2.4, 1.2]}
          color={P.ember}
          intensity={9}
          distance={9}
          decay={1.6}
        />
      ))}
      {/* faint threat glow under the far reactor door. The entity is never drawn. */}
      <pointLight position={[cellX(4) - CELL / 2 + 0.3, 0.12, 0]} color={P.threat} intensity={2.5} distance={4} decay={2} />
    </>
  );
}
