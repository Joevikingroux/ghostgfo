import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { login, verify2FA, getMe } from "@/lib/api";

type Step = "credentials" | "2fa";

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const paymentSuccess = searchParams.get("payment") === "success";
  const sessionExpired = searchParams.get("reason") === "timeout";

  const [step, setStep] = useState<Step>("credentials");
  const [partialToken, setPartialToken] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      if (res.data.requires_2fa && res.data.partial_token) {
        setPartialToken(res.data.partial_token);
        setStep("2fa");
      } else {
        await redirectAfterLogin();
      }
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  };

  const handle2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await verify2FA(partialToken, code.replace(/\s/g, ""));
      await redirectAfterLogin();
    } catch {
      setError("Incorrect authentication code. Try again.");
      setCode("");
    } finally {
      setLoading(false);
    }
  };

  const redirectAfterLogin = async () => {
    const me = await getMe();
    if (me.data.must_change_password) {
      navigate("/change-password", { replace: true });
    } else {
      navigate("/dashboard", { replace: true });
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-black px-4">
      <div className="mb-10 text-center">
        <h1 className="font-heading text-4xl font-bold brand-text mb-2">Ghost CFO</h1>
        <p className="text-zinc-500 text-sm">AI-powered financial insight for South African SMBs</p>
      </div>

      {paymentSuccess && (
        <div className="w-full max-w-sm mb-4 rounded-lg bg-teal-500/10 border border-teal-500/30 px-4 py-3">
          <p className="text-teal-400 text-sm font-medium">Payment successful — your account is active!</p>
          <p className="text-zinc-400 text-xs mt-1">Log in below with the email and password you used during signup.</p>
        </div>
      )}

      {sessionExpired && (
        <div className="w-full max-w-sm mb-4 rounded-lg bg-amber-500/10 border border-amber-500/30 px-4 py-3">
          <p className="text-amber-400 text-sm font-medium">Session expired due to inactivity.</p>
        </div>
      )}

      <div className="card w-full max-w-sm p-8">
        {step === "credentials" ? (
          <>
            <h2 className="font-heading text-xl font-bold mb-6">Sign in</h2>
            <form onSubmit={handleCredentials} className="space-y-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5">Email address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-base w-full"
                  placeholder="you@company.co.za"
                  required
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-base w-full"
                  placeholder="••••••••"
                  required
                />
              </div>
              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3">
                  <p className="text-red-400 text-sm font-medium">{error}</p>
                </div>
              )}
              <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
                {loading ? "Signing in…" : "Sign in"}
              </button>
            </form>
            <p className="text-center mt-4">
              <Link to="/forgot-password" className="text-xs text-zinc-500 hover:text-teal-400 transition-colors">
                Forgot your password?
              </Link>
            </p>
          </>
        ) : (
          <>
            <button
              onClick={() => { setStep("credentials"); setError(""); setCode(""); }}
              className="text-xs text-zinc-500 hover:text-zinc-300 mb-5 flex items-center gap-1"
            >
              ← Back
            </button>
            <h2 className="font-heading text-xl font-bold mb-2">Two-factor authentication</h2>
            <p className="text-zinc-400 text-sm mb-6">
              Open your authenticator app and enter the 6-digit code.
            </p>
            <form onSubmit={handle2FA} className="space-y-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5">Authentication code</label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9 ]*"
                  maxLength={7}
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="input-base w-full text-center text-2xl tracking-widest font-mono"
                  placeholder="000 000"
                  required
                  autoFocus
                />
              </div>
              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3">
                  <p className="text-red-400 text-sm font-medium">{error}</p>
                </div>
              )}
              <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
                {loading ? "Verifying…" : "Verify"}
              </button>
            </form>
          </>
        )}
      </div>

      <p className="mt-8 text-xs text-zinc-600">
        Powered by Numbers10 Technology Solutions
      </p>
    </div>
  );
}
