"""LLM prompt templates for every report section.

Every prompt receives a ``metrics`` dict formatted as plain text — never raw
JSON. This keeps prompts compact and prevents the model from echoing keys.
"""
from __future__ import annotations

from typing import Any

from app.narrative.tone import currency, pct

SYSTEM_PROMPT_EN = """\
You are Ghost CFO, a friendly but professional financial advisor for South African \
small businesses. You receive key financial numbers and write clear, plain-language \
report sections that non-financial business owners can understand and act on.

Rules:
- Write in simple, direct English
- Never use accounting jargon without explaining it in brackets
- Always include specific rand amounts, not just percentages
- Be honest about problems — don't sugarcoat, but stay encouraging
- Keep each section to 3–5 sentences maximum
- Write as if you are talking directly to the business owner
- Do not repeat numbers already stated in a previous section
- Do not use bullet points unless specifically asked
"""

SYSTEM_PROMPT_AF = """\
Jy is Ghost CFO, 'n vriendelike maar professionele finansiële adviseur vir Suid-Afrikaanse \
klein besighede. Jy ontvang sleutelfinansieëlesyfers en skryf duidelike, eenvoudige \
verslagafdelings wat nie-finansiële besigheidseienaars kan verstaan en op kan optree.

Reëls:
- Skryf in eenvoudige, direkte Afrikaans
- Gebruik nooit rekeningkundige jargon sonder om dit in hakies te verduidelik nie
- Sluit altyd spesifieke randbedrae in, nie net persentasies nie
- Wees eerlik oor probleme — moenie versag nie, maar bly aanmoedigend
- Hou elke afdeling tot 3–5 sinne
- Skryf asof jy direk met die besigheidseienaar praat
- Moenie syfers herhaal wat reeds in 'n vorige afdeling genoem is nie
- Moenie punte gebruik nie, tensy spesifiek gevra
"""

# Backwards compat alias
SYSTEM_PROMPT = SYSTEM_PROMPT_EN


def _system_prompt(lang: str) -> str:
    return SYSTEM_PROMPT_AF if lang == "af" else SYSTEM_PROMPT_EN


def _fmt(m: dict[str, Any]) -> str:
    """Format the key metrics as a numbered plain-text brief for the LLM."""
    rev_arrow = "▲" if m.get("revenue_change_pct", 0) >= 0 else "▼"
    lines = [
        f"Company: {m.get('company_name', 'the business')}",
        f"Period: {m.get('period_month')}/{m.get('period_year')}",
        "",
        "— REVENUE —",
        f"Current month: {currency(m.get('revenue_current_month', 0))}",
        f"Previous month: {currency(m.get('revenue_previous_month', 0))}  {rev_arrow} {pct(m.get('revenue_change_pct', 0))}",
        f"YTD: {currency(m.get('revenue_ytd', 0))}",
        f"Trend: {m.get('revenue_trend', 'stable')}",
        "",
        "— GROSS PROFIT —",
        f"Gross profit: {currency(m.get('gross_profit_current', 0))}",
        f"Gross margin: {m.get('gross_margin_pct', 0):.1f}% (prev: {m.get('gross_margin_prev_pct', 0):.1f}%)",
        "",
        "— COSTS —",
        f"Total costs: {currency(m.get('total_costs_current', 0))} "
        f"(prev: {currency(m.get('total_costs_previous', 0))})",
        f"Biggest mover: {m.get('top_cost_mover', 'n/a')}  "
        f"change: {currency(m.get('top_cost_mover_change', 0))}  "
        f"({m.get('top_cost_mover_change_pct', 0):+.0f}%)",
        "",
        "— DEBTORS (CUSTOMERS WHO OWE MONEY) —",
        f"Total owed: {currency(m.get('debtors_total', 0))}",
        f"Overdue 60+ days: {currency(m.get('debtors_61_90_days', 0) + m.get('debtors_over_90_days', 0))}",
        f"Overdue invoices: {m.get('overdue_invoices_count', 0)} invoices worth "
        f"{currency(m.get('overdue_invoices_value', 0))}",
        f"Debtor days: {m.get('debtor_days', 0):.0f}",
        f"Health: {m.get('debtors_health', 'unknown')}",
    ]

    # Payroll section (only if data is present)
    if m.get("payroll_gross_total", 0) > 0:
        lines += [
            "",
            "— PAYROLL & STAFF COSTS —",
            f"Gross payroll: {currency(m.get('payroll_gross_total', 0))}",
            f"True employer cost (incl UIF/SDL): {currency(m.get('payroll_true_employer_cost', 0))}",
            f"Headcount: {m.get('payroll_headcount', 0)}",
            f"Payroll as % of revenue: {m.get('payroll_pct_of_revenue', 0):.1f}%",
            f"vs last month: {m.get('payroll_change_pct', 0):+.1f}%",
            f"Leave liability: {currency(m.get('leave_liability_rand', 0))} "
            f"({m.get('leave_liability_weeks_payroll', 0):.1f} weeks of payroll)",
            f"Next payroll run: {m.get('next_payroll_date', 'unknown')}",
            f"Cash covers next payroll (1.5x): {'YES' if m.get('cash_covers_payroll') else 'NO — URGENT'}",
            f"Health: {m.get('payroll_health', 'unknown')}",
        ]

    lines += [
        "",
        "— CASH POSITION —",
        f"Bank balance: {currency(m.get('cash_balance', 0))}",
        f"Monthly burn rate: {currency(m.get('monthly_burn_rate', 0))}",
        f"Cash runway: {m.get('cash_runway_weeks', 0):.1f} weeks",
        f"Health: {m.get('cash_health', 'unknown')}",
        "",
        "— OVERALL HEALTH —",
        f"Score: {m.get('health_score', 0)}/100  ({m.get('health_rating', '')})",
        f"Flags: {'; '.join(m.get('health_flags', [])) or 'none'}",
    ]

    return "\n".join(lines)


