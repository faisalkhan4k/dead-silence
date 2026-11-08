import { btnPrimary, Callout } from "@/components/Room";
import CorridorPoster from "./CorridorPoster";

export default function Hull() {
  return (
    <header id="hull" className="relative flex min-h-svh items-end overflow-hidden">
      <CorridorPoster />
      <div className="hud-text relative w-full px-4 pt-32 pb-[10vh] sm:px-8">
        <Callout>Ship log / last survivor</Callout>
        <h1 className="font-display text-[clamp(4rem,17vw,15rem)] leading-[0.8] font-extrabold tracking-tight uppercase">
          Dead Silence
        </h1>
        <span aria-hidden="true" className="slash mt-5 w-40" />
        <p className="mt-6 font-display text-[clamp(1.6rem,4vw,2.6rem)] font-bold text-ember uppercase">
          Don&apos;t breathe too loud.
        </p>
        <p className="scrim mt-3 mb-8 max-w-[52ch] px-4 py-3">
          You are the last one alive on this ship. Something killed the crew,
          and it hunts by sound.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="#corridor" className={btnPrimary}>
            Try the breath code
          </a>
        </div>
      </div>
    </header>
  );
}
