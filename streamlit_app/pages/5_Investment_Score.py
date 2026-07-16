import os
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, inject_css, _get_logo_b64, render_navbar, render_stripes
from ai_insight import generate_insight

st.set_page_config(page_title="Investment Score · InvestStay", layout="wide", initial_sidebar_state="collapsed")

# -----------------------------
# LOAD DATA
# -----------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

lad_df = pd.read_csv(os.path.join(DATA_DIR, "lad_investment_summary.csv"))
msoa_df = pd.read_csv(os.path.join(DATA_DIR, "msoa_investment_summary.csv"))

# -----------------------------
# STYLE
# -----------------------------
t = inject_css(extra_css=f"""
.main-title {{ font-size: 42px; font-weight: 800; }}
.teal {{ color: {TEAL}; }}
.score {{ font-size: 54px; font-weight: 800; color: {TEAL}; }}
.stButton > button {{
    background-color: {TEAL}; color: white; border: none;
    border-radius: 12px; padding: 0.7rem 1.2rem; font-weight: 600;
}}
.stButton > button:hover {{ background-color: #0b7d73; color: white; }}
""")
render_navbar(active="Score")

# -----------------------------
# SCORING
# -----------------------------
def normalise(series):
    if series.max() == series.min():
        return series * 0
    return ((series - series.min()) / (series.max() - series.min())) * 100

def add_investment_score(df):
    df = df.copy()

    df["revenue_score"] = normalise(df["str_annual_revenue_est"])
    df["occupancy_proxy"] = 365 - df["avg_availability_365"]
    df["occupancy_score"] = normalise(df["occupancy_proxy"])
    df["str_yield_score"] = normalise(df["str_gross_yield"])
    df["yield_gap_score"] = normalise(df["str_vs_ltr_yield_delta"])
    df["saturation_score"] = 100 - normalise(df["total_listings"])

    df["investment_score"] = (
        0.30 * df["revenue_score"]
        + 0.25 * df["occupancy_score"]
        + 0.25 * df["str_yield_score"]
        + 0.10 * df["yield_gap_score"]
        + 0.10 * df["saturation_score"]
    ).round(1)

    return df

lad_df = add_investment_score(lad_df)
msoa_df = add_investment_score(msoa_df)

# -----------------------------
# SESSION STATE
# -----------------------------
if "score_page" not in st.session_state:
    # Jump straight to the Dashboard tab if we arrived via Home's "Analyse
    # Investment" flow (city is set in session_state); otherwise land on Home.
    st.session_state.score_page = "Dashboard" if "city" in st.session_state else "Home"

# -----------------------------
# SEARCH INPUTS (persist across pages via shared session_state keys)
# -----------------------------
with st.container():
    st.markdown("<div class='filter-card'>", unsafe_allow_html=True)
    st.subheader("Search Inputs")
    i1, i2, i3, i4 = st.columns([1, 1.4, 1, 0.8])

    with i1:
        city_options = sorted(lad_df["city"].dropna().str.title().unique())
        if st.session_state.get("global_city") not in city_options:
            st.session_state["global_city"] = city_options[0]
        city = st.selectbox("Select City", city_options, key="global_city")

    with i2:
        budget = st.slider(
            "Investment Budget (£)", 50000, 1000000, step=10000, key="global_budget",
        )

    with i3:
        profile = st.selectbox(
            "Investor Profile",
            ["First-time investor", "Multi-property host"],
            key="global_profile",
        )

    with i4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        analyse = st.button("Analyse Investment")

    st.markdown("</div>", unsafe_allow_html=True)

    if analyse:
        st.session_state.score_page = "Dashboard"

# -----------------------------
# FILTER DATA
# -----------------------------
city_df = lad_df[lad_df["city"].str.title() == city].copy()

if "median_house_price_2025_lad" in city_df.columns:
    city_df = city_df[city_df["median_house_price_2025_lad"] <= budget]

if city_df.empty:
    best_area = None
    st.warning("No areas match this budget. Try increasing the budget.")
else:
    best_area = city_df.sort_values("investment_score", ascending=False).iloc[0]

# -----------------------------
# MAIN HEADER
# -----------------------------
st.markdown(
    '<div class="main-title">Welcome to <span class="teal">InvestStay</span></div>',
    unsafe_allow_html=True
)

st.write("Smart Data. Smart Investments.")
render_stripes()

# -----------------------------
# MAIN PAGE NAVIGATION BUTTONS
# -----------------------------
nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

with nav1:
    if st.button("Home", key="score_nav_home"):
        st.session_state.score_page = "Home"

with nav2:
    if st.button("Dashboard", key="score_nav_dashboard"):
        st.session_state.score_page = "Dashboard"

with nav3:
    if st.button("Score Breakdown", key="score_nav_breakdown"):
        st.session_state.score_page = "Score Breakdown"

with nav4:
    if st.button("Compare Areas", key="score_nav_compare"):
        st.session_state.score_page = "Compare Areas"

