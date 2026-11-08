import Room, { Heading } from "@/components/Room";
import { media } from "@/media";

const linkCls =
  "rounded-sm border-2 border-lamp px-5 py-3 text-lamp no-underline hover:border-bone hover:bg-bone hover:text-soil";

export default function Launchpad() {
  return (
    <Room id="launchpad">
      <Heading>Built in 24 hours.</Heading>
      <p className="max-w-[62ch]">
        UB Hacking 2026, theme &quot;Into the Hackosmos&quot;. Four builders: one
        on breath recognition and the hunter, three on the game and its look.
      </p>
      <p className="mt-4 mb-8 font-mono text-sm">
        Builder 1 / Builder 2 / Builder 3 / Builder 4
      </p>
      <div className="flex flex-wrap gap-3 font-mono">
        <a href={media.demoVideo.src ?? "#launchpad"} className={linkCls}>
          {media.demoVideo.label}
        </a>
        <a href={media.sourceUrl} className={linkCls}>
          Read the source
        </a>
      </div>
      <p className="mt-16 font-mono text-sm opacity-85">
        Dead Silence. UB Hacking 2026. Original characters and art.
      </p>
    </Room>
  );
}
