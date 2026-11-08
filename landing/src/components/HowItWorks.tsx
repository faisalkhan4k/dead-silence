import { Plate } from "@/components/Room";

const facts = [
  "A Windows desktop app listens through a headset microphone.",
  "Audio is read in 50 ms windows.",
  "A random forest classifies each window as silence, inhale or exhale, smoothed over three windows.",
  "The decoder turns breaths into digits and letters: 0.8 s letter gap, 2.0 s word gap, 4.0 s send gap.",
  "2211 deletes the last letter.",
  "Gemini suggests words and writes replies.",
  "ElevenLabs speaks the reply through the default output device.",
];

const planned = ["The RL entity.", "The connection to the game."];

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
          {planned.map((p) => (
            <li key={p}>
              <span className="font-mono text-xs tracking-widest uppercase opacity-80">
                Planned, not built:
              </span>{" "}
              {p}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm opacity-80">
          This page&apos;s demo uses keys 1 and 2 in place of the microphone.
        </p>
      </Plate>
    </div>
  );
}
