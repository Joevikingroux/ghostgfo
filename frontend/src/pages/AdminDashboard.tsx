import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { forceSyncAgent, getAdminOverview } from "@/lib/api";
import { formatPeriod } from "@/lib/format";
import type { AdminClientCard, AdminOverview, SystemStatus } from "@/lib/types";

// ─── Helpers ────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const RATING_STROKE: Record<string, string> = {
  excellent: "text-emerald-400",
  good:      "text-teal-400",
  fair:      "text-amber-400",
  poor:      "text-orange-400",
  critical:  "text-red-500",
};

const RATING_TEXT: Record<string, string> = {
  excellent: "text-emerald-400",
  good:      "text-teal-400",
  fair:      "text-amber-400",
  poor:      "text-orange-400",
  critical:  "text-red-400",
};

const PLAN_STYLE: Record<string, string> = {
  starter:      "bg-zinc-800 border-zinc-700 text-zinc-300",
  professional: "bg-teal-950 border-teal-800 text-teal-300",
  premium:      "bg-violet-950 border-violet-800 text-violet-300",
};

const HEALTH_BAR_COLOR: Record<string, string> = {
  excellent: "bg-emerald-500",
  good:      "bg-teal-500",
  fair:      "bg-amber-500",
  poor:      "bg-orange-500",
  critical:  "bg-red-500",
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function HealthRing({ score, rating }: { score: number | null; rating: string | null }) {
  if (score == null) {
    return (
      <div className="w-11 h-11 rounded-full bg-zinc-800 flex items-center justify-center text-xs text-zinc-600 shrink-0">
        —
      </div>
    );
  }
  const r = 17;
  const circ = 2 * Math.PI * r;
  const strokeClass = RATING_STROKE[rating ?? ""] ?? "text-zinc-500";

  return (
    <div className="relative w-11 h-11 shrink-0">
      <svg viewBox="0 0 40 40" className="w-full h-full -rotate-90">
        <circle cx="20" cy="20" r={r} fill="none" strokeWidth="3.5"
          stroke="currentColor" className="text-zinc-800" />
        <circle cx="20" cy="20" r={r} fill="none" strokeWidth="3.5"
          stroke="currentColor" className={strokeClass} strokeLinecap="round"
          strokeDasharray={`${(score / 100) * circ} ${circ}`} />
      </svg>
      <span className={`absolute inset-0 flex items-center justify-center text-[11px] font-bold ${strokeClass}`}>
        {score}
      </span>
    </div>
  );
}

function StatTile({
  label, value, sub, accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "teal" | "amber" | "violet";
}) {
  const gradients: Record<string, string> = {
    teal:   "bg-gradient-to-br from-teal-500/15 to-cyan-500/5 border-teal-500/25",
    amber:  "bg-gradient-to-br from-amber-500/15 to-orange-500/5 border-amber-500/25",
    violet: "bg-gradient-to-br from-violet-500/15 to-purple-500/5 border-violet-500/25",
  };
  const valueColors: Record<string, string> = {
    teal:   "brand-text",
    amber:  "text-amber-400",
    violet: "text-violet-400",
  };

  return (
    <div className={`rounded-xl border p-5 ${accent ? gradients[accent] : "bg-zinc-900 border-white/8"}`}>
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1.5">{label}</p>
      <p className={`font-heading text-3xl font-bold ${accent ? valueColors[accent] : "text-white"}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-zinc-500 mt-1.5">{sub}</p>}
    </div>
  );
}

function SystemStatusBar() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [age, setAge] = useState(0);

  const fetchStatus = useCallback(() => {
    axios
      .get<SystemStatus>("/api/agent/system-status", { withCredentials: true })
      .then((r) => { setStatus(r.data); setAge(0); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchStatus();
    const poll = setInterval(fetchStatus, 30_000);
    const tick = setInterval(() => setAge((a) => a + 1), 1_000);
    return () => { clearInterval(poll); clearInterval(tick); };
  }, [fetchStatus]);

  const LABELS: Partial<Record<keyof SystemStatus, string>> = {
    database:   "Database",
    redis:      "Redis",
    payfast:    "PayFast",
    resend:     "Email",
    openrouter: "LLM",
    agent_key:  "Agent Key",
  };

  if (!status) return null;

  const allOk = (Object.values(status) as { ok: boolean }[]).every((c) => c.ok);

  return (
    <div className="rounded-xl border border-white/8 bg-zinc-900/60 px-5 py-3 flex items-center gap-5 flex-wrap">
      <div className="flex items-center gap-2 shrink-0">
        <span className={`inline-block w-2 h-2 rounded-full animate-pulse ${allOk ? "bg-emerald-400" : "bg-red-400"}`} />
        <span className="text-xs font-medium text-zinc-300">Services</span>
        <span className="text-xs text-zinc-600">· {age}s ago</span>
      </div>
      <div className="h-4 w-px bg-white/10 hidden sm:block" />
      <div className="flex items-center gap-5 flex-wrap">
        {(Object.keys(LABELS) as (keyof SystemStatus)[]).map((k) => (
          <div key={k} className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${status[k].ok ? "bg-emerald-400" : "bg-red-400"}`} />
            <span className={`text-xs ${status[k].ok ? "text-zinc-400" : "text-red-400 font-medium"}`}>
              {LABELS[k]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function HealthDistributionBar({ distribution }: { distribution: Record<string, number> }) {
  const order = ["excellent", "good", "fair", "poor", "critical"];
  const total = Object.values(distribution).reduce((s, n) => s + n, 0) || 1;
  const hasData = Object.values(distribution).some((n) => n > 0);

  if (!hasData) return <p className="text-xs text-zinc-600">No reports yet.</p>;

  return (
    <div className="space-y-2.5">
      {order
        .filter((r) => (distribution[r] ?? 0) > 0)
        .map((r) => {
          const n = distribution[r] ?? 0;
          const pct = (n / total) * 100;
          return (
            <div key={r} className="flex items-center gap-3">
              <span className="text-xs text-zinc-400 w-16 capitalize">{r}</span>
              <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${HEALTH_BAR_COLOR[r]}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-xs text-zinc-500 w-3 text-right font-medium">{n}</span>
            </div>
          );
        })}
    </div>
  );
}

function ClientCard({ c }: { c: AdminClientCard }) {
  return (
    <div className="rounded-xl border border-white/8 bg-zinc-900 p-4 hover:border-white/15 transition-colors">
      <div className="flex items-start gap-3">
        <HealthRing score={c.health_score} rating={c.health_rating} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-white truncate leading-tight">{c.name}</span>
            {c.payroll_pending && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-950 border border-amber-800 text-amber-300 shrink-0">
                Payroll
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
            <span className={`text-[10px] px-1.5 py-0.5 rounded border capitalize ${PLAN_STYLE[c.plan] ?? PLAN_STYLE.starter}`}>
              {c.plan}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
              c.data_source === "evolution"
                ? "bg-emerald-950 text-emerald-400"
                : "bg-blue-950 text-blue-400"
            }`}>
              {c.data_source === "evolution" ? "Auto" : "Upload"}
            </span>
            {c.health_rating && (
              <span className={`text-[10px] capitalize ${RATING_TEXT[c.health_rating] ?? "text-zinc-400"}`}>
                {c.health_rating}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-zinc-500">
        <span>
          {c.last_report_month
            ? `${formatPeriod(c.last_report_month, c.last_report_year!)}`
            : "No report yet"}
        </span>
        {c.data_source === "evolution" && (
          c.agent_last_heartbeat
            ? (() => {
                const online = Date.now() - new Date(c.agent_last_heartbeat).getTime() <= 12 * 60 * 1000;
                return (
                  <span className={`flex items-center gap-1 ${online ? "text-emerald-500" : "text-red-400"}`}>
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${online ? "bg-emerald-400 animate-pulse" : "bg-red-500"}`} />
                    {online ? "Connected" : `Offline · ${timeAgo(c.agent_last_heartbeat)}`}
                  </span>
                );
              })()
            : <span className="text-zinc-700">Awaiting first heartbeat</span>
        )}
      </div>
    </div>
  );
}

