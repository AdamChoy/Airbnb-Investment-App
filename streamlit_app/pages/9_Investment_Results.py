import json
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, get_theme, inject_css, render_navbar, render_styled_table, style_chart, render_stat_card
from ai_insight import generate_insight
from scoring import PROFILES, DEFAULT_PROFILE, add_investment_score

st.set_page_config(page_title="Investment Results · InvestStay", layout="wide", initial_sidebar_state="collapsed")

# -----------------------------
# LOAD DATA
# -----------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

lad_df = pd.read_csv(os.path.join(DATA_DIR, "lad_investment_summary.csv"))
msoa_df = pd.read_csv(os.path.join(DATA_DIR, "msoa_investment_summary.csv"))
lad_df = lad_df[lad_df["city"].isin(["london", "manchester", "bristol"])].copy()

@st.cache_data
def load_msoa_geojson():
    path = os.path.join(DATA_DIR, "msoa_boundaries_filtered.geojson")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

msoa_geojson = load_msoa_geojson()

# -----------------------------
# SCORING (same weights/logic as the Invest page and Home.py's coverage
# map — see scoring.py — so the same LAD never shows two different
# "Investment Score" numbers)
# -----------------------------
selected_profile = st.session_state.get("global_profile_key")
if selected_profile not in PROFILES:
    selected_profile = DEFAULT_PROFILE

profile = PROFILES[selected_profile]["label"]

lad_df = add_investment_score(lad_df, PROFILES[selected_profile]["weights"])
msoa_df = add_investment_score(msoa_df, PROFILES[selected_profile]["weights"])

if "score_page" not in st.session_state:
    st.session_state.score_page = "Dashboard"

# -----------------------------
# READ SEARCH CRITERIA FROM THE INVEST PAGE (session_state — this page has
# no inputs of its own; go back to /Property_Analysis to change them)
# -----------------------------
cities = st.session_state.get("global_cities", [])
lads = st.session_state.get("global_lads", [])
budget_min, budget_max = st.session_state.get("global_budget_range", (50000, 300000))
transport_access = st.session_state.get("global_transport", "Any")
min_gp = st.session_state.get("global_min_gp", 0)
min_parks = st.session_state.get("global_min_parks", 0)

t = get_theme()
inject_css(extra_css=f"""
.main-title {{ font-size: 2.25rem; font-weight: 800; }}
.teal {{ color: {TEAL}; }}
/* Scoped to just the 5 Dashboard/Score Breakdown/etc. nav tabs — NOT a
   blanket .stButton > button rule. A blanket rule here would apply to
   every button on the page, forcing others to fight it back off with
   !important. (Streamlit puts the st-key-<key> class on the
   stElementContainer wrapping the button, not on the button/stButton div
   itself — the descendant selector below still reaches the <button> fine.) */
.st-key-score_nav_dashboard button,
.st-key-score_nav_breakdown button,
.st-key-score_nav_compare button,
.st-key-score_nav_recommendation button,
.st-key-score_nav_risks button {{
    background-color: {TEAL}; color: white; border: none;
    border-radius: 12px; padding: 0.7rem 1.2rem; font-weight: 600;
}}
.st-key-score_nav_dashboard button:hover,
.st-key-score_nav_breakdown button:hover,
.st-key-score_nav_compare button:hover,
.st-key-score_nav_recommendation button:hover,
.st-key-score_nav_risks button:hover {{
    background-color: #0b7d73; color: white;
}}
[data-testid="stPlotlyChart"] {{
    border: 1px solid {t['border']};
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
.st-key-edit_search button {{
    background: transparent !important; color: {TEAL} !important; border: none !important;
    box-shadow: none !important; padding: 0 !important; height: auto !important;
    font-size: 0.85rem !important; font-weight: 600 !important; text-decoration: underline !important;
}}
.st-key-edit_search button:hover {{
    color: #0b7d73 !important; background: transparent !important;
}}
""")
render_navbar(active="Invest")

# -----------------------------
# GUARD — this page only makes sense after the Invest page's inputs have
# been set (e.g. a direct link, or a fresh session with nothing chosen yet)
# -----------------------------
if not cities or not lads:
    st.markdown(
        '<div class="main-title" style="margin-bottom:12px;">Investment <span class="teal">Results</span></div>',
        unsafe_allow_html=True,
    )
    st.warning("No search criteria set yet.")
    if st.button("← Set your search criteria", key="go_to_search"):
        st.switch_page("pages/5_Property_Analysis.py")
    st.stop()

