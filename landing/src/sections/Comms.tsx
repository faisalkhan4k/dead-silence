import Room, { Copy, Heading } from "@/components/Room";

const call = [
  "we have your suit on telemetry. You're the only one still moving.",
  "stay quiet. Enter the code.",
];

export default function Comms() {
  return (
    <Room id="comms" tag="02 / Comms bay" place="right">
      <div className="scrim inline-block px-4 py-2">
        <Heading>Earth Command is on the line.</Heading>
      </div>
      <Copy>
        <p>
          The crew is dead. The ship is still running. The only help you have is
          a voice in your ear, a long way from here, reading you door codes.
        </p>
      </Copy>
      <div className="mt-8 border-l-4 border-signal bg-void/70 px-4 py-3 font-mono text-signal">
        <p className="mb-2 text-xs tracking-widest uppercase opacity-80">
          ● Scripted call / channel 4
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
