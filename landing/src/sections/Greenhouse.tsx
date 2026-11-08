import Room, { Heading } from "@/components/Room";

const belief = [
  ["kitchen", 62],
  ["hall", 24],
  ["workshop", 9],
  ["greenhouse", 3],
  ["cold storage", 2],
] as const;

export default function Greenhouse() {
  return (
    <Room id="greenhouse">
      <div className="grid items-end gap-10 md:grid-cols-2">
        <div className="max-w-[62ch]">
          <Heading>It remembers where it heard you.</Heading>
          <p className="mb-4">
            The hunter is trained with reinforcement learning. It keeps a belief
            map of the house. Every sound raises the odds of a room, and the
            odds fade as time passes.
          </p>
          <p>Stay quiet and it widens its search. Get loud and it commits.</p>
        </div>
        <figure
          role="img"
          aria-label="Example belief map: kitchen 62 percent, hall 24 percent, workshop 9 percent, others low."
          className="font-mono text-sm"
        >
          <figcaption className="mb-3 opacity-80">
            Its guess, 5 seconds after a loud breath
          </figcaption>
          {belief.map(([room, pct]) => (
            <div
              key={room}
              className="grid grid-cols-[7.5em_1fr] items-center gap-3 border-b border-plank py-1.5"
            >
              <span>{room}</span>
              <span className="block h-2.5 bg-bone/70" style={{ width: `${pct}%` }} />
            </div>
          ))}
        </figure>
      </div>
    </Room>
  );
}