top_row1, top_row2 = st.columns([5, 1.3])
with top_row1:
    st.markdown(
        '<div class="main-title" style="margin-bottom:4px;">Investment <span class="teal">Results</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{t['text_muted']};margin-bottom:0;'>"
        f"{', '.join(cities)}  ·  £{budget_min:,}–£{budget_max:,}  ·  {profile} profile</p>",
        unsafe_allow_html=True,
    )
with top_row2:
    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
    if st.button("← Edit search", key="edit_search", use_container_width=True):
        st.switch_page("pages/5_Property_Analysis.py")

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

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
suitable_msoas = suitable_msoas[suitable_msoas["total_parks_count"].fillna(0) >= min_parks]
suitable_msoas = suitable_msoas.sort_values("investment_score", ascending=False)

st.markdown("<div class='step-label' style='margin-top:24px;margin-bottom:20px;'>Suitable neighbourhoods (MSOA)</div>", unsafe_allow_html=True)

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

    render_styled_table(msoa_table, highlight_cols=["Investment Score"])

# -----------------------------
# INVESTMENT SCORE MAP
# -----------------------------
st.markdown("<div class='step-label' style='margin-top:32px;'>Investment score by area</div>", unsafe_allow_html=True)

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
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
            style_chart(fig)
            fig.update_layout(coloraxis_colorbar=dict(title_font_color="#1a1a1a", tickfont_color="#1a1a1a"))
            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})

st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)

# -----------------------------
# FILTER DATA
# -----------------------------
city_df = lad_df[
    lad_df["city"].str.title().isin(cities) & lad_df["lad_name"].isin(lads)
].copy()

# Budget is a per-property figure, so it's applied at MSOA level (see
# suitable_msoas above) rather than against a LAD's aggregate median price —
# a LAD stays in play here as long as at least one of its MSOAs is in budget.
budget_ok_lads = suitable_msoas["lad_name"].unique()
city_df = city_df[city_df["lad_name"].isin(budget_ok_lads)]

if city_df.empty:
    best_area = None
else:
    best_area = city_df.sort_values("investment_score", ascending=False).iloc[0]

# -----------------------------
# MAIN PAGE NAVIGATION BUTTONS
# -----------------------------
nav1, nav2, nav3, nav4, nav5 = st.columns(5)

with nav1:
    if st.button("Dashboard", key="score_nav_dashboard"):
        st.session_state.score_page = "Dashboard"

with nav2:
    if st.button("Score Breakdown", key="score_nav_breakdown"):
        st.session_state.score_page = "Score Breakdown"

with nav3:
    if st.button("Compare Areas", key="score_nav_compare"):
        st.session_state.score_page = "Compare Areas"

with nav4:
    if st.button("Recommendation", key="score_nav_recommendation"):
        st.session_state.score_page = "Recommendation"

with nav5:
    if st.button("Risks", key="score_nav_risks"):
        st.session_state.score_page = "Risks"

st.divider()

