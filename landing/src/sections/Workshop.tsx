import Room, { Heading } from "@/components/Room";

const rooms = [
  ["Kitchen.", "The fuse box hides behind the pantry. Your crewmate reads the order, you flip the switches."],
  ["Greenhouse.", "Glass floors and loud leaves. Good place to lose it, if you stay still."],
  ["Workshop.", "Tools that clatter when dropped. Useful as a lure."],
  ["Med bay.", "Locked until you find the code. Your crewmate has half of it."],
  ["Cold storage.", "A door that seals from outside. Two consoles, one shared word, ten seconds."],
  ["Launch pad.", "Punch in the code with your own breath. Every digit is noise."],
] as const;

export default function Workshop() {
  return (
    <Room id="workshop">
      <Heading>Six rooms between you and the ship.</Heading>
      <ol className="max-w-[62ch]">
        {rooms.map(([name, body], i) => (
          <li key={name} className="flex gap-4 border-b border-plank py-3">
            <span aria-hidden="true" className="pt-0.5 font-mono text-sm opacity-60">
              {i % 2 ? "●" : "○"}
            </span>
            <p>
              <b className="text-lamp">{name}</b> {body}
            </p>
          </li>
        ))}
      </ol>
    </Room>
  );
}
