import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import base64
import plotly.express as px

st.set_page_config(
    page_title="InvestStay",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Settings menu (dark mode + currency) ────────────────────────────────────────
with st.container(key="settings_menu"):
    dark_mode = st.toggle("🌙 Dark mode", key="dark_mode", label_visibility="visible")
    st.markdown('<div class="settings-divider"></div>', unsafe_allow_html=True)
    currency = st.radio(
        "Currency", ["£ GBP", "$ USD"], key="currency",
        horizontal=True, label_visibility="collapsed",
    )

GBP_TO_USD = 1.27  # static conversion rate, not live-fetched
CURRENCY_SYMBOL = "£" if currency == "£ GBP" else "$"

def fmt_money(gbp_amount):
    if pd.isna(gbp_amount):
        return "N/A"
    amount = gbp_amount if currency == "£ GBP" else gbp_amount * GBP_TO_USD
    return f"{CURRENCY_SYMBOL}{amount:,.0f}"

if dark_mode:
    THEME = dict(
        bg="#12181b", text="#f2ede4", text_muted="#93a0a3", border="#2a3336",
        card_bg="#1b2226", card_alt_bg="#212a2e", card_alt_hover="#283236",
        table_row_alt="#1f272b",
    )
else:
    THEME = dict(
        bg="#F1F6F5", text="#1a1a1a", text_muted="#888", border="#D7E5E2",
        card_bg="#ffffff", card_alt_bg="#E3EEEC", card_alt_hover="#D8E8E5",
        table_row_alt="#EDF5F3",
    )

theme_vars_css = f""":root {{
    --bg: {THEME['bg']};
    --text: {THEME['text']};
    --text-muted: {THEME['text_muted']};
    --border: {THEME['border']};
    --card-bg: {THEME['card_bg']};
    --card-alt-bg: {THEME['card_alt_bg']};
    --card-alt-hover: {THEME['card_alt_hover']};
    --table-row-alt: {THEME['table_row_alt']};
}}"""

# ── Load logo ─────────────────────────────────────────────────────────────────
def get_logo_b64():
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_investstay_simple_cropped.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_b64()
logo_img     = f'<img src="data:image/png;base64,{logo_b64}" style="height:220px;width:auto;"/>' if logo_b64 else ""
navbar_logo_img = f'<img src="data:image/png;base64,{logo_b64}" style="height:82px;width:auto;display:block;transform:translateY(-6px);"/>' if logo_b64 else ""

# ── Load city photos ──────────────────────────────────────────────────────────
def get_city_img_tag(city_name):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(assets_dir, f"{city_name.lower()}{ext}")
        if os.path.exists(path):
            mime = "jpeg" if ext in (".jpg", ".jpeg") else ext.lstrip(".")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/{mime};base64,{b64}" alt="{city_name}"/>'
    return ""

# ── Load hero carousel images ───────────────────────────────────────────────────
def get_asset_uri(stem):
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(assets_dir, f"{stem}{ext}")
        if os.path.exists(path):
            mime = "jpeg" if ext in (".jpg", ".jpeg") else ext.lstrip(".")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/{mime};base64,{b64}"
    return None

hero_slide_uris = [uri for uri in (get_asset_uri(f"hero_{i}") for i in (1, 2, 3)) if uri]
if not hero_slide_uris:
    fallback = get_asset_uri("hero-bg")
    if fallback:
        hero_slide_uris = [fallback]

HERO_SLIDE_SECONDS = 12  # seconds each image is fully visible before crossfading
hero_cycle_seconds = max(len(hero_slide_uris), 1) * HERO_SLIDE_SECONDS

hero_slides_html = "".join(
    f'''<div class="hero-slide" style="background-image:linear-gradient(180deg, rgba(15,20,25,0.35) 0%, rgba(10,14,18,0.75) 100%), url('{uri}');
        animation-duration:{hero_cycle_seconds}s; animation-delay:{i * HERO_SLIDE_SECONDS}s;"></div>'''
    for i, uri in enumerate(hero_slide_uris)
)
hero_bg_css = "background: var(--bg);" if not hero_slide_uris else ""

CITIES = ["London", "Manchester", "Bristol"]
city_cards = "".join([
    f'''<a class="city-card" href="/Explore_Areas?city={name}" target="_self">
        {get_city_img_tag(name) or '<div class="city-card-placeholder"></div>'}
        <div class="city-card-label">{name}</div>
    </a>'''
    for name in CITIES
])

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "data")
    msoa = pd.read_csv(os.path.join(base, "msoa_investment_summary.csv"))
    lad  = pd.read_csv(os.path.join(base, "lad_investment_summary.csv"))
    try:
        sent = pd.read_csv(os.path.join(base, "msoa_review_sentiment.csv"))
        msoa = msoa.merge(
            sent[["msoa_code","avg_sentiment_score","pct_positive","pct_negative","review_count"]],
            on="msoa_code", how="left"
        )
    except FileNotFoundError:
        pass
    return msoa, lad

