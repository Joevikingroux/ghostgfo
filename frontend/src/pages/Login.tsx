import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/lib/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-black px-4">
      {/* Logo */}
      <div className="mb-10 text-center">
        <h1 className="font-heading text-4xl font-bold brand-text mb-2">Ghost CFO</h1>
        <p className="text-zinc-500 text-sm">AI-powered financial insight for South African SMBs</p>
      </div>

      {/* Card */}
      <div className="card w-full max-w-sm p-8">
        <h2 className="font-heading text-xl font-bold mb-6">Sign in</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
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
            <p className="text-red-400 text-xs">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full mt-2"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>

      <p className="mt-8 text-xs text-zinc-600">
        Powered by Numbers10 Technology Solutions
      </p>
    </div>
  );
}
