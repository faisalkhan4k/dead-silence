import Room, { btnGhost, Copy, Heading } from "@/components/Room";
import { media } from "@/media";

export default function Airlock() {
  return (
    <Room id="airlock" tag="06 / Airlock" place="left">
      <Heading>Built in 24 hours.</Heading>
      <Copy>
        <p>
          UB Hacking 2026, theme &quot;Into the Hackosmos&quot;. Four builders:
          one on breath recognition and the entity, three on the game and its
          look.
        </p>
      </Copy>
      <p className="mt-4 mb-8 font-mono text-sm uppercase">
        Builder 1 / Builder 2 / Builder 3 / Builder 4
      </p>
      <div className="flex flex-wrap gap-3">
        <a href={media.demoVideo.src ?? "#airlock"} className={btnGhost}>
          {media.demoVideo.label}
        </a>
        <a href={media.sourceUrl} className={btnGhost}>
          Read the source
        </a>
      </div>
      <p className="mt-16 font-mono text-sm opacity-85">
        Dead Silence. UB Hacking 2026. Original characters and art.
      </p>
    </Room>
  );
}
