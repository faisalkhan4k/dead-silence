"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { LETTERS as T, ROWS } from "./letters";
import { initial, NOISE_LINE, reducer, type Sym } from "./breathState";

const LETTER_GAP = 800;
const WORD_GAP = 2000;

export default function BreathDemo({
  onBreath,
}: {
  onBreath?: (symbol: Sym, level: number) => void;
}) {
  const [st, dispatch] = useReducer(reducer, initial);
  const [hit, setHit] = useState<Sym | null>(null);
  const timers = useRef<{ letter?: number; word?: number; hit?: number }>({});
  const onBreathRef = useRef(onBreath);
  useEffect(() => {
    onBreathRef.current = onBreath;
  }, [onBreath]);

  // Report each breath with the noise level it produced.
  useEffect(() => {
    if (st.last) onBreathRef.current?.(st.last, st.level);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fire once per breath only
  }, [st.breaths]);

  const breath = useCallback((sym: Sym) => {
    const t = timers.current;
    dispatch({ type: "breath", sym });
    clearTimeout(t.letter);
    clearTimeout(t.word);
    t.letter = window.setTimeout(() => dispatch({ type: "letter" }), LETTER_GAP);
    t.word = window.setTimeout(() => dispatch({ type: "word" }), WORD_GAP);
  }, []);

  const flash = useCallback((sym: Sym) => {
    setHit(sym);
    clearTimeout(timers.current.hit);
    timers.current.hit = window.setTimeout(() => setHit(null), 120);
  }, []);

  const reset = () => {
    clearTimeout(timers.current.letter);
    clearTimeout(timers.current.word);
    dispatch({ type: "reset" });
  };

  // Noise decays while you stay quiet.
  useEffect(() => {
    const id = window.setInterval(() => dispatch({ type: "decay" }), 300);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "1" || e.key === "2") {
        breath(e.key);
        flash(e.key);
      }
    };
    document.addEventListener("keydown", onKey);
    const t = timers.current;
    return () => {
      document.removeEventListener("keydown", onKey);
      clearTimeout(t.letter);
      clearTimeout(t.word);
      clearTimeout(t.hit);
    };
  }, [breath, flash]);

  const loud = st.level > NOISE_LINE;
  const keyCls = (sym: Sym) =>
    `border-2 border-signal px-5 py-3 font-mono uppercase tracking-wider active:bg-signal active:text-void active:shadow-[0_0_18px_rgb(47_196_214/0.6)] ${
      hit === sym ? "bg-signal text-void shadow-[0_0_18px_rgb(47_196_214/0.6)]" : "bg-void text-ash"
    }`;

  return (
    <div className="mt-6">
      <div className="grid items-center gap-7 md:grid-cols-[220px_minmax(0,1fr)]">
        <svg
          viewBox="0 0 220 220"
          role="img"
          aria-label="Lung ring. Grows on a sniff, shrinks on a puff."
          className="h-[200px] w-[200px]"
        >
          <circle cx="110" cy="110" r="90" fill="none" stroke="#3A3D45" strokeWidth="8" />
          <circle
            cx="110"
            cy="110"
            r={st.r}
            fill="none"
            stroke={loud ? "#E3182D" : "#2FC4D6"}
            strokeWidth="8"
            className="transition-[r] duration-250 ease-in-out"
          />
          <text x="110" y="118" textAnchor="middle" fill="#E6E3DC" fontSize="22" className="font-mono uppercase">
            {st.lung}
          </text>
        </svg>

        <div className="w-full min-w-0 font-mono">
          <div className="mb-3.5 flex flex-wrap gap-2.5" aria-live="polite">
            {[0, 1, 2].map((i) => {
              const on = i === st.words.length && Boolean(st.cur || st.buf);
              const text = st.words[i] || (i === st.words.length ? st.cur : "");
              return (
                <div
                  key={i}
                  className={`min-h-[2.6em] min-w-[5.5ch] border-2 bg-plate px-3 py-2 text-lg tracking-[0.12em] ${
                    on ? "border-ember" : "border-rivet"
                  }`}
                >
                  {text}
                </div>
              );
            })}
          </div>

          <div className="h-[2em] text-2xl tracking-[0.3em] text-signal" aria-label="Current code">
            {st.buf
              .split("")
              .map((c) => (c === "1" ? "○" : "●"))
              .join(" ")}
            {T[st.buf] && <span className="text-ash"> {T[st.buf]}</span>}
          </div>

          <div
            className={`relative mt-2.5 mb-1 h-4 border-2 bg-void ${
              loud ? "border-threat shadow-[0_0_18px_rgb(227_24_45/0.55)] motion-safe:animate-shake" : "border-rivet"
            }`}
          >
            <div
              className={`h-full transition-[width,background-color] duration-150 ${
                loud ? "bg-threat" : "bg-signal"
              }`}
              style={{ width: `${st.level}%` }}
            />
            <i
              className="absolute -top-1.5 -bottom-1.5 w-0.5 bg-threat"
              style={{ left: `${NOISE_LINE}%` }}
            />
          </div>
          <div className="text-sm uppercase opacity-80">noise</div>

          <div className="my-4 flex flex-wrap items-center gap-3">
            <button type="button" aria-label="Sniff, symbol 1" className={keyCls("1")} onClick={() => breath("1")}>
              1 sniff
            </button>
            <button type="button" aria-label="Puff, symbol 2" className={keyCls("2")} onClick={() => breath("2")}>
              2 puff
            </button>
            <button type="button" className="text-sm text-ember uppercase underline" onClick={reset}>
              clear message
            </button>
          </div>
          <div
            role="status"
            className={
              loud
                ? "font-display text-2xl font-extrabold text-threat uppercase"
                : "text-sm opacity-80"
            }
          >
            {st.status}
          </div>
        </div>
      </div>

      <h3 className="mt-7 mb-2 font-display text-2xl font-extrabold uppercase">Letter table</h3>
      <p className="mb-2 font-mono text-sm opacity-80">
        Common letters get the shortest codes. 1 = sniff, 2 = puff.
      </p>
      <table className="w-full max-w-[760px] border-collapse font-mono text-sm">
        <tbody>
          {ROWS.map(({ n, codes }) => (
            <tr key={n} className="border-b-2 border-rivet align-top">
              <th className="w-[5.5em] px-2.5 py-1.5 text-left font-normal text-ember uppercase">
                {n} {n === 1 ? "breath" : "breaths"}
              </th>
              <td className="px-2.5 py-1.5">
                {codes.map((k) => (
                  <span key={k} className="mr-4 inline-block whitespace-nowrap">
                    <span className="text-signal">{k}</span> {T[k]}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
