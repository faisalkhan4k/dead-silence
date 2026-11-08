import { cellX } from "./ping";
import { D, newParts, put, type Parts } from "./parts";
import { shell } from "./shell";

const W = -D / 2; // back wall z

function hull(b: Parts) {
  const x = cellX(0);
  // window frame (stars are drawn in Extras)
  put(b, "void", [x - 1, 1.9, W + 0.1], [2.6, 1.2, 0.04]);
  put(b, "rivet", [x - 1, 2.55, W + 0.13], [2.8, 0.1, 0.1]);
  put(b, "rivet", [x - 1, 1.25, W + 0.13], [2.8, 0.1, 0.1]);
  for (const dx of [-2.35, 0.35]) put(b, "rivet", [x + dx, 1.9, W + 0.13], [0.1, 1.4, 0.1]);
  // exterior plating with seams
  [[-2.6, 1.3, 0.5, 2.6, 0.7], [-2.1, 0.7, 0.6, 1.4, 0.9], [-2.7, 2.6, 0.45, 0.9, 0.6]].forEach(([dx, y, w, h, d]) =>
    put(b, "plate", [x + dx, y, W + d / 2], [w, h, d]),
  );
  for (let k = 0; k < 6; k++) put(b, "rivet", [x - 2.6, 0.5 + k * 0.4, W + 0.9], [0.06, 0.06, 0.06]);
  // dish post and feed arm, landing light
  put(b, "plate", [x + 2.1, 1.5, -1.6], [0.18, 3, 0.18]);
  put(b, "rivet", [x + 2.1, 3.0, -1.6], [0.5, 0.1, 0.1]);
  put(b, "ember", [x + 2.3, 0.1, 1.8], [0.4, 0.08, 0.4]);
}

function comms(b: Parts) {
  const x = cellX(1);
  // console banks with small screens
  for (const [cx, w] of [[-1.5, 2.4], [1.7, 1.8]]) {
    put(b, "plate", [x + cx, 0.5, W + 0.8], [w, 1, 1]);
    put(b, "rivet", [x + cx, 1.03, W + 0.9], [w, 0.06, 0.9]);
    put(b, "plate", [x + cx, 1.4, W + 0.35], [w + 0.1, 0.5, 0.06]);
    for (let k = 0; k < Math.floor(w / 0.5); k++)
      put(b, "screen", [x + cx - w / 2 + 0.3 + k * 0.5, 1.4, W + 0.4], [0.38, 0.26, 0.05]);
    for (let k = 0; k < 5; k++) put(b, "ember", [x + cx - 0.5 + k * 0.25, 1.08, W + 1.05], [0.06, 0.03, 0.06]);
  }
  // big Earth-call screen
  put(b, "void", [x, 2.1, W + 0.1], [3.4, 1.4, 0.06]);
  put(b, "signal", [x, 2.1, W + 0.14], [3.0, 1.1, 0.04]);
  for (let k = 0; k < 6; k++) put(b, "void", [x, 1.75 + k * 0.14, W + 0.17], [3.0, 0.02, 0.02]);
  // chair
  put(b, "plate", [x, 0.4, 0.4], [0.5, 0.8, 0.5]);
  put(b, "plate", [x, 0.95, 0.65], [0.5, 0.7, 0.1]);
}

function corridor(b: Parts) {
  const x = cellX(2);
  for (const dx of [-2, 0, 2]) {
    put(b, "rivet", [x + dx, 1.2, W + 0.1], [1.2, 2.4, 0.1]);
    put(b, "void", [x + dx, 1.2, W + 0.17], [0.9, 2.1, 0.04]);
    put(b, "ember", [x + dx, 2.45, W + 0.18], [1.2, 0.05, 0.04]);
    put(b, "screen", [x + dx + 0.75, 1.6, W + 0.18], [0.2, 0.14, 0.04]);
  }
  for (let k = 0; k < 11; k += 2) put(b, "hazard", [x - 2.6 + k * 0.5, 0.03, 1.4], [0.3, 0.02, 0.12]);
  for (let k = 0; k < 5; k++) put(b, "strip", [x - 2 + k, 3.1, -1.0], [0.9, 0.05, 0.12]);
}

