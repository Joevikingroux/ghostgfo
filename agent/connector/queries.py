"""All Pastel Evolution SQL queries.

All connections are READ-ONLY. The agent never writes to the client database.
Tables prefixed with _btbl are standard Evolution table names.

Every query function accepts a ``period_end`` date (the last day of the target
month) so the agent can pull data for any specific period on demand.
"""
from __future__ import annotations

import datetime


def _period_end(period_month: int, period_year: int) -> datetime.date:
    """Return the last day of the given month."""
    if period_month == 12:
        return datetime.date(period_year, 12, 31)
    return datetime.date(period_year, period_month + 1, 1) - datetime.timedelta(days=1)


# ---------------------------------------------------------------------------
# Revenue — income accounts (type 4) for the 13 months up to period_end
# ---------------------------------------------------------------------------

REVENUE_MONTHLY = """
SELECT
    p.cPeriodName                                             AS period_name,
    p.dPeriodDate                                            AS period_date,
    SUM(CASE WHEN a.iAccountType = 4
             THEN t.dDebit - t.dCredit
             ELSE 0 END)                                     AS total_revenue
FROM _btblGLTransactions t
JOIN _btblGLAccounts a  ON t.iAccountID  = a.iAccountID
JOIN _btblGLPeriods  p  ON t.iPeriodID   = p.iPeriodID
WHERE a.iAccountType = 4
  AND p.dPeriodDate  <= ?
  AND p.dPeriodDate  >= DATEADD(month, -13, ?)
GROUP BY p.cPeriodName, p.dPeriodDate
ORDER BY p.dPeriodDate;
"""

# ---------------------------------------------------------------------------
# Cost of sales — account type 5
# ---------------------------------------------------------------------------

COST_OF_SALES_MONTHLY = """
SELECT
    p.cPeriodName                                             AS period_name,
    p.dPeriodDate                                            AS period_date,
    SUM(CASE WHEN a.iAccountType = 5
             THEN t.dDebit - t.dCredit
             ELSE 0 END)                                     AS total_cos
FROM _btblGLTransactions t
JOIN _btblGLAccounts a  ON t.iAccountID  = a.iAccountID
JOIN _btblGLPeriods  p  ON t.iPeriodID   = p.iPeriodID
WHERE a.iAccountType = 5
  AND p.dPeriodDate  <= ?
  AND p.dPeriodDate  >= DATEADD(month, -13, ?)
GROUP BY p.cPeriodName, p.dPeriodDate
ORDER BY p.dPeriodDate;
"""

# ---------------------------------------------------------------------------
# Expenses — account types 6-9 — current and previous period only
# ---------------------------------------------------------------------------

EXPENSES_MONTHLY = """
SELECT
    p.cPeriodName                                             AS period_name,
    p.dPeriodDate                                            AS period_date,
    a.cAccountCode                                           AS account_code,
    a.cAccountName                                           AS account_name,
    SUM(t.dDebit - t.dCredit)                                AS amount
FROM _btblGLTransactions t
JOIN _btblGLAccounts a  ON t.iAccountID  = a.iAccountID
JOIN _btblGLPeriods  p  ON t.iPeriodID   = p.iPeriodID
WHERE a.iAccountType IN (6, 7, 8, 9)
  AND p.dPeriodDate  <= ?
  AND p.dPeriodDate  >= DATEADD(month, -2, ?)
GROUP BY p.cPeriodName, p.dPeriodDate, a.cAccountCode, a.cAccountName
ORDER BY p.dPeriodDate, ABS(SUM(t.dDebit - t.dCredit)) DESC;
"""

# ---------------------------------------------------------------------------
# Debtor age analysis — aged relative to period_end
# ---------------------------------------------------------------------------

DEBTOR_AGE = """
SELECT
    c.cCustomerCode                                          AS customer_code,
    c.cCustomerName                                          AS customer_name,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) <= 30
             THEN t.dBalance ELSE 0 END)                     AS current_amount,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) BETWEEN 31 AND 60
             THEN t.dBalance ELSE 0 END)                     AS days_30_60,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) BETWEEN 61 AND 90
             THEN t.dBalance ELSE 0 END)                     AS days_61_90,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) > 90
             THEN t.dBalance ELSE 0 END)                     AS over_90_days,
    SUM(t.dBalance)                                          AS total_outstanding
FROM _btblARTransactions t
JOIN _btblARCustomers c ON t.iCustomerID = c.iCustomerID
WHERE t.dBalance    > 0
  AND t.iTransactionType IN (1, 2)
GROUP BY c.cCustomerCode, c.cCustomerName
HAVING SUM(t.dBalance) > 0
ORDER BY over_90_days DESC;
"""

# ---------------------------------------------------------------------------
# Creditor age analysis — aged relative to period_end
# ---------------------------------------------------------------------------

