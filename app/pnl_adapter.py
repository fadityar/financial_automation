"""
app/pnl_adapter.py
------------------
Adapter khusus untuk membaca file PNL.xlsx dengan format laporan 
multi-kolom (13 bulan sekaligus dalam satu sheet).

Format file:
- Header bulan ada di baris ke-4 (index 3)
- Kolom 0-4: hierarki akun (tidak rapi)
- Kolom 5: nama akun
- Kolom 6-18: nilai per bulan (Mar 2026 s/d Mar 2025)

Row kunci yang diekstrak:
- Row 30  : Total Revenue
- Row 54  : Total COGS
- Row 66  : Total Energy
- Row 260 : Total Other Expenses (OpEx + Energy)
- Row 382 : Total Payroll
- Row 404 : EBITDA
- Row 430 : NETT INCOME (LOSS)
"""

import pandas as pd
import os


MONTHS = [
    'Mar 2026', 'Feb 2026', 'Jan 2026',
    'Dec 2025', 'Nov 2025', 'Oct 2025',
    'Sep 2025', 'Aug 2025', 'Jul 2025',
    'Jun 2025', 'May 2025', 'Apr 2025', 'Mar 2025'
]

# Row index → label (berbasis 0, setelah skip 4 baris header)
KEY_ROWS = {
    'total_revenue':    30,
    'total_cogs':       54,
    'total_energy':     66,
    'total_other_opex': 260,
    'total_payroll':    382,
    'ebitda':           404,
    'net_income':       430,
}

# Sub-revenue breakdown
REVENUE_ROWS = {
    'Villa Revenue':      5,
    'Food Revenue':       9,
    'Beverage Revenue':  13,
    'Transport Revenue': 16,
    'Laundry Revenue':   19,
    'Wellness Revenue':  22,
    'Other Income':      29,
}


