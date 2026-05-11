/**
 * Public page — handles /set-password?token=xxx links from welcome and reset emails.
 * No auth required.
 */
import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { confirmPasswordReset, requestPasswordReset } from "@/lib/api";
import GhostLogo from "@/components/GhostLogo";

export default function SetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  // Forgot-password request mode (no token in URL)
  const [requestEmail, setRequestEmail] = useState("");
  const [requestSent, setRequestSent] = useState(false);

  const handleSet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setError("");
    setLoading(true);
    try {
      await confirmPasswordReset(token, password);
      setDone(true);
      setTimeout(() => navigate("/login", { replace: true }), 2500);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "This link is invalid or has expired.");
    } finally {
      setLoading(false);
    }
  };

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await requestPasswordReset(requestEmail);
      setRequestSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-black px-4">
      <div className="mb-10">
        <GhostLogo size={40} showText />
      </div>

      <div className="card w-full max-w-sm p-8">
        {!token ? (
          requestSent ? (
            <div className="text-center">
              <p className="text-teal-400 font-medium mb-2">Check your inbox</p>
              <p className="text-zinc-400 text-sm">
                If that email is registered, a reset link has been sent.
              </p>
              <Link to="/login" className="mt-6 inline-block text-xs text-zinc-500 hover:text-zinc-300">
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <h2 className="font-heading text-xl font-bold mb-2">Forgot your password?</h2>
              <p className="text-zinc-400 text-sm mb-6">Enter your email and we'll send a reset link.</p>
              <form onSubmit={handleRequest} className="space-y-4">
                <input
                  type="email"
                  value={requestEmail}
                  onChange={(e) => setRequestEmail(e.target.value)}
                  className="input-base w-full"
                  placeholder="you@company.co.za"
                  required
                  autoFocus
                />
                <button type="submit" disabled={loading} className="btn-primary w-full">
                  {loading ? "Sending…" : "Send reset link"}
                </button>
              </form>
              <p className="text-center mt-4">
                <Link to="/login" className="text-xs text-zinc-500 hover:text-zinc-300">
                  Back to sign in
                </Link>
              </p>
            </>
          )
        ) : done ? (
          <div className="text-center">
            <p className="text-teal-400 font-medium mb-2">Password set!</p>
            <p className="text-zinc-400 text-sm">Redirecting you to sign in…</p>
          </div>
        ) : (
          <>
            <h2 className="font-heading text-xl font-bold mb-2">Set your password</h2>
            <p className="text-zinc-400 text-sm mb-6">Choose a strong password for your Ghost CFO account.</p>
            <form onSubmit={handleSet} className="space-y-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5">New password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-base w-full"
                  placeholder="Min. 8 characters"
                  required
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-xs text-zinc-400 mb-1.5">Confirm password</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="input-base w-full"
                  placeholder="Repeat your password"
                  required
                />
              </div>
              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? "Saving…" : "Set password and sign in"}
              </button>
            </form>
          </>
        )}
      </div>

      <p className="mt-8 text-xs text-zinc-600">Powered by Numbers10 Technology Solutions</p>
    </div>
  );
}
