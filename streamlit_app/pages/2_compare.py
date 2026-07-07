import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Compare Cities — InvestStay", layout="wide")

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
    <h1>⚖️ Compare Cities</h1>
    <p>Side-by-side STR and LTR yield comparison across all four cities.</p>
</div>
""", unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

@st.cache_data
def load_lad():
    path = os.path.join(DATA_DIR, "lad_investment_summary.csv")
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

@st.cache_data
def load_msoa():
    path = os.path.join(DATA_DIR, "msoa_investment_summary.csv")
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

lad_df  = load_lad()
msoa_df = load_msoa()

if lad_df.empty:
    st.warning("No data found. Add `lad_investment_summary.csv` to the `data/` folder.")
    st.stop()

CITY_COLOURS = {
    "london": "#1B2A4A", "manchester": "#0D9488",
    "bristol": "#0F766E", "edinburgh": "#7FB3D3"
}

# ── City summary cards ─────────────────────────────────────────────────────────
st.markdown("<div class='section-label'>City overview</div>", unsafe_allow_html=True)
cols = st.columns(4)
for i, city in enumerate(["london", "manchester", "edinburgh", "bristol"]):
    city_data = lad_df[lad_df["city"] == city]
    if city_data.empty:
        continue
    avg_str = city_data["str_gross_yield"].mean()
    avg_ltr = city_data["ltr_gross_yield"].mean()
    listings = city_data["total_listings"].sum()
    with cols[i]:
        st.markdown(f"""
        <div style='background:white; border:1px solid #E2E8F0; border-top: 4px solid {CITY_COLOURS.get(city,"#0D9488")}; border-radius:10px; padding:1.1rem 1.3rem;'>
            <div style='font-family:Sora,sans-serif; font-size:1.1rem; font-weight:700; color:#1B2A4A; text-transform:capitalize;'>{city}</div>
            <div style='margin-top:0.7rem;'>
                <div style='font-size:1.4rem; font-weight:700; color:#0D9488;'>{avg_str:.1%}</div>
                <div style='font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;'>Avg STR yield</div>
            </div>
            <div style='margin-top:0.5rem;'>
                <div style='font-size:1.1rem; font-weight:600; color:#1B2A4A;'>{avg_ltr:.1%}</div>
                <div style='font-size:0.72rem; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;'>Avg LTR yield</div>
            </div>
            <div style='margin-top:0.5rem; font-size:0.8rem; color:#64748B;'>{listings:,} listings</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── STR vs LTR bar chart ───────────────────────────────────────────────────────
st.markdown("<div class='section-label'>STR vs LTR yield by city</div>", unsafe_allow_html=True)

city_summary = (
    lad_df.groupby("city")[["str_gross_yield", "ltr_gross_yield"]]
    .mean()
    .reset_index()
    .sort_values("str_gross_yield", ascending=False)
)

fig = go.Figure()
fig.add_trace(go.Bar(
    name="STR Gross Yield",
    x=city_summary["city"].str.capitalize(),
    y=city_summary["str_gross_yield"],
    marker_color="#0D9488",
    text=city_summary["str_gross_yield"].map("{:.1%}".format),
    textposition="outside"
))
fig.add_trace(go.Bar(
    name="LTR Gross Yield",
    x=city_summary["city"].str.capitalize(),
    y=city_summary["ltr_gross_yield"],
    marker_color="#1B2A4A",
    text=city_summary["ltr_gross_yield"].map("{:.1%}".format),
    textposition="outside"
))
fig.update_layout(
    barmode="group",
    plot_bgcolor="white", paper_bgcolor="white",
    font_family="Inter",
    yaxis_tickformat=".1%",
    yaxis_title="Gross Yield",
    xaxis_title="",
    legend_title="",
    height=380,
    title_font_family="Sora"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── MSOA yield distribution ────────────────────────────────────────────────────
if not msoa_df.empty:
    st.markdown("<div class='section-label'>STR yield distribution by city (MSOA level)</div>", unsafe_allow_html=True)

    fig2 = px.box(
        msoa_df.dropna(subset=["str_gross_yield"]),
        x="city", y="str_gross_yield",
        color="city",
        color_discrete_map=CITY_COLOURS,
        labels={"city": "City", "str_gross_yield": "STR Gross Yield"},
        category_orders={"city": ["london", "manchester", "bristol", "edinburgh"]}
    )
    fig2.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="Inter",
        yaxis_tickformat=".1%",
        showlegend=False,
        height=360
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

# ── House price vs yield scatter ───────────────────────────────────────────────
if not msoa_df.empty:
    st.markdown("<div class='section-label'>House price vs STR yield (all MSOAs)</div>", unsafe_allow_html=True)

    fig3 = px.scatter(
        msoa_df.dropna(subset=["median_house_price_2025", "str_gross_yield"]),
        x="median_house_price_2025",
        y="str_gross_yield",
        color="city",
        opacity=0.5,
        color_discrete_map=CITY_COLOURS,
        labels={
            "median_house_price_2025": "Median House Price (£)",
            "str_gross_yield": "STR Gross Yield",
            "city": "City"
        },
        hover_name="msoa_name"
    )
    fig3.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="Inter",
        yaxis_tickformat=".1%",
        xaxis_tickprefix="£",
        xaxis_tickformat=",.0f",
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)
