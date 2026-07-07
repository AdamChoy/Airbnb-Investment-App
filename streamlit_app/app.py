import streamlit as st

st.set_page_config(
    page_title="InvestStay",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1B2A4A;
    border-right: none;
}
section[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #E2E8F0 !important;
    font-size: 0.95rem;
}

/* Main background */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Page header */
.page-header {
    background: linear-gradient(135deg, #1B2A4A 0%, #0D9488 100%);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    color: white;
}
.page-header h1 {
    font-family: 'Sora', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 0.4rem 0;
    color: white;
}
.page-header p {
    font-size: 1rem;
    color: #B2D8D8;
    margin: 0;
}

/* Metric cards */
.metric-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.metric-card .metric-value {
    font-family: 'Sora', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #1B2A4A;
    line-height: 1.1;
}
.metric-card .metric-label {
    font-size: 0.78rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.3rem;
}
.metric-card .metric-delta {
    font-size: 0.85rem;
    color: #0D9488;
    font-weight: 600;
    margin-top: 0.2rem;
}

/* Section headers */
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #0D9488;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
}

/* Teal accent button override */
.stButton > button {
    background-color: #0D9488;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
}
.stButton > button:hover {
    background-color: #0F766E;
    color: white;
}

/* DataFrames */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

/* Divider */
hr {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar branding ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 1.5rem 0;'>
        <div style='font-family: Sora, sans-serif; font-size: 1.5rem; font-weight: 800; color: white;'>
            🏠 InvestStay
        </div>
        <div style='font-size: 0.78rem; color: #7FB3D3; margin-top: 0.2rem;'>
            Analyse. Invest. Grow.
        </div>
    </div>
    <hr style='border-color: #2D4A6A; margin: 0 0 1.2rem 0;'>
    """, unsafe_allow_html=True)

    st.page_link("app.py",            label="🏠  Home",            )
    st.page_link("pages/1_explore.py", label="🔍  Explore Areas",  )
    st.page_link("pages/2_compare.py", label="⚖️  Compare Cities", )
    st.page_link("pages/3_sentiment.py", label="💬  Guest Sentiment",)
    st.page_link("pages/4_insights.py", label="🤖  AI Insights",   )

    st.markdown("<hr style='border-color: #2D4A6A; margin: 1.2rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.72rem; color: #7FB3D3;'>Data sourced from Inside Airbnb, ONS, Land Registry, NHS Digital & OS OpenData.</div>", unsafe_allow_html=True)

# ── Homepage ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class='page-header'>
    <h1>InvestStay</h1>
    <p>Neighbourhood-level STR vs LTR investment intelligence across London, Manchester, Edinburgh and Bristol.</p>
</div>
""", unsafe_allow_html=True)

# Quick stats row
import pandas as pd, os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

@st.cache_data
def load_msoa():
    path = os.path.join(DATA_DIR, "msoa_investment_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data
def load_lad():
    path = os.path.join(DATA_DIR, "lad_investment_summary.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data
def load_sentiment():
    path = os.path.join(DATA_DIR, "msoa_review_sentiment.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

msoa_df = load_msoa()
lad_df  = load_lad()
sent_df = load_sentiment()

if not msoa_df.empty:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{msoa_df['total_listings'].sum():,}</div>
            <div class='metric-label'>Total listings</div>
            <div class='metric-delta'>across 4 cities</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{len(msoa_df):,}</div>
            <div class='metric-label'>MSOAs analysed</div>
            <div class='metric-delta'>England & Wales</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        top_yield = msoa_df['str_gross_yield'].max()
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{top_yield:.1%}</div>
            <div class='metric-label'>Highest STR yield</div>
            <div class='metric-delta'>gross, 65% occupancy</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        positive_delta = (msoa_df['str_vs_ltr_yield_delta'] > 0).sum()
        pct = positive_delta / len(msoa_df) * 100
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{pct:.0f}%</div>
            <div class='metric-label'>MSOAs where STR beats LTR</div>
            <div class='metric-delta'>{positive_delta:,} areas</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Top 10 areas teaser
    st.markdown("<div class='section-label'>Top areas by STR yield advantage</div>", unsafe_allow_html=True)
    top10 = (
        msoa_df[msoa_df["str_vs_ltr_yield_delta"].notna()]
        .sort_values("str_vs_ltr_yield_delta", ascending=False)
        .head(10)[["city", "msoa_name", "lad_name", "median_nightly_price",
                   "str_gross_yield", "ltr_gross_yield", "str_vs_ltr_yield_delta"]]
        .rename(columns={
            "city": "City", "msoa_name": "MSOA", "lad_name": "LAD",
            "median_nightly_price": "Median Nightly (£)",
            "str_gross_yield": "STR Yield",
            "ltr_gross_yield": "LTR Yield",
            "str_vs_ltr_yield_delta": "Yield Delta"
        })
    )
    top10["STR Yield"]   = top10["STR Yield"].map("{:.1%}".format)
    top10["LTR Yield"]   = top10["LTR Yield"].map("{:.1%}".format)
    top10["Yield Delta"] = top10["Yield Delta"].map("{:+.1%}".format)
    top10["Median Nightly (£)"] = top10["Median Nightly (£)"].map("£{:.0f}".format)
    st.dataframe(top10, use_container_width=True, hide_index=True)

else:
    st.info("📂 No data loaded yet. Add your CSV exports to the `data/` folder and refresh.")
    st.markdown("""
    **Expected files in `data/`:**
    - `msoa_investment_summary.csv`
    - `lad_investment_summary.csv`
    - `msoa_review_sentiment.csv`
    """)
