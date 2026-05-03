from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

RAW_COLUMN_MAP = {
    "Order Date": "order_date",
    "Year": "year",
    "Order Qty": "order_qty",
    "Cost of Sales": "cost_of_sales",
    "Sales": "sales",
    "Profit": "profit",
    "Channel": "channel",
    "Product Name": "product_name",
    "Manufacturer": "manufacturer",
    "Brand Name": "brand_name",
    "Product Sub Category": "product_sub_category",
    "Product Category": "product_category",
    "Region": "region",
    "City": "city",
    "Country": "country",
}

BASE_DIR = Path(__file__).resolve().parent
SEARCH_ROOTS = [Path.cwd(), BASE_DIR, BASE_DIR.parent]
DATA_CANDIDATES = [
    "SalesData.xlsx",
    "salesdata.xlsx",
    "data/SalesData.xlsx",
    "data/salesdata.xlsx",
]


def find_file(candidates: Iterable[str] = DATA_CANDIDATES) -> Path | None:
    for root in SEARCH_ROOTS:
        for candidate in candidates:
            path = (root / candidate).resolve()
            if path.exists():
                return path
    return None


def load_sales_data(path: str | Path | None = None) -> pd.DataFrame:
    data_path = Path(path) if path is not None else find_file()
    if data_path is None:
        raise FileNotFoundError("SalesData.xlsx tidak ditemukan di workspace.")
    return pd.read_excel(data_path)


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [column.strip() for column in cleaned.columns]
    cleaned = cleaned.rename(columns=RAW_COLUMN_MAP)

    if "order_date" not in cleaned.columns:
        raise KeyError("Kolom 'Order Date' tidak ditemukan pada data.")

    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    cleaned = cleaned.dropna(subset=["order_date"]).copy()

    for column in ["order_qty", "cost_of_sales", "sales", "profit"]:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").fillna(0)

    for column in [
        "channel",
        "product_name",
        "manufacturer",
        "brand_name",
        "product_sub_category",
        "product_category",
        "region",
        "city",
        "country",
    ]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype(str).str.strip()

    cleaned["year"] = cleaned["order_date"].dt.year.astype("int64")
    cleaned["month"] = cleaned["order_date"].dt.month.astype("int64")
    cleaned["month_name"] = cleaned["order_date"].dt.strftime("%b")
    cleaned["order_month"] = cleaned["order_date"].dt.to_period("M").dt.to_timestamp()
    cleaned["order_day_name"] = cleaned["order_date"].dt.day_name()

    cleaned["profit_margin"] = np.where(
        cleaned["sales"] != 0,
        cleaned["profit"] / cleaned["sales"],
        0,
    )

    cleaned = cleaned.sort_values("order_date").reset_index(drop=True)
    return cleaned


def quality_report(df: pd.DataFrame) -> dict[str, object]:
    report = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    if "order_date" in df.columns and "year" in df.columns:
        report["date_range"] = (df["order_date"].min(), df["order_date"].max())
        report["year_mismatches"] = int((df["order_date"].dt.year != df["year"]).sum())
    return report


def metric_summary(df: pd.DataFrame) -> dict[str, float]:
    return {
        "total_sales": float(df["sales"].sum()),
        "total_profit": float(df["profit"].sum()),
        "total_orders": float(df.shape[0]),
        "total_quantity": float(df["order_qty"].sum()),
        "avg_profit_margin": float(df["profit_margin"].mean()),
    }


