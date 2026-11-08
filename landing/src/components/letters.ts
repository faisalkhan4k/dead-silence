// Breath code: 1 = inhale, 2 = exhale. Every letter is five breaths.
// The first 26 five-digit codes of 1 and 2, in ascending order, are A to Z.
const toCode = (n: number) =>
  [...n.toString(2).padStart(5, "0")].map((b) => (b === "0" ? "1" : "2")).join("");

export const LETTERS: Record<string, string> = Object.fromEntries(
  Array.from({ length: 26 }, (_, n) => [toCode(n), String.fromCharCode(65 + n)]),
);

// The 27th code deletes the last letter.
export const DELETE_CODE = toCode(26);

export const CODES = Object.keys(LETTERS).sort();
