export const MONTHS = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export const MONTHS_FULL = [
  "", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `R ${(value / 1_000_000).toFixed(2)}m`;
  }
  return `R ${Math.round(value).toLocaleString("en-ZA")}`;
}

export function formatPct(value: number, showSign = false): string {
  const sign = showSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function formatPeriod(month: number, year: number): string {
  return `${MONTHS_FULL[month]} ${year}`;
}

export function healthColor(rating: string): string {
  switch (rating) {
    case "excellent": return "text-emerald-400";
    case "good":      return "text-green-400";
    case "fair":      return "text-yellow-400";
    case "poor":      return "text-orange-400";
    case "critical":  return "text-red-400";
    default:          return "text-zinc-400";
  }
}
