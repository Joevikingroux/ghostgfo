import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createUpload, getMe, getCompany } from "@/lib/api";
import UploadDropzone from "@/components/UploadDropzone";
import type { Company } from "@/lib/types";

const CURRENT_YEAR = new Date().getFullYear();
const CURRENT_MONTH = new Date().getMonth() + 1;

// ── How-to guide component ─────────────────────────────────────────────────

interface Step {
  action: string;
  detail?: string;
}

interface ReportGuide {
  name: string;
  steps: Step[];
}

function HowToGuide({ guides, software }: { guides: ReportGuide[]; software: string }) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);

  return (
    <div className="rounded-lg border border-surface-border bg-black/30">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <span className="flex items-center gap-2 text-xs font-medium text-zinc-400">
          <span className="text-brand-teal">?</span>
          How to export these files from {software}
        </span>
        <span className="text-zinc-600 text-xs">{open ? "▲ Hide" : "▼ Show"}</span>
      </button>

      {open && (
        <div className="border-t border-surface-border">
          <div className="flex overflow-x-auto gap-1 px-4 pt-3 pb-0">
            {guides.map((g, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setActive(i)}
                className={`shrink-0 px-3 py-1.5 rounded-t text-xs font-medium border-b-2 transition-colors ${
                  active === i
                    ? "border-brand-teal text-white bg-surface-card"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {g.name}
              </button>
            ))}
          </div>
          <div className="px-4 py-4 space-y-2">
            {guides[active].steps.map((step, i) => (
              <div key={i} className="flex gap-3">
                <span className="mt-0.5 shrink-0 w-5 h-5 rounded-full bg-surface-card border border-surface-border text-xs flex items-center justify-center text-brand-teal font-bold">
                  {i + 1}
                </span>
                <div>
                  <p className="text-sm text-zinc-200">{step.action}</p>
                  {step.detail && <p className="text-xs text-zinc-500 mt-0.5">{step.detail}</p>}
                </div>
              </div>
            ))}
            <p className="text-xs text-zinc-600 pt-2 border-t border-surface-border mt-3">
              Tip: Save the file anywhere on your computer, then drag it into the upload box below.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Guide data ─────────────────────────────────────────────────────────────

const ACCOUNTING_GUIDES: ReportGuide[] = [
  {
    name: "Income Statement",
    steps: [
      { action: "Open Sage Pastel Partner." },
      { action: "Go to View → General Ledger → Income Statement.", detail: "In older versions: Reports → Financial Statements → Income Statement." },
      { action: "Set the period to the month you are reporting on.", detail: "Use From Period and To Period — both set to the same month-end period." },
      { action: "Click Print or Preview to open the report." },
      { action: "Click Export (or right-click → Export to Excel).", detail: "Select Excel (.xlsx) or CSV." },
      { action: "Save the file and upload it here." },
    ],
  },
  {
    name: "Balance Sheet",
    steps: [
      { action: "Open Sage Pastel Partner." },
      { action: "Go to View → General Ledger → Balance Sheet.", detail: "In older versions: Reports → Financial Statements → Balance Sheet." },
      { action: "Set the period to the last period of the reporting month." },
      { action: "Click Print or Preview." },
      { action: "Click Export → select Excel or CSV." },
      { action: "Save the file and upload it here." },
    ],
  },
  {
    name: "Debtor Age Analysis",
    steps: [
      { action: "Open Sage Pastel Partner." },
      { action: "Go to View → Customers → Age Analysis.", detail: "May also be under Reports → Debtors → Age Analysis." },
      { action: "Set the date to the last day of the reporting month.", detail: "e.g. for October 2025, set date to 31 October 2025." },
      { action: "Leave the customer filter blank to include all debtors." },
      { action: "Click Print or Preview." },
      { action: "Click Export → select CSV or Excel." },
      { action: "Save the file and upload it here." },
    ],
  },
  {
    name: "Creditor Age Analysis",
    steps: [
      { action: "Open Sage Pastel Partner." },
      { action: "Go to View → Suppliers → Age Analysis.", detail: "May also appear as Reports → Creditors → Age Analysis." },
      { action: "Set the date to the last day of the reporting month." },
      { action: "Leave the supplier filter blank to include all creditors." },
      { action: "Click Print or Preview." },
      { action: "Click Export → select CSV or Excel." },
      { action: "Save the file and upload it here." },
    ],
  },
];

const PAYROLL_GUIDES: ReportGuide[] = [
  {
    name: "Payroll Summary",
    steps: [
      { action: "Open Sage Pastel Payroll." },
      { action: "Go to Reports → Payroll Reports → Payroll Summary.", detail: "May also be under Reports → Summary Reports." },
      { action: "Select the payroll period for the reporting month.", detail: "If weekly, include all periods in the month." },
      { action: "Leave the employee filter set to All Employees." },
      { action: "Click Print or Preview." },
      { action: "Click the Export icon and choose Excel or CSV." },
      { action: "Save the file and upload it here." },
    ],
  },
  {
    name: "Employee Cost Report",
    steps: [
      { action: "Open Sage Pastel Payroll." },
      { action: "Go to Reports → Payroll Reports → Employee Cost Report.", detail: "May also appear as Cost to Company or Employer Cost Report." },
      { action: "Select the payroll period for the reporting month." },
      { action: "Ensure employer contributions (UIF, SDL) are included." },
      { action: "Click Print or Preview." },
      { action: "Click Export → select Excel or CSV." },
      { action: "Save the file and upload it here." },
    ],
  },
  {
    name: "Leave Liability",
    steps: [
      { action: "Open Sage Pastel Payroll." },
      { action: "Go to Reports → Leave Reports → Leave Liability Report.", detail: "May be listed as Leave Balances or Leave Provision." },
      { action: "Set the date to the last day of the reporting month." },
      { action: "Select Annual Leave, or leave on All to include all leave types." },
      { action: "Click Print or Preview." },
      { action: "Click Export → select Excel or CSV." },
      { action: "Save the file and upload it here." },
    ],
  },
];

// ── Evolution upload form (payroll only) ───────────────────────────────────

function EvolutionUploadForm() {
  const navigate = useNavigate();
  const [month, setMonth] = useState(CURRENT_MONTH);
  const [year, setYear] = useState(CURRENT_YEAR);
  const [files, setFiles] = useState<Record<string, File | null>>({
    payroll_summary: null,
    payroll_employee_cost: null,
    payroll_leave: null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const setFile = (key: string) => (file: File) =>
    setFiles((prev) => ({ ...prev, [key]: file }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const fd = new FormData();
    fd.append("period_month", String(month));
    fd.append("period_year", String(year));
    for (const [key, f] of Object.entries(files)) {
      if (f) fd.append(key, f, f.name);
    }
    try {
      await createUpload(fd);
      navigate("/reports");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed. Please try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Upload Payroll Exports</h1>
        <p className="text-zinc-400 text-sm mt-1">
          Your financial data is pulled automatically from Pastel Evolution on the 1st of each month.
          Upload your Sage Pastel Payroll exports below to complete the monthly report.
        </p>
      </div>

      {/* Evolution data source notice */}
      <div className="card p-4 flex gap-3 items-start border-brand-teal/30">
        <div className="mt-0.5 w-8 h-8 rounded-full bg-brand-teal/10 flex items-center justify-center shrink-0">
          <span className="text-brand-teal text-sm font-bold">✓</span>
        </div>
        <div>
          <p className="text-sm font-medium text-white">Pastel Evolution — fully automatic</p>
          <p className="text-xs text-zinc-400 mt-0.5">
            Revenue, costs, debtors, creditors, and cash data are pulled automatically
            from your Pastel Evolution system on the 1st of each month. No manual export needed.
            You will receive a reminder email when your accounting data is ready and payroll is required.
          </p>
          <p className="text-xs text-zinc-500 mt-1.5">
            Payroll is managed by Sage Pastel Payroll (a separate product) and must be
            uploaded manually below. Once uploaded, your complete report will be generated
            and emailed to the business owner automatically.
          </p>
        </div>
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
              <select value={month} onChange={(e) => setMonth(Number(e.target.value))} className="input-base w-full">
                {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div className="w-28">
              <label className="block text-xs text-zinc-400 mb-1.5">Year</label>
              <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} min={2020} max={2099} className="input-base w-full" />
            </div>
          </div>
        </div>

        {/* Payroll files */}
        <div className="card p-5 space-y-5">
          <div>
            <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
              Payroll Exports <span className="text-zinc-500 font-normal normal-case">(recommended)</span>
            </h2>
            <p className="text-xs text-zinc-500 mt-1">
              Upload your Sage Pastel Payroll exports to include staff cost analysis,
              leave liability warnings, and payroll cash cover checks in the report.
              You can also click Generate without payroll files — the report will use
              accounting data only.
            </p>
          </div>
          <HowToGuide guides={PAYROLL_GUIDES} software="Sage Pastel Payroll" />
          <UploadDropzone label="Payroll Summary" description="Per-employee gross pay, PAYE, UIF, SDL, and net pay" file={files.payroll_summary} onFile={setFile("payroll_summary")} />
          <UploadDropzone label="Employee Cost Report" description="Full employer cost breakdown per employee including UIF & SDL" file={files.payroll_employee_cost} onFile={setFile("payroll_employee_cost")} />
          <UploadDropzone label="Leave Liability Report" description="Outstanding annual leave balances and rand value per employee" file={files.payroll_leave} onFile={setFile("payroll_leave")} />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <div className="flex items-center justify-between">
          <p className="text-xs text-zinc-500">
            At least one payroll file is recommended. You can upload without payroll
            — the report will include accounting data only.
          </p>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? "Uploading…" : "Upload Payroll →"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Partner upload form (all files) ───────────────────────────────────────

function PartnerUploadForm() {
  const navigate = useNavigate();
  const [month, setMonth] = useState(CURRENT_MONTH);
  const [year, setYear] = useState(CURRENT_YEAR);
  const [files, setFiles] = useState<Record<string, File | null>>({
    income_statement: null, balance_sheet: null, debtors_age: null,
    creditors_age: null, payroll_summary: null, payroll_employee_cost: null, payroll_leave: null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const setFile = (key: string) => (file: File) =>
    setFiles((prev) => ({ ...prev, [key]: file }));

  const canSubmit = files.income_statement && files.balance_sheet && files.debtors_age;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setError("");
    setSubmitting(true);
    const fd = new FormData();
    fd.append("period_month", String(month));
    fd.append("period_year", String(year));
    for (const [key, f] of Object.entries(files)) {
      if (f) fd.append(key, f, f.name);
    }
    try {
      await createUpload(fd);
      navigate("/reports");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed. Please try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Upload Monthly Files</h1>
        <p className="text-zinc-400 text-sm mt-1">
          Export your reports from Sage Pastel and upload them here. The three
          accounting files are required; payroll files are optional but recommended.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card p-5">
          <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-4">
            Reporting Period
          </h2>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs text-zinc-400 mb-1.5">Month</label>
              <select value={month} onChange={(e) => setMonth(Number(e.target.value))} className="input-base w-full">
                {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
              </select>
            </div>
            <div className="w-28">
              <label className="block text-xs text-zinc-400 mb-1.5">Year</label>
              <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} min={2020} max={2099} className="input-base w-full" />
            </div>
          </div>
        </div>

        <div className="card p-5 space-y-5">
          <div>
            <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
              Accounting Exports <span className="text-zinc-500 font-normal normal-case">(required)</span>
            </h2>
            <p className="text-xs text-zinc-500 mt-1">Export these four reports from Sage Pastel Partner at month end.</p>
          </div>
          <HowToGuide guides={ACCOUNTING_GUIDES} software="Sage Pastel Partner" />
          <UploadDropzone label="Income Statement" description="Monthly income statement — all revenue and expense lines" file={files.income_statement} required onFile={setFile("income_statement")} />
          <UploadDropzone label="Balance Sheet" description="Balance sheet at month end — assets, liabilities, equity" file={files.balance_sheet} required onFile={setFile("balance_sheet")} />
          <UploadDropzone label="Debtor Age Analysis" description="List of customers who owe you money, aged by days outstanding" file={files.debtors_age} required onFile={setFile("debtors_age")} />
          <UploadDropzone label="Creditor Age Analysis" description="List of suppliers you owe money to (optional but recommended)" file={files.creditors_age} onFile={setFile("creditors_age")} />
        </div>

        <div className="card p-5 space-y-5">
          <div>
            <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider">
              Payroll Exports <span className="text-zinc-500 font-normal normal-case">(recommended)</span>
            </h2>
            <p className="text-xs text-zinc-500 mt-1">
              Upload payroll data to enable staff cost analysis, leave liability warnings,
              and payroll cash cover checks in your report.
            </p>
          </div>
          <HowToGuide guides={PAYROLL_GUIDES} software="Sage Pastel Payroll" />
          <UploadDropzone label="Payroll Summary" description="Per-employee gross pay, PAYE, UIF, SDL, and net pay" file={files.payroll_summary} onFile={setFile("payroll_summary")} />
          <UploadDropzone label="Employee Cost Report" description="Full employer cost breakdown per employee including UIF & SDL" file={files.payroll_employee_cost} onFile={setFile("payroll_employee_cost")} />
          <UploadDropzone label="Leave Liability Report" description="Outstanding annual leave balances and rand value per employee" file={files.payroll_leave} onFile={setFile("payroll_leave")} />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <div className="flex items-center justify-between">
          <p className="text-xs text-zinc-500">* Income statement, balance sheet, and debtor age are required</p>
          <button type="submit" disabled={!canSubmit || submitting} className="btn-primary">
            {submitting ? "Uploading…" : "Generate Report →"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Main page — detects data source and renders correct form ───────────────

export default function UploadPage() {
  const [dataSource, setDataSource] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then((r) => r.data.company_id ? getCompany(r.data.company_id) : null)
      .then((r) => setDataSource(r ? r.data.data_source : "partner"))
      .catch(() => setDataSource("partner"));
  }, []);

  if (dataSource === null) {
    return <div className="text-zinc-500 text-sm">Loading…</div>;
  }

  return dataSource === "evolution" ? <EvolutionUploadForm /> : <PartnerUploadForm />;
}
