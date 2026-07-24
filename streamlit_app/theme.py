import base64
import os
import streamlit as st
import streamlit.components.v1 as components

TEAL = "#0D9488"


@st.cache_data
def _get_logo_b64():
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_investstay_simple_cropped.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def get_theme():
    dark = st.session_state.get("dark_mode", False)
    if dark:
        return dict(
            bg="#12181b", text="#f2ede4", text_muted="#93a0a3", border="#2a3336",
            card_bg="#1b2226", card_alt_bg="#212a2e", card_alt_hover="#283236", sidebar_bg="#1b2226",
        )
    return dict(
        bg="#F1F6F5", text="#1a1a1a", text_muted="#888", border="#D7E5E2",
        card_bg="#ffffff", card_alt_bg="#E3EEEC", card_alt_hover="#D8E8E5", sidebar_bg="#ffffff",
    )


def inject_css(extra_css=""):
    t = get_theme()
    st.markdown(f"""
    <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
        [data-testid="stMainBlockContainer"], .block-container {{
            background-color:{t['bg']} !important;
            color:{t['text']} !important;
            font-family:'Inter','Segoe UI',sans-serif;
        }}
        [data-testid="stSidebar"] {{
            background-color:{t['sidebar_bg']} !important;
            border-right:1px solid {t['border']};
        }}
        [data-testid="stSidebar"] * {{ color:{t['text']} !important; }}
        [data-testid="stSidebar"] hr {{ border-color:{t['border']}; }}
        #MainMenu, footer, header {{ visibility:hidden; }}
        /* Streamlit's own widget labels (st.slider/selectbox/multiselect/etc.)
           ship a fixed near-black color that's fine on a white background but
           unreadable on our dark-mode background — override it to match. */
        [data-testid="stWidgetLabel"] p {{ color:{t['text']} !important; }}
        .section-header {{
            font-size:1.1rem; font-weight:700; color:{t['text']}; text-transform:uppercase;
            letter-spacing:0.08em; border-bottom:2px solid {TEAL}; padding-bottom:6px; margin:24px 0 16px 0;
        }}
        .filter-card, .card {{
            background:{t['card_bg']}; border-radius:12px; padding:20px;
            box-shadow:0 2px 8px rgba(0,0,0,0.07); color:{t['text']};
        }}
        .review-card {{
            background:{t['card_bg']}; border-radius:14px; padding:20px 22px;
            box-shadow:0 2px 10px rgba(0,0,0,0.07); margin-bottom:20px;
            font-size:0.95rem; line-height:1.6;
            font-style:italic; color:{t['text']};
        }}
        .review-card::before {{
            content:"\\201C"; font-style:normal; font-weight:800; color:{TEAL};
            opacity:0.6; margin-right:2px;
        }}
        .review-card::after {{
            content:"\\201D"; font-style:normal; font-weight:800; color:{TEAL};
            opacity:0.6; margin-left:2px;
        }}
        .table-card {{
            background: {t['card_bg']};
            border-radius: 16px;
            overflow: auto;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            margin-bottom: 8px;
        }}
        .stat-card {{
            background: {t['card_bg']};
            border-radius: 16px;
            padding: 24px 28px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .stat-label {{
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: {t['text_muted']};
            margin-bottom: 10px;
        }}
        .stat-number {{
            font-weight: 800;
            color: {TEAL};
            line-height: 1.05;
            white-space: nowrap;
        }}
        .stat-note {{
            font-size: 0.85rem;
            font-style: italic;
            color: {t['text_muted']};
            margin-top: 8px;
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
        {extra_css}
    </style>
    """, unsafe_allow_html=True)
    return t


