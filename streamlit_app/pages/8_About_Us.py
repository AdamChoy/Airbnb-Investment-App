import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from theme import TEAL, inject_css, render_navbar, render_stripes

st.set_page_config(page_title="About Us · InvestStay", page_icon="🏙️", layout="wide", initial_sidebar_state="collapsed")

t = inject_css()
NAVY = t["text"]; MID = t["text_muted"]; WHITE = t["card_bg"]
render_navbar(active="About Us")

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>About <span style='color:{TEAL};'>Us</span></h2>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{MID};margin-bottom:24px;'>Who's behind InvestStay, and why we built it.</p>",
    unsafe_allow_html=True,
)
render_stripes()

st.markdown(
    f"""
    <div style='background:{WHITE};border-radius:12px;padding:24px 28px;margin-bottom:32px;
         box-shadow:0 2px 8px rgba(0,0,0,0.07);'>
    <p style='color:{NAVY};font-size:1rem;line-height:1.7;margin:0;'>
    InvestStay was built to answer one question property investors keep asking with too little
    real data: <b>short-term or long-term let — which actually performs better, and where?</b>
    We combine open datasets on Airbnb listings, house prices, rents, transport and guest
    sentiment into a single, transparent scoring model, so the answer comes from the numbers
    rather than a hunch. Every figure traces back to a real source — see the
    <a href="/Data_Dictionary" target="_self" style="color:{TEAL};">Data Dictionary</a> for exact
    definitions, and <a href="/How_It_Works" target="_self" style="color:{TEAL};">How It Works</a>
    for the full pipeline.
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='section-header'>The Team</div>", unsafe_allow_html=True)

LINKEDIN_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46c.98 0 1.77-.77 1.77-1.72V1.72C24 .77 23.21 0 22.23 0zM7.06 20.45H3.56V9h3.5v11.45zM5.31 7.43c-1.12 0-2.03-.92-2.03-2.05 0-1.13.91-2.05 2.03-2.05 1.12 0 2.03.92 2.03 2.05 0 1.13-.91 2.05-2.03 2.05zM20.45 20.45h-3.5v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.13 1.44-2.13 2.94v5.67h-3.5V9h3.36v1.56h.05c.47-.89 1.62-1.85 3.34-1.85 3.57 0 4.23 2.35 4.23 5.41v6.33z"/></svg>'

TEAM = [
    ("Adam Choy",           "Data Engineer and Frontend Designer", "https://www.linkedin.com/in/adam-choy-b95715190/"),
    ("Roisin Houchen",      "Data Analyst",                        "https://www.linkedin.com/in/roisin-houchen-aa4175313/"),
    ("Tariq Ali",           "Data Analyst",                        "https://www.linkedin.com/in/tariq-ali-10l/"),
    ("Thadsha Sivashanker", "Data Engineer",                       "https://www.linkedin.com/in/thadsha-sivashanker-877946243/"),
]

cols = st.columns(4)
for col, (name, role, url) in zip(cols, TEAM):
    initials = "".join(part[0] for part in name.split() if part)
    with col:
        st.markdown(
            f"""
            <div style='background:{WHITE};border-radius:12px;padding:20px;text-align:center;
                 box-shadow:0 2px 8px rgba(0,0,0,0.07);'>
                <div style='width:56px;height:56px;border-radius:50%;background:{TEAL};
                     color:#fff;display:flex;align-items:center;justify-content:center;
                     font-weight:700;font-size:1.1rem;margin:0 auto 12px;'>{initials}</div>
                <div style='font-weight:700;color:{NAVY};margin-bottom:4px;'>{name}</div>
                <div style='color:{MID};font-size:0.8rem;margin-bottom:8px;'>{role}</div>
                <a href="{url}" target="_blank" style='color:{TEAL};text-decoration:none;
                   display:inline-flex;align-items:center;gap:6px;font-size:0.85rem;'>
                   {LINKEDIN_ICON} LinkedIn
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>Data Sources</div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <p style='color:{MID};font-size:0.9rem;line-height:1.7;'>
    Inside Airbnb &middot; HM Land Registry &middot; Office for National Statistics &middot;
    OS OpenData &middot; NHS Digital
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
