"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { P } from "./palette";
import { cellX } from "./ping";
import { rng } from "./parts";

const W = -3;

// Reactor core with three slow rings. Sits on the platform in the reactor.
export function Core({ still }: { still: boolean }) {
  const rings = useRef<(THREE.Mesh | null)[]>([]);
  useFrame(({ clock }) => {
    if (still) return;
    const t = clock.elapsedTime;
    rings.current.forEach((m, i) => {
      if (!m) return;
      m.rotation.x = t * (0.3 + i * 0.17);
      m.rotation.y = t * (0.2 - i * 0.11);
    });
  });
  return (
    <group position={[cellX(3), 1.6, -0.8]}>
      <mesh>
        <cylinderGeometry args={[0.45, 0.45, 2, 20]} />
        <meshStandardMaterial color={P.ember} emissive={P.ember} emissiveIntensity={2.6} roughness={0.3} />
      </mesh>
      {[0.85, 1.05, 1.25].map((r, i) => (
        <mesh key={r} ref={(el) => { rings.current[i] = el; }}>
          <torusGeometry args={[r, 0.045, 8, 48]} />
          <meshStandardMaterial color="#5A5F6C" metalness={0.9} roughness={0.3} emissive={i === 1 ? P.ember : "#000000"} emissiveIntensity={i === 1 ? 1.5 : 0} />
        </mesh>
      ))}
      <pointLight color={P.ember} intensity={9} distance={7} decay={1.6} />
    </group>
  );
}

// Round airlock door with an ember ring.
export function AirlockDoor() {
  return (
    <group position={[cellX(5), 1.4, W + 0.3]}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[1, 1, 0.12, 32]} />
        <meshStandardMaterial color="#5A5F6C" metalness={0.9} roughness={0.35} />
      </mesh>
      <mesh position={[0, 0, 0.08]}>
        <torusGeometry args={[1.08, 0.07, 10, 48]} />
        <meshStandardMaterial color={P.ember} emissive={P.ember} emissiveIntensity={3} />
      </mesh>
      <mesh position={[0, 0, 0.07]}>
        <torusGeometry args={[0.7, 0.03, 8, 40]} />
        <meshStandardMaterial color="#3A3E48" metalness={0.8} roughness={0.4} />
      </mesh>
    </group>
  );
}

// Satellite dish on the hull.
export function Dish() {
  return (
    <mesh position={[cellX(0) + 2.1, 3.15, -1.6]} rotation={[Math.PI - 0.6, 0.5, 0]}>
      <sphereGeometry args={[1.1, 24, 8, 0, Math.PI * 2, 0, Math.PI / 3]} />
      <meshStandardMaterial color="#8A8F9C" metalness={0.9} roughness={0.3} side={THREE.DoubleSide} />
    </mesh>
  );
}

// Stars behind the hull window.
export function Stars() {
  const pos = useMemo(() => {
    const r = rng(7);
    const a = new Float32Array(150 * 3);
    for (let i = 0; i < 150; i++) {
      a[i * 3] = cellX(0) - 1 + (r() - 0.5) * 2.5;
      a[i * 3 + 1] = 1.9 + (r() - 0.5) * 1.1;
      a[i * 3 + 2] = W + 0.14;
    }
    return a;
  }, []);
  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[pos, 3]} />
      </bufferGeometry>
      <pointsMaterial color={P.ash} size={0.035} sizeAttenuation />
    </points>
  );
}

// Slow drifting dust across the whole ship.
export function Dust({ still }: { still: boolean }) {
  const ref = useRef<THREE.Points>(null);
  const pos = useMemo(() => {
    const r = rng(21);
    const a = new Float32Array(240 * 3);
    for (let i = 0; i < 240; i++) {
      a[i * 3] = -3 + r() * 36;
      a[i * 3 + 1] = 0.2 + r() * 2.8;
      a[i * 3 + 2] = -2.6 + r() * 5;
    }
    return a;
  }, []);
  useFrame((_, dt) => {
    const g = ref.current?.geometry.attributes.position;
    if (!g || still) return;
    const a = g.array as Float32Array;
    for (let i = 0; i < a.length; i += 3) {
      a[i + 1] += dt * (0.03 + (i % 7) * 0.006);
      a[i] += dt * 0.02;
      if (a[i + 1] > 3.1) a[i + 1] = 0.2;
      if (a[i] > 33) a[i] = -3;
    }
    g.needsUpdate = true;
  });
  return (
    <points ref={ref} frustumCulled={false}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[pos, 3]} />
      </bufferGeometry>
      <pointsMaterial color={P.ash} size={0.045} sizeAttenuation transparent opacity={0.4} depthWrite={false} />
    </points>
  );
}