def top_n_by_metric(
    df: pd.DataFrame,
    group_column: str,
    metric: str = "sales",
    n: int = 10,
) -> pd.DataFrame:
    summary = (
        df.groupby(group_column, as_index=False)
        .agg({metric: "sum", "profit": "sum", "order_qty": "sum"})
        .sort_values(metric, ascending=False)
        .head(n)
    )
    return summary


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("order_month", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            order_qty=("order_qty", "sum"),
        )
        .sort_values("order_month")
    )
    return summary

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Analisis Data Penjualan",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Main Background */
.main { background: #0f172a; }
.stApp { background-color: #0f172a; }

/* Sidebar */
[data-testid="stSidebar"] { 
    background-color: #1e293b; 
    border-right: 1px solid #334155;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px; 
    padding: 20px; 
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.9rem; font-weight: 500; }
[data-testid="stMetricValue"] { color: #f8fafc !important; font-weight: 700; }

/* Headings */
h1, h2, h3 { color: #f8fafc !important; font-weight: 600; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #334155; }
.stTabs [data-baseweb="tab"] {
    background: transparent; 
    border-radius: 8px 8px 0 0;
    color: #94a3b8; 
    border: none;
    padding: 10px 16px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(59, 130, 246, 0.1) !important;
    color: #60a5fa !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* Expanders */
div[data-testid="stExpander"] {
    background: #1e293b; 
    border: 1px solid #334155;
    border-radius: 12px;
}
div[data-testid="stExpander"] summary { color: #f8fafc; font-weight: 600; }

/* Insight Box */
.insight-box {
    background: rgba(59, 130, 246, 0.1);
    border-left: 4px solid #3b82f6; 
    border-radius: 8px;
    padding: 16px; 
    margin: 12px 0; 
    color: #e2e8f0;
    font-size: 0.95rem;
    line-height: 1.5;
}
.insight-box b { color: #60a5fa; }

/* Divider */
.section-divider { border-top: 1px solid #334155; margin: 32px 0; }

/* Dataframes */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; border: 1px solid #334155; }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(l=40, r=20, t=50, b=40),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
    hovermode="x unified"
)

# Professional Blue Color Palette
COLORS = ["#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#1d4ed8", "#2563eb", "#0ea5e9", "#38bdf8", "#7dd3fc"]
SEQ_COLORS = px.colors.sequential.Blues


def fmt(v: float) -> str:
    return f"${v:,.0f}"

def fmt_pct(v: float) -> str:
    return f"{v*100:.1f}%"


@st.cache_data(show_spinner=False)
def get_data() -> pd.DataFrame:
    return clean_sales_data(load_sales_data())


def apply_filters(df, start, end, channels, regions, categories):
    mask = (
        (df["order_date"] >= pd.to_datetime(start))
        & (df["order_date"] <= pd.to_datetime(end))
        & df["channel"].isin(channels)
        & df["region"].isin(regions)
        & df["product_category"].isin(categories)
    )
    return df[mask].copy()


# ── Load Data ────────────────────────────────────────────────
try:
    df = get_data()
except FileNotFoundError as e:
    st.error(str(e)); st.stop()

min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filter Data")
    date_range = st.date_input("📅 Rentang Tanggal", value=(min_date, max_date),
                                min_value=min_date, max_value=max_date)
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if not isinstance(date_range, (list, tuple)) else date_range[0]

    channels = sorted(df["channel"].unique())
    regions = sorted(df["region"].unique())
    categories = sorted(df["product_category"].unique())
    sel_ch = st.multiselect("🏪 Channel", channels, default=channels)
    sel_rg = st.multiselect("🌍 Region", regions, default=regions)
    sel_cat = st.multiselect("📦 Kategori Produk", categories, default=categories)
    
    st.markdown("---")
    st.markdown("##### 📊 Dashboard Analisis Penjualan")
    st.caption("Data: SalesData.xlsx • Feb 2018 – Feb 2021")

fdf = apply_filters(df, start_date, end_date, sel_ch, sel_rg, sel_cat)
if fdf.empty:
    st.warning("Tidak ada data yang cocok dengan filter."); st.stop()

ms = metric_summary(fdf)

# ── Header ───────────────────────────────────────────────────
st.markdown("# 📊 Dashboard Analisis Data Penjualan")
st.caption("Analisis komprehensif penjualan, profit, channel, region, dan kategori produk dengan antarmuka yang bersih.")

# ── KPI Cards ────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Total Sales", fmt(ms["total_sales"]))
c2.metric("📈 Total Profit", fmt(ms["total_profit"]))
c3.metric("📋 Total Orders", f"{ms['total_orders']:,.0f}")
c4.metric("📦 Total Quantity", f"{ms['total_quantity']:,.0f}")
c5.metric("💎 Avg Margin", fmt_pct(ms["avg_profit_margin"]))

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Rumusan Masalah ──────────────────────────────────────────
with st.expander("📋 Rumusan Masalah (8 Pertanyaan Penelitian)", expanded=False):
    problems = [
        "Bagaimana **tren penjualan dan profit** berubah dari waktu ke waktu?",
        "**Channel penjualan** mana yang memberikan kontribusi terbesar?",
        "**Region** mana yang memiliki performa penjualan tertinggi?",
        "**Kategori produk** apa yang paling diminati dan menguntungkan?",
        "Bagaimana **profit margin** bervariasi antar kategori dan channel?",
        "Seberapa signifikan **transaksi dengan profit negatif (kerugian)**?",
        "Bagaimana performa berdasarkan **negara dan kota**?",
        "Bagaimana **pola penjualan berdasarkan hari** dalam seminggu?",
    ]
    for i, p in enumerate(problems, 1):
        st.markdown(f"**{i}.** {p}")

# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Tren Waktu", "🏪 Channel & Region", "📦 Produk & Kategori",
    "💎 Profitabilitas", "🌍 Geografi", "🔍 Insight & Kesimpulan"
])

# ── TAB 1: Tren Waktu ───────────────────────────────────────
with tab1:
    st.subheader("Tren Penjualan & Profit Bulanan")
    mdf = monthly_summary(fdf)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=mdf["order_month"], y=mdf["sales"], name="Sales",
                             line=dict(color="#3b82f6", width=3), fill="tozeroy",
                             fillcolor="rgba(59, 130, 246, 0.1)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=mdf["order_month"], y=mdf["profit"], name="Profit",
                             line=dict(color="#0ea5e9", width=3, dash="dot"), fill="tozeroy",
                             fillcolor="rgba(14, 165, 233, 0.05)"), secondary_y=True)
    fig.update_layout(**PLOTLY_LAYOUT, title="Tren Bulanan: Sales vs Profit",
                      legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Pertumbuhan Tahunan (Year-over-Year)")
    yearly = fdf.groupby("year")["sales"].sum().reset_index()
    yearly["growth"] = yearly["sales"].pct_change() * 100
    col_a, col_b = st.columns(2)
    with col_a:
        fig_y = px.bar(yearly, x="year", y="sales", text_auto=",.0f",
                       color_discrete_sequence=["#3b82f6"], title="Total Sales per Tahun")
        fig_y.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_y, use_container_width=True)
    with col_b:
        fdf["quarter"] = fdf["order_date"].dt.quarter
        qdf = fdf.groupby(["year", "quarter"], as_index=False)["sales"].sum()
        qdf["label"] = qdf["year"].astype(str) + " Q" + qdf["quarter"].astype(str)
        fig_q = px.bar(qdf, x="label", y="sales", color="year",
                       color_discrete_sequence=COLORS, title="Sales per Kuartal")
        fig_q.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_q, use_container_width=True)

    st.markdown('<div class="insight-box">📌 <b>Insight:</b> Penjualan menurun YoY — dari $18.9M (2018) ke $17.7M (2019, -6.2%) ke $17.3M (2020, -2.6%). Puncak bulanan terjadi di Jun 2018 ($2.05M) dan Jan 2019 ($2.08M).</div>', unsafe_allow_html=True)

# ── TAB 2: Channel & Region ─────────────────────────────────
with tab2:
    st.subheader("Kontribusi Channel & Region")
    col1, col2 = st.columns(2)
    with col1:
        ch_df = fdf.groupby("channel", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
        fig_ch = px.pie(ch_df, values="sales", names="channel", hole=0.5,
                        color_discrete_sequence=COLORS, title="Distribusi Sales per Channel")
        fig_ch.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_ch, use_container_width=True)
    with col2:
        rg_df = fdf.groupby("region", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
        fig_rg = px.pie(rg_df, values="sales", names="region", hole=0.5,
                        color_discrete_sequence=COLORS[2:], title="Distribusi Sales per Region")
        fig_rg.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_rg, use_container_width=True)

    st.subheader("Channel × Region Heatmap")
    cross = pd.crosstab(fdf["region"], fdf["channel"], values=fdf["sales"], aggfunc="sum").fillna(0)
    fig_hm = px.imshow(cross, text_auto=",.0f", color_continuous_scale="Blues",
                       title="Sales: Channel vs Region", aspect="auto")
    fig_hm.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_hm, use_container_width=True)

    st.markdown('<div class="insight-box">📌 <b>Insight:</b> Store mendominasi 57.3% total sales. Catalog HANYA beroperasi di North America ($5.0M) — ekspansi ke Asia & Europe berpotensi besar.</div>', unsafe_allow_html=True)

# ── TAB 3: Produk & Kategori ─────────────────────────────────
with tab3:
    st.subheader("Top Kategori & Sub-Kategori Produk")
    col1, col2 = st.columns(2)
    with col1:
        cat_df = top_n_by_metric(fdf, "product_category", "sales", 10)
        fig_cat = px.bar(cat_df.sort_values("sales"), x="sales", y="product_category",
                         orientation="h", color="sales", color_continuous_scale="Blues",
                         title="Sales per Kategori Produk")
        fig_cat.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)
    with col2:
        scat_df = top_n_by_metric(fdf, "product_sub_category", "sales", 10)
        fig_sc = px.bar(scat_df.sort_values("sales"), x="sales", y="product_sub_category",
                        orientation="h", color="sales", color_continuous_scale="Blues",
                        title="Top 10 Sub-Kategori")
        fig_sc.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        st.plotly_chart(fig_sc, use_container_width=True)

    st.subheader("Top 10 Brand / Manufacturer")
    col1, col2 = st.columns(2)
    with col1:
        brand_df = top_n_by_metric(fdf, "brand_name", "sales", 10)
        fig_br = px.bar(brand_df.sort_values("sales"), x="sales", y="brand_name",
                        orientation="h", color_discrete_sequence=["#60a5fa"],
                        title="Top 10 Brand")
        fig_br.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_br, use_container_width=True)
    with col2:
        mfg_df = top_n_by_metric(fdf, "manufacturer", "sales", 10)
        fig_mf = px.bar(mfg_df.sort_values("sales"), x="sales", y="manufacturer",
                        orientation="h", color_discrete_sequence=["#3b82f6"],
                        title="Top 10 Manufacturer")
        fig_mf.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_mf, use_container_width=True)

    st.markdown('<div class="insight-box">📌 <b>Insight:</b> Computers ($21.3M) dan Cameras ($17.0M) menyumbang 69% total sales. Brand Fabrikam mendominasi dengan 21.8% share.</div>', unsafe_allow_html=True)

