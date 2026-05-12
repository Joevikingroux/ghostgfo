import axios from "axios";
import type { AdminOverview, Company, CompanyAgentStatus, Metrics, Report, ReportListItem, Upload, User, UserAdminView } from "./types";

const client = axios.create({
  baseURL: "/api",
  withCredentials: true, // send httpOnly cookie automatically
});

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ---- Auth ----
export const login = (email: string, password: string) =>
  client.post<{ access_token: string; requires_2fa: boolean; partial_token: string | null }>(
    "/auth/login", { email, password }
  );

export const verify2FA = (partial_token: string, code: string) =>
  client.post<{ access_token: string }>("/auth/2fa/verify", { partial_token, code });

export const setup2FA = () =>
  client.get<{ secret: string; qr_data_uri: string; otp_uri: string }>("/auth/2fa/setup");

export const confirm2FA = (secret: string, code: string) =>
  client.post("/auth/2fa/confirm", { secret, code });

export const disableOwn2FA = () => client.delete("/auth/2fa");

export const changePassword = (current_password: string, new_password: string) =>
  client.post("/auth/change-password", { current_password, new_password });

export const requestPasswordReset = (email: string) =>
  client.post("/auth/reset-password/request", { email });

export const confirmPasswordReset = (token: string, new_password: string) =>
  client.post("/auth/reset-password/confirm", { token, new_password });

export const adminReset2FA = (user_id: string) =>
  client.post(`/auth/2fa/reset/${user_id}`);

export const logout = () => client.post("/auth/logout");

export const getMe = () => client.get<User>("/auth/me");

// ---- Admin users ----
export const getUsers = () => client.get<UserAdminView[]>("/users");

export const createUser = (data: {
  email: string; full_name?: string; role: string; company_id?: string | null;
}) => client.post<UserAdminView>("/users", data);

export const updateUser = (user_id: string, data: {
  email?: string; full_name?: string; role?: string; company_id?: string | null; active?: boolean;
}) => client.patch<UserAdminView>(`/users/${user_id}`, data);

export const deactivateUser = (user_id: string) =>
  client.patch(`/users/${user_id}/deactivate`);

export const activateUser = (user_id: string) =>
  client.patch(`/users/${user_id}/activate`);

export const adminResetPassword = (user_id: string) =>
  client.post<{ ok: boolean; email_sent: boolean }>(`/users/${user_id}/reset-password`);

// ---- Companies ----
export const getCompanies = () => client.get<Company[]>("/companies");

export const getCompany = (id: string) => client.get<Company>(`/companies/${id}`);

export const createCompany = (data: Partial<Company>) =>
  client.post<Company>("/companies", data);

export const updateCompany = (id: string, data: Partial<Company>) =>
  client.patch<Company>(`/companies/${id}`, data);

// ---- Uploads ----
export const createUpload = (formData: FormData) =>
  client.post<Upload>("/uploads", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getUploads = () => client.get<Upload[]>("/uploads");

export const getUpload = (id: string) => client.get<Upload>(`/uploads/${id}`);

// ---- Reports ----
export const getReports = () => client.get<ReportListItem[]>("/reports");

export const getReport = (id: string) => client.get<Report>(`/reports/${id}`);

export const deleteReport = (id: string) =>
  client.delete(`/reports/${id}`);

export const getReportStatus = (id: string) =>
  client.get<{ id: string; generated: boolean; pdf_ready: boolean; health_score: number | null }>(
    `/reports/${id}/status`
  );

export const downloadReport = (id: string) =>
  client.get(`/reports/${id}/download`, { responseType: "blob" });

export const sendReportEmail = (id: string, extraEmails: string[] = []) =>
  client.post<{ ok: boolean; to: string[] }>(`/reports/${id}/send-email`, {
    extra_emails: extraEmails,
  });


export const getRevenueTrends = () =>
  client.get<Array<{
    period_month: number;
    period_year: number;
    revenue: number;
    gross_profit: number;
  }>>("/reports/trends/revenue");

// ---- Evolution agents ----
export const reactivateAgent = (agent_id: string) =>
  client.post(`/agent/agents/${agent_id}/reactivate`);

export const deactivateAgent = (agent_id: string) =>
  client.post(`/agent/agents/${agent_id}/deactivate`);

export const deleteAgent = (agent_id: string) =>
  client.delete(`/agent/agents/${agent_id}`);

export const forceSyncAgent = (agent_id: string, month: number, year: number) =>
  client.post<{ ok: boolean; queued_month: number; queued_year: number }>(
    `/agent/agents/${agent_id}/force-sync`,
    { month, year },
  );

export const getMyAgentStatus = () =>
  client.get<CompanyAgentStatus>("/agent/company-status");

export const requestCompanySync = (month: number, year: number) =>
  client.post<{ ok: boolean }>("/agent/company-sync", { month, year });

// ---- Admin overview ----
export const getAdminOverview = () => client.get<AdminOverview>("/admin/overview");

// Helper: trigger a PDF download in the browser
export const triggerPdfDownload = async (reportId: string, filename: string) => {
  const res = await downloadReport(reportId);
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};