def style_chart(fig):
    """Apply the shared black-Inter text theme to a Plotly figure. Call this
    AFTER fig.update_layout(template=...) / px.* — templates supply their own
    (grey) tick/legend font that otherwise silently overrides a bare
    font_color set earlier in the same call."""
    axis_font = dict(family="Inter, sans-serif", color="#1a1a1a")
    fig.update_layout(
        font=dict(family="Inter, sans-serif", color="#1a1a1a"),
        legend=dict(font=dict(family="Inter, sans-serif", color="#1a1a1a")),
    )
    fig.update_xaxes(tickfont=axis_font, title_font=axis_font)
    fig.update_yaxes(tickfont=axis_font, title_font=axis_font)
    return fig


def render_stat_card(label, value, note="", unit="", big=False, min_height=None):
    """Render the shared white-card "label + big number + note" stat card
    used across the app (Home Valuation's price/rent cards, Property
    Analysis's Investment Score card, etc.) — previously each page hand-
    rolled its own near-identical version of this with a different CSS
    class name, so this is the one place to change how it looks.

    `unit` renders as small muted text right after the number (e.g. "/
    month"). `big=True` uses a larger fixed font size for a single
    headline stat instead of the default responsive clamp() size used when
    several of these sit in a row. `min_height` pins card height (useful
    to keep a row of cards even) — left unset, a card sizes to its content.
    """
    t = get_theme()
    number_size = "54px" if big else "clamp(1.7rem, 2.1vw, 2.3rem)"
    height_style = f"min-height:{min_height}px;" if min_height else ""
    unit_html = f'<span style="font-size:0.85rem;color:{t["text_muted"]};"> {unit}</span>' if unit else ""
    note_html = f'<div class="stat-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="stat-card" style="{height_style}">
            <div class="stat-label">{label}</div>
            <div class="stat-number" style="font-size:{number_size};">{value}{unit_html}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_styled_table(df, highlight_cols=None, max_height=480):
    """Render a DataFrame as the shared white-card / teal-header table style
    used across the app. Columns should already be formatted as display
    strings (currency, %, etc.) by the caller. `highlight_cols` names columns
    to render in bold teal (e.g. a score column)."""
    highlight_cols = set(highlight_cols or [])
    thead_cells = "".join(f"<th>{c}</th>" for c in df.columns)
    body_rows = "".join(
        "<tr>" + "".join(
            f'<td class="score-cell">{row[col]}</td>' if col in highlight_cols else f"<td>{row[col]}</td>"
            for col in df.columns
        ) + "</tr>"
        for _, row in df.iterrows()
    )
    st.markdown(
        f'''<div class="table-card" style="max-height:{max_height}px;"><table class="styled-table">
            <thead><tr>{thead_cells}</tr></thead>
            <tbody>{body_rows}</tbody>
        </table></div>''',
        unsafe_allow_html=True,
    )


def _logo_img_tag(height, extra_style=""):
    logo_b64 = _get_logo_b64()
    if logo_b64:
        return f'<img src="data:image/png;base64,{logo_b64}" style="height:{height}px;width:auto;display:block;{extra_style}"/>'
    return '<span style="font-size:1.4rem;font-weight:900;letter-spacing:-0.05em;">IS</span>'


def render_logo_link():
    """Fixed top-left logo for pages that hide the sidebar (no [data-testid='stSidebar'])."""
    st.markdown(f"""
    <a href="/" target="_self" style="position:fixed; top:14px; left:24px; z-index:999999;
        display:inline-flex; transition:opacity 0.2s ease, transform 0.2s ease;"
        onmouseover="this.style.opacity=0.75;this.style.transform='scale(1.04)';"
        onmouseout="this.style.opacity=1;this.style.transform='scale(1)';">
        {_logo_img_tag(115)}
    </a>
    """, unsafe_allow_html=True)


STRIPE_COLORS = ["#1B4F72", "#1A6B8A", "#0D9488", "#10c87a", "#12db6b"]


