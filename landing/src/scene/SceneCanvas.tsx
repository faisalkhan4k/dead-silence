"use client";

import { Canvas } from "@react-three/fiber";
import CameraRig from "./CameraRig";
import { P } from "./palette";
import Ship from "./Ship";
import Rings from "./Rings";

export default function SceneCanvas({ still }: { still: boolean }) {
  return (
    <Canvas
      dpr={[1, 1.5]}
      frameloop={still ? "demand" : "always"}
      camera={{ fov: 42, near: 0.1, far: 80, position: [-4, 2.4, 10.5] }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      style={{ pointerEvents: "none" }}
      aria-hidden="true"
    >
      <color attach="background" args={[P.void]} />
      <fog attach="fog" args={[P.void, 8, 30]} />
      <Ship still={still} />
      <Rings still={still} />
      <CameraRig still={still} />
    </Canvas>
  );
}
