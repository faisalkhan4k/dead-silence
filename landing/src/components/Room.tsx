import type { ReactNode } from "react";

// Chamfered steel plate with a 2 px rivet outline (clip-path hides borders).
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

// One full-height compartment. Text sits low and left on a plate.
export default function Room({
  id,
  className = "",
  children,
}: {
  id: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      className={`relative flex min-h-svh items-end py-24 ${className}`}
    >
      <div className="relative mx-auto w-full max-w-[1040px] px-4">
        <Plate>{children}</Plate>
      </div>
    </section>
  );
}

export function Heading({ children }: { children: ReactNode }) {
  return (
    <div className="mb-6">
      <h2 className="font-display text-[clamp(2.2rem,6vw,3.6rem)] leading-[0.95] font-extrabold tracking-tight uppercase">
        {children}
      </h2>
      <span aria-hidden="true" className="slash mt-3" />
    </div>
  );
}

export const btnCls =
  "inline-block border-2 border-ember px-5 py-3 font-mono uppercase tracking-wider no-underline active:shadow-[0_0_18px_rgb(255_90_31/0.6)]";
