import { P } from "./palette";
import { CELL } from "./ping";

export type V3 = [number, number, number];
export type Item = { p: V3; s: V3 };
export type MatKey =
  | "steel"
  | "plate"
  | "rivet"
  | "ash"
  | "ember"
  | "hazard"
  | "signal"
  | "screen"
  | "threat"
  | "void"
  | "strip";
export type Parts = Record<MatKey, Item[]>;

type Spec = {
  color: string;
  metalness: number;
  roughness: number;
  emissive?: string;
  emissiveIntensity?: number;
};

export const MATS: Record<MatKey, Spec> = {
  steel: { color: "#2A2D35", metalness: 0.7, roughness: 0.55 },
  plate: { color: "#3A3E48", metalness: 0.8, roughness: 0.4 },
  rivet: { color: "#5A5F6C", metalness: 0.9, roughness: 0.3 },
  ash: { color: P.ash, metalness: 0.2, roughness: 0.6 },
  ember: { color: P.ember, metalness: 0.2, roughness: 0.4, emissive: P.ember, emissiveIntensity: 3.2 },
  hazard: { color: P.ember, metalness: 0.3, roughness: 0.6, emissive: P.ember, emissiveIntensity: 0.5 },
  signal: { color: P.signal, metalness: 0.1, roughness: 0.3, emissive: P.signal, emissiveIntensity: 2.4 },
  screen: { color: P.signal, metalness: 0.1, roughness: 0.3, emissive: P.signal, emissiveIntensity: 1.3 },
  threat: { color: P.threat, metalness: 0.1, roughness: 0.4, emissive: P.threat, emissiveIntensity: 1.5 },
  void: { color: "#0E0F12", metalness: 0.5, roughness: 0.7 },
  strip: { color: "#DDEFF2", metalness: 0.1, roughness: 0.3, emissive: "#CFE9F0", emissiveIntensity: 2 },
};

export const newParts = (): Parts => ({
  steel: [], plate: [], rivet: [], ash: [], ember: [], hazard: [],
  signal: [], screen: [], threat: [], void: [], strip: [],
});

export const put = (b: Parts, k: MatKey, p: V3, s: V3) => {
  b[k].push({ p, s });
};

export const H = 3.2;
export const D = CELL;

// Small deterministic random so scatter looks the same every load.
export function rng(seed: number) {
  let a = seed;
  return () => {
    a = (a * 1664525 + 1013904223) % 4294967296;
    return a / 4294967296;
  };
}
