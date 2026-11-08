import type { ReactNode } from "react";

// Chamfered steel plate with a 2 px rivet outline (clip-path hides borders).
// Only for interactive HUD: the breath demo and its keypad readout.
export function Plate({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className="chamfer bg-rivet p-[2px]">
      <div className={`chamfer bg-steel/90 p-5 [--cut:9px] sm:p-8 ${className}`}>
        {children}
      </div>
    </div>
  );
}

type Place = "left" | "right" | "low";

const placeCls: Record<Place, string> = {
  left: "items-center",
  right: "items-center md:justify-end",
  low: "items-end",
};

// One full-height compartment. Content floats over the scene, no box.
export default function Room({
  id,
  tag,
  place = "left",
  wide = false,
  children,
}: {
  id: string;
  tag: string;
  place?: Place;
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <section id={id} className="relative min-h-svh py-24">
      <div
        className={`relative mx-auto flex min-h-[calc(100svh-12rem)] w-full max-w-[1200px] px-4 ${placeCls[place]}`}
      >
        <div className={`hud-text w-full ${wide ? "max-w-[56rem]" : "max-w-[36rem]"}`}>
          <Callout>{tag}</Callout>
          {children}
        </div>
      </div>
    </section>
  );
}

// Small HUD label on a thin rivet line.
export function Callout({ children }: { children: ReactNode }) {
  return (
    <p className="mb-4 flex items-center gap-3 font-mono text-xs tracking-[0.25em] uppercase">
      <span aria-hidden="true" className="h-[2px] w-10 bg-rivet" />
      {children}
    </p>
  );
}

export function Heading({ children }: { children: ReactNode }) {
  return (
    <div className="mb-6">
      <h2 className="font-display text-[clamp(2.6rem,8vw,5rem)] leading-[0.9] font-extrabold tracking-tight uppercase">
        {children}
      </h2>
      <span aria-hidden="true" className="slash mt-3" />
    </div>
  );
}

// Body copy: narrow flat scrim for readability over the scene.
export function Copy({ children }: { children: ReactNode }) {
  return <div className="scrim max-w-[62ch] space-y-4 px-4 py-3">{children}</div>;
}

const btnBase =
  "inline-block border-2 px-5 py-3 font-mono uppercase tracking-wider no-underline active:shadow-[0_0_18px_rgb(255_90_31/0.6)]";
// Void on ember 6:1, void on ash 15:1, ember on void 6:1.
export const btnPrimary = `${btnBase} border-ember bg-ember text-void hover:border-ash hover:bg-ash hover:text-void`;
export const btnGhost = `${btnBase} border-ember bg-void/70 text-ember hover:border-ash hover:bg-ash hover:text-void`;
