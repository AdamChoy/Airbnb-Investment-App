import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from theme import TEAL, get_theme, inject_css, render_navbar, style_chart, render_stat_card

st.set_page_config(page_title="Home Valuation · InvestStay", page_icon="🏡", layout="wide", initial_sidebar_state="collapsed")

t = get_theme()
inject_css(extra_css=f"""
.val-title {{ font-size: 2.25rem; font-weight: 800; margin-bottom: 4px; }}
.val-disclaimer {{
    background: {t['card_alt_bg']}; border-radius: 12px; padding: 16px 20px;
    font-size: 0.85rem; color: {t['text_muted']}; margin-top: 24px;
}}
""")
NAVY = t["text"]; MID = t["text_muted"]; WHITE = t["card_bg"]
render_navbar(active="Valuation")

@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    return pd.read_csv(os.path.join(base, "msoa_investment_summary.csv"))

msoa_df = load_data()

st.markdown("<div class='val-title'>Value Your <span style='color:" + TEAL + ";'>Home</span></div>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{MID};margin-bottom:20px;'>An area-level estimate based on median transaction prices for your neighbourhood.</p>",
    unsafe_allow_html=True,
)

# ── Location picker ──────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    cities = sorted(msoa_df["city"].dropna().str.title().unique())
    city = st.selectbox("City", cities)

city_df = msoa_df[msoa_df["city"].str.title() == city]

with c2:
    lads = sorted(city_df["lad_name"].dropna().unique())
    lad = st.selectbox("Local Authority District", lads)

lad_df_ = city_df[city_df["lad_name"] == lad]

with c3:
    msoas = sorted(lad_df_["msoa_name"].dropna().unique())
    msoa_name = st.selectbox("Neighbourhood (MSOA)", msoas)

row = lad_df_[lad_df_["msoa_name"] == msoa_name]

if row.empty:
    st.warning("No data available for this area.")
    st.stop()

area = row.iloc[0]

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ── Headline valuation ───────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    render_stat_card(
        "Estimated Value (2025)", f"£{area['median_house_price_2025']:,.0f}",
        note=f"Median transaction price, {msoa_name}", min_height=188,
    )

with col2:
    growth_pct = area["price_growth_10yr"] * 100
    render_stat_card(
        "10-Year Price Growth", f"{growth_pct:+.1f}%",
        note=f"From £{area['median_house_price_2015']:,.0f} in 2015", min_height=188,
    )

with col3:
    value_2035 = area["median_house_price_2025"] * (1 + area["price_growth_10yr"])
    render_stat_card(
        "Projected Value (2035)", f"£{value_2035:,.0f}",
        note="If the last 10 years' growth rate continues", min_height=188,
    )

st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)

# ── Price trend ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Price Trend</div>", unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[2015, 2025], y=[area["median_house_price_2015"], area["median_house_price_2025"]],
    mode="lines+markers", name="Actual", line=dict(color=TEAL, width=3), marker=dict(size=8),
))
fig.add_trace(go.Scatter(
    x=[2025, 2035], y=[area["median_house_price_2025"], value_2035],
    mode="lines+markers", name="Projected", line=dict(color=TEAL, width=3, dash="dash"), marker=dict(size=8),
))
fig.update_layout(
    height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20), legend=dict(title_text=""), template="plotly_white",
)
fig.update_xaxes(tickvals=[2015, 2025, 2035], title_text="Year")
fig.update_yaxes(title_text="Median House Price (£)")
style_chart(fig)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Rental potential ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Rental Income Potential</div>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{MID};font-size:0.9rem;margin-bottom:16px;'>How this property could perform as a short-term (Airbnb) vs. long-term let.</p>",
    unsafe_allow_html=True,
)

r1, r2 = st.columns(2)
with r1:
    str_monthly = area["str_annual_revenue_est"] / 12
    render_stat_card(
        "Short-Term Rental (Airbnb)", f"£{str_monthly:,.0f}", unit="/ month",
        note=f"Estimated gross yield: {area['str_gross_yield']*100:.2f}%",
    )
with r2:
    ltr_monthly = area["ltr_annual_revenue_est"] / 12
    render_stat_card(
        "Long-Term Rental", f"£{ltr_monthly:,.0f}", unit="/ month",
        note=f"Estimated gross yield: {area['ltr_gross_yield']*100:.2f}%",
    )

st.markdown(
    f"""
    <div class="val-disclaimer">
        This estimate is derived from median house price and rental data for <b>{msoa_name}</b>
        ({lad}), not an appraisal of your specific property. Actual value depends on condition,
        size, exact location and other factors this estimate can't account for.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
