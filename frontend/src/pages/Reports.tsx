import { useEffect, useState } from "react";
import axios from "axios";
import { getReports, triggerPdfDownload, getMe } from "@/lib/api";
import { formatPeriod } from "@/lib/format";
import type { ReportListItem, User } from "@/lib/types";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [redelivering, setRedelivering] = useState<string | null>(null);
  const [toast, setToast] = useState("");

  useEffect(() => {
    Promise.all([getReports(), getMe()])
      .then(([r, u]) => {
        setReports(r.data);
        setUser(u.data);
      })
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

  const handleRedeliver = async (r: ReportListItem) => {
    setRedelivering(r.id);
    try {
      await axios.post(`/api/reports/${r.id}/deliver`, {}, { withCredentials: true });
      showToast("Delivery queued — email and WhatsApp will be sent shortly.");
    } catch {
      showToast("Re-delivery failed. Check admin logs.");
    } finally {
      setRedelivering(null);
    }
  };

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  };

  if (loading) return <div className="text-zinc-500 text-sm">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Reports</h1>
        <p className="text-zinc-400 text-sm mt-1">
          All generated financial reports — download as PDF, view delivery status, or re-send.
        </p>
      </div>

      {toast && (
        <div className="bg-emerald-900 border border-emerald-700 text-emerald-200 text-sm px-4 py-3 rounded-lg">
          {toast}
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

                  {/* Delivery badges */}
                  <div className="flex gap-1.5">
                    <DeliveryBadge sent={r.email_sent} label="Email" />
                    <DeliveryBadge sent={r.whatsapp_sent} label="WhatsApp" />
                  </div>

                  {/* Actions */}
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

                    {user?.role === "admin" && r.pdf_ready && (
                      <button
                        onClick={() => handleRedeliver(r)}
                        disabled={redelivering === r.id}
                        className="btn-ghost text-xs px-3 py-1.5 border border-surface-border"
                      >
                        {redelivering === r.id ? "…" : "Re-send"}
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

function DeliveryBadge({ sent, label }: { sent: boolean; label: string }) {
  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-full ${
        sent ? "bg-emerald-950 text-emerald-400" : "bg-zinc-800 text-zinc-500"
      }`}
    >
      {sent ? "✓" : "○"} {label}
    </span>
  );
}
