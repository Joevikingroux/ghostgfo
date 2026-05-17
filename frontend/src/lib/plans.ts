export interface PlanCompat {
  partner: boolean;
  evolution: boolean;
  payroll: boolean;
}

export interface PlanDef {
  id: "starter" | "professional" | "premium";
  name: string;
  price: number;
  tagline: string;
  popular?: boolean;
  features: string[];
  compatibility: PlanCompat;
}

export const PLANS: PlanDef[] = [
  {
    id: "starter",
    name: "Starter",
    price: 500,
    tagline: "For businesses that want clarity",
    features: [
      "Monthly PDF report",
      "Plain English narrative",
      "Email delivery",
      "Health score + flags",
      "Debtor age analysis",
      "12-month report history",
    ],
    compatibility: { partner: true, evolution: false, payroll: true },
  },
  {
    id: "professional",
    name: "Professional",
    price: 900,
    tagline: "For active business owners",
    popular: true,
    features: [
      "Everything in Starter",
      "Weekly cash pulse (Monday)",
      "Debtor overdue alerts",
      "Payroll cost analysis",
      "Leave liability tracking",
      "Afrikaans language option",
    ],
    compatibility: { partner: false, evolution: true, payroll: true },
  },
  {
    id: "premium",
    name: "Premium",
    price: 1500,
    tagline: "For businesses that want more",
    features: [
      "Everything in Professional",
      "Quarterly trend analysis",
      "Year-on-year comparison",
      "Anomaly alerts",
      "Custom commentary section",
      "Priority support from Numbers10",
      "Dedicated account manager",
    ],
    compatibility: { partner: false, evolution: true, payroll: true },
  },
];

export const COMPAT_LABELS: { key: keyof PlanCompat; label: string }[] = [
  { key: "partner", label: "Pastel Partner" },
  { key: "evolution", label: "Pastel Evolution" },
  { key: "payroll", label: "Pastel Payroll" },
];