msoa_df, lad_df = load_data()

# ── Load LAD boundary map ────────────────────────────────────────────────────
@st.cache_data
def load_lad_geojson():
    path = os.path.join(os.path.dirname(__file__), "data", "lad_boundaries_filtered.geojson")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

lad_geojson = load_lad_geojson()

total_listings = int(msoa_df["total_listings"].sum())
total_msoas    = len(msoa_df)
avg_str_yield  = msoa_df["str_gross_yield"].mean()
top_delta      = msoa_df["str_vs_ltr_yield_delta"].max()
avg_ltr_yield  = msoa_df["ltr_gross_yield"].mean()
cities_covered = msoa_df["city"].nunique()

top10 = (
    msoa_df[msoa_df["str_vs_ltr_yield_delta"].notna()]
    .nlargest(10, "str_vs_ltr_yield_delta")
    [["city","msoa_name","lad_name","median_nightly_price",
      "str_gross_yield","ltr_gross_yield","str_vs_ltr_yield_delta",
      "median_house_price_2025","less_than_15_minute_walk"]]
    .copy()
)
top10["str_gross_yield"]         = (top10["str_gross_yield"]*100).round(2).astype(str)+"%"
top10["ltr_gross_yield"]         = (top10["ltr_gross_yield"]*100).round(2).astype(str)+"%"
top10["str_vs_ltr_yield_delta"]  = (top10["str_vs_ltr_yield_delta"]*100).round(2).astype(str)+"%"
top10["median_house_price_2025"] = top10["median_house_price_2025"].apply(fmt_money)
top10["median_nightly_price"]    = top10["median_nightly_price"].apply(fmt_money)
top10.columns = ["City","MSOA Name","LAD Name","Nightly Price","STR Yield","LTR Yield","Delta","House Price","15-min Rail %"]
top10["City"] = top10["City"].str.title()

city_summary = (
    msoa_df.groupby("city")
    .agg(MSOAs=("msoa_code","count"), Listings=("total_listings","sum"),
         STR=("str_gross_yield","mean"), LTR=("ltr_gross_yield","mean"),
         Delta=("str_vs_ltr_yield_delta","mean"), HP=("median_house_price_2025","mean"))
    .reset_index()
)
city_summary["STR"]      = (city_summary["STR"]*100).round(2).astype(str)+"%"
city_summary["LTR"]      = (city_summary["LTR"]*100).round(2).astype(str)+"%"
city_summary["Delta"]    = (city_summary["Delta"]*100).round(2).astype(str)+"%"
city_summary["HP"]       = city_summary["HP"].apply(fmt_money)
city_summary["Listings"] = city_summary["Listings"].apply(lambda x: f"{x:,}")
city_summary.columns     = ["City","MSOAs","Listings","Avg STR Yield","Avg LTR Yield","Avg Delta","Avg House Price"]
city_summary["City"] = city_summary["City"].str.title()

