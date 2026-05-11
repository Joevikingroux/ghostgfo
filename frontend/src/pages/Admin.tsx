import { useEffect, useState } from "react";
import axios from "axios";
import { getUsers, adminReset2FA, deactivateUser, activateUser, updateUser } from "@/lib/api";
import type { Company, EvolutionAgent, UserAdminView } from "@/lib/types";

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
  owner_name: "", owner_email: "", owner_telegram: "",
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
              <label className="block text-xs text-zinc-400 mb-1">Telegram Chat ID</label>
              <input value={form.owner_telegram} onChange={set("owner_telegram")} className="input-base w-full" placeholder="e.g. 123456789" />
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

function EditCompanyForm({ company, onSaved, onCancel }: {
  company: Company;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    name: company.name ?? "",
    trading_name: company.trading_name ?? "",
    industry: company.industry ?? "",
    owner_name: company.owner_name ?? "",
    owner_email: company.owner_email ?? "",
    owner_telegram: company.owner_telegram ?? "",
    bookkeeper_name: company.bookkeeper_name ?? "",
    bookkeeper_email: company.bookkeeper_email ?? "",
    plan: company.plan ?? "starter",
    data_source: company.data_source ?? "partner",
    language: company.language ?? "en",
    active: company.active,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await axios.patch(`/api/companies/${company.id}`, form, { withCredentials: true });
      onSaved();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-5 space-y-4 bg-surface-card/60 border-t border-brand-teal/30">
      <p className="text-xs font-bold text-brand-teal uppercase tracking-wider">Editing: {company.name}</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Company Name *</label>
          <input required value={form.name} onChange={set("name")} className="input-base w-full" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Trading Name</label>
          <input value={form.trading_name} onChange={set("trading_name")} className="input-base w-full" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Industry</label>
          <input value={form.industry} onChange={set("industry")} className="input-base w-full" />
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

      <p className="text-xs text-zinc-500 uppercase tracking-wider pt-1">Owner Contact</p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Owner Name</label>
          <input value={form.owner_name} onChange={set("owner_name")} className="input-base w-full" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Owner Email</label>
          <input type="email" value={form.owner_email} onChange={set("owner_email")} className="input-base w-full" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Telegram Chat ID</label>
          <input value={form.owner_telegram} onChange={set("owner_telegram")} className="input-base w-full" placeholder="e.g. 123456789" />
        </div>
      </div>

      <p className="text-xs text-zinc-500 uppercase tracking-wider pt-1">Bookkeeper Contact</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Bookkeeper Name</label>
          <input value={form.bookkeeper_name} onChange={set("bookkeeper_name")} className="input-base w-full" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Bookkeeper Email</label>
          <input type="email" value={form.bookkeeper_email} onChange={set("bookkeeper_email")} className="input-base w-full" />
        </div>
      </div>

      <div className="flex items-center gap-4 pt-1">
        <label className="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
          <input
            type="checkbox"
            checked={form.active}
            onChange={(e) => setForm((p) => ({ ...p, active: e.target.checked }))}
            className="w-4 h-4 accent-teal-400"
          />
          Active
        </label>
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}
      <div className="flex gap-3">
        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? "Saving…" : "Save Changes"}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  );
}