with nav5:
    if st.button("Recommendation", key="score_nav_recommendation"):
        st.session_state.score_page = "Recommendation"

with nav6:
    if st.button("Risks", key="score_nav_risks"):
        st.session_state.score_page = "Risks"

st.divider()

# -----------------------------
# HOME PAGE
# -----------------------------
if st.session_state.score_page == "Home":

    st.subheader("Find the best area to invest in")

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown(
            """
            <div class="card">
            <h3>What does this app do?</h3>
            <p>
            InvestStay helps property investors compare short-term rental income,
            long-term rental yield, demand, market saturation and review quality.
            </p>
            <p>
            Enter your search inputs on the left, then click Analyse Investment.
            </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="card">
            <h3>Your Search</h3>
            <p><b>City:</b> {city}</p>
            <p><b>Budget:</b> £{budget:,}</p>
            <p><b>Investor Type:</b> {profile}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------
# DASHBOARD PAGE
# -----------------------------
elif st.session_state.score_page == "Dashboard":

    st.subheader("Investment Dashboard")

    if best_area is None:
        st.warning("No data available.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div class="card">
                <p>Investment Score</p>
                <div class="score">{best_area['investment_score']}/100</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.metric("Recommended Area", best_area["lad_name"])
            st.metric("STR Yield", f"{best_area['str_gross_yield']:.2%}")

        with col3:
            st.metric("LTR Yield", f"{best_area['ltr_gross_yield']:.2%}")
            st.metric("Estimated STR Revenue", f"£{best_area['str_annual_revenue_est']:,.0f}")

        st.subheader("Top 5 Investment Areas")

        top5 = city_df.sort_values("investment_score", ascending=False).head(5)

        st.dataframe(
            top5[
                [
                    "lad_name",
                    "investment_score",
                    "str_gross_yield",
                    "ltr_gross_yield",
                    "str_annual_revenue_est",
                    "total_listings"
                ]
            ],
            use_container_width=True
        )

# -----------------------------
# SCORE BREAKDOWN
# -----------------------------
elif st.session_state.score_page == "Score Breakdown":

    st.subheader("Score Breakdown")

    if best_area is None:
        st.warning("No data available.")
    else:
        breakdown = pd.DataFrame({
            "Metric": [
                "Revenue Score",
                "Occupancy Score",
                "STR Yield Score",
                "Yield Gap Score",
                "Saturation Score"
            ],
            "Score": [
                best_area["revenue_score"],
                best_area["occupancy_score"],
                best_area["str_yield_score"],
                best_area["yield_gap_score"],
                best_area["saturation_score"]
            ]
        })

        st.bar_chart(breakdown.set_index("Metric"))

        st.markdown(
            """
            <div class="card">
            <h3>How the score works</h3>
            <p>The investment score combines revenue, occupancy, short-term rental yield,
            yield gap and market saturation into one overall score out of 100.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------
# COMPARE AREAS
# -----------------------------
elif st.session_state.score_page == "Compare Areas":

    st.subheader(f"Compare Areas in {city}")

    ranked = city_df.sort_values("investment_score", ascending=False)

    cols = [
        "lad_name",
        "investment_score",
        "str_gross_yield",
        "ltr_gross_yield",
        "str_vs_ltr_yield_delta",
        "str_annual_revenue_est",
        "avg_nightly_price",
        "total_listings",
        "avg_review_score"
    ]

    available_cols = [c for c in cols if c in ranked.columns]

    st.dataframe(ranked[available_cols], use_container_width=True)

    st.subheader("Investment Score Ranking")
    st.bar_chart(ranked.set_index("lad_name")["investment_score"])

# -----------------------------
# RECOMMENDATION
# -----------------------------
elif st.session_state.score_page == "Recommendation":

    st.subheader("Recommendation")

    if best_area is None:
        st.warning("No recommendation available.")
    else:
        st.success(f"Recommended Area: {best_area['lad_name']}")

        insight = generate_insight(
            area_name=best_area["lad_name"],
            city=city,
            budget=budget,
            stats={
                "str_yield": best_area["str_gross_yield"],
                "ltr_yield": best_area["ltr_gross_yield"],
                "str_revenue": best_area["str_annual_revenue_est"],
                "saturation_score": best_area["saturation_score"],
                "investment_score": best_area["investment_score"],
            },
        )

        st.markdown(
            f"""
            <div class="card">
            <h3>Why {best_area['lad_name']}?</h3>
            <p>{insight}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------
# RISKS
# -----------------------------
elif st.session_state.score_page == "Risks":

    st.subheader("Risk Assessment")

    if best_area is None:
        st.warning("No risk data available.")
    else:
        st.markdown(
            f"""
            <div class="card">
            <h3>Risk overview for {best_area['lad_name']}</h3>
            <p>
            This section highlights key investment risks that could affect
            short-term rental performance.
            </p>
            </div>
            """,
            unsafe_allow_html=True
        )
