import { useEffect, useState } from "react";
import axios from "axios";
import { getMe, setup2FA, confirm2FA, disableOwn2FA, changePassword } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { User } from "@/lib/types";

interface CompanySettings {
  id: string;
  name: string;
  trading_name: string | null;
  owner_name: string | null;
  owner_email: string | null;
  bookkeeper_name: string | null;
  bookkeeper_email: string | null;
  plan: string;
  language: string;
}

export default function SettingsPage() {
  const { refetch: refetchAuth } = useAuth();
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

  if (!user) {
    return <div className="text-zinc-500 text-sm">Loading…</div>;
  }

  // Staff accounts (admin/tech) have no company — show personal security only
  if (!company) {
    return (
      <div className="max-w-xl space-y-6">
        <div>
          <h1 className="font-heading text-2xl font-bold">Account Settings</h1>
          <p className="text-zinc-400 text-sm mt-1">
            Manage your password and two-factor authentication.
          </p>
        </div>
        <div className="card p-5 bg-zinc-900/50 border border-white/5">
          <p className="text-xs text-zinc-500">
            Staff accounts are not tied to a specific company. To manage client settings go to{" "}
            <strong className="text-zinc-300">Admin → Clients</strong>.
          </p>
        </div>
        <TwoFASection user={user} onUpdated={async () => { const r = await getMe(); setUser(r.data); refetchAuth(); }} />
        <ChangePasswordSection />
      </div>
    );
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
            The owner receives the monthly PDF report by email.
          </p>
          <Field label="Owner Name" value={form.owner_name ?? ""} onChange={set("owner_name")} />
          <Field
            label="Owner Email"
            type="email"
            value={form.owner_email ?? ""}
            onChange={set("owner_email")}
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
              Narrative language for PDF reports
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
              {company.plan === "starter" && "Monthly email report"}
              {company.plan === "professional" && "Monthly email report + debtor alerts"}
              {company.plan === "premium" && "Monthly report + quarterly trend analysis"}
            </span>
          </div>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}
        {saved && <p className="text-emerald-400 text-sm">✓ Settings saved.</p>}

        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Saving…" : "Save Settings"}
          </button>
        </div>
      </form>

      {/* Security section — outside the company form */}
      <TwoFASection user={user} onUpdated={async () => { const r = await getMe(); setUser(r.data); refetchAuth(); }} />
      <ChangePasswordSection />
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2FA setup section
// ---------------------------------------------------------------------------

type TwoFAStep = "idle" | "setup" | "confirming";

function TwoFASection({ user, onUpdated }: { user: User | null; onUpdated: () => void }) {
  const [step, setStep] = useState<TwoFAStep>("idle");
  const [qrData, setQrData] = useState<{ secret: string; qr_data_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [disabling, setDisabling] = useState(false);

  const startSetup = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await setup2FA();
      setQrData({ secret: res.data.secret, qr_data_uri: res.data.qr_data_uri });
      setStep("setup");
    } catch {
      setError("Failed to generate 2FA setup. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qrData) return;
    setLoading(true);
    setError("");
    try {
      await confirm2FA(qrData.secret, code.replace(/\s/g, ""));
      setStep("idle");
      setCode("");
      setQrData(null);
      onUpdated();
    } catch {
      setError("Incorrect code. Make sure your phone's time is correct and try again.");
      setCode("");
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    if (!confirm("Are you sure you want to disable two-factor authentication?")) return;
    setDisabling(true);
    try {
      await disableOwn2FA();
      onUpdated();
    } finally {
      setDisabling(false);
    }
  };

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
          Two-Factor Authentication
        </h2>
        {user?.totp_enabled && (
          <span className="text-xs text-emerald-400 font-medium">✓ Enabled</span>
        )}
      </div>

      {!user?.totp_enabled && step === "idle" && (
        <>
          <p className="text-zinc-400 text-sm">
            Add a second layer of security. You'll need an authenticator app like
            Google Authenticator or Authy.
          </p>
          <button onClick={startSetup} disabled={loading} className="btn-primary">
            {loading ? "Loading…" : "Set up 2FA"}
          </button>
        </>
      )}

      {step === "setup" && qrData && (
        <div className="space-y-4">
          <p className="text-zinc-400 text-sm">
            Scan this QR code with your authenticator app, then enter the 6-digit code to confirm.
          </p>
          <div className="flex justify-center">
            <img
              src={qrData.qr_data_uri}
              alt="2FA QR code"
              className="rounded-lg border border-white/10"
              style={{ width: 180, height: 180 }}
            />
          </div>
          <div className="bg-black/40 rounded-lg p-3">
            <p className="text-xs text-zinc-500 mb-1">Or enter this key manually:</p>
            <p className="font-mono text-xs text-zinc-300 tracking-widest break-all">{qrData.secret}</p>
          </div>
          <form onSubmit={handleConfirm} className="space-y-3">
            <input
              type="text"
              inputMode="numeric"
              maxLength={7}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input-base w-full text-center text-xl tracking-widest font-mono"
              placeholder="000 000"
              autoFocus
              required
            />
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <div className="flex gap-3">
              <button type="submit" disabled={loading} className="btn-primary flex-1">
                {loading ? "Verifying…" : "Activate 2FA"}
              </button>
              <button
                type="button"
                onClick={() => { setStep("idle"); setQrData(null); setCode(""); setError(""); }}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {user?.totp_enabled && step === "idle" && (
        <div className="space-y-3">
          <p className="text-zinc-400 text-sm">
            Your account is protected with two-factor authentication.
          </p>
          <button onClick={handleDisable} disabled={disabling} className="btn-secondary text-sm">
            {disabling ? "Disabling…" : "Disable 2FA"}
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Change password section
// ---------------------------------------------------------------------------

function ChangePasswordSection() {
  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (next !== confirm) { setError("Passwords do not match."); return; }
    if (next.length < 8) { setError("Password must be at least 8 characters."); return; }
    setError("");
    setLoading(true);
    try {
      await changePassword(current, next);
      setDone(true);
      setCurrent(""); setNext(""); setConfirm("");
      setTimeout(() => { setDone(false); setOpen(false); }, 2000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to change password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">Password</h2>
        <button onClick={() => setOpen((o) => !o)} className="text-xs text-zinc-400 hover:text-white">
          {open ? "Cancel" : "Change password"}
        </button>
      </div>
      {open && (
        <form onSubmit={handleSubmit} className="space-y-3">
          <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)}
            className="input-base w-full" placeholder="Current password" required />
          <input type="password" value={next} onChange={(e) => setNext(e.target.value)}
            className="input-base w-full" placeholder="New password (min. 8 characters)" required />
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
            className="input-base w-full" placeholder="Confirm new password" required />
          {error && <p className="text-red-400 text-xs">{error}</p>}
          {done && <p className="text-emerald-400 text-xs">✓ Password changed.</p>}
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Saving…" : "Update password"}
          </button>
        </form>
      )}
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