function reactor(b: Parts) {
  const x = cellX(3);
  put(b, "plate", [x, 0.15, -0.8], [2.4, 0.3, 2.4]);
  put(b, "rivet", [x, 0.32, -0.8], [2.0, 0.04, 2.0]);
  for (const dx of [-1.7, 1.7]) {
    put(b, "plate", [x + dx, 1.6, -2.4], [0.3, 3.2, 0.3]);
    put(b, "rivet", [x + dx * 0.5, 2.9, -2.4], [Math.abs(dx), 0.14, 0.14]);
  }
  put(b, "rivet", [x, 0.9, 1.4], [4, 0.05, 0.05]);
  for (const dx of [-2, -1, 0, 1, 2]) put(b, "rivet", [x + dx, 0.45, 1.4], [0.05, 0.9, 0.05]);
  put(b, "plate", [x + 2.1, 0.6, -2.0], [0.7, 1.2, 0.6]);
  put(b, "screen", [x + 2.1, 1.0, -1.68], [0.5, 0.3, 0.04]);
  put(b, "ember", [x - 2.2, 2.8, W + 0.1], [0.15, 0.15, 0.1]);
}

function cargo(b: Parts) {
  const x = cellX(4);
  const crates: [number, number, number, number, number, number][] = [
    [-1.8, 0.5, -1.8, 1.2, 1, 1.2], [-0.5, 0.4, -2.0, 1, 0.8, 1],
    [-1.7, 1.4, -1.8, 0.9, 0.8, 0.9], [1.2, 0.5, -1.4, 1.4, 1, 1.4], [1.3, 1.5, -1.4, 1, 1, 1],
  ];
  crates.forEach(([dx, y, z, w, h, d]) => {
    put(b, "plate", [x + dx, y, z], [w, h, d]);
    for (const k of [-1, 1]) put(b, "rivet", [x + dx, y + k * h * 0.33, z], [w + 0.05, 0.08, d + 0.05]);
  });
  put(b, "hazard", [x - 0.5, 0.82, -1.5], [0.6, 0.05, 0.05]);
  for (const [dx, z] of [[-2.6, -2.6], [2.6, -2.6], [-2.6, 1.0], [2.6, 1.0]]) put(b, "rivet", [x + dx, 1.6, z], [0.14, 3.2, 0.14]);
  for (const z of [-2.6, 1.0]) put(b, "plate", [x, 3.0, z], [5.4, 0.16, 0.16]);
  put(b, "plate", [x + 0.8, 3.0, -0.8], [0.2, 0.2, 3.6]);
  for (let k = 0; k < 8; k += 2) put(b, "hazard", [x - 2.4 + k * 0.6, 3.0, -2.6], [0.3, 0.18, 0.18]);
  put(b, "rivet", [x + 0.8, 2.85, -0.5], [0.5, 0.2, 0.5]);
  put(b, "void", [x + 0.8, 2.2, -0.5], [0.03, 1.2, 0.03]);
  put(b, "hazard", [x + 0.8, 1.55, -0.5], [0.2, 0.2, 0.2]);
}

function airlock(b: Parts) {
  const x = cellX(5);
  put(b, "plate", [x, 1.4, W + 0.1], [3, 2.8, 0.16]);
  put(b, "plate", [x, 1.4, W + 0.2], [1.8, 0.1, 0.06]);
  put(b, "plate", [x, 1.4, W + 0.2], [0.1, 1.8, 0.06]);
  for (const dx of [-1.5, 1.5]) {
    put(b, "ember", [x + dx, 2.7, W + 0.2], [0.18, 0.18, 0.1]);
    put(b, "ember", [x + dx, 0.03, 0.4], [0.06, 0.02, 3.2]);
  }
  for (let k = 0; k < 8; k += 2) put(b, "hazard", [x - 1.4 + k * 0.4, 0.03, -1.6], [0.4, 0.02, 0.3]);
  put(b, "plate", [x + 2.4, 1.1, -2.2], [0.7, 2.2, 0.7]);
  for (const y of [0.5, 1.1, 1.7]) put(b, "rivet", [x + 2.4, y, -1.84], [0.6, 0.06, 0.04]);
}

export function buildShip(): Parts {
  const b = newParts();
  for (let i = 0; i < 6; i++) shell(b, i);
  hull(b); comms(b); corridor(b); reactor(b); cargo(b); airlock(b);
  return b;
}
