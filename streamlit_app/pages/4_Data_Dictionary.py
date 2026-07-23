import streamlit as st
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, inject_css, render_navbar, render_stripes

st.set_page_config(page_title="Data Dictionary · InvestStay", page_icon="📖", layout="wide", initial_sidebar_state="collapsed")

t = inject_css()
NAVY = t["text"]; LIGHT = t["bg"]; WHITE = t["card_bg"]; MID = t["text_muted"]
render_navbar(active="Data")

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>Data Dictionary</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MID};margin-bottom:24px;'>Schema reference for <code>msoa_investment_summary</code> — the core export table powering this app.</p>", unsafe_allow_html=True)
render_stripes()

import pandas as pd

SOURCES = [
    ("Inside Airbnb", "Listing-level Airbnb data — prices, availability, reviews, room type — scraped and published independently of Airbnb.", "Listing aggregates"),
    ("HM Land Registry", "Price Paid Data: every residential property transaction in England & Wales, used to derive median house prices and 10-year growth.", "House prices, growth"),
    ("Office for National Statistics (ONS)", "Geography boundaries (MSOA/LAD), population estimates, and private rental market statistics.", "Geography, rents, population"),
    ("OS OpenData", "Ordnance Survey's open datasets on parks and green/open spaces, aggregated to LAD level.", "Parks & open spaces"),
    ("NHS Digital", "Register of GP practices in England, aggregated to count and per-capita figures by LAD.", "GP surgeries"),
]

st.markdown("<div class='section-header'>Data Sources</div>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{MID};font-size:0.9rem;margin-bottom:16px;'>"
    f"Every figure in this app traces back to one of the public sources below — nothing is estimated "
    f"without a documented method (see <b>Derived Yield Columns</b> further down for the formulas)."
    f"</p>",
    unsafe_allow_html=True,
)
src_cols = st.columns(len(SOURCES))
for col, (name, desc, powers) in zip(src_cols, SOURCES):
    with col:
        st.markdown(
            f"""
            <div style='background:{WHITE};border-radius:12px;padding:16px;height:100%;
                 box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
                <div style='font-weight:700;color:{NAVY};font-size:0.9rem;margin-bottom:6px;'>{name}</div>
                <div style='color:{MID};font-size:0.8rem;line-height:1.5;margin-bottom:10px;'>{desc}</div>
                <div style='color:{TEAL};font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;'>Powers: {powers}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>Schema</div>", unsafe_allow_html=True)

sections = {
    "Geography": [
        ("msoa_code",   "string",    "ONS",           "MSOA 2021 code e.g. E02000001"),
        ("msoa_name",   "string",    "ONS",           "MSOA 2021 name e.g. City of London 001"),
        ("lad_code",    "string",    "ONS",           "Parent LAD code e.g. E09000001"),
        ("lad_name",    "string",    "ONS",           "Parent LAD name e.g. City of London"),
        ("city",        "string",    "Pipeline",      "london / manchester / bristol"),
    ],
    "Listing Aggregates": [
        ("total_listings",       "long",   "Inside Airbnb", "Count of active listings in MSOA"),
        ("avg_nightly_price",    "double", "Inside Airbnb", "Mean nightly price (£)"),
        ("median_nightly_price", "double", "Inside Airbnb", "Median nightly price (£) — used in yield calculations"),
        ("avg_review_score",     "double", "Inside Airbnb", "Mean guest review score (0–5)"),
        ("avg_availability_365", "double", "Inside Airbnb", "Mean days available per year"),
    ],
    "MSOA-Level Enrichment": [
        ("median_house_price_2025",  "double", "Land Registry", "Median house price 2025 (£)"),
        ("median_house_price_2015",  "double", "Land Registry", "Median house price 2015 (£)"),
        ("price_growth_10yr",        "double", "Land Registry", "% house price growth 2015–2025"),
        ("less_than_15_minute_walk", "double", "ONS",           "% of MSOA within 15-min walk of rail station"),
        ("less_than_30_minute_walk", "double", "ONS",           "% of MSOA within 30-min walk of rail station"),
    ],
    "LAD-Level Enrichment": [
        ("gp_surgery_count",        "long",   "NHS Digital",  "GP surgeries in parent LAD"),
        ("gps_per_100000_people",   "double", "NHS Digital",  "GP surgeries per 100k population"),
        ("total_parks_count",       "long",   "OS OpenData",  "Parks and open spaces in parent LAD"),
        ("parks_per_100000_people", "double", "OS OpenData",  "Parks per 100k population"),
        ("median_monthly_rent",     "double", "ONS Rents",    "Median monthly private rent (£) in LAD"),
    ],
    "Derived Yield Columns": [
        ("str_annual_revenue_est",  "double",    "Derived",   "median_nightly_price × 0.65 × 365"),
        ("str_gross_yield",         "double",    "Derived",   "str_annual_revenue_est ÷ median_house_price_2025"),
        ("ltr_annual_revenue_est",  "double",    "Derived",   "median_monthly_rent × 12"),
        ("ltr_gross_yield",         "double",    "Derived",   "ltr_annual_revenue_est ÷ median_house_price_2025"),
        ("str_vs_ltr_yield_delta",  "double",    "Derived",   "str_gross_yield − ltr_gross_yield  ← key signal"),
        ("_export_created_at",      "timestamp", "Pipeline",  "Timestamp when export table was written"),
    ],
}

for section, rows in sections.items():
    st.markdown(f"<div class='section-header'>{section}</div>", unsafe_allow_html=True)
    df = pd.DataFrame(rows, columns=["Column", "Type", "Source", "Description"])
    st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown(f"""
<div style='margin-top:32px;padding:16px;background:{WHITE};border-radius:10px;
     border-left:4px solid {TEAL};color:{MID};font-size:0.85rem;'>
    <b>Assumptions:</b> STR occupancy rate 65% · Gross yields only (no mortgage, tax, void, or management costs) ·
    Edinburgh excluded from MSOA tables (Scotland uses Data Zones, not MSOAs) ·
    GP, parks, and rent columns repeat the same LAD-level value across all MSOAs within a LAD.
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
