import { useEffect, useState } from "react";
import { getSubscription, changePlan, cancelSubscription } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { SubscriptionInfo } from "@/lib/types";

// ---------------------------------------------------------------------------
// Plan definitions
// ---------------------------------------------------------------------------

const PLANS: Array<{
  id: PlanId;
  name: string;
  price: number;
  popular?: boolean;
  features: string[];
}> = [
  {
    id: "starter",
    name: "Starter",
    price: 500,
    features: [
      "Monthly PDF report",
      "Email delivery",
      "12-month report history",
      "Pastel Partner or Evolution",
    ],
  },
  {
    id: "professional",
    name: "Professional",
    price: 900,
    popular: true,
    features: [
      "Everything in Starter",
      "Weekly cash pulse",
      "Debtor alert notifications",
      "WhatsApp delivery",
    ],
  },
  {
    id: "premium",
    name: "Premium",
    price: 1500,
    features: [
      "Everything in Professional",
      "Quarterly trend analysis",
      "Year-on-year comparison",
      "Anomaly alerts",
      "Custom commentary",
      "Priority support",
    ],
  },
];

type PlanId = "starter" | "professional" | "premium";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(amount: number) {
  return `R${amount.toLocaleString("en-ZA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-ZA", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    active: "text-emerald-400",
    cancelled: "text-red-400",
    pending: "text-amber-400",
    inactive: "text-zinc-500",
  };
  const label: Record<string, string> = {
    active: "Active",
    cancelled: "Cancelled",
    pending: "Pending",
    inactive: "Inactive",
  };
  return (
    <span className={`text-xs font-semibold uppercase tracking-wider ${map[status] ?? "text-zinc-400"}`}>
      {label[status] ?? status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Plan card
// ---------------------------------------------------------------------------

type PlanDef = (typeof PLANS)[number];

function PlanCard({
  plan,
  current,
  sub,
  onSelect,
  disabled,
}: {
  plan: PlanDef;
  current: boolean;
  sub: SubscriptionInfo;
  onSelect: (id: PlanId) => void;
  disabled: boolean;
}) {
  const isUpgrade = plan.price > sub.plan_price;
  const isDowngrade = plan.price < sub.plan_price;
  const daysLeft = sub.days_remaining_in_cycle ?? 30;
  const prorated = Math.round((plan.price / 30) * daysLeft * 100) / 100;

  return (
    <div
      className={`card p-5 flex flex-col gap-4 relative transition-all ${
        current
          ? "border-brand-teal/50 bg-brand-teal/5"
          : plan.popular
          ? "border-white/20"
          : "border-white/5 opacity-80 hover:opacity-100"
      }`}
    >
      {plan.popular && !current && (
        <span className="absolute -top-2.5 left-4 text-[10px] font-bold uppercase tracking-widest bg-brand-teal text-black px-2 py-0.5 rounded-full">
          Most Popular
        </span>
      )}
      {current && (
        <span className="absolute -top-2.5 left-4 text-[10px] font-bold uppercase tracking-widest bg-white/10 text-zinc-300 px-2 py-0.5 rounded-full">
          Current Plan
        </span>
      )}

      <div>
        <p className="font-heading font-bold text-base text-white">{plan.name}</p>
        <p className="text-2xl font-bold mt-1 brand-text">{fmt(plan.price)}<span className="text-sm font-normal text-zinc-500">/month</span></p>
      </div>

      <ul className="space-y-1.5 flex-1">
        {plan.features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-xs text-zinc-400">
            <span className="text-brand-teal mt-0.5 shrink-0">✓</span>
            {f}
          </li>
        ))}
      </ul>

      {current ? (
        <div className="text-xs text-zinc-500 text-center pt-1">You are on this plan</div>
      ) : (
        <div className="space-y-1.5">
          {isUpgrade && sub.days_remaining_in_cycle !== null && (
            <p className="text-[11px] text-zinc-500 text-center">
              Pay {fmt(prorated)} now ({daysLeft} days prorated), then {fmt(plan.price)}/month
            </p>
          )}
          {isDowngrade && (
            <p className="text-[11px] text-zinc-500 text-center">
              Takes effect at next billing date
            </p>
          )}
          <button
            disabled={disabled || sub.subscription_status === "cancelled"}
            onClick={() => onSelect(plan.id as PlanId)}
            className={`w-full text-sm font-medium py-2 rounded-lg transition-colors ${
              isUpgrade
                ? "btn-primary"
                : "btn-secondary"
            } disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            {isUpgrade ? "Upgrade" : "Downgrade"}
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Confirm modal
// ---------------------------------------------------------------------------

function ConfirmModal({
  plan,
  sub,
  onConfirm,
  onCancel,
  loading,
}: {
  plan: PlanDef;
  sub: SubscriptionInfo;
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const isUpgrade = plan.price > sub.plan_price;
  const daysLeft = sub.days_remaining_in_cycle ?? 30;
  const prorated = Math.round((plan.price / 30) * daysLeft * 100) / 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={onCancel}>
      <div className="w-full max-w-md bg-zinc-900 border border-white/10 rounded-xl p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="font-heading font-bold text-lg mb-2">
          {isUpgrade ? "Confirm Upgrade" : "Confirm Downgrade"}
        </h2>

        <div className="space-y-3 my-4">
          <div className="flex justify-between text-sm py-2 border-b border-white/5">
            <span className="text-zinc-400">Current plan</span>
            <span className="font-medium capitalize">{sub.plan} — {fmt(sub.plan_price)}/month</span>
          </div>
          <div className="flex justify-between text-sm py-2 border-b border-white/5">
            <span className="text-zinc-400">New plan</span>
            <span className="font-medium capitalize">{plan.name} — {fmt(plan.price)}/month</span>
          </div>

          {isUpgrade ? (
            <>
              <div className="flex justify-between text-sm py-2 border-b border-white/5">
                <span className="text-zinc-400">Days remaining in cycle</span>
                <span className="font-medium">{daysLeft} days</span>
              </div>
              <div className="flex justify-between text-sm py-2 border-b border-white/5">
                <span className="text-zinc-400">Charge now (prorated)</span>
                <span className="font-bold text-brand-teal">{fmt(prorated)}</span>
              </div>
              {sub.next_billing_date && (
                <div className="flex justify-between text-sm py-2">
                  <span className="text-zinc-400">Then from {fmtDate(sub.next_billing_date)}</span>
                  <span className="font-medium">{fmt(plan.price)}/month</span>
                </div>
              )}
            </>
          ) : (
            <div className="flex justify-between text-sm py-2">
              <span className="text-zinc-400">Takes effect</span>
              <span className="font-medium">{sub.next_billing_date ? fmtDate(sub.next_billing_date) : "Next billing date"}</span>
            </div>
          )}
        </div>

        {isUpgrade && (
          <p className="text-xs text-zinc-500 bg-zinc-800/60 rounded-lg p-3 mb-4">
            The prorated amount of {fmt(prorated)} will be charged immediately to your card on file.
          </p>
        )}

        <div className="flex gap-3">
          <button onClick={onConfirm} disabled={loading} className="btn-primary flex-1">
            {loading ? "Processing…" : isUpgrade ? `Pay ${fmt(prorated)} & Upgrade` : "Confirm Downgrade"}
          </button>
          <button onClick={onCancel} disabled={loading} className="btn-secondary">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cancel confirmation
// ---------------------------------------------------------------------------

function CancelSection({
  sub,
  onCancelled,
}: {
  sub: SubscriptionInfo;
  onCancelled: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCancel = async () => {
    setLoading(true);
    setError("");
    try {
      await cancelSubscription();
      setOpen(false);
      onCancelled();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to cancel. Please try again or contact support.");
    } finally {
      setLoading(false);
    }
  };

  if (sub.subscription_status === "cancelled") {
    return (
      <div className="card p-5 border-red-500/20 bg-red-500/5">
        <p className="text-sm text-red-400 font-medium">Subscription cancelled</p>
        <p className="text-xs text-zinc-500 mt-1">
          Your subscription has been cancelled.
          {sub.next_billing_date && ` Access continues until ${fmtDate(sub.next_billing_date)}.`}
          {" "}Contact Numbers10 if you'd like to reactivate.
        </p>
      </div>
    );
  }

  return (
    <div className="card p-5 space-y-3">
      <h2 className="font-heading text-sm font-bold text-zinc-400 uppercase tracking-wider">
        Cancel Subscription
      </h2>
      <p className="text-xs text-zinc-500">
        You can cancel at any time. Your access will continue until the end of your current billing period.
      </p>
      {!open ? (
        <button onClick={() => setOpen(true)} className="text-sm text-red-400 hover:text-red-300 transition-colors">
          Cancel my subscription
        </button>
      ) : (
        <div className="space-y-3 pt-1">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <p className="text-sm font-medium text-red-300 mb-1">Are you sure?</p>
            <p className="text-xs text-zinc-400">
              Your subscription will be cancelled immediately and you will lose access to new reports
              {sub.next_billing_date && ` after ${fmtDate(sub.next_billing_date)}`}.
            </p>
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-3">
            <button
              onClick={handleCancel}
              disabled={loading}
              className="text-sm bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? "Cancelling…" : "Yes, cancel my subscription"}
            </button>
            <button
              onClick={() => setOpen(false)}
              disabled={loading}
              className="btn-secondary text-sm"
            >
              Keep subscription
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function SubscriptionPage() {
  const { user } = useAuth();
  const [sub, setSub] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pendingPlan, setPendingPlan] = useState<PlanDef | null>(null);
  const [changing, setChanging] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    getSubscription()
      .then((r) => setSub(r.data))
      .catch(() => setError("Failed to load subscription details."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (user?.role !== "owner" && user?.role !== "admin") {
    return (
      <div className="text-zinc-500 text-sm">
        Subscription management is only available to account owners.
      </div>
    );
  }

  const handlePlanSelect = (id: PlanId) => {
    const plan = PLANS.find((p) => p.id === id);
    if (plan) setPendingPlan(plan);
  };

  const handleConfirmChange = async () => {
    if (!pendingPlan) return;
    setChanging(true);
    setSuccessMsg("");
    try {
      const res = await changePlan(pendingPlan.id);
      setPendingPlan(null);
      setSuccessMsg(res.data.message);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to change plan. Please try again.");
      setPendingPlan(null);
    } finally {
      setChanging(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-8">
      {pendingPlan && sub && (
        <ConfirmModal
          plan={pendingPlan}
          sub={sub}
          onConfirm={handleConfirmChange}
          onCancel={() => setPendingPlan(null)}
          loading={changing}
        />
      )}

      <div>
        <h1 className="font-heading text-2xl font-bold">Subscription</h1>
        <p className="text-zinc-400 text-sm mt-1">
          Manage your Ghost CFO plan and billing.
        </p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4 text-sm text-emerald-400">
          {successMsg}
        </div>
      )}

      {loading && !sub && (
        <div className="text-zinc-500 text-sm">Loading subscription details…</div>
      )}

      {sub && (
        <>
          {/* Current plan summary */}
          <div className="card p-6 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-heading text-sm font-bold text-brand-teal uppercase tracking-wider mb-3">
                  Current Plan
                </h2>
                <div className="flex items-center gap-3">
                  <span className="text-xl font-bold capitalize">{sub.plan}</span>
                  <span className="text-lg text-zinc-400">·</span>
                  <span className="text-xl font-bold brand-text">{fmt(sub.plan_price)}<span className="text-sm font-normal text-zinc-500">/month</span></span>
                </div>
              </div>
              <div className="text-right shrink-0">
                {statusBadge(sub.subscription_status)}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2 border-t border-white/5">
              {sub.next_billing_date && (
                <div>
                  <p className="text-xs text-zinc-500 mb-0.5">Next billing date</p>
                  <p className="text-sm font-medium">{fmtDate(sub.next_billing_date)}</p>
                </div>
              )}
              {sub.next_billing_amount !== null && (
                <div>
                  <p className="text-xs text-zinc-500 mb-0.5">Next billing amount</p>
                  <p className="text-sm font-medium">{fmt(sub.next_billing_amount)}</p>
                </div>
              )}
              {sub.days_remaining_in_cycle !== null && (
                <div>
                  <p className="text-xs text-zinc-500 mb-0.5">Days remaining</p>
                  <p className="text-sm font-medium">{sub.days_remaining_in_cycle} days</p>
                </div>
              )}
              {sub.plan_start_date && (
                <div>
                  <p className="text-xs text-zinc-500 mb-0.5">Subscription started</p>
                  <p className="text-sm font-medium">{fmtDate(sub.plan_start_date)}</p>
                </div>
              )}
            </div>

            {sub.days_remaining_in_cycle !== null && (
              <div className="pt-1">
                <div className="flex justify-between text-xs text-zinc-500 mb-1.5">
                  <span>Billing cycle</span>
                  <span>{sub.days_remaining_in_cycle} days remaining</span>
                </div>
                <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-brand-teal to-cyan-400 rounded-full transition-all"
                    style={{ width: `${((30 - sub.days_remaining_in_cycle) / 30) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Change plan */}
          {sub.subscription_status !== "cancelled" && (
            <div className="space-y-4">
              <h2 className="font-heading text-sm font-bold text-zinc-300 uppercase tracking-wider">
                Change Plan
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {PLANS.map((plan) => (
                  <PlanCard
                    key={plan.id}
                    plan={plan}
                    current={plan.id === sub.plan}
                    sub={sub}
                    onSelect={handlePlanSelect}
                    disabled={changing}
                  />
                ))}
              </div>
              <p className="text-xs text-zinc-600">
                Upgrade charges are prorated for the remaining days in your current billing cycle.
                Downgrade changes take effect at the start of your next billing cycle.
              </p>
            </div>
          )}

          {/* Cancel */}
          <CancelSection sub={sub} onCancelled={load} />
        </>
      )}
    </div>
  );
}
