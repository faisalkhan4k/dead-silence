import type { ReactNode } from "react";

// One full-height room. Text sits low and left behind a thin plank rule.
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
        <div className="border-l border-plank pl-5 sm:pl-8">{children}</div>
      </div>
    </section>
  );
}

export function Heading({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-6 text-[clamp(1.8rem,4vw,2.6rem)] leading-[1.1] font-bold tracking-tight">
      {children}
    </h2>
  );
}
