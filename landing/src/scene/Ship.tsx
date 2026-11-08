"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { P } from "./palette";
import { CELL, cellX, flickerGain } from "./ping";

type V3 = [number, number, number];

function Box({
  p,
  s,
  c = P.plate,
  glow,
}: {
  p: V3;
  s: V3;
  c?: string;
  glow?: number;
}) {
  return (
    <mesh position={p}>
      <boxGeometry args={s} />
      <meshStandardMaterial
        color={c}
        flatShading
        roughness={0.9}
        metalness={0.3}
        emissive={glow ? c : "#000000"}
        emissiveIntensity={glow ?? 0}
      />
    </mesh>
  );
}

const H = 3.2;
const D = CELL;

// Floor, back wall, rib bands, and a bulkhead with a doorway and ember strips.
// The front is open: a cutaway.
function Compartment({ i, floor }: { i: number; floor: string }) {
  return (
    <group position={[cellX(i), 0, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[CELL, D]} />
        <meshStandardMaterial color={floor} flatShading roughness={1} />
      </mesh>
      <mesh position={[0, H / 2, -D / 2]}>
        <planeGeometry args={[CELL, H]} />
        <meshStandardMaterial color={P.steel} flatShading roughness={1} />
      </mesh>
      {[0.5, 1.7, 2.9].map((y) => (
        <Box key={y} p={[0, y, -D / 2 + 0.03]} s={[CELL, 0.06, 0.04]} c={P.rivet} />
      ))}
      <Box p={[0, 0.04, D / 2]} s={[CELL, 0.08, 0.1]} c={P.rivet} />
      {i > 0 && (
        <group position={[-CELL / 2, 0, 0]}>
          <Box p={[0, H / 2, -D / 4 - 0.4]} s={[0.18, H, D / 2 - 0.8]} c={P.plate} />
          <Box p={[0, H / 2, D / 4 + 0.4]} s={[0.18, H, D / 2 - 0.8]} c={P.plate} />
          <Box p={[0, H - 0.3, 0]} s={[0.18, 0.6, 1.6]} c={P.plate} />
          {/* ember strips on the door frame */}
          <Box p={[0.11, 1.3, -0.8]} s={[0.03, 2.6, 0.06]} c={P.ember} glow={2.2} />
          <Box p={[0.11, 1.3, 0.8]} s={[0.03, 2.6, 0.06]} c={P.ember} glow={2.2} />
          <Box p={[0.11, 2.6, 0]} s={[0.03, 0.06, 1.6]} c={P.ember} glow={2.2} />
        </group>
      )}
    </group>
  );
}

// One slow ember emergency pulse; stutters once when the demo gets too loud.
function Emergency({ still }: { still: boolean }) {
  const ref = useRef<THREE.PointLight>(null);
  useFrame(({ clock }) => {
    if (!ref.current || still) return;
    const t = clock.elapsedTime;
    const pulse = 0.55 + 0.45 * Math.sin(t * 1.1);
    ref.current.intensity = 30 * pulse * flickerGain(performance.now() / 1000);
  });
  return (
    <pointLight
      ref={ref}
      position={[cellX(2), 2.8, 0.5]}
      color={P.ember}
      intensity={20}
      distance={18}
      decay={1.5}
    />
  );
}

export default function Ship({ still }: { still: boolean }) {
  const fill = useRef<THREE.DirectionalLight>(null);
  useFrame(() => {
    if (fill.current && !still)
      fill.current.intensity = 0.4 * flickerGain(performance.now() / 1000);
  });
  return (
    <group>
      <ambientLight intensity={0.1} color={P.ash} />
      <directionalLight ref={fill} position={[8, 10, 14]} intensity={0.4} color={P.signal} />
      <Emergency still={still} />
      {/* faint threat glow under the reactor door. The entity is never drawn. */}
      <pointLight
        position={[cellX(3) - CELL / 2 + 0.3, 0.12, 0]}
        color={P.threat}
        intensity={2.5}
        distance={4}
        decay={2}
      />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[cellX(2.5), -0.02, 0]}>
        <planeGeometry args={[120, 60]} />
        <meshStandardMaterial color={P.void} roughness={1} />
      </mesh>

      {[P.steel, P.plate, P.steel, P.plate, P.steel, P.plate].map((f, i) => (
        <Compartment key={i} i={i} floor={f} />
      ))}

      {/* 0 hull: outer plating, antenna mast, hatch */}
      <Box p={[cellX(0) - 1.6, 1.6, -2.7]} s={[1.4, 3.2, 0.3]} c={P.rivet} />
      <Box p={[cellX(0) + 1.8, 2.2, -2.2]} s={[0.12, 4.4, 0.12]} c={P.ash} />
      <Box p={[cellX(0) + 1.8, 4.1, -2.2]} s={[1.2, 0.08, 0.08]} c={P.ash} />

      {/* 1 comms: console desk with signal screens */}
      <Box p={[cellX(1), 0.5, -2.2]} s={[4.4, 1, 1]} c={P.plate} />
      <Box p={[cellX(1) - 1, 1.5, -2.5]} s={[1.3, 0.8, 0.08]} c={P.signal} glow={1.4} />
      <Box p={[cellX(1) + 1, 1.5, -2.5]} s={[1.3, 0.8, 0.08]} c={P.signal} glow={0.8} />

      {/* 2 corridor: ribs and floor grating */}
      {[-2, -0.7, 0.7, 2].map((dx) => (
        <Box key={dx} p={[cellX(2) + dx, H / 2, -2.85]} s={[0.25, H, 0.25]} c={P.rivet} />
      ))}
      <Box p={[cellX(2), 0.03, 0.3]} s={[5, 0.03, 1.2]} c={P.rivet} />

      {/* 3 reactor: core stack with a faint ember glow */}
      <Box p={[cellX(3), 1.4, -1.2]} s={[1.6, 2.8, 1.6]} c={P.plate} />
      <Box p={[cellX(3), 1.5, -0.38]} s={[0.7, 1.8, 0.05]} c={P.ember} glow={0.7} />
      <Box p={[cellX(3) + 2.1, 1.3, -2.4]} s={[0.35, 2.6, 0.35]} c={P.rivet} />

      {/* 4 cargo: crates */}
      <Box p={[cellX(4) - 1.2, 0.5, -1.8]} s={[1.4, 1, 1.2]} c={P.rivet} />
      <Box p={[cellX(4) - 1.2, 1.4, -1.8]} s={[1.0, 0.8, 0.9]} c={P.plate} />
      <Box p={[cellX(4) + 1.3, 0.4, -1.4]} s={[1.2, 0.8, 1.2]} c={P.plate} />

      {/* 5 airlock: heavy outer door */}
      <Box p={[cellX(5), 1.4, -2.85]} s={[2.4, 2.8, 0.2]} c={P.rivet} />
      <Box p={[cellX(5), 2.9, -2.72]} s={[2.6, 0.08, 0.06]} c={P.ember} glow={2.2} />
      <Box p={[cellX(5), 0.05, 0.4]} s={[2.6, 0.03, 3.4]} c={P.ember} glow={0.5} />
    </group>
  );
}