# ── TAB 4: Profitabilitas ────────────────────────────────────
with tab4:
    st.subheader("Analisis Profit Margin")
    col1, col2 = st.columns(2)
    with col1:
        pm_cat = fdf.groupby("product_category", as_index=False).agg(
            avg_margin=("profit_margin", "mean"), total_profit=("profit", "sum")
        ).sort_values("avg_margin", ascending=True)
        fig_pm = px.bar(pm_cat, x="avg_margin", y="product_category", orientation="h",
                        color="avg_margin", color_continuous_scale="Blues",
                        title="Avg Profit Margin per Kategori")
        fig_pm.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        fig_pm.update_traces(text=[f"{v*100:.1f}%" for v in pm_cat["avg_margin"]], textposition="outside")
        st.plotly_chart(fig_pm, use_container_width=True)
    with col2:
        pm_ch = fdf.groupby("channel", as_index=False).agg(
            avg_margin=("profit_margin", "mean"), total_profit=("profit", "sum")
        ).sort_values("avg_margin", ascending=True)
        fig_pmc = px.bar(pm_ch, x="avg_margin", y="channel", orientation="h",
                         color="avg_margin", color_continuous_scale="Blues",
                         title="Avg Profit Margin per Channel")
        fig_pmc.update_layout(**PLOTLY_LAYOUT, showlegend=False)
        fig_pmc.update_traces(text=[f"{v*100:.1f}%" for v in pm_ch["avg_margin"]], textposition="outside")
        st.plotly_chart(fig_pmc, use_container_width=True)

    st.subheader("Analisis Transaksi Rugi (Profit Negatif)")
    neg = fdf[fdf["profit"] < 0]
    total_neg = neg["profit"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Transaksi Rugi", f"{len(neg):,}")
    col2.metric("💸 Total Kerugian", f"${abs(total_neg):,.0f}")
    col3.metric("📊 % dari Total Transaksi", f"{len(neg)/len(fdf)*100:.1f}%")

    if not neg.empty:
        neg_cat = neg.groupby("product_category", as_index=False)["profit"].sum().sort_values("profit")
        fig_neg = px.bar(neg_cat, x="profit", y="product_category", orientation="h",
                         color_discrete_sequence=["#ef4444"], title="Kerugian per Kategori")
        fig_neg.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_neg, use_container_width=True)

    st.subheader("Sales vs Profit Scatter (per Sub-Kategori)")
    sp = fdf.groupby("product_sub_category", as_index=False).agg(
        sales=("sales","sum"), profit=("profit","sum"), qty=("order_qty","sum")
    )
    fig_sp = px.scatter(sp, x="sales", y="profit", size="qty", color="profit",
                        hover_name="product_sub_category",
                        color_continuous_scale="RdBu", title="Sales vs Profit per Sub-Kategori")
    fig_sp.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_sp, use_container_width=True)

    st.markdown('<div class="insight-box">📌 <b>Insight:</b> Overall margin 64.25%. Cameras margin tertinggi (64.0%). 1.545 transaksi (11.9%) rugi senilai $2.7M — Computers paling terdampak (-$1.15M).</div>', unsafe_allow_html=True)

