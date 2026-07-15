import streamlit as st
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, inject_css, render_navbar, render_stripes

st.set_page_config(page_title="How It Works · InvestStay", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")

t = inject_css()
NAVY = t["text"]; LIGHT = t["bg"]; WHITE = t["card_bg"]; MID = t["text_muted"]
render_navbar(active="How it works")

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>How It Works</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MID};margin-bottom:24px;'>From open data to an investment signal — the pipeline behind InvestStay.</p>", unsafe_allow_html=True)
render_stripes()

STEPS = [
    ("Ingest", "We pull raw listings from Inside Airbnb alongside Land Registry house prices, ONS rents and transport access, and NHS/OS amenity data — all open datasets, refreshed on a schedule."),
    ("Aggregate", "Listings and enrichment data are rolled up to MSOA and LAD geography, giving every neighbourhood a consistent set of comparable figures."),
    ("Estimate yield", "For each area we estimate short-term rental (STR) income at a 65% occupancy assumption, and compare it against a standard long-term tenancy (LTR) using median rent."),
    ("Score the delta", "The gap between STR and LTR gross yield is the core signal — it shows where running a short-let outperforms a normal buy-to-let, after accounting for local house prices."),
    ("Layer in sentiment", "Guest review sentiment is scored per area, so a high yield doesn't come as a surprise cost to reputation or guest experience."),
    ("Surface it", "The result is published as the tables and scores you see across Explore, Yields, Sentiment and Score — all traceable back to the source figures in the Data Dictionary."),
]

for i, (title, desc) in enumerate(STEPS, start=1):
    st.markdown(f"""
    <div style='display:flex;gap:20px;align-items:flex-start;padding:18px 0;
         border-bottom:1px solid {t["border"]};'>
        <div style='flex:0 0 auto;width:36px;height:36px;border-radius:50%;background:{TEAL};
             color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;
             font-size:0.9rem;'>{i}</div>
        <div>
            <div style='font-weight:700;color:{NAVY};font-size:1.05rem;margin-bottom:4px;'>{title}</div>
            <div style='color:{MID};font-size:0.92rem;line-height:1.6;'>{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style='margin-top:32px;padding:16px;background:{WHITE};border-radius:10px;
     border-left:4px solid {TEAL};color:{MID};font-size:0.85rem;'>
    Every figure here is gross, not net — no mortgage, tax, void periods or management costs are modelled.
    See the <a href="/Data_Dictionary" target="_self" style="color:{TEAL};">Data Dictionary</a> for exact column definitions and assumptions.
</div>
""", unsafe_allow_html=True)