_INSTRUCTIONS_EN = {
    "summary": (
        "Write a 2–3 sentence executive summary for this month's financial report. "
        "Start with the company name and period. Cover the most important positive and negative."
    ),
    "revenue": (
        "Write the revenue section (3–4 sentences) explaining what revenue "
        "did this month, how it compares to last month, and what this means "
        "for the business owner."
    ),
    "costs": (
        "Write the costs section (3–4 sentences) covering total costs, the "
        "biggest cost mover, and gross margin. Explain why it matters."
    ),
    "debtors": (
        "Write the debtors section (3–4 sentences) about who owes the business "
        "money, which invoices are overdue, and what the owner should do about it."
    ),
    "payroll": (
        "Write the payroll section (4–5 sentences) covering the total wage bill "
        "including employer UIF and SDL, headcount, payroll as a % of revenue, "
        "leave liability risk, and whether the next payroll run is fully covered "
        "by cash on hand."
    ),
    "cash": (
        "Write the cash section (3–4 sentences) covering the bank balance, how "
        "many weeks the business can run at its current spending rate, and an "
        "honest assessment of the situation."
    ),
    "actions": (
        "Write a numbered list of 3–5 specific, urgent actions the business owner "
        "should take this month, most urgent first. Be concrete — name amounts, "
        "dates and specific customers where possible. One sentence per action."
    ),
}

_INSTRUCTIONS_AF = {
    "summary": (
        "Skryf 'n 2–3 sin uitvoerende opsomming vir hierdie maand se finansiële verslag. "
        "Begin met die maatskappynaam en tydperk. Dek die belangrikste positiewe en negatiewe."
    ),
    "revenue": (
        "Skryf die inkomste-afdeling (3–4 sinne) wat verduidelik wat inkomste "
        "hierdie maand gedoen het, hoe dit vergelyk met verlede maand, en wat dit "
        "vir die besigheidseienaar beteken."
    ),
    "costs": (
        "Skryf die koste-afdeling (3–4 sinne) oor totale koste, die grootste "
        "kostebeweging en bruto marge. Verduidelik waarom dit saak maak."
    ),
    "debtors": (
        "Skryf die debiteure-afdeling (3–4 sinne) oor wie die besigheid geld skuld, "
        "watter fakture agterstallig is, en wat die eienaar daaraan moet doen."
    ),
    "payroll": (
        "Skryf die salarisafdeling (4–5 sinne) oor die totale loonrekening "
        "insluitend werkgewer UIF en SDL, hoofde, salarisse as 'n % van inkomste, "
        "verlofaanspreeklikheidsrisiko, en of die volgende salarisopdrag volledig "
        "deur beskikbare kontant gedek word."
    ),
    "cash": (
        "Skryf die kontantafdeling (3–4 sinne) oor die bankbalans, hoeveel weke "
        "die besigheid teen sy huidige besteding kan voortgaan, en 'n eerlike "
        "beoordeling van die situasie."
    ),
    "actions": (
        "Skryf 'n genommerde lys van 3–5 spesifieke, dringende aksies wat die "
        "besigheidseienaar hierdie maand moet neem, die mees dringende eerste. "
        "Wees konkreet — noem bedrae, datums en spesifieke kliënte waar moontlik. "
        "Een sin per aksie."
    ),
}


def build_summary_prompt(m: dict[str, Any], lang: str = "en") -> list[dict[str, str]]:
    instructions = _INSTRUCTIONS_AF if lang == "af" else _INSTRUCTIONS_EN
    return [
        {"role": "system", "content": _system_prompt(lang)},
        {"role": "user", "content": f"{instructions['summary']}\n\n{_fmt(m)}"},
    ]


def build_section_prompt(
    section: str,
    m: dict[str, Any],
    lang: str = "en",
) -> list[dict[str, str]]:
    instructions = _INSTRUCTIONS_AF if lang == "af" else _INSTRUCTIONS_EN
    instruction = instructions.get(section, f"Write the {section} section.")
    return [
        {"role": "system", "content": _system_prompt(lang)},
        {"role": "user", "content": f"{instruction}\n\n{_fmt(m)}"},
    ]
