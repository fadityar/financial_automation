"""
app/dashboard.py
----------------
Dashboard Streamlit untuk visualisasi laporan keuangan.
Jalankan: streamlit run app/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import sys

# Tambah root path agar bisa import modul lain
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_loader import load_coa_mapping, load_all_files
from app.report_generator import build_pl_summary, build_expense_breakdown, build_general_ledger
from app.insight_generator import generate_insights

# ── Config ───────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
MAPPING_DIR = os.path.join(BASE_DIR, "mapping", "coa_mapping.csv")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")

# ── Page Setup ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial Dashboard | Hospitality",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0F1117; }
    .metric-card {
        background: linear-gradient(135deg, #1E2130, #252A3D);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid;
        margin-bottom: 10px;
    }
    .stMetric { background: #1E2130; border-radius: 8px; padding: 15px; }
    h1 { color: #E8EAF0; font-family: 'Georgia', serif; }
    .insight-box {
        background: #1E2130;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
        border-left: 3px solid #4CAF50;
    }
    .alert-box {
        background: #2A1A1A;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
        border-left: 3px solid #F44336;
    }
</style>
""", unsafe_allow_html=True)


# ── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    coa = load_coa_mapping(MAPPING_DIR)
    df  = load_all_files(DATA_DIR, coa)
    pl  = build_pl_summary(df)
    exp = build_expense_breakdown(df)
    gl  = build_general_ledger(df)
    return df, pl, exp, gl


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/financial-analytics.png", width=80)
    st.title("🏨 Financial\nDashboard")
    st.markdown("---")
    st.markdown("**Hospitality Analytics**")
    st.markdown("Laporan Keuangan Otomatis")
    st.markdown("---")

    try:
        df, pl_summary, expense_breakdown, general_ledger = load_data()
        months_available = pl_summary["month"].tolist()
        selected_month = st.selectbox("📅 Pilih Bulan", months_available, index=len(months_available)-1)
        st.success(f"✅ {len(months_available)} bulan loaded")
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# ── Main Content ─────────────────────────────────────────────────────────────
st.title("📊 Financial Performance Dashboard")
st.caption(f"Hospitality Financial Analytics | Data terupdate otomatis dari folder /data")

latest_pl = pl_summary[pl_summary["month"] == selected_month].iloc[0]

# ── KPI Row ──────────────────────────────────────────────────────────────────
st.subheader(f"🎯 Key Performance Indicators — {selected_month}")
k1, k2, k3, k4, k5 = st.columns(5)

def format_idr_short(val):
    if abs(val) >= 1e9:
        return f"Rp {val/1e9:.1f}M"
    return f"Rp {val/1e6:.1f} jt"

# Hitung delta vs bulan sebelumnya
def get_delta(col):
    idx = pl_summary[pl_summary["month"] == selected_month].index[0]
    if idx == 0:
        return None
    prev = pl_summary.iloc[idx - 1][col]
    curr = latest_pl[col]
    if prev == 0:
        return None
    return f"{((curr-prev)/prev*100):+.1f}%"

k1.metric("💰 Total Revenue",   format_idr_short(latest_pl["total_revenue"]),   get_delta("total_revenue"))
k2.metric("📦 Gross Profit",    format_idr_short(latest_pl["gross_profit"]),    get_delta("gross_profit"))
k3.metric("💵 Net Profit",      format_idr_short(latest_pl["net_profit"]),      get_delta("net_profit"))
k4.metric("🥩 Food Cost %",     f"{latest_pl['food_cost_%']:.1f}%",            None)
k5.metric("👥 Labor Cost %",    f"{latest_pl['labor_cost_%']:.1f}%",           None)

st.markdown("---")

