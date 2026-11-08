export default function Exterior() {
  return (
    <header
      id="exterior"
      className="relative flex min-h-svh items-end overflow-hidden"
    >
      <svg
        viewBox="0 0 1200 700"
        preserveAspectRatio="xMidYMax slice"
        aria-hidden="true"
        className="absolute inset-0 h-full w-full"
      >
        <g fill="#C8643B" opacity=".18">
          <circle cx="180" cy="130" r="2" />
          <circle cx="420" cy="70" r="1.5" />
          <circle cx="860" cy="110" r="2" />
          <circle cx="1040" cy="60" r="1.5" />
          <circle cx="640" cy="170" r="1.5" />
        </g>
        <path d="M0 520 Q200 470 420 505 T820 490 T1200 510 V700 H0Z" fill="#3B2A22" />
        <path d="M0 580 Q300 540 600 575 T1200 565 V700 H0Z" fill="#2A1B15" />
        <g id="house" transform="translate(830,300)">
          <g fill="none" stroke="#5FA8A0" strokeWidth="3">
            <circle className="ring" cx="80" cy="120" r="60" />
            <circle className="ring" cx="80" cy="120" r="60" />
            <circle className="ring" cx="80" cy="120" r="60" />
          </g>
          <path d="M-10 190 V90 L80 20 L170 90 V190Z" fill="#140E0C" stroke="#E8DCC4" strokeWidth="2.5" strokeLinejoin="round" />
          <path d="M-24 92 L80 6 L184 92" fill="none" stroke="#C8643B" strokeWidth="6" strokeLinecap="round" />
          <rect x="55" y="130" width="50" height="60" fill="#2A1B15" stroke="#E8DCC4" strokeWidth="2" />
          <rect className="win" x="18" y="98" width="30" height="28" fill="#E7B65C" />
          <rect x="120" y="98" width="30" height="28" fill="#2A1B15" stroke="#E8DCC4" strokeWidth="2" />
          <rect x="128" y="-10" width="14" height="40" fill="#2A1B15" stroke="#E8DCC4" strokeWidth="2" />
          <path d="M-60 190 H230" stroke="#C8643B" strokeWidth="3" />
        </g>
      </svg>
      <div className="relative mx-auto w-full max-w-[1040px] px-4 pt-32 pb-[12vh]">
        <div className="border-l border-plank pl-5 sm:pl-8">
          <h1 className="text-[clamp(3.25rem,12vw,8rem)] leading-[0.95] font-bold tracking-[-0.03em] [font-variation-settings:'opsz'_144]">
            Dead Silence
          </h1>
          <p className="mt-3 mb-8 text-[clamp(1.2rem,3vw,1.7rem)] leading-tight text-lamp italic">
            Don&apos;t breathe too loud.
          </p>
          <div className="flex flex-wrap gap-3 font-mono">
            <a
              href="#hall"
              className="rounded-sm border-2 border-lamp bg-lamp px-5 py-3 text-soil no-underline hover:border-bone hover:bg-bone"
            >
              Try the breath code
            </a>
            <a
              href="#launchpad"
              className="rounded-sm border-2 border-lamp px-5 py-3 text-lamp no-underline hover:border-bone hover:bg-bone hover:text-soil"
            >
              Watch the demo
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
