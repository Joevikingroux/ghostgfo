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

// ── New Company form ───────────────────────────────────────────────────────

const BLANK_COMPANY = {
  name: "", trading_name: "", industry: "",
  owner_name: "", owner_email: "", owner_whatsapp: "",
  bookkeeper_name: "", bookkeeper_email: "",
  plan: "starter", data_source: "partner", language: "en",
};

function NewCompanyForm({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(BLANK_COMPANY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await axios.post("/api/companies", form, { withCredentials: true });
      setForm(BLANK_COMPANY);
      setOpen(false);
      onCreated();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to create company.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between p-5 text-left"
      >
        <span className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
          + Add New Client
        </span>
        <span className="text-zinc-500 text-sm">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-4 border-t border-surface-border pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Company Name *</label>
              <input required value={form.name} onChange={set("name")} className="input-base w-full" placeholder="ABC Hardware (Pty) Ltd" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Trading Name</label>
              <input value={form.trading_name} onChange={set("trading_name")} className="input-base w-full" placeholder="ABC Hardware" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Industry</label>
              <input value={form.industry} onChange={set("industry")} className="input-base w-full" placeholder="Retail - Hardware" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Plan</label>
              <select value={form.plan} onChange={set("plan")} className="input-base w-full">
                <option value="starter">Starter — R500/mo</option>
                <option value="professional">Professional — R900/mo</option>
                <option value="premium">Premium — R1,500/mo</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Data Source</label>
              <select value={form.data_source} onChange={set("data_source")} className="input-base w-full">
                <option value="partner">Pastel Partner (file upload)</option>
                <option value="evolution">Pastel Evolution (SQL agent)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Report Language</label>
              <select value={form.language} onChange={set("language")} className="input-base w-full">
                <option value="en">English</option>
                <option value="af">Afrikaans</option>
              </select>
            </div>
          </div>

          <p className="text-xs text-zinc-500 uppercase tracking-wider pt-2">Owner Contact</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Owner Name</label>
              <input value={form.owner_name} onChange={set("owner_name")} className="input-base w-full" placeholder="John Smith" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Owner Email</label>
              <input type="email" value={form.owner_email} onChange={set("owner_email")} className="input-base w-full" placeholder="owner@company.co.za" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">WhatsApp (+27…)</label>
              <input value={form.owner_whatsapp} onChange={set("owner_whatsapp")} className="input-base w-full" placeholder="+27821234567" />
            </div>
          </div>

          <p className="text-xs text-zinc-500 uppercase tracking-wider pt-2">Bookkeeper Contact</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Bookkeeper Name</label>
              <input value={form.bookkeeper_name} onChange={set("bookkeeper_name")} className="input-base w-full" placeholder="Jane Doe" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Bookkeeper Email</label>
              <input type="email" value={form.bookkeeper_email} onChange={set("bookkeeper_email")} className="input-base w-full" placeholder="bookkeeper@company.co.za" />
            </div>
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-3 pt-1">
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Creating…" : "Create Client"}
            </button>
            <button type="button" onClick={() => setOpen(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

// ── Companies tab ──────────────────────────────────────────────────────────

function CompaniesTab({ companies, onRefresh }: { companies: Company[]; onRefresh: () => void }) {
  const PLAN_COLOUR: Record<string, string> = {
    starter: "text-zinc-400",
    professional: "text-brand-teal",
    premium: "text-brand-cyan",
  };

  return (
    <div className="space-y-4">
      <NewCompanyForm onCreated={onRefresh} />

      {companies.length === 0 ? (
        <p className="text-zinc-500 text-sm">No clients yet — add one above.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-xs text-zinc-500 uppercase tracking-wider">
                <th className="p-4 text-left font-medium">Company</th>
                <th className="p-4 text-left font-medium">Owner</th>
                <th className="p-4 text-left font-medium">Plan</th>
                <th className="p-4 text-left font-medium">Source</th>
                <th className="p-4 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.id} className="border-b border-surface-border/40 hover:bg-surface-card/40 transition-colors">
                  <td className="p-4">
                    <p className="font-medium">{c.name}</p>
                    {c.trading_name && c.trading_name !== c.name && (
                      <p className="text-xs text-zinc-500">{c.trading_name}</p>
                    )}
                  </td>
                  <td className="p-4">
                    <p>{c.owner_name ?? "—"}</p>
                    <p className="text-xs text-zinc-500">{c.owner_email ?? ""}</p>
                  </td>
                  <td className="p-4">
                    <span className={`font-medium capitalize ${PLAN_COLOUR[c.plan] ?? ""}`}>
                      {c.plan}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`text-xs font-medium ${
                      c.data_source === "evolution" ? "text-brand-teal" : "text-zinc-400"
                    }`}>
                      {c.data_source === "evolution" ? "Evolution" : "Partner"}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`text-xs font-medium ${c.active ? "text-emerald-400" : "text-red-400"}`}>
                      {c.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Users tab ──────────────────────────────────────────────────────────────

interface UserRow {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  company_id: string | null;
  active: boolean;
}

const BLANK_USER = { email: "", password: "", full_name: "", role: "owner", company_id: "" };

function UsersTab({ companies }: { companies: Company[] }) {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(BLANK_USER);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);

  const load = () =>
    axios.get("/api/users", { withCredentials: true })
      .then((r) => setUsers(r.data))
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = { ...form, company_id: form.company_id || null };
      await axios.post("/api/users", payload, { withCredentials: true });
      setForm(BLANK_USER);
      setOpen(false);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to create user.");
    } finally {
      setSaving(false);
    }
  };

  const deleteUser = async (id: string, email: string) => {
    if (!confirm(`Delete user ${email}? This cannot be undone.`)) return;
    await axios.delete(`/api/users/${id}`, { withCredentials: true });
    load();
  };

  const companyName = (id: string | null) =>
    companies.find((c) => c.id === id)?.name ?? "—";

  const ROLE_COLOUR: Record<string, string> = {
    admin: "text-brand-teal",
    owner: "text-white",
    bookkeeper: "text-zinc-300",
    viewer: "text-zinc-500",
  };

  return (
    <div className="space-y-4">
      {/* New user form */}
      <div className="card">
        <button
          onClick={() => setOpen((o) => !o)}
          className="w-full flex items-center justify-between p-5 text-left"
        >
          <span className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
            + Add New User
          </span>
          <span className="text-zinc-500 text-sm">{open ? "▲" : "▼"}</span>
        </button>

        {open && (
          <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-4 border-t border-surface-border pt-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Email *</label>
                <input required type="email" value={form.email} onChange={set("email")} className="input-base w-full" placeholder="owner@client.co.za" />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Full Name</label>
                <input value={form.full_name} onChange={set("full_name")} className="input-base w-full" placeholder="John Smith" />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Password *</label>
                <div className="relative">
                  <input
                    required
                    type={showPw ? "text" : "password"}
                    value={form.password}
                    onChange={set("password")}
                    className="input-base w-full pr-16"
                    placeholder="Min. 8 characters"
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((p) => !p)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-zinc-500 hover:text-white"
                  >
                    {showPw ? "Hide" : "Show"}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Role</label>
                <select value={form.role} onChange={set("role")} className="input-base w-full">
                  <option value="owner">Owner — sees reports &amp; dashboard</option>
                  <option value="bookkeeper">Bookkeeper — uploads files</option>
                  <option value="viewer">Viewer — read only</option>
                  <option value="admin">Admin — full access (Numbers10 only)</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs text-zinc-400 mb-1">Company</label>
                <select value={form.company_id} onChange={set("company_id")} className="input-base w-full">
                  <option value="">— No company (admin account) —</option>
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            </div>
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <div className="flex gap-3 pt-1">
              <button type="submit" disabled={saving} className="btn-primary">
                {saving ? "Creating…" : "Create User"}
              </button>
              <button type="button" onClick={() => setOpen(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Users list */}
      {loading ? (
        <p className="text-zinc-500 text-sm">Loading users…</p>
      ) : users.length === 0 ? (
        <p className="text-zinc-500 text-sm">No users yet.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-xs text-zinc-500 uppercase tracking-wider">
                <th className="p-4 text-left font-medium">User</th>
                <th className="p-4 text-left font-medium">Role</th>
                <th className="p-4 text-left font-medium">Company</th>
                <th className="p-4 text-left font-medium">Status</th>
                <th className="p-4 text-left font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-surface-border/40 hover:bg-surface-card/40 transition-colors">
                  <td className="p-4">
                    <p className="font-medium">{u.full_name ?? u.email}</p>
                    {u.full_name && <p className="text-xs text-zinc-500">{u.email}</p>}
                  </td>
                  <td className="p-4">
                    <span className={`capitalize font-medium ${ROLE_COLOUR[u.role] ?? ""}`}>{u.role}</span>
                  </td>
                  <td className="p-4 text-zinc-400">{companyName(u.company_id)}</td>
                  <td className="p-4">
                    <span className={`text-xs font-medium ${u.active ? "text-emerald-400" : "text-red-400"}`}>
                      {u.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="p-4">
                    <button
                      onClick={() => deleteUser(u.id, u.email)}
                      className="text-xs text-zinc-600 hover:text-red-400 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Agents tab ─────────────────────────────────────────────────────────────

const MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function ManualSyncGenerator({ agent }: { agent: EvolutionAgent }) {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [copied, setCopied] = useState(false);

  const cmd = `GhostCFOAgent.exe run --month ${month} --year ${year}`;

  const copy = () => {
    navigator.clipboard.writeText(cmd).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  return (
    <div className="border-t border-surface-border pt-3 space-y-2">
      <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Manual sync — pull a specific period</p>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-zinc-600 mb-1">Month</label>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="input-base text-xs py-1.5"
          >
            {MONTHS_SHORT.map((m, i) => (
              <option key={i + 1} value={i + 1}>{m}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-zinc-600 mb-1">Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={2020} max={2099}
            className="input-base text-xs py-1.5 w-24"
          />
        </div>
        <div className="flex-1 min-w-0">
          <label className="block text-xs text-zinc-600 mb-1">Run this command on {agent.company_name}'s server</label>
          <div className="bg-black rounded-md px-3 py-2 flex items-center justify-between gap-3">
            <code className="text-xs text-zinc-300 font-mono truncate">{cmd}</code>
            <button
              type="button"
              onClick={copy}
              className="shrink-0 text-xs px-2 py-1 rounded bg-surface-card text-zinc-400 hover:text-white transition-colors"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>
      </div>
      <p className="text-xs text-zinc-600">
        Log file on client's server: <code className="text-zinc-400">C:\GhostCFO\agent.log</code>
      </p>
    </div>
  );
}

function AgentsTab({ companies }: { companies: Company[] }) {
  const [agents, setAgents] = useState<EvolutionAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);

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
              <div>
                <p className="text-xs text-zinc-500 mb-1.5">Install command (run once on client's server)</p>
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
              <ManualSyncGenerator agent={a} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Admin page ─────────────────────────────────────────────────────────────

type Tab = "companies" | "users" | "agents";

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("companies");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  const loadCompanies = () =>
    axios.get("/api/companies", { withCredentials: true })
      .then((r) => setCompanies(r.data))
      .finally(() => setLoading(false));

  useEffect(() => { loadCompanies(); }, []);

  const activeCount = companies.filter((c) => c.active).length;
  const evolutionCount = companies.filter((c) => c.data_source === "evolution").length;
  const mrr = companies
    .filter((c) => c.active)
    .reduce((sum, c) => {
      const prices: Record<string, number> = { starter: 500, professional: 900, premium: 1500 };
      return sum + (prices[c.plan] ?? 0);
    }, 0);

  const TAB_LABELS: Record<Tab, string> = {
    companies: "Clients",
    users: "Users",
    agents: "Evolution Agents",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Admin</h1>
        <p className="text-zinc-400 text-sm mt-1">Numbers10 — all Ghost CFO clients</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Active Clients", value: activeCount },
          { label: "Evolution Agents", value: evolutionCount },
          { label: "Est. MRR", value: `R${mrr.toLocaleString("en-ZA")}` },
        ].map((tile) => (
          <div key={tile.label} className="card p-4">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">{tile.label}</p>
            <p className="text-2xl font-bold font-heading brand-text">{tile.value}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-2 border-b border-surface-border">
        {(["companies", "users", "agents"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-brand-teal text-white"
                : "border-transparent text-zinc-500 hover:text-white"
            }`}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-zinc-500 text-sm">Loading…</p>
      ) : tab === "companies" ? (
        <CompaniesTab companies={companies} onRefresh={loadCompanies} />
      ) : tab === "users" ? (
        <UsersTab companies={companies} />
      ) : (
        <AgentsTab companies={companies} />
      )}
    </div>
  );
}
