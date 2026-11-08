import { Plate } from "@/components/Room";

const facts = [
  "A Python bridge reads a microphone and sends breath events to the game over a local TCP connection.",
  "Audio is read as a rolling one-second window, with a prediction every 50 ms.",
  "A random forest on 12 features labels each prediction inhale, exhale or silence; three matching predictions switch the state.",
  "Five breaths make a letter. After a letter: 1 s cooldown. 3 s of silence adds a space. 5 s sends.",
  "22121 deletes the last letter.",
];

const status = [
  ["Planned, not built:", "Gemini-written riddles."],
  ["In progress:", "The Godot scene and the entity's behavior."],
] as const;

export default function HowItWorks() {
  return (
    <div className="mt-6">
      <Plate>
        <p className="mb-4 font-mono text-xs tracking-widest uppercase opacity-80">
          How it works
        </p>
        <ul className="list-disc space-y-2 pl-5">
          {facts.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
        <ul className="mt-4 list-disc space-y-2 pl-5">
          {status.map(([label, text]) => (
            <li key={text}>
              <span className="font-mono text-xs tracking-widest uppercase opacity-80">
                {label}
              </span>{" "}
              {text}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm opacity-80">
          Offline: 20 of 20 on original held-out clips (no silence clips) and 21
          of 22 on newer ones, 97 training clips. Live accuracy not measured.
        </p>
        <p className="mt-4 text-sm opacity-80">
          This page&apos;s demo uses keys 1 and 2 in place of the microphone.
        </p>
      </Plate>
    </div>
  );
}
