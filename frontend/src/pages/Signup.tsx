/**
 * Self-service signup page — user picks a plan, enters details,
 * gets redirected to PayFast to complete payment.
 * Account activates automatically after successful payment via ITN.
 */
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import GhostLogo from "@/components/GhostLogo";

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    price: 500,
    features: ["Monthly PDF report", "Email delivery", "12-month history", "Pastel Partner or Evolution"],
  },
  {
    id: "professional",
    name: "Professional",
    price: 900,
    popular: true,
    features: ["Everything in Starter", "WhatsApp delivery", "Weekly cash pulse", "Debtor alerts"],
  },
  {
    id: "premium",
    name: "Premium",
    price: 1500,
    features: ["Everything in Professional", "Quarterly trend analysis", "Anomaly alerts", "Custom commentary", "Priority support"],
  },
];

interface PayFastFields {
  [key: string]: string;
}

export default function SignupPage() {
  const [params] = useSearchParams();
  const [plan, setPlan] = useState(params.get("plan") || "professional");
  const [form, setForm] = useState({ company_name: "", owner_name: "", email: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pfData, setPfData] = useState<{ url: string; fields: PayFastFields } | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  // Auto-submit PayFast form once we have the data
  useEffect(() => {
    if (pfData && formRef.current) {
      formRef.current.submit();
    }
  }, [pfData]);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/payments/initiate", { ...form, plan });
      setPfData({ url: res.data.payfast_url, fields: res.data.fields });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  const selected = PLANS.find((p) => p.id === plan)!;

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hidden PayFast form — auto-submitted after initiate succeeds */}
      {pfData && (
        <form ref={formRef} action={pfData.url} method="POST" style={{ display: "none" }}>
          {Object.entries(pfData.fields).map(([k, v]) => (
            <input key={k} type="hidden" name={k} value={v} />
          ))}
        </form>
      )}

      {/* Nav */}
      <nav className="border-b border-white/5 px-6 h-16 flex items-center justify-between">
        <Link to="/"><GhostLogo size={32} showText /></Link>
        <Link to="/login" className="text-sm text-zinc-400 hover:text-white transition-colors">
          Already have an account? Log in
        </Link>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="text-center mb-10">
          <h1 className="font-heading text-3xl font-bold mb-2">Choose your plan</h1>
          <p className="text-zinc-400">No setup fees. Cancel anytime. Your first report arrives at month-end.</p>
        </div>

        {/* Plan selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          {PLANS.map((p) => (
            <button
              key={p.id}
              onClick={() => setPlan(p.id)}
              className={`relative text-left rounded-xl border-2 p-6 transition-all ${
                plan === p.id
                  ? "border-teal-400 bg-teal-400/5"
                  : "border-white/10 hover:border-white/30 bg-white/2"
              }`}
            >
              {p.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-bold px-3 py-1 rounded-full text-black"
                  style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}>
                  Most Popular
                </span>
              )}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="font-heading font-bold text-lg">{p.name}</p>
                  <p className="text-2xl font-bold mt-1">
                    R{p.price.toLocaleString()}
                    <span className="text-sm font-normal text-zinc-400">/mo</span>
                  </p>
                </div>
                <div className={`w-5 h-5 rounded-full border-2 mt-1 flex items-center justify-center shrink-0 ${
                  plan === p.id ? "border-teal-400 bg-teal-400" : "border-zinc-600"
                }`}>
                  {plan === p.id && <div className="w-2 h-2 rounded-full bg-black" />}
                </div>
              </div>
              <ul className="space-y-2">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-zinc-300">
                    <span className="text-teal-400 mt-0.5 shrink-0">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
            </button>
          ))}
        </div>

        {/* Signup form */}
        <div className="max-w-md mx-auto">
          <div className="rounded-xl border border-white/10 bg-white/3 p-8">
            <h2 className="font-heading font-bold text-xl mb-1">
              Get started with {selected.name}
            </h2>
            <p className="text-zinc-400 text-sm mb-6">
              R{selected.price.toLocaleString()}/month · Pay securely via PayFast
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Business / Company Name *</label>
                <input
                  required
                  value={form.company_name}
                  onChange={set("company_name")}
                  className="input-base w-full"
                  placeholder="ABC Hardware (Pty) Ltd"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Your Name *</label>
                <input
                  required
                  value={form.owner_name}
                  onChange={set("owner_name")}
                  className="input-base w-full"
                  placeholder="John Smith"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Email Address *</label>
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={set("email")}
                  className="input-base w-full"
                  placeholder="john@company.co.za"
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1">Create Password *</label>
                <div className="relative">
                  <input
                    required
                    type={showPw ? "text" : "password"}
                    value={form.password}
                    onChange={set("password")}
                    className="input-base w-full pr-14"
                    placeholder="Min. 8 characters"
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((p) => !p)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500 hover:text-white"
                  >
                    {showPw ? "Hide" : "Show"}
                  </button>
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
                {loading ? "Preparing payment…" : `Pay R${selected.price.toLocaleString()}/mo via PayFast`}
              </button>

              <p className="text-center text-xs text-zinc-500 leading-relaxed">
                You'll be redirected to PayFast to complete payment securely.
                Your account activates automatically after payment.
                Cancel anytime from your PayFast account.
              </p>
            </form>
          </div>

          <p className="text-center text-xs text-zinc-600 mt-6">
            Powered by Numbers10 Technology Solutions · numbers10.co.za
          </p>
        </div>
      </div>
    </div>
  );
}
