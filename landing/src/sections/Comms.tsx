import Room, { Heading } from "@/components/Room";

const call = [
  "we have your suit on telemetry. You're the only one still moving.",
  "stay quiet. Four digits.",
];

export default function Comms() {
  return (
    <Room id="comms">
      <Heading>Earth Command is on the line.</Heading>
      <p className="max-w-[64ch]">
        The crew is dead. The ship is still running. The only help you have is
        a voice in your ear, a long way from here, reading you door codes.
      </p>
      <div className="mt-8 border-l-4 border-signal bg-void/60 px-4 py-3 font-mono text-signal">
        <p className="mb-2 text-xs tracking-widest uppercase opacity-80">
          ● Live call / channel 4
        </p>
        {call.map((line) => (
          <p key={line}>
            <span className="uppercase">Earth Command:</span> {line}
          </p>
        ))}
      </div>
    </Room>
  );
}
