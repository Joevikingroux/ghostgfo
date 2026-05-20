import { useEffect, useState } from "react";
import { getReports, triggerPdfDownload, sendReportEmail, deleteReport, getMe } from "@/lib/api";
import { formatPeriod } from "@/lib/format";
import type { ReportListItem, User } from "@/lib/types";

type TotpAction = { kind: "download"; report: ReportListItem } | { kind: "email"; report: ReportListItem };

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [sendingEmail, setSendingEmail] = useState<string | null>(null);
  const [emailPanelId, setEmailPanelId] = useState<string | null>(null);
  const [extraEmails, setExtraEmails] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean }>({ msg: "", ok: true });

  // TOTP modal state
  const [totpAction, setTotpAction] = useState<TotpAction | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [totpError, setTotpError] = useState("");
  const [totpBusy, setTotpBusy] = useState(false);

  useEffect(() => {
    Promise.all([
      getReports().then((r) => setReports(r.data)),
      getMe().then((r) => setCurrentUser(r.data)),
    ]).finally(() => setLoading(false));
  }, []);

  const needsTotp = () => !!currentUser?.totp_enabled;

  // --- Download ---
  const handleDownload = (r: ReportListItem) => {
    if (needsTotp()) {
      setTotpAction({ kind: "download", report: r });
      setTotpCode("");
      setTotpError("");
    } else {
      execDownload(r);
    }
  };

  const execDownload = async (r: ReportListItem, code?: string) => {
    setDownloading(r.id);
    try {
      const filename = `ghostcfo_report_${r.period_year}-${String(r.period_month).padStart(2, "0")}.pdf`;
      await triggerPdfDownload(r.id, filename, code);
      setTotpAction(null);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 403) {
        setTotpError("Invalid 2FA code — please try again.");
      } else {
        showToast("Download failed — try again.", false);
        setTotpAction(null);
      }
    } finally {
      setDownloading(null);
    }
  };

  // --- Send email ---
  const openEmailPanel = (r: ReportListItem) => {
    setEmailPanelId(r.id);
    setExtraEmails("");
  };

  const handleSendEmail = (r: ReportListItem) => {
    if (needsTotp()) {
      setTotpAction({ kind: "email", report: r });
      setTotpCode("");
      setTotpError("");
    } else {
      execSendEmail(r);
    }
  };

  const execSendEmail = async (r: ReportListItem, code?: string) => {
    setSendingEmail(r.id);
    const extras = extraEmails
      .split(/[\s,;]+/)
      .map((e) => e.trim())
      .filter(Boolean);
    try {
      const res = await sendReportEmail(r.id, extras, code);
      const sent = res.data.to;
      const label = sent.length > 1 ? `${sent[0]} + ${sent.length - 1} more` : sent[0];
      showToast(`Email sent to ${label}`, true);
      setReports((prev) =>
        prev.map((x) => (x.id === r.id ? { ...x, email_sent: true } : x))
      );
      setEmailPanelId(null);
      setExtraEmails("");
      setTotpAction(null);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 403) {
        setTotpError("Invalid 2FA code — please try again.");
      } else {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        showToast(detail ?? "Email failed — check server logs.", false);
        setTotpAction(null);
      }
    } finally {
      setSendingEmail(null);
    }
  };

  // --- TOTP modal submit ---
  const handleTotpSubmit = async () => {
    if (!totpAction || !totpCode.trim()) {
      setTotpError("Enter your 6-digit code.");
      return;
    }
    setTotpBusy(true);
    setTotpError("");
    try {
      if (totpAction.kind === "download") {
        await execDownload(totpAction.report, totpCode.trim());
      } else {
        await execSendEmail(totpAction.report, totpCode.trim());
      }
    } finally {
      setTotpBusy(false);
    }
  };

  // --- Delete ---
  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await deleteReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
      showToast("Report deleted.", true);
    } catch {
      showToast("Delete failed — try again.", false);
    } finally {
      setDeleting(null);
      setConfirmDeleteId(null);
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
            <div key={r.id} className="card">
              {/* Main row */}
              <div className="flex items-center justify-between p-4">
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

                  {r.payroll_pending && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800">
                      Payroll pending
                    </span>
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
                        onClick={() =>
                          emailPanelId === r.id
                            ? setEmailPanelId(null)
                            : openEmailPanel(r)
                        }
                        className="btn-ghost text-xs px-3 py-1.5 border border-surface-border"
                      >
                        Send Email
                      </button>
                    )}

                    <button
                      onClick={() =>
                        confirmDeleteId === r.id
                          ? setConfirmDeleteId(null)
                          : setConfirmDeleteId(r.id)
                      }
                      className="btn-ghost text-xs px-3 py-1.5 border border-red-900 text-red-400 hover:bg-red-950"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>

              {/* Delete confirmation panel */}
              {confirmDeleteId === r.id && (
                <div className="border-t border-red-900/40 px-4 py-3 bg-red-950/20 flex items-center justify-between">
                  <p className="text-xs text-red-300">
                    Permanently delete this report and its PDF? This cannot be undone.
                  </p>
                  <div className="flex gap-2 ml-4 shrink-0">
                    <button
                      onClick={() => setConfirmDeleteId(null)}
                      className="btn-ghost text-xs px-3 py-1.5"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleDelete(r.id)}
                      disabled={deleting === r.id}
                      className="text-xs px-3 py-1.5 rounded bg-red-700 hover:bg-red-600 text-white font-medium"
                    >
                      {deleting === r.id ? "Deleting…" : "Yes, delete"}
                    </button>
                  </div>
                </div>
              )}

              {/* Extra recipients panel */}
              {emailPanelId === r.id && (
                <div className="border-t border-white/6 px-4 py-3 bg-zinc-900/50 space-y-2">
                  <p className="text-xs text-zinc-400">
                    Sends to the company's primary email. Add extra recipients below (comma-separated), or leave blank.
                  </p>
                  <input
                    type="text"
                    value={extraEmails}
                    onChange={(e) => setExtraEmails(e.target.value)}
                    placeholder="extra@example.com, another@example.com"
                    className="input-base w-full text-sm"
                    autoFocus
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => setEmailPanelId(null)}
                      className="btn-ghost text-xs px-3 py-1.5"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSendEmail(r)}
                      disabled={sendingEmail === r.id}
                      className="btn-primary text-xs px-3 py-1.5"
                    >
                      {sendingEmail === r.id ? "Sending…" : "Send"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 2FA confirmation modal */}
      {totpAction && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-zinc-900 border border-white/10 rounded-xl p-6 w-full max-w-sm space-y-4">
            <div>
              <h2 className="font-heading font-bold text-lg">Confirm with 2FA</h2>
              <p className="text-sm text-zinc-400 mt-1">
                {totpAction.kind === "download"
                  ? "Enter your authenticator code to download this report."
                  : "Enter your authenticator code to send this report by email."}
              </p>
            </div>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              value={totpCode}
              onChange={(e) => { setTotpCode(e.target.value.replace(/\D/g, "")); setTotpError(""); }}
              onKeyDown={(e) => e.key === "Enter" && handleTotpSubmit()}
              placeholder="000000"
              className="input-base w-full text-center text-xl tracking-widest font-mono"
              autoFocus
            />
            {totpError && (
              <p className="text-xs text-red-400">{totpError}</p>
            )}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setTotpAction(null); setTotpCode(""); setTotpError(""); }}
                className="btn-ghost text-sm px-4 py-2"
                disabled={totpBusy}
              >
                Cancel
              </button>
              <button
                onClick={handleTotpSubmit}
                disabled={totpBusy || totpCode.length < 6}
                className="btn-primary text-sm px-4 py-2"
              >
                {totpBusy ? "Verifying…" : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
