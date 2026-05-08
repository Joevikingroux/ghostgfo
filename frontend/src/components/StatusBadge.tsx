type StatusBadgeProps = {
  status: string;
};

const STATUS_STYLES: Record<string, string> = {
  pending:    "bg-zinc-800 text-zinc-400",
  processing: "bg-blue-950 text-blue-300",
  complete:   "bg-emerald-950 text-emerald-400",
  failed:     "bg-red-950 text-red-400",
  excellent:  "bg-emerald-950 text-emerald-300",
  good:       "bg-green-950 text-green-400",
  fair:       "bg-yellow-950 text-yellow-400",
  poor:       "bg-orange-950 text-orange-400",
  critical:   "bg-red-950 text-red-400",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const cls = STATUS_STYLES[status.toLowerCase()] ?? "bg-zinc-800 text-zinc-400";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