def load_pnl_file(filepath: str) -> dict:
    """
    Load file PNL.xlsx dan ekstrak semua data penting.
    
    Returns:
        dict dengan keys:
          - summary_df   : DataFrame P&L summary per bulan
          - revenue_df   : DataFrame breakdown revenue per bulan
          - raw_df       : DataFrame raw (seluruh data)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File tidak ditemukan: {filepath}")

    # Load dengan skip 4 baris pertama (header di baris ke-4)
    df = pd.read_excel(filepath, header=3, sheet_name=0)
    df.columns = ['c0', 'c1', 'c2', 'c3', 'c4', 'account'] + MONTHS

    # ── Ekstrak Summary P&L ─────────────────────────────────────────────────
    records = []
    for month in MONTHS:
        try:
            rev   = float(df.iloc[KEY_ROWS['total_revenue']][month])
            cogs  = float(df.iloc[KEY_ROWS['total_cogs']][month])
            energy = float(df.iloc[KEY_ROWS['total_energy']][month])
            opex  = float(df.iloc[KEY_ROWS['total_other_opex']][month])
            pay   = float(df.iloc[KEY_ROWS['total_payroll']][month])
            ebitda = float(df.iloc[KEY_ROWS['ebitda']][month])
            net   = float(df.iloc[KEY_ROWS['net_income']][month])
        except (ValueError, TypeError):
            continue

        gross_profit = rev - cogs
        gross_margin = (gross_profit / rev * 100) if rev != 0 else 0
        net_margin   = (net / rev * 100) if rev != 0 else 0
        ebitda_margin= (ebitda / rev * 100) if rev != 0 else 0
        labor_pct    = (pay / rev * 100) if rev != 0 else 0
        cogs_pct     = (cogs / rev * 100) if rev != 0 else 0

        records.append({
            'month':           month,
            'total_revenue':   rev,
            'total_cogs':      cogs,
            'gross_profit':    gross_profit,
            'gross_margin_%':  round(gross_margin, 2),
            'total_energy':    energy,
            'total_opex':      opex,
            'total_payroll':   pay,
            'ebitda':          ebitda,
            'ebitda_margin_%': round(ebitda_margin, 2),
            'net_income':      net,
            'net_margin_%':    round(net_margin, 2),
            'cogs_%':          round(cogs_pct, 2),
            'labor_cost_%':    round(labor_pct, 2),
        })

    summary_df = pd.DataFrame(records)

    # ── Ekstrak Revenue Breakdown ────────────────────────────────────────────
    rev_records = []
    for seg_name, row_idx in REVENUE_ROWS.items():
        for month in MONTHS:
            try:
                val = float(df.iloc[row_idx][month])
            except (ValueError, TypeError):
                val = 0.0
            rev_records.append({
                'month':    month,
                'segment':  seg_name,
                'amount':   val,
            })

    revenue_df = pd.DataFrame(rev_records)

    return {
        'summary_df': summary_df,
        'revenue_df': revenue_df,
        'raw_df':     df,
    }


def build_insights_from_pnl(summary_df: pd.DataFrame) -> dict:
    """
    Generate insight otomatis khusus untuk format PNL ini.
    Threshold disesuaikan dengan skala bisnis hospitality resort.
    """
    insights  = []
    alerts    = []
    positives = []

    if summary_df.empty or len(summary_df) < 2:
        return {'insights': [], 'alerts': [], 'positives': [], 'summary_text': 'Data tidak cukup.'}

    latest = summary_df.iloc[0]   # Bulan terbaru (Mar 2026)
    prev   = summary_df.iloc[1]   # Bulan sebelumnya (Feb 2026)

    def pct_chg(a, b):
        return ((a - b) / abs(b) * 100) if b != 0 else 0

    def fmt(val):
        if abs(val) >= 1e9:
            return f"Rp {val/1e9:.2f}M"
        return f"Rp {val/1e6:.1f} jt"

    # --- Revenue ---
    rev_chg = pct_chg(latest['total_revenue'], prev['total_revenue'])
    if rev_chg >= 10:
        positives.append(f"✅ Revenue naik {rev_chg:.1f}% vs {prev['month']} ({fmt(prev['total_revenue'])} → {fmt(latest['total_revenue'])})")
    elif rev_chg <= -10:
        alerts.append(f"⚠️ Revenue TURUN {abs(rev_chg):.1f}% dari {prev['month']} ke {latest['month']} ({fmt(prev['total_revenue'])} → {fmt(latest['total_revenue'])}). Perlu investigasi!")
    else:
        insights.append(f"📊 Revenue {latest['month']}: {fmt(latest['total_revenue'])} ({rev_chg:+.1f}% vs {prev['month']})")

    # --- Net Income ---
    net_chg = pct_chg(latest['net_income'], prev['net_income'])
    if latest['net_income'] < 0:
        alerts.append(f"🚨 Net Income NEGATIF: {fmt(latest['net_income'])}. Bisnis dalam kondisi rugi bulan ini!")
    elif latest['net_margin_%'] >= 30:
        positives.append(f"✅ Net Margin sangat baik: {latest['net_margin_%']:.1f}% ({fmt(latest['net_income'])})")
    elif latest['net_margin_%'] < 10:
        alerts.append(f"⚠️ Net Margin rendah: {latest['net_margin_%']:.1f}%. Target minimal 15-20% untuk resort.")
    else:
        insights.append(f"📊 Net Income {latest['month']}: {fmt(latest['net_income'])} | Margin: {latest['net_margin_%']:.1f}%")

    # --- EBITDA ---
    if latest['ebitda'] < 0:
        alerts.append(f"🚨 EBITDA NEGATIF ({fmt(latest['ebitda'])}). Core bisnis bermasalah — review operasional mendesak!")
    elif latest['ebitda_margin_%'] >= 35:
        positives.append(f"✅ EBITDA Margin kuat di {latest['ebitda_margin_%']:.1f}% ({fmt(latest['ebitda'])})")
    else:
        insights.append(f"📊 EBITDA: {fmt(latest['ebitda'])} | Margin: {latest['ebitda_margin_%']:.1f}%")

    # --- COGS % ---
    if latest['cogs_%'] > 25:
        alerts.append(f"⚠️ COGS {latest['cogs_%']:.1f}% dari revenue — cukup tinggi untuk resort. Target ideal < 20%.")
    else:
        positives.append(f"✅ COGS terkontrol di {latest['cogs_%']:.1f}% dari revenue")

    # --- Labor / Payroll ---
    if latest['labor_cost_%'] > 40:
        alerts.append(f"⚠️ Labor Cost {latest['labor_cost_%']:.1f}% dari revenue ({fmt(latest['total_payroll'])}). Di atas threshold 40% untuk resort luxury.")
    elif latest['labor_cost_%'] > 35:
        insights.append(f"📊 Labor Cost {latest['labor_cost_%']:.1f}% — mendekati batas. Monitor staffing efficiency.")
    else:
        positives.append(f"✅ Labor Cost efisien di {latest['labor_cost_%']:.1f}%")

    # --- Energy ---
    energy_pct = (latest['total_energy'] / latest['total_revenue'] * 100) if latest['total_revenue'] != 0 else 0
    energy_chg = pct_chg(latest['total_energy'], prev['total_energy'])
    if energy_pct > 10:
        alerts.append(f"⚠️ Energy Cost {energy_pct:.1f}% dari revenue ({fmt(latest['total_energy'])}). Perlu audit efisiensi energi.")
    if energy_chg > 20:
        alerts.append(f"⚠️ Energy naik {energy_chg:.1f}% vs bulan lalu. Cek konsumsi listrik/LPG/air.")

    # --- Trend 3 bulan terakhir ---
    if len(summary_df) >= 3:
        last3_rev = summary_df.head(3)['total_revenue'].tolist()
        last3_net = summary_df.head(3)['net_income'].tolist()
        if all(last3_net[i] > last3_net[i+1] for i in range(2)):
            positives.append(f"✅ Net Income tumbuh konsisten 3 bulan berturut-turut")
        months_neg = [summary_df.iloc[i]['month'] for i in range(min(6, len(summary_df))) if summary_df.iloc[i]['net_income'] < 0]
        if months_neg:
            alerts.append(f"⚠️ Bulan dengan Net Income negatif dalam 6 bulan terakhir: {', '.join(months_neg)}")

    # --- Summary text ---
    lines = [
        f"{'='*55}",
        f"  AUTO INSIGHT REPORT — {latest['month']}",
        f"{'='*55}",
        f"",
        f"  Revenue      : {fmt(latest['total_revenue'])}",
        f"  Gross Profit : {fmt(latest['gross_profit'])} ({latest['gross_margin_%']:.1f}%)",
        f"  EBITDA       : {fmt(latest['ebitda'])} ({latest['ebitda_margin_%']:.1f}%)",
        f"  Net Income   : {fmt(latest['net_income'])} ({latest['net_margin_%']:.1f}%)",
        f"  Payroll      : {fmt(latest['total_payroll'])} ({latest['labor_cost_%']:.1f}% of Rev)",
        f"",
    ]
    if positives:
        lines += ["🟢 POSITIF:"] + [f"  {p}" for p in positives] + [""]
    if alerts:
        lines += ["🔴 PERHATIAN:"] + [f"  {a}" for a in alerts] + [""]
    if insights:
        lines += ["💡 INFO:"] + [f"  {i}" for i in insights]

    return {
        'insights': insights,
        'alerts': alerts,
        'positives': positives,
        'summary_text': '\n'.join(lines),
    }
