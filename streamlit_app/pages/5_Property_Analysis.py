import base64
import json
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, get_theme, inject_css, _get_logo_b64, render_navbar, render_styled_table, style_chart, render_stat_card
from ai_insight import generate_insight
from scoring import PROFILES, DEFAULT_PROFILE, add_investment_score

st.set_page_config(page_title="Investment Score · InvestStay", layout="wide", initial_sidebar_state="collapsed")

# -----------------------------
# LOAD DATA
# -----------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

lad_df = pd.read_csv(os.path.join(DATA_DIR, "lad_investment_summary.csv"))
msoa_df = pd.read_csv(os.path.join(DATA_DIR, "msoa_investment_summary.csv"))

# lad_investment_summary.csv still has an Edinburgh row left over from an
# earlier dataset, but it's not one of the 3 cities selectable anywhere in
# this app's UI (see CITIES below) and msoa_investment_summary.csv never
# had it in the first place. Left in, it silently skews the min-max
# normalisation every investment_score is built from — drop it before
# scoring so LAD- and MSOA-level scores are computed over the same
# population of cities.
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
# CITY CARDS
# -----------------------------
def get_city_img_uri(city_name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(ASSETS_DIR, f"{city_name.lower()}{ext}")
        if os.path.exists(path):
            mime = "jpeg" if ext in (".jpg", ".jpeg") else ext.lstrip(".")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/{mime};base64,{b64}"
    return None

CITIES = ["London", "Manchester", "Bristol"]

# -----------------------------
# SCORING (shared with Home.py's coverage map — see scoring.py — so the
# same LAD never shows two different "Investment Score" numbers)
# -----------------------------
selected_profile = st.session_state.get("global_profile_key")
if selected_profile not in PROFILES:
    selected_profile = DEFAULT_PROFILE

st.session_state["global_profile_key"] = selected_profile
profile = PROFILES[selected_profile]["label"]

lad_df = add_investment_score(lad_df, PROFILES[selected_profile]["weights"])
msoa_df = add_investment_score(msoa_df, PROFILES[selected_profile]["weights"])

# -----------------------------
# SESSION STATE
# -----------------------------
if "score_page" not in st.session_state:
    st.session_state.score_page = "Dashboard"

# -----------------------------
# CITY SELECTION (city cards write straight to session_state + st.rerun(),
# so no other widget on the page loses its state — see the card buttons below)
# -----------------------------
city_options = sorted(lad_df["city"].dropna().str.title().unique())

selected_cities = [c for c in st.session_state.get("global_cities", []) if c in city_options]
if not selected_cities:
    selected_cities = [city_options[0]]

st.session_state["global_cities"] = selected_cities
cities = selected_cities

# -----------------------------
# LAD SELECTION (auto-selects all LADs in the chosen cities; user can narrow down)
# -----------------------------
lad_options = sorted(lad_df[lad_df["city"].str.title().isin(cities)]["lad_name"].dropna().unique())

# Auto-select all LADs whenever the city selection changes (or on first load) —
# but once that's happened, respect an explicit empty selection (e.g. from the
# "Clear all" button below) instead of silently re-filling it.
if "global_lads" not in st.session_state or st.session_state.get("global_lads_cities") != cities:
    prev_lads = lad_options
else:
    prev_lads = [l for l in st.session_state.get("global_lads", []) if l in lad_options]

st.session_state["global_lads_cities"] = cities
st.session_state["global_lads"] = prev_lads

# -----------------------------
# STYLE (one injection point for the whole page — city/profile/LAD-button
# CSS depends on selected_cities/selected_profile, computed above, so it's
# folded in here rather than injected separately later via ad hoc
# st.markdown("<style>...") calls scattered through the render code)
# -----------------------------
t = get_theme()

city_button_css = ""
for name in CITIES:
    uri = get_city_img_uri(name)
    bg_img = f"url('{uri}')" if uri else "none"
    bg_fallback = "#1a1a1a" if uri else "linear-gradient(135deg, #1B4F72, #10c87a)"
    shadow = f"0 0 0 3px {TEAL}" if name in selected_cities else "0 2px 12px rgba(0,0,0,0.08)"
    city_button_css += f"""
    .st-key-city_{name} button {{
        height: 220px !important; width: 100% !important; border: none !important;
        border-radius: 16px !important;
        background-image: linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.65) 100%), {bg_img} !important;
        background-size: cover !important; background-position: center !important;
        background-color: {bg_fallback} !important;
        display: flex !important; align-items: flex-end !important; justify-content: flex-start !important;
        padding: 16px 20px !important; color: #fff !important; font-size: 1.3rem !important;
        font-weight: 700 !important; letter-spacing: -0.02em !important; text-align: left !important;
        box-shadow: {shadow} !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .st-key-city_{name} button:hover {{
        transform: translateY(-4px);
        box-shadow: 0 0 0 2px rgba(255,255,255,0.85), 0 0 28px 4px rgba(255,255,255,0.6), 0 10px 24px rgba(0,0,0,0.2) !important;
    }}
    """

profile_button_css = "".join(f"""
.st-key-profile_{key} button {{
    width: 100% !important; border: none !important; border-radius: 16px !important;
    background: {t['card_bg']} !important; color: {t['text']} !important;
    padding: 20px 22px !important; text-align: left !important; font-size: 1.05rem !important;
    font-weight: 700 !important; white-space: normal !important;
    box-shadow: {"0 0 0 3px " + TEAL if key == selected_profile else "0 2px 12px rgba(0,0,0,0.08)"} !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.st-key-profile_{key} button:hover {{
    transform: translateY(-4px);
    box-shadow: 0 4px 18px rgba(0,0,0,0.12) !important;
}}
""" for key in PROFILES)

inject_css(extra_css=f"""
.main-title {{ font-size: 2.25rem; font-weight: 800; }}
.teal {{ color: {TEAL}; }}
/* Scoped to just the 5 Dashboard/Score Breakdown/etc. nav tabs — NOT a
   blanket .stButton > button rule. A blanket rule here would apply to
   every button on the page (city cards, profile cards, LAD select/clear),
   forcing each of those to fight it back off with !important. Scoping the
   teal-pill look to only the buttons that actually want it means the
   others don't have to. (Streamlit puts the st-key-<key> class on the
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
.step-label {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {TEAL};
    margin-bottom: 10px;
}}
.profile-card-desc {{
    font-size: 0.85rem;
    line-height: 1.5;
    color: {t['text_muted']};
    margin-top: 8px;
}}
[data-testid="stPlotlyChart"] {{
    border: 1px solid {t['border']};
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
{city_button_css}
{profile_button_css}
.st-key-lads_select_all button, .st-key-lads_clear_all button {{
    background: transparent !important; color: {TEAL} !important; border: none !important;
    box-shadow: none !important; padding: 0 !important; height: auto !important;
    font-size: 0.78rem !important; font-weight: 600 !important; text-decoration: underline !important;
}}
.st-key-lads_select_all button:hover, .st-key-lads_clear_all button:hover {{
    color: #0b7d73 !important; background: transparent !important;
}}
""")
render_navbar(active="Score")

# -----------------------------
# SEARCH INPUTS (persist across pages via shared session_state keys)
# -----------------------------
with st.container():
    st.markdown(
        '<div class="main-title" style="margin-bottom:20px;">Find Your Perfect <span class="teal">Property</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div class='step-label'>1. Select your areas</div>", unsafe_allow_html=True)

    city_cols = st.columns(3)
    for col, name in zip(city_cols, CITIES):
        with col:
            if st.button(name, key=f"city_{name}", use_container_width=True):
                s = set(selected_cities)
                if name in s:
                    if len(s) > 1:
                        s.discard(name)
                else:
                    s.add(name)
                st.session_state["global_cities"] = sorted(s)
                st.rerun()

    label_col, sel_col, clr_col = st.columns([8, 1.3, 1.3])
    with label_col:
        st.markdown("<div class='step-label'>2. Local Authority Districts</div>", unsafe_allow_html=True)
    with sel_col:
        if st.button("Select all", key="lads_select_all", use_container_width=True):
            st.session_state["global_lads"] = lad_options
            st.rerun()
    with clr_col:
        if st.button("Clear all", key="lads_clear_all", use_container_width=True):
            st.session_state["global_lads"] = []
            st.rerun()

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

    st.markdown("<div class='step-label'>4. Transport &amp; local amenities</div>", unsafe_allow_html=True)
    amen_col1, amen_col2, amen_col3 = st.columns(3)
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
    with amen_col3:
        min_parks = st.slider(
            "Minimum parks nearby",
            0, int(msoa_df["total_parks_count"].max()), 0,
            key="global_min_parks",
        )

    st.markdown("<div class='step-label'>5. Investor profile</div>", unsafe_allow_html=True)

    profile_cols = st.columns(3)
    for col, (key, data) in zip(profile_cols, PROFILES.items()):
        with col:
            if st.button(data["label"], key=f"profile_{key}", use_container_width=True):
                st.session_state["global_profile_key"] = key
                st.rerun()
            st.markdown(f"<div class='profile-card-desc'>{data['sentence']}</div>", unsafe_allow_html=True)

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

st.markdown("<div class='step-label' style='margin-top:8px;margin-bottom:20px;'>Suitable areas</div>", unsafe_allow_html=True)

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

        st.subheader("Top 5 Investment Areas")

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

        st.markdown(
            f"""
            <div class="card">
            <h3>How the score works</h3>
            <p>The investment score combines revenue, occupancy, short-term rental yield,
            yield gap, market saturation and guest review score into one overall score out
            of 100. Your <b>{profile}</b> profile is currently selected: {PROFILES[selected_profile]['sentence']}</p>
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
