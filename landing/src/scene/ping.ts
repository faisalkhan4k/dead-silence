// Tiny shared store: anything can drop a floor ring; Rings.tsx draws them.
export type Ping = { x: number; z: number; t: number };

export const CELL = 6;
export const cellX = (i: number) => i * CELL;

const pings: Ping[] = [];

export function ping(x: number, z: number) {
  pings.push({ x, z, t: performance.now() / 1000 });
  if (pings.length > 12) pings.shift();
}

export const livePings = () => pings;
