"use client";

import BreathDemo from "./BreathDemo";
import { cellX, ping } from "@/scene/ping";

// Each breath in the demo drops a ring on the hall floor.
export default function HallBreath() {
  return (
    <BreathDemo
      onBreath={(sym) => ping(cellX(2) + (sym === "1" ? -0.8 : 0.8), 0.8)}
    />
  );
}
