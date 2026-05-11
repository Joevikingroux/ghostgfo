import { useCallback, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthContext } from "@/lib/auth";
import { getMe } from "@/lib/api";
import type { User } from "@/lib/types";
import WebsitePage from "@/pages/Website";
import LoginPage from "@/pages/Login";
import SignupPage from "@/pages/Signup";
import SetPasswordPage from "@/pages/SetPassword";
import ChangePasswordPage from "@/pages/ChangePassword";
import DashboardPage from "@/pages/Dashboard";
import UploadPage from "@/pages/Upload";
import ReportsPage from "@/pages/Reports";
import SettingsPage from "@/pages/Settings";
import AdminPage from "@/pages/Admin";
import AdminDashboard from "@/pages/AdminDashboard";
import SetupPage from "@/pages/Setup";
import Layout from "@/components/Layout";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(() => {
    getMe()
      .then((r) => setUser(r.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { refetch(); }, [refetch]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="brand-text text-lg font-heading">Loading…</span>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  // Force password change before any other page
  if (user.must_change_password && window.location.pathname !== "/change-password") {
    return <Navigate to="/change-password" replace />;
  }

  return (
    <AuthContext.Provider value={{ user, loading, refetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public pages */}
        <Route path="/" element={<WebsitePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/set-password" element={<SetPasswordPage />} />
        <Route path="/forgot-password" element={<SetPasswordPage />} />

        {/* Authenticated: change password (outside Layout so user can't nav away) */}
        <Route
          path="/change-password"
          element={
            <RequireAuth>
              <ChangePasswordPage />
            </RequireAuth>
          }
        />

        {/* Authenticated portal */}
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/setup" element={<SetupPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/manage" element={<AdminPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
