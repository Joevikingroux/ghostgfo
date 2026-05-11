/**
 * Authenticated page — shown after login when must_change_password is true.
 * User cannot navigate elsewhere until they've set a new password.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { changePassword } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import GhostLogo from "@/components/GhostLogo";

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const { refetch } = useAuth();

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (next !== confirm) { setError("Passwords do not match."); return; }
    if (next.length < 8) { setError("Password must be at least 8 characters."); return; }
    setError("");
    setLoading(true);
    try {
      await changePassword(current, next);
      await refetch();
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to update password.");
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
        <h2 className="font-heading text-xl font-bold mb-2">Set your password</h2>
        <p className="text-zinc-400 text-sm mb-6">
          Your account requires a new password before you can continue.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-zinc-400 mb-1.5">Current / temporary password</label>
            <input
              type="password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              className="input-base w-full"
              placeholder="••••••••"
              required
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs text-zinc-400 mb-1.5">New password</label>
            <input
              type="password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              className="input-base w-full"
              placeholder="Min. 8 characters"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-zinc-400 mb-1.5">Confirm new password</label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="input-base w-full"
              placeholder="Repeat password"
              required
            />
          </div>
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Saving…" : "Set password and continue"}
          </button>
        </form>
      </div>

      <p className="mt-8 text-xs text-zinc-600">Powered by Numbers10 Technology Solutions</p>
    </div>
  );
}
