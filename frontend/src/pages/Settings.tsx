import { useEffect, useState } from "react";
import axios from "axios";
import { getMe } from "@/lib/api";
import type { User } from "@/lib/types";

interface CompanySettings {
  id: string;
  name: string;
  trading_name: string | null;
  owner_name: string | null;
  owner_email: string | null;
  owner_whatsapp: string | null;
  bookkeeper_name: string | null;
  bookkeeper_email: string | null;
  plan: string;
  language: string;
}

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [company, setCompany] = useState<CompanySettings | null>(null);
  const [form, setForm] = useState<Partial<CompanySettings>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getMe().then((r) => {
      setUser(r.data);
      if (r.data.company_id) {
        axios
          .get(`/api/companies/${r.data.company_id}`, { withCredentials: true })
          .then((cr) => {
            setCompany(cr.data);
            setForm(cr.data);
          });
      }
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company) return;
    setSaving(true);
    setError("");
    try {
      await axios.patch(`/api/companies/${company.id}`, form, {
        withCredentials: true,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError("Failed to save settings. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const set = (key: keyof CompanySettings) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  if (!user || !company) {
    return <div className="text-zinc-500 text-sm">Loading…</div>;
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Settings</h1>
        <p className="text-zinc-400 text-sm mt-1">
          Delivery details for your Ghost CFO reports.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        {/* Company */}
        <div className="card p-5 space-y-4">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
            Company
          </h2>
          <Field label="Company Name" value={form.name ?? ""} onChange={set("name")} />
          <Field label="Trading Name" value={form.trading_name ?? ""} onChange={set("trading_name")} />
        </div>

        {/* Owner */}
        <div className="card p-5 space-y-4">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
            Business Owner
          </h2>
          <p className="text-xs text-zinc-500">
            The owner receives the PDF by email and a summary on WhatsApp.
          </p>
          <Field label="Owner Name" value={form.owner_name ?? ""} onChange={set("owner_name")} />
          <Field
            label="Owner Email"
            type="email"
            value={form.owner_email ?? ""}
            onChange={set("owner_email")}
          />
          <Field
            label="WhatsApp Number"
            value={form.owner_whatsapp ?? ""}
            onChange={set("owner_whatsapp")}
            placeholder="+27800000000"
            hint="International format with country code, e.g. +27800000000"
          />
        </div>

        {/* Bookkeeper */}
        <div className="card p-5 space-y-4">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
            Bookkeeper
          </h2>
          <Field label="Bookkeeper Name" value={form.bookkeeper_name ?? ""} onChange={set("bookkeeper_name")} />
          <Field
            label="Bookkeeper Email"
            type="email"
            value={form.bookkeeper_email ?? ""}
            onChange={set("bookkeeper_email")}
          />
        </div>

        {/* Report language */}
        <div className="card p-5 space-y-4">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
            Report Language
          </h2>
          <div>
            <label className="block text-xs text-zinc-400 mb-1.5">
              Narrative language for PDF and WhatsApp reports
            </label>
            <select
              value={form.language ?? "en"}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, language: e.target.value }))
              }
              className="input-base w-full"
            >
              <option value="en">English</option>
              <option value="af">Afrikaans</option>
            </select>
          </div>
        </div>

        {/* Plan info (read-only) */}
        <div className="card p-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-3">
            Plan
          </h2>
          <div className="flex items-center justify-between">
            <span className="text-sm capitalize font-medium">{company.plan}</span>
            <span className="text-xs text-zinc-500">
              {company.plan === "starter" && "Email delivery only"}
              {company.plan === "professional" && "Email + WhatsApp delivery"}
              {company.plan === "premium" && "Email + WhatsApp + quarterly trend analysis"}
            </span>
          </div>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {saved && (
          <p className="text-emerald-400 text-sm">✓ Settings saved.</p>
        )}

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Saving…" : "Save Settings"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  hint,
}: {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-zinc-400 mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="input-base w-full"
      />
      {hint && <p className="text-xs text-zinc-600 mt-1">{hint}</p>}
    </div>
  );
}
