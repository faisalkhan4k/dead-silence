import Room, { Heading } from "@/components/Room";

const rules = [
  "Every door is locked. Earth Command reads you the code.",
  "You answer with your breath. A sniff is 1, a puff is 2.",
  "When it is close, breathe the code. Do not speak.",
  "When it is far, your voice is safe. Use it.",
  "Every breath is noise. Keep it short.",
  "The last door is the airlock. Open it and you live.",
];

export default function Cargo() {
  return (
    <Room id="cargo" tag="05 / Cargo" place="low">
      <Heading>Open every door. Then get out.</Heading>
      <ol className="scrim max-w-[62ch] px-4">
        {rules.map((r, i) => (
          <li key={r} className="flex gap-4 border-b border-rivet py-3 last:border-b-0">
            <span aria-hidden="true" className="w-6 shrink-0 font-mono text-ember">
              {i % 2 ? "●" : "○"}
            </span>
            <p>{r}</p>
          </li>
        ))}
      </ol>
    </Room>
  );
}
