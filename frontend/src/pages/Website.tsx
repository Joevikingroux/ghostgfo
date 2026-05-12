import { useState } from "react";
import { Link } from "react-router-dom";
import GhostLogo from "@/components/GhostLogo";

// ── Icons (inline SVG — no icon library dependency) ──────────────────────

const Icon = {
  menu: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  ),
  close: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  ),
  check: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="2.5" strokeLinecap="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  ),
  bolt: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  ),
  chart: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
  bell: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  ),
  users: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  phone: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 9.91a16 16 0 0 0 6 6l.92-.92a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
    </svg>
  ),
  shield: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
  ),
  file: (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
    </svg>
  ),
  arrow: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
    </svg>
  ),
};

// ── Reusable components ───────────────────────────────────────────────────

function GradientText({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={className}
      style={{
        background: "linear-gradient(135deg, #2DD4BF 0%, #06B6D4 50%, #818CF8 100%)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        backgroundClip: "text",
      }}
    >
      {children}
    </span>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="inline-flex items-center gap-2 bg-[#0d1f1e] border border-[#1a3330] rounded-full px-4 py-1.5 text-xs font-semibold text-brand-teal uppercase tracking-widest mb-6">
      <span className="w-1.5 h-1.5 rounded-full bg-brand-teal" />
      {children}
    </div>
  );
}

// ── Navbar ────────────────────────────────────────────────────────────────

function Navbar() {
  const [open, setOpen] = useState(false);

  const links = [
    { href: "#how-it-works", label: "How it works" },
    { href: "#features", label: "Features" },
    { href: "#pricing", label: "Pricing" },
    { href: "#about", label: "About" },
  ];

  const scrollTo = (id: string) => {
    setOpen(false);
    const el = document.querySelector(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 backdrop-blur-md bg-black/80">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <a href="#" className="flex items-center">
          <GhostLogo size={36} showText textSize="text-lg" />
        </a>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6">
          {links.map((l) => (
            <button
              key={l.href}
              onClick={() => scrollTo(l.href)}
              className="text-sm text-zinc-400 hover:text-white transition-colors"
            >
              {l.label}
            </button>
          ))}
        </div>

        {/* CTA + mobile toggle */}
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="hidden md:inline-flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg border border-[#2DD4BF]/40 text-[#2DD4BF] hover:bg-[#2DD4BF]/10 transition-all"
          >
            Client Login
          </Link>
          <a
            href="mailto:ghostcfo@numbers10.co.za"
            className="hidden md:inline-flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg text-black transition-all"
            style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
          >
            Get Started
          </a>
          <button
            className="md:hidden text-zinc-400 hover:text-white transition-colors"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? Icon.close : Icon.menu}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-white/5 bg-black/95 px-6 py-4 space-y-3">
          {links.map((l) => (
            <button
              key={l.href}
              onClick={() => scrollTo(l.href)}
              className="block w-full text-left text-sm text-zinc-400 hover:text-white py-1.5 transition-colors"
            >
              {l.label}
            </button>
          ))}
          <div className="pt-2 flex flex-col gap-2">
            <Link
              to="/login"
              onClick={() => setOpen(false)}
              className="text-sm font-semibold px-4 py-2.5 rounded-lg border border-[#2DD4BF]/40 text-[#2DD4BF] text-center"
            >
              Client Login
            </Link>
            <a
              href="mailto:ghostcfo@numbers10.co.za"
              className="text-sm font-semibold px-4 py-2.5 rounded-lg text-black text-center"
              style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
            >
              Get Started
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Background glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(45,212,191,0.12) 0%, transparent 70%)",
        }}
      />
      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(rgba(45,212,191,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(45,212,191,0.05) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative max-w-5xl mx-auto px-6 text-center py-20">
        <div className="inline-flex items-center gap-2 bg-[#0d1f1e] border border-[#1a3330] rounded-full px-4 py-1.5 text-xs font-semibold text-brand-teal uppercase tracking-widest mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-teal animate-pulse" />
          Now live — South Africa's first AI CFO service
        </div>

        <h1 className="font-heading font-bold leading-[1.1] mb-6"
          style={{ fontSize: "clamp(2.5rem, 6vw, 5rem)" }}>
          Your numbers,{" "}
          <GradientText>explained in plain English.</GradientText>
        </h1>

        <p className="text-zinc-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mb-10">
          Ghost CFO connects to your Sage Pastel accounting system and delivers a
          monthly plain-language financial report — delivered by email — that
          tells you exactly what happened, why it matters, and what to do about it.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
          <Link
            to="/signup"
            className="group flex items-center gap-2 px-8 py-4 rounded-xl text-black font-bold text-base transition-all hover:scale-105 hover:shadow-[0_0_30px_rgba(45,212,191,0.4)]"
            style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
          >
            Get started from R500/month
            <span className="group-hover:translate-x-1 transition-transform">{Icon.arrow}</span>
          </Link>
          <button
            onClick={() => document.querySelector("#how-it-works")?.scrollIntoView({ behavior: "smooth" })}
            className="flex items-center gap-2 px-8 py-4 rounded-xl text-zinc-300 font-semibold border border-white/10 hover:border-white/20 hover:text-white transition-all text-base"
          >
            See how it works
          </button>
        </div>

        {/* Hero report preview */}
        <div className="max-w-2xl mx-auto">
          <ReportPreviewCard />
        </div>
      </div>
    </section>
  );
}

