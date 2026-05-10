/**
 * First-login setup wizard — owner completes company details after payment activates account.
 * Redirects to /dashboard on completion.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { getCompany, updateCompany } from "@/lib/api";
import GhostLogo from "@/components/GhostLogo";

const INDUSTRIES = [
  "Retail",
  "Construction",
  "Manufacturing",
  "Professional Services",
  "Hospitality",
  "Healthcare",
  "Agriculture",
  "Transport & Logistics",
  "Technology",
  "Other",
];

export default function SetupPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    industry: "",
    owner_whatsapp: "",
    trading_name: "",
    vat_number: "",
    reg_number: "",
    bookkeeper_name: "",
    bookkeeper_email: "",
    data_source: "partner" as "partner" | "evolution",
    language: "en",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k: string) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.industry) { setError("Please select your industry."); return; }
    if (!user?.company_id) return;

    setLoading(true);
    setError("");
    try {
      await updateCompany(user.company_id, form);
      navigate("/dashboard");
    } catch {
      setError("Failed to save. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      <header className="border-b border-white/5 px-6 h-16 flex items-center">
        <GhostLogo size={32} showText />
      </header>

      <div className="flex-1 flex items-start justify-center px-6 py-12">
        <div className="w-full max-w-xl">
          <div className="mb-8">
            <h1 className="font-heading text-2xl font-bold mb-1">Complete your company profile</h1>
            <p className="text-zinc-400 text-sm">
              This takes 2 minutes and helps Ghost CFO personalise your reports.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="rounded-xl border border-white/10 bg-white/3 p-6 space-y-4">
              <h2 className="font-heading font-semibold text-sm text-zinc-400 uppercase tracking-wider">Business details</h2>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">Industry *</label>
                <select
                  required
                  value={form.industry}
                  onChange={set("industry")}
                  className="input-base w-full"
                >
                  <option value="">Select your industry…</option>
                  {INDUSTRIES.map((i) => (
                    <option key={i} value={i}>{i}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">Trading name (if different from registered name)</label>
                <input
                  value={form.trading_name}
                  onChange={set("trading_name")}
                  className="input-base w-full"
                  placeholder="e.g. ABC Hardware"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">VAT number</label>
                  <input
                    value={form.vat_number}
                    onChange={set("vat_number")}
                    className="input-base w-full"
                    placeholder="4XXXXXXXXX"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Registration number</label>
                  <input
                    value={form.reg_number}
                    onChange={set("reg_number")}
                    className="input-base w-full"
                    placeholder="2020/123456/07"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/3 p-6 space-y-4">
              <h2 className="font-heading font-semibold text-sm text-zinc-400 uppercase tracking-wider">Delivery & contact</h2>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">Owner WhatsApp number</label>
                <input
                  type="tel"
                  value={form.owner_whatsapp}
                  onChange={set("owner_whatsapp")}
                  className="input-base w-full"
                  placeholder="+27 82 000 0000"
                />
                <p className="text-xs text-zinc-600 mt-1">Used to send your monthly report via WhatsApp (Professional & Premium plans).</p>
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">Bookkeeper name</label>
                <input
                  value={form.bookkeeper_name}
                  onChange={set("bookkeeper_name")}
                  className="input-base w-full"
                  placeholder="Jane Smith"
                />
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">Bookkeeper email</label>
                <input
                  type="email"
                  value={form.bookkeeper_email}
                  onChange={set("bookkeeper_email")}
                  className="input-base w-full"
                  placeholder="jane@company.co.za"
                />
              </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/3 p-6 space-y-4">
              <h2 className="font-heading font-semibold text-sm text-zinc-400 uppercase tracking-wider">Pastel setup</h2>

              <div>
                <label className="block text-xs text-zinc-400 mb-3">How do you use Sage Pastel?</label>
                <div className="space-y-2">
                  {[
                    { value: "partner", label: "Pastel Partner / Xpress", desc: "I'll upload CSV/Excel exports each month" },
                    { value: "evolution", label: "Pastel Evolution", desc: "Direct SQL connection via Ghost CFO Agent on my server" },
                  ].map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-start gap-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                        form.data_source === opt.value
                          ? "border-teal-400 bg-teal-400/5"
                          : "border-white/10 hover:border-white/20"
                      }`}
                    >
                      <input
                        type="radio"
                        name="data_source"
                        value={opt.value}
                        checked={form.data_source === opt.value}
                        onChange={set("data_source")}
                        className="mt-0.5 accent-teal-400"
                      />
                      <div>
                        <p className="text-sm font-medium">{opt.label}</p>
                        <p className="text-xs text-zinc-500 mt-0.5">{opt.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-3">Preferred report language</label>
                <div className="flex gap-3">
                  {[{ value: "en", label: "English" }, { value: "af", label: "Afrikaans" }].map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-2 rounded-lg border px-4 py-3 cursor-pointer transition-colors flex-1 ${
                        form.language === opt.value
                          ? "border-teal-400 bg-teal-400/5"
                          : "border-white/10 hover:border-white/20"
                      }`}
                    >
                      <input
                        type="radio"
                        name="language"
                        value={opt.value}
                        checked={form.language === opt.value}
                        onChange={set("language")}
                        className="accent-teal-400"
                      />
                      <span className="text-sm">{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {error && (
              <p className="text-red-400 text-sm bg-red-400/10 rounded-lg px-4 py-3">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-bold text-black transition-all disabled:opacity-60"
              style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
            >
              {loading ? "Saving…" : "Complete setup and go to dashboard"}
            </button>

            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="w-full py-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Skip for now
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
