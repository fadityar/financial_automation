"""
app/insight_generator.py
------------------------
Generate insight otomatis dari data P&L Summary.
Menggunakan rule-based logic dengan threshold hospitality industry.
"""

import pandas as pd
from typing import List, Dict


# ── Industry Threshold (Hospitality) ────────────────────────────────────────
THRESHOLDS = {
    "food_cost_warning":   35.0,   # Food Cost % > 35% = warning
    "food_cost_critical":  40.0,   # Food Cost % > 40% = critical
    "labor_cost_warning":  30.0,   # Labor Cost % > 30% = warning
    "labor_cost_critical": 35.0,   # Labor Cost % > 35% = critical
    "net_margin_warning":  10.0,   # Net Margin < 10% = warning
    "net_margin_good":     20.0,   # Net Margin > 20% = good
    "gross_margin_warning": 50.0,  # Gross Margin < 50% = warning
    "revenue_growth_good": 10.0,   # Revenue growth > 10% = positive
    "revenue_decline_warn": -5.0,  # Revenue decline > 5% = warning
}


def _pct_change(current: float, previous: float) -> float:
    """Hitung persentase perubahan."""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100


def _format_idr(amount: float) -> str:
    """Format angka ke Rupiah singkat."""
    if abs(amount) >= 1_000_000_000:
        return f"Rp {amount/1_000_000_000:.1f}M"
    elif abs(amount) >= 1_000_000:
        return f"Rp {amount/1_000_000:.1f} jt"
    else:
        return f"Rp {amount:,.0f}"


