import Room, { Copy, Heading, Plate } from "@/components/Room";
import CorridorBreath from "@/components/CorridorBreath";

const corner = "pointer-events-none absolute h-5 w-5 border-ember";

export default function Corridor() {
  return (
    <Room id="corridor" tag="03 / Corridor" wide>
      <Heading>Try the breath code.</Heading>
      <Copy>
        <p>
          Every door on this ship takes a code, and you enter it with your
          breath. Press <b>1</b> for a sniff and <b>2</b> for a puff, or tap the
          buttons. Pause 0.8 seconds to lock a letter, 2 seconds to lock a word.
          Past the red line, it hears you.
        </p>
      </Copy>
      <div className="mt-8 [text-shadow:none]">
        <Plate>
          <div className="relative p-4 sm:p-6">
            <span
              aria-hidden="true"
              className={`${corner} top-0 left-0 border-t-2 border-l-2`}
            />
            <span
              aria-hidden="true"
              className={`${corner} top-0 right-0 border-t-2 border-r-2`}
            />
            <span
              aria-hidden="true"
              className={`${corner} bottom-0 left-0 border-b-2 border-l-2`}
            />
            <span
              aria-hidden="true"
              className={`${corner} right-0 bottom-0 border-r-2 border-b-2`}
            />
            <p className="font-mono text-xs tracking-widest uppercase opacity-80">
              Door 01 / keypad
            </p>
            <CorridorBreath />
          </div>
        </Plate>
      </div>
    </Room>
  );
}
