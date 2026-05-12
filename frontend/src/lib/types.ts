export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: "owner" | "bookkeeper" | "viewer" | "admin";
  company_id: string | null;
  must_change_password: boolean;
  totp_enabled: boolean;
}

export interface UserAdminView {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  company_id: string | null;
  company_name: string | null;
  active: boolean;
  must_change_password: boolean;
  totp_enabled: boolean;
}

export interface Company {
  id: string;
  name: string;
  trading_name: string | null;
  industry: string | null;
  owner_name: string | null;
  owner_email: string | null;
  bookkeeper_name: string | null;
  bookkeeper_email: string | null;
  plan: "starter" | "professional" | "premium";
  active: boolean;
  data_source: "partner" | "evolution";
  language: string;
  plan_start_date: string | null;
}

export interface Metrics {
  company_name: string;
  period_month: number;
  period_year: number;
  revenue_current_month: number;
  revenue_previous_month: number;
  revenue_change_pct: number;
  revenue_ytd: number;
  revenue_trend: "growing" | "stable" | "declining";
  gross_profit_current: number;
  gross_margin_pct: number;
  gross_margin_prev_pct: number;
  gross_margin_trend: string;
  total_costs_current: number;
  total_costs_previous: number;
  cost_change_pct: number;
  top_cost_mover: string | null;
  top_cost_mover_change: number;
  top_cost_mover_change_pct: number;
  debtors_total: number;
  debtors_current: number;
  debtors_30_60_days: number;
  debtors_61_90_days: number;
  debtors_over_90_days: number;
  debtor_days: number;
  overdue_invoices_count: number;
  overdue_invoices_value: number;
  debtors_health: "good" | "warning" | "critical";
  worst_offenders: Array<{ name: string; overdue_value: number; worst_bucket: string }>;
  cash_balance: number;
  monthly_burn_rate: number;
  cash_runway_weeks: number;
  cash_health: "good" | "warning" | "critical";
  payroll_gross_total: number;
  payroll_net_total: number;
  payroll_employer_uif: number;
  payroll_employer_sdl: number;
  payroll_true_employer_cost: number;
  payroll_headcount: number;
  payroll_pct_of_revenue: number;
  payroll_change_pct: number;
  leave_liability_rand: number;
  leave_liability_weeks_payroll: number;
  next_payroll_date: string;
  cash_covers_payroll: boolean;
  payroll_health: "good" | "warning" | "critical";
  health_score: number;
  health_rating: "excellent" | "good" | "fair" | "poor" | "critical";
  health_flags: string[];
  warnings: string[];
  // Premium-only
  yoy_available?: boolean;
  yoy_revenue_change_pct?: number | null;
  yoy_gross_profit_change_pct?: number | null;
  yoy_cost_change_pct?: number | null;
  yoy_prior_year_revenue?: number;
  quarterly_revenue?: number;
  quarterly_period?: string;
  anomalies?: string[];
}

export interface Report {
  id: string;
  company_id: string;
  upload_id: string | null;
  period_month: number;
  period_year: number;
  metrics: Metrics;
  narrative_summary: string | null;
  narrative_revenue: string | null;
  narrative_costs: string | null;
  narrative_debtors: string | null;
  narrative_payroll: string | null;
  narrative_cash: string | null;
  narrative_actions: string | null;
  narrative_trend: string | null;
  narrative_custom: string | null;
  pdf_path: string | null;
  email_sent: boolean;
  generated_at: string | null;
  created_at: string;
}

export interface ReportListItem {
  id: string;
  company_id: string;
  period_month: number;
  period_year: number;
  health_score: number | null;
  health_rating: string | null;
  pdf_ready: boolean;
  email_sent: boolean;
  payroll_pending: boolean;
  generated_at: string | null;
}

export interface Upload {
  id: string;
  company_id: string;
  period_month: number;
  period_year: number;
  status: "pending" | "processing" | "complete" | "failed";
  error_message: string | null;
  created_at: string;
}

export interface EvolutionAgent {
  id: string;
  company_id: string;
  company_name: string;
  api_key: string;
  encryption_key: string;
  server_name: string | null;
  db_name: string | null;
  db_username: string | null;
  db_password: string | null;
  last_sync_at: string | null;
  last_sync_status: string | null;
  active: boolean;
}

export interface AdminClientCard {
  id: string;
  name: string;
  plan: "starter" | "professional" | "premium";
  data_source: "partner" | "evolution";
  health_score: number | null;
  health_rating: string | null;
  last_report_month: number | null;
  last_report_year: number | null;
  last_report_generated: string | null;
  payroll_pending: boolean;
  email_sent: boolean;
  // Agent fields
  agent_id: string | null;
  agent_last_heartbeat: string | null;
  agent_last_sync: string | null;
  agent_status: string | null;
  agent_active: boolean;
  agent_server_name: string | null;
  agent_db_name: string | null;
  agent_sql_ok: boolean | null;
  agent_pending_sync_month: number | null;
  agent_pending_sync_year: number | null;
}

export interface AdminRecentReport {
  company_name: string;
  period_month: number;
  period_year: number;
  health_score: number | null;
  health_rating: string | null;
  generated_at: string;
  email_sent: boolean;
}

export interface AdminOverview {
  mrr: number;
  active_clients: number;
  inactive_clients: number;
  plans: Record<string, number>;
  reports_this_month: number;
  payroll_pending_count: number;
  health_distribution: Record<string, number>;
  clients: AdminClientCard[];
  recent_reports: AdminRecentReport[];
  fetched_at: string;
}

export interface ServiceCheck {
  ok: boolean;
  message: string;
}

export interface SystemStatus {
  database: ServiceCheck;
  redis: ServiceCheck;
  payfast: ServiceCheck;
  resend: ServiceCheck;
  openrouter: ServiceCheck;
  agent_key: ServiceCheck;
}
