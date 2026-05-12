import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyAgentStatus, getReport, getReports, getRevenueTrends, requestCompanySync } from "@/lib/api";
import { formatCurrency, formatPct, formatPeriod, healthColor } from "@/lib/format";
import type { CompanyAgentStatus, Report, ReportListItem } from "@/lib/types";
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
  const [agentStatus, setAgentStatus] = useState<CompanyAgentStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshAgent = () => {
    getMyAgentStatus().then((r) => setAgentStatus(r.data)).catch(() => {});
  };

  useEffect(() => {
    Promise.all([getReports(), getRevenueTrends(), getMyAgentStatus()])
      .then(async ([listRes, trendRes, agentRes]) => {
        setItems(listRes.data);
        setTrends(trendRes.data);
        setAgentStatus(agentRes.data);
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
        {agentStatus?.has_agent ? (
          <>
            <p className="text-zinc-400 text-sm max-w-md text-center">
              Your Evolution agent is installed. Your first report will be generated
              automatically on the 1st of next month, or you can request a sync now.
            </p>
            <EvolutionAgentCard status={agentStatus} onSynced={refreshAgent} />
          </>
        ) : (
          <>
            <p className="text-zinc-400 text-sm max-w-md text-center">
              No reports yet. Upload your Pastel Partner exports to generate your first
              financial report.
            </p>
            <Link to="/upload" className="btn-primary mt-2">
              Upload your first files →
            </Link>
          </>
        )}
      </div>
    );
  }

  const m = latest.metrics;

  return (
    <div className="space-y-8">
      {/* Evolution agent status — only visible for Evolution companies */}
      {agentStatus?.has_agent && (
        <EvolutionAgentCard status={agentStatus} onSynced={refreshAgent} />
      )}

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

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function EvolutionAgentCard({
  status,
  onSynced,
}: {
  status: CompanyAgentStatus;
  onSynced: () => void;
}) {
  const now = new Date();
  const defaultMonth = now.getMonth() === 0 ? 12 : now.getMonth();
  const defaultYear  = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();

  const [open, setOpen]       = useState(false);
  const [month, setMonth]     = useState(defaultMonth);
  const [year, setYear]       = useState(defaultYear);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<"ok" | "error" | null>(null);

  const handleSync = async () => {
    setLoading(true);
    setResult(null);
    try {
      await requestCompanySync(month, year);
      setResult("ok");
      setOpen(false);
      onSynced();
      setTimeout(() => setResult(null), 8000);
    } catch {
      setResult("error");
    } finally {
      setLoading(false);
    }
  };

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const years  = [now.getFullYear() - 1, now.getFullYear()];
  const hasPending = !!(status.pending_sync_month && status.pending_sync_year);

  return (
    <div className="rounded-xl border border-white/8 bg-zinc-900/60 p-4 space-y-3">
      {/* Status row */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Connection */}
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full shrink-0 ${status.connected ? "bg-emerald-400 animate-pulse" : "bg-red-500"}`} />
          <span className={`text-xs font-medium ${status.connected ? "text-emerald-400" : "text-red-400"}`}>
            {status.connected ? "Agent connected" : "Agent offline"}
          </span>
        </div>

        <span className="text-zinc-700 text-xs hidden sm:block">·</span>

        {/* SQL status */}
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
            status.sql_ok === true  ? "bg-emerald-400" :
            status.sql_ok === false ? "bg-red-500" : "bg-zinc-600"
          }`} />
          <span className={`text-xs ${
            status.sql_ok === true  ? "text-zinc-400" :
            status.sql_ok === false ? "text-red-400" : "text-zinc-600"
          }`}>
            {status.sql_ok === true  ? "Pastel connected" :
             status.sql_ok === false ? "Pastel connection error" :
             "Pastel status unknown"}
          </span>
        </div>

        <span className="text-zinc-700 text-xs hidden sm:block">·</span>

        {/* Last sync */}
        <span className="text-xs text-zinc-500">
          {status.last_sync_status === "accepted" && status.last_sync_at
            ? `Last sync ${timeAgo(status.last_sync_at)}`
            : status.last_sync_at
            ? `Last attempt ${timeAgo(status.last_sync_at)} — ${status.last_sync_status}`
            : "Not yet synced"}
        </span>

        {/* Pending badge */}
        {hasPending && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-950 border border-amber-800 text-amber-300">
            Sync queued for {status.pending_sync_month}/{status.pending_sync_year}
          </span>
        )}

        {/* Force sync button */}
        <button
          onClick={() => { setOpen((o) => !o); setResult(null); }}
          className="ml-auto text-xs px-3 py-1.5 rounded border border-white/10 text-zinc-400 hover:text-white hover:border-teal-500/40 hover:bg-teal-500/10 transition-colors"
        >
          {open ? "Cancel" : "↺ Request Sync"}
        </button>
      </div>

      {/* Inline sync form */}
      {open && (
        <div className="flex items-center gap-2 flex-wrap pt-1 border-t border-white/5">
          <span className="text-xs text-zinc-500">Sync period:</span>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="text-xs bg-zinc-800 border border-white/10 rounded px-2 py-1 text-zinc-200"
          >
            {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="text-xs bg-zinc-800 border border-white/10 rounded px-2 py-1 text-zinc-200"
          >
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
          <button
            onClick={handleSync}
            disabled={loading}
            className="text-xs px-3 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-white font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? "Requesting…" : "Request Sync"}
          </button>
          <span className="text-xs text-zinc-600">Agent will run within 5 min</span>
        </div>
      )}

      {/* Feedback */}
      {result && (
        <p className={`text-xs ${result === "ok" ? "text-emerald-400" : "text-red-400"}`}>
          {result === "ok"
            ? `Sync requested for ${MONTHS[month - 1]} ${year}. Your agent will run it within 5 minutes.`
            : "Could not queue sync. Check that your agent is online and try again."}
        </p>
      )}
    </div>
  );
}

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