# ── TAB 5: Geografi ──────────────────────────────────────────
with tab5:
    st.subheader("Performa per Negara & Kota")
    col1, col2 = st.columns(2)
    with col1:
        country_df = fdf.groupby("country", as_index=False).agg(
            sales=("sales","sum"), profit=("profit","sum")
        ).sort_values("sales", ascending=False).head(10)
        fig_co = px.bar(country_df, x="country", y="sales", color="profit",
                        color_continuous_scale="Blues", title="Top 10 Negara")
        fig_co.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_co, use_container_width=True)
    with col2:
        city_df = fdf.groupby("city", as_index=False).agg(
            sales=("sales","sum"), profit=("profit","sum")
        ).sort_values("sales", ascending=False).head(10)
        fig_ci = px.bar(city_df, x="city", y="sales", color="profit",
                        color_continuous_scale="Blues", title="Top 10 Kota")
        fig_ci.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_ci, use_container_width=True)

    st.subheader("Pola Penjualan per Hari")
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = fdf.groupby("order_day_name", as_index=False).agg(
        sales=("sales","sum"), count=("sales","count")
    )
    dow["order_day_name"] = pd.Categorical(dow["order_day_name"], categories=day_order, ordered=True)
    dow = dow.sort_values("order_day_name")
    fig_dow = px.bar(dow, x="order_day_name", y="sales", color="sales",
                     color_continuous_scale="Blues", title="Sales per Hari dalam Seminggu",
                     text_auto=",.0f")
    fig_dow.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_dow, use_container_width=True)

    st.markdown('<div class="insight-box">📌 <b>Insight:</b> USA ($31.6M) mendominasi, namun Beijing ($6.6M) adalah kota #1. Jumat konsisten sebagai hari dengan penjualan tertinggi ($8.4M).</div>', unsafe_allow_html=True)

