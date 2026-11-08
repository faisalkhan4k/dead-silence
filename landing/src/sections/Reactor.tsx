import Room, { Copy, Heading } from "@/components/Room";

const belief = [
  ["comms", 62],
  ["corridor", 24],
  ["cargo", 9],
  ["reactor", 3],
  ["airlock", 2],
] as const;

const rules = [
  ["Near", "Breath code only. Not a word."],
  ["Far", "Your voice is safe. Talk to Earth Command."],
] as const;

export default function Reactor() {
  return (
    <Room id="reactor" tag="04 / Reactor" place="right">
      <div className="space-y-8">
        <div>
          <Heading>It hears everything.</Heading>
          <Copy>
            <p>
              Nobody has seen it. It finds you by sound: footsteps, doors,
              dropped tools, your breathing. It keeps a map of where it last
              heard you, and the odds fade as time passes.
            </p>
          </Copy>
          <dl className="scrim mt-4 space-y-2 px-4 py-3 font-mono">
            {rules.map(([k, v]) => (
              <div key={k} className="flex gap-4 border-b-2 border-rivet pb-2">
                <dt className="w-12 shrink-0 text-ember uppercase">{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 font-display text-3xl font-extrabold text-threat uppercase">
            Noise near it is instant death.
          </p>
        </div>
        <figure
          role="img"
          aria-label="Example belief map: comms 62 percent, corridor 24 percent, cargo 9 percent, others low."
          className="scrim px-4 py-3 font-mono text-sm"
        >
          <figcaption className="mb-3 uppercase opacity-80">
            Its guess, 5 seconds after a loud breath
          </figcaption>
          {belief.map(([room, pct]) => (
            <div
              key={room}
              className="grid grid-cols-[7em_1fr] items-center gap-3 border-b-2 border-rivet py-1.5"
            >
              <span className="uppercase">{room}</span>
              <span
                className="block h-2.5 bg-threat"
                style={{ width: `${pct}%` }}
              />
            </div>
          ))}
        </figure>
      </div>
    </Room>
  );
}
