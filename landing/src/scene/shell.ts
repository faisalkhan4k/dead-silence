import { CELL, cellX } from "./ping";
import { D, H, put, type Parts } from "./parts";

// Floor, ribbed back wall, grating, vents, ceiling pipes and a bulkhead door.
export function shell(b: Parts, i: number) {
  const x = cellX(i);
  put(b, "plate", [x, -0.05, 0], [CELL, 0.1, D]);
  put(b, "rivet", [x, 0.05, D / 2], [CELL, 0.1, 0.12]);
  put(b, "steel", [x, H / 2, -D / 2 - 0.05], [CELL, H, 0.1]);
  for (let k = 0; k < 11; k++) put(b, "rivet", [x - 2.5 + k * 0.5, H / 2, -D / 2 + 0.04], [0.1, H, 0.08]);
  for (const y of [0.35, 1.6, 2.9]) put(b, "plate", [x, y, -D / 2 + 0.07], [CELL, 0.14, 0.12]);
  for (let k = 0; k < 18; k++) put(b, "rivet", [x, 0.02, -1.2 + k * 0.24], [CELL - 0.4, 0.03, 0.08]);

  // vents with slats
  put(b, "void", [x - 1.9, 2.3, -D / 2 + 0.14], [0.8, 0.5, 0.06]);
  for (let k = 0; k < 4; k++) put(b, "rivet", [x - 1.9, 2.14 + k * 0.1, -D / 2 + 0.18], [0.72, 0.03, 0.04]);

  // ceiling pipes, cable run and drops
  put(b, "plate", [x, H - 0.2, -2.55], [CELL, 0.16, 0.16]);
  put(b, "rivet", [x, H - 0.45, -2.6], [CELL, 0.1, 0.1]);
  put(b, "void", [x, H - 0.1, -2.2], [CELL, 0.05, 0.05]);
  put(b, "void", [x + 1.2, 2.2, -2.6], [0.04, 1.6, 0.04]);
  put(b, "plate", [x, H - 0.05, -D / 2 + 0.2], [CELL, 0.1, 0.4]);

  if (i === 0) return;
  // bulkhead at the left edge: posts, lintel, ember strips, hazard blocks
  const bx = x - CELL / 2;
  put(b, "plate", [bx, H / 2, -1.9], [0.2, H, 2.2]);
  put(b, "plate", [bx, H / 2, 1.9], [0.2, H, 2.2]);
  put(b, "plate", [bx, H - 0.3, 0], [0.2, 0.6, 1.6]);
  for (const z of [-0.88, 0.88]) put(b, "rivet", [bx, 1.3, z], [0.26, 2.6, 0.1]);
  for (const z of [-0.8, 0.8]) put(b, "ember", [bx, 1.3, z], [0.28, 2.6, 0.06]);
  put(b, "ember", [bx, 2.6, 0], [0.28, 0.06, 1.7]);
  for (let k = 0; k < 8; k += 2) put(b, "hazard", [bx, H - 0.45, -0.7 + k * 0.2], [0.28, 0.14, 0.18]);
}
