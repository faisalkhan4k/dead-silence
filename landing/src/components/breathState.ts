import { LETTERS as T } from "./letters";

export type Sym = "1" | "2";

export const MAX_WORDS = 3;
export const NOISE_LINE = 70;

export type State = {
  buf: string;
  cur: string;
  words: string[];
  level: number;
  r: number;
  lung: string;
  status: string;
  breaths: number;
  last: Sym | null;
};

export type Action =
  | { type: "breath"; sym: Sym }
  | { type: "letter" }
  | { type: "word" }
  | { type: "decay" }
  | { type: "reset" };

export const initial: State = {
  buf: "",
  cur: "",
  words: [],
  level: 0,
  r: 60,
  lung: "breathe",
  status: "Try: 1 (E), 2 (T), 11 (A), 22 (N).",
  breaths: 0,
  last: null,
};

function commitLetter(s: State): State {
  if (!s.buf) return s;
  const L = T[s.buf];
  return {
    ...s,
    buf: "",
    cur: L ? s.cur + L : s.cur,
    status: L ? "Locked " + L + "." : "No letter for " + s.buf + ". Cleared.",
  };
}

function commitWord(prev: State): State {
  const s = commitLetter(prev);
  if (!s.cur) return s;
  if (s.words.length >= MAX_WORDS) return { ...s, cur: "" };
  const words = [...s.words, s.cur];
  return {
    ...s,
    words,
    cur: "",
    status:
      "Word locked: " +
      s.cur +
      (words.length === MAX_WORDS ? ". Message full. Clear to start over." : "."),
  };
}

export function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "breath": {
      const buf = (s.buf + a.sym).slice(-4);
      const level = Math.min(100, s.level + 22);
      return {
        ...s,
        buf,
        r: Math.max(30, Math.min(88, s.r + (a.sym === "1" ? 10 : -10))),
        lung: a.sym === "1" ? "sniff" : "puff",
        level,
        status: level > NOISE_LINE ? "Too loud. It heard that." : s.status,
        breaths: s.breaths + 1,
        last: a.sym,
      };
    }
    case "letter":
      return commitLetter(s);
    case "word":
      return commitWord(s);
    case "decay":
      return s.level > 0 ? { ...s, level: Math.max(0, s.level - 6) } : s;
    case "reset":
      return { ...s, buf: "", cur: "", words: [], status: "Cleared." };
  }
}
