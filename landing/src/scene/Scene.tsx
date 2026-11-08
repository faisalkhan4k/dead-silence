"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const SceneCanvas = dynamic(() => import("./SceneCanvas"), { ssr: false });

function hasWebGL() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

// Mounts the fixed canvas only on wide screens with WebGL. Otherwise the
// static SVG poster in the hull section is the poster.
export default function Scene() {
  const [on, setOn] = useState(false);
  const [still, setStill] = useState(false);

  useEffect(() => {
    const wide = window.matchMedia("(min-width: 768px)");
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => {
      const ok = wide.matches && hasWebGL();
      setOn(ok);
      setStill(calm.matches);
      document.documentElement.dataset.scene = ok ? "on" : "off";
    };
    sync();
    wide.addEventListener("change", sync);
    calm.addEventListener("change", sync);
    return () => {
      wide.removeEventListener("change", sync);
      calm.removeEventListener("change", sync);
      delete document.documentElement.dataset.scene;
    };
  }, []);

  if (!on) return null;
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0">
      <SceneCanvas key={String(still)} still={still} />
    </div>
  );
}
