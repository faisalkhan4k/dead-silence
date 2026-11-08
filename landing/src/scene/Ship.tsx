"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import Batch from "./Batch";
import { AirlockDoor, Core, Dish, Dust, Stars } from "./Extras";
import { Reflections, ShipLights } from "./Lights";
import { MATS, type MatKey } from "./parts";
import { cellX, flickerGain } from "./ping";
import { buildShip } from "./rooms";

const KEYS = Object.keys(MATS) as MatKey[];

export default function Ship({ still }: { still: boolean }) {
  const parts = useMemo(() => buildShip(), []);
  const strip = useRef<THREE.MeshStandardMaterial>(null);
  // Corridor strip lights stutter on their own, slowly.
  useFrame(({ clock }) => {
    if (!strip.current || still) return;
    const t = clock.elapsedTime;
    const dip = Math.sin(t * 0.6) > 0.93 ? 0.15 : 1;
    strip.current.emissiveIntensity =
      (2 + 0.3 * Math.sin(t * 7)) * dip * flickerGain(performance.now() / 1000);
  });
  return (
    <group>
      <Reflections />
      <ShipLights still={still} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[cellX(2.5), -0.12, 0]}>
        <planeGeometry args={[140, 70]} />
        <meshStandardMaterial color="#0A0A0C" roughness={1} />
      </mesh>
      {KEYS.map((k) => (
        <Batch key={k} mat={k} items={parts[k]} matRef={k === "strip" ? strip : undefined} />
      ))}
      <Core still={still} />
      <AirlockDoor />
      <Dish />
      <Stars />
      <Dust still={still} />
    </group>
  );
}