// ─── Agent status panel ──────────────────────────────────────────────────────

type AgentConnectionStatus = "online" | "offline" | "inactive";

// Agent is "online" if it sent a heartbeat in the last 12 minutes
// (5-min interval + 7-min grace for slow networks / sleep)
const HEARTBEAT_GRACE_MS = 12 * 60 * 1000;

function agentConnectionStatus(c: AdminClientCard): AgentConnectionStatus {
  if (!c.agent_active) return "inactive";
  if (!c.agent_last_heartbeat) return "offline";
  const age = Date.now() - new Date(c.agent_last_heartbeat).getTime();
  return age <= HEARTBEAT_GRACE_MS ? "online" : "offline";
}

const CONN_DOT: Record<AgentConnectionStatus, string> = {
  online:   "bg-emerald-400",
  offline:  "bg-red-500",
  inactive: "bg-zinc-700",
};

const CONN_LABEL: Record<AgentConnectionStatus, string> = {
  online:   "Connected",
  offline:  "Offline",
  inactive: "Inactive",
};

const CONN_TEXT: Record<AgentConnectionStatus, string> = {
  online:   "text-emerald-400",
  offline:  "text-red-400",
  inactive: "text-zinc-600",
};

function AgentStatusPanel({
  clients,
  onSyncQueued,
}: {
  clients: AdminClientCard[];
  onSyncQueued: () => void;
}) {
  const agentClients = clients.filter((c) => c.data_source === "evolution" || c.agent_active);
  if (agentClients.length === 0) return null;

  const statuses = agentClients.map((c) => ({ c, status: agentConnectionStatus(c) }));
  const onlineCount  = statuses.filter((s) => s.status === "online").length;
  const problemCount = statuses.filter((s) => s.status === "offline").length;

  // Force-sync state
  const now = new Date();
  const defaultMonth = now.getMonth() === 0 ? 12 : now.getMonth();
  const defaultYear  = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();

  const [openSyncId, setOpenSyncId] = useState<string | null>(null);
  const [syncMonth, setSyncMonth]   = useState(defaultMonth);
  const [syncYear, setSyncYear]     = useState(defaultYear);
  const [syncing, setSyncing]       = useState(false);
  const [syncResult, setSyncResult] = useState<{ id: string; ok: boolean } | null>(null);

  const handleForceSync = async (agentId: string) => {
    if (!agentId) return;
    setSyncing(true);
    setSyncResult(null);
    try {
      await forceSyncAgent(agentId, syncMonth, syncYear);
      setSyncResult({ id: agentId, ok: true });
      setOpenSyncId(null);
      onSyncQueued();
      setTimeout(() => setSyncResult(null), 8000);
    } catch {
      setSyncResult({ id: agentId, ok: false });
    } finally {
      setSyncing(false);
    }
  };

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const years  = [now.getFullYear() - 1, now.getFullYear()];

  return (
    <div className="card p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full shrink-0 ${problemCount > 0 ? "bg-red-500 animate-pulse" : "bg-emerald-400 animate-pulse"}`} />
          <h3 className="font-heading font-bold text-sm text-white">Evolution Agents</h3>
          <span className="text-xs text-zinc-600">· live</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-emerald-400 font-medium">{onlineCount} online</span>
          <span className="text-zinc-600">/</span>
          <span className="text-zinc-400">{agentClients.length} total</span>
          {problemCount > 0 && (
            <span className="ml-1 px-2 py-0.5 rounded-full bg-red-950 border border-red-800 text-red-300 font-medium">
              {problemCount} offline
            </span>
          )}
        </div>
      </div>

      {/* Agent rows */}
      <div className="divide-y divide-white/5">
        {statuses.map(({ c, status }) => {
          const hasPending = !!(c.agent_pending_sync_month && c.agent_pending_sync_year);
          const isOpen = openSyncId === c.id;

          return (
            <div key={c.id} className="py-3 first:pt-0 last:pb-0 space-y-2">
              {/* Main row */}
              <div className="flex items-center gap-3 flex-wrap">
                {/* Connection dot */}
                <span className={`w-2 h-2 rounded-full shrink-0 ${CONN_DOT[status]} ${status === "online" ? "animate-pulse" : ""}`} />

                {/* Company + server / db */}
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium text-zinc-200">{c.name}</span>
                  {c.agent_server_name && (
                    <span className="text-xs text-zinc-500 ml-2">{c.agent_server_name}</span>
                  )}
                  {c.agent_db_name && (
                    <span className="text-xs text-zinc-600 ml-1">/ {c.agent_db_name}</span>
                  )}
                </div>

                {/* Connection status */}
                <span className={`text-xs font-medium shrink-0 ${CONN_TEXT[status]}`}>
                  {CONN_LABEL[status]}
                </span>

                {/* SQL status */}
                <span className={`flex items-center gap-1 text-xs shrink-0 ${
                  c.agent_sql_ok === true  ? "text-emerald-400" :
                  c.agent_sql_ok === false ? "text-red-400" :
                  "text-zinc-600"
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    c.agent_sql_ok === true  ? "bg-emerald-400" :
                    c.agent_sql_ok === false ? "bg-red-500" :
                    "bg-zinc-700"
                  }`} />
                  {c.agent_sql_ok === true  ? "SQL OK" :
                   c.agent_sql_ok === false ? "SQL Error" :
                   "SQL Unknown"}
                </span>

                {/* Last heartbeat */}
                <span className="text-xs text-zinc-600 shrink-0 hidden sm:block">
                  {c.agent_last_heartbeat ? `Ping ${timeAgo(c.agent_last_heartbeat)}` : "Never connected"}
                </span>

                {/* Last sync */}
                <span className="text-xs text-zinc-500 shrink-0 hidden md:block">
                  {c.agent_status === "accepted" && c.agent_last_sync
                    ? `Synced ${timeAgo(c.agent_last_sync)}`
                    : c.agent_last_sync
                    ? `Sync ${c.agent_status ?? "unknown"} ${timeAgo(c.agent_last_sync)}`
                    : "Not yet synced"}
                </span>

                {/* Pending badge */}
                {hasPending && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-950 border border-amber-800 text-amber-300 shrink-0">
                    Sync pending {c.agent_pending_sync_month}/{c.agent_pending_sync_year}
                  </span>
                )}

                {/* Force sync toggle */}
                {c.agent_id && (
                  <button
                    onClick={() => {
                      if (isOpen) { setOpenSyncId(null); return; }
                      setSyncMonth(defaultMonth);
                      setSyncYear(defaultYear);
                      setSyncResult(null);
                      setOpenSyncId(c.id);
                    }}
                    className="text-xs px-2.5 py-1 rounded border border-white/10 text-zinc-400 hover:text-white hover:border-teal-500/50 hover:bg-teal-500/10 transition-colors shrink-0"
                  >
                    {isOpen ? "Cancel" : "↺ Force Sync"}
                  </button>
                )}
              </div>

              {/* Inline force-sync form */}
              {isOpen && c.agent_id && (
                <div className="flex items-center gap-2 pl-5 flex-wrap">
                  <span className="text-xs text-zinc-500">Sync period:</span>
                  <select
                    value={syncMonth}
                    onChange={(e) => setSyncMonth(Number(e.target.value))}
                    className="text-xs bg-zinc-800 border border-white/10 rounded px-2 py-1 text-zinc-200"
                  >
                    {MONTHS.map((m, i) => (
                      <option key={i + 1} value={i + 1}>{m}</option>
                    ))}
                  </select>
                  <select
                    value={syncYear}
                    onChange={(e) => setSyncYear(Number(e.target.value))}
                    className="text-xs bg-zinc-800 border border-white/10 rounded px-2 py-1 text-zinc-200"
                  >
                    {years.map((y) => <option key={y} value={y}>{y}</option>)}
                  </select>
                  <button
                    onClick={() => handleForceSync(c.agent_id!)}
                    disabled={syncing}
                    className="text-xs px-3 py-1 rounded bg-teal-600 hover:bg-teal-500 text-white font-medium disabled:opacity-50 transition-colors"
                  >
                    {syncing ? "Queuing…" : "Queue Sync"}
                  </button>
                  <span className="text-xs text-zinc-500">
                    Agent will pick up within 5 min
                  </span>
                </div>
              )}

              {/* Success / error feedback */}
              {syncResult?.id === c.id && (
                <p className={`text-xs pl-5 ${syncResult.ok ? "text-emerald-400" : "text-red-400"}`}>
                  {syncResult.ok
                    ? `Sync queued for ${MONTHS[syncMonth - 1]} ${syncYear} — agent will run it within 5 minutes.`
                    : "Failed to queue sync. Check the agent is active and try again."}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [age, setAge] = useState(0);

  const fetchData = useCallback(() => {
    setError(false);
    getAdminOverview()
      .then((r) => { setData(r.data); setAge(0); })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
    const poll = setInterval(fetchData, 60_000);
    const tick = setInterval(() => setAge((a) => a + 1), 1_000);
    return () => { clearInterval(poll); clearInterval(tick); };
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-zinc-500 text-sm">
        <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
        Loading dashboard…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card p-6 text-center space-y-3">
        <p className="text-red-400 text-sm">Failed to load dashboard.</p>
        <button onClick={fetchData} className="btn-primary text-xs px-4 py-2">Retry</button>
      </div>
    );
  }

  const mrrFmt = `R ${data.mrr.toLocaleString("en-ZA")}`;
  const planSub = Object.entries(data.plans)
    .sort(([a], [b]) => ["starter", "professional", "premium"].indexOf(a) - ["starter", "professional", "premium"].indexOf(b))
    .map(([p, n]) => `${n} ${p}`)
    .join(" · ");
  const reportGap = data.active_clients - data.reports_this_month;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-heading text-2xl font-bold">Operator Dashboard</h1>
          <p className="text-zinc-500 text-xs mt-0.5">
            All client metrics · refreshed {age}s ago
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </span>
          <button
            onClick={fetchData}
            className="btn-ghost text-xs px-3 py-1.5 border border-surface-border"
          >
            Refresh
          </button>
          <Link to="/admin/manage" className="btn-primary text-xs px-3 py-1.5">
            Clients &amp; Users →
          </Link>
        </div>
      </div>

      {/* Stat tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile
          label="Monthly Revenue"
          value={mrrFmt}
          sub={planSub || "no active plans"}
          accent="teal"
        />
        <StatTile
          label="Active Clients"
          value={data.active_clients}
          sub={data.inactive_clients > 0 ? `${data.inactive_clients} inactive` : "all active"}
        />
        <StatTile
          label="Reports This Month"
          value={data.reports_this_month}
          sub={reportGap > 0 ? `${reportGap} not yet generated` : "all up to date"}
        />
        <StatTile
          label="Payroll Pending"
          value={data.payroll_pending_count}
          sub="waiting for upload"
          accent={data.payroll_pending_count > 0 ? "amber" : undefined}
        />
      </div>

      {/* System status */}
      <SystemStatusBar />

      {/* Agent connections */}
      <AgentStatusPanel clients={data.clients} onSyncQueued={fetchData} />

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Client cards — 2 cols */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="font-heading font-bold text-[11px] uppercase tracking-wider text-zinc-500">
            Clients — {data.active_clients} active
          </h2>
          {data.clients.length === 0 ? (
            <div className="card p-10 text-center text-zinc-600 text-sm">
              No active clients yet.{" "}
              <Link to="/admin/manage" className="text-teal-400 hover:underline">
                Add your first client →
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {data.clients.map((c) => (
                <ClientCard key={c.id} c={c} />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Health distribution */}
          <div className="card p-5">
            <h3 className="font-heading font-bold text-[11px] uppercase tracking-wider text-zinc-500 mb-4">
              Portfolio Health
            </h3>
            <HealthDistributionBar distribution={data.health_distribution} />
          </div>

          {/* Recent reports feed */}
          <div className="card p-5">
            <h3 className="font-heading font-bold text-[11px] uppercase tracking-wider text-zinc-500 mb-4">
              Recent Reports
            </h3>
            {data.recent_reports.length === 0 ? (
              <p className="text-xs text-zinc-600">No reports generated yet.</p>
            ) : (
              <div className="space-y-3">
                {data.recent_reports.map((r, i) => (
                  <div key={i} className="flex items-start justify-between gap-2 py-2 border-b border-white/5 last:border-0">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-zinc-200 truncate leading-tight">{r.company_name}</p>
                      <p className="text-[11px] text-zinc-500 mt-0.5">{formatPeriod(r.period_month, r.period_year)}</p>
                    </div>
                    <div className="text-right shrink-0">
                      {r.health_score != null && r.health_rating ? (
                        <span className={`text-xs font-medium ${RATING_TEXT[r.health_rating] ?? "text-zinc-400"}`}>
                          {r.health_score}/100
                        </span>
                      ) : (
                        <span className="text-xs text-zinc-600">—</span>
                      )}
                      <p className="text-[10px] text-zinc-600 mt-0.5">{timeAgo(r.generated_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Plan breakdown */}
          <div className="card p-5">
            <h3 className="font-heading font-bold text-[11px] uppercase tracking-wider text-zinc-500 mb-4">
              Plan Breakdown
            </h3>
            <div className="space-y-2.5">
              {(["starter", "professional", "premium"] as const).map((key) => {
                const count = data.plans[key] ?? 0;
                const prices = { starter: "R500", professional: "R900", premium: "R1,500" };
                return (
                  <div key={key} className="flex items-center justify-between">
                    <span className={`text-[11px] px-2 py-0.5 rounded border capitalize ${PLAN_STYLE[key]}`}>
                      {key}
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-white">{count}</span>
                      <span className="text-xs text-zinc-600">{prices[key]}/mo</span>
                    </div>
                  </div>
                );
              })}
              <div className="pt-2 mt-1 border-t border-white/8 flex items-center justify-between">
                <span className="text-xs text-zinc-500">Total MRR</span>
                <span className="text-sm font-bold brand-text">{mrrFmt}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
