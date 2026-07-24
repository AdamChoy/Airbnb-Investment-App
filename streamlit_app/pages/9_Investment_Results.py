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

# lad_investment_summary.csv has no house-price-growth column (only MSOA-level
# data does) — derive a LAD figure as the median of its MSOAs' 10yr growth,
# so the Dashboard can show it alongside median house price.
lad_price_growth = msoa_df.groupby("lad_name")["price_growth_10yr"].median().rename("price_growth_10yr_lad")
lad_df = lad_df.merge(lad_price_growth, on="lad_name", how="left")

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
# global_lads/global_budget_range/etc. are owned by their st.slider/
# st.multiselect/st.selectbox widgets on the Invest page — Streamlit purges
# widget-owned session_state once that widget isn't instantiated (i.e. as
# soon as we're not on that page), so this page reads the plain "persist_*"
# copies the Invest page mirrors them into instead. See the comment there.
lads = st.session_state.get("persist_lads", [])
budget_min, budget_max = st.session_state.get("persist_budget_range", (50000, 300000))
transport_access = st.session_state.get("persist_transport", "Any")
min_gp = st.session_state.get("persist_min_gp", 0)
min_parks = st.session_state.get("persist_min_parks", 0)
granularity = st.session_state.get("persist_granularity", "Local Authority District (LAD)")

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
.st-key-score_nav_map button,
.st-key-score_nav_breakdown button,
.st-key-score_nav_compare button,
.st-key-score_nav_recommendation button,
.st-key-score_nav_risks button {{
    background-color: {TEAL}; color: white; border: none;
    border-radius: 12px; padding: 0.7rem 1.2rem; font-weight: 600;
}}
.st-key-score_nav_dashboard button:hover,
.st-key-score_nav_map button:hover,
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
.st-key-dashboard_border {{
    border: 2px solid #000; border-radius: 16px; padding: 28px 32px;
}}
.st-key-dashboard_border, .st-key-dashboard_border * {{
    color: #000 !important;
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

top_row1, top_row2 = st.columns([5, 1.3], vertical_alignment="center")
with top_row1:
    st.markdown(
        '<div class="main-title" style="margin-bottom:4px;">Investment <span class="teal">Results</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{t['text_muted']};margin-bottom:0;'>"
        f"{', '.join(cities)}  ·  £{budget_min:,}–£{budget_max:,}  ·  {profile} profile  ·  {granularity} recommendation</p>",
        unsafe_allow_html=True,
    )
with top_row2:
    if st.button("← Edit search", key="edit_search", use_container_width=True):
        st.switch_page("pages/5_Property_Analysis.py")

st.markdown("<div style='height:56px;'></div>", unsafe_allow_html=True)

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

# -----------------------------
# FILTER DATA + RECOMMENDATION GRANULARITY
# -----------------------------
# granularity (read above) decides what unit "best_area" and every tab
# below recommend. MSOA already has a ready-made, fully filtered, fully
# scored dataframe (suitable_msoas). LAD is the original city_df logic.
# City has no ready-made dataset, so it's built by aggregating the
# LAD-level rows up to city level and re-running the same scoring
# function on that.
lad_scope_df = lad_df[
    lad_df["city"].str.title().isin(cities) & lad_df["lad_name"].isin(lads)
].copy()

# Budget is a per-property figure, so it's applied at MSOA level (see
# suitable_msoas above) rather than against a LAD's aggregate median price —
# a LAD stays in play here as long as at least one of its MSOAs is in budget.
budget_ok_lads = suitable_msoas["lad_name"].unique()
lad_scope_df = lad_scope_df[lad_scope_df["lad_name"].isin(budget_ok_lads)]
lad_scope_df = lad_scope_df.rename(columns={
    "median_house_price_2025_lad": "median_house_price",
    "price_growth_10yr_lad": "price_growth_10yr",
})

if granularity == "Neighbourhood (MSOA)":
    area_df = suitable_msoas.rename(columns={"median_house_price_2025": "median_house_price"}).copy()
    name_col = "msoa_name"
    area_word = "neighbourhood"
elif granularity == "City":
    if lad_scope_df.empty:
        area_df = lad_scope_df.copy()
    else:
        agg_spec = {
            "total_listings": "sum",
            "avg_nightly_price": "mean",
            "median_nightly_price": "mean",
            "avg_review_score": "mean",
            "avg_availability_365": "mean",
            "median_house_price": "mean",
            "price_growth_10yr": "mean",
            "median_monthly_rent": "mean",
            "str_annual_revenue_est": "mean",
            "str_gross_yield": "mean",
            "ltr_annual_revenue_est": "mean",
            "ltr_gross_yield": "mean",
            "str_vs_ltr_yield_delta": "mean",
        }
        agg_spec = {k: v for k, v in agg_spec.items() if k in lad_scope_df.columns}
        city_agg = lad_scope_df.groupby("city", as_index=False).agg(agg_spec)
        area_df = add_investment_score(city_agg, PROFILES[selected_profile]["weights"])
        area_df["city"] = area_df["city"].str.title()
    name_col = "city"
    area_word = "city"
else:
    area_df = lad_scope_df
    name_col = "lad_name"
    area_word = "district"

name_col_label = {"msoa_name": "MSOA", "lad_name": "Local Authority District", "city": "City"}[name_col]

if area_df.empty:
    best_area = None
else:
    best_area = area_df.sort_values("investment_score", ascending=False).iloc[0]

# -----------------------------
# MAIN PAGE NAVIGATION BUTTONS
# -----------------------------
nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)

with nav1:
    if st.button("Dashboard", key="score_nav_dashboard", use_container_width=True):
        st.session_state.score_page = "Dashboard"

with nav2:
    if st.button("Map", key="score_nav_map", use_container_width=True):
        st.session_state.score_page = "Map"

with nav3:
    if st.button("Score Breakdown", key="score_nav_breakdown", use_container_width=True):
        st.session_state.score_page = "Score Breakdown"

with nav4:
    if st.button("Compare Areas", key="score_nav_compare", use_container_width=True):
        st.session_state.score_page = "Compare Areas"

with nav5:
    if st.button("Recommendation", key="score_nav_recommendation", use_container_width=True):
        st.session_state.score_page = "Recommendation"

with nav6:
    if st.button("Risks", key="score_nav_risks", use_container_width=True):
        st.session_state.score_page = "Risks"

st.divider()

# -----------------------------
# DASHBOARD PAGE
# -----------------------------
if st.session_state.score_page == "Dashboard":

    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

    with st.container(key="dashboard_border"):
        st.subheader("Investment Dashboard")

        if best_area is None:
            st.warning("No data available.")
        else:
            col1, col2, col3 = st.columns(3, gap="large")

            with col1:
                render_stat_card(
                    "Investment Score", best_area["investment_score"], unit="/ 100", big=True,
                    note=f"A weighted blend of revenue, occupancy, yield, saturation and reviews, tuned to your {profile} profile — see Score Breakdown for the full formula.",
                )

            with col2:
                st.metric(f"Recommended {name_col_label}", best_area[name_col])
                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                st.metric("Short-Term Rental (STR) Yield", f"{best_area['str_gross_yield']:.2%}")

            with col3:
                st.metric("Long-Term Rental (LTR) Yield", f"{best_area['ltr_gross_yield']:.2%}")
                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                st.metric("Estimated STR Revenue", f"£{best_area['str_annual_revenue_est']:,.0f}")

            st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
            col4, col5, col6, col7 = st.columns(4, gap="large")

            with col4:
                st.metric("Median House Price", f"£{best_area['median_house_price']:,.0f}")

            with col5:
                growth = best_area["price_growth_10yr"]
                st.metric("House Price Growth (10yr)", f"{growth:+.1%}" if pd.notna(growth) else "N/A")

            with col6:
                st.metric("Estimated LTR Revenue", f"£{best_area['ltr_annual_revenue_est']:,.0f}")

            with col7:
                st.metric("Market Saturation", f"{best_area['saturation_score']:.0f} / 100")

            st.subheader(f"Top 5 {name_col_label}s" if name_col != "city" else "Top 5 Cities")

            top5 = area_df.sort_values("investment_score", ascending=False).head(5)[
                [name_col, "investment_score", "str_gross_yield", "ltr_gross_yield",
                 "str_annual_revenue_est", "total_listings"]
            ].copy()
            top5["investment_score"] = top5["investment_score"].round(1)
            top5["str_gross_yield"] = (top5["str_gross_yield"] * 100).round(2).astype(str) + "%"
            top5["ltr_gross_yield"] = (top5["ltr_gross_yield"] * 100).round(2).astype(str) + "%"
            top5["str_annual_revenue_est"] = top5["str_annual_revenue_est"].apply(lambda x: f"£{x:,.0f}")
            top5.columns = [name_col_label, "Investment Score", "Short-Term Rental (STR) Yield",
                             "Long-Term Rental (LTR) Yield", "Est. STR Revenue", "Total Listings"]

            render_styled_table(top5, highlight_cols=["Investment Score"])

# -----------------------------
# MAP
# -----------------------------
elif st.session_state.score_page == "Map":

    st.subheader("Investment Score by Area")

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
            city_map_df = map_msoas[map_msoas["city"].str.title() == city_name].copy()
            city_map_df["city"] = city_map_df["city"].str.title()
            city_map_df["Investment Rank"] = city_map_df["investment_score"].rank(
                ascending=False, method="min", na_option="bottom"
            ).astype(int)
            city_map_df["Estimated STR Revenue"] = city_map_df["str_annual_revenue_est"].apply(lambda x: f"£{x:,.0f}")
            city_map_df["Estimated LTR Revenue"] = city_map_df["ltr_annual_revenue_est"].apply(lambda x: f"£{x:,.0f}")
            city_map_df["Average Rating"] = city_map_df["avg_review_score"].round(2)

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

                hover_cols = [
                    "city", "total_listings", "Investment Rank", "investment_score",
                    "Estimated STR Revenue", "Estimated LTR Revenue", "Average Rating",
                ]
                fig = px.choropleth_map(
                    city_map_df,
                    geojson=filtered_geojson,
                    locations="msoa_code",
                    featureidkey="properties.MSOA21CD",
                    color="investment_score",
                    color_continuous_scale=[[0, "#E3EEEC"], [1, TEAL]],
                    hover_name="msoa_name",
                    custom_data=hover_cols,
                    labels={"investment_score": "Investment Score"},
                    map_style="carto-positron",
                    center=center,
                    zoom=9.3,
                    opacity=0.85,
                    height=460,
                )
                fig.update_traces(
                    marker_line_width=1, marker_line_color="#ffffff",
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        "City - %{customdata[0]}<br>"
                        "No. of Airbnb Listings - %{customdata[1]}<br>"
                        "Investment Rank - %{customdata[2]}<br>"
                        "Investment Score - %{customdata[3]:.1f}<br>"
                        "Estimated STR Revenue - %{customdata[4]}<br>"
                        "Estimated LTR Revenue - %{customdata[5]}<br>"
                        "Average Rating - %{customdata[6]}"
                        "<extra></extra>"
                    ),
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    hoverlabel=dict(bgcolor="#ffffff", font_color="#1a1a1a", font_family="Inter", bordercolor=TEAL),
                )
                style_chart(fig)
                fig.update_layout(coloraxis_colorbar=dict(title_font_color="#1a1a1a", tickfont_color="#1a1a1a"))
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})

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
                "LTR Yield Score",
            ],
            "Score": [
                best_area["revenue_score"],
                best_area["occupancy_score"],
                best_area["str_yield_score"],
                best_area["yield_gap_score"],
                best_area["saturation_score"],
                best_area["review_score"],
                best_area["ltr_yield_score"],
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
        # Built as single-line HTML (no embedded newlines/indentation) —
        # pasting an independently-indented multi-line block into the
        # middle of the outer f-string's HTML below confuses Streamlit's
        # Markdown parser and it starts printing tags like </tbody> as
        # literal text instead of rendering them.
        metric_rows = "".join(
            f'<tr><td style="padding:10px 16px;font-weight:600;">{metric}</td>'
            f'<td style="padding:10px 16px;color:{t["text_muted"]};">{desc}</td>'
            f'<td style="padding:10px 16px;text-align:right;font-weight:700;color:{TEAL};">{weights.get(wkey, 0)*100:.0f}%</td></tr>'
            for metric, desc, wkey in [
            ("Revenue", "Estimated annual short-term rental income for the area", "revenue"),
            ("Occupancy", "How booked up the area's listings tend to be", "occupancy"),
            ("STR Yield", "Short-term rental income as a % of property value", "str_yield"),
            ("Yield Gap", "How much better STR yield is than long-term letting", "yield_gap"),
            ("Saturation", "Rewards areas with fewer competing listings", "saturation"),
            ("Reviews", "Average guest review score", "review"),
            ("LTR Yield", "Long-term rental income as a % of property value", "ltr_yield"),
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

    st.subheader(f"Compare {name_col_label}s in {', '.join(cities)}")

    ranked = area_df.sort_values("investment_score", ascending=False)

    cols = [
        name_col,
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
    ranked_display = ranked_display.rename(columns={name_col: name_col_label})
    ranked_display.columns = [
        c if c == name_col_label else
        c.replace("_", " ").title().replace("Str", "STR").replace("Ltr", "LTR").replace("Msoa", "MSOA").replace("Lad", "LAD")
        for c in ranked_display.columns
    ]

    render_styled_table(ranked_display, highlight_cols=["Investment Score"])

    st.subheader("Investment Score Ranking")
    ranking_fig = px.bar(
        ranked, x=name_col, y="investment_score",
        color_discrete_sequence=[TEAL],
        labels={name_col: "", "investment_score": "Investment Score"},
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
        area_name = best_area[name_col]
        # City granularity has no separate "city" field to report — the
        # recommended area IS the city in that case.
        city_for_insight = area_name if name_col == "city" else best_area["city"].title()

        st.success(f"Recommended {name_col_label}: {area_name}")

        # When more than one candidate area is in play, also tell the AI
        # about the lowest-ranked one so the write-up explains why it lost
        # out, not just why the top pick won.
        worst_area_stats = None
        if len(area_df) > 1:
            worst_row = area_df.sort_values("investment_score", ascending=True).iloc[0]
            if worst_row[name_col] != area_name:
                worst_area_stats = {
                    "area_name": worst_row[name_col],
                    "investment_score": worst_row["investment_score"],
                    "str_yield": worst_row["str_gross_yield"],
                    "saturation_score": worst_row["saturation_score"],
                }

        insight = generate_insight(
            area_name=area_name,
            city=city_for_insight,
            budget=budget_max,
            stats={
                "str_yield": best_area["str_gross_yield"],
                "ltr_yield": best_area["ltr_gross_yield"],
                "str_revenue": best_area["str_annual_revenue_est"],
                "saturation_score": best_area["saturation_score"],
                "investment_score": best_area["investment_score"],
            },
            worst_area=worst_area_stats,
        )

        st.markdown(
            f"""
            <div class="card">
            <h3>Why {area_name}?</h3>
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
        area_name = best_area[name_col]

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
            if best_area["total_listings"] > area_df["total_listings"].median():
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
Although **{area_name}** achieved the highest investment score,
investors should consider the following risks:

- Competition from nearby Airbnb properties
- High upfront property costs
- Seasonal changes affecting occupancy
- Changes in short-term rental regulations

Overall, **{area_name}** offers strong investment potential,
but returns depend on maintaining good occupancy and managing costs effectively.
""")

        st.markdown("---")

        # Additional investor information
        st.subheader("Additional Risk Information")
        st.caption(
            "General guidance for UK short-term-let investing — not specific to "
            f"{area_name} or calculated from this app's data."
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

**{area_name}** provides attractive investment potential,
but investors should balance expected returns against:

- Market competition
- Regulatory uncertainty
- Operating costs
- Management requirements

A strong investment decision requires considering both
financial performance and potential risks.
""")

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
