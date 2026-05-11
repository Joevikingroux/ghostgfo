import { useEffect, useRef, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { logout, getCompany } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import GhostLogo from "@/components/GhostLogo";
import type { SystemStatus } from "@/lib/types";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "Upload Files" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

const INACTIVITY_MS = 5 * 60 * 1000; // 5 minutes

// ---------------------------------------------------------------------------
// System status modal (admin double-click logo)
// ---------------------------------------------------------------------------

function StatusModal({ onClose }: { onClose: () => void }) {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    axios.get<SystemStatus>("/api/agent/system-status", { withCredentials: true })
      .then((r) => setStatus(r.data))
      .catch(() => setError(true));
  }, []);

  const LABELS: Record<keyof SystemStatus, string> = {
    database: "PostgreSQL Database",
    redis: "Redis / Celery",
    payfast: "PayFast",
    resend: "Resend (Email)",
    openrouter: "OpenRouter (LLM)",
    whatsapp: "WhatsApp",
    agent_key: "Agent Encryption Key",
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm bg-zinc-900 border border-white/10 rounded-xl p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-heading font-bold text-sm uppercase tracking-wider text-zinc-300">System Status</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-white text-lg leading-none">×</button>
        </div>

        {error && <p className="text-red-400 text-sm">Failed to fetch status.</p>}
        {!status && !error && <p className="text-zinc-500 text-sm">Checking…</p>}

        {status && (
          <div className="space-y-2">
            {(Object.keys(LABELS) as (keyof SystemStatus)[]).map((key) => {
              const check = status[key];
              return (
                <div key={key} className="flex items-center justify-between gap-3 py-1.5 border-b border-white/5 last:border-0">
                  <span className="text-sm text-zinc-300">{LABELS[key]}</span>
                  <span className={`text-xs ${check.ok ? "text-emerald-400" : "text-red-400"}`}>
                    {check.ok ? "✓" : "✗"} {check.message}
                  </span>
                </div>
              );
            })}
          </div>
        )}
        <p className="text-xs text-zinc-600 mt-4 text-center">Double-click the logo to open this panel</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2FA reminder banner
// ---------------------------------------------------------------------------

const BANNER_DISMISSED_KEY = "gcfo_2fa_banner_dismissed";

function TwoFABanner() {
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem(BANNER_DISMISSED_KEY) === "1"
  );

  const dismiss = () => {
    sessionStorage.setItem(BANNER_DISMISSED_KEY, "1");
    setDismissed(true);
  };

  if (dismissed) return null;

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center justify-between gap-4">
      <p className="text-amber-300 text-xs">
        <span className="font-semibold">Secure your account:</span>{" "}
        Two-factor authentication is not enabled.{" "}
        <Link to="/settings" className="underline hover:text-amber-200">
          Set up 2FA in Settings
        </Link>{" "}
        to protect your financial data.
      </p>
      <button
        onClick={dismiss}
        className="text-amber-500 hover:text-amber-300 text-lg leading-none shrink-0"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export default function Layout() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [statusOpen, setStatusOpen] = useState(false);
  const inactivityTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-logout after INACTIVITY_MS of no user interaction
  useEffect(() => {
    const resetTimer = () => {
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
      inactivityTimer.current = setTimeout(async () => {
        await logout().catch(() => {});
        window.location.href = "/login?reason=timeout";
      }, INACTIVITY_MS);
    };

    const events = ["mousemove", "mousedown", "keydown", "touchstart", "scroll"];
    events.forEach((e) => document.addEventListener(e, resetTimer, { passive: true }));
    resetTimer();

    return () => {
      events.forEach((e) => document.removeEventListener(e, resetTimer));
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    };
  }, []);

  // Redirect owner to /setup on first login if company profile is incomplete
  useEffect(() => {
    if (user?.role === "owner" && user.company_id && location.pathname !== "/setup") {
      getCompany(user.company_id).then((res) => {
        if (!res.data.industry) navigate("/setup", { replace: true });
      }).catch(() => {});
    }
  }, [user, location.pathname, navigate]);

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  const nav = user?.role === "admin"
    ? [...NAV, { to: "/admin", label: "Admin" }]
    : NAV;

  return (
    <div className="min-h-screen flex flex-col bg-black">
      {statusOpen && user?.role === "admin" && (
        <StatusModal onClose={() => setStatusOpen(false)} />
      )}

      {/* 2FA reminder banner — shown to all non-admin users who haven't enabled 2FA */}
      {user && user.role !== "admin" && !user.totp_enabled && (
        <TwoFABanner />
      )}

      {/* Top nav */}
      <header className="border-b border-surface-border px-6 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-8">
          <span onDoubleClick={() => user?.role === "admin" && setStatusOpen(true)} className="cursor-default select-none">
            <GhostLogo size={30} showText textSize="text-lg" />
          </span>
          <nav className="flex items-center gap-1">
            {nav.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  location.pathname.startsWith(n.to)
                    ? "bg-surface-card text-white"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                {n.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-500">{user?.email}</span>
          <button onClick={handleLogout} className="btn-ghost text-xs">
            Sign out
          </button>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-border px-6 py-3 text-center text-xs text-zinc-600">
        Powered by Numbers10 Technology Solutions &nbsp;·&nbsp; numbers10.co.za
      </footer>
    </div>
  );
}
