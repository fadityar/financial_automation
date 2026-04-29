"""
main.py
-------
Entry point utama untuk menjalankan pipeline otomatis:
  1. Load & clean semua data dari /data
  2. Generate laporan P&L, Expense Breakdown, General Ledger
  3. Export ke Excel di /output
  4. Print insight otomatis ke terminal
  
Jalankan: python main.py
"""

import os
import sys

# Pastikan root project ada di path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.data_loader import load_coa_mapping, load_all_files
from app.report_generator import (
    build_pl_summary,
    build_expense_breakdown,
    build_general_ledger,
    export_to_excel,
)
from app.insight_generator import generate_insights


def run_pipeline():
    """Jalankan full pipeline financial automation."""

    print("\n" + "="*60)
    print("  FINANCIAL AUTOMATION PIPELINE")
    print("  Hospitality Financial Reporting System")
    print("="*60)

    # ── 1. Path Setup ─────────────────────────────────────────────
    data_dir    = os.path.join(BASE_DIR, "data")
    mapping_path = os.path.join(BASE_DIR, "mapping", "coa_mapping.csv")
    output_path  = os.path.join(BASE_DIR, "output", "financial_report.xlsx")

    # ── 2. Load COA Mapping ───────────────────────────────────────
    print("\n[1/5] Loading Chart of Accounts mapping...")
    coa_mapping = load_coa_mapping(mapping_path)
    print(f"  ✓ {len(coa_mapping)} akun dimuat dari mapping")

    # ── 3. Load & Clean Data ──────────────────────────────────────
    print("\n[2/5] Loading & cleaning raw data files...")
    df_combined = load_all_files(data_dir, coa_mapping)
    print(f"  ✓ Total {len(df_combined)} records dari {df_combined['month'].nunique()} bulan")
    print(f"  ✓ Bulan: {', '.join(df_combined['month'].unique())}")

    # ── 4. Generate Reports ───────────────────────────────────────
    print("\n[3/5] Generating financial reports...")
    pl_summary         = build_pl_summary(df_combined)
    expense_breakdown  = build_expense_breakdown(df_combined)
    general_ledger     = build_general_ledger(df_combined)
    print(f"  ✓ P&L Summary: {len(pl_summary)} bulan")
    print(f"  ✓ Expense Breakdown: {len(expense_breakdown)} rows")
    print(f"  ✓ General Ledger: {len(general_ledger)} entries")

    # ── 5. Export to Excel ────────────────────────────────────────
    print("\n[4/5] Exporting to Excel...")
    export_to_excel(pl_summary, expense_breakdown, general_ledger, output_path)

    # ── 6. Generate Insights ──────────────────────────────────────
    print("\n[5/5] Generating auto insights...\n")
    insights = generate_insights(pl_summary, expense_breakdown)
    print(insights["summary_text"])

    # ── Done ──────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(f"  ✅ PIPELINE COMPLETE")
    print(f"  📁 Output: {output_path}")
    print(f"  🚀 Dashboard: streamlit run app/dashboard.py")
    print("="*60 + "\n")

    return {
        "df_combined": df_combined,
        "pl_summary": pl_summary,
        "expense_breakdown": expense_breakdown,
        "general_ledger": general_ledger,
        "insights": insights,
        "output_path": output_path,
    }


if __name__ == "__main__":
    run_pipeline()