# ── Styled HTML tables ──────────────────────────────────────────────────────────
def df_to_html_table(df, right_align_from=1, highlight_col=None):
    cols = df.columns.tolist()
    thead_cells = "".join(
        f'<th style="text-align:{"right" if i >= right_align_from else "left"};">{c}</th>'
        for i, c in enumerate(cols)
    )
    body_rows = ""
    for _, row in df.iterrows():
        cells = ""
        for i, c in enumerate(cols):
            align = "right" if i >= right_align_from else "left"
            cls = ' class="delta-cell"' if c == highlight_col else ""
            cells += f'<td style="text-align:{align};"{cls}>{row[c]}</td>'
        body_rows += f"<tr>{cells}</tr>"
    return f'''<div class="table-card"><table class="styled-table">
        <thead><tr>{thead_cells}</tr></thead>
        <tbody>{body_rows}</tbody>
    </table></div>'''

top10_table_html = df_to_html_table(top10, right_align_from=3, highlight_col="Delta")
city_summary_table_html = df_to_html_table(city_summary, right_align_from=1, highlight_col="Avg Delta")

# ── Metrics marquee (duplicated once for a seamless scroll loop) ────────────────
METRICS = [
    (f"{total_listings:,}", "Total Airbnb Listings"),
    (f"{total_msoas:,}", "MSOAs Analysed"),
    (f"{avg_str_yield*100:.1f}%", "Average Short-Term Rental (STR) Gross Yield"),
    (f"+{top_delta*100:.1f}%", "Best STR vs LTR Delta"),
    (f"{avg_ltr_yield*100:.1f}%", "Average Long-Term Rental (LTR) Gross Yield"),
    (f"{cities_covered}", "Cities Covered"),
]
metric_items_html = "".join(
    f'''<div class="metric-item">
        <div class="metric-num">{num}</div>
        <div class="metric-lbl">{lbl}</div>
    </div>'''
    for num, lbl in METRICS
)

# ── Footer constants ──────────────────────────────────────────────────────────
LINKEDIN_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46c.98 0 1.77-.77 1.77-1.72V1.72C24 .77 23.21 0 22.23 0zM7.06 20.45H3.56V9h3.5v11.45zM5.31 7.43c-1.12 0-2.03-.92-2.03-2.05 0-1.13.91-2.05 2.03-2.05 1.12 0 2.03.92 2.03 2.05 0 1.13-.91 2.05-2.03 2.05zM20.45 20.45h-3.5v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.13 1.44-2.13 2.94v5.67h-3.5V9h3.36v1.56h.05c.47-.89 1.62-1.85 3.34-1.85 3.57 0 4.23 2.35 4.23 5.41v6.33z"/></svg>'

TEAM = [
    ("Adam Choy",           "https://www.linkedin.com/in/adam-choy-b95715190/"),
    ("Roisin Houchen",      "https://www.linkedin.com/in/roisin-houchen-aa4175313/"),
    ("Tariq Ali",           "https://www.linkedin.com/in/tariq-ali-10l/"),
    ("Thadsha Sivashanker", "https://www.linkedin.com/in/thadsha-sivashanker-877946243/"),
]

team_links = " &middot; ".join([
    f'<a href="{url}" target="_blank" style="color:var(--text);text-decoration:none;'
    f'display:inline-flex;align-items:center;gap:5px;font-size:0.82rem;">'
    f'{LINKEDIN_ICON} {name}</a>'
    for name, url in TEAM
])

# ── Main HTML block ───────────────────────────────────────────────────────────
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">

<style>
{theme_vars_css}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{ overflow-x: hidden; max-width: 100vw; }}

html, [data-testid="stMain"], [data-testid="stAppViewContainer"] {{ scroll-behavior: smooth; }}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
.block-container {{
    font-family: 'Inter', sans-serif !important;
    -webkit-font-smoothing: antialiased;
    background: var(--bg) !important;
    color: var(--text) !important;
    padding: 0 !important;
    margin-top: 0 !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}}
