"use client";

import { Canvas } from "@react-three/fiber";
import CameraRig from "./CameraRig";
import House from "./House";
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
      <color attach="background" args={["#140E0C"]} />
      <fog attach="fog" args={["#140E0C", 9, 34]} />
      <House still={still} />
      <Rings still={still} />
      <CameraRig still={still} />
    </Canvas>
  );
}