def render_stripes():
    """The 5-color gradient stripe band used on Home, for visual consistency across pages."""
    bars = "".join(f'<div style="height:18px;width:100%;background:{c};"></div>' for c in STRIPE_COLORS)
    st.markdown(
        f'<div style="display:flex;flex-direction:column;width:100%;margin:8px 0 24px;">{bars}</div>',
        unsafe_allow_html=True,
    )


NAV_LINKS = [
    ("/Property_Analysis", "Invest"),
    ("/Home_Valuation", "Valuation"),
    ("/Sentiment", "Sentiment"),
    ("/Explore_Areas", "Explore"),
    ("/Yield_Analysis", "Yields"),
    ("/Data_Dictionary", "Data"),
    ("/How_It_Works", "How it Works"),
    ("/About_Us", "About Us"),
]


def navbar_links_html(active=None):
    """Shared <li> markup for the nav-links list. Home.py's own hero navbar
    and this module's render_navbar() both call this instead of each
    hardcoding the link list, so link text/hrefs never need to be edited
    in two places again."""
    return "".join(
        f'<li><a href="{href}" target="_self"{" style=\'opacity:1;font-weight:700;\'" if label == active else ""}>{label}</a></li>'
        for href, label in NAV_LINKS
    )


def navbar_shared_css(t):
    """CSS shared by both navbar implementations: the logo link, the link
    list itself, and the settings gear. Positioning (Home's navbar is
    `sticky` and sits above the hero; every other page's is `fixed` so it
    can escape ancestor padding) and CTA-button layout differ intentionally
    between the two, so those rules stay defined locally at each call site."""
    return f"""
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
    .navbar-logo-link:hover {{ opacity: 0.75; transform: scale(1.04); }}
    .nav-links {{
        display: flex;
        align-items: center;
        margin-top: auto;
        margin-bottom: auto;
        gap: 22px;
        list-style: none;
        transform: translateX(-10px);
    }}
    .nav-links li {{ display: flex; align-items: center; }}
    .nav-links a {{
        color: {t['text']};
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
        color: {t['text']};
        background: {t['card_alt_bg']};
        transition: transform 0.15s ease, background 0.15s ease;
    }}
    .settings-btn svg {{ width: 18px; height: 18px; }}
    .settings-btn:hover {{ transform: rotate(45deg); background: {t['card_alt_hover']}; }}
    """


def render_settings_toggle_script():
    """Wire up click/tap toggling for the settings-gear dropdown, which
    otherwise only opens on CSS :hover — meaning dark mode has no way to be
    reached at all on a touchscreen (no hover event exists there). Must run
    via components.html: it renders in its own iframe, so unlike a plain
    onclick="..." attribute inside st.markdown(unsafe_allow_html=True)
    (which Streamlit's HTML sanitizer silently strips), this actually
    executes and can reach into the parent document to bind a real
    listener. Call this once per page, anywhere after the navbar markup."""
    components.html("""
    <script>
    (function() {
        var doc = window.parent.document;
        function bind(attemptsLeft) {
            var btn = doc.querySelector('.settings-btn');
            if (!btn) {
                if (attemptsLeft > 0) setTimeout(function() { bind(attemptsLeft - 1); }, 300);
                return;
            }
            if (btn.dataset.toggleBound) return;
            btn.dataset.toggleBound = "1";
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                doc.body.classList.toggle('settings-open');
            });
            doc.addEventListener('click', function(e) {
                var menu = doc.querySelector('.st-key-settings_menu');
                if (menu && !menu.contains(e.target) && !btn.contains(e.target)) {
                    doc.body.classList.remove('settings-open');
                }
            });
        }
        bind(20);
    })();
    </script>
    """, height=0)


