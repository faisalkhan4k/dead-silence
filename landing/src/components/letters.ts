// Breath code: 1 = sniff, 2 = puff. Common letters get the shortest codes.
export const LETTERS: Record<string, string> = {
  "1": "E", "2": "T",
  "11": "A", "12": "O", "21": "I", "22": "N",
  "111": "S", "112": "H", "121": "R", "122": "D",
  "211": "L", "212": "U", "221": "C", "222": "M",
  "1111": "F", "1112": "W", "1121": "G", "1122": "Y",
  "1211": "P", "1212": "B", "1221": "V", "1222": "K",
  "2111": "J", "2112": "X", "2121": "Q", "2122": "Z",
};

export const ROWS = [1, 2, 3, 4].map((n) => ({
  n,
  codes: Object.keys(LETTERS).filter((k) => k.length === n),
}));
