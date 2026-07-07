import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Sentiment · InvestStay", page_icon="💬", layout="wide")

NAVY = "#1B2A4A"; TEAL = "#0D9488"; LIGHT = "#F0F4F8"; WHITE = "#FFFFFF"; MID = "#64748B"

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color:{LIGHT}; font-family:'Inter','Segoe UI',sans-serif; }}
    [data-testid="stSidebar"] {{ background-color:{NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color:{WHITE} !important; }}
    [data-testid="stSidebar"] hr {{ border-color:#2d4a6e; }}
    #MainMenu, footer, header {{ visibility:hidden; }}
    .section-header {{
        font-size:1.1rem;font-weight:700;color:{NAVY};text-transform:uppercase;
        letter-spacing:0.08em;border-bottom:2px solid {TEAL};padding-bottom:6px;margin:24px 0 16px 0;
    }}
    .review-card {{
        background:{WHITE}; border-radius:10px; padding:16px 20px;
        box-shadow:0 2px 6px rgba(0,0,0,0.06); border-left:4px solid {TEAL};
        margin-bottom:12px; font-size:0.9rem; color:{MID};
    }}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 0 8px 0;'>
        <div style='font-size:1.6rem;font-weight:800;color:white;letter-spacing:-0.02em;'>
            Invest<span style='color:{TEAL};'>Stay</span>
        </div>
        <div style='font-size:0.75rem;color:#7fb3d3;margin-top:2px;letter-spacing:0.1em;'>ANALYSE · INVEST · GROW</div>
    </div><hr/>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    try:
        msoa_sent = pd.read_csv(os.path.join(base, "msoa_review_sentiment.csv"))
        lad_sent  = pd.read_csv(os.path.join(base, "lad_review_sentiment.csv"))
        return msoa_sent, lad_sent
    except FileNotFoundError:
        return None, None

msoa_sent, lad_sent = load_data()

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>Guest Sentiment</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MID};margin-bottom:24px;'>VADER sentiment analysis on Airbnb reviews — English-language only, aggregated by MSOA and LAD.</p>", unsafe_allow_html=True)

if msoa_sent is None:
    st.warning("Sentiment data not found. Run notebook 05 and place msoa_review_sentiment.csv and lad_review_sentiment.csv in the data/ folder.")
    st.stop()

city_filter = st.selectbox("Filter by city", ["All"] + sorted(msoa_sent["city"].dropna().unique().tolist()))
df = msoa_sent if city_filter == "All" else msoa_sent[msoa_sent["city"] == city_filter]

# ── Sentiment distribution ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Sentiment Distribution by City</div>", unsafe_allow_html=True)

city_sent = (
    msoa_sent.groupby("city")[["pct_positive","pct_neutral","pct_negative"]]
    .mean().reset_index()
)
city_sent_melted = city_sent.melt(id_vars="city", var_name="Sentiment", value_name="Percentage")
city_sent_melted["Sentiment"] = city_sent_melted["Sentiment"].str.replace("pct_","").str.title()

fig1 = px.bar(
    city_sent_melted, x="city", y="Percentage", color="Sentiment",
    color_discrete_map={"Positive": TEAL, "Neutral": "#94A3B8", "Negative": "#EF4444"},
    barmode="stack", template="plotly_white",
    labels={"city": "City", "Percentage": "% of Reviews"},
)
fig1.update_layout(height=360, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                   font=dict(family="Inter, Segoe UI, sans-serif"))
st.plotly_chart(fig1, use_container_width=True)

# ── Top and bottom MSOAs ──────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='section-header'>Highest Rated MSOAs</div>", unsafe_allow_html=True)
    top = (
        df[df["review_count"] >= 10]
        .nlargest(10, "avg_sentiment_score")
        [["msoa_name","city","avg_sentiment_score","review_count","pct_positive"]]
        .copy()
    )
    top["avg_sentiment_score"] = top["avg_sentiment_score"].round(3)
    top["pct_positive"] = top["pct_positive"].round(1).astype(str) + "%"
    top.columns = ["MSOA","City","Avg Sentiment","Reviews","% Positive"]
    st.dataframe(top.reset_index(drop=True), use_container_width=True, hide_index=True)

with col2:
    st.markdown("<div class='section-header'>Lowest Rated MSOAs</div>", unsafe_allow_html=True)
    bottom = (
        df[df["review_count"] >= 10]
        .nsmallest(10, "avg_sentiment_score")
        [["msoa_name","city","avg_sentiment_score","review_count","pct_negative"]]
        .copy()
    )
    bottom["avg_sentiment_score"] = bottom["avg_sentiment_score"].round(3)
    bottom["pct_negative"] = bottom["pct_negative"].round(1).astype(str) + "%"
    bottom.columns = ["MSOA","City","Avg Sentiment","Reviews","% Negative"]
    st.dataframe(bottom.reset_index(drop=True), use_container_width=True, hide_index=True)

# ── Sentiment vs Yield scatter ────────────────────────────────────────────────
try:
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    msoa_inv = pd.read_csv(os.path.join(base, "msoa_investment_summary.csv"))
    combined = msoa_inv.merge(
        msoa_sent[["msoa_code","avg_sentiment_score","review_count"]],
        on="msoa_code", how="inner"
    ).dropna(subset=["str_gross_yield","avg_sentiment_score"])

    if city_filter != "All":
        combined = combined[combined["city"] == city_filter]

    st.markdown("<div class='section-header'>Sentiment vs STR Yield</div>", unsafe_allow_html=True)
    fig2 = px.scatter(
        combined, x="avg_sentiment_score", y="str_gross_yield",
        color="city", size="review_count", hover_name="msoa_name",
        color_discrete_sequence=[TEAL, NAVY, "#D97706", "#059669"],
        labels={"avg_sentiment_score": "Avg Sentiment Score", "str_gross_yield": "STR Gross Yield"},
        template="plotly_white",
    )
    fig2.update_layout(height=420, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                       font=dict(family="Inter, Segoe UI, sans-serif"))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Bubble size = number of reviews. Shows whether high-yield areas also have high guest satisfaction.")
except Exception:
    pass

# ── Sample reviews ────────────────────────────────────────────────────────────
if "sample_reviews" in df.columns:
    st.markdown("<div class='section-header'>Sample Reviews by Area</div>", unsafe_allow_html=True)
    area_options = df.dropna(subset=["sample_reviews"])["msoa_name"].unique().tolist()
    if area_options:
        selected_area = st.selectbox("Select MSOA", sorted(area_options))
        row = df[df["msoa_name"] == selected_area].iloc[0]
        reviews = str(row["sample_reviews"]).split(" | ")
        for review in reviews:
            if review.strip():
                st.markdown(f"<div class='review-card'>{review.strip()}</div>", unsafe_allow_html=True)
