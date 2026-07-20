import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="InvestStay Dashboard", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

lad_df = pd.read_csv(
    os.path.join(BASE_DIR, "data", "lad_investment_summary.csv")
)

msoa_df = pd.read_csv(
    os.path.join(BASE_DIR, "data", "msoa_investment_summary.csv")
)


# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #F3FBFA;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #0D223F;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #0D223F;
}

.teal {
    color: #00A99D;
}

.card {
    background-color: white;
    padding: 24px;
    border-radius: 18px;
    border: 1px solid #D9F3F0;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
}

.score {
    font-size: 54px;
    font-weight: 800;
    color: #00A99D;
}

.stButton > button {
    background-color: #00A99D;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 1.2rem;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #008C84;
    color: white;
}
</style>
""", unsafe_allow_html=True)

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
if "page" not in st.session_state:
    st.session_state.page = "Home"

# -----------------------------
# LEFT SIDEBAR = INPUTS ONLY
# -----------------------------
city = st.session_state.get("city", "London")
budget = st.session_state.get("budget", 250000)
profile = st.session_state.get("profile", "First-time investor")
rooms = st.session_state.get("bedrooms", 1)

with st.sidebar:
    logo_path = os.path.join(BASE_DIR, "assets", "logo investstay.png")
    st.image(logo_path, use_container_width=True)

    st.header("Your Search")
    st.write(f"**City:** {city}")
    st.write(f"**Budget:** £{budget:,}")
    st.write(f"**Investor Type:** {profile}")
    st.write(f"**Bedrooms:** {rooms}")

    if st.button("Change Search"):
        st.switch_page("home.py")

# -----------------------------
# FILTER DATA
# -----------------------------
city_df = lad_df[
    lad_df["city"].astype(str).str.lower() == city.lower()
].copy()

#if "median_house_price_2025_lad" in city_df.columns:
    #city_df = city_df[city_df["median_house_price_2025_lad"] <= budget]

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

# -----------------------------
# MAIN PAGE NAVIGATION BUTTONS
# -----------------------------
nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

with nav1:
    if st.button("Home"):
        st.session_state.page = "Home"

with nav2:
    if st.button("Dashboard"):
        st.session_state.page = "Dashboard"

with nav3:
    if st.button("Score Breakdown"):
        st.session_state.page = "Score Breakdown"

with nav4:
    if st.button("Compare Areas"):
        st.session_state.page = "Compare Areas"

with nav5:
    if st.button("Recommendation"):
        st.session_state.page = "Recommendation"

with nav6:
    if st.button("Risks"):
        st.session_state.page = "Risks"

st.divider()

# -----------------------------
# HOME PAGE
# -----------------------------
if st.session_state.page == "Home":

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
            <p><b>Bedrooms:</b> {rooms}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------
# DASHBOARD PAGE
# -----------------------------
elif st.session_state.page == "Dashboard":

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
elif st.session_state.page == "Score Breakdown":

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
elif st.session_state.page == "Compare Areas":

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
elif st.session_state.page == "Recommendation":

    st.subheader("Recommendation")

    if best_area is None:
        st.warning("No recommendation available.")
    else:
        st.success(f"Recommended Area: {best_area['lad_name']}")

        st.markdown(
            f"""
            <div class="card">
            <h3>Why {best_area['lad_name']}?</h3>
            <p>
            Based on your search for <b>{city}</b> with a budget of <b>£{budget:,}</b>,
            this area has the highest investment score.
            </p>
            <p>
            It performs well because it balances revenue potential, rental yield,
            demand and market saturation.
            </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
