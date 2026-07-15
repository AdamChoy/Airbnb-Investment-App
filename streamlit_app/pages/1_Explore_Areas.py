import streamlit as st
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, inject_css, render_navbar, render_stripes

st.set_page_config(page_title="Explore Areas · InvestStay", page_icon="🔍", layout="wide", initial_sidebar_state="collapsed")

t = inject_css()
NAVY = t["text"]; LIGHT = t["bg"]; WHITE = t["card_bg"]; MID = t["text_muted"]
render_navbar(active="Explore")

@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    msoa = pd.read_csv(os.path.join(base, "msoa_investment_summary.csv"))
    try:
        sent = pd.read_csv(os.path.join(base, "msoa_review_sentiment.csv"))
        msoa = msoa.merge(
            sent[["msoa_code","avg_sentiment_score","pct_positive","pct_negative","review_count"]],
            on="msoa_code", how="left"
        )
    except FileNotFoundError:
        pass
    return msoa

msoa_df = load_data()

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>Explore Areas</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MID};margin-bottom:24px;'>Filter and rank MSOAs by yield, price, transport, and sentiment.</p>", unsafe_allow_html=True)
render_stripes()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.container():
    st.markdown("<div class='filter-card'>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)

    with f1:
        cities = ["All"] + sorted(msoa_df["city"].dropna().str.title().unique().tolist())
        query_city = st.query_params.get("city")
        if query_city and "city_filter" not in st.session_state:
            match = next((c for c in cities if c.lower() == query_city.lower()), None)
            if match:
                st.session_state["city_filter"] = match
        city = st.selectbox("City", cities, key="city_filter")

    with f2:
        max_price = int(msoa_df["median_house_price_2025"].dropna().max())
        price_range = st.slider("Max House Price (£)", 0, max_price, max_price, step=25000,
                                format="£%d")

    with f3:
        min_yield = st.slider("Min STR Yield (%)", 0.0, 20.0, 0.0, step=0.5)

    with f4:
        rail_options = ["Any", "Within 15-min walk", "Within 30-min walk"]
        rail = st.selectbox("Rail Access", rail_options)

    with f5:
        if "avg_sentiment_score" in msoa_df.columns:
            min_sentiment = st.slider("Min Sentiment Score", -1.0, 1.0, -1.0, step=0.05)
        else:
            st.caption("Sentiment data not loaded")
            min_sentiment = -1.0

    st.markdown("</div>", unsafe_allow_html=True)

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = msoa_df.copy()

if city != "All":
    filtered = filtered[filtered["city"].str.title() == city]

filtered = filtered[filtered["median_house_price_2025"].fillna(999999999) <= price_range]
filtered = filtered[filtered["str_gross_yield"].fillna(0) * 100 >= min_yield]

if rail == "Within 15-min walk":
    filtered = filtered[filtered["less_than_15_minute_walk"].fillna(0) > 0]
elif rail == "Within 30-min walk":
    filtered = filtered[filtered["less_than_30_minute_walk"].fillna(0) > 0]

if "avg_sentiment_score" in filtered.columns:
    filtered = filtered[filtered["avg_sentiment_score"].fillna(-1) >= min_sentiment]

# ── Sort control ──────────────────────────────────────────────────────────────
sort_col_map = {
    "STR vs LTR Yield Delta": "str_vs_ltr_yield_delta",
    "STR Gross Yield":        "str_gross_yield",
    "Median Nightly Price":   "median_nightly_price",
    "House Price":            "median_house_price_2025",
    "Review Sentiment":       "avg_sentiment_score",
}
sort_choice = st.selectbox("Sort by", list(sort_col_map.keys()), index=0)
sort_key = sort_col_map[sort_choice]
if sort_key in filtered.columns:
    filtered = filtered.sort_values(sort_key, ascending=False)

st.markdown(f"<div class='section-header'>{len(filtered):,} MSOAs matched</div>", unsafe_allow_html=True)

# ── Display columns ───────────────────────────────────────────────────────────
display_cols = ["city", "msoa_name", "lad_name", "total_listings",
                "median_nightly_price", "str_gross_yield", "ltr_gross_yield",
                "str_vs_ltr_yield_delta", "median_house_price_2025",
                "less_than_15_minute_walk", "price_growth_10yr"]

if "avg_sentiment_score" in filtered.columns:
    display_cols += ["avg_sentiment_score", "pct_positive", "pct_negative"]

display = filtered[[c for c in display_cols if c in filtered.columns]].copy()

for col in ["str_gross_yield", "ltr_gross_yield", "str_vs_ltr_yield_delta", "price_growth_10yr"]:
    if col in display.columns:
        display[col] = (display[col] * 100).round(2).astype(str) + "%"

if "median_house_price_2025" in display.columns:
    display["median_house_price_2025"] = display["median_house_price_2025"].apply(
        lambda x: f"£{x:,.0f}" if pd.notna(x) else "N/A"
    )
if "median_nightly_price" in display.columns:
    display["median_nightly_price"] = display["median_nightly_price"].apply(
        lambda x: f"£{x:.0f}" if pd.notna(x) else "N/A"
    )

display.columns = [
    c.replace("_", " ").title().replace("Msoa", "MSOA").replace("Lad", "LAD")
    for c in display.columns
]
st.dataframe(display.reset_index(drop=True), use_container_width=True, hide_index=True, height=500)

# ── CSV download ──────────────────────────────────────────────────────────────
st.download_button(
    label="Download filtered results as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="investstay_filtered_msoa.csv",
    mime="text/csv",
)
