import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, inject_css, render_navbar, render_styled_table, style_chart
from ai_insight import summarise_reviews, is_filler

st.set_page_config(page_title="Sentiment · InvestStay", page_icon="💬", layout="wide", initial_sidebar_state="collapsed")

t = inject_css(extra_css=f"""
.st-key-sentiment_area_select [data-testid="stWidgetLabel"] p {{
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: {TEAL};
}}
.st-key-sentiment_area_select [data-baseweb="select"] > div {{
    border: 1.5px solid {TEAL} !important;
}}
.st-key-sentiment_area_select [data-baseweb="select"] * {{
    color: #000 !important;
}}
.st-key-global_city_filter [data-baseweb="select"] > div {{
    border: 1.5px solid {TEAL} !important;
}}
.st-key-sentiment_area_level [data-testid="stWidgetLabel"] p,
.st-key-sentiment_area_level [role="radiogroup"] label p {{
    color: #000 !important;
}}
""")
NAVY = t["text"]; LIGHT = t["bg"]; WHITE = t["card_bg"]; MID = t["text_muted"]
render_navbar(active="Sentiment")

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

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>Guest <span style='color:{TEAL};'>Sentiment</span></h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MID};margin-bottom:24px;'>Real guest review sentiment by neighbourhood, so you can understand what guests really appreciate from their hosts.</p>", unsafe_allow_html=True)

if msoa_sent is None:
    st.warning("Sentiment data not found. Run notebook 05 and place msoa_review_sentiment.csv and lad_review_sentiment.csv in the data/ folder.")
    st.stop()

cities = ["All"] + sorted(msoa_sent["city"].dropna().str.title().unique().tolist())
if st.session_state.get("global_city_filter") not in cities:
    st.session_state["global_city_filter"] = "All"
city_filter = st.selectbox("Filter by city", cities, key="global_city_filter")
df = msoa_sent if city_filter == "All" else msoa_sent[msoa_sent["city"].str.title() == city_filter]
lad_df = lad_sent if city_filter == "All" else lad_sent[lad_sent["city"].str.title() == city_filter]

# ── Sample reviews ────────────────────────────────────────────────────────────
if "sample_reviews" in df.columns:
    st.markdown("<div class='section-header'>Sample Reviews by Area</div>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{MID};font-size:0.85rem;margin-top:12px;margin-bottom:20px;'>"
        f"Pick an area to see an AI-generated summary of what guests say, alongside three raw reviews it's based on. (Sample reviews are restricted to 200 characters).</p>",
        unsafe_allow_html=True,
    )

    area_level = st.radio(
        "Area level", ["Local Authority District (LAD)", "Neighbourhood (MSOA)"],
        horizontal=True, key="sentiment_area_level",
    )
    if area_level.startswith("Neighbourhood"):
        source_df, name_col, select_label = df, "msoa_name", "Select MSOA"
    else:
        source_df, name_col, select_label = lad_df, "lad_name", "Select LAD"

    area_options = source_df.dropna(subset=["sample_reviews"])[name_col].unique().tolist()
    if area_options:
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        selected_area = st.selectbox(select_label, sorted(area_options), key="sentiment_area_select")
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        row = source_df[source_df[name_col] == selected_area].iloc[0]
        raw_reviews = [r.strip() for r in str(row["sample_reviews"]).split(" | ") if r.strip()]
        # The export pipeline hard-truncates each review to 200 chars
        # mid-word (see notebooks/05_reviews_export.ipynb), so anything at
        # that length is almost certainly cut off — trim back to the last
        # whole word and mark it clearly instead of ending mid-sentence.
        reviews = [
            (r[: r.rfind(" ")].rstrip(".,;:") + "…") if len(r) >= 200 and " " in r else r
            for r in raw_reviews
        ]

        summary = summarise_reviews(selected_area, tuple(reviews))
        # Filler text (shown while no OPENAI_API_KEY is configured) is for
        # visually testing this card's own layout, not something an actual
        # user should see — a "not configured yet" message reads as broken.
        # No key just means: show the raw reviews below, like before this
        # feature existed.
        if summary and not is_filler(summary):
            st.markdown(
                f"""<div class="card" style="margin-bottom:16px;">
                <p style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.1em;color:{TEAL};margin-bottom:8px;">🤖 AI Summary</p>
                <p style="margin:0;">{summary}</p>
                </div>""",
                unsafe_allow_html=True,
            )

        for review in reviews:
            st.markdown(f"<div class='review-card'>{review}</div>", unsafe_allow_html=True)

