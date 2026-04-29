# 📊 Financial Automation System
### Hospitality Financial Reporting | Python + Streamlit

---

## 🗂️ Struktur Project

```
financial_automation/
│
├── data/                        ← Taruh file CSV/Excel mentah di sini
│   ├── january_2024.csv
│   ├── february_2024.csv
│   └── march_2024.csv
│
├── mapping/
│   └── coa_mapping.csv          ← Chart of Accounts: kode akun → kategori
│
├── output/
│   └── financial_report.xlsx    ← Output otomatis (auto-generated)
│
├── app/
│   ├── data_loader.py           ← Load & clean raw data (pandas)
│   ├── report_generator.py      ← Build P&L, export Excel
│   ├── insight_generator.py     ← Rule-based insight engine
│   └── dashboard.py             ← Streamlit visual dashboard
│
├── main.py                      ← Entry point pipeline
├── requirements.txt
└── README.md
```

---

## ⚡ Cara Menjalankan di VS Code

### Step 1: Buka Project
```bash
# Buka folder di VS Code
code financial_automation
```

### Step 2: Buat Virtual Environment
```bash
# Di terminal VS Code (Ctrl + `)
python -m venv venv

# Aktifkan (Windows)
venv\Scripts\activate

# Aktifkan (Mac/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Jalankan Pipeline (Generate Report + Insight)
```bash
python main.py
```
Output: file Excel di `/output/financial_report.xlsx` + insight di terminal.

### Step 5: Jalankan Dashboard
```bash
streamlit run app/dashboard.py
```
Buka browser: http://localhost:8501

---

## 📥 Format Data Input

File CSV/Excel di folder `/data` harus memiliki kolom:

| Kolom          | Keterangan                     |
|----------------|-------------------------------|
| Account Code   | Kode akun (wajib, numerik)    |
| Account Name   | Nama akun                      |
| Debit          | Nominal debit                  |
| Credit         | Nominal kredit                 |

**Baris kosong otomatis diabaikan.** Nama kolom tidak harus persis sama — sistem akan auto-mapping kolom umum (kode_akun, acc_code, dll).

---

## 🗺️ COA Mapping (`mapping/coa_mapping.csv`)

Tambahkan akun baru sesuai kebutuhan:

| account_code | account_name      | category             | subcategory              |
|-------------|-------------------|----------------------|--------------------------|
| 4001        | Food Revenue      | Revenue              | Food & Beverage Revenue  |
| 5001        | Food Cost         | Cost of Goods Sold   | Food Cost                |
| 6001        | Salaries & Wages  | Operating Expense    | Labor Cost               |

**Kategori yang didukung:** Revenue, Cost of Goods Sold, Operating Expense, Other Expense, Balance Sheet

---

## 📊 Output yang Dihasilkan

### 1. Excel Report (`output/financial_report.xlsx`)
- **Sheet 1 — P&L Summary**: Revenue, COGS, Gross Profit, OpEx, Net Profit, semua margin
- **Sheet 2 — Expense Breakdown**: Detail biaya per subcategory per bulan
- **Sheet 3 — General Ledger**: Semua transaksi detail

### 2. Dashboard (Streamlit)
- Revenue vs Cost trend
- Profit margin chart
- Expense breakdown pie chart
- KPI: Food Cost % & Labor Cost % vs threshold
- Auto insight: alert + positif + informasi

### 3. Terminal Insight
```
=== INSIGHT REPORT: March 2024 ===

📈 KINERJA BULAN INI:
   • Revenue      : Rp 212.0 jt
   • Gross Profit : Rp 164.1 jt (77.4%)
   • Net Profit   : Rp 114.4 jt (54.0%)

🟢 POSITIF:
   ✅ Revenue naik konsisten 3 bulan berturut-turut (+21.2%)
   ✅ Food Cost terkontrol di 32.0%

🔴 PERHATIAN:
   ⚠️ Utilities naik 17.3% bulan ini
```

---

## 🏨 KPI Hospitality (Default Threshold)

| KPI            | Warning  | Critical |
|---------------|----------|----------|
| Food Cost %   | > 35%    | > 40%    |
| Labor Cost %  | > 30%    | > 35%    |
| Net Margin    | < 10%    | -        |

> Edit threshold di `app/insight_generator.py` → bagian `THRESHOLDS`

---

## 🔧 Tambah Outlet / Multi-Outlet

Cukup tambahkan file CSV per outlet ke folder `/data`:
```
data/
├── january_2024_outlet_a.csv
├── january_2024_outlet_b.csv
└── february_2024_outlet_a.csv
```
Sistem akan otomatis menggabungkan semua file.

---

## 💼 Best Practice (Portfolio)

1. **Modular code** — setiap file punya satu tanggung jawab jelas
2. **Virtual environment** — selalu pakai `venv`, jangan install global
3. **COA mapping terpisah** — mudah di-update tanpa ubah kode
4. **Type hints & docstrings** — kode lebih readable dan maintainable
5. **Cache di Streamlit** — `@st.cache_data` untuk performa dashboard
6. **Error handling** — file tidak ada / kolom tidak cocok ditangani gracefully

---

*Built for: Financial Data Analyst / Business Analyst Portfolio*
*Stack: Python · Pandas · Openpyxl · Streamlit · Plotly*
