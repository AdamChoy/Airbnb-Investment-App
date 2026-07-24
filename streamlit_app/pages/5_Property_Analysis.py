import base64
import os
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from theme import TEAL, get_theme, inject_css, render_navbar
from scoring import PROFILES, DEFAULT_PROFILE, add_investment_score

st.set_page_config(page_title="Search Properties · InvestStay", layout="wide", initial_sidebar_state="collapsed")

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
# SCORING (shared with Home.py's coverage map and the results page — see
# scoring.py — so the same LAD never shows two different "Investment Score"
# numbers)
# -----------------------------
selected_profile = st.session_state.get("global_profile_key")
if selected_profile not in PROFILES:
    selected_profile = DEFAULT_PROFILE

st.session_state["global_profile_key"] = selected_profile
profile = PROFILES[selected_profile]["label"]

lad_df = add_investment_score(lad_df, PROFILES[selected_profile]["weights"])
msoa_df = add_investment_score(msoa_df, PROFILES[selected_profile]["weights"])

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
    is_selected = name in selected_cities
    shadow = (
        f"0 0 0 4px {TEAL}, 0 0 0 8px rgba(13,148,136,0.25), 0 10px 24px rgba(0,0,0,0.25)"
        if is_selected else "0 2px 12px rgba(0,0,0,0.08)"
    )
    filter_css = "none" if is_selected else "brightness(0.6) saturate(0.7)"
    badge_css = f"""
    .st-key-city_{name} button::after {{
        content: "✓ Selected";
        position: absolute; top: 12px; right: 12px;
        background: {TEAL}; color: #fff; font-size: 0.7rem; font-weight: 700;
        padding: 4px 10px; border-radius: 999px; letter-spacing: 0.02em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }}
    """ if is_selected else ""
    city_button_css += f"""
    .st-key-city_{name} button {{
        position: relative !important;
        height: 220px !important; width: 100% !important; border: none !important;
        border-radius: 16px !important;
        background-image: linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.65) 100%), {bg_img} !important;
        background-size: cover !important; background-position: center !important;
        background-color: {bg_fallback} !important;
        display: flex !important; align-items: flex-end !important; justify-content: flex-start !important;
        padding: 16px 20px !important; color: #fff !important; font-size: 1.3rem !important;
        font-weight: 700 !important; letter-spacing: -0.02em !important; text-align: left !important;
        box-shadow: {shadow} !important;
        filter: {filter_css};
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }}
    .st-key-city_{name} button:hover {{
        transform: translateY(-4px);
        filter: none;
        box-shadow: 0 0 0 2px rgba(255,255,255,0.85), 0 0 28px 4px rgba(255,255,255,0.6), 0 10px 24px rgba(0,0,0,0.2) !important;
    }}
    {badge_css}
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
.step-label {{
    font-size: 0.8rem;
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
.profile-card-persona {{
    font-size: 0.85rem;
    line-height: 1.5;
    color: {TEAL};
    font-weight: 600;
    margin-top: 8px;
}}
{city_button_css}
{profile_button_css}
.st-key-lads_select_all button {{
    background: transparent !important; color: {TEAL} !important; border: none !important;
    box-shadow: none !important; padding: 0 !important; height: auto !important;
    font-size: 0.78rem !important; font-weight: 600 !important; text-decoration: underline !important;
}}
.st-key-lads_select_all button:hover {{
    color: #0b7d73 !important; background: transparent !important;
}}
.st-key-analyse_investment button {{
    background-color: {TEAL} !important; color: white !important; border: none !important;
    border-radius: 12px !important; padding: 0.85rem 1.4rem !important;
    font-weight: 700 !important; font-size: 1rem !important;
}}
.st-key-analyse_investment button:hover {{
    background-color: #0b7d73 !important; color: white !important;
}}
.st-key-global_granularity [role="radiogroup"] label p {{
    color: #000 !important;
}}
""")
render_navbar(active="Invest")

# -----------------------------
# SEARCH INPUTS (persist across pages via shared session_state keys)
# -----------------------------
with st.container():
    st.markdown(
        '<div class="main-title" style="margin-bottom:20px;">Find Your Perfect <span class="teal">Property</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{t['text_muted']};margin-bottom:24px;'>"
        f"Narrow down by area, budget and amenities to find the investment that fits your strategy.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='step-label'>1. Select your cities</div>", unsafe_allow_html=True)

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

    label_col, sel_col = st.columns([9, 1.3])
    with label_col:
        st.markdown("<div class='step-label'>2. Pick your Local Authority Districts (LAD)</div>", unsafe_allow_html=True)
    with sel_col:
        if st.button("Select all", key="lads_select_all", use_container_width=True):
            st.session_state["global_lads"] = lad_options
            st.rerun()

    lads = st.multiselect(
        "Local Authority Districts",
        options=lad_options,
        key="global_lads",
        label_visibility="collapsed",
    )
    # Widget-owned session_state keys (like global_lads above) get purged by
    # Streamlit once their widget stops being instantiated — which happens
    # the moment we're no longer on this page. The results page can't read
    # global_lads directly, so mirror it into a plain, non-widget-owned key
    # that survives the navigation. Same story for every widget below.
    st.session_state["persist_lads"] = lads

    st.markdown("<div class='step-label'>3. Choose your investment budget (£)</div>", unsafe_allow_html=True)
    budget_min, budget_max = st.slider(
        "Choose your investment budget (£)", 50000, 1000000, value=(50000, 300000), step=10000,
        key="global_budget_range", label_visibility="collapsed",
    )
    st.session_state["persist_budget_range"] = (budget_min, budget_max)

    st.markdown("<div class='step-label'>4. Decide Transport &amp; local amenities</div>", unsafe_allow_html=True)
    amen_col1, amen_col2, amen_col3 = st.columns(3)
    with amen_col1:
        transport_access = st.selectbox(
            "Transport access",
            ["Any", "Within 15-min walk", "Within 30-min walk"],
            key="global_transport",
        )
        st.session_state["persist_transport"] = transport_access
    with amen_col2:
        min_gp = st.slider(
            "Minimum GP surgeries nearby",
            0, int(msoa_df["gp_surgery_count"].max()), 0,
            key="global_min_gp",
        )
        st.session_state["persist_min_gp"] = min_gp
    with amen_col3:
        min_parks = st.slider(
            "Minimum parks nearby",
            0, int(msoa_df["total_parks_count"].max()), 0,
            key="global_min_parks",
        )
        st.session_state["persist_min_parks"] = min_parks

    st.markdown("<div class='step-label'>5. Determine Investor profile</div>", unsafe_allow_html=True)

    profile_cols = st.columns(len(PROFILES))
    for col, (key, data) in zip(profile_cols, PROFILES.items()):
        with col:
            if st.button(data["label"], key=f"profile_{key}", use_container_width=True):
                st.session_state["global_profile_key"] = key
                st.rerun()
            st.markdown(f"<div class='profile-card-desc'>{data['sentence']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='profile-card-persona'>{data['persona']}</div>", unsafe_allow_html=True)

    st.markdown("<div class='step-label'>6. Recommendation granularity</div>", unsafe_allow_html=True)
    granularity = st.radio(
        "Recommendation granularity",
        ["City", "Local Authority District (LAD)", "Neighbourhood (MSOA)"],
        index=1, key="global_granularity", horizontal=True, label_visibility="collapsed",
    )
    st.session_state["persist_granularity"] = granularity

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if not lads:
        st.warning("Pick at least one Local Authority District to continue.")
    if st.button("Analyse Investment →", key="analyse_investment", disabled=not lads):
        st.switch_page("pages/9_Investment_Results.py")

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
