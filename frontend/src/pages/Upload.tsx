import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createUpload } from "@/lib/api";
import UploadDropzone from "@/components/UploadDropzone";

const CURRENT_YEAR = new Date().getFullYear();
const CURRENT_MONTH = new Date().getMonth() + 1;

export default function UploadPage() {
  const navigate = useNavigate();
  const [month, setMonth] = useState(CURRENT_MONTH);
  const [year, setYear] = useState(CURRENT_YEAR);
  const [files, setFiles] = useState<Record<string, File | null>>({
    income_statement: null,
    balance_sheet: null,
    debtors_age: null,
    creditors_age: null,
    payroll_summary: null,
    payroll_employee_cost: null,
    payroll_leave: null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const setFile = (key: string) => (file: File) =>
    setFiles((prev) => ({ ...prev, [key]: file }));

  const canSubmit =
    files.income_statement && files.balance_sheet && files.debtors_age;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setError("");
    setSubmitting(true);

    const fd = new FormData();
    fd.append("period_month", String(month));
    fd.append("period_year", String(year));

    const mapping: Record<string, string> = {
      income_statement: "income_statement",
      balance_sheet: "balance_sheet",
      debtors_age: "debtors_age",
      creditors_age: "creditors_age",
      payroll_summary: "payroll_summary",
      payroll_employee_cost: "payroll_employee_cost",
      payroll_leave: "payroll_leave",
    };

    for (const [key, field] of Object.entries(mapping)) {
      const f = files[key];
      if (f) fd.append(field, f, f.name);
    }

    try {
      await createUpload(fd);
      navigate("/reports");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed. Please try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  const MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
  ];

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Upload Monthly Files</h1>
        <p className="text-zinc-400 text-sm mt-1">
          Upload your Pastel Partner exports for the month. The three accounting
          files are required; payroll files are optional but recommended.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Period */}
        <div className="card p-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-4">
            Reporting Period
          </h2>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs text-zinc-400 mb-1.5">Month</label>
              <select
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                className="input-base w-full"
              >
                {MONTHS.map((m, i) => (
                  <option key={i + 1} value={i + 1}>{m}</option>
                ))}
              </select>
            </div>
            <div className="w-28">
              <label className="block text-xs text-zinc-400 mb-1.5">Year</label>
              <input
                type="number"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                min={2020}
                max={2099}
                className="input-base w-full"
              />
            </div>
          </div>
        </div>

        {/* Accounting files */}
        <div className="card p-5 space-y-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
            Accounting Exports <span className="text-zinc-500 font-normal normal-case">(required)</span>
          </h2>
          <UploadDropzone
            label="Income Statement"
            description="Monthly income statement — all revenue and expense lines"
            file={files.income_statement}
            required
            onFile={setFile("income_statement")}
          />
          <UploadDropzone
            label="Balance Sheet"
            description="Balance sheet at month end — assets, liabilities, equity"
            file={files.balance_sheet}
            required
            onFile={setFile("balance_sheet")}
          />
          <UploadDropzone
            label="Debtor Age Analysis"
            description="List of customers who owe you money, aged by days outstanding"
            file={files.debtors_age}
            required
            onFile={setFile("debtors_age")}
          />
          <UploadDropzone
            label="Creditor Age Analysis"
            description="List of suppliers you owe money to (optional)"
            file={files.creditors_age}
            onFile={setFile("creditors_age")}
          />
        </div>

        {/* Payroll files */}
        <div className="card p-5 space-y-5">
          <div>
            <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
              Payroll Exports <span className="text-zinc-500 font-normal normal-case">(recommended)</span>
            </h2>
            <p className="text-xs text-zinc-500 mt-1">
              Adding payroll files enables staff cost analysis, leave liability
              warnings, and payroll cash cover checks in your report.
            </p>
          </div>
          <UploadDropzone
            label="Payroll Summary"
            description="Per-employee gross pay, PAYE, UIF, SDL, and net pay"
            file={files.payroll_summary}
            onFile={setFile("payroll_summary")}
          />
          <UploadDropzone
            label="Employee Cost Report"
            description="Full employer cost breakdown per employee including UIF & SDL"
            file={files.payroll_employee_cost}
            onFile={setFile("payroll_employee_cost")}
          />
          <UploadDropzone
            label="Leave Liability Report"
            description="Outstanding annual leave balances and rand value per employee"
            file={files.payroll_leave}
            onFile={setFile("payroll_leave")}
          />
        </div>

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        <div className="flex items-center justify-between">
          <p className="text-xs text-zinc-500">
            * Income statement, balance sheet, and debtor age are required
          </p>
          <button
            type="submit"
            disabled={!canSubmit || submitting}
            className="btn-primary"
          >
            {submitting ? "Uploading…" : "Generate Report →"}
          </button>
        </div>
      </form>
    </div>
  );
}
