interface MetricTileProps {
  label: string;
  value: string;
  delta?: string;
  deltaPositive?: boolean | null;
  sub?: string;
}

export default function MetricTile({
  label,
  value,
  delta,
  deltaPositive,
  sub,
}: MetricTileProps) {
  const deltaClass =
    deltaPositive === true
      ? "text-emerald-400"
      : deltaPositive === false
      ? "text-red-400"
      : "text-zinc-500";

  return (
    <div className="card p-4 flex flex-col gap-1">
      <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
      <span className="font-heading text-2xl font-bold text-white leading-tight">
        {value}
      </span>
      {delta && (
        <span className={`text-xs ${deltaClass}`}>{delta}</span>
      )}
      {sub && <span className="text-xs text-zinc-600">{sub}</span>}
    </div>
  );
}