# ── TAB 6: Insight & Kesimpulan ──────────────────────────────
with tab6:
    st.subheader("💡 10 Insight Utama")
    insights = [
        ("📉 Tren Menurun YoY", "Penjualan turun dari $18.9M (2018) → $17.7M (2019, -6.2%) → $17.3M (2020, -2.6%). Tren negatif konsisten memerlukan strategi pemulihan."),
        ("🏪 Store Dominasi 57%", "Channel Store menyumbang 57.3% total sales ($31.7M). Online hanya 20.8% — potensi pertumbuhan besar di era digital."),
        ("🌎 NA = 60% Revenue", "North America menyumbang 59.4% total revenue. Ketergantungan tinggi — diversifikasi ke Asia (22.4%) dan Europe (18.2%) penting."),
        ("💻 2 Kategori = 69% Sales", "Computers ($21.3M, 38.5%) dan Cameras ($17.0M, 30.8%) mendominasi — konsentrasi produk sangat tinggi."),
        ("📸 Cameras Margin Terbaik", "Cameras memiliki profit margin tertinggi (64.0%) dengan volume tinggi — kategori 'golden goose'."),
        ("🔴 $2.7M Kerugian", "1.545 transaksi (11.9%) mengalami kerugian. Computers paling terdampak (-$1.15M). Perlu audit pricing."),
        ("🏙️ Beijing Kota #1", "Beijing ($6.6M) melampaui semua kota AS secara individual — potensi pasar Asia sangat besar."),
        ("📅 Jumat Tertinggi", "Jumat konsisten sebagai hari penjualan tertinggi ($8.4M) — cocok untuk kampanye 'Friday Deals'."),
        ("🏷️ Fabrikam Dominan", "Brand Fabrikam menyumbang 21.8% total sales ($12.1M). Top 5 brand = 74.4% total penjualan."),
        ("📮 Catalog Hanya di NA", "Channel Catalog hanya beroperasi di North America ($5.0M). Ekspansi ke Asia & Europe = peluang besar."),
    ]
    for title, desc in insights:
        st.markdown(f'<div class="insight-box"><b>{title}</b><br>{desc}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("✅ Kesimpulan & Rekomendasi")

    conclusions = {
        "Tren Penjualan": "Menurun YoY (-6.2%, -2.6%). Puncak di pertengahan & akhir tahun menunjukkan pola musiman.",
        "Channel Terbaik": "Store (57.3%) mendominasi dengan margin tertinggi (61.5%). Online potensial untuk dikembangkan.",
        "Region Terbaik": "North America (59.4%). Asia & Europe masih punya ruang pertumbuhan besar.",
        "Kategori Terlaris": "Computers ($21.3M) & Cameras ($17.0M) = 69.3% total sales.",
        "Profit Margin": "Overall 64.25%. Cameras tertinggi (64.0%), Audio terendah (56.9%).",
        "Transaksi Rugi": "1.545 transaksi (11.9%) rugi $2.7M. Computers paling terdampak.",
        "Geografi": "USA ($31.6M) & China ($7.6M) pasar terbesar. Beijing kota #1.",
        "Pola Hari": "Jumat konsisten tertinggi. Tidak ada perbedaan signifikan weekday vs weekend.",
    }
    for k, v in conclusions.items():
        st.markdown(f"**{k}:** {v}")

    st.markdown("---")
    st.subheader("🎯 Rekomendasi Strategis")
    recs = [
        "**Atasi Tren Penurunan** — Diversifikasi produk & kampanye agresif",
        "**Optimalkan Channel Online** — Potensi pertumbuhan terbesar di era digital",
        "**Ekspansi Catalog ke Asia & Europe** — Revenue stream baru",
        "**Investigasi Kerugian $2.7M** — Audit pricing di kategori Computers",
        "**Perkuat Pasar Asia (Beijing/China)** — Kota sales tertinggi",
        "**Kampanye Friday Deals** — Leverage pola penjualan Jumat",
        "**Pertahankan Investasi di Cameras** — Margin & volume terbaik",
    ]
    for r in recs:
        st.markdown(f"- {r}")

# ── Footer ───────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Data Quality Check")
report = quality_report(fdf)
qc1, qc2, qc3, qc4 = st.columns(4)
qc1.metric("Baris", f"{report['rows']:,}")
qc2.metric("Kolom", f"{report['columns']}")
qc3.metric("Missing Values", f"{report['missing_values']}")
qc4.metric("Duplikat", f"{report['duplicate_rows']}")

st.subheader("📄 Cuplikan Data")
show_cols = ["order_date","channel","region","country","product_category",
             "product_sub_category","brand_name","sales","profit","profit_margin"]
st.dataframe(fdf[show_cols].head(50), use_container_width=True)
st.caption(f"Menampilkan 50 dari {len(fdf):,} baris data terfilter")
