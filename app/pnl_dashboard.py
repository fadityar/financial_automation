"""
app/pnl_dashboard.py
--------------------
Dashboard Streamlit untuk file PNL.xlsx (format resort/villa).
Jalankan: streamlit run app/pnl_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.pnl_adapter import load_pnl_file, build_insights_from_pnl

PNL_PATH = os.path.join(BASE_DIR, "data", "PNL.xlsx")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resort P&L Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stMetric"] { background:#1E2130; border-radius:10px; padding:12px; }
    .alert { background:#2A1A1A; border-left:4px solid #EF5350; border-radius:8px; padding:12px; margin:4px 0; }
    .positive { background:#1A2A1A; border-left:4px solid #66BB6A; border-radius:8px; padding:12px; margin:4px 0; }
    .info-box { background:#1A1E2A; border-left:4px solid #42A5F5; border-radius:8px; padding:12px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_data():
    return load_pnl_file(PNL_PATH)

try:
    data = get_data()
    summary = data['summary_df']
    revenue_breakdown = data['revenue_df']
except Exception as e:
    st.error(f"❌ Error membaca PNL.xlsx: {e}")
    st.stop()

def fmt_idr(v):
    if abs(v) >= 1e9: return f"Rp {v/1e9:.2f}M"
    if abs(v) >= 1e6: return f"Rp {v/1e6:.1f} jt"
    return f"Rp {v:,.0f}"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏨 Resort P&L\nDashboard")
    st.markdown("---")
    selected = st.selectbox("📅 Bulan Aktif", summary['month'].tolist(), index=0)
    st.markdown("---")
    show_raw = st.checkbox("Tampilkan Data Mentah", value=False)
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.caption("Sumber: PNL.xlsx")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 Resort Financial Dashboard")
st.caption(f"Data: Mar 2025 — Mar 2026 | {len(summary)} bulan | Aktif: **{selected}**")

row = summary[summary['month'] == selected].iloc[0]
idx = summary[summary['month'] == selected].index[0]
prev_row = summary.iloc[idx + 1] if idx + 1 < len(summary) else None

def delta(col):
    if prev_row is None: return None
    c, p = row[col], prev_row[col]
    if p == 0: return None
    return f"{((c-p)/abs(p)*100):+.1f}%"

# ── KPIs ───────────────────────────────────────────────────────────────────────
st.subheader(f"🎯 KPI — {selected}")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("💰 Revenue",     fmt_idr(row['total_revenue']),  delta('total_revenue'))
c2.metric("📦 Gross Profit",fmt_idr(row['gross_profit']),   delta('gross_profit'))
c3.metric("⚡ EBITDA",      fmt_idr(row['ebitda']),         delta('ebitda'))
c4.metric("💵 Net Income",  fmt_idr(row['net_income']),     delta('net_income'))
c5.metric("👥 Labor %",     f"{row['labor_cost_%']:.1f}%",  None)
c6.metric("📉 Net Margin",  f"{row['net_margin_%']:.1f}%",  delta('net_margin_%'))

st.markdown("---")

# ── Chart 1: Revenue & Profit Trend ───────────────────────────────────────────
col1, col2 = st.columns([3, 2])
with col1:
    st.subheader("📈 Revenue & Income Trend (Rp Juta)")
    fig = go.Figure()
    x = summary['month'][::-1]

    fig.add_trace(go.Bar(x=x, y=(summary['total_revenue'][::-1]/1e6),
                         name='Revenue', marker_color='#42A5F5', opacity=0.8))
    fig.add_trace(go.Bar(x=x, y=(summary['total_cogs'][::-1]/1e6),
                         name='COGS', marker_color='#EF5350', opacity=0.8))
    fig.add_trace(go.Bar(x=x, y=(summary['total_payroll'][::-1]/1e6),
                         name='Payroll', marker_color='#AB47BC', opacity=0.8))
    fig.add_trace(go.Scatter(x=x, y=(summary['net_income'][::-1]/1e6),
                             name='Net Income', mode='lines+markers',
                             line=dict(color='#FFCA28', width=3), marker=dict(size=7)))
    fig.update_layout(template='plotly_dark', barmode='group',
                      legend=dict(orientation='h', y=-0.2),
                      margin=dict(l=0,r=0,t=10,b=0), height=360)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Margin Trend")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x, y=summary['gross_margin_%'][::-1],
                              name='Gross Margin', mode='lines+markers',
                              line=dict(color='#26C6DA', width=2)))
    fig2.add_trace(go.Scatter(x=x, y=summary['ebitda_margin_%'][::-1],
                              name='EBITDA Margin', mode='lines+markers',
                              line=dict(color='#FFCA28', width=2)))
    fig2.add_trace(go.Scatter(x=x, y=summary['net_margin_%'][::-1],
                              name='Net Margin', mode='lines+markers',
                              line=dict(color='#66BB6A', width=2)))
    fig2.add_hline(y=0, line_dash='dash', line_color='red', annotation_text='Break Even')
    fig2.update_layout(template='plotly_dark',
                       yaxis=dict(ticksuffix='%'),
                       legend=dict(orientation='h', y=-0.2),
                       margin=dict(l=0,r=0,t=10,b=0), height=360)
    st.plotly_chart(fig2, use_container_width=True)

# ── Chart 2: Revenue Breakdown & Cost ─────────────────────────────────────────
col3, col4 = st.columns([2, 3])

with col3:
    st.subheader(f"🍕 Revenue Mix — {selected}")
    rev_m = revenue_breakdown[revenue_breakdown['month'] == selected].copy()
    rev_m = rev_m[rev_m['amount'] > 0]
    if not rev_m.empty:
        fig3 = px.pie(rev_m, values='amount', names='segment', hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_layout(template='plotly_dark', height=320,
                           margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("💰 Revenue per Segmen (Trend)")
    segments = revenue_breakdown['segment'].unique()
    fig4 = go.Figure()
    colors = px.colors.qualitative.Set2
    for i, seg in enumerate(segments):
        seg_data = revenue_breakdown[revenue_breakdown['segment']==seg].iloc[::-1]
        fig4.add_trace(go.Scatter(
            x=seg_data['month'], y=seg_data['amount']/1e6,
            name=seg, mode='lines+markers',
            line=dict(color=colors[i % len(colors)], width=2)
        ))
    fig4.update_layout(template='plotly_dark',
                       yaxis=dict(title='Rp Juta'),
                       legend=dict(orientation='h', y=-0.25),
                       margin=dict(l=0,r=0,t=10,b=0), height=320)
    st.plotly_chart(fig4, use_container_width=True)

# ── Cost Efficiency Chart ──────────────────────────────────────────────────────
st.subheader("⚖️ Cost Efficiency (%  dari Revenue)")
fig5 = go.Figure()
fig5.add_trace(go.Bar(x=x, y=summary['cogs_%'][::-1], name='COGS %',
                      marker_color='#EF5350'))
fig5.add_trace(go.Bar(x=x, y=summary['labor_cost_%'][::-1], name='Labor %',
                      marker_color='#AB47BC'))
energy_pct_series = (summary['total_energy'] / summary['total_revenue'] * 100).round(2)
fig5.add_trace(go.Bar(x=x, y=energy_pct_series[::-1], name='Energy %',
                      marker_color='#FFA726'))
fig5.add_hline(y=40, line_dash='dot', line_color='white',
               annotation_text='Labor Threshold 40%')
fig5.update_layout(template='plotly_dark', barmode='stack',
                   yaxis=dict(ticksuffix='%'),
                   legend=dict(orientation='h', y=-0.2),
                   margin=dict(l=0,r=0,t=10,b=0), height=300)
st.plotly_chart(fig5, use_container_width=True)

# ── Insights ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 Auto Insight Generator")
ins = build_insights_from_pnl(summary)

t1, t2, t3 = st.tabs(["🔴 Alerts", "🟢 Positif", "💡 Info"])
with t1:
    if ins['alerts']:
        for a in ins['alerts']:
            st.markdown(f'<div class="alert">{a}</div>', unsafe_allow_html=True)
    else:
        st.success("Tidak ada alert.")
with t2:
    for p in ins['positives']:
        st.markdown(f'<div class="positive">{p}</div>', unsafe_allow_html=True)
with t3:
    for i in ins['insights']:
        st.markdown(f'<div class="info-box">{i}</div>', unsafe_allow_html=True)

# ── Raw Data ──────────────────────────────────────────────────────────────────
if show_raw:
    st.markdown("---")
    st.subheader("📋 Data Lengkap P&L Summary")
    st.dataframe(summary.style.format({
        col: "{:,.0f}" for col in summary.columns if summary[col].dtype in ['float64','int64']
        and '%' not in col
    } | {col: "{:.1f}%" for col in summary.columns if '%' in col}),
    use_container_width=True)

st.markdown("---")
st.caption("Resort Financial Dashboard | Powered by Python + Streamlit + Plotly")
