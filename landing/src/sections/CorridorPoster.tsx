// Static ship corridor: door frames receding to one point, ember strips on
// each frame, a red light under the far door. Hidden when the 3D scene runs.
const VP = { x: 600, y: 330 };
const SCALES = [1, 0.68, 0.46, 0.31, 0.21];

function frame(s: number) {
  const w = 980 * s;
  const h = 660 * s;
  return { x: VP.x - w / 2, y: VP.y - h / 2, w, h, t: 34 * s };
}

export default function CorridorPoster() {
  const far = frame(SCALES[SCALES.length - 1]);
  return (
    <svg
      viewBox="0 0 1200 700"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      className="absolute inset-0 h-full w-full"
    >
      <rect width="1200" height="700" fill="#0A0A0C" />
      {[
        [0, 700],
        [1200, 700],
        [0, 0],
        [1200, 0],
      ].map(([x, y]) => (
        <line key={`${x}-${y}`} x1={x} y1={y} x2={VP.x} y2={VP.y} stroke="#24262C" strokeWidth="2" />
      ))}
      {SCALES.map((s) => {
        const f = frame(s);
        return (
          <g key={s}>
            <path
              d={`M${f.x} ${f.y}h${f.w}v${f.h}h${-f.w}Z M${f.x + f.t} ${f.y + f.t}v${f.h - f.t}h${f.w - 2 * f.t}v${-(f.h - f.t)}Z`}
              fill="#16171B"
              fillRule="evenodd"
              stroke="#3A3D45"
              strokeWidth={Math.max(1, 2 * s)}
            />
            <rect x={f.x + f.t * 0.35} y={f.y + f.t * 1.4} width={4 * s + 1} height={f.h * 0.55} fill="#FF5A1F" />
            <rect x={f.x + f.w - f.t * 0.35 - (4 * s + 1)} y={f.y + f.t * 1.4} width={4 * s + 1} height={f.h * 0.55} fill="#FF5A1F" />
          </g>
        );
      })}
      <rect x={far.x + far.t} y={far.y + far.h - 6} width={far.w - 2 * far.t} height="4" fill="#E3182D" opacity=".8" />
    </svg>
  );
}