function ReportPreviewCard() {
  return (
    <div
      className="rounded-2xl border border-white/10 p-1 shadow-2xl"
      style={{ background: "linear-gradient(135deg, rgba(45,212,191,0.05), rgba(6,182,212,0.03))" }}
    >
      <div className="rounded-xl bg-[#0a0a0a] p-5 text-left space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-0.5">Ghost CFO Report</p>
            <p className="font-heading font-bold text-white text-lg">ABC Hardware</p>
            <p className="text-xs text-zinc-500">October 2025</p>
          </div>
          <div className="text-right">
            <div className="font-heading text-3xl font-bold" style={{ color: "#facc15" }}>61</div>
            <div className="text-xs text-zinc-400">/100 health score</div>
            <div className="text-xs font-semibold mt-0.5" style={{ color: "#facc15" }}>Fair</div>
          </div>
        </div>
        {/* Narrative excerpt */}
        <div className="bg-[#0d1a19] border border-[#1a3330] rounded-lg p-3">
          <p className="text-sm text-zinc-300 leading-relaxed">
            "October was a tough month for ABC Hardware. Revenue came in at{" "}
            <span className="text-[#2DD4BF] font-semibold">R312,000</span> — 8% lower than September.
            Your payroll is your single biggest cost at{" "}
            <span className="text-[#2DD4BF] font-semibold">28% of revenue</span>.
            You are owed <span className="text-amber-400 font-semibold">R94,000</span> — 3 invoices
            overdue 60+ days need urgent attention."
          </p>
        </div>
        {/* Mini metrics */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: "Revenue", val: "R312k", delta: "-8%", pos: false },
            { label: "Cash", val: "R87k", delta: "9 weeks", pos: true },
            { label: "Debtors", val: "R94k", delta: "3 overdue", pos: false },
          ].map((m) => (
            <div key={m.label} className="bg-[#111] rounded-lg p-2.5">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{m.label}</p>
              <p className="font-heading font-bold text-white text-base">{m.val}</p>
              <p className={`text-[10px] mt-0.5 ${m.pos ? "text-emerald-400" : "text-amber-400"}`}>{m.delta}</p>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 pt-1">
          <span className="text-[10px] text-zinc-500">Delivered via</span>
          <span className="bg-[#1a1a2e] text-blue-400 text-[10px] font-semibold px-2 py-0.5 rounded">Email PDF</span>
        </div>
      </div>
    </div>
  );
}

// ── Social proof strip ─────────────────────────────────────────────────────

function SocialProof() {
  const items = [
    "Sage Pastel Evolution",
    "Pastel Partner",
    "Pastel Payroll",
    "Email PDF delivery",
    "Plain English • Afrikaans",
    "From R500/month",
  ];
  return (
    <div className="border-y border-white/5 bg-[#030303] py-4 overflow-hidden">
      <div className="flex gap-12 items-center whitespace-nowrap animate-none">
        <div className="flex gap-12 items-center px-8">
          {items.map((item, i) => (
            <span key={i} className="flex items-center gap-2.5 text-sm text-zinc-500">
              <span className="w-1 h-1 rounded-full bg-[#2DD4BF]" />
              {item}
            </span>
          ))}
          {/* Duplicate for visual fill */}
          {items.map((item, i) => (
            <span key={`b${i}`} className="flex items-center gap-2.5 text-sm text-zinc-500">
              <span className="w-1 h-1 rounded-full bg-[#2DD4BF]" />
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── How it works ──────────────────────────────────────────────────────────

function HowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Connect your Pastel",
      desc: "For Evolution clients, our agent installs on your server and connects automatically. For Partner clients, your bookkeeper uploads 3–4 standard Pastel exports — takes 5 minutes.",
    },
    {
      num: "02",
      title: "We analyse everything",
      desc: "Our AI reads your revenue, costs, debtors, payroll and cash — then calculates your true financial position, health score, and the biggest risks to your business this month.",
    },
    {
      num: "03",
      title: "You receive the report",
      desc: "On the 1st of every month you receive a plain-language PDF by email. No spreadsheets. No jargon. Just clear answers to: how did my business do?",
    },
  ];

  return (
    <section id="how-it-works" className="py-24 max-w-6xl mx-auto px-6">
      <div className="text-center mb-16">
        <SectionLabel>How it works</SectionLabel>
        <h2 className="font-heading font-bold text-4xl md:text-5xl text-white">
          Three steps to financial clarity
        </h2>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {steps.map((s, i) => (
          <div key={i} className="relative group">
            {/* Connector line */}
            {i < steps.length - 1 && (
              <div className="hidden md:block absolute top-10 left-full w-full h-px bg-gradient-to-r from-[#2DD4BF]/30 to-transparent z-10" />
            )}
            <div className="rounded-2xl border border-white/8 bg-[#080808] p-7 h-full hover:border-[#2DD4BF]/30 transition-colors group-hover:bg-[#0a0a0a]">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center font-heading font-bold text-lg mb-5"
                style={{ background: "linear-gradient(135deg,rgba(45,212,191,0.15),rgba(6,182,212,0.1))", color: "#2DD4BF", border: "1px solid rgba(45,212,191,0.2)" }}
              >
                {s.num}
              </div>
              <h3 className="font-heading font-bold text-white text-xl mb-3">{s.title}</h3>
              <p className="text-zinc-400 text-sm leading-relaxed">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── Features ──────────────────────────────────────────────────────────────

function Features() {
  const features = [
    {
      icon: Icon.file,
      title: "Plain-language narrative",
      desc: "AI reads your numbers and writes a report in simple English (or Afrikaans) that any business owner can understand — no accounting degree required.",
    },
    {
      icon: Icon.phone,
      title: "Email PDF delivery",
      desc: "Receive your full report as a professionally formatted PDF by email on the 1st of every month. Done by 7am — ready when you start your day.",
    },
    {
      icon: Icon.users,
      title: "Payroll cost analysis",
      desc: "Know your true staff cost — gross salary, employer UIF, SDL, leave liability, and whether your cash covers next payroll. Most owners don't know this number.",
    },
    {
      icon: Icon.bell,
      title: "Debtor alerts",
      desc: "Ghost CFO flags overdue invoices in your monthly report — showing exactly which customers owe what and for how long. No more discovering late payments at month-end.",
    },
    {
      icon: Icon.chart,
      title: "Cash runway calculation",
      desc: "At your current burn rate, how many weeks of cash do you have left? Ghost CFO calculates this every month and warns you before it becomes a crisis.",
    },
    {
      icon: Icon.shield,
      title: "Business health score",
      desc: "A single 0–100 score combining revenue trend, cash position, debtor health and payroll sustainability. Track it month-by-month to see if your business is improving.",
    },
  ];

  return (
    <section id="features" className="py-24 bg-[#030303] border-y border-white/5">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <SectionLabel>Features</SectionLabel>
          <h2 className="font-heading font-bold text-4xl md:text-5xl text-white mb-4">
            Everything a CFO would tell you —{" "}
            <GradientText>automated</GradientText>
          </h2>
          <p className="text-zinc-400 max-w-xl mx-auto">
            A real CFO charges R50,000–R150,000 a month. Ghost CFO delivers the same
            insight for a fraction of the cost.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <div
              key={i}
              className="rounded-2xl border border-white/8 bg-[#080808] p-6 hover:border-[#2DD4BF]/25 transition-all hover:bg-[#0a100f] group"
            >
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                style={{ background: "rgba(45,212,191,0.08)", border: "1px solid rgba(45,212,191,0.15)" }}>
                {f.icon}
              </div>
              <h3 className="font-heading font-bold text-white text-lg mb-2">{f.title}</h3>
              <p className="text-zinc-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Pricing ───────────────────────────────────────────────────────────────

const XIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#52525b" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

function Pricing() {
  const plans = [
    {
      id: "starter",
      name: "Starter",
      price: "R500",
      tagline: "For businesses that want clarity",
      features: [
        "Monthly PDF report",
        "Plain English narrative",
        "Email delivery",
        "Health score + flags",
        "Debtor age analysis",
        "12-month report history",
      ],
      compatibility: {
        partner: true,
        evolution: false,
        payroll: true,
      },
      popular: false,
    },
    {
      id: "professional",
      name: "Professional",
      price: "R900",
      tagline: "For active business owners",
      features: [
        "Everything in Starter",
        "Weekly cash pulse (Monday)",
        "Debtor overdue alerts",
        "Payroll cost analysis",
        "Leave liability tracking",
        "Afrikaans language option",
      ],
      compatibility: {
        partner: false,
        evolution: true,
        payroll: true,
      },
      popular: true,
    },
    {
      id: "premium",
      name: "Premium",
      price: "R1,500",
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
      compatibility: {
        partner: false,
        evolution: true,
        payroll: true,
      },
      popular: false,
    },
  ];

  const compat = [
    { key: "partner" as const, label: "Pastel Partner", color: "#2DD4BF" },
    { key: "evolution" as const, label: "Pastel Evolution", color: "#06B6D4" },
    { key: "payroll" as const, label: "Pastel Payroll", color: "#818CF8" },
  ];
  // Starter = Partner; Professional/Premium = Evolution; Payroll = all plans

  return (
    <section id="pricing" className="py-24 max-w-6xl mx-auto px-6">
      <div className="text-center mb-16">
        <SectionLabel>Pricing</SectionLabel>
        <h2 className="font-heading font-bold text-4xl md:text-5xl text-white mb-4">
          Simple, transparent pricing
        </h2>
        <p className="text-zinc-400 max-w-lg mx-auto">
          No setup fee. No long-term contract. Cancel any time.
          Pay securely via PayFast — card, EFT, or instant EFT.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 items-start">
        {plans.map((p) => (
          <div
            key={p.name}
            className="relative rounded-2xl border p-7 flex flex-col"
            style={{
              background: p.popular
                ? "linear-gradient(135deg,rgba(45,212,191,0.06),rgba(6,182,212,0.04))"
                : "#080808",
              borderColor: p.popular ? "rgba(45,212,191,0.4)" : "rgba(255,255,255,0.08)",
            }}
          >
            {p.popular && (
              <div
                className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold text-black"
                style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
              >
                Most Popular
              </div>
            )}

            <div className="mb-6">
              <h3 className="font-heading font-bold text-white text-xl mb-0.5">{p.name}</h3>
              <p className="text-zinc-500 text-sm mb-4">{p.tagline}</p>
              <div className="flex items-baseline gap-1">
                <span className="font-heading font-bold text-white text-4xl">{p.price}</span>
                <span className="text-zinc-500 text-sm">/month</span>
              </div>
            </div>

            <ul className="space-y-3 mb-6">
              {p.features.map((f) => (
                <li key={f} className="flex items-start gap-2.5 text-sm text-zinc-300">
                  <span className="mt-0.5 shrink-0">{Icon.check}</span>
                  {f}
                </li>
              ))}
            </ul>

            {/* Sage compatibility */}
            <div className="border-t border-white/6 pt-5 mb-7">
              <p className="text-[10px] uppercase tracking-widest text-zinc-600 mb-3 font-semibold">Works with</p>
              <ul className="space-y-2">
                {compat.map((c) => {
                  const supported = p.compatibility[c.key];
                  return (
                    <li key={c.key} className="flex items-center gap-2.5">
                      <span className="shrink-0">
                        {supported
                          ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={c.color} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                          : XIcon}
                      </span>
                      <span className={`text-xs ${supported ? "text-zinc-300" : "text-zinc-600"}`}>
                        {c.label}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>

            <Link
              to={`/signup?plan=${p.id}`}
              className="block text-center py-3.5 rounded-xl font-bold text-sm transition-all hover:scale-105 mt-auto"
              style={
                p.popular
                  ? { background: "linear-gradient(135deg,#2DD4BF,#06B6D4)", color: "#000" }
                  : { border: "1px solid rgba(45,212,191,0.3)", color: "#2DD4BF" }
              }
            >
              Get started
            </Link>
          </div>
        ))}
      </div>

      <p className="text-center text-zinc-600 text-sm mt-8">
        All prices exclude VAT · Billed monthly · Secured by PayFast
      </p>
    </section>
  );
}

// ── Pastel compatibility ──────────────────────────────────────────────────

function PastelBadges() {
  const CheckCell = ({ color }: { color: string }) => (
    <div className="flex justify-center">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    </div>
  );
  const DashCell = () => (
    <div className="flex justify-center">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3f3f46" strokeWidth="2.5" strokeLinecap="round">
        <line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
    </div>
  );

  const products = [
    {
      name: "Sage Pastel Partner",
      desc: "CSV/Excel export upload — takes 5 minutes",
      color: "#2DD4BF",
      starter: true, professional: false, premium: false,
    },
    {
      name: "Sage Pastel Evolution",
      desc: "Direct SQL — automatic monthly sync via agent",
      color: "#06B6D4",
      starter: false, professional: true, premium: true,
    },
    {
      name: "Sage Pastel Payroll",
      desc: "Payroll exports — full staff cost breakdown",
      color: "#818CF8",
      starter: true, professional: true, premium: true,
    },
  ];

  return (
    <section className="py-20 bg-[#030303] border-y border-white/5">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-12">
          <SectionLabel>Pastel Integration</SectionLabel>
          <h2 className="font-heading font-bold text-3xl md:text-4xl text-white mb-3">
            Built specifically for Sage Pastel
          </h2>
          <p className="text-zinc-400 max-w-lg mx-auto text-sm">
            Ghost CFO is the only AI reporting service purpose-built for the South African
            Sage Pastel product family — across all three products.
          </p>
        </div>

        {/* Compatibility matrix */}
        <div className="rounded-2xl border border-white/8 bg-[#080808] overflow-hidden">
          {/* Header row */}
          <div className="grid grid-cols-4 border-b border-white/8">
            <div className="p-5 col-span-1" />
            {["Starter", "Professional", "Premium"].map((plan, i) => (
              <div key={plan} className={`p-5 text-center border-l border-white/8 ${i === 1 ? "bg-[#0a1a19]" : ""}`}>
                <div className="font-heading font-bold text-white text-sm">{plan}</div>
                <div className="text-zinc-500 text-xs mt-0.5">{["R500", "R900", "R1,500"][i]}/mo</div>
              </div>
            ))}
          </div>

          {/* Product rows */}
          {products.map((p, ri) => (
            <div
              key={p.name}
              className={`grid grid-cols-4 ${ri < products.length - 1 ? "border-b border-white/5" : ""}`}
            >
              <div className="p-5 flex items-start gap-3">
                <div
                  className="w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-xs font-bold font-heading mt-0.5"
                  style={{ background: `${p.color}18`, color: p.color, border: `1px solid ${p.color}25` }}
                >
                  P
                </div>
                <div>
                  <div className="text-white text-sm font-semibold">{p.name}</div>
                  <div className="text-zinc-500 text-xs mt-0.5 leading-snug">{p.desc}</div>
                </div>
              </div>
              <div className="flex items-center justify-center border-l border-white/8">
                {p.starter ? <CheckCell color={p.color} /> : <DashCell />}
              </div>
              <div className="flex items-center justify-center border-l border-white/8 bg-[#0a1a19]">
                {p.professional ? <CheckCell color={p.color} /> : <DashCell />}
              </div>
              <div className="flex items-center justify-center border-l border-white/8">
                {p.premium ? <CheckCell color={p.color} /> : <DashCell />}
              </div>
            </div>
          ))}

          {/* Footer note */}
          <div className="border-t border-white/5 px-5 py-3 bg-[#050505]">
            <p className="text-zinc-600 text-xs">
              Starter uses Sage Pastel Partner (file upload). Professional and Premium connect directly to Sage Pastel Evolution via the Ghost CFO Agent. Pastel Payroll is supported on all plans.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── About ─────────────────────────────────────────────────────────────────

function About() {
  return (
    <section id="about" className="py-24 max-w-6xl mx-auto px-6">
      <div className="grid md:grid-cols-2 gap-16 items-center">
        <div>
          <SectionLabel>About</SectionLabel>
          <h2 className="font-heading font-bold text-4xl text-white mb-5 leading-tight">
            Built by a team that has lived inside Pastel for 20 years
          </h2>
          <p className="text-zinc-400 leading-relaxed mb-4">
            Ghost CFO is a product by{" "}
            <span className="text-white font-semibold">Numbers10 Technology Solutions</span>,
            a South African IT company that has been implementing, supporting and integrating
            Sage Pastel for small businesses since 2006.
          </p>
          <p className="text-zinc-400 leading-relaxed mb-6">
            We've seen hundreds of business owners receive a trial balance they don't
            understand, or find out their cash is critical only when the bank calls.
            Ghost CFO exists to change that — by turning your accounting data into
            a conversation you can actually act on.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <a
              href="https://numbers10.co.za"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-[#2DD4BF] hover:underline flex items-center gap-1.5"
            >
              Visit numbers10.co.za {Icon.arrow}
            </a>
            <a
              href="mailto:ghostcfo@numbers10.co.za"
              className="text-sm text-zinc-400 hover:text-white transition-colors"
            >
              ghostcfo@numbers10.co.za
            </a>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {[
            { stat: "20+", label: "Years Pastel experience" },
            { stat: "R500", label: "Starting price per month" },
            { stat: "3 mins", label: "Monthly upload time" },
            { stat: "7am", label: "Report in your inbox" },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-2xl border border-white/8 bg-[#080808] p-6 text-center"
            >
              <div className="font-heading font-bold text-3xl mb-1" style={{ color: "#2DD4BF" }}>
                {s.stat}
              </div>
              <div className="text-zinc-400 text-sm">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── CTA strip ─────────────────────────────────────────────────────────────

function CTAStrip() {
  return (
    <section className="py-24 relative overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 50%, rgba(45,212,191,0.1) 0%, transparent 70%)",
        }}
      />
      <div className="relative max-w-3xl mx-auto px-6 text-center">
        <h2 className="font-heading font-bold text-4xl md:text-5xl text-white mb-5 leading-tight">
          Ready to actually understand your numbers?
        </h2>
        <p className="text-zinc-400 text-lg mb-10 max-w-xl mx-auto">
          First month free. No setup fee. Works with your existing Sage Pastel installation.
          Numbers10 handles everything.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/signup"
            className="group flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-black font-bold text-base transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(45,212,191,0.35)]"
            style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
          >
            Start your subscription
            <span className="group-hover:translate-x-1 transition-transform">{Icon.arrow}</span>
          </Link>
          <a
            href="mailto:info@numbers10.co.za"
            className="flex items-center justify-center gap-2 px-8 py-4 rounded-xl text-white font-semibold border border-white/10 hover:border-white/25 transition-all text-base"
          >
            Email us
          </a>
        </div>
      </div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="border-t border-white/5 bg-[#030303]">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid md:grid-cols-4 gap-8 mb-10">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: "linear-gradient(135deg,#2DD4BF,#06B6D4)" }}
              >
                <span className="text-black font-bold text-sm font-heading">G</span>
              </div>
              <span className="font-heading font-bold text-lg text-white">Ghost CFO</span>
            </div>
            <p className="text-zinc-500 text-sm leading-relaxed max-w-xs">
              AI-powered monthly financial reports for South African small businesses
              running Sage Pastel. Plain English. Delivered by the 1st.
            </p>
            <p className="text-zinc-600 text-xs mt-4">
              Powered by{" "}
              <a href="https://numbers10.co.za" className="text-zinc-400 hover:text-white transition-colors">
                Numbers10 Technology Solutions
              </a>
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-heading font-semibold text-white text-sm mb-4">Product</h4>
            <ul className="space-y-2.5">
              {["Features", "Pricing", "How it works", "Pastel integration"].map((l) => (
                <li key={l}>
                  <button
                    onClick={() => {
                      const map: Record<string, string> = {
                        "Features": "#features",
                        "Pricing": "#pricing",
                        "How it works": "#how-it-works",
                        "Pastel integration": "#features",
                      };
                      document.querySelector(map[l] ?? "#")?.scrollIntoView({ behavior: "smooth" });
                    }}
                    className="text-zinc-500 hover:text-white text-sm transition-colors"
                  >
                    {l}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-heading font-semibold text-white text-sm mb-4">Contact</h4>
            <ul className="space-y-2.5">
              <li>
                <a href="mailto:ghostcfo@numbers10.co.za" className="text-zinc-500 hover:text-white text-sm transition-colors">
                  ghostcfo@numbers10.co.za
                </a>
              </li>
              <li>
                <a href="https://numbers10.co.za" className="text-zinc-500 hover:text-white text-sm transition-colors" target="_blank" rel="noopener noreferrer">
                  numbers10.co.za
                </a>
              </li>
              <li>
                <Link to="/login" className="text-zinc-500 hover:text-white text-sm transition-colors">
                  Client login →
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/5 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-zinc-600 text-xs">
            © {new Date().getFullYear()} Numbers10 Technology Solutions. All rights reserved.
          </p>
          <p className="text-zinc-700 text-xs">
            Ghost CFO is not an auditing service. Reports are for management information only.
          </p>
        </div>
      </div>
    </footer>
  );
}

// ── Page assembly ─────────────────────────────────────────────────────────

export default function WebsitePage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />
      <Hero />
      <SocialProof />
      <HowItWorks />
      <Features />
      <Pricing />
      <PastelBadges />
      <About />
      <CTAStrip />
      <Footer />
    </div>
  );
}
