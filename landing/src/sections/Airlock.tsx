import Room, { btnGhost, Copy, Heading } from "@/components/Room";
import { media } from "@/media";

export default function Airlock() {
  return (
    <Room id="airlock" tag="06 / Airlock" place="left">
      <Heading>Watch a run.</Heading>
      <Copy>
        <p>One ship. One breath code. Don&apos;t breathe too loud.</p>
      </Copy>
      <Copy>
        <p>
          UB Hacking 2026, theme &quot;Into the Hackosmos&quot;. Four builders:
          one on breath recognition, three on the game and its look.
        </p>
      </Copy>
      <div className="flex flex-wrap gap-3">
        {media.demoVideo.src && (
          <a href={media.demoVideo.src} className={btnGhost}>
            {media.demoVideo.label}
          </a>
        )}
        {media.sourceUrl && (
          <a href={media.sourceUrl} className={btnGhost}>
            Read the source
          </a>
        )}
      </div>
      <p className="mt-16 font-mono text-sm opacity-85">
        Dead Silence. UB Hacking 2026. Original characters and art.
      </p>
    </Room>
  );
}
