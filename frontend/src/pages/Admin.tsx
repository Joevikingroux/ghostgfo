import { useEffect, useState } from "react";
import axios from "axios";
import type { Company, EvolutionAgent } from "@/lib/types";

// ── helpers ────────────────────────────────────────────────────────────────

function fmt(dt: string | null): string {
  if (!dt) return "—";
  return new Date(dt).toLocaleString("en-ZA", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function syncBadge(status: string | null) {
  if (!status) return <span className="text-zinc-500 text-xs">Never</span>;
  const ok = status === "accepted";
  return (
    <span className={`text-xs font-medium ${ok ? "text-emerald-400" : "text-red-400"}`}>
      {ok ? "✓ OK" : "✗ " + status}
    </span>
  );
}

// ── Agents tab ─────────────────────────────────────────────────────────────

function AgentsTab({ companies }: { companies: Company[] }) {
  const [agents, setAgents] = useState<EvolutionAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);

  // New agent form
  const [form, setForm] = useState({ company_id: "", server_name: "", db_name: "" });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const load = () =>
    axios.get("/api/agent/agents", { withCredentials: true })
      .then((r) => setAgents(r.data))
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const copyCommand = (cmd: string, id: string) => {
    navigator.clipboard.writeText(cmd).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 2500);
    });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.company_id) return;
    setCreating(true);
    setCreateError("");
    try {
      await axios.post("/api/agent/agents", form, { withCredentials: true });
      setForm({ company_id: "", server_name: "", db_name: "" });
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setCreateError(msg || "Failed to create agent.");
    } finally {
      setCreating(false);
    }
  };

  const deactivate = async (id: string) => {
    if (!confirm("Deactivate this agent? The client's agent will stop syncing.")) return;
    await axios.delete(`/api/agent/agents/${id}`, { withCredentials: true });
    load();
  };

  const evolutionCompanies = companies.filter((c) => c.data_source === "evolution");

  return (
    <div className="space-y-6">
      {/* Provision new agent */}
      <div className="card p-5">
        <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-4">
          Provision New Agent
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs text-zinc-400 mb-1">Company</label>
            <select
              value={form.company_id}
              onChange={(e) => setForm((p) => ({ ...p, company_id: e.target.value }))}
              className="input-base w-full"
              required
            >
              <option value="">Select company…</option>
              {evolutionCompanies.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-zinc-400 mb-1">SQL Server</label>
            <input
              type="text"
              placeholder="SERVERNAME\SQLEXPRESS"
              value={form.server_name}
              onChange={(e) => setForm((p) => ({ ...p, server_name: e.target.value }))}
              className="input-base w-full"
            />
          </div>
          <div>
            <label className="block text-xs text-zinc-400 mb-1">Database Name</label>
            <input
              type="text"
              placeholder="PASTEL_EVOLUTION_DB"
              value={form.db_name}
              onChange={(e) => setForm((p) => ({ ...p, db_name: e.target.value }))}
              className="input-base w-full"
            />
          </div>
          <button type="submit" disabled={creating} className="btn-primary h-9">
            {creating ? "Creating…" : "Create Agent"}
          </button>
        </form>
        {createError && <p className="text-red-400 text-xs mt-2">{createError}</p>}
      </div>

      {/* Agent list */}
      {loading ? (
        <p className="text-zinc-500 text-sm">Loading agents…</p>
      ) : agents.length === 0 ? (
        <p className="text-zinc-500 text-sm">No Evolution agents provisioned yet.</p>
      ) : (
        <div className="space-y-3">
          {agents.map((a) => (
            <div key={a.id} className="card p-4 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-medium text-sm">{a.company_name}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {a.server_name ?? "—"} &nbsp;/&nbsp; {a.db_name ?? "—"}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <p className="text-xs text-zinc-500">Last sync</p>
                    <p className="text-xs mt-0.5">{fmt(a.last_sync_at)}</p>
                  </div>
                  {syncBadge(a.last_sync_status)}
                  {a.active ? (
                    <span className="text-xs text-emerald-400 font-medium">Active</span>
                  ) : (
                    <span className="text-xs text-red-400 font-medium">Inactive</span>
                  )}
                  {a.active && (
                    <button
                      onClick={() => deactivate(a.id)}
                      className="text-xs text-zinc-500 hover:text-red-400 transition-colors"
                    >
                      Deactivate
                    </button>
                  )}
                </div>
              </div>

              {/* Install command */}
              <div className="bg-black rounded-md p-3 flex items-start justify-between gap-3">
                <code className="text-xs text-zinc-300 break-all font-mono leading-relaxed">
                  {a.install_command}
                </code>
                <button
                  onClick={() => copyCommand(a.install_command, a.id)}
                  className="shrink-0 text-xs px-2 py-1 rounded bg-surface-card text-zinc-400 hover:text-white transition-colors"
                >
                  {copied === a.id ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Companies tab ──────────────────────────────────────────────────────────

function CompaniesTab({ companies }: { companies: Company[] }) {
  const PLAN_COLOUR: Record<string, string> = {
    starter: "text-zinc-400",
    professional: "text-brand-teal",
    premium: "text-brand-cyan",
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-border text-xs text-zinc-500 uppercase tracking-wider">
            <th className="pb-2 text-left font-medium">Company</th>
            <th className="pb-2 text-left font-medium">Owner</th>
            <th className="pb-2 text-left font-medium">Plan</th>
            <th className="pb-2 text-left font-medium">Source</th>
            <th className="pb-2 text-left font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {companies.map((c) => (
            <tr key={c.id} className="border-b border-surface-border/40 hover:bg-surface-card/40 transition-colors">
              <td className="py-3 pr-4">
                <p className="font-medium">{c.name}</p>
                {c.trading_name && c.trading_name !== c.name && (
                  <p className="text-xs text-zinc-500">{c.trading_name}</p>
                )}
              </td>
              <td className="py-3 pr-4">
                <p>{c.owner_name ?? "—"}</p>
                <p className="text-xs text-zinc-500">{c.owner_email ?? ""}</p>
              </td>
              <td className="py-3 pr-4">
                <span className={`font-medium capitalize ${PLAN_COLOUR[c.plan] ?? ""}`}>
                  {c.plan}
                </span>
              </td>
              <td className="py-3 pr-4">
                <span className={`text-xs font-medium ${
                  c.data_source === "evolution" ? "text-brand-teal" : "text-zinc-400"
                }`}>
                  {c.data_source === "evolution" ? "Evolution" : "Partner"}
                </span>
              </td>
              <td className="py-3">
                <span className={`text-xs font-medium ${c.active ? "text-emerald-400" : "text-red-400"}`}>
                  {c.active ? "Active" : "Inactive"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Admin page ─────────────────────────────────────────────────────────────

type Tab = "companies" | "agents";

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("companies");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("/api/companies", { withCredentials: true })
      .then((r) => setCompanies(r.data))
      .finally(() => setLoading(false));
  }, []);

  const activeCount = companies.filter((c) => c.active).length;
  const evolutionCount = companies.filter((c) => c.data_source === "evolution").length;
  const mrr = companies
    .filter((c) => c.active)
    .reduce((sum, c) => {
      const prices: Record<string, number> = { starter: 500, professional: 900, premium: 1500 };
      return sum + (prices[c.plan] ?? 0);
    }, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Admin</h1>
        <p className="text-zinc-400 text-sm mt-1">Numbers10 — all Ghost CFO clients</p>
      </div>

      {/* MRR overview */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Active Clients", value: activeCount },
          { label: "Evolution Agents", value: evolutionCount },
          {
            label: "Est. MRR",
            value: `R${mrr.toLocaleString("en-ZA")}`,
          },
        ].map((tile) => (
          <div key={tile.label} className="card p-4">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">{tile.label}</p>
            <p className="text-2xl font-bold font-heading brand-text">{tile.value}</p>
          </div>
        ))}
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 border-b border-surface-border">
        {(["companies", "agents"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize ${
              tab === t
                ? "border-brand-teal text-white"
                : "border-transparent text-zinc-500 hover:text-white"
            }`}
          >
            {t === "agents" ? "Evolution Agents" : "Companies"}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-zinc-500 text-sm">Loading…</p>
      ) : tab === "companies" ? (
        <CompaniesTab companies={companies} />
      ) : (
        <AgentsTab companies={companies} />
      )}
    </div>
  );
}