st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)

# ── Sentiment distribution ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Sentiment Distribution by City</div>", unsafe_allow_html=True)

city_sent = (
    msoa_sent.groupby("city")[["pct_positive","pct_neutral","pct_negative"]]
    .mean().reset_index()
)
city_sent["city"] = city_sent["city"].str.title()
city_sent_melted = city_sent.melt(id_vars="city", var_name="Sentiment", value_name="Percentage")
city_sent_melted["Sentiment"] = city_sent_melted["Sentiment"].str.replace("pct_","").str.title()

fig1 = px.bar(
    city_sent_melted, x="city", y="Percentage", color="Sentiment",
    color_discrete_map={"Positive": TEAL, "Neutral": "#94A3B8", "Negative": "#EF4444"},
    barmode="stack", template="plotly_white",
    labels={"city": "City", "Percentage": "% of Reviews"},
)
fig1.update_layout(height=360, plot_bgcolor=WHITE, paper_bgcolor=WHITE)
style_chart(fig1)
st.plotly_chart(fig1, use_container_width=True)

# ── Top and bottom MSOAs ──────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='section-header' style='color:#16C784;'>Most Positively Reviewed MSOAs</div>", unsafe_allow_html=True)
    top = (
        df[df["review_count"] >= 10]
        .nlargest(10, "avg_sentiment_score")
        [["msoa_name","city","avg_sentiment_score","review_count","pct_positive"]]
        .copy()
    )
    top["city"] = top["city"].str.title()
    top["avg_sentiment_score"] = top["avg_sentiment_score"].round(3)
    top["pct_positive"] = top["pct_positive"].round(1).astype(str) + "%"
    top.columns = ["MSOA","City","Avg Sentiment","Reviews","% Positive"]
    render_styled_table(top.reset_index(drop=True), highlight_cols=["Avg Sentiment"])

with col2:
    st.markdown("<div class='section-header' style='color:#EF4444;'>Most Negatively Reviewed MSOAs</div>", unsafe_allow_html=True)
    bottom = (
        df[df["review_count"] >= 10]
        .nsmallest(10, "avg_sentiment_score")
        [["msoa_name","city","avg_sentiment_score","review_count","pct_negative"]]
        .copy()
    )
    bottom["city"] = bottom["city"].str.title()
    bottom["avg_sentiment_score"] = bottom["avg_sentiment_score"].round(3)
    bottom["pct_negative"] = bottom["pct_negative"].round(1).astype(str) + "%"
    bottom.columns = ["MSOA","City","Avg Sentiment","Reviews","% Negative"]
    render_styled_table(bottom.reset_index(drop=True), highlight_cols=["Avg Sentiment"])

# ── Sentiment vs Yield scatter ────────────────────────────────────────────────
try:
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    msoa_inv = pd.read_csv(os.path.join(base, "msoa_investment_summary.csv"))
    combined = msoa_inv.merge(
        msoa_sent[["msoa_code","avg_sentiment_score","review_count"]],
        on="msoa_code", how="inner"
    ).dropna(subset=["str_gross_yield","avg_sentiment_score"])

    if city_filter != "All":
        combined = combined[combined["city"].str.title() == city_filter]
    combined["city"] = combined["city"].str.title()

    st.markdown("<div class='section-header'>Review Sentiment vs Short-Term Rental Yield</div>", unsafe_allow_html=True)
    fig2 = px.scatter(
        combined, x="avg_sentiment_score", y="str_gross_yield",
        color="city", size="review_count", hover_name="msoa_name",
        color_discrete_sequence=[TEAL, NAVY, "#D97706", "#059669"],
        labels={"avg_sentiment_score": "Avg Sentiment Score", "str_gross_yield": "STR Gross Yield", "city": "City"},
        template="plotly_white",
    )
    fig2.update_layout(height=420, plot_bgcolor=WHITE, paper_bgcolor=WHITE)
    style_chart(fig2)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Bubble size = number of reviews. Shows whether high-yield areas also have high guest satisfaction.")
except Exception as e:
    print(f"[Sentiment page] Sentiment vs STR Yield chart failed to build: {e}")
    st.info("Sentiment vs STR Yield chart is unavailable right now.")

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
