import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Yield Analysis · InvestStay", page_icon="📈", layout="wide")

NAVY = "#1B2A4A"; TEAL = "#0D9488"; LIGHT = "#F0F4F8"; WHITE = "#FFFFFF"; MID = "#64748B"

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{ background-color:{LIGHT}; font-family:'Inter','Segoe UI',sans-serif; }}
    [data-testid="stSidebar"] {{ background-color:{NAVY} !important; }}
    [data-testid="stSidebar"] * {{ color:{WHITE} !important; }}
    [data-testid="stSidebar"] hr {{ border-color:#2d4a6e; }}
    #MainMenu, footer, header {{ visibility:hidden; }}
    .section-header {{
        font-size:1.1rem;font-weight:700;color:{NAVY};text-transform:uppercase;
        letter-spacing:0.08em;border-bottom:2px solid {TEAL};padding-bottom:6px;margin:24px 0 16px 0;
    }}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 0 8px 0;'>
        <div style='font-size:1.6rem;font-weight:800;color:white;letter-spacing:-0.02em;'>
            Invest<span style='color:{TEAL};'>Stay</span>
        </div>
        <div style='font-size:0.75rem;color:#7fb3d3;margin-top:2px;letter-spacing:0.1em;'>ANALYSE · INVEST · GROW</div>
    </div><hr/>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    msoa = pd.read_csv(os.path.join(base, "msoa_investment_summary.csv"))
    lad  = pd.read_csv(os.path.join(base, "lad_investment_summary.csv"))
    return msoa, lad

msoa_df, lad_df = load_data()

st.markdown(f"<h2 style='color:{NAVY};font-weight:800;margin-bottom:4px;'>Yield Analysis</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MID};margin-bottom:24px;'>Compare STR and LTR gross yields across cities and neighbourhoods.</p>", unsafe_allow_html=True)

city_filter = st.selectbox("Filter by city", ["All"] + sorted(msoa_df["city"].dropna().unique().tolist()))
plot_df = msoa_df if city_filter == "All" else msoa_df[msoa_df["city"] == city_filter]
plot_df = plot_df.dropna(subset=["str_gross_yield", "ltr_gross_yield"])

# ── STR vs LTR scatter ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>STR Yield vs LTR Yield by MSOA</div>", unsafe_allow_html=True)

fig1 = px.scatter(
    plot_df,
    x="ltr_gross_yield",
    y="str_gross_yield",
    color="city",
    hover_name="msoa_name",
    hover_data={"lad_name": True, "median_house_price_2025": True,
                "str_vs_ltr_yield_delta": ":.3f", "city": False},
    color_discrete_sequence=[TEAL, NAVY, "#D97706", "#059669"],
    labels={"ltr_gross_yield": "LTR Gross Yield", "str_gross_yield": "STR Gross Yield"},
    template="plotly_white",
)
# Diagonal line: where STR = LTR
max_val = max(plot_df["str_gross_yield"].max(), plot_df["ltr_gross_yield"].max())
fig1.add_trace(go.Scatter(
    x=[0, max_val], y=[0, max_val],
    mode="lines", line=dict(color="lightgrey", dash="dash", width=1),
    name="STR = LTR", showlegend=True
))
fig1.update_layout(height=480, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                   font=dict(family="Inter, Segoe UI, sans-serif"))
st.plotly_chart(fig1, use_container_width=True)
st.caption("Points above the dashed line = STR outperforms LTR on gross yield.")

# ── Top 15 MSOAs bar chart ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Top 15 MSOAs by STR vs LTR Yield Delta</div>", unsafe_allow_html=True)

top15 = (
    plot_df.dropna(subset=["str_vs_ltr_yield_delta"])
    .nlargest(15, "str_vs_ltr_yield_delta")
    .copy()
)
top15["label"] = top15["msoa_name"].str[:30] + " (" + top15["city"] + ")"
top15["delta_pct"] = top15["str_vs_ltr_yield_delta"] * 100

fig2 = px.bar(
    top15, x="delta_pct", y="label", orientation="h",
    color="delta_pct",
    color_continuous_scale=[[0, "#e6faf8"], [1, TEAL]],
    labels={"delta_pct": "Yield Delta (%)", "label": ""},
    template="plotly_white",
)
fig2.update_layout(height=480, showlegend=False, coloraxis_showscale=False,
                   plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                   yaxis=dict(autorange="reversed"),
                   font=dict(family="Inter, Segoe UI, sans-serif"))
st.plotly_chart(fig2, use_container_width=True)

# ── Yield by city box plot ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>STR Yield Distribution by City</div>", unsafe_allow_html=True)

fig3 = px.box(
    plot_df, x="city", y="str_gross_yield",
    color="city",
    color_discrete_sequence=[TEAL, NAVY, "#D97706", "#059669"],
    labels={"str_gross_yield": "STR Gross Yield", "city": "City"},
    template="plotly_white",
)
fig3.update_layout(height=380, showlegend=False,
                   plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                   font=dict(family="Inter, Segoe UI, sans-serif"))
st.plotly_chart(fig3, use_container_width=True)
