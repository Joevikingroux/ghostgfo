import { useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { logout, getCompany } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import GhostLogo from "@/components/GhostLogo";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "Upload Files" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

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
      {/* Top nav */}
      <header className="border-b border-surface-border px-6 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-8">
          <GhostLogo size={30} showText textSize="text-lg" />
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
