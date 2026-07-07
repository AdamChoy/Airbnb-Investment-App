import streamlit as st
import pandas as pd
import os
import base64

st.set_page_config(
    page_title="InvestStay",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme toggle ───────────────────────────────────────────────────────────────
dark_mode = st.toggle("🌙 Dark mode", key="dark_mode", label_visibility="visible")

if dark_mode:
    THEME = dict(
        bg="#12181b", text="#f2ede4", text_muted="#93a0a3", border="#2a3336",
        card_bg="#1b2226", card_alt_bg="#212a2e", card_alt_hover="#283236",
        table_row_alt="#1f272b",
    )
else:
    THEME = dict(
        bg="#f5f0e8", text="#1a1a1a", text_muted="#888", border="#d4cfc5",
        card_bg="#ffffff", card_alt_bg="#eee8d8", card_alt_hover="#e3ddc9",
        table_row_alt="#f9f6ef",
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
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo investstay.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_b64()
logo_img     = f'<img src="data:image/png;base64,{logo_b64}" style="height:110px;width:auto;"/>' if logo_b64 else ""
navbar_logo_img = f'<img src="data:image/png;base64,{logo_b64}" style="height:96px;width:auto;"/>' if logo_b64 else ""

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

# ── Load hero background ──────────────────────────────────────────────────────
def get_hero_bg_b64():
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(assets_dir, f"hero-bg{ext}")
        if os.path.exists(path):
            mime = "jpeg" if ext in (".jpg", ".jpeg") else ext.lstrip(".")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/{mime};base64,{b64}"
    return None

hero_bg_uri = get_hero_bg_b64()
hero_bg_css = (
    f"background-image: linear-gradient(180deg, rgba(15,20,25,0.35) 0%, rgba(10,14,18,0.75) 100%), url('{hero_bg_uri}');"
    "background-size: cover; background-position: center;"
    if hero_bg_uri else "background: var(--bg);"
)

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

total_listings = int(msoa_df["total_listings"].sum())
total_msoas    = len(msoa_df)
avg_str_yield  = msoa_df["str_gross_yield"].mean()
top_delta      = msoa_df["str_vs_ltr_yield_delta"].max()

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
top10["median_house_price_2025"] = top10["median_house_price_2025"].apply(lambda x: f"£{x:,.0f}" if pd.notna(x) else "N/A")
top10["median_nightly_price"]    = top10["median_nightly_price"].apply(lambda x: f"£{x:.0f}")
top10.columns = ["City","MSOA","LAD","Nightly Price","STR Yield","LTR Yield","Delta","House Price","15-min Rail %"]
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
city_summary["HP"]       = city_summary["HP"].apply(lambda x: f"£{x:,.0f}")
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

# ── Footer constants ──────────────────────────────────────────────────────────
LINKEDIN_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46c.98 0 1.77-.77 1.77-1.72V1.72C24 .77 23.21 0 22.23 0zM7.06 20.45H3.56V9h3.5v11.45zM5.31 7.43c-1.12 0-2.03-.92-2.03-2.05 0-1.13.91-2.05 2.03-2.05 1.12 0 2.03.92 2.03 2.05 0 1.13-.91 2.05-2.03 2.05zM20.45 20.45h-3.5v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.13 1.44-2.13 2.94v5.67h-3.5V9h3.36v1.56h.05c.47-.89 1.62-1.85 3.34-1.85 3.57 0 4.23 2.35 4.23 5.41v6.33z"/></svg>'

TEAM = [
    ("Adam Choy",           "https://www.linkedin.com/in/adam-choy-b95715190/"),
    ("Roisin Houchen",      "https://www.linkedin.com/in/roisin-houchen/"),
    ("Tariq Ali",           "https://www.linkedin.com/in/tariq-ali/"),
    ("Thadsha Sivashanker", "https://www.linkedin.com/in/thadsha-sivashanker/"),
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

html, [data-testid="stMain"], [data-testid="stAppViewContainer"] {{ scroll-behavior: smooth; }}

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.block-container {{
    font-family: 'Inter', sans-serif !important;
    -webkit-font-smoothing: antialiased;
    background: var(--bg) !important;
    color: var(--text) !important;
    padding: 0 !important;
    max-width: 100% !important;
}}

[data-testid="stElementContainer"]:has([data-testid="stCheckbox"]) {{
    position: fixed;
    top: 14px;
    right: 48px;
    z-index: 1000;
    background: var(--card-alt-bg);
    padding: 4px 14px;
    border-radius: 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    width: auto !important;
}}
[data-testid="stElementContainer"]:has([data-testid="stCheckbox"]) label p {{
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem !important;
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
    left: 24px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 999;
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
    padding: 8px 48px;
    background: var(--bg);
}}
.navbar-left {{
    display: flex;
    align-items: center;
    gap: 48px;
}}
.navbar-logo-link {{
    display: inline-flex;
    transition: opacity 0.2s ease, transform 0.2s ease;
}}
.navbar-logo-link:hover {{
    opacity: 0.75;
    transform: scale(1.04);
}}
.nav-links {{
    display: flex;
    gap: 36px;
    list-style: none;
}}
.nav-links a {{
    color: var(--text);
    text-decoration: none;
    font-size: 1.15rem;
    font-weight: 500;
    transition: opacity 0.2s;
}}
.nav-links a:hover {{ opacity: 0.6; }}

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
    margin: 0 32px;
    {hero_bg_css}
    border-radius: 20px;
    overflow: hidden;
    position: relative;
    min-height: 460px;
    display: flex;
    align-items: flex-end;
}}
.hero-inner {{
    padding: 40px 48px 32px;
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
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 800;
    line-height: 1.0;
    letter-spacing: -0.04em;
    color: #ffffff !important;
    margin-bottom: 0;
}}
.hero-subheading {{
    font-size: 1.05rem;
    font-weight: 400;
    color: #ffffff !important;
    opacity: 0.65;
    margin-top: 16px;
}}

/* ── Gradient stripes ── */
.stripes {{
    display: flex;
    flex-direction: column;
    width: 100%;
    flex-shrink: 0;
    margin-top: 32px;
}}
.stripe {{ height: 18px; width: 100%; }}
.s1 {{ background: #1B4F72; }}
.s2 {{ background: #1A6B8A; }}
.s3 {{ background: #0D9488; }}
.s4 {{ background: #10c87a; }}
.s5 {{ background: #12db6b; }}

/* ── Metrics ── */
.metrics-section {{
    padding: 64px 48px 48px;
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
.metrics-grid {{
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 0;
    border-top: 1px solid var(--border);
}}
.metric-item {{
    padding: 28px 0;
    border-right: 1px solid var(--border);
}}
.metric-item:last-child {{ border-right: none; }}
.metric-item:not(:first-child) {{ padding-left: 28px; }}
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
        </ul>
    </div>
    <a href="#" style="background:var(--text);color:var(--bg);padding:10px 24px;
        border-radius:8px;font-size:0.875rem;font-weight:500;text-decoration:none;
        font-family:'Inter',sans-serif;">Get Started</a>
</div>

<!-- ═══ HERO CARD ═══ -->
<div class="hero-card" id="section-home">
    <div class="hero-inner">
        <h1 class="hero-heading">
            From raw data to real returns.
        </h1>
        <p class="hero-subheading">Built on open data. Designed for smarter property investment.</p>
    </div>
</div>
<div class="stripes">
    <div class="stripe s1"></div>
    <div class="stripe s2"></div>
    <div class="stripe s3"></div>
    <div class="stripe s4"></div>
    <div class="stripe s5"></div>
</div>

<!-- ═══ METRICS ═══ -->
<div class="metrics-section" id="section-metrics">
    <div class="metrics-grid">
        <div class="metric-item">
            <div class="metric-num">{total_listings:,}</div>
            <div class="metric-lbl">Total Listings</div>
        </div>
        <div class="metric-item">
            <div class="metric-num">{total_msoas:,}</div>
            <div class="metric-lbl">MSOAs Analysed</div>
        </div>
        <div class="metric-item">
            <div class="metric-num">{avg_str_yield*100:.1f}%</div>
            <div class="metric-lbl">Average Short-Term Rental (STR) Gross Yield</div>
        </div>
        <div class="metric-item">
            <div class="metric-num">+{top_delta*100:.1f}%</div>
            <div class="metric-lbl">Best STR vs LTR Delta</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Investor Setup ──────────────────────────────────────────────────────────────
with st.container(key="investor_setup"):
    st.markdown('<div class="investor-setup-title">Investor Setup</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        investor_city = st.selectbox(
            "City",
            sorted(msoa_df["city"].dropna().str.title().unique()),
            key="investor_city",
        )
    with c2:
        investor_budget = st.slider(
            "Investment Budget (£)", 50000, 1000000, 250000, step=10000,
            format="£%d", key="investor_budget",
        )
    with c3:
        investor_profile = st.selectbox(
            "Investor Profile",
            ["First-time investor", "Multi-property host"],
            key="investor_profile",
        )
    with c4:
        investor_bedrooms = st.selectbox(
            "Bedrooms", [1, 2, 3, 4, 5], key="investor_bedrooms",
        )

st.markdown(f"""
<!-- ═══ CITY CARDS ═══ -->
<div class="cities-section" id="section-cities">
    <div class="metrics-heading">Explore by city</div>
    <div class="cities-grid">
        {city_cards}
    </div>
</div>

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
            <li><a href="#">Top Opportunities</a></li>
            <li><a href="#">City Explorer</a></li>
            <li><a href="#">MSOA Search</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">Analysis</div>
        <ul class="footer-links">
            <li><a href="#">STR Yields</a></li>
            <li><a href="#">LTR Yields</a></li>
            <li><a href="#">Yield Delta</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">Insights</div>
        <ul class="footer-links">
            <li><a href="#">Sentiment</a></li>
            <li><a href="#">House Prices</a></li>
            <li><a href="#">Rail Access</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">Data</div>
        <ul class="footer-links">
            <li><a href="#">Data Dictionary</a></li>
            <li><a href="#">Pipeline Docs</a></li>
            <li><a href="#">Assumptions</a></li>
        </ul>
    </div>
    <div>
        <div class="footer-col-title">About</div>
        <ul class="footer-links">
            <li><a href="#">Methodology</a></li>
            <li><a href="https://github.com/" target="_blank">GitHub</a></li>
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