def render_navbar(active=None):
    """Top navbar (logo, links, CTA, settings dropdown) used on every page instead of the native sidebar."""
    t = get_theme()

    with st.container(key="settings_menu"):
        st.toggle("🌙 Dark mode", key="dark_mode", label_visibility="visible")

    links_html = navbar_links_html(active)
    # On the Invest page itself, the navbar CTA would just link back to
    # the page you're already on, duplicating the in-page "Analyse Investment"
    # button that actually does something (jumps to the Dashboard tab).
    # An indented blank line here would satisfy Markdown's 4-space code-block
    # rule and swallow the rest of the navbar HTML into a <pre> block — so an
    # HTML comment stands in for "no CTA" instead of an empty string.
    cta_html = (
        '<a href="/Property_Analysis" target="_self" class="nav-cta-btn">Analyse Properties →</a>'
        if active != "Invest" else "<!-- no CTA on the Invest page -->"
    )

    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ display: none !important; }}
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"],
    .block-container {{
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 32px !important;
        padding-right: 32px !important;
        margin-top: 0 !important;
        max-width: 100% !important;
    }}
    /* The navbar is position:fixed (escapes every ancestor's padding/
       max-width entirely, so it's immune to however many nested
       containers Streamlit wraps content in). Since a fixed element is
       pulled out of normal flow, this reserves the same space back so
       page content doesn't render underneath it. */
    [data-testid="stMainBlockContainer"] {{
        padding-top: 74px !important;
    }}
    [data-testid="stMain"] > div:first-child,
    [data-testid="stElementContainer"]:first-of-type {{
        margin-top: 0 !important;
    }}
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{
        gap: 0 !important;
    }}
    .navbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 48px;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100%;
        background: {t['card_bg']};
        border-bottom: 1px solid {t['border']};
        z-index: 100;
    }}
    {navbar_shared_css(t)}
    .nav-cta-btn {{
        background: {TEAL};
        color: #ffffff !important;
        padding: 10px 24px;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 600;
        text-decoration: none !important;
        line-height: 1.2;
        display: inline-flex;
        align-items: center;
        margin-top: auto;
        margin-bottom: auto;
        font-family: 'Inter', sans-serif;
        transition: transform 0.15s ease, background 0.15s ease;
    }}
    .nav-cta-btn:hover {{
        background: #0b7a70;
        transform: translateY(-1px);
    }}
    .st-key-settings_menu {{
        position: fixed;
        top: 46px;
        right: 254px;
        z-index: 1000;
        background: {t['card_bg']};
        padding: 14px 18px;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.14);
        width: auto !important;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-6px);
        transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s;
        pointer-events: none;
    }}
    body:has(.settings-btn:hover) .st-key-settings_menu,
    body.settings-open .st-key-settings_menu,
    .st-key-settings_menu:hover {{
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
        pointer-events: auto;
    }}
    .st-key-settings_menu label p {{
        color: {t['text']} !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem !important;
    }}
    </style>

    <div class="navbar">
        <div class="navbar-left">
            <a href="/" target="_self" class="navbar-logo-link">{_logo_img_tag(82, "transform:translateY(-6px);")}</a>
            <ul class="nav-links">{links_html}</ul>
        </div>
        <div class="navbar-right">
            <a href="#" onclick="return false;" class="settings-btn" title="Settings" aria-label="Settings" aria-haspopup="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
            </a>
            {cta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_settings_toggle_script()


def render_sidebar_branding():
    """Logo + wordmark at the top of the sidebar, linking back to Home."""
    t = get_theme()
    with st.sidebar:
        st.markdown(f"""
        <a href="/" target="_self" style="text-decoration:none; display:block; padding:16px 0 8px 0;">
            {_logo_img_tag(96)}
            <div style='font-size:1.6rem;font-weight:800;color:{t['text']};letter-spacing:-0.02em;margin-top:8px;'>
                Invest<span style='color:{TEAL};'>Stay</span>
            </div>
            <div style='font-size:0.75rem;color:{t['text_muted']};margin-top:2px;letter-spacing:0.1em;'>ANALYSE · INVEST · GROW</div>
        </a><hr/>
        """, unsafe_allow_html=True)
