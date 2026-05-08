import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { MONTHS } from "@/lib/format";

interface DataPoint {
  period_month: number;
  period_year: number;
  revenue: number;
  gross_profit: number;
}

interface TrendChartProps {
  data: DataPoint[];
}

function fmtR(v: number): string {
  if (v >= 1_000_000) return `R${(v / 1_000_000).toFixed(1)}m`;
  if (v >= 1_000) return `R${(v / 1_000).toFixed(0)}k`;
  return `R${v.toFixed(0)}`;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#1a1a1a] border border-[#333] rounded-lg p-3 text-xs shadow-xl">
      <p className="text-zinc-400 mb-1.5 font-medium">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="leading-5">
          {p.name}: {fmtR(p.value)}
        </p>
      ))}
    </div>
  );
};

export default function TrendChart({ data }: TrendChartProps) {
  const chartData = data.map((d) => ({
    label: `${MONTHS[d.period_month]} ${String(d.period_year).slice(2)}`,
    Revenue: d.revenue,
    "Gross Profit": d.gross_profit,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gradRev" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradGP" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: "#6b7280", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={fmtR}
          tick={{ fill: "#6b7280", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="Revenue"
          stroke="#2DD4BF"
          strokeWidth={2}
          fill="url(#gradRev)"
          dot={false}
          activeDot={{ r: 4, fill: "#2DD4BF" }}
        />
        <Area
          type="monotone"
          dataKey="Gross Profit"
          stroke="#06B6D4"
          strokeWidth={2}
          fill="url(#gradGP)"
          dot={false}
          activeDot={{ r: 4, fill: "#06B6D4" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
