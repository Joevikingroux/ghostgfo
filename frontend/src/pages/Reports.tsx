import { useEffect, useState } from "react";
import { getReports, triggerPdfDownload, sendReportEmail } from "@/lib/api";
import { formatPeriod } from "@/lib/format";
import type { ReportListItem } from "@/lib/types";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [sendingEmail, setSendingEmail] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean }>({ msg: "", ok: true });

  useEffect(() => {
    getReports()
      .then((r) => setReports(r.data))
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async (r: ReportListItem) => {
    setDownloading(r.id);
    try {
      const filename = `ghostcfo_report_${r.period_year}-${String(r.period_month).padStart(2, "0")}.pdf`;
      await triggerPdfDownload(r.id, filename);
    } finally {
      setDownloading(null);
    }
  };

  const handleSendEmail = async (r: ReportListItem) => {
    setSendingEmail(r.id);
    try {
      const res = await sendReportEmail(r.id);
      showToast(`Email sent to ${res.data.to}`, true);
      setReports((prev) =>
        prev.map((x) => (x.id === r.id ? { ...x, email_sent: true } : x))
      );
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast(detail ?? "Email failed — check server logs.", false);
    } finally {
      setSendingEmail(null);
    }
  };

  const showToast = (msg: string, ok: boolean) => {
    setToast({ msg, ok });
    setTimeout(() => setToast({ msg: "", ok: true }), 4000);
  };

  if (loading) return <div className="text-zinc-500 text-sm">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Reports</h1>
        <p className="text-zinc-400 text-sm mt-1">
          All generated financial reports — download as PDF or re-send by email.
        </p>
      </div>

      {toast.msg && (
        <div
          className={`text-sm px-4 py-3 rounded-lg border ${
            toast.ok
              ? "bg-emerald-900 border-emerald-700 text-emerald-200"
              : "bg-red-950 border-red-800 text-red-300"
          }`}
        >
          {toast.msg}
        </div>
      )}

      {reports.length === 0 ? (
        <div className="card p-10 text-center text-zinc-500 text-sm">
          No reports yet. Upload your Pastel exports to generate your first report.
        </div>
      ) : (
        <div className="space-y-2">
          {reports.map((r) => (
            <div key={r.id} className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">
                    {formatPeriod(r.period_month, r.period_year)}
                  </div>
                  <div className="text-xs text-zinc-500 mt-0.5">
                    {r.generated_at
                      ? `Generated ${new Date(r.generated_at).toLocaleDateString("en-ZA")}`
                      : "Generating…"}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {r.health_rating && (
                    <div className="text-right hidden sm:block">
                      <div className="font-heading text-lg font-bold brand-text">
                        {r.health_score}/100
                      </div>
                      <div className="text-xs text-zinc-500 capitalize">{r.health_rating}</div>
                    </div>
                  )}

                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      r.email_sent ? "bg-emerald-950 text-emerald-400" : "bg-zinc-800 text-zinc-500"
                    }`}
                  >
                    {r.email_sent ? "✓" : "○"} Email
                  </span>

                  <div className="flex gap-2">
                    {r.pdf_ready ? (
                      <button
                        onClick={() => handleDownload(r)}
                        disabled={downloading === r.id}
                        className="btn-primary text-xs px-3 py-1.5"
                      >
                        {downloading === r.id ? "…" : "Download PDF"}
                      </button>
                    ) : (
                      <span className="text-xs text-zinc-500 px-3 py-1.5">Generating…</span>
                    )}

                    {r.pdf_ready && (
                      <button
                        onClick={() => handleSendEmail(r)}
                        disabled={sendingEmail === r.id}
                        title="Re-send report PDF by email"
                        className="btn-ghost text-xs px-3 py-1.5 border border-surface-border"
                      >
                        {sendingEmail === r.id ? "…" : "Send Email"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