# ── Charts Row 1 ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📈 Revenue vs Cost Trend")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pl_summary["month"], y=pl_summary["total_revenue"],
        name="Revenue", marker_color="#4FC3F7"
    ))
    fig.add_trace(go.Bar(
        x=pl_summary["month"], y=pl_summary["total_cogs"],
        name="COGS", marker_color="#EF5350"
    ))
    fig.add_trace(go.Bar(
        x=pl_summary["month"], y=pl_summary["total_opex"],
        name="OpEx", marker_color="#FF8A65"
    ))
    fig.add_trace(go.Scatter(
        x=pl_summary["month"], y=pl_summary["net_profit"],
        name="Net Profit", mode="lines+markers",
        line=dict(color="#66BB6A", width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Margin Trend")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=pl_summary["month"], y=pl_summary["gross_margin_%"],
        name="Gross Margin %", mode="lines+markers+text",
        line=dict(color="#4FC3F7", width=2),
        text=[f"{v:.1f}%" for v in pl_summary["gross_margin_%"]],
        textposition="top center"
    ))
    fig2.add_trace(go.Scatter(
        x=pl_summary["month"], y=pl_summary["net_margin_%"],
        name="Net Margin %", mode="lines+markers+text",
        line=dict(color="#66BB6A", width=2),
        text=[f"{v:.1f}%" for v in pl_summary["net_margin_%"]],
        textposition="bottom center"
    ))
    fig2.update_layout(
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        yaxis=dict(ticksuffix="%")
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Charts Row 2 ─────────────────────────────────────────────────────────────
col3, col4 = st.columns([2, 3])

with col3:
    st.subheader(f"🍕 Expense Breakdown — {selected_month}")
    exp_month = expense_breakdown[expense_breakdown["month"] == selected_month]
    if not exp_month.empty:
        fig3 = px.pie(
            exp_month, values="total_amount", names="subcategory",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig3.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("📊 KPI: Food Cost % & Labor Cost %")
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=pl_summary["month"], y=pl_summary["food_cost_%"],
        name="Food Cost %", marker_color="#FF7043"
    ))
    fig4.add_trace(go.Bar(
        x=pl_summary["month"], y=pl_summary["labor_cost_%"],
        name="Labor Cost %", marker_color="#AB47BC"
    ))
    # Threshold lines
    fig4.add_hline(y=35, line_dash="dot", line_color="red",
                   annotation_text="Food Cost Threshold 35%")
    fig4.add_hline(y=30, line_dash="dot", line_color="orange",
                   annotation_text="Labor Cost Threshold 30%")
    fig4.update_layout(
        barmode="group", template="plotly_dark",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        height=300
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Insight Generator ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 Auto Insight Generator")

insight_data = generate_insights(pl_summary, expense_breakdown)

tab1, tab2, tab3 = st.tabs(["🔴 Alerts", "🟢 Positif", "💡 Insight"])

with tab1:
    if insight_data["alerts"]:
        for alert in insight_data["alerts"]:
            st.markdown(f'<div class="alert-box">{alert}</div>', unsafe_allow_html=True)
    else:
        st.success("Tidak ada alert untuk periode ini.")

with tab2:
    if insight_data["positives"]:
        for pos in insight_data["positives"]:
            st.markdown(f'<div class="insight-box">{pos}</div>', unsafe_allow_html=True)
    else:
        st.info("Tidak ada highlight positif.")

with tab3:
    if insight_data["insights"]:
        for ins in insight_data["insights"]:
            st.info(ins)
    else:
        st.info("Tidak ada insight tambahan.")

# ── P&L Table ────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📋 Lihat P&L Summary Table"):
    st.dataframe(
        pl_summary.style.format({
            "total_revenue": "{:,.0f}",
            "total_cogs": "{:,.0f}",
            "gross_profit": "{:,.0f}",
            "total_opex": "{:,.0f}",
            "ebitda": "{:,.0f}",
            "total_other_expense": "{:,.0f}",
            "net_profit": "{:,.0f}",
            "gross_margin_%": "{:.1f}%",
            "net_margin_%": "{:.1f}%",
            "food_cost_%": "{:.1f}%",
            "labor_cost_%": "{:.1f}%",
        }),
        use_container_width=True
    )

with st.expander("📋 Lihat General Ledger"):
    st.dataframe(general_ledger, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Financial Automation System | Built with Python + Streamlit | Hospitality Use Case")
