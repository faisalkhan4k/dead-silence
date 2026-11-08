import Room, { Heading } from "@/components/Room";
import HallBreath from "@/components/HallBreath";

export default function Hall() {
  return (
    <Room id="hall" className="bg-wood">
      <Heading>Try the breath code.</Heading>
      <p className="max-w-[62ch]">
        Press <b>1</b> for a sniff and <b>2</b> for a puff, or tap the buttons.
        Pause 0.8 seconds to lock a letter, 2 seconds to lock a word. Watch the
        noise meter: past the red line, it hears you.
      </p>
      <HallBreath />
    </Room>
  );
}