def generate_insights(pl_summary: pd.DataFrame, expense_breakdown: pd.DataFrame) -> Dict:
    """
    Analisis data dan hasilkan insight otomatis.
    
    Returns:
        Dict dengan keys: insights (list), alerts (list), positives (list), summary_text (str)
    """
    insights = []
    alerts = []
    positives = []

    if pl_summary.empty:
        return {"insights": ["Data tidak cukup untuk generate insight."], "alerts": [], "positives": [], "summary_text": ""}

    months = pl_summary["month"].tolist()
    latest = pl_summary.iloc[-1]
    
    # ── 1. Revenue Analysis ──────────────────────────────────────────────────
    if len(pl_summary) >= 2:
        prev = pl_summary.iloc[-2]
        
        rev_change = _pct_change(latest["total_revenue"], prev["total_revenue"])
        if rev_change >= THRESHOLDS["revenue_growth_good"]:
            positives.append(
                f"✅ Revenue {latest['month']} naik {rev_change:.1f}% dibanding {prev['month']} "
                f"({_format_idr(prev['total_revenue'])} → {_format_idr(latest['total_revenue'])})"
            )
        elif rev_change <= THRESHOLDS["revenue_decline_warn"]:
            alerts.append(
                f"⚠️ Revenue turun {abs(rev_change):.1f}% dari {prev['month']} ke {latest['month']}. "
                f"Perlu investigasi segera."
            )
        else:
            insights.append(
                f"📊 Revenue {latest['month']}: {_format_idr(latest['total_revenue'])} "
                f"({rev_change:+.1f}% vs bulan lalu)"
            )

        # Profit change
        profit_change = _pct_change(latest["net_profit"], prev["net_profit"])
        if profit_change > 15:
            positives.append(
                f"✅ Net Profit meningkat signifikan {profit_change:.1f}% → {_format_idr(latest['net_profit'])}"
            )
        elif profit_change < -10:
            alerts.append(
                f"⚠️ Net Profit turun {abs(profit_change):.1f}% ke {_format_idr(latest['net_profit'])}. "
                f"Review cost structure."
            )

        # COGS change
        cogs_change = _pct_change(latest["total_cogs"], prev["total_cogs"])
        if cogs_change > rev_change + 5:
            alerts.append(
                f"⚠️ COGS naik {cogs_change:.1f}% lebih cepat dari revenue ({rev_change:.1f}%). "
                f"Gross margin tertekan."
            )

    # ── 2. Food Cost % ──────────────────────────────────────────────────────
    fc_pct = latest["food_cost_%"]
    if fc_pct >= THRESHOLDS["food_cost_critical"]:
        alerts.append(
            f"🚨 CRITICAL: Food Cost {latest['month']} = {fc_pct:.1f}% "
            f"(threshold: {THRESHOLDS['food_cost_critical']}%). "
            f"Review menu pricing dan purchasing segera!"
        )
    elif fc_pct >= THRESHOLDS["food_cost_warning"]:
        alerts.append(
            f"⚠️ Food Cost {latest['month']} = {fc_pct:.1f}% melebihi batas ideal "
            f"{THRESHOLDS['food_cost_warning']}%. Perlu cost control."
        )
    else:
        positives.append(
            f"✅ Food Cost terkontrol di {fc_pct:.1f}% (under threshold {THRESHOLDS['food_cost_warning']}%)"
        )

    # ── 3. Labor Cost % ─────────────────────────────────────────────────────
    lc_pct = latest["labor_cost_%"]
    if lc_pct >= THRESHOLDS["labor_cost_critical"]:
        alerts.append(
            f"🚨 CRITICAL: Labor Cost {latest['month']} = {lc_pct:.1f}% "
            f"(threshold: {THRESHOLDS['labor_cost_critical']}%). Review staffing efficiency."
        )
    elif lc_pct >= THRESHOLDS["labor_cost_warning"]:
        alerts.append(
            f"⚠️ Labor Cost {latest['month']} = {lc_pct:.1f}% di atas batas ideal "
            f"{THRESHOLDS['labor_cost_warning']}%."
        )
    else:
        positives.append(
            f"✅ Labor Cost efisien di {lc_pct:.1f}% (under threshold {THRESHOLDS['labor_cost_warning']}%)"
        )

    # ── 4. Net Margin Analysis ───────────────────────────────────────────────
    nm_pct = latest["net_margin_%"]
    if nm_pct >= THRESHOLDS["net_margin_good"]:
        positives.append(
            f"✅ Net Margin sangat baik di {nm_pct:.1f}% (target: >{THRESHOLDS['net_margin_good']}%)"
        )
    elif nm_pct < THRESHOLDS["net_margin_warning"]:
        alerts.append(
            f"⚠️ Net Margin {nm_pct:.1f}% di bawah threshold {THRESHOLDS['net_margin_warning']}%. "
            f"Profitabilitas perlu ditingkatkan."
        )
    else:
        insights.append(f"📊 Net Margin {latest['month']}: {nm_pct:.1f}%")

    # ── 5. Expense Breakdown Analysis ───────────────────────────────────────
    if not expense_breakdown.empty:
        latest_month = months[-1]
        exp_latest = expense_breakdown[expense_breakdown["month"] == latest_month]

        if len(months) >= 2 and len(expense_breakdown["month"].unique()) >= 2:
            prev_month = months[-2]
            exp_prev = expense_breakdown[expense_breakdown["month"] == prev_month]

            for _, row in exp_latest.iterrows():
                subcat = row["subcategory"]
                curr_amt = row["total_amount"]
                prev_row = exp_prev[exp_prev["subcategory"] == subcat]

                if not prev_row.empty:
                    prev_amt = prev_row["total_amount"].values[0]
                    chg = _pct_change(curr_amt, prev_amt)

                    if chg > 20:
                        alerts.append(
                            f"⚠️ {subcat} naik signifikan {chg:.1f}% "
                            f"({_format_idr(prev_amt)} → {_format_idr(curr_amt)})"
                        )
                    elif chg > 10:
                        insights.append(
                            f"📊 {subcat} meningkat {chg:.1f}% di {latest_month}"
                        )

    # ── 6. Trend Analysis (3+ bulan) ────────────────────────────────────────
    if len(pl_summary) >= 3:
        # Cek apakah revenue konsisten naik
        revenues = pl_summary["total_revenue"].tolist()
        is_growing = all(revenues[i] < revenues[i+1] for i in range(len(revenues)-1))
        if is_growing:
            total_growth = _pct_change(revenues[-1], revenues[0])
            positives.append(
                f"✅ Tren positif: Revenue tumbuh konsisten selama {len(revenues)} bulan terakhir "
                f"(+{total_growth:.1f}% dari {months[0]} ke {months[-1]})"
            )

        # Cek apakah net profit konsisten
        profits = pl_summary["net_profit"].tolist()
        is_profit_growing = all(profits[i] < profits[i+1] for i in range(len(profits)-1))
        if is_profit_growing:
            positives.append(
                f"✅ Net Profit tumbuh konsisten {len(profits)} bulan berturut-turut"
            )

    # ── 7. Summary Text ─────────────────────────────────────────────────────
    summary_lines = [
        f"=== INSIGHT REPORT: {latest['month']} ===",
        f"",
        f"📈 KINERJA BULAN INI:",
        f"   • Revenue      : {_format_idr(latest['total_revenue'])}",
        f"   • Gross Profit : {_format_idr(latest['gross_profit'])} ({latest['gross_margin_%']:.1f}%)",
        f"   • Net Profit   : {_format_idr(latest['net_profit'])} ({latest['net_margin_%']:.1f}%)",
        f"   • Food Cost %  : {latest['food_cost_%']:.1f}%",
        f"   • Labor Cost % : {latest['labor_cost_%']:.1f}%",
        f"",
    ]

    if positives:
        summary_lines.append("🟢 POSITIF:")
        for p in positives:
            summary_lines.append(f"   {p}")
        summary_lines.append("")

    if alerts:
        summary_lines.append("🔴 PERHATIAN:")
        for a in alerts:
            summary_lines.append(f"   {a}")
        summary_lines.append("")

    if insights:
        summary_lines.append("💡 INSIGHT LAIN:")
        for i in insights:
            summary_lines.append(f"   {i}")

    summary_text = "\n".join(summary_lines)

    return {
        "insights": insights,
        "alerts": alerts,
        "positives": positives,
        "summary_text": summary_text,
        "latest_month": latest["month"],
    }