[data-testid="stMain"] > div:first-child,
[data-testid="stElementContainer"]:first-of-type {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
[data-testid="stVerticalBlock"] {{
    gap: 0 !important;
}}

.st-key-settings_menu {{
    position: fixed;
    top: 46px;
    right: 48px;
    z-index: 1000;
    background: var(--card-bg);
    padding: 14px 18px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.14);
    width: auto !important;
    opacity: 0;
    visibility: hidden;
    transform: translateY(-6px);
    transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
body:has(.settings-btn:hover) .st-key-settings_menu,
.st-key-settings_menu:hover {{
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
    pointer-events: auto;
}}
.st-key-settings_menu label p {{
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem !important;
}}
.st-key-settings_menu [data-testid="stRadio"] > div {{
    gap: 6px;
}}
.settings-divider {{
    height: 1px;
    background: var(--border);
    margin: 2px 0 6px;
}}
.st-key-settings_menu [data-testid="stToggle"] [role="switch"][aria-checked="true"],
.st-key-settings_menu [data-testid="stToggle"] div[data-baseweb="toggle"][aria-checked="true"] {{
    background-color: #0D9488 !important;
    border-color: #0D9488 !important;
}}

#MainMenu, footer, header,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"] {{
    display: none !important;
}}

/* ── Section side rail ── */
.side-rail {{
    position: fixed;
    left: 8px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 999;
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transition: opacity 0.25s ease, visibility 0.25s ease;
}}
.side-rail.is-visible {{
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
}}
.side-rail a {{
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: var(--card-alt-bg);
    color: var(--text);
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    transition: transform 0.15s ease, background 0.15s ease, color 0.15s ease;
}}
.side-rail a svg {{ width: 20px; height: 20px; }}
.side-rail a:hover {{ transform: scale(1.08); background: var(--card-alt-hover); }}
body:has(#section-home:target) .side-rail a[href="#section-home"],
body:has(#section-metrics:target) .side-rail a[href="#section-metrics"],
body:has(#section-cities:target) .side-rail a[href="#section-cities"],
body:has(#section-tables:target) .side-rail a[href="#section-tables"],
body:has(#section-footer:target) .side-rail a[href="#section-footer"] {{
    background: var(--text);
    color: var(--bg);
}}
.side-rail a[href="#section-home"] {{ background: var(--text); color: var(--bg); }}
body:has(#section-metrics:target) .side-rail a[href="#section-home"],
body:has(#section-cities:target) .side-rail a[href="#section-home"],
body:has(#section-tables:target) .side-rail a[href="#section-home"],
body:has(#section-footer:target) .side-rail a[href="#section-home"] {{
    background: var(--card-alt-bg);
    color: var(--text);
}}

/* ── Navbar ── */
.navbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 48px;
    background: var(--bg);
    position: sticky;
    top: 0;
    z-index: 1101;
}}
.navbar-divider {{
    height: 1.5px;
    margin: 0 32px;
    background: var(--text-muted);
    opacity: 0.4;
    position: sticky;
    top: 66px;
    z-index: 1100;
}}
.navbar-left {{
    display: flex;
    align-items: center;
    height: 58px;
    gap: 28px;
}}
.navbar-logo-link {{
    display: inline-flex;
    margin-top: auto;
    margin-bottom: auto;
    transition: opacity 0.2s ease, transform 0.2s ease;
}}
.navbar-logo-link:hover {{
    opacity: 0.75;
    transform: scale(1.04);
}}
.nav-links {{
    display: flex;
    align-items: center;
    margin-top: auto;
    margin-bottom: auto;
    gap: 22px;
    list-style: none;
    transform: translateX(-10px);
}}
.nav-links li {{
    display: flex;
    align-items: center;
}}
.nav-links a {{
    color: var(--text);
    text-decoration: none;
    font-size: 1.15rem;
    font-weight: 500;
    line-height: 1;
    transition: opacity 0.2s;
}}
.nav-links a:hover {{ opacity: 0.6; }}
.navbar-right {{
    display: flex;
    align-items: center;
    height: 58px;
    gap: 14px;
}}
.settings-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    margin-top: auto;
    margin-bottom: auto;
    border-radius: 50%;
    color: var(--text);
    background: var(--card-alt-bg);
    transition: transform 0.15s ease, background 0.15s ease;
}}
.settings-btn svg {{ width: 18px; height: 18px; }}
.settings-btn:hover {{ transform: rotate(45deg); background: var(--card-alt-hover); }}

/* ── Investor setup ── */
.st-key-investor_setup {{
    margin: 8px 32px 32px;
    padding: 28px 48px 32px;
    background: var(--card-bg);
    border-radius: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
.investor-setup-title {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #0D9488;
    margin-bottom: 18px;
}}
.st-key-investor_setup label p {{
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
}}

/* ── Hero card ── */
.hero-card {{
    margin: 0;
    {hero_bg_css}
    border-radius: 0;
    overflow: hidden;
    position: relative;
    min-height: 564px;
    display: flex;
    align-items: flex-end;
}}
.hero-slide {{
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    opacity: 0;
    animation-name: heroFade;
    animation-timing-function: ease-in-out;
    animation-iteration-count: infinite;
    z-index: 0;
}}
@keyframes heroFade {{
    0%      {{ opacity: 0; }}
    6.2%    {{ opacity: 1; }}
    26.8%   {{ opacity: 1; }}
    33%     {{ opacity: 0; }}
    100%    {{ opacity: 0; }}
}}
@media (prefers-reduced-motion: reduce) {{
    .hero-slide {{ animation: none; opacity: 1; }}
}}
.hero-inner {{
    padding: 40px 48px 32px 72px;
    position: relative;
    z-index: 2;
}}
.hero-logo-mark {{
    font-size: 2rem;
    font-weight: 900;
    color: #1a1a1a;
    margin-bottom: 48px;
    letter-spacing: -0.05em;
}}
.hero-heading {{
    font-size: clamp(3.8rem, 7.8vw, 6.6rem);
    font-weight: 800;
    line-height: 1.0;
    letter-spacing: -0.04em;
    color: #ffffff !important;
    margin-bottom: 0;
}}
.hero-subheading {{
    font-size: 1.45rem;
    font-weight: 400;
    color: #ffffff !important;
    opacity: 0.85;
    margin-top: 16px;
}}

/* ── Gradient stripes ── */
.stripes {{
    display: flex;
    flex-direction: column;
    width: 100%;
    flex-shrink: 0;
    margin-top: 0;
}}
.stripe {{ height: 18px; width: 100%; }}
.s0 {{ background: #0A2740; }}
.s1 {{ background: #1B4F72; }}
.s2 {{ background: #1A6B8A; }}
.s3 {{ background: #0D9488; }}
.s4 {{ background: #10c87a; }}
.s5 {{ background: #12db6b; }}

/* ── Metrics ── */
.metrics-section {{
    padding: 24px 48px 48px;
    margin: 0 32px;
}}
.metrics-heading {{
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    margin-bottom: 32px;
}}
.metrics-marquee {{
    overflow: hidden;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 64px, #000 calc(100% - 64px), transparent 100%);
    mask-image: linear-gradient(90deg, transparent 0, #000 64px, #000 calc(100% - 64px), transparent 100%);
}}
.metrics-track {{
    display: flex;
    width: max-content;
    animation: metricsScroll 55s linear infinite;
}}
.metrics-marquee:hover .metrics-track {{
    animation-play-state: paused;
}}
@keyframes metricsScroll {{
    from {{ transform: translateX(0); }}
    to   {{ transform: translateX(-50%); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .metrics-track {{ animation: none; }}
}}
.metric-item {{
    flex: 0 0 auto;
    width: 280px;
    padding: 28px 32px;
    border-right: 1px solid var(--border);
}}
.metric-num {{
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: var(--text);
    line-height: 1;
}}
.metric-lbl {{
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* ── City cards ── */
.cities-section {{
    padding: 0 48px 48px;
    margin: 0 32px;
}}
.cities-grid {{
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 24px;
}}
.city-card {{
    position: relative;
    display: block;
    height: 260px;
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

/* ── Content section ── */
.content-section {{
    padding: 0 48px 24px;
    margin: 0 32px;
}}
.section-title {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #0D9488;
    margin-bottom: 16px;
    padding-top: 40px;
    border-top: 1px solid var(--border);
}}

/* ── Styled tables ── */
.table-card {{
    background: var(--card-bg);
    border-radius: 16px;
    overflow-x: auto;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 8px;
}}
[data-testid="stPlotlyChart"] {{
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}}
.styled-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    white-space: nowrap;
}}
.styled-table thead th {{
    background: #0D9488;
    color: #fff;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 14px 20px;
}}
.styled-table tbody td {{
    padding: 12px 20px;
    color: var(--text);
    border-bottom: 1px solid var(--border);
}}
.styled-table tbody tr:nth-child(even) {{ background: var(--table-row-alt); }}
.styled-table tbody tr:hover {{ background: var(--card-alt-bg); }}
.styled-table tbody tr:last-child td {{ border-bottom: none; }}
.styled-table td.delta-cell {{
    color: #0D9488;
    font-weight: 700;
}}

/* ── Footer grid ── */
.footer-grid {{
    background: var(--bg);
    padding: 56px 80px 40px;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 40px;
    margin-top: 0;
}}
.footer-col-title {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #0D9488;
    margin-bottom: 16px;
}}
.footer-links {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.footer-links a {{
    color: var(--text-muted);
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 400;
    transition: color 0.2s;
}}
.footer-links a:hover {{ color: #0D9488; }}

/* ── Footer stripe band ── */
.footer-stripes {{
    display: flex;
    flex-direction: column;
    width: 100%;
}}
.fs {{ height: 18px; width: 100%; }}
.fs0 {{ background: #0A2740; }}
.fs1 {{ background: #1B4F72; }}
.fs2 {{ background: #1A6B8A; }}
.fs3 {{ background: #0D9488; }}
.fs4 {{ background: #10c87a; }}
.fs5 {{ background: #12db6b; }}

/* ── Footer bottom bar ── */
.footer-bar {{
    background: var(--bg);
    padding: 32px 80px;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 20px;
    border-top: 1px solid var(--border);
    font-family: 'Inter', sans-serif;
}}

</style>

<div id="section-home"></div>

<!-- ═══ SECTION SIDE RAIL ═══ -->
<div class="side-rail">
    <a href="#section-home" target="_self" title="Home">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9"/></svg>
    </a>
    <a href="#section-metrics" target="_self" title="Pipeline metrics">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10"/><path d="M12 20V4"/><path d="M20 20v-7"/></svg>
    </a>
    <a href="#section-cities" target="_self" title="Explore by city">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.1 7-11.5A7 7 0 0 0 5 9.5C5 14.9 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.3"/></svg>
    </a>
    <a href="#section-tables" target="_self" title="Investment tables">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M9 10v10"/></svg>
    </a>
    <a href="#section-footer" target="_self" title="Footer & sources">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 16v-5"/><path d="M12 8h.01"/></svg>
    </a>
</div>

<!-- ═══ NAVBAR ═══ -->
<div class="navbar">
    <div class="navbar-left">
        <a href="/" target="_self" class="navbar-logo-link">{navbar_logo_img if navbar_logo_img else '<span style="font-size:1.4rem;font-weight:900;letter-spacing:-0.05em;">IS</span>'}</a>
        <ul class="nav-links">
            <li><a href="/Explore_Areas" target="_self">Explore</a></li>
            <li><a href="/Yield_Analysis" target="_self">Yields</a></li>
            <li><a href="/Sentiment" target="_self">Sentiment</a></li>
            <li><a href="/Investment_Score" target="_self">Score</a></li>
            <li><a href="/Data_Dictionary" target="_self">Data</a></li>
            <li><a href="/How_It_Works" target="_self">How It Works</a></li>
            <li><a href="#section-footer" target="_self">About Us</a></li>
        </ul>
    </div>
    <div class="navbar-right">
        <a href="/Investment_Score" target="_self" style="background:var(--text);color:var(--bg);padding:10px 24px;
            border-radius:8px;font-size:0.875rem;font-weight:500;text-decoration:none;line-height:1.2;
            display:inline-flex;align-items:center;margin-top:auto;margin-bottom:auto;font-family:'Inter',sans-serif;">Analyse Investment</a>
        <a href="#" onclick="return false;" class="settings-btn" title="Settings" aria-label="Settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
        </a>
    </div>
</div>
<div class="navbar-divider"></div>

<!-- ═══ HERO CARD ═══ -->
<div class="hero-card" id="hero-visual">
    {hero_slides_html}
    <div class="hero-inner">
        <h1 class="hero-heading">
            Find your perfect property to invest in.
        </h1>
        <p class="hero-subheading">From raw data to real returns. Built on open data. Designed for smarter property investment.</p>
    </div>
</div>
<div class="stripes">
    <div class="stripe s0"></div>
    <div class="stripe s1"></div>
    <div class="stripe s2"></div>
    <div class="stripe s3"></div>
    <div class="stripe s4"></div>
    <div class="stripe s5"></div>
</div>

<!-- ═══ METRICS ═══ -->
<div class="metrics-section" id="section-metrics">
    <div class="metrics-marquee">
        <div class="metrics-track">
            {metric_items_html}
            {metric_items_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

components.html("""
<script>
(function() {
    var doc = window.parent.document;
    function tryBind(attemptsLeft) {
        var footer = doc.getElementById('section-footer');
        var rail = doc.querySelector('.side-rail');
        if (!footer || !rail) {
            if (attemptsLeft > 0) setTimeout(function(){ tryBind(attemptsLeft - 1); }, 300);
            return;
        }
        function update() {
            var top = footer.getBoundingClientRect().top;
            var winHeight = doc.defaultView.innerHeight;
            rail.classList.toggle('is-visible', top <= winHeight);
        }
        var scrollHost = doc.querySelector('[data-testid="stMain"]') || doc.querySelector('[data-testid="stAppViewContainer"]') || doc;
        scrollHost.addEventListener('scroll', update, { passive: true });
        doc.defaultView.addEventListener('scroll', update, { passive: true });
        setInterval(update, 200);
        update();
    }
    tryBind(20);
})();
</script>
""", height=0)

# ── Investor Setup ──────────────────────────────────────────────────────────────
with st.container(key="investor_setup"):
    st.markdown('<div class="investor-setup-title">Investor Setup</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        city_options = sorted(msoa_df["city"].dropna().str.title().unique())
        if st.session_state.get("global_city") not in city_options:
            st.session_state["global_city"] = city_options[0]
        investor_city = st.selectbox("City", city_options, key="global_city")
    with c2:
        investor_budget = st.slider(
            f"Investment Budget ({CURRENCY_SYMBOL})", 50000, 1000000, 250000, step=10000,
            format=f"{CURRENCY_SYMBOL}%d", key="global_budget",
        )
    with c3:
        investor_profile = st.selectbox(
            "Investor Profile",
            ["First-time investor", "Multi-property host"],
            key="global_profile",
        )
st.session_state["global_city_filter"] = investor_city
st.markdown(f"""
<!-- ═══ CITY CARDS ═══ -->
<div class="cities-section" id="section-cities">
    <div class="metrics-heading">Explore by city</div>
    <div class="cities-grid">
        {city_cards}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Coverage map ─────────────────────────────────────────────────────────────
if lad_geojson:
    map_df = lad_df[lad_df["city"].isin(["london", "bristol", "manchester"])].copy()
    map_df["City"] = map_df["city"].str.title()
    map_df["STR Gross Yield (%)"] = (map_df["str_gross_yield"] * 100).round(2)

    st.markdown("""
    <div class="content-section" style="padding-bottom:0;">
        <div class="section-title" style="border-top:none;padding-top:0;">Three Cities — London, Manchester and Bristol</div>
    </div>
    """, unsafe_allow_html=True)

    map_fig = px.choropleth_map(
        map_df,
        geojson=lad_geojson,
        locations="lad_code",
        featureidkey="properties.lad_code",
        color="STR Gross Yield (%)",
        color_continuous_scale=[[0, "#E3EEEC"], [1, "#0D9488"]],
        hover_name="lad_name",
        hover_data={"City": True, "lad_code": False, "STR Gross Yield (%)": True},
        map_style="carto-positron",
        zoom=5.4,
        center={"lat": 53.4, "lon": -1.9},
        opacity=0.85,
        height=520,
    )
    map_fig.update_traces(marker_line_width=1, marker_line_color="#ffffff")
    map_fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
    )
    st.markdown('<div class="content-section" style="padding-top:0;">', unsafe_allow_html=True)
    map_col_l, map_col_mid, map_col_r = st.columns([1, 3, 1])
    with map_col_mid:
        st.plotly_chart(map_fig, use_container_width=True, config={"scrollZoom": False})
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<!-- ═══ TABLES ═══ -->
<div class="content-section" id="section-tables">
    <div class="section-title">Top Investment Opportunities — STR vs LTR Yield Delta</div>
    {top10_table_html}
</div>

<div class="content-section">
    <div class="section-title">City Summary</div>
    {city_summary_table_html}
</div>
""", unsafe_allow_html=True)


# ── Combined footer ───────────────────────────────────────────────────────────
st.markdown(f"""

<!-- Stripe band -->
<div class="footer-stripes" id="section-footer">
    <div class="fs fs0"></div>
    <div class="fs fs1"></div>
    <div class="fs fs2"></div>
    <div class="fs fs3"></div>
    <div class="fs fs4"></div>
    <div class="fs fs5"></div>
</div>

<!-- Footer grid (links) -->
<div class="footer-grid">
    <div>
        <div class="footer-col-title">Explore</div>
        <ul class="footer-links">
            <li><a href="#section-tables" target="_self">Top Opportunities</a></li>
            <li><a href="/Explore_Areas" target="_self">City Explorer</a></li>
            <li><a href="/Explore_Areas" target="_self">MSOA Search</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">Analysis</div>
        <ul class="footer-links">
            <li><a href="/Yield_Analysis" target="_self">STR Yields</a></li>
            <li><a href="/Yield_Analysis" target="_self">LTR Yields</a></li>
            <li><a href="/Yield_Analysis" target="_self">Yield Delta</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">Insights</div>
        <ul class="footer-links">
            <li><a href="/Sentiment" target="_self">Sentiment</a></li>
            <li><a href="/Yield_Analysis" target="_self">House Prices</a></li>
            <li><a href="/Explore_Areas" target="_self">Rail Access</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">Data</div>
        <ul class="footer-links">
            <li><a href="/Data_Dictionary" target="_self">Data Dictionary</a></li>
            <li><a href="/Data_Dictionary" target="_self">Pipeline Docs</a></li>
            <li><a href="/Data_Dictionary" target="_self">Assumptions</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">About</div>
        <ul class="footer-links">
            <li><a href="/Data_Dictionary" target="_self">Methodology</a></li>
            <li><a href="https://github.com/AdamChoy/Airbnb-Investment-App" target="_blank">GitHub</a></li>
        </ul>
    </div>
</div>

<!-- Footer bottom bar: copyright + LinkedIn + data sources -->
<div class="footer-bar">
    <div style="line-height:1.6;">
        <div style="font-size:0.85rem;color:var(--text);font-weight:500;">
            InvestStay &copy; 2026
        </div>
        <div style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">
            Built at Rockborne &middot; Databricks Unity Catalog
        </div>
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:8px;">
            <span style="font-size:0.75rem;color:var(--text-muted);">Built by</span>
            {team_links}
        </div>
    </div>
    <div style="display:flex;align-items:center;justify-content:center;">
        {logo_img}
    </div>
    <div style="font-size:0.78rem;color:var(--text-muted);text-align:right;line-height:1.8;justify-self:end;">
        Inside Airbnb &middot; Land Registry &middot; ONS<br>
        NHS Digital &middot; OS OpenData &middot; Databricks
    </div>
</div>
""", unsafe_allow_html=True)
