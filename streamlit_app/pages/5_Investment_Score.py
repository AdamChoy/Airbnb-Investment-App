import base64
import json
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, get_theme, inject_css, _get_logo_b64, render_navbar, render_stripes
from ai_insight import generate_insight

st.set_page_config(page_title="Investment Score · InvestStay", layout="wide", initial_sidebar_state="collapsed")

# -----------------------------
# LOAD DATA
# -----------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

lad_df = pd.read_csv(os.path.join(DATA_DIR, "lad_investment_summary.csv"))
msoa_df = pd.read_csv(os.path.join(DATA_DIR, "msoa_investment_summary.csv"))

@st.cache_data
def load_msoa_geojson():
    path = os.path.join(DATA_DIR, "msoa_boundaries_filtered.geojson")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

msoa_geojson = load_msoa_geojson()

# -----------------------------
# CITY CARDS
# -----------------------------
def get_city_img_tag(city_name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(ASSETS_DIR, f"{city_name.lower()}{ext}")
        if os.path.exists(path):
            mime = "jpeg" if ext in (".jpg", ".jpeg") else ext.lstrip(".")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/{mime};base64,{b64}" alt="{city_name}"/>'
    return ""

CITIES = ["London", "Manchester", "Bristol"]

# -----------------------------
# STYLE
# -----------------------------
t = get_theme()
inject_css(extra_css=f"""
.main-title {{ font-size: 2.25rem; font-weight: 800; }}
.teal {{ color: {TEAL}; }}
.score {{ font-size: 54px; font-weight: 800; color: {TEAL}; }}
.stButton > button {{
    background-color: {TEAL}; color: white; border: none;
    border-radius: 12px; padding: 0.7rem 1.2rem; font-weight: 600;
}}
.stButton > button:hover {{ background-color: #0b7d73; color: white; }}
.step-label {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {TEAL};
    margin-bottom: 10px;
}}
.cities-grid {{
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 24px;
    margin-bottom: 28px;
}}
.city-card.is-selected, .city-card:focus, .city-card:focus-visible {{
    outline: none;
    box-shadow: 0 0 0 3px {TEAL};
}}
.city-card {{
    position: relative;
    display: block;
    height: 220px;
    border-radius: 16px;
    overflow: hidden;
    text-decoration: none;
    background: #1a1a1a;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.city-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 0 0 2px rgba(255,255,255,0.85), 0 0 28px 4px rgba(255,255,255,0.6), 0 10px 24px rgba(0,0,0,0.2);
}}
.city-card img {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}}
.city-card-placeholder {{
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #1B4F72, #10c87a);
}}
.city-card::after {{
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.65) 100%);
}}
.city-card-label {{
    position: absolute;
    left: 20px;
    bottom: 16px;
    z-index: 2;
    color: #fff;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}}
.table-card {{
    background: {t['card_bg']};
    border-radius: 16px;
    overflow: auto;
    max-height: 480px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 8px;
}}
.styled-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    white-space: nowrap;
}}
.styled-table thead th {{
    position: sticky;
    top: 0;
    background: {TEAL};
    color: #fff;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 14px 20px;
    text-align: left;
}}
.styled-table tbody td {{
    padding: 12px 20px;
    color: {t['text']};
    border-bottom: 1px solid {t['border']};
}}
.styled-table tbody tr:nth-child(even) {{ background: {t['card_alt_bg']}; }}
.styled-table tbody tr:hover {{ background: {t['card_alt_hover']}; }}
.styled-table tbody tr:last-child td {{ border-bottom: none; }}
.styled-table td.score-cell {{
    color: {TEAL};
    font-weight: 700;
}}
[data-testid="stPlotlyChart"] {{
    border: 1px solid {t['border']};
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
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
# CITY SELECTION (city cards toggle ?cities= on click, read back here)
# -----------------------------
city_options = sorted(lad_df["city"].dropna().str.title().unique())

selected_cities = [c for c in st.session_state.get("global_cities", []) if c in city_options]
if not selected_cities:
    selected_cities = [city_options[0]]

qp_cities = [c.title() for c in st.query_params.get("cities", "").split(",") if c.strip()]
qp_cities = [c for c in qp_cities if c in city_options]
if qp_cities:
    selected_cities = qp_cities

st.session_state["global_cities"] = selected_cities
cities = selected_cities

# -----------------------------
# LAD SELECTION (auto-selects all LADs in the chosen cities; user can narrow down)
# -----------------------------
lad_options = sorted(lad_df[lad_df["city"].str.title().isin(cities)]["lad_name"].dropna().unique())

prev_lads = [l for l in st.session_state.get("global_lads", []) if l in lad_options]
if st.session_state.get("global_lads_cities") != cities or not prev_lads:
    prev_lads = lad_options

st.session_state["global_lads_cities"] = cities
st.session_state["global_lads"] = prev_lads

# -----------------------------
# SEARCH INPUTS (persist across pages via shared session_state keys)
# -----------------------------
with st.container():
    st.markdown(
        '<div class="main-title" style="margin-bottom:20px;">Find Your Perfect <span class="teal">Property</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div class='step-label'>1. Select your areas</div>", unsafe_allow_html=True)

    def _toggle_href(name):
        s = set(selected_cities)
        if name in s:
            if len(s) > 1:
                s.discard(name)
        else:
            s.add(name)
        return "?cities=" + ",".join(sorted(s))

    city_cards = "".join([
        f'''<a class="city-card{" is-selected" if name in selected_cities else ""}" href="{_toggle_href(name)}" target="_self">
            {get_city_img_tag(name) or '<div class="city-card-placeholder"></div>'}
            <div class="city-card-label">{name}</div>
        </a>'''
        for name in CITIES
    ])
    st.markdown(f'<div class="cities-grid">{city_cards}</div>', unsafe_allow_html=True)

    st.markdown("<div class='step-label'>2. Local Authority Districts</div>", unsafe_allow_html=True)
    lads = st.multiselect(
        "Local Authority Districts",
        options=lad_options,
        key="global_lads",
        label_visibility="collapsed",
    )

    st.markdown("<div class='step-label'>3. Choose your investment budget (£)</div>", unsafe_allow_html=True)
    budget_min, budget_max = st.slider(
        "Choose your investment budget (£)", 50000, 1000000, value=(50000, 300000), step=10000,
        key="global_budget_range", label_visibility="collapsed",
    )

    st.markdown("<div class='step-label'>4. Investor profile</div>", unsafe_allow_html=True)
    profile = st.selectbox(
        "Investor Profile",
        ["First-time investor", "Multi-property host"],
        key="global_profile",
        label_visibility="collapsed",
    )

    st.markdown("<div class='step-label'>5. Transport &amp; GP amenities</div>", unsafe_allow_html=True)
    amen_col1, amen_col2 = st.columns(2)
    with amen_col1:
        transport_access = st.selectbox(
            "Transport access",
            ["Any", "Within 15-min walk", "Within 30-min walk"],
            key="global_transport",
        )
    with amen_col2:
        min_gp = st.slider(
            "Minimum GP surgeries nearby",
            0, int(msoa_df["gp_surgery_count"].max()), 0,
            key="global_min_gp",
        )

    analyse = st.button("Analyse Investment")

    if analyse:
        st.session_state.score_page = "Dashboard"

# -----------------------------
# SUITABLE MSOAS
# -----------------------------
suitable_msoas = msoa_df[
    msoa_df["city"].str.title().isin(cities) & msoa_df["lad_name"].isin(lads)
].copy()
if "median_house_price_2025" in suitable_msoas.columns:
    suitable_msoas = suitable_msoas[
        suitable_msoas["median_house_price_2025"].between(budget_min, budget_max)
    ]
if transport_access == "Within 15-min walk":
    suitable_msoas = suitable_msoas[suitable_msoas["less_than_15_minute_walk"].fillna(0) > 0]
elif transport_access == "Within 30-min walk":
    suitable_msoas = suitable_msoas[suitable_msoas["less_than_30_minute_walk"].fillna(0) > 0]
suitable_msoas = suitable_msoas[suitable_msoas["gp_surgery_count"].fillna(0) >= min_gp]
suitable_msoas = suitable_msoas.sort_values("investment_score", ascending=False)

st.markdown("<div class='step-label' style='margin-top:8px;'>Suitable areas</div>", unsafe_allow_html=True)

if suitable_msoas.empty:
    st.warning(f"No areas in {', '.join(cities)} match your budget, transport and amenity filters. Try widening them.")
else:
    msoa_table = suitable_msoas[
        ["msoa_name", "city", "lad_name", "median_house_price_2025",
         "str_gross_yield", "ltr_gross_yield", "investment_score"]
    ].copy()
    msoa_table["city"] = msoa_table["city"].str.title()
    msoa_table["median_house_price_2025"] = msoa_table["median_house_price_2025"].apply(lambda x: f"£{x:,.0f}")
    msoa_table["str_gross_yield"] = (msoa_table["str_gross_yield"] * 100).round(2).astype(str) + "%"
    msoa_table["ltr_gross_yield"] = (msoa_table["ltr_gross_yield"] * 100).round(2).astype(str) + "%"
    msoa_table["investment_score"] = suitable_msoas["investment_score"].round(1)
    msoa_table.columns = [
        "MSOA", "City", "Local Authority District", "House Price",
        "Short-Term Rental Yield", "Long-Term Rental Yield", "Investment Score",
    ]

    thead_cells = "".join(f"<th>{c}</th>" for c in msoa_table.columns)
    body_rows = "".join(
        "<tr>" + "".join(
            f'<td class="score-cell">{row["Investment Score"]}</td>' if col == "Investment Score" else f"<td>{row[col]}</td>"
            for col in msoa_table.columns
        ) + "</tr>"
        for _, row in msoa_table.iterrows()
    )
    st.markdown(
        f'''<div class="table-card"><table class="styled-table">
            <thead><tr>{thead_cells}</tr></thead>
            <tbody>{body_rows}</tbody>
        </table></div>''',
        unsafe_allow_html=True,
    )

# -----------------------------
# INVESTMENT SCORE MAP
# -----------------------------
st.markdown("<div class='step-label' style='margin-top:8px;'>Investment score by area</div>", unsafe_allow_html=True)

map_msoas = msoa_df[
    msoa_df["city"].str.title().isin(cities) & msoa_df["lad_name"].isin(lads)
].copy()

if msoa_geojson is None or map_msoas.empty:
    st.info("No map data available for the selected areas.")
else:
    map_codes = set(map_msoas["msoa_code"])
    filtered_geojson = {
        "type": "FeatureCollection",
        "features": [
            f for f in msoa_geojson["features"]
            if f["properties"].get("MSOA21CD") in map_codes
        ],
    }

    visible_cities = [c for c in cities if not map_msoas[map_msoas["city"].str.title() == c].empty]
    map_cols = st.columns(len(visible_cities)) if visible_cities else []

    for col, city_name in zip(map_cols, visible_cities):
        city_map_df = map_msoas[map_msoas["city"].str.title() == city_name]

        city_codes = set(city_map_df["msoa_code"])
        coords = [
            (f["properties"]["LAT"], f["properties"]["LONG"])
            for f in filtered_geojson["features"]
            if f["properties"].get("MSOA21CD") in city_codes
            and "LAT" in f["properties"] and "LONG" in f["properties"]
        ]
        center = (
            {"lat": sum(c[0] for c in coords) / len(coords), "lon": sum(c[1] for c in coords) / len(coords)}
            if coords else {"lat": 52.5, "lon": -1.5}
        )

        with col:
            st.markdown(f"<p style='font-weight:600;margin-bottom:8px;'>{city_name}</p>", unsafe_allow_html=True)

            fig = px.choropleth_map(
                city_map_df,
                geojson=filtered_geojson,
                locations="msoa_code",
                featureidkey="properties.MSOA21CD",
                color="investment_score",
                color_continuous_scale=[[0, "#E3EEEC"], [1, TEAL]],
                hover_name="msoa_name",
                hover_data={"msoa_code": False, "investment_score": ":.1f"},
                labels={"investment_score": "Investment Score"},
                map_style="carto-positron",
                center=center,
                zoom=9.3,
                opacity=0.85,
                height=460,
            )
            fig.update_traces(marker_line_width=1, marker_line_color="#ffffff")
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", font_family="Inter")
            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})

# -----------------------------
# FILTER DATA
# -----------------------------
city_df = lad_df[
    lad_df["city"].str.title().isin(cities) & lad_df["lad_name"].isin(lads)
].copy()

if "median_house_price_2025_lad" in city_df.columns:
    city_df = city_df[
        city_df["median_house_price_2025_lad"].between(budget_min, budget_max)
    ]

if city_df.empty:
    best_area = None
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
            <p><b>Areas:</b> {", ".join(cities)}</p>
            <p><b>Budget:</b> £{budget_min:,} – £{budget_max:,}</p>
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

    st.subheader(f"Compare Areas in {', '.join(cities)}")

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
            city=best_area["city"].title(),
            budget=budget_max,
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
        # Overall risk level
        if best_area["saturation_score"] < 40:
            overall_risk = "🔴 High"
        elif best_area["saturation_score"] < 70:
            overall_risk = "🟡 Medium"
        else:
            overall_risk = "🟢 Low"

        st.markdown(f"## Overall Risk Level: {overall_risk}")

        # Risk cards
        rc1, rc2 = st.columns(2)

        with rc1:
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

            st.info("""
### 💷 Property Price

**Risk Level:** Medium 🟡

Higher property prices require greater upfront investment.

Expensive areas may provide strong long-term appreciation,
but they can increase the time required to recover the initial investment.
""")

        with rc2:
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

        # Risk summary
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

        # Additional investor information
        st.subheader("Additional Risk Information")

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
