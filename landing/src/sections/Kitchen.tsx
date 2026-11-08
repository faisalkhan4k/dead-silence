import Room, { Heading } from "@/components/Room";

const premise = [
  {
    title: "Where you are",
    body: "A habitat that looks like someone's home. Kitchen, greenhouse, a workshop with the lights half on. The Artemis III is on the pad behind it.",
  },
  {
    title: "What hunts you",
    body: "It can't see well. It listens. Footsteps, doors, dropped tools, and your breathing all tell it where you are.",
  },
  {
    title: "How you talk",
    body: "You and your crewmate share a breath code. A sniff is 1. A puff is 2. Every word costs noise, so you get three.",
  },
];

export default function Kitchen() {
  return (
    <Room id="kitchen">
      <Heading>The house on Mars has a tenant.</Heading>
      <dl className="max-w-[62ch] space-y-6">
        {premise.map((p) => (
          <div key={p.title}>
            <dt className="font-mono text-sm text-lamp">{p.title}</dt>
            <dd className="mt-1">{p.body}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-8 inline-block -rotate-[1.5deg] font-hand text-2xl opacity-85">
        say less. live longer.
      </p>
    </Room>
  );
}