function CompaniesTab({ companies, onRefresh }: { companies: Company[]; onRefresh: () => void }) {
  const [editingId, setEditingId] = useState<string | null>(null);

  const PLAN_COLOUR: Record<string, string> = {
    starter: "text-zinc-400",
    professional: "text-brand-teal",
    premium: "text-brand-cyan",
  };

  const deleteCompany = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This will permanently remove the company and all its data. This cannot be undone.`)) return;
    try {
      await axios.delete(`/api/companies/${id}`, { withCredentials: true });
      onRefresh();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg || "Failed to delete company.");
    }
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
                <th className="p-4 text-left font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <>
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
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setEditingId(editingId === c.id ? null : c.id)}
                          className={`text-xs transition-colors ${editingId === c.id ? "text-brand-teal" : "text-zinc-500 hover:text-white"}`}
                        >
                          {editingId === c.id ? "Cancel" : "Edit"}
                        </button>
                        <button
                          onClick={() => deleteCompany(c.id, c.name)}
                          className="text-xs text-zinc-600 hover:text-red-400 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  {editingId === c.id && (
                    <tr key={`${c.id}-edit`}>
                      <td colSpan={6} className="p-0">
                        <EditCompanyForm
                          company={c}
                          onSaved={() => { setEditingId(null); onRefresh(); }}
                          onCancel={() => setEditingId(null)}
                        />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Users tab ──────────────────────────────────────────────────────────────

function UserEditForm({
  user,
  companies,
  onSaved,
  onCancel,
}: {
  user: UserAdminView;
  companies: Company[];
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    full_name: user.full_name ?? "",
    email: user.email,
    role: user.role,
    company_id: user.company_id ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await updateUser(user.id, {
        full_name: form.full_name || undefined,
        email: form.email,
        role: form.role,
        company_id: form.company_id || null,
      });
      onSaved();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <tr>
      <td colSpan={5} className="p-0">
        <form
          onSubmit={handleSave}
          className="px-5 py-4 bg-surface-card/60 border-t border-brand-teal/30 space-y-3"
        >
          <p className="text-xs font-bold text-brand-teal uppercase tracking-wider">
            Editing: {user.email}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Full Name</label>
              <input value={form.full_name} onChange={set("full_name")} className="input-base w-full" placeholder="Jane Smith" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Email *</label>
              <input required type="email" value={form.email} onChange={set("email")} className="input-base w-full" />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Role</label>
              <select value={form.role} onChange={set("role")} className="input-base w-full">
                <option value="owner">Owner</option>
                <option value="bookkeeper">Bookkeeper</option>
                <option value="viewer">Viewer</option>
                <option value="admin">Admin (Numbers10 only)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Company</label>
              <select value={form.company_id} onChange={set("company_id")} className="input-base w-full">
                <option value="">— No company (admin) —</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? "Saving…" : "Save Changes"}
            </button>
            <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </td>
    </tr>
  );
}

const ROLE_COLOUR: Record<string, string> = {
  admin: "text-brand-teal",
  owner: "text-white",
  bookkeeper: "text-zinc-300",
  viewer: "text-zinc-500",
};

function UsersTab({ companies }: { companies: Company[] }) {
  const [users, setUsers] = useState<UserAdminView[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const load = () =>
    getUsers().then((r) => setUsers(r.data)).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const handleReset2FA = async (u: UserAdminView) => {
    if (!confirm(`Reset 2FA for ${u.email}? They will need to re-enrol on next login.`)) return;
    setActionInProgress(u.id);
    try {
      await adminReset2FA(u.id);
      load();
    } finally {
      setActionInProgress(null);
    }
  };

  const handleToggleActive = async (u: UserAdminView) => {
    const action = u.active ? "deactivate" : "activate";
    if (!confirm(`${u.active ? "Deactivate" : "Activate"} user ${u.email}?`)) return;
    setActionInProgress(u.id);
    try {
      u.active ? await deactivateUser(u.id) : await activateUser(u.id);
      load();
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDelete = async (u: UserAdminView) => {
    if (!confirm(`Permanently delete ${u.email}? This cannot be undone.`)) return;
    setActionInProgress(u.id);
    try {
      await axios.delete(`/api/users/${u.id}`, { withCredentials: true });
      load();
    } finally {
      setActionInProgress(null);
    }
  };

  // Group users by company
  const grouped = users.reduce<Record<string, UserAdminView[]>>((acc, u) => {
    const key = u.company_name ?? "__admin__";
    (acc[key] ??= []).push(u);
    return acc;
  }, {});

  const groupKeys = Object.keys(grouped).sort((a, b) => {
    if (a === "__admin__") return 1;
    if (b === "__admin__") return -1;
    return a.localeCompare(b);
  });

  if (loading) return <p className="text-zinc-500 text-sm">Loading users…</p>;

  return (
    <div className="space-y-4">
      {groupKeys.map((group) => (
        <div key={group} className="card overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-border bg-white/2">
            <p className="font-heading text-xs font-bold text-zinc-400 uppercase tracking-wider">
              {group === "__admin__" ? "Numbers10 / Admin accounts" : group}
            </p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-xs text-zinc-600 uppercase tracking-wider">
                <th className="px-5 py-2.5 text-left font-medium">User</th>
                <th className="px-5 py-2.5 text-left font-medium">Role</th>
                <th className="px-5 py-2.5 text-left font-medium">2FA</th>
                <th className="px-5 py-2.5 text-left font-medium">Status</th>
                <th className="px-5 py-2.5 text-left font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {grouped[group].map((u) => {
                const busy = actionInProgress === u.id;
                const isEditing = editingId === u.id;
                return (
                  <>
                    <tr key={u.id} className="border-b border-surface-border/30 last:border-0 hover:bg-white/2 transition-colors">
                      <td className="px-5 py-3">
                        <p className="font-medium">{u.full_name ?? u.email}</p>
                        {u.full_name && <p className="text-xs text-zinc-500">{u.email}</p>}
                        {u.must_change_password && (
                          <p className="text-xs text-amber-400 mt-0.5">⚠ Must set password</p>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`capitalize font-medium text-sm ${ROLE_COLOUR[u.role] ?? ""}`}>{u.role}</span>
                      </td>
                      <td className="px-5 py-3">
                        {u.totp_enabled ? (
                          <span className="text-xs text-emerald-400 font-medium">✓ On</span>
                        ) : (
                          <span className="text-xs text-zinc-600">Off</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`text-xs font-medium ${u.active ? "text-emerald-400" : "text-red-400"}`}>
                          {u.active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => setEditingId(isEditing ? null : u.id)}
                            className={`text-xs transition-colors ${isEditing ? "text-brand-teal" : "text-zinc-400 hover:text-white"}`}
                          >
                            {isEditing ? "Cancel" : "Edit"}
                          </button>
                          {u.totp_enabled && (
                            <button
                              onClick={() => handleReset2FA(u)}
                              disabled={busy}
                              className="text-xs text-zinc-500 hover:text-amber-400 transition-colors"
                            >
                              Reset 2FA
                            </button>
                          )}
                          <button
                            onClick={() => handleToggleActive(u)}
                            disabled={busy}
                            className={`text-xs transition-colors ${
                              u.active ? "text-zinc-500 hover:text-red-400" : "text-zinc-500 hover:text-emerald-400"
                            }`}
                          >
                            {u.active ? "Deactivate" : "Activate"}
                          </button>
                          <button
                            onClick={() => handleDelete(u)}
                            disabled={busy}
                            className="text-xs text-zinc-600 hover:text-red-400 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                    {isEditing && (
                      <UserEditForm
                        key={`${u.id}-edit`}
                        user={u}
                        companies={companies}
                        onSaved={() => { setEditingId(null); load(); }}
                        onCancel={() => setEditingId(null)}
                      />
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}
      {users.length === 0 && <p className="text-zinc-500 text-sm">No users yet.</p>}
    </div>
  );
}

// ── Agents tab ─────────────────────────────────────────────────────────────

function CopyField({ label, value, secret }: { label: string; value: string; secret?: boolean }) {
  const [copied, setCopied] = useState(false);
  const [revealed, setRevealed] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  return (
    <div>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <div className="bg-black rounded-md px-3 py-2 flex items-center gap-2">
        <code className={`flex-1 text-xs font-mono text-zinc-300 break-all ${secret && !revealed ? "blur-sm select-none" : ""}`}>
          {value}
        </code>
        {secret && (
          <button
            type="button"
            onClick={() => setRevealed((r) => !r)}
            className="shrink-0 text-xs text-zinc-500 hover:text-white transition-colors"
          >
            {revealed ? "Hide" : "Show"}
          </button>
        )}
        <button
          type="button"
          onClick={copy}
          className="shrink-0 text-xs px-2 py-1 rounded bg-surface-card text-zinc-400 hover:text-white transition-colors"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </div>
  );
}

const BLANK_AGENT_FORM = { company_id: "", server_name: "", db_name: "", db_username: "", db_password: "" };

function AgentsTab({ companies }: { companies: Company[] }) {
  const [agents, setAgents] = useState<EvolutionAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(BLANK_AGENT_FORM);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);

  const load = () =>
    axios.get("/api/agent/agents", { withCredentials: true })
      .then((r) => setAgents(r.data))
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const setF = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.company_id) return;
    setCreating(true);
    setCreateError("");
    try {
      await axios.post("/api/agent/agents", form, { withCredentials: true });
      setForm(BLANK_AGENT_FORM);
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
      {/* Provision form */}
      <div className="card p-5">
        <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-4">
          Provision New Agent
        </h2>
        <form onSubmit={handleCreate} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-3">
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
                onChange={setF("server_name")}
                className="input-base w-full"
              />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">Database Name</label>
              <input
                type="text"
                placeholder="PASTEL_EVOLUTION_DB"
                value={form.db_name}
                onChange={setF("db_name")}
                className="input-base w-full"
              />
            </div>
            <div>{/* spacer */}</div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">SQL Username</label>
              <input
                type="text"
                placeholder="ghostcfo_reader"
                value={form.db_username}
                onChange={setF("db_username")}
                className="input-base w-full"
              />
            </div>
            <div>
              <label className="block text-xs text-zinc-400 mb-1">SQL Password</label>
              <input
                type="password"
                placeholder="••••••••"
                value={form.db_password}
                onChange={setF("db_password")}
                className="input-base w-full"
              />
            </div>
          </div>
          {createError && <p className="text-red-400 text-xs">{createError}</p>}
          <button type="submit" disabled={creating} className="btn-primary">
            {creating ? "Creating…" : "Create Agent"}
          </button>
        </form>
      </div>

      {/* Agent list */}
      {loading ? (
        <p className="text-zinc-500 text-sm">Loading agents…</p>
      ) : agents.length === 0 ? (
        <p className="text-zinc-500 text-sm">No Evolution agents provisioned yet.</p>
      ) : (
        <div className="space-y-3">
          {agents.map((a) => (
            <div key={a.id} className="card p-4 space-y-4">
              {/* Header row */}
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-medium">{a.company_name}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {a.server_name ?? "—"} &nbsp;/&nbsp; {a.db_name ?? "—"}
                    {a.db_username && <span> &nbsp;·&nbsp; user: {a.db_username}</span>}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <p className="text-xs text-zinc-500">Last sync</p>
                    <p className="text-xs mt-0.5">{fmt(a.last_sync_at)}</p>
                  </div>
                  {syncBadge(a.last_sync_status)}
                  <span className={`text-xs font-medium ${a.active ? "text-emerald-400" : "text-red-400"}`}>
                    {a.active ? "Active" : "Inactive"}
                  </span>
                  <button
                    onClick={() => setEditingId(editingId === a.id ? null : a.id)}
                    className="text-xs text-zinc-500 hover:text-white transition-colors"
                  >
                    {editingId === a.id ? "Done" : "Edit"}
                  </button>
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

              {/* Credentials */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <CopyField label="API Key" value={a.api_key} secret />
                <CopyField label="AES Encryption Key" value={a.encryption_key} secret />
              </div>

              {/* Inline edit for SQL connection details */}
              {editingId === a.id && (
                <AgentEditForm agent={a} onSaved={() => { setEditingId(null); load(); }} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentEditForm({ agent, onSaved }: { agent: EvolutionAgent; onSaved: () => void }) {
  const [form, setForm] = useState({
    server_name: agent.server_name ?? "",
    db_name: agent.db_name ?? "",
    db_username: agent.db_username ?? "",
    db_password: agent.db_password ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const setF = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await axios.patch(`/api/agent/agents/${agent.id}`, { company_id: agent.company_id, ...form }, { withCredentials: true });
      onSaved();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="border-t border-surface-border pt-3 space-y-3">
      <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Update SQL Connection</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">SQL Server</label>
          <input value={form.server_name} onChange={setF("server_name")} className="input-base w-full" placeholder="SERVERNAME\SQLEXPRESS" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">Database Name</label>
          <input value={form.db_name} onChange={setF("db_name")} className="input-base w-full" placeholder="PASTEL_EVOLUTION_DB" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">SQL Username</label>
          <input value={form.db_username} onChange={setF("db_username")} className="input-base w-full" placeholder="ghostcfo_reader" />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">SQL Password</label>
          <input type="password" value={form.db_password} onChange={setF("db_password")} className="input-base w-full" placeholder="••••••••" />
        </div>
      </div>
      {error && <p className="text-red-400 text-xs">{error}</p>}
      <button type="submit" disabled={saving} className="btn-primary">
        {saving ? "Saving…" : "Save Changes"}
      </button>
    </form>
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