CREDITOR_AGE = """
SELECT
    s.cSupplierCode                                          AS supplier_code,
    s.cSupplierName                                          AS supplier_name,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) <= 30
             THEN t.dBalance ELSE 0 END)                     AS current_amount,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) BETWEEN 31 AND 60
             THEN t.dBalance ELSE 0 END)                     AS days_30_60,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) BETWEEN 61 AND 90
             THEN t.dBalance ELSE 0 END)                     AS days_61_90,
    SUM(CASE WHEN DATEDIFF(day, t.dTransactionDate, ?) > 90
             THEN t.dBalance ELSE 0 END)                     AS over_90_days,
    SUM(t.dBalance)                                          AS total_outstanding
FROM _btblAPTransactions t
JOIN _btblAPSuppliers s ON t.iSupplierID = s.iSupplierID
WHERE t.dBalance > 0
GROUP BY s.cSupplierCode, s.cSupplierName
HAVING SUM(t.dBalance) > 0
ORDER BY total_outstanding DESC;
"""

# ---------------------------------------------------------------------------
# Cash balance — bank / cash accounts at period_end
# ---------------------------------------------------------------------------

CASH_BALANCE = """
SELECT
    a.cAccountCode                                           AS account_code,
    a.cAccountName                                           AS account_name,
    SUM(t.dDebit - t.dCredit)                                AS balance
FROM _btblGLTransactions t
JOIN _btblGLAccounts a  ON t.iAccountID = a.iAccountID
JOIN _btblGLPeriods  p  ON t.iPeriodID  = p.iPeriodID
WHERE a.iAccountType = 1
  AND p.dPeriodDate  <= ?
  AND (
      LOWER(a.cAccountName) LIKE '%bank%'
   OR LOWER(a.cAccountName) LIKE '%cash%'
   OR LOWER(a.cAccountName) LIKE '%cheque%'
   OR LOWER(a.cAccountName) LIKE '%current account%'
  )
GROUP BY a.cAccountCode, a.cAccountName
ORDER BY balance DESC;
"""

# ---------------------------------------------------------------------------
# Payroll GL journal detection
# ---------------------------------------------------------------------------

PAYROLL_JOURNAL_CHECK = """
SELECT TOP 1
    js.JournalDate,
    js.GLAccountCode,
    js.Amount
FROM PayrollGLJournal js
WHERE js.JournalDate >= DATEADD(month, -1, ?)
  AND js.JournalDate <= ?
  AND js.Posted = 1
ORDER BY js.JournalDate DESC;
"""

# ---------------------------------------------------------------------------
# Payroll summary (linked Payroll DB only)
# ---------------------------------------------------------------------------

PAYROLL_SUMMARY = """
SELECT
    pp.PeriodDescription                                     AS period_desc,
    pp.PeriodEndDate                                         AS period_end,
    COUNT(DISTINCT pt.EmployeeID)                            AS headcount,
    SUM(CASE WHEN pc.ComponentType = 'Earnings'
             THEN pt.Amount ELSE 0 END)                      AS gross_payroll,
    SUM(CASE WHEN pc.ComponentCode = 'UIF_EE'
             THEN pt.Amount ELSE 0 END)                      AS employee_uif,
    SUM(CASE WHEN pc.ComponentCode = 'UIF_ER'
             THEN pt.Amount ELSE 0 END)                      AS employer_uif,
    SUM(CASE WHEN pc.ComponentCode = 'SDL'
             THEN pt.Amount ELSE 0 END)                      AS employer_sdl,
    SUM(CASE WHEN pc.ComponentCode = 'PAYE'
             THEN pt.Amount ELSE 0 END)                      AS paye_deducted,
    SUM(CASE WHEN pc.ComponentType = 'Earnings'
             THEN pt.Amount ELSE 0 END)
    - SUM(CASE WHEN pc.ComponentType = 'Deductions'
               THEN pt.Amount ELSE 0 END)                    AS net_payroll
FROM PayrollTransaction pt
JOIN PayrollComponent pc ON pt.ComponentID = pc.ComponentID
JOIN PayrollPeriod pp    ON pt.PeriodID    = pp.PeriodID
WHERE pp.PeriodEndDate >= DATEADD(month, -2, ?)
  AND pp.PeriodEndDate <= ?
GROUP BY pp.PeriodDescription, pp.PeriodEndDate
ORDER BY pp.PeriodEndDate;
"""

# ---------------------------------------------------------------------------
# Leave liability (linked Payroll DB only)
# ---------------------------------------------------------------------------

LEAVE_LIABILITY = """
SELECT
    pm.EmployeeName                                          AS employee_name,
    lt.LeaveTypeName                                         AS leave_type,
    lb.BalanceDays                                           AS balance_days,
    pm.BasicSalary / 21.67                                   AS daily_rate,
    (lb.BalanceDays * pm.BasicSalary / 21.67)                AS liability_rand
FROM LeaveBalance lb
JOIN PayrollMaster pm ON lb.EmployeeID  = pm.EmployeeID
JOIN LeaveType lt     ON lb.LeaveTypeID = lt.LeaveTypeID
WHERE lt.LeaveTypeName = 'Annual Leave'
  AND lb.BalanceDays   > 0
ORDER BY liability_rand DESC;
"""
