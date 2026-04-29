"""
app/data_loader.py
------------------
Modul untuk load & clean data dari file CSV/Excel mentah.
Handles: baris kosong, kolom tidak rapi, tipe data, multi-file.
"""

import pandas as pd
import os
import glob


def load_coa_mapping(mapping_path: str) -> pd.DataFrame:
    """Load Chart of Accounts mapping dari file CSV."""
    df = pd.read_csv(mapping_path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["account_code"] = df["account_code"].astype(str).str.strip()
    return df


def clean_raw_file(filepath: str, month_label: str = None) -> pd.DataFrame:
    """
    Load satu file CSV/Excel mentah dan bersihkan.
    
    Args:
        filepath: Path ke file data mentah
        month_label: Label bulan (opsional, auto-detect jika tidak diisi)
    
    Returns:
        DataFrame yang sudah bersih
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    # --- 1. Load file ---
    if ext in [".xlsx", ".xls"]:
        df_raw = pd.read_excel(filepath, header=0)
    else:
        df_raw = pd.read_csv(filepath, header=0)

    # --- 2. Standardisasi nama kolom ---
    df_raw.columns = [str(c).strip().lower().replace(" ", "_") for c in df_raw.columns]

    # Rename kolom umum ke standar
    col_map = {
        "account_code": "account_code",
        "acc_code": "account_code",
        "kode_akun": "account_code",
        "account_name": "account_name",
        "nama_akun": "account_name",
        "debit": "debit",
        "credit": "credit",
        "kredit": "credit",
    }
    df_raw.rename(columns={k: v for k, v in col_map.items() if k in df_raw.columns}, inplace=True)

    # --- 3. Pastikan kolom wajib ada ---
    required_cols = ["account_code", "account_name", "debit", "credit"]
    for col in required_cols:
        if col not in df_raw.columns:
            df_raw[col] = None

    df = df_raw[required_cols].copy()

    # --- 4. Hapus baris kosong (semua kolom kosong) ---
    df.dropna(how="all", inplace=True)
    df = df[df["account_code"].notna()]
    df = df[df["account_code"].astype(str).str.strip() != ""]

    # --- 5. Bersihkan account_code ---
    df["account_code"] = df["account_code"].astype(str).str.strip()

    # Hapus baris yang bukan kode akun (header tersembunyi, dsb)
    df = df[df["account_code"].str.match(r"^\d+")]

    # Normalise float-like codes: "1001.0" → "1001"
    df["account_code"] = df["account_code"].str.replace(r"\.0$", "", regex=True)

    # --- 6. Convert numeric: hapus koma, titik ribuan, dsb ---
    for col in ["debit", "credit"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace(r"[^\d.]", "", regex=True)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --- 7. Tambah label bulan ---
    if month_label:
        df["month"] = month_label
    else:
        # Auto-detect dari nama file: "january_2024.csv" → "January 2024"
        basename = os.path.basename(filepath)
        name_no_ext = os.path.splitext(basename)[0]
        df["month"] = name_no_ext.replace("_", " ").title()

    return df.reset_index(drop=True)


def load_all_files(data_folder: str, coa_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Load semua file CSV/Excel di folder data, bersihkan, dan gabungkan.
    
    Args:
        data_folder: Path folder /data
        coa_mapping: DataFrame mapping COA
    
    Returns:
        DataFrame gabungan semua bulan + mapping kategori
    """
    files = glob.glob(os.path.join(data_folder, "*.csv")) + \
            glob.glob(os.path.join(data_folder, "*.xlsx"))

    if not files:
        raise FileNotFoundError(f"Tidak ada file CSV/Excel di folder: {data_folder}")

    all_dfs = []
    for f in sorted(files):
        print(f"  → Loading: {os.path.basename(f)}")
        df = clean_raw_file(f)
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)

    # --- Merge dengan COA mapping ---
    combined = combined.merge(
        coa_mapping[["account_code", "account_name", "category", "subcategory"]],
        on="account_code",
        how="left",
        suffixes=("_raw", "")
    )

    # Gunakan account_name dari mapping (lebih bersih), fallback ke raw
    if "account_name_raw" in combined.columns:
        combined["account_name"] = combined["account_name"].fillna(combined["account_name_raw"])
        combined.drop(columns=["account_name_raw"], inplace=True)

    # Filter: hanya akun yang ada di mapping (Balance Sheet diabaikan untuk P&L)
    combined = combined[combined["category"].notna()]

    # --- Hitung net amount (untuk P&L logic) ---
    # Revenue: ambil credit; Cost/Expense: ambil debit
    combined["amount"] = combined.apply(
        lambda r: r["credit"] if r["category"] == "Revenue" else r["debit"],
        axis=1
    )

    return combined.reset_index(drop=True)
