"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { CELL, cellX } from "./ping";

const C = {
  floor: "#3B2A22",
  wall: "#2A1B15",
  trim: "#C8643B",
  bone: "#E8DCC4",
  lamp: "#E7B65C",
  breath: "#5FA8A0",
};

type V3 = [number, number, number];

function Box({ p, s, c, o }: { p: V3; s: V3; c: string; o?: number }) {
  return (
    <mesh position={p}>
      <boxGeometry args={s} />
      <meshStandardMaterial
        color={c}
        flatShading
        roughness={1}
        transparent={o !== undefined}
        opacity={o ?? 1}
      />
    </mesh>
  );
}

const H = 3.2;
const D = CELL;

// Floor, back wall, and a partition with a doorway. The front is open: a cutaway.
function Shell({ i, floor }: { i: number; floor: string }) {
  const x = cellX(i);
  return (
    <group position={[x, 0, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[CELL, D]} />
        <meshStandardMaterial color={floor} flatShading roughness={1} />
      </mesh>
      <mesh position={[0, H / 2, -D / 2]}>
        <planeGeometry args={[CELL, H]} />
        <meshStandardMaterial color={C.wall} flatShading roughness={1} />
      </mesh>
      {i > 0 && (
        <>
          <Box p={[-CELL / 2, H / 2, -D / 4 - 0.4]} s={[0.15, H, D / 2 - 0.8]} c={C.wall} />
          <Box p={[-CELL / 2, H / 2, D / 4 + 0.4]} s={[0.15, H, D / 2 - 0.8]} c={C.wall} />
          <Box p={[-CELL / 2, H - 0.3, 0]} s={[0.15, 0.6, 1.6]} c={C.wall} />
        </>
      )}
      <Box p={[0, 0.05, D / 2]} s={[CELL, 0.1, 0.12]} c={C.trim} />
    </group>
  );
}

// Warm kitchen lamp with a slow, uneven flicker.
function Lamp({ still }: { still: boolean }) {
  const ref = useRef<THREE.PointLight>(null);
  useFrame(({ clock }) => {
    if (!ref.current || still) return;
    const t = clock.elapsedTime;
    const dip = Math.sin(t * 0.9) > 0.96 ? 0.45 : 1;
    ref.current.intensity = 26 * dip * (0.9 + 0.1 * Math.sin(t * 2.3));
  });
  return (
    <pointLight
      ref={ref}
      position={[cellX(1), 2.7, 0.5]}
      color={C.lamp}
      intensity={26}
      distance={16}
      decay={1.6}
    />
  );
}

export default function House({ still }: { still: boolean }) {
  return (
    <group>
      <ambientLight intensity={0.12} color="#E8DCC4" />
      <directionalLight position={[8, 10, 14]} intensity={0.35} color={C.breath} />
      <Lamp still={still} />

      {/* ground outside the house */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[cellX(2.5), -0.02, 0]}>
        <planeGeometry args={[120, 60]} />
        <meshStandardMaterial color="#140E0C" roughness={1} />
      </mesh>

      {[
        C.floor, // 0 porch
        C.floor, // 1 kitchen
        "#34251E", // 2 hall
        C.floor, // 3 greenhouse
        "#34251E", // 4 workshop
        "#2A1B15", // 5 launch pad
      ].map((f, i) => (
        <Shell key={i} i={i} floor={f} />
      ))}

      {/* 0 porch: steps and a post */}
      <Box p={[cellX(0) - 1, 0.2, 1.8]} s={[2.4, 0.4, 1.2]} c={C.trim} />
      <Box p={[cellX(0) + 2.4, 1.2, -2.6]} s={[0.2, 2.4, 0.2]} c={C.bone} />

      {/* 1 kitchen: counter, table, lit window */}
      <Box p={[cellX(1) + 0.4, 0.5, -2.4]} s={[4.4, 1, 0.9]} c="#3B2A22" />
      <Box p={[cellX(1) - 0.8, 0.45, 0.8]} s={[1.6, 0.1, 1.1]} c={C.bone} />
      <Box p={[cellX(1) - 0.8, 0.22, 0.8]} s={[0.15, 0.44, 0.15]} c={C.wall} />
      <Box p={[cellX(1) - 1.9, 1.9, -2.96]} s={[1.2, 0.9, 0.05]} c={C.lamp} />

      {/* 2 hall: console and a long rug */}
      <Box p={[cellX(2), 0.45, -2.5]} s={[3, 0.9, 0.6]} c="#3B2A22" />
      <Box p={[cellX(2), 0.03, 0.4]} s={[1.4, 0.04, 4.2]} c={C.trim} />

      {/* 3 greenhouse: glass panes and planters */}
      <Box p={[cellX(3), 1.6, -2.9]} s={[5.6, 2.6, 0.04]} c={C.breath} o={0.14} />
      {[-1.8, 0, 1.8].map((dx) => (
        <group key={dx}>
          <Box p={[cellX(3) + dx, 0.3, -1.4]} s={[1.2, 0.6, 0.8]} c="#3B2A22" />
          <Box p={[cellX(3) + dx, 0.95, -1.4]} s={[0.9, 0.7, 0.5]} c={C.breath} />
        </group>
      ))}

      {/* 4 workshop: bench, tool wall */}
      <Box p={[cellX(4) - 0.5, 0.55, -1.8]} s={[3.4, 1.1, 1.1]} c="#3B2A22" />
      <Box p={[cellX(4) + 1.6, 1.8, -2.95]} s={[1.4, 1.2, 0.05]} c={C.trim} />

      {/* 5 launch pad: open slab, tower, rocket */}
      <Box p={[cellX(5), 0.06, 0]} s={[5, 0.12, 5]} c="#3B2A22" />
      <Box p={[cellX(5) + 1.6, 2.2, -1.6]} s={[0.35, 4.4, 0.35]} c={C.trim} />
      <Box p={[cellX(5) - 0.4, 2, -1.4]} s={[0.9, 3.8, 0.9]} c={C.bone} />
    </group>
  );
}
