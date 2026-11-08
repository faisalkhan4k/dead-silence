import { DELETE_CODE, LETTERS as T } from "./letters";

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
  cool: boolean;
};

export type Action =
  | { type: "breath"; sym: Sym }
  | { type: "ready" }
  | { type: "word" }
  | { type: "send" }
  | { type: "decay" }
  | { type: "reset" };

export const initial: State = {
  buf: "",
  cur: "",
  words: [],
  level: 0,
  r: 60,
  lung: "breathe",
  status: "Try 11111 for A.",
  breaths: 0,
  last: null,
  cool: false,
};

// Fifth breath of a code: lock the letter, or delete on 22121. Then cool down.
function commitCode(s: State, buf: string): State {
  const base = { ...s, buf: "", cool: true };
  if (buf === DELETE_CODE) {
    if (s.cur) return { ...base, cur: s.cur.slice(0, -1), status: "Deleted." };
    const last = s.words[s.words.length - 1];
    if (!last) return { ...base, status: "Nothing to delete." };
    return { ...base, words: s.words.slice(0, -1), cur: last.slice(0, -1), status: "Deleted." };
  }
  const L = T[buf];
  return {
    ...base,
    cur: L ? s.cur + L : s.cur,
    status: L ? "Locked " + L + "." : "No letter for " + buf + ". Cleared.",
  };
}

function commitWord(s: State): State {
  if (!s.cur) return s.buf ? { ...s, buf: "" } : s;
  if (s.words.length >= MAX_WORDS) return { ...s, buf: "", cur: "", status: "Message full." };
  return { ...s, buf: "", words: [...s.words, s.cur], cur: "", status: "Word locked: " + s.cur + "." };
}

export function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "breath": {
      if (s.cool) return s;
      const buf = (s.buf + a.sym).slice(-5);
      const level = Math.min(100, s.level + 14);
      const next: State = {
        ...(buf.length === 5 ? commitCode(s, buf) : { ...s, buf }),
        r: Math.max(30, Math.min(88, s.r + (a.sym === "1" ? 10 : -10))),
        lung: a.sym === "1" ? "inhale" : "exhale",
        level,
        breaths: s.breaths + 1,
        last: a.sym,
      };
      return level > NOISE_LINE ? { ...next, status: "Noise meter (simulated): too loud." } : next;
    }
    case "ready":
      return { ...s, cool: false };
    case "word":
      return commitWord(s);
    case "send": {
      const msg = [...s.words, s.cur].filter(Boolean).join(" ");
      if (!msg) return s;
      return { ...s, buf: "", cur: "", words: [], status: "Sent: " + msg + ". (demo only)" };
    }
    case "decay":
      return s.level > 0 ? { ...s, level: Math.max(0, s.level - 6) } : s;
    case "reset":
      return { ...s, buf: "", cur: "", words: [], status: "Cleared." };
  }
}