# -----------------------------
# DASHBOARD PAGE
# -----------------------------
if st.session_state.score_page == "Dashboard":

    st.subheader("Investment Dashboard")

    if best_area is None:
        st.warning("No data available.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            render_stat_card("Investment Score", best_area["investment_score"], unit="/ 100", big=True)

        with col2:
            st.metric("Recommended Area", best_area["lad_name"])
            st.metric("STR Yield", f"{best_area['str_gross_yield']:.2%}")

        with col3:
            st.metric("LTR Yield", f"{best_area['ltr_gross_yield']:.2%}")
            st.metric("Estimated STR Revenue", f"£{best_area['str_annual_revenue_est']:,.0f}")

        st.subheader("Top 5 Districts (LAD)")

        top5 = city_df.sort_values("investment_score", ascending=False).head(5)[
            ["lad_name", "investment_score", "str_gross_yield", "ltr_gross_yield",
             "str_annual_revenue_est", "total_listings"]
        ].copy()
        top5["investment_score"] = top5["investment_score"].round(1)
        top5["str_gross_yield"] = (top5["str_gross_yield"] * 100).round(2).astype(str) + "%"
        top5["ltr_gross_yield"] = (top5["ltr_gross_yield"] * 100).round(2).astype(str) + "%"
        top5["str_annual_revenue_est"] = top5["str_annual_revenue_est"].apply(lambda x: f"£{x:,.0f}")
        top5.columns = ["Local Authority District", "Investment Score", "STR Yield",
                         "LTR Yield", "Est. STR Revenue", "Total Listings"]

        render_styled_table(top5, highlight_cols=["Investment Score"])

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
                "Saturation Score",
                "Review Score",
            ],
            "Score": [
                best_area["revenue_score"],
                best_area["occupancy_score"],
                best_area["str_yield_score"],
                best_area["yield_gap_score"],
                best_area["saturation_score"],
                best_area["review_score"],
            ]
        })

        breakdown_fig = px.bar(
            breakdown, x="Metric", y="Score",
            color_discrete_sequence=[TEAL],
            template="plotly_white",
        )
        breakdown_fig.update_layout(
            height=360, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20), showlegend=False,
        )
        style_chart(breakdown_fig)
        st.plotly_chart(breakdown_fig, use_container_width=True)

        weights = PROFILES[selected_profile]["weights"]
        metric_rows = "".join(f"""
            <tr>
                <td style="padding:10px 16px;font-weight:600;">{metric}</td>
                <td style="padding:10px 16px;color:{t['text_muted']};">{desc}</td>
                <td style="padding:10px 16px;text-align:right;font-weight:700;color:{TEAL};">{weights[wkey]*100:.0f}%</td>
            </tr>
        """ for metric, desc, wkey in [
            ("Revenue", "Estimated annual short-term rental income for the area", "revenue"),
            ("Occupancy", "How booked up the area's listings tend to be", "occupancy"),
            ("STR Yield", "Short-term rental income as a % of property value", "str_yield"),
            ("Yield Gap", "How much better STR yield is than long-term letting", "yield_gap"),
            ("Saturation", "Rewards areas with fewer competing listings", "saturation"),
            ("Reviews", "Average guest review score", "review"),
        ])

        st.markdown(
            f"""
            <div class="card">
            <h3 style="margin-top:0;">How the Investment Score is calculated</h3>
            <p style="color:{t['text_muted']};">
            Every area gets a 0–100 score built from six metrics, each normalised across
            all areas and combined as a weighted average. The weights below shift
            depending on which <b>investor profile</b> you pick — right now that's
            <b>{profile}</b>: {PROFILES[selected_profile]['sentence']}
            </p>
            <table style="width:100%;border-collapse:collapse;margin-top:12px;">
                <thead>
                    <tr style="border-bottom:2px solid {TEAL};">
                        <th style="padding:8px 16px;text-align:left;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.05em;">Metric</th>
                        <th style="padding:8px 16px;text-align:left;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.05em;">What it measures</th>
                        <th style="padding:8px 16px;text-align:right;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.05em;">Weight</th>
                    </tr>
                </thead>
                <tbody>
                    {metric_rows}
                </tbody>
            </table>
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

    ranked_display = ranked[available_cols].copy()
    if "investment_score" in ranked_display.columns:
        ranked_display["investment_score"] = ranked_display["investment_score"].round(1)
    for pct_col in ["str_gross_yield", "ltr_gross_yield", "str_vs_ltr_yield_delta"]:
        if pct_col in ranked_display.columns:
            ranked_display[pct_col] = (ranked_display[pct_col] * 100).round(2).astype(str) + "%"
    if "str_annual_revenue_est" in ranked_display.columns:
        ranked_display["str_annual_revenue_est"] = ranked_display["str_annual_revenue_est"].apply(lambda x: f"£{x:,.0f}")
    if "avg_nightly_price" in ranked_display.columns:
        ranked_display["avg_nightly_price"] = ranked_display["avg_nightly_price"].apply(lambda x: f"£{x:,.0f}")
    if "avg_review_score" in ranked_display.columns:
        ranked_display["avg_review_score"] = ranked_display["avg_review_score"].round(2)
    ranked_display.columns = [
        c.replace("_", " ").title().replace("Str", "STR").replace("Ltr", "LTR").replace("Lad", "LAD")
        for c in ranked_display.columns
    ]

    render_styled_table(ranked_display, highlight_cols=["Investment Score"])

    st.subheader("Investment Score Ranking")
    ranking_fig = px.bar(
        ranked, x="lad_name", y="investment_score",
        color_discrete_sequence=[TEAL],
        labels={"lad_name": "", "investment_score": "Investment Score"},
        template="plotly_white",
    )
    ranking_fig.update_layout(
        height=360, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20), showlegend=False,
    )
    style_chart(ranking_fig)
    st.plotly_chart(ranking_fig, use_container_width=True)

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
        st.caption(
            "General guidance for UK short-term-let investing — not specific to "
            f"{best_area['lad_name']} or calculated from this app's data."
        )

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

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
