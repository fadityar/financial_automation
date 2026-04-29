"""
run_pnl.py
----------
Runner khusus untuk file PNL.xlsx yang sudah ada.
Tidak perlu setup COA mapping manual — format sudah dikenali otomatis.

Jalankan: python run_pnl.py
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.pnl_adapter import load_pnl_file, build_insights_from_pnl
from app.report_generator import export_to_excel
import pandas as pd


def run():
    print("\n" + "="*55)
    print("  PNL AUTOMATION — File PNL.xlsx")
    print("="*55)

    pnl_path    = os.path.join(BASE_DIR, "data", "PNL.xlsx")
    output_path = os.path.join(BASE_DIR, "output", "PNL_report_output.xlsx")

    # ── 1. Load file PNL ─────────────────────────────────────────
    print("\n[1/4] Membaca file PNL.xlsx...")
    data = load_pnl_file(pnl_path)

    summary_df = data['summary_df']
    revenue_df = data['revenue_df']

    print(f"  ✓ {len(summary_df)} bulan terdeteksi")
    print(f"  ✓ Bulan: {', '.join(summary_df['month'].tolist())}")

    # ── 2. Preview summary ───────────────────────────────────────
    print("\n[2/4] P&L Summary Preview (dalam juta Rp):")
    preview_cols = ['month','total_revenue','gross_profit','ebitda','net_income','net_margin_%']
    preview = summary_df[preview_cols].copy()
    for col in ['total_revenue','gross_profit','ebitda','net_income']:
        preview[col] = (preview[col] / 1_000_000).round(1)
    preview.columns = ['Bulan','Revenue (jt)','Gross Profit (jt)','EBITDA (jt)','Net Income (jt)','Net Margin %']
    print(preview.to_string(index=False))

    # ── 3. Export Excel ──────────────────────────────────────────
    print(f"\n[3/4] Export ke Excel...")

    # Siapkan expense_breakdown sederhana dari revenue_df
    # (pakai revenue breakdown sebagai substitute)
    expense_df = revenue_df.rename(columns={'segment': 'subcategory', 'amount': 'total_amount'})
    expense_df['category'] = 'Revenue'

    # General ledger: summary_df semua kolom
    gl_df = summary_df.copy()

    export_to_excel(summary_df, expense_df, gl_df, output_path)

    # ── 4. Insights ──────────────────────────────────────────────
    print("\n[4/4] Auto Insight Generator:")
    insights = build_insights_from_pnl(summary_df)
    print()
    print(insights['summary_text'])

    print("\n" + "="*55)
    print(f"  ✅ SELESAI")
    print(f"  📁 Output: {output_path}")
    print(f"  🚀 Dashboard: streamlit run app/pnl_dashboard.py")
    print("="*55 + "\n")


if __name__ == "__main__":
    run()
