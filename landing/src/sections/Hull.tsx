import { btnCls, Plate } from "@/components/Room";
import CorridorPoster from "./CorridorPoster";

export default function Hull() {
  return (
    <header id="hull" className="relative flex min-h-svh items-end overflow-hidden">
      <CorridorPoster />
      <div className="relative mx-auto w-full max-w-[1040px] px-4 pt-32 pb-[12vh]">
        <Plate>
          <h1 className="font-display text-[clamp(3.5rem,14vw,9rem)] leading-[0.85] font-extrabold tracking-tight uppercase">
            Dead Silence
          </h1>
          <span aria-hidden="true" className="slash mt-4 w-32" />
          <p className="mt-5 font-display text-[clamp(1.4rem,3.5vw,2rem)] font-bold text-ember uppercase">
            Don&apos;t breathe too loud.
          </p>
          <p className="mt-3 mb-8 max-w-[64ch]">
            You are the last one alive on this ship. Something killed the crew,
            and it hunts by sound.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href="#corridor" className={`${btnCls} bg-ember text-void`}>
              Try the breath code
            </a>
            <a href="#airlock" className={`${btnCls} text-ember`}>
              Watch the demo
            </a>
          </div>
        </Plate>
      </div>
    </header>
  );
}
