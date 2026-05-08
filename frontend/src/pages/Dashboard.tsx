import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getReports, getReport, getRevenueTrends } from "@/lib/api";
import { formatCurrency, formatPct, formatPeriod, healthColor } from "@/lib/format";
import type { Report, ReportListItem } from "@/lib/types";
import MetricTile from "@/components/MetricTile";
import StatusBadge from "@/components/StatusBadge";
import TrendChart from "@/components/TrendChart";
import HealthScoreRing from "@/components/HealthScoreRing";

interface TrendPoint {
  period_month: number;
  period_year: number;
  revenue: number;
  gross_profit: number;
}

export default function DashboardPage() {
  const [items, setItems] = useState<ReportListItem[]>([]);
  const [latest, setLatest] = useState<Report | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getReports(), getRevenueTrends()])
      .then(async ([listRes, trendRes]) => {
        setItems(listRes.data);
        setTrends(trendRes.data);
        if (listRes.data.length > 0) {
          const full = await getReport(listRes.data[0].id);
          setLatest(full.data);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-zinc-500 text-sm">Loading…</div>;
  }

  if (!latest) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <h2 className="font-heading text-2xl font-bold">Welcome to Ghost CFO</h2>
        <p className="text-zinc-400 text-sm max-w-md text-center">
          No reports yet. Upload your Pastel Partner exports to generate your first
          financial report.
        </p>
        <Link to="/upload" className="btn-primary mt-2">
          Upload your first files →
        </Link>
      </div>
    );
  }

  const m = latest.metrics;

  return (
    <div className="space-y-8">
      {/* Header row — title + health score ring */}
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <h1 className="font-heading text-2xl font-bold">{m.company_name}</h1>
          <p className="text-zinc-400 text-sm mt-0.5">
            {formatPeriod(m.period_month, m.period_year)} &nbsp;·&nbsp; Latest report
          </p>

          {/* Flags */}
          {m.health_flags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {m.health_flags.map((flag, i) => (
                <span
                  key={i}
                  className="text-xs bg-amber-950 border border-amber-800 text-amber-300 px-3 py-1 rounded-full"
                >
                  ⚑ {flag}
                </span>
              ))}
            </div>
          )}
        </div>

        <HealthScoreRing score={m.health_score} rating={m.health_rating} size={96} />
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricTile
          label="Revenue"
          value={formatCurrency(m.revenue_current_month)}
          delta={`${formatPct(m.revenue_change_pct, true)} vs last month`}
          deltaPositive={m.revenue_change_pct >= 0}
        />
        <MetricTile
          label="Gross Margin"
          value={formatPct(m.gross_margin_pct)}
          delta={m.gross_margin_trend}
          deltaPositive={null}
        />
        <MetricTile
          label="Cash Balance"
          value={formatCurrency(m.cash_balance)}
          delta={`${m.cash_runway_weeks.toFixed(1)} weeks runway`}
          deltaPositive={m.cash_runway_weeks >= 12}
        />
        <MetricTile
          label="Debtors"
          value={formatCurrency(m.debtors_total)}
          delta={`${m.overdue_invoices_count} overdue invoice${m.overdue_invoices_count !== 1 ? "s" : ""}`}
          deltaPositive={m.overdue_invoices_count === 0}
        />
        {m.payroll_gross_total > 0 && (
          <>
            <MetricTile
              label="Payroll (gross)"
              value={formatCurrency(m.payroll_gross_total)}
              delta={`${formatPct(m.payroll_change_pct, true)} vs last month`}
              deltaPositive={m.payroll_change_pct <= 5}
            />
            <MetricTile
              label="True Employer Cost"
              value={formatCurrency(m.payroll_true_employer_cost)}
              sub="incl. UIF & SDL"
            />
            <MetricTile
              label="Payroll % of Revenue"
              value={formatPct(m.payroll_pct_of_revenue)}
              delta={m.payroll_pct_of_revenue > 40 ? "HIGH — review" : "within range"}
              deltaPositive={m.payroll_pct_of_revenue <= 40}
            />
            <MetricTile
              label="Leave Liability"
              value={formatCurrency(m.leave_liability_rand)}
              delta={`${m.leave_liability_weeks_payroll.toFixed(1)} weeks of payroll`}
              deltaPositive={m.leave_liability_weeks_payroll < 4}
            />
          </>
        )}
      </div>

      {/* Revenue trend chart */}
      {trends.length > 1 && (
        <div className="card p-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-4">
            Revenue Trend (last {trends.length} months)
          </h2>
          <TrendChart data={trends} />
          <div className="flex gap-5 mt-3 justify-end">
            <LegendDot color="#2DD4BF" label="Revenue" />
            <LegendDot color="#06B6D4" label="Gross Profit" />
          </div>
        </div>
      )}

      {/* Debtor aging bar */}
      {m.debtors_total > 0 && (
        <div className="card p-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-4">
            Debtor Aging
          </h2>
          <DebtorAgingBar
            current={m.debtors_current}
            d3060={m.debtors_30_60_days}
            d6190={m.debtors_61_90_days}
            over90={m.debtors_over_90_days}
            total={m.debtors_total}
          />
          {m.worst_offenders.length > 0 && (
            <table className="w-full text-sm mt-4">
              <thead>
                <tr className="text-xs text-zinc-500 uppercase border-b border-surface-border">
                  <th className="text-left pb-2">Customer</th>
                  <th className="text-right pb-2">Overdue amount</th>
                  <th className="text-right pb-2">Age</th>
                </tr>
              </thead>
              <tbody>
                {m.worst_offenders.map((d, i) => (
                  <tr key={i} className="border-b border-surface-border last:border-0">
                    <td className="py-2.5 text-zinc-300">{d.name}</td>
                    <td className="py-2.5 text-right font-mono text-sm">
                      {formatCurrency(d.overdue_value)}
                    </td>
                    <td className="py-2.5 text-right">
                      <StatusBadge status={d.worst_bucket === "90+" ? "critical" : "poor"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Executive summary */}
      {latest.narrative_summary && (
        <div className="card p-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-3">
            Executive Summary
          </h2>
          <p className="text-sm text-zinc-300 leading-relaxed">{latest.narrative_summary}</p>
        </div>
      )}

      {/* Recommended actions */}
      {latest.narrative_actions && (
        <div className="card p-5 border-l-2 border-brand-teal">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-3">
            Recommended Actions
          </h2>
          <pre className="text-sm text-zinc-300 whitespace-pre-line font-sans leading-relaxed">
            {latest.narrative_actions}
          </pre>
        </div>
      )}

      {/* PDF link */}
      {items[0]?.pdf_ready && (
        <div className="flex justify-end">
          <Link
            to="/reports"
            className="btn-primary text-sm"
          >
            View full report &amp; download PDF →
          </Link>
        </div>
      )}

      {/* Previous reports */}
      {items.length > 1 && (
        <div>
          <h2 className="font-heading text-sm font-bold text-zinc-400 uppercase tracking-wider mb-3">
            Previous Reports
          </h2>
          <div className="space-y-2">
            {items.slice(1).map((r) => (
              <Link
                key={r.id}
                to="/reports"
                className="card p-4 flex items-center justify-between hover:border-zinc-600 transition-colors"
              >
                <span className="text-sm">
                  {formatPeriod(r.period_month, r.period_year)}
                </span>
                <div className="flex items-center gap-3">
                  {r.health_rating && (
                    <StatusBadge status={r.health_rating} />
                  )}
                  <span className="text-xs text-zinc-500">
                    {r.pdf_ready ? "PDF ready" : "Generating…"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
      <span className="text-xs text-zinc-500">{label}</span>
    </div>
  );
}

function DebtorAgingBar({
  current, d3060, d6190, over90, total,
}: {
  current: number; d3060: number; d6190: number; over90: number; total: number;
}) {
  const pct = (v: number) => total > 0 ? (v / total) * 100 : 0;
  const segments = [
    { label: "Current", value: current, color: "#059669" },
    { label: "30–60 days", value: d3060, color: "#d97706" },
    { label: "61–90 days", value: d6190, color: "#ea580c" },
    { label: "90+ days", value: over90, color: "#dc2626" },
  ].filter((s) => s.value > 0);

  return (
    <div className="space-y-3">
      <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
        {segments.map((s) => (
          <div
            key={s.label}
            style={{ width: `${pct(s.value)}%`, background: s.color }}
            title={`${s.label}: R${Math.round(s.value).toLocaleString("en-ZA")}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-4">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5">
            <span
              className="inline-block w-2.5 h-2.5 rounded-sm shrink-0"
              style={{ background: s.color }}
            />
            <span className="text-xs text-zinc-400">{s.label}</span>
            <span className="text-xs font-mono text-zinc-300">
              {formatCurrency(s.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
