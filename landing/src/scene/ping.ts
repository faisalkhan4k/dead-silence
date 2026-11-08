// Tiny shared store: anything can drop a floor ring; Rings.tsx draws them.
export type Ping = { x: number; z: number; t: number; hot: boolean };

export const CELL = 6;
export const cellX = (i: number) => i * CELL;
export const NOISE_LINE = 70;

const pings: Ping[] = [];
let flickerAt = -10;

// level is the demo noise (0..100). Over the line: red ring and one flicker.
export function ping(x: number, z: number, level = 0) {
  const t = performance.now() / 1000;
  const hot = level > NOISE_LINE;
  if (hot) flickerAt = t;
  pings.push({ x, z, t, hot });
  if (pings.length > 12) pings.shift();
}

export const livePings = () => pings;

// Light multiplier: 1 normally, stutters once for 0.6 s after a hot ping.
export function flickerGain(now: number) {
  const k = now - flickerAt;
  if (k < 0 || k > 0.6) return 1;
  return Math.floor(k * 14) % 2 === 0 ? 0.15 : 1;
}
