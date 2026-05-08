import axios from "axios";
import type { Company, Metrics, Report, ReportListItem, Upload, User } from "./types";

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
  client.post<{ access_token: string }>("/auth/login", { email, password });

export const logout = () => client.post("/auth/logout");

export const getMe = () => client.get<User>("/auth/me");

// ---- Companies ----
export const getCompanies = () => client.get<Company[]>("/companies");

export const createCompany = (data: Partial<Company>) =>
  client.post<Company>("/companies", data);

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

export const getReportStatus = (id: string) =>
  client.get<{ id: string; generated: boolean; pdf_ready: boolean; health_score: number | null }>(
    `/reports/${id}/status`
  );

export const downloadReport = (id: string) =>
  client.get(`/reports/${id}/download`, { responseType: "blob" });

export const getRevenueTrends = () =>
  client.get<Array<{
    period_month: number;
    period_year: number;
    revenue: number;
    gross_profit: number;
  }>>("/reports/trends/revenue");

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
