import { healthColor } from "@/lib/format";

interface HealthScoreRingProps {
  score: number;
  rating: string;
  size?: number;
}

const RATING_STROKE: Record<string, string> = {
  excellent: "#34d399",
  good:      "#4ade80",
  fair:      "#facc15",
  poor:      "#fb923c",
  critical:  "#f87171",
};

export default function HealthScoreRing({
  score,
  rating,
  size = 96,
}: HealthScoreRingProps) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const stroke = RATING_STROKE[rating] ?? "#9ca3af";
  const cx = size / 2;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        {/* Track */}
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke="#222"
          strokeWidth={8}
        />
        {/* Progress */}
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="none"
          stroke={stroke}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circ}`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
        {/* Score text — unrotate it */}
        <text
          x={cx}
          y={cx + 1}
          textAnchor="middle"
          dominantBaseline="middle"
          style={{
            transform: `rotate(90deg) translate(0, -${size}px)`,
            transformOrigin: `${cx}px ${cx}px`,
            fill: stroke,
            fontSize: size / 3.8,
            fontWeight: 700,
            fontFamily: "Space Grotesk, sans-serif",
          }}
        >
          {score}
        </text>
      </svg>
      <span className={`text-xs font-semibold capitalize ${healthColor(rating)}`}>
        {rating}
      </span>
    </div>
  );
}
