import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Explore Areas — InvestStay", layout="wide")

# ── Shared styles (duplicated so pages work standalone) ────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
section[data-testid="stSidebar"] { background-color: #1B2A4A; }
section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
.main .block-container { padding-top: 2rem; max-width: 1200px; }
.page-header { background: linear-gradient(135deg, #1B2A4A 0%, #0D9488 100%); border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.5rem; color: white; }
.page-header h1 { font-family: 'Sora', sans-serif; font-size: 1.6rem; font-weight: 800; margin: 0 0 0.3rem 0; color: white; }
.page-header p { font-size: 0.9rem; color: #B2D8D8; margin: 0; }
.section-label { font-size: 0.72rem; font-weight: 600; color: #0D9488; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem; }
hr { border: none; border-top: 1px solid #E2E8F0; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 1.5rem 0;'>
        <div style='font-family: Sora, sans-serif; font-size: 1.5rem; font-weight: 800; color: white;'>🏠 InvestStay</div>
        <div style='font-size: 0.78rem; color: #7FB3D3; margin-top: 0.2rem;'>Analyse. Invest. Grow.</div>
    </div>
    <hr style='border-color: #2D4A6A; margin: 0 0 1.2rem 0;'>
    """, unsafe_allow_html=True)
    st.page_link("app.py",               label="🏠  Home")
    st.page_link("pages/1_explore.py",   label="🔍  Explore Areas")
    st.page_link("pages/2_compare.py",   label="⚖️  Compare Cities")
    st.page_link("pages/3_sentiment.py", label="💬  Guest Sentiment")
    st.page_link("pages/4_insights.py",  label="🤖  AI Insights")

st.markdown("""
<div class='page-header'>
    <h1>🔍 Explore Areas</h1>
    <p>Filter and rank MSOAs and LADs by investment yield, price, and amenities.</p>
</div>
""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

@st.cache_data
def load_msoa():
    path = os.path.join(DATA_DIR, "msoa_investment_summary.csv")
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

@st.cache_data
def load_sentiment():
    path = os.path.join(DATA_DIR, "msoa_review_sentiment.csv")
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

msoa_df = load_msoa()
sent_df = load_sentiment()

if msoa_df.empty:
    st.warning("No data found. Add `msoa_investment_summary.csv` to the `data/` folder.")
    st.stop()

# Merge sentiment if available
if not sent_df.empty:
    msoa_df = msoa_df.merge(
        sent_df[["msoa_code", "avg_sentiment_score", "pct_positive", "review_count"]],
        on="msoa_code", how="left"
    )

# ── Filters ────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>Filters</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    cities = sorted(msoa_df["city"].dropna().unique())
    selected_cities = st.multiselect("City", cities, default=cities)

with col2:
    max_price = int(msoa_df["median_house_price_2025"].max())
    min_price = int(msoa_df["median_house_price_2025"].min())
    price_range = st.slider(
        "Max house price (£)",
        min_value=min_price,
        max_value=max_price,
        value=max_price,
        step=25000,
        format="£%d"
    )

with col3:
    min_yield = float(msoa_df["str_gross_yield"].min())
    max_yield = float(msoa_df["str_gross_yield"].max())
    yield_threshold = st.slider(
        "Min STR gross yield",
        min_value=min_yield,
        max_value=max_yield,
        value=min_yield,
        step=0.001,
        format="%.1%%"
    )

with col4:
    rail_options = ["Any", "15 min walk", "30 min walk"]
    rail_filter = st.selectbox("Rail access", rail_options)

if not sent_df.empty:
    min_sentiment = st.slider(
        "Min average guest sentiment (-1 to +1)",
        min_value=-1.0, max_value=1.0, value=-1.0, step=0.05
    )
else:
    min_sentiment = -1.0

st.markdown("<hr>", unsafe_allow_html=True)

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = msoa_df[
    (msoa_df["city"].isin(selected_cities)) &
    (msoa_df["median_house_price_2025"] <= price_range) &
    (msoa_df["str_gross_yield"] >= yield_threshold)
].copy()

if rail_filter == "15 min walk":
    filtered = filtered[filtered["less_than_15_minute_walk"] == 1]
elif rail_filter == "30 min walk":
    filtered = filtered[
        (filtered["less_than_15_minute_walk"] == 1) |
        (filtered["less_than_30_minute_walk"] == 1)
    ]

if not sent_df.empty and "avg_sentiment_score" in filtered.columns:
    filtered = filtered[filtered["avg_sentiment_score"].fillna(-1) >= min_sentiment]

st.markdown(f"<div class='section-label'>{len(filtered):,} areas match your filters</div>", unsafe_allow_html=True)

# ── Chart ──────────────────────────────────────────────────────────────────────
if not filtered.empty:
    fig = px.scatter(
        filtered.dropna(subset=["str_gross_yield", "median_house_price_2025"]),
        x="median_house_price_2025",
        y="str_gross_yield",
        color="city",
        size="total_listings",
        hover_name="msoa_name",
        hover_data={"lad_name": True, "str_vs_ltr_yield_delta": ":.2%",
                    "median_nightly_price": ":£.0f", "city": False},
        labels={
            "median_house_price_2025": "Median House Price (£)",
            "str_gross_yield": "STR Gross Yield",
            "city": "City"
        },
        color_discrete_map={
            "london": "#1B2A4A", "manchester": "#0D9488",
            "bristol": "#0F766E", "edinburgh": "#7FB3D3"
        },
        title="STR Yield vs House Price by MSOA"
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="Inter",
        yaxis_tickformat=".1%",
        xaxis_tickprefix="£",
        xaxis_tickformat=",.0f",
        legend_title="City",
        title_font_size=15,
        title_font_family="Sora",
        height=420
    )
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=0.5, color="white")))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Results table ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-label'>Results</div>", unsafe_allow_html=True)

    display_cols = ["city", "msoa_name", "lad_name", "total_listings",
                    "median_nightly_price", "median_house_price_2025",
                    "str_gross_yield", "ltr_gross_yield", "str_vs_ltr_yield_delta"]

    if "avg_sentiment_score" in filtered.columns:
        display_cols.append("avg_sentiment_score")

    display_df = (
        filtered[display_cols]
        .sort_values("str_vs_ltr_yield_delta", ascending=False)
        .rename(columns={
            "city": "City", "msoa_name": "MSOA", "lad_name": "LAD",
            "total_listings": "Listings",
            "median_nightly_price": "Median Nightly (£)",
            "median_house_price_2025": "House Price (£)",
            "str_gross_yield": "STR Yield",
            "ltr_gross_yield": "LTR Yield",
            "str_vs_ltr_yield_delta": "Yield Delta",
            "avg_sentiment_score": "Avg Sentiment"
        })
    )
    for col in ["STR Yield", "LTR Yield"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].map("{:.1%}".format)
    if "Yield Delta" in display_df.columns:
        display_df["Yield Delta"] = display_df["Yield Delta"].map("{:+.1%}".format)
    if "House Price (£)" in display_df.columns:
        display_df["House Price (£)"] = display_df["House Price (£)"].map("£{:,.0f}".format)
    if "Median Nightly (£)" in display_df.columns:
        display_df["Median Nightly (£)"] = display_df["Median Nightly (£)"].map("£{:.0f}".format)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("No areas match your current filters. Try adjusting them.")