# -----------------------------
# RISKS
# -----------------------------
elif st.session_state.page == "Risks":

    st.subheader("Risk Assessment")

    if best_area is None:
        st.warning("No risk data available.")

    else:

        # -----------------------------
        # Calculate Overall Risk
        # -----------------------------

        if best_area["saturation_score"] < 40:
            overall_risk = "🔴 High"
        elif best_area["saturation_score"] < 70:
            overall_risk = "🟡 Medium"
        else:
            overall_risk = "🟢 Low"


        st.markdown(f"## Overall Risk Level: {overall_risk}")


        # -----------------------------
        # Risk Cards
        # -----------------------------

        col1, col2 = st.columns(2)


        with col1:

            # Market Saturation Risk
            if best_area["total_listings"] > city_df["total_listings"].median():
                competition = "High 🔴"
            else:
                competition = "Low 🟢"


            st.info(f"""
### 🏠 Market Saturation

**Risk Level:** {competition}

There are **{int(best_area['total_listings'])} Airbnb listings** in this area.

Higher listing numbers indicate increased competition between hosts,
which may reduce occupancy rates and pricing power.
""")


            # Property Price Risk
            st.info("""
### 💷 Property Price

**Risk Level:** Medium 🟡

Higher property prices require greater upfront investment.

Expensive areas may provide strong long-term appreciation,
but they can increase the time required to recover the initial investment.
""")


        with col2:

            # Occupancy Risk
            occupancy = 365 - best_area["avg_availability_365"]


            if occupancy > 250:
                occupancy_risk = "Low 🟢"
            elif occupancy > 180:
                occupancy_risk = "Medium 🟡"
            else:
                occupancy_risk = "High 🔴"


            st.info(f"""
### 📅 Occupancy

**Risk Level:** {occupancy_risk}

Estimated booked nights per year:

**{int(occupancy)} nights**

Lower occupancy can significantly impact Airbnb profitability.
""")


            # Regulation Risk
            st.info("""
### ⚖️ Regulation

**Risk Level:** Medium 🟡

Short-term rental regulations may change over time.

Investors should consider:
- Local council licensing rules
- Planning restrictions
- Future Airbnb policy changes
""")


        st.markdown("---")


        # -----------------------------
        # Risk Summary
        # -----------------------------

        st.subheader("Risk Summary")


        st.markdown(f"""
Although **{best_area['lad_name']}** achieved the highest investment score,
investors should consider the following risks:

- Competition from nearby Airbnb properties
- High upfront property costs
- Seasonal changes affecting occupancy
- Changes in short-term rental regulations

Overall, **{best_area['lad_name']}** offers strong investment potential,
but returns depend on maintaining good occupancy and managing costs effectively.
""")


        st.markdown("---")


        # -----------------------------
        # Additional Investor Information
        # -----------------------------

        st.subheader("Additional Risk Information")


        # AI Policy Section
        with st.expander("🤖 AI Use & Data Policy"):

            st.write("""
## How AI insights are generated

AI is used to help analyse properties, compare investment strategies,
and present investment insights clearly.

However, AI does not freely browse the internet or create unsupported facts.

The AI only uses:

- Property data provided by the user
- Market datasets loaded into the platform
- Defined rules, assumptions and investment models


## Reducing AI Hallucinations

To improve reliability:

- AI is restricted to structured and verified datasets
- Calculations are based on predefined formulas
- AI focuses on explaining trends rather than inventing facts
- Uncertainty is highlighted instead of guessed


## Investor Control

AI is a supporting tool, not a decision maker.

Investors remain responsible for:
- The data they provide
- The assumptions they choose
- Their final investment decisions
""")


        # Airbnb vs Renting Section
        with st.expander("🏠 Airbnb vs Long-Term Renting Risks"):

            st.write("""
## Airbnb Investment Risks


### ⚖️ Laws & Regulations

Airbnb investments may be affected by:

- Short-term rental licensing requirements
- The London 90-day rule for entire-home listings
- Planning permission restrictions
- Fire safety requirements
- Gas and electrical safety checks
- Insurance requirements


### 💰 Startup Costs

Airbnb usually requires higher initial spending:

- Furniture and property styling
- Kitchen equipment
- Smart locks/key systems
- Professional photography
- Safety equipment
- Listing setup


### 🔧 Maintenance Costs

Airbnb properties often have higher ongoing costs:

- Cleaning between guests
- Linen and consumable replacement
- Increased furniture wear
- More frequent repairs
- Higher insurance costs



---


# Long-Term Renting Risks


### ⚖️ Laws & Regulations

Long-term rentals require:

- Legal tenancy agreements
- Deposit protection
- Right-to-rent checks
- Gas safety certificates
- Electrical safety certificates
- EPC compliance


### 💰 Startup Costs

Typically lower than Airbnb:

- Basic property preparation
- Safety certificates
- Agent fees (if used)
- Initial cleaning


### 🔧 Maintenance Costs

Common costs include:

- Repairs
- Appliance replacement
- Landlord insurance
- Void periods
- Property refresh costs



---


## Investment Comparison


### Airbnb

✅ Potentially higher returns

❌ More regulations

❌ Higher operating costs

❌ Requires more active management


### Long-Term Renting

✅ Stable predictable income

✅ Lower maintenance workload

✅ Simpler management

❌ Usually lower maximum returns
""")


        st.markdown("---")


        # Final takeaway
        st.success(f"""
### Final Investor Takeaway

**{best_area['lad_name']}** provides attractive investment potential,
but investors should balance expected returns against:

- Market competition
- Regulatory uncertainty
- Operating costs
- Management requirements

A strong investment decision requires considering both
financial performance and potential risks.
""")
""")
        
