"""
RestNet — Sleep Environment Monitor
Streamlit dashboard for visualising sleep quality, bedroom environment conditions,
and external air quality over a 2-week collection period (9-22 February 2026).

Data sources:
    1. Bedroom sensors (Heltec WiFi LoRa 32 V3) — temperature, humidity, noise
    2. Breathe London API (site BL0046) — PM2.5, NO2
    3. Ultrahuman Ring wearable — sleep score, duration, stages
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ============================================================
# APP CONFIGURATION
# ============================================================
st.set_page_config(page_title="RestNet", page_icon="🌙", layout="wide")

# ============================================================
# CUSTOM CSS
# Injected via st.markdown to override Streamlit defaults.
# Inline style= attributes are used elsewhere in the code
# because Streamlit strips class attributes from some elements.
# ============================================================
st.markdown("""
<style>
    /* ── Sidebar width ── */
    [data-testid="stSidebar"] {
        min-width: 440px;
        max-width: 440px;
    }

    /* ── Metric Cards — shared base style ── */
    .metric-card {
        border-radius: 14px;
        padding: 1rem 1.2rem;
        text-align: left;
        position: relative;
        overflow: hidden;
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }

    /* ── Ochre Gold — Sleep Overview ── */
    .metric-card.card-gold {
        background: rgba(196, 164, 78, 0.06);
        border: 1px solid rgba(196, 164, 78, 0.18);
    }
    .metric-card.card-gold:hover {
        border-color: rgba(196, 164, 78, 0.35);
        box-shadow: 0 4px 20px rgba(196, 164, 78, 0.10);
    }
    .metric-card.card-gold::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #C4A44E, rgba(196, 164, 78, 0.15));
        border-radius: 14px 14px 0 0;
    }
    .metric-card.card-gold .metric-label-top { color: rgba(196, 164, 78, 0.75); }
    .metric-card.card-gold .metric-value { color: #C4A44E; }
    .metric-card.card-gold .metric-unit { color: rgba(196, 164, 78, 0.50); }

    /* ── Turquoise — Bedroom Environment ── */
    .metric-card.card-turquoise {
        background: rgba(92, 184, 178, 0.06);
        border: 1px solid rgba(92, 184, 178, 0.18);
    }
    .metric-card.card-turquoise:hover {
        border-color: rgba(92, 184, 178, 0.35);
        box-shadow: 0 4px 20px rgba(92, 184, 178, 0.10);
    }
    .metric-card.card-turquoise::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #5CB8B2, rgba(92, 184, 178, 0.15));
        border-radius: 14px 14px 0 0;
    }
    .metric-card.card-turquoise .metric-label-top { color: rgba(92, 184, 178, 0.75); }
    .metric-card.card-turquoise .metric-value { color: #5CB8B2; }
    .metric-card.card-turquoise .metric-unit { color: rgba(92, 184, 178, 0.50); }

    /* ── Dusty Rose — External Air Quality ── */
    .metric-card.card-rose {
        background: rgba(212, 122, 152, 0.06);
        border: 1px solid rgba(212, 122, 152, 0.18);
    }
    .metric-card.card-rose:hover {
        border-color: rgba(212, 122, 152, 0.35);
        box-shadow: 0 4px 20px rgba(212, 122, 152, 0.10);
    }
    .metric-card.card-rose::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #D47A98, rgba(212, 122, 152, 0.15));
        border-radius: 14px 14px 0 0;
    }
    .metric-card.card-rose .metric-label-top { color: rgba(212, 122, 152, 0.75); }
    .metric-card.card-rose .metric-value { color: #D47A98; }
    .metric-card.card-rose .metric-unit { color: rgba(212, 122, 152, 0.50); }

    .metric-label-top {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.5px;
    }
    .metric-unit {
        font-size: 1.1rem;
        font-weight: 400;
        margin-left: 2px;
    }

    /* ═══════════════════════════════════════════════
       PREMIUM SIDEBAR
       ═══════════════════════════════════════════════ */

    /* Sidebar base */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e2a3a 0%, #2a3849 100%);
    }

    /* Sidebar inner content — flex column for footer pinning */
    [data-testid="stSidebar"] > div:first-child {
        display: flex !important;
        flex-direction: column !important;
        min-height: 100vh !important;
        height: 100% !important;
        padding-top: 2.5rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
        min-height: 100vh !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 !important;
    }

    /* ── Sidebar Section Dividers ── */
    .sb-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(61, 79, 99, 0.6), transparent);
        margin: 2rem 1.5rem;
    }
    .sb-divider-logo {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(61, 79, 99, 0.6), transparent);
        margin: 2.5rem 1.5rem 2rem 1.5rem;
    }

    /* ── User Profile Card ── */
    .user-profile {
        padding: 1rem 1.25rem;
        margin: 0 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
    }

    .avatar-pulse {
        position: absolute;
        top: -3px; left: -3px; right: -3px; bottom: -3px;
        border-radius: 50%;
        border: 2px solid rgba(232, 147, 122, 0.4);
        animation: pulse-ring 2.5s ease-in-out infinite;
    }

    @keyframes pulse-ring {
        0%, 100% { opacity: 0.4; transform: scale(1); }
        50% { opacity: 0.15; transform: scale(1.08); }
    }

    /* ── Nav Buttons: Kill Streamlit wrapper spacing ── */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ── Inactive nav (secondary buttons) ── */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        all: unset !important;
        display: flex !important;
        width: 100% !important;
        box-sizing: border-box !important;
        padding: 1.1rem 1.5rem !important;
        margin: 4px 0 !important;
        color: #94A3B8 !important;
        font-size: 2rem !important;
        font-weight: 500 !important;
        font-family: inherit !important;
        letter-spacing: 0.2px !important;
        cursor: pointer !important;
        border-left: 3px solid transparent !important;
        transition: all 0.28s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"] *,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] * {
        color: #94A3B8 !important;
        font-size: 2rem !important;
        text-align: left !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(226, 232, 240, 0.06) !important;
        transform: translateX(3px) !important;
        border-left-color: #475569 !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover *,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover * {
        color: #CBD5E1 !important;
    }

    /* ── Active nav (primary buttons) ── */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        all: unset !important;
        display: flex !important;
        width: 100% !important;
        box-sizing: border-box !important;
        padding: 1.1rem 1.5rem !important;
        margin: 4px 0 !important;
        color: #E8937A !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        font-family: inherit !important;
        letter-spacing: 0.2px !important;
        cursor: pointer !important;
        border-left: 3px solid #E8937A !important;
        background: linear-gradient(90deg, rgba(232, 147, 122, 0.18), rgba(232, 147, 122, 0.04), transparent) !important;
        transition: all 0.28s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] *,
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] * {
        color: #E8937A !important;
        font-size: 2rem !important;
        text-align: left !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(90deg, rgba(232, 147, 122, 0.22), rgba(232, 147, 122, 0.06), transparent) !important;
    }

    /* ═══════════════════════════════════════════════
       SECTION GLASS CARDS — Coral-tinted containers
       ═══════════════════════════════════════════════ */
    .main [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(
            160deg,
            rgba(232, 147, 122, 0.07) 0%,
            rgba(209, 122, 95, 0.03) 40%,
            rgba(30, 41, 59, 0.5) 100%
        ) !important;
        border: 1px solid rgba(232, 147, 122, 0.13) !important;
        border-radius: 24px !important;
        padding: 1.5rem 2rem !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1rem !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        box-shadow:
            0 0 0 1px rgba(232, 147, 122, 0.05),
            0 8px 40px rgba(0, 0, 0, 0.15),
            0 2px 12px rgba(232, 147, 122, 0.03) !important;
        transition: border-color 0.3s ease !important;
    }
    .main [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(232, 147, 122, 0.22) !important;
    }
    .main [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: transparent !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# PLOTLY THEME
# Shared layout dict applied to all charts via **PLOTLY_LAYOUT.
# Note: xaxis/yaxis keys are already set here, so per-chart
# overrides must use fig.update_xaxes() / fig.update_yaxes()
# or a second fig.update_layout() call to avoid duplicates.
# ============================================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", size=22),
    xaxis=dict(gridcolor="#334155", zerolinecolor="#334155",
               tickfont=dict(size=22), title_font=dict(size=24)),
    yaxis=dict(gridcolor="#334155", zerolinecolor="#334155",
               tickfont=dict(size=22), title_font=dict(size=24)),
    margin=dict(l=80, r=20, t=40, b=90),
)

COLORS = {
    "blue": "#7A9FE8",
    "pink": "#F472B6",
}

# ============================================================
# DATA LOADING
# ============================================================
DATA_DIR = Path("data")

@st.cache_data
def load_sensor_data():
    df = pd.read_csv(DATA_DIR / "bedroom_sensors.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["night"] = df["timestamp"].apply(
        lambda t: t.date() if t.hour >= 12 else (t - pd.Timedelta(days=1)).date()
    )
    return df

@st.cache_data
def load_air_quality():
    df = pd.read_csv(DATA_DIR / "breathe_london_air_quality.csv")
    df.columns = ["timestamp", "pm25", "no2"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["night"] = df["timestamp"].apply(
        lambda t: t.date() if t.hour >= 12 else (t - pd.Timedelta(days=1)).date()
    )
    return df

@st.cache_data
def load_sleep_data():
    df = pd.read_csv(DATA_DIR / "ultrahuman_sleep_data.csv")
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

sensors = load_sensor_data()
air = load_air_quality()
sleep = load_sleep_data()

# ============================================================
# NIGHTLY SUMMARIES
# ============================================================
@st.cache_data
def build_nightly_summary():
    sensor_nightly = sensors.groupby("night").agg(
        avg_temp=("temperature_c", "mean"),
        avg_humidity=("humidity_pct", "mean"),
        avg_sound=("sound_avg", "mean"),
        std_sound=("sound_avg", "std"),
        range_temp=("temperature_c", lambda x: x.max() - x.min()),
        light_pct=("light_detected", "mean"),
    ).round(1)
    sensor_nightly["light_pct"] = (sensor_nightly["light_pct"] * 100).round(1)

    air_nightly = air.groupby("night").agg(
        avg_pm25=("pm25", "mean"),
        avg_no2=("no2", "mean"),
    ).round(1)

    summary = sensor_nightly.join(air_nightly, how="outer")
    summary = summary.join(
        sleep.set_index("Date")[["Sleep Score", "Total Sleep", "Sleep Awake Time", "Deep Sleep", "REM Sleep", "Light Sleep"]],
        how="outer"
    )
    summary.index.name = "night"
    summary = summary.reset_index()
    summary["night"] = pd.to_datetime(summary["night"])
    return summary

nightly = build_nightly_summary()

# ============================================================
# CORRELATION FINDINGS (from notebook Part 2, Subpart 2)
# Hardcoded Spearman correlations between environment features
# and Sleep Score, computed over the 14-night study period.
# Only factors with p < 0.05 are included.
# ============================================================
SLEEP_PREDICTORS = [
    {"feature": "std_sound",    "label": "Noise variability",  "r": -0.80, "p": 0.001, "unit": "",   "good": "low",  "bad": "high",  "verdict_bad": "This mattered more than any other bedroom condition. Variable noise disrupts sleep.", "verdict_neutral": "Close to your usual level. Noise variability mattered more than any other bedroom condition.", "verdict_good": "This mattered more than any other bedroom condition. Steady noise tonight."},
    {"feature": "avg_humidity", "label": "Humidity",            "r": -0.70, "p": 0.005, "unit": "%",  "good": "low",  "bad": "high",  "verdict_bad": "Higher humidity linked to lower sleep scores.",                     "verdict_neutral": "Close to your usual humidity level.",                                            "verdict_good": "Humidity was in the better range for your sleep."},
    {"feature": "avg_sound",    "label": "Noise level",         "r": -0.69, "p": 0.006, "unit": "",   "good": "low",  "bad": "high",  "verdict_bad": "Louder nights linked to worse sleep.",                              "verdict_neutral": "Close to your usual noise level.",                                               "verdict_good": "A quieter night, linked to better sleep."},
    {"feature": "range_temp",   "label": "Temperature stability","r": -0.56, "p": 0.037, "unit": "°C", "good": "low",  "bad": "high",  "verdict_bad": "Wide temperature swings linked to poorer sleep.",                   "verdict_neutral": "Temperature range was typical for you.",                                         "verdict_good": "Stable temperature, no concern."},
]
NON_SIGNIFICANT = ["Light exposure", "PM2.5", "NO₂"]

# ============================================================
# SIDEBAR
# ============================================================

# Logo
st.sidebar.markdown("""
<div style="padding: 0 1.5rem; margin-bottom: 0;">
    <div style="font-size: 3.5rem; font-weight: 900; color: #E8937A; letter-spacing: 1px; line-height: 1;">RestNet</div>
    <div style="font-size: 1.2rem; color: #94A3B8; margin-top: 0.75rem; font-weight: 300; letter-spacing: 1.2px; text-transform: uppercase;">Understand Your Sleep</div>
</div>
<div class="sb-divider-logo"></div>
""", unsafe_allow_html=True)

# User profile card
st.sidebar.markdown("""
<div class="user-profile">
    <div style="position: relative; flex-shrink: 0;">
        <div class="avatar-pulse"></div>
        <div style="width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #E8937A, #D17A5F); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 500; color: #FFFFFF; position: relative; z-index: 2;">YA</div>
    </div>
    <div style="flex: 1; min-width: 0;">
        <div style="font-size: 2.2rem; font-weight: 600; color: #E2E8F0; margin-bottom: 0.2rem; line-height: 1.3;">Yasmin Akhmedova</div>
        <div style="font-size: 1.6rem; color: #94A3B8;">9 – 22 February 2026</div>
    </div>
</div>
<div class="sb-divider"></div>
""", unsafe_allow_html=True)

# Page navigation
PAGES = ["Sleep Dashboard", "Night Explorer", "My Sleep Insights"]

if "page" not in st.session_state:
    st.session_state.page = "Sleep Dashboard"

st.sidebar.markdown('<div style="font-size: 1.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2rem; font-weight: 600; padding-left: 1.5rem;">Navigation</div>', unsafe_allow_html=True)

for p in PAGES:
    is_active = p == st.session_state.page
    btn_type = "primary" if is_active else "secondary"
    if st.sidebar.button(p, key=f"nav_{p}", use_container_width=True, type=btn_type):
        st.session_state.page = p
        st.rerun()

page = st.session_state.page

# Footer
st.sidebar.markdown("""
<div style="margin-top: 12rem; padding: 1.5rem 1.5rem; border-top: 1px solid rgba(61, 79, 99, 0.5);">
    <div style="color: #64748B; font-size: 1.7rem; line-height: 1.8; font-weight: 300;">
        <strong style="color: #94A3B8; font-weight: 500; font-size: 1.7rem;">Environmental Sensing for<br>Sleep Quality Analysis</strong><br><br>
        IoT & Applications<br>
        Imperial College London<br>
        March 2026
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PAGE 1: SLEEP DASHBOARD
# ============================================================
if page == "Sleep Dashboard":

    st.markdown('<div style="font-size: 5rem; font-weight: 800; color: #E8937A; margin-bottom: 0.5rem; line-height: 1.1;">Sleep Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.8rem; color: #94A3B8; margin-top: 0.5rem; margin-bottom: 1.5rem; font-weight: 600;">Two-Week Overview | 9 – 23 February 2026</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 1.575rem; line-height: 1.8; margin-bottom: 3rem; font-weight: 400;">
        <span style="color: #8892a5; font-size: 1.575rem;">Here's your overview of 14 nights (9–22 February 2026).
        It covers your </span><span style="color: #C4A44E; font-weight: 600; font-size: 1.575rem;">nightly sleep scores, duration, and deep sleep</span><span style="color: #8892a5; font-size: 1.575rem;">,
        the </span><span style="color: #5CB8B2; font-weight: 600; font-size: 1.575rem;">four bedroom conditions that affected your sleep</span><span style="color: #8892a5; font-size: 1.575rem;"> (noise variability, humidity, noise level, and temperature stability),
        and </span><span style="color: #D47A98; font-weight: 600; font-size: 1.575rem;">outdoor air quality</span><span style="color: #8892a5; font-size: 1.575rem;"> around your home.</span>
    </div>
    """, unsafe_allow_html=True)

    avg_score = sleep["Sleep Score"].mean()
    avg_temp = nightly["avg_temp"].mean()
    avg_humidity = nightly["avg_humidity"].mean()
    avg_sound = nightly["avg_sound"].mean()
    avg_std_sound = nightly["std_sound"].mean()
    avg_range_temp = nightly["range_temp"].mean()
    avg_sleep_hrs = sleep["Total Sleep"].mean() / 60
    avg_deep_sleep = sleep["Deep Sleep"].mean() / 60

    st.markdown("""
    <div style="display: flex; gap: 1.5rem; margin-bottom: 1rem; font-size: 0.95rem; color: #94A3B8;">
        <span>Colour key across all charts:</span>
        <span><span style="color: #9EDEBE;">&#9679;</span> Good sleep (score ≥ 80)</span>
        <span><span style="color: #E8C88A;">&#9679;</span> Fair sleep (70–79)</span>
        <span><span style="color: #E09C9C;">&#9679;</span> Poor sleep (score &lt; 70)</span>
    </div>""", unsafe_allow_html=True)

    # ── SECTION 1: SLEEP OVERVIEW ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #C4A44E; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(196, 164, 78, 0.20);">Sleep Overview</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card card-gold">
                <div class="metric-label-top">Average Sleep Score</div>
                <div class="metric-value">{avg_score:.0f}<span class="metric-unit">/ 100</span></div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card card-gold">
                <div class="metric-label-top">Average Duration</div>
                <div class="metric-value">{avg_sleep_hrs:.1f}<span class="metric-unit">hrs</span></div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card card-gold">
                <div class="metric-label-top">Average Deep Sleep</div>
                <div class="metric-value">{avg_deep_sleep:.1f}<span class="metric-unit">hrs</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #C4A44E; margin-top: 1rem; margin-bottom: 0.25rem;">Nightly Sleep Score</div>', unsafe_allow_html=True)

        scores = nightly["Sleep Score"]
        nights = nightly["night"]
        night_labels = [d.strftime("%a %-d") for d in nights]

        great_y = [s if s >= 80 else None for s in scores]
        fair_y  = [s if 70 <= s < 80 else None for s in scores]
        poor_y  = [s if s < 70 else None for s in scores]

        fig_score = go.Figure()
        fig_score.add_trace(go.Bar(x=night_labels, y=great_y, marker_color="#9EDEBE", opacity=0.85,
            name="Good (80+)", marker_line=dict(width=0),
            hovertemplate="<b>%{x}</b><br>Sleep Score: %{y}<extra></extra>"))
        fig_score.add_trace(go.Bar(x=night_labels, y=fair_y, marker_color="#E8C88A", opacity=0.85,
            name="Fair (70–79)", marker_line=dict(width=0),
            hovertemplate="<b>%{x}</b><br>Sleep Score: %{y}<extra></extra>"))
        fig_score.add_trace(go.Bar(x=night_labels, y=poor_y, marker_color="#E09C9C", opacity=0.85,
            name="Poor (<70)", marker_line=dict(width=0),
            hovertemplate="<b>%{x}</b><br>Sleep Score: %{y}<extra></extra>"))

        fig_score.add_hline(y=80, line_dash="dash", line_color="#E05555", line_width=2.5,
            annotation_text="Good (80+)", annotation_position="top left",
            annotation_font=dict(color="#E05555", size=13))

        fig_score.update_layout(**PLOTLY_LAYOUT, height=420, yaxis_title="Sleep Score",
            yaxis_range=[50, 100], bargap=0.25, barmode="overlay",
            showlegend=False)
        fig_score.update_xaxes(type="category", tickangle=-45, title_text="February 2026")
        st.plotly_chart(fig_score, use_container_width=True)

        st.markdown('<div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;"><em>Sleep scores are provided by the Ultrahuman Ring. Score categories (Excellent, Good, Fair, Poor) are defined by this dashboard and are not official Ultrahuman classifications.</em></div>', unsafe_allow_html=True)

    # ── SECTION 2: BEDROOM ENVIRONMENT ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #5CB8B2; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(92, 184, 178, 0.20);">Bedroom Environment</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card card-turquoise">
                <div class="metric-label-top">Avg Noise Variability</div>
                <div class="metric-value">{avg_std_sound:.1f}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card card-turquoise">
                <div class="metric-label-top">Avg Humidity</div>
                <div class="metric-value">{avg_humidity:.0f}<span class="metric-unit">%</span></div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card card-turquoise">
                <div class="metric-label-top">Avg Noise Level</div>
                <div class="metric-value">{avg_sound:.0f}</div>
            </div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card card-turquoise">
                <div class="metric-label-top">Avg Temp Range</div>
                <div class="metric-value">{avg_range_temp:.1f}<span class="metric-unit">°C</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size: 0.95rem; color: #94A3B8; margin-top: 0.75rem; margin-bottom: 0.75rem; line-height: 1.5;">
            These are the four bedroom conditions that showed a statistically significant correlation
            with your sleep score across 14 nights, ordered by strength of association.
            Select each tab below to see how it varied night to night.
        </div>""", unsafe_allow_html=True)

        env_night_labels = [d.strftime("%a %-d") for d in nightly["night"]]

        score_colors = []
        for s in nightly["Sleep Score"]:
            if pd.isna(s):
                score_colors.append("#475569")
            elif s >= 80:
                score_colors.append("#9EDEBE")
            elif s >= 70:
                score_colors.append("#E8C88A")
            else:
                score_colors.append("#E09C9C")

        def env_bar_chart(y_data, y_title, hover_template):
            y_min, y_max = y_data.min(), y_data.max()
            y_pad = max((y_max - y_min) * 0.3, 0.5)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=env_night_labels, y=y_data,
                marker_color=score_colors, marker_line=dict(width=0),
                opacity=0.85, hovertemplate=hover_template, showlegend=False))
            fig.update_layout(**PLOTLY_LAYOUT, height=500, yaxis_title=y_title,
                yaxis_range=[y_min - y_pad, y_max + y_pad], showlegend=False)
            fig.update_xaxes(type="category", tickangle=-45, title_text="February 2026")
            return fig

        tab_std_sound, tab_humid, tab_noise, tab_temp_range = st.tabs(
            ["Noise Variability", "Humidity", "Noise Level", "Temperature Stability"])

        with tab_std_sound:
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #5CB8B2; margin-top: 1rem; margin-bottom: 0.25rem;">Nightly Noise Variability</div>', unsafe_allow_html=True)
            st.plotly_chart(env_bar_chart(nightly["std_sound"], "Noise Std Dev (sensor units)",
                "<b>%{x}</b><br>Noise variability: %{y:.1f}<extra></extra>"), use_container_width=True)
            st.markdown('<div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;"><em>Standard deviation of noise readings per night. Higher values mean more fluctuation in noise levels (e.g. intermittent traffic, doors closing).</em></div>', unsafe_allow_html=True)

        with tab_humid:
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #5CB8B2; margin-top: 1rem; margin-bottom: 0.25rem;">Nightly Humidity</div>', unsafe_allow_html=True)
            st.plotly_chart(env_bar_chart(nightly["avg_humidity"], "Humidity (%)",
                "<b>%{x}</b><br>%{y:.0f}%<extra></extra>"), use_container_width=True)
            st.markdown('<div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;"><em>Average relative humidity in the bedroom per night. Both very dry and very humid air can disrupt sleep.</em></div>', unsafe_allow_html=True)

        with tab_noise:
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #5CB8B2; margin-top: 1rem; margin-bottom: 0.25rem;">Nightly Noise Level</div>', unsafe_allow_html=True)
            st.plotly_chart(env_bar_chart(nightly["avg_sound"], "Noise Level (sensor units)",
                "<b>%{x}</b><br>Avg Noise: %{y:.0f}<extra></extra>"), use_container_width=True)
            st.markdown('<div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;"><em>Average noise level per night on a relative sensor scale. Higher values correspond to louder environments.</em></div>', unsafe_allow_html=True)

        with tab_temp_range:
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #5CB8B2; margin-top: 1rem; margin-bottom: 0.25rem;">Nightly Temperature Stability</div>', unsafe_allow_html=True)
            st.plotly_chart(env_bar_chart(nightly["range_temp"], "Temperature Range (°C)",
                "<b>%{x}</b><br>Temp range: %{y:.1f}°C<extra></extra>"), use_container_width=True)
            st.markdown('<div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;"><em>Difference between the highest and lowest temperature recorded during the night. Smaller values indicate a more stable sleeping temperature.</em></div>', unsafe_allow_html=True)

    # ── SECTION 3: EXTERNAL AIR QUALITY ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #D47A98; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(212, 122, 152, 0.20);">External Air Quality</div>', unsafe_allow_html=True)

        WHO_PM25 = 15
        WHO_NO2  = 25

        total_nights = len(nightly)
        nights_outside_pm25 = int((nightly["avg_pm25"] > WHO_PM25).sum())
        nights_outside_no2  = int((nightly["avg_no2"] > WHO_NO2).sum())

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card card-rose">
                <div class="metric-label-top">Outside WHO PM2.5 Guideline</div>
                <div class="metric-value">{nights_outside_pm25}<span class="metric-unit">/ {total_nights} nights</span></div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card card-rose">
                <div class="metric-label-top">Outside WHO NO₂ Guideline</div>
                <div class="metric-value">{nights_outside_no2}<span class="metric-unit">/ {total_nights} nights</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #D47A98; margin-top: 1rem; margin-bottom: 0.25rem;">Nightly Air Pollutant Levels</div>', unsafe_allow_html=True)

        air_night_labels = [d.strftime("%a %-d") for d in nightly["night"]]
        air_all_vals = list(nightly["avg_pm25"]) + list(nightly["avg_no2"]) + [WHO_PM25, WHO_NO2]
        air_min, air_max = min(air_all_vals), max(air_all_vals)
        air_pad = max((air_max - air_min) * 0.2, 2)

        fig_air = go.Figure()
        fig_air.add_trace(go.Scatter(x=air_night_labels, y=nightly["avg_pm25"],
            name="PM2.5 (µg/m³)", line=dict(color=COLORS["pink"], width=2.5),
            fill="tozeroy", fillcolor="rgba(244, 114, 182, 0.12)",
            hovertemplate="<b>%{x}</b><br>PM2.5: %{y:.1f} µg/m³<extra></extra>"))
        fig_air.add_trace(go.Scatter(x=air_night_labels, y=nightly["avg_no2"],
            name="NO₂ (µg/m³)", line=dict(color=COLORS["blue"], width=2.5),
            fill="tozeroy", fillcolor="rgba(122, 159, 232, 0.12)",
            hovertemplate="<b>%{x}</b><br>NO₂: %{y:.1f} µg/m³<extra></extra>"))

        fig_air.add_hline(y=WHO_PM25, line_dash="dash", line_color="#E05555", line_width=2.5,
            annotation_text="WHO PM2.5 (15 µg/m³)", annotation_position="top left",
            annotation_font=dict(color="#E05555", size=13))
        fig_air.add_hline(y=WHO_NO2, line_dash="dash", line_color="#E05555", line_width=2.5,
            annotation_text="WHO NO₂ (25 µg/m³)", annotation_position="top left",
            annotation_font=dict(color="#E05555", size=13))

        fig_air.update_layout(**PLOTLY_LAYOUT, height=500, yaxis_title="Concentration (µg/m³)",
            yaxis_range=[max(0, air_min - air_pad), air_max + air_pad],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center",
                        font=dict(size=22, color="#94A3B8"), bgcolor="rgba(0,0,0,0)"))
        fig_air.update_xaxes(type="category", tickangle=-45, title_text="February 2026")
        st.plotly_chart(fig_air, use_container_width=True)

        st.markdown(f"""
        <div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
            <em>Neither PM2.5 nor NO₂ showed a significant correlation with sleep quality in this dataset.
            These are included for general health context against WHO guidelines.
            Air quality data covers the sleep window (11 pm to 9 am) only.
            WHO guidelines for PM2.5 ({WHO_PM25} µg/m³) and NO₂ ({WHO_NO2} µg/m³) are based on 24-hour averages,
            so these comparisons represent partial-day measurements.</em>
        </div>""", unsafe_allow_html=True)

# ============================================================
# PAGE 2: NIGHT EXPLORER
# ============================================================
elif page == "Night Explorer":

    st.markdown('<div style="font-size: 5rem; font-weight: 800; color: #E8937A; margin-bottom: 0.5rem; line-height: 1.1;">Night Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.8rem; color: #94A3B8; margin-top: 0.5rem; margin-bottom: 1.5rem; font-weight: 600;">Dive Into a Single Night</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 1.575rem; line-height: 1.8; margin-bottom: 3rem; font-weight: 400;">
        <span style="color: #8892a5; font-size: 1.575rem;">Select a night below to explore what happened while you slept.
        This page breaks down your </span><span style="color: #C4A44E; font-weight: 600; font-size: 1.575rem;">sleep architecture</span><span style="color: #8892a5; font-size: 1.575rem;">,
        shows a minute-by-minute </span><span style="color: #5CB8B2; font-weight: 600; font-size: 1.575rem;">bedroom environment timeline</span><span style="color: #8892a5; font-size: 1.575rem;">,
        checks whether </span><span style="color: #D47A98; font-weight: 600; font-size: 1.575rem;">outdoor air quality</span><span style="color: #8892a5; font-size: 1.575rem;"> met WHO guidelines,
        provides a </span><span style="color: #E8937A; font-weight: 600; font-size: 1.575rem;">quick summary</span><span style="color: #8892a5; font-size: 1.575rem;"> of the night,
        and explains </span><span style="color: #B89ADE; font-weight: 600; font-size: 1.575rem;">why your sleep scored the way it did</span><span style="color: #8892a5; font-size: 1.575rem;">.</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Night selector ──
    available_nights = sorted(sleep["Date"].tolist())
    st.markdown('<div style="font-size: 1.8rem; color: #94A3B8; font-weight: 600; margin-bottom: 0.5rem;">Select a Night</div>', unsafe_allow_html=True)
    selected_night = st.date_input("Select a night", value=available_nights[-1],
        min_value=available_nights[0], max_value=available_nights[-1],
        key="night_selector", label_visibility="collapsed")

    night_sleep_df = sleep[sleep["Date"] == selected_night]
    if night_sleep_df.empty:
        st.warning("No sleep data available for this date. Please select another night.")
        st.stop()

    night_sensors = sensors[sensors["night"] == selected_night].copy().sort_values("timestamp").reset_index(drop=True)
    night_air = air[air["night"] == selected_night].copy().sort_values("timestamp").reset_index(drop=True)
    night_sleep = night_sleep_df.iloc[0]

    # ============================================================
    # SECTION 1: SLEEP ARCHITECTURE
    # ============================================================
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #C4A44E; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(196, 164, 78, 0.20);">Sleep Architecture</div>', unsafe_allow_html=True)

        score = night_sleep["Sleep Score"]
        avg_score_all = sleep["Sleep Score"].mean()
        score_diff = score - avg_score_all
        diff_sign = "+" if score_diff > 0 else ""
        diff_color = "#9EDEBE" if score_diff >= 0 else "#E09C9C"

        deep = int(night_sleep["Deep Sleep"])
        rem = int(night_sleep["REM Sleep"])
        light_sl = int(night_sleep["Light Sleep"])
        awake = int(night_sleep["Sleep Awake Time"])
        total_sleep_min = deep + rem + light_sl + awake
        total_hrs = total_sleep_min // 60
        total_mins = total_sleep_min % 60

        col_score, col_compare, col_total = st.columns(3)
        with col_score:
            st.markdown(f"""
            <div class="metric-card card-gold">
                <div class="metric-label-top">Sleep Score</div>
                <div class="metric-value">{score}<span class="metric-unit">/ 100</span></div>
            </div>""", unsafe_allow_html=True)
        with col_compare:
            st.markdown(f"""
            <div class="metric-card card-gold">
                <div class="metric-label-top">vs. 2-Week Average</div>
                <div class="metric-value" style="color: {diff_color};">{diff_sign}{score_diff:.0f}<span class="metric-unit" style="color: {diff_color};">points</span></div>
            </div>""", unsafe_allow_html=True)
        with col_total:
            st.markdown(f"""
            <div class="metric-card card-gold">
                <div class="metric-label-top">Total Sleep Time</div>
                <div class="metric-value">{total_hrs}<span class="metric-unit">h</span> {total_mins}<span class="metric-unit">m</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #C4A44E; margin-top: 1rem; margin-bottom: 0.25rem;">Sleep Stages Breakdown</div>', unsafe_allow_html=True)

        stage_colors = {"Deep": "#E8937A", "REM": "#F2BFB0", "Light": "#7BC8A4", "Awake": "#94A3B8"}
        stages_ordered = [("Deep", deep), ("REM", rem), ("Light", light_sl), ("Awake", awake)]

        fig_arch = go.Figure()
        running_x = 0
        for stage_name, stage_val in stages_ordered:
            pct = stage_val / total_sleep_min * 100 if total_sleep_min else 0
            hrs = stage_val // 60
            mins = stage_val % 60
            fig_arch.add_trace(go.Bar(y=["Sleep Stages"], x=[stage_val], name=stage_name,
                orientation="h", marker_color=stage_colors[stage_name], marker_line=dict(width=0),
                hovertemplate=f"<b>{stage_name}</b><br>{hrs}h {mins}m ({pct:.0f}%)<extra></extra>"))
            if pct >= 8:
                fig_arch.add_annotation(x=running_x + stage_val / 2, y="Sleep Stages",
                    text=f"{stage_name} {pct:.0f}%", showarrow=False,
                    font=dict(size=15, color="#FFFFFF", weight="bold"),
                    xanchor="center", yanchor="middle")
            running_x += stage_val

        fig_arch.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", size=18), barmode="stack", height=170, showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.15, x=0.5, xanchor="center",
                        font=dict(size=16, color="#94A3B8"), bgcolor="rgba(0,0,0,0)", traceorder="normal"),
            margin=dict(l=0, r=0, t=10, b=50), bargap=0)
        fig_arch.update_xaxes(visible=False, automargin=False, range=[0, total_sleep_min])
        fig_arch.update_yaxes(visible=False, automargin=False)
        fig_arch.update_traces(marker_cornerradius=8)
        st.plotly_chart(fig_arch, use_container_width=True, config={"displayModeBar": False})

        if awake > 50:
            st.markdown('<div style="font-size: 0.85rem; color: #E09C9C; line-height: 1.5; margin-top: 0.75rem;"><em>High awake time (>50 min) is the strongest predictor of a low sleep score in your data.</em></div>', unsafe_allow_html=True)

    # ============================================================
    # SECTION 2: BEDROOM ENVIRONMENT TIMELINE
    # Line charts for temperature, humidity, noise; binary strip for light.
    # ============================================================
    if len(night_sensors) > 0:
        with st.container(border=True):
            st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #5CB8B2; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(92, 184, 178, 0.20);">Bedroom Environment Timeline</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #5CB8B2; margin-bottom: 0.25rem;">Minute-by-minute bedroom conditions from 11 pm to 9 am. Hover for exact values.</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.95rem; color: #94A3B8; margin-bottom: 1rem;">These are the four bedroom conditions recorded by your sensors throughout the night. Temperature, humidity, and noise level were all linked to sleep quality across your 14 nights. Light exposure is included for completeness but did not show a significant link to sleep quality.</div>', unsafe_allow_html=True)

            time_vals = night_sensors["timestamp"]
            temp_vals = night_sensors["temperature_c"].values
            humid_vals = night_sensors["humidity_pct"].values
            sound_vals = night_sensors["sound_avg"].values
            light_vals = night_sensors["light_detected"].values

            def make_env_line(x, y, title, y_label, color, hover_unit, fill=False):
                fig = go.Figure()
                fill_color = None
                if fill:
                    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                    fill_color = f"rgba({r},{g},{b},0.08)"
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines",
                    line=dict(color=color, width=2),
                    fill="tozeroy" if fill else None, fillcolor=fill_color,
                    hovertemplate=f"<b>%{{x|%H:%M}}</b><br>{title}: %{{y:.1f}}{hover_unit}<extra></extra>",
                    showlegend=False))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0", size=14), height=200,
                    margin=dict(l=60, r=20, t=30, b=30), showlegend=False)
                fig.update_xaxes(tickformat="%H:%M", tickfont=dict(size=13, color="#94A3B8"),
                    gridcolor="rgba(51,65,85,0.3)", nticks=10)
                fig.update_yaxes(title_text=y_label, title_font=dict(size=13, color="#94A3B8"),
                    tickfont=dict(size=13, color="#94A3B8"), gridcolor="rgba(51,65,85,0.3)")
                return fig

            st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #7BC8A4; margin-top: 0.75rem; margin-bottom: 0;">Temperature</div>', unsafe_allow_html=True)
            st.plotly_chart(make_env_line(time_vals, temp_vals, "Temp", "°C", "#7BC8A4", "°C"),
                            use_container_width=True, config={"displayModeBar": False})

            st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #4ECDC4; margin-top: 0.25rem; margin-bottom: 0;">Humidity</div>', unsafe_allow_html=True)
            st.plotly_chart(make_env_line(time_vals, humid_vals, "Humidity", "%", "#4ECDC4", "%"),
                            use_container_width=True, config={"displayModeBar": False})

            st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #5B8FB9; margin-top: 0.25rem; margin-bottom: 0;">Noise Level</div>', unsafe_allow_html=True)
            st.plotly_chart(make_env_line(time_vals, sound_vals, "Noise", "Sensor Units", "#5B8FB9", "", fill=True),
                            use_container_width=True, config={"displayModeBar": False})

            # Light — binary strip (inherently categorical)
            st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #94A3B8; margin-top: 0.25rem; margin-bottom: 0;">Light On / Off</div>', unsafe_allow_html=True)
            time_labels_light = night_sensors["timestamp"].dt.strftime("%H:%M").tolist()
            if time_labels_light and time_labels_light[-1] != "09:00":
                time_labels_light[-1] = "09:00"
            tick_interval = max(1, len(time_labels_light) // 10)
            tickvals_light = list(time_labels_light[::tick_interval])
            if "09:00" not in tickvals_light:
                tickvals_light.append("09:00")

            fig_light = go.Figure()
            fig_light.add_trace(go.Heatmap(z=[light_vals], x=time_labels_light, y=["Light"],
                colorscale=[[0.0, "#0F172A"], [1.0, "#F5E6D3"]], zmin=0, zmax=1,
                showscale=False, hovertemplate="<b>%{x}</b><br>Light: %{z}<extra></extra>"))
            fig_light.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0", size=14), height=100,
                margin=dict(l=60, r=20, t=5, b=40), showlegend=False)
            fig_light.update_xaxes(tickmode="array", tickvals=tickvals_light, tickangle=0,
                tickfont=dict(size=13, color="#94A3B8"), gridcolor="rgba(51,65,85,0.3)")
            fig_light.update_yaxes(showticklabels=False, gridcolor="rgba(51,65,85,0.3)")
            st.plotly_chart(fig_light, use_container_width=True, config={"displayModeBar": False})

    # ============================================================
    # SECTION 3: AIR QUALITY VERDICT
    # Rose-themed verdict cards with green/red accents for pass/fail.
    # ============================================================
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #D47A98; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(212, 122, 152, 0.20);">Air Quality Verdict</div>', unsafe_allow_html=True)

        WHO_PM25_NE = 15
        WHO_NO2_NE = 25

        if len(night_air) > 0:
            avg_pm25_ne = night_air["pm25"].mean()
            avg_no2_ne = night_air["no2"].mean()

            pm25_ok = avg_pm25_ne <= WHO_PM25_NE
            no2_ok = avg_no2_ne <= WHO_NO2_NE

            if pm25_ok:
                pm25_icon, pm25_accent = "✓", "#9EDEBE"
                pm25_msg = f"Overnight PM2.5 averaged {avg_pm25_ne:.1f} µg/m³, within WHO 24-hour guideline ({WHO_PM25_NE})"
            else:
                pm25_icon, pm25_accent = "✗", "#E09C9C"
                pm25_msg = f"Overnight PM2.5 averaged {avg_pm25_ne:.1f} µg/m³, {avg_pm25_ne / WHO_PM25_NE:.1f}× the WHO 24-hour guideline ({WHO_PM25_NE})"

            if no2_ok:
                no2_icon, no2_accent = "✓", "#9EDEBE"
                no2_msg = f"Overnight NO₂ averaged {avg_no2_ne:.1f} µg/m³, within WHO 24-hour guideline ({WHO_NO2_NE})"
            else:
                no2_icon, no2_accent = "✗", "#E09C9C"
                no2_msg = f"Overnight NO₂ averaged {avg_no2_ne:.1f} µg/m³, {avg_no2_ne / WHO_NO2_NE:.1f}× the WHO 24-hour guideline ({WHO_NO2_NE})"

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="border-radius: 14px; padding: 1.2rem 1.5rem; display: flex; align-items: center; gap: 1rem;
                            background: rgba(212, 122, 152, 0.06); border: 1px solid rgba(212, 122, 152, 0.18);">
                    <div style="font-size: 2rem; line-height: 1; color: {pm25_accent};">{pm25_icon}</div>
                    <div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {pm25_accent};">
                            {avg_pm25_ne:.1f} <span style="font-size: 0.9rem; font-weight: 400;">µg/m³</span></div>
                        <div style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.4;">{pm25_msg}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="border-radius: 14px; padding: 1.2rem 1.5rem; display: flex; align-items: center; gap: 1rem;
                            background: rgba(212, 122, 152, 0.06); border: 1px solid rgba(212, 122, 152, 0.18);">
                    <div style="font-size: 2rem; line-height: 1; color: {no2_accent};">{no2_icon}</div>
                    <div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {no2_accent};">
                            {avg_no2_ne:.1f} <span style="font-size: 0.9rem; font-weight: 400;">µg/m³</span></div>
                        <div style="font-size: 0.95rem; color: #CBD5E1; line-height: 1.4;">{no2_msg}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

            # Informative summary with peak values
            if pm25_ok and no2_ok:
                summary_msg = f"Both pollutants stayed within WHO guidelines overnight. PM2.5 peaked at {night_air['pm25'].max():.1f} µg/m³ and NO₂ at {night_air['no2'].max():.1f} µg/m³."
                summary_color = "#9EDEBE"
            elif not pm25_ok and not no2_ok:
                summary_msg = "Both PM2.5 and NO₂ exceeded WHO guidelines. Consider keeping windows closed on similar nights."
                summary_color = "#E09C9C"
            elif not pm25_ok:
                summary_msg = f"PM2.5 was elevated (peak {night_air['pm25'].max():.1f} µg/m³) while NO₂ stayed within limits."
                summary_color = "#E8C88A"
            else:
                summary_msg = f"NO₂ was elevated (peak {night_air['no2'].max():.1f} µg/m³) while PM2.5 stayed within limits."
                summary_color = "#E8C88A"

            st.markdown(f'<div style="font-size: 1.3rem; font-weight: 600; color: #D47A98; margin-top: 0.75rem;">{summary_msg}</div>', unsafe_allow_html=True)

            # Non-significance disclaimer + WHO caveat
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.5; margin-top: 0.75rem;">
                <em>Neither PM2.5 nor NO₂ showed a significant link to sleep quality in this dataset.
                These are included for general health context against WHO guidelines.
                WHO guidelines for PM2.5 ({WHO_PM25_NE} µg/m³) and NO₂ ({WHO_NO2_NE} µg/m³) are based on
                24-hour averages. This comparison uses overnight data only (approx. 11 pm to 9 am),
                so values shown represent a partial-day average rather than a full 24-hour measurement.</em>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size: 1.1rem; color: #64748B;">Air quality data unavailable for this night.</div>', unsafe_allow_html=True)

    # ============================================================
    # SECTION 4: NIGHT AT A GLANCE
    # Icon card grid with auto-generated insights.
    # ============================================================
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #E8937A; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(232, 147, 122, 0.20);">Night at a Glance</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #E8937A; margin-bottom: 0.25rem;">A quick snapshot of your bedroom conditions for this night.</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.95rem; color: #94A3B8; margin-bottom: 1rem;">Temperature, humidity, and noise were linked to sleep quality across your 14 nights. Light exposure and air quality are included for general context.</div>', unsafe_allow_html=True)

        def insight_card(icon, value, description, accent="#CBD5E1"):
            return f"""
            <div style="border-radius: 12px; padding: 0.9rem 1rem; background: rgba(255,255,255,0.02);
                        border: 1px solid rgba(255,255,255,0.06); height: 100%;">
                <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{icon}</div>
                <div style="font-size: 1.15rem; font-weight: 700; color: {accent}; line-height: 1.3; margin-bottom: 0.2rem;">{value}</div>
                <div style="font-size: 0.8rem; color: #64748B; line-height: 1.4;">{description}</div>
            </div>"""

        insight_cards = []

        def fmt_hour(h):
            if h == 0: return "12 AM"
            elif h < 12: return f"{h} AM"
            elif h == 12: return "12 PM"
            else: return f"{h - 12} PM"

        if len(night_sensors) > 0:
            night_sensors["hour"] = night_sensors["timestamp"].dt.hour

            hourly_temp = night_sensors.groupby("hour")["temperature_c"].mean()
            coolest_hr = hourly_temp.idxmin()
            warmest_hr = hourly_temp.idxmax()
            insight_cards.append(insight_card("❄️", f"{hourly_temp[coolest_hr]:.1f}°C at {fmt_hour(coolest_hr)}", "Coolest hour", "#7BC8A4"))
            insight_cards.append(insight_card("🔥", f"{hourly_temp[warmest_hr]:.1f}°C at {fmt_hour(warmest_hr)}", "Warmest hour", "#E8937A"))

            hourly_sound = night_sensors.groupby("hour")["sound_avg"].mean()
            quietest_hr = hourly_sound.idxmin()
            noisiest_hr = hourly_sound.idxmax()
            insight_cards.append(insight_card("🤫", f"{fmt_hour(quietest_hr)}, avg {hourly_sound[quietest_hr]:.0f}", "Quietest hour", "#5B8FB9"))
            insight_cards.append(insight_card("🔊", f"{fmt_hour(noisiest_hr)}, avg {hourly_sound[noisiest_hr]:.0f}", "Noisiest hour", "#E8C88A"))

            night_avg_humidity = night_sensors["humidity_pct"].mean()
            overall_avg_humidity = nightly["avg_humidity"].mean()
            insight_cards.append(insight_card("💧", f"{night_avg_humidity:.1f}%", f"Avg humidity (14-night avg: {overall_avg_humidity:.1f}%)", "#5CB8B2"))

            night_avg_sound = night_sensors["sound_avg"].mean()
            overall_avg_sound = nightly["avg_sound"].mean()
            insight_cards.append(insight_card("🔉", f"{night_avg_sound:.0f}", f"Avg noise level (14-night avg: {overall_avg_sound:.0f})", "#D4A574"))

            light_on_minutes = int(night_sensors["light_detected"].sum())
            total_minutes = len(night_sensors)
            light_pct = (light_on_minutes / total_minutes) * 100
            insight_cards.append(insight_card("💡", f"{light_on_minutes} of {total_minutes} min ({light_pct:.0f}%)", "Light exposure", "#94A3B8"))

        if len(night_air) > 0:
            if pm25_ok and no2_ok:
                insight_cards.append(insight_card("🌿", "Within WHO guidelines", "Overnight air quality", "#9EDEBE"))
            else:
                exceeded_names = []
                if not pm25_ok: exceeded_names.append("PM2.5")
                if not no2_ok: exceeded_names.append("NO₂")
                insight_cards.append(insight_card("⚠️", f"{' & '.join(exceeded_names)} elevated", "Overnight air quality", "#E09C9C"))

        # Render 4-column grid
        n_cols = 4
        rows_needed = (len(insight_cards) + n_cols - 1) // n_cols
        card_idx = 0
        for row_i in range(rows_needed):
            cols = st.columns(n_cols)
            for col_i in range(n_cols):
                if card_idx < len(insight_cards):
                    with cols[col_i]:
                        st.markdown(insight_cards[card_idx], unsafe_allow_html=True)
                    card_idx += 1

    # ============================================================
    # SECTION 5: WHY THIS NIGHT?
    # Contextualises this night's environment against the 14-night
    # study using hardcoded Spearman correlation findings from the
    # notebook (Part 2, Subpart 2).
    # ============================================================
    night_row = nightly[nightly["night"] == pd.Timestamp(selected_night)]
    if not night_row.empty and len(night_sensors) > 0:
        night_row = night_row.iloc[0]
        with st.container(border=True):
            st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #B89ADE; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(184, 154, 222, 0.20);">Why This Night?</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #B89ADE; margin-bottom: 0.25rem;">How this night\'s conditions compare to your usual, based on what affected your sleep.</div>', unsafe_allow_html=True)

            st.markdown("""
            <div style="display: flex; gap: 1.5rem; margin-top: 0.5rem; margin-bottom: 1rem; font-size: 0.85rem; color: #64748B;">
                <span><span style="color: #9EDEBE;">&#9679;</span> Better than usual</span>
                <span><span style="color: #C4A44E;">&#9679;</span> Close to usual</span>
                <span><span style="color: #E09C9C;">&#9679;</span> Worse than usual</span>
            </div>""", unsafe_allow_html=True)

            predictor_html = ""
            for pred in SLEEP_PREDICTORS:
                col = pred["feature"]
                value = night_row.get(col, None)
                if value is None or pd.isna(value):
                    continue

                median_val = nightly[col].median()
                diff_from_median = value - median_val

                # Determine if this night was in the good or bad direction
                # All significant predictors have negative r, so higher = worse
                if pred["bad"] == "high":
                    is_bad = value > median_val
                else:
                    is_bad = value < median_val

                # Traffic light colour
                abs_diff_pct = abs(diff_from_median) / median_val * 100 if median_val != 0 else 0
                if abs_diff_pct < 10:
                    dot_color = "#C4A44E"  # yellow — close to median
                elif is_bad:
                    dot_color = "#E09C9C"  # red — bad direction
                else:
                    dot_color = "#9EDEBE"  # green — good direction

                if abs_diff_pct < 10:
                    verdict = pred["verdict_neutral"]
                elif is_bad:
                    verdict = pred["verdict_bad"]
                else:
                    verdict = pred["verdict_good"]
                direction = "above" if diff_from_median > 0 else "below"
                unit = pred["unit"]

                predictor_html += f"""
                <div style="display: flex; align-items: flex-start; gap: 0.8rem; margin-bottom: 0.8rem;
                            padding: 0.7rem 1rem; background: rgba(184, 154, 222, 0.04);
                            border: 1px solid rgba(184, 154, 222, 0.10); border-radius: 10px;">
                    <div style="font-size: 1.8rem; line-height: 1; margin-top: 0.1rem; color: {dot_color};">&#9679;</div>
                    <div>
                        <div style="font-size: 1rem; font-weight: 600; color: #94A3B8;">
                            {pred["label"]}:
                            <span style="color: {dot_color};">{value:.1f}{unit}</span>
                            <span style="font-weight: 400;"> (your median: {median_val:.1f}{unit})</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #8892a5; margin-top: 0.2rem; line-height: 1.4;">
                            <em>{verdict}</em>
                        </div>
                    </div>
                </div>"""

            st.markdown(predictor_html, unsafe_allow_html=True)

            # Non-significant factors note
            non_sig_str = ", ".join(NON_SIGNIFICANT)
            st.markdown(f"""
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.5; margin-top: 0.5rem;">
                <em>{non_sig_str} showed no statistically significant correlation with sleep quality
                across your 14 nights of data.</em>
            </div>""", unsafe_allow_html=True)

# ============================================================
# PAGE 3: MY COMFORT ZONE
# Convergence page — where sleep, environment, and air quality
# data come together to answer "what helps me sleep best?"
# ============================================================
elif page == "My Sleep Insights":
    import numpy as np
    from scipy import stats as sp_stats

    st.markdown('<div style="font-size: 5rem; font-weight: 800; color: #E8937A; margin-bottom: 0.5rem; line-height: 1.1;">My Sleep Insights</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.8rem; color: #94A3B8; margin-top: 0.5rem; margin-bottom: 1.5rem; font-weight: 600;">What Helps You Sleep Best?</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 1.575rem; line-height: 1.8; margin-bottom: 3rem; font-weight: 400;">
        <span style="color: #8892a5; font-size: 1.575rem;">This page brings your
        </span><span style="color: #D4A574; font-weight: 600; font-size: 1.575rem;">sleep</span><span style="color: #8892a5; font-size: 1.575rem;">,
        </span><span style="color: #D4A574; font-weight: 600; font-size: 1.575rem;">bedroom environment</span><span style="color: #8892a5; font-size: 1.575rem;">, and
        </span><span style="color: #D4A574; font-weight: 600; font-size: 1.575rem;">air quality</span><span style="color: #8892a5; font-size: 1.575rem;"> data together
        to find the conditions behind your best and worst nights of rest.</span>
    </div>
    """, unsafe_allow_html=True)

    # Page-specific CSS
    st.markdown("""
    <style>
        .metric-card.card-amber {
            background: rgba(212, 165, 116, 0.06);
            border: 1px solid rgba(212, 165, 116, 0.18);
        }
        .metric-card.card-amber:hover {
            border-color: rgba(212, 165, 116, 0.35);
            box-shadow: 0 4px 20px rgba(212, 165, 116, 0.10);
        }
        .metric-card.card-amber::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #D4A574, rgba(212, 165, 116, 0.15));
            border-radius: 14px 14px 0 0;
        }
        .metric-card.card-amber .metric-label-top { color: rgba(212, 165, 116, 0.75); }
        .metric-card.card-amber .metric-value { color: #D4A574; }
        .metric-card.card-amber .metric-unit { color: rgba(212, 165, 116, 0.50); }

        .metric-card.card-steel {
            background: rgba(107, 140, 174, 0.06);
            border: 1px solid rgba(107, 140, 174, 0.18);
        }
        .metric-card.card-steel:hover {
            border-color: rgba(107, 140, 174, 0.35);
            box-shadow: 0 4px 20px rgba(107, 140, 174, 0.10);
        }
        .metric-card.card-steel::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #6B8CAE, rgba(107, 140, 174, 0.15));
            border-radius: 14px 14px 0 0;
        }
        .metric-card.card-steel .metric-label-top { color: rgba(107, 140, 174, 0.75); }
        .metric-card.card-steel .metric-value { color: #6B8CAE; }
        .metric-card.card-steel .metric-unit { color: rgba(107, 140, 174, 0.50); }

        .snapshot-env {
            display: flex; flex-wrap: wrap; gap: 0.4rem 1.2rem;
            margin-top: 0.75rem; padding-top: 0.6rem;
            border-top: 1px solid rgba(255,255,255,0.06);
        }
        .snapshot-env-item { font-size: 0.85rem; color: #94A3B8; line-height: 1.4; }
        .snapshot-env-item strong { color: #CBD5E1; font-weight: 600; }

        .takeaway-box {
            border-radius: 14px; padding: 1.5rem 1.8rem;
            background: linear-gradient(135deg, rgba(212, 165, 116, 0.08), rgba(196, 149, 106, 0.04));
            border: 1px solid rgba(212, 165, 116, 0.20); margin-top: 0.5rem;
        }
        .takeaway-box .takeaway-title { font-size: 1.1rem; font-weight: 700; color: #D4A574; margin-bottom: 0.5rem; }
        .takeaway-box .takeaway-text { font-size: 1.05rem; color: #CBD5E1; line-height: 1.7; }
    </style>
    """, unsafe_allow_html=True)

    # ── Real data from nightly summary ──
    analysis = nightly.dropna(subset=["Sleep Score"]).copy()

    n_nights = len(analysis)

    def fmt_duration(mins):
        return f"{int(mins) // 60}h {int(mins) % 60}m"

    # ── SECTION 1: BEST vs WORST NIGHT SNAPSHOT ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #D4A574; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(212, 165, 116, 0.20);">Best vs Worst Nights</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.3rem; color: #8892a5; margin-bottom: 1rem;">Your highest and lowest scoring nights side by side. Same bed, different conditions.</div>', unsafe_allow_html=True)

        best_row = analysis.loc[analysis["Sleep Score"].idxmax()]
        worst_score_row = analysis.loc[analysis["Sleep Score"].idxmin()]
        worst_dur_row = analysis.loc[analysis["Total Sleep"].idxmin()]

        def snapshot_card(row, label, sublabel, card_class, accent_color):
            date_str = row["night"].strftime("%A %-d %b")
            return f"""
            <div class="metric-card {card_class}" style="min-height: 220px;">
                <div class="metric-label-top">{label}</div>
                <div style="font-size: 0.9rem; color: #94A3B8; margin-bottom: 0.5rem;">{date_str}</div>
                <div class="metric-value">{int(row["Sleep Score"])}<span class="metric-unit">/ 100</span></div>
                <div style="font-size: 1rem; color: {accent_color}; margin-top: 0.2rem; font-weight: 500;">
                    {fmt_duration(row["Total Sleep"])} total · {fmt_duration(row["Deep Sleep"])} deep · {int(row["Sleep Awake Time"])}m awake
                </div>
                <div class="snapshot-env">
                    <div class="snapshot-env-item"><strong>{row["avg_temp"]:.1f}°C</strong> temp</div>
                    <div class="snapshot-env-item"><strong>{row["avg_humidity"]:.0f}%</strong> humidity</div>
                    <div class="snapshot-env-item"><strong>{row["avg_sound"]:.0f}</strong> noise</div>
                    <div class="snapshot-env-item"><strong>{row["avg_pm25"]:.1f}</strong> PM2.5</div>
                    <div class="snapshot-env-item"><strong>{row["avg_no2"]:.1f}</strong> NO₂</div>
                </div>
                <div style="font-size: 0.75rem; color: #475569; margin-top: 0.5rem;">{sublabel}</div>
            </div>"""

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(snapshot_card(best_row, "Best Night", "Highest sleep score", "card-amber", "#D4A574"), unsafe_allow_html=True)
        with col2:
            st.markdown(snapshot_card(worst_score_row, "Worst Night (Score)", "Lowest sleep score", "card-steel", "#6B8CAE"), unsafe_allow_html=True)
        with col3:
            st.markdown(snapshot_card(worst_dur_row, "Worst Night (Duration)", "Shortest total sleep", "card-steel", "#6B8CAE"), unsafe_allow_html=True)

    # ── SECTION 2: CORRELATION EXPLORER ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #D4A574; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(212, 165, 116, 0.20);">Correlation Explorer</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size: 0.95rem; color: #94A3B8; background: rgba(107, 140, 174, 0.08);
                    border: 1px solid rgba(107, 140, 174, 0.15); border-radius: 10px;
                    padding: 0.8rem 1.2rem; margin-bottom: 1.5rem; line-height: 1.5;">
            Based on <strong style="color: #CBD5E1;">{n_nights} nights</strong> of data.
            Patterns may become clearer with more nights.
        </div>""", unsafe_allow_html=True)

        scatter_vars = [
            ("avg_temp", "Temperature", "Avg Temperature (°C)", "°C"),
            ("avg_humidity", "Humidity", "Avg Humidity (%)", "%"),
            ("avg_sound", "Noise Level", "Avg Noise (sensor)", ""),
            ("std_sound", "Noise Variability", "Noise Std Dev (sensor)", ""),
            ("avg_pm25", "PM2.5", "Avg PM2.5 (µg/m³)", "µg/m³"),
            ("avg_no2", "NO₂", "Avg NO₂ (µg/m³)", "µg/m³"),
            ("Sleep Awake Time", "Awake Time", "Awake Time (min)", "min"),
        ]

        def strength_label(r):
            ar = abs(r)
            if ar >= 0.5: return "Moderate–Strong"
            elif ar >= 0.3: return "Weak–Moderate"
            else: return "Weak"

        def make_scatter(col_name, title, x_label, unit):
            x = analysis[col_name].values
            y = analysis["Sleep Score"].values
            r, p = sp_stats.spearmanr(x, y)
            strength = strength_label(r)

            z = np.polyfit(x, y, 1)
            poly = np.poly1d(z)
            x_trend = np.linspace(x.min(), x.max(), 50)
            y_trend = poly(x_trend)
            trend_color = "#D4A574" if r > 0 else "#6B8CAE"

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y, mode="markers",
                marker=dict(size=10, color="#CBD5E1", opacity=0.85,
                            line=dict(width=1, color="rgba(255,255,255,0.2)")),
                hovertemplate=f"<b>{title}</b>: %{{x:.1f}} {unit}<br>Sleep Score: %{{y}}<extra></extra>",
                showlegend=False))
            fig.add_trace(go.Scatter(x=x_trend, y=y_trend, mode="lines",
                line=dict(color=trend_color, width=2.5, dash="dot"),
                showlegend=False, hoverinfo="skip"))

            p_str = f"p = {p:.3f}" if p >= 0.001 else "p < 0.001"
            fig.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper",
                xanchor="right", yanchor="top",
                text=f"r = {r:+.2f} ({strength})<br><span style='font-size:11px;color:#64748B'>{p_str}</span>",
                showarrow=False, font=dict(size=14, color=trend_color),
                bgcolor="rgba(15, 23, 42, 0.7)", bordercolor="rgba(255,255,255,0.08)",
                borderwidth=1, borderpad=8)

            fig.update_layout(**PLOTLY_LAYOUT, height=320)
            fig.update_layout(margin=dict(l=60, r=20, t=35, b=55))
            fig.update_xaxes(title_text=x_label, title_font=dict(size=14),
                             tickfont=dict(size=12), gridcolor="#1E293B")
            fig.update_yaxes(title_text="Sleep Score", title_font=dict(size=14),
                             tickfont=dict(size=12), gridcolor="#1E293B")
            return fig, r, p

        correlations = {}
        row1 = st.columns(4)
        row2 = st.columns(4)
        grid_positions = list(row1) + list(row2)

        for i, (col_name, title, x_label, unit) in enumerate(scatter_vars):
            fig, r, p = make_scatter(col_name, title, x_label, unit)
            correlations[col_name] = {"r": r, "p": p, "title": title, "unit": unit}
            with grid_positions[i]:
                st.markdown(f'<div style="font-size: 1rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.25rem; text-align: center;">{title}</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── SECTION 3: YOUR OPTIMAL RANGES ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #D4A574; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(212, 165, 116, 0.20);">Your Optimal Ranges</div>', unsafe_allow_html=True)
        median_score = analysis["Sleep Score"].median()
        good = analysis[analysis["Sleep Score"] >= median_score]
        poor = analysis[analysis["Sleep Score"] < median_score]
        st.markdown(f'<div style="font-size: 1.3rem; color: #8892a5; margin-bottom: 1.5rem;">Median-split comparison: <strong style="color: #D4A574;">{len(good)} good</strong> nights (score ≥ {median_score:.0f}) vs <strong style="color: #6B8CAE;">{len(poor)} poor</strong> nights (score < {median_score:.0f}).</div>', unsafe_allow_html=True)

        range_vars = [
            ("avg_temp", "Temperature", "°C", "cooler", "warmer"),
            ("avg_humidity", "Humidity", "%", "drier", "more humid"),
            ("avg_sound", "Noise Level", "", "quieter", "louder"),
            ("std_sound", "Noise Variability", "", "steadier", "more variable"),
            ("avg_pm25", "PM2.5", "µg/m³", "cleaner", "more polluted"),
            ("avg_no2", "NO₂", "µg/m³", "cleaner", "more polluted"),
        ]

        dumbbell_labels, good_means, poor_means, finding_texts = [], [], [], []

        for col_name, label, unit, less_word, more_word in range_vars:
            t_mean = good[col_name].mean()
            b_mean = poor[col_name].mean()
            diff = t_mean - b_mean
            dumbbell_labels.append(label)
            good_means.append(t_mean)
            poor_means.append(b_mean)
            direction = less_word if diff < 0 else more_word
            finding_texts.append(f"<strong>{abs(diff):.1f}{unit}</strong> {direction} on good nights")

        fig_dumbbell = go.Figure()
        for i, label in enumerate(dumbbell_labels):
            t_val, b_val = good_means[i], poor_means[i]
            fig_dumbbell.add_trace(go.Scatter(x=[t_val, b_val], y=[label, label],
                mode="lines", line=dict(color="#475569", width=3), showlegend=False, hoverinfo="skip"))
            fig_dumbbell.add_trace(go.Scatter(x=[t_val], y=[label], mode="markers",
                marker=dict(size=14, color="#D4A574", symbol="circle", line=dict(width=2, color="rgba(212,165,116,0.3)")),
                name="Good nights" if i == 0 else None, showlegend=(i == 0),
                hovertemplate=f"<b>{label}</b> (Good)<br>{t_val:.1f}<extra></extra>"))
            fig_dumbbell.add_trace(go.Scatter(x=[b_val], y=[label], mode="markers",
                marker=dict(size=14, color="#6B8CAE", symbol="circle", line=dict(width=2, color="rgba(107,140,174,0.3)")),
                name="Poor nights" if i == 0 else None, showlegend=(i == 0),
                hovertemplate=f"<b>{label}</b> (Poor)<br>{b_val:.1f}<extra></extra>"))

        fig_dumbbell.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", size=16), height=400,
            margin=dict(l=120, r=40, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center",
                        font=dict(size=16, color="#94A3B8"), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(visible=False), yaxis=dict(gridcolor="rgba(51,65,85,0.3)", tickfont=dict(size=16)))
        st.plotly_chart(fig_dumbbell, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #94A3B8; margin-top: 0.5rem; margin-bottom: 0.75rem;">Key Differences</div>', unsafe_allow_html=True)

        findings_with_r = []
        for i, (col_name, label, unit, lw, mw) in enumerate(range_vars):
            abs_r = abs(correlations[col_name]["r"]) if col_name in correlations else 0
            findings_with_r.append((abs_r, finding_texts[i], label))
        findings_with_r.sort(key=lambda x: x[0], reverse=True)

        findings_html = ""
        for rank, (abs_r, text, label) in enumerate(findings_with_r):
            highlight = "border-left: 3px solid #D4A574; padding-left: 0.8rem;" if rank == 0 else "border-left: 3px solid transparent; padding-left: 0.8rem;"
            badge = '<span style="font-size: 0.7rem; background: rgba(212,165,116,0.15); color: #D4A574; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.5rem; font-weight: 600;">STRONGEST</span>' if rank == 0 else ""
            findings_html += f'<div style="{highlight} margin-bottom: 0.6rem; font-size: 1rem; color: #CBD5E1; line-height: 1.5;">{text}{badge}</div>'
        st.markdown(findings_html, unsafe_allow_html=True)

        good_awake = good["Sleep Awake Time"].mean()
        poor_awake = poor["Sleep Awake Time"].mean()
        awake_diff = poor_awake - good_awake
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 0.8rem 1.2rem; background: rgba(107, 140, 174, 0.06);
                    border: 1px solid rgba(107, 140, 174, 0.12); border-radius: 10px;">
            <span style="font-size: 0.95rem; color: #94A3B8;">
                Awake time averaged <strong style="color: #6B8CAE;">{good_awake:.0f} min</strong> on good nights
                vs <strong style="color: #6B8CAE;">{poor_awake:.0f} min</strong> on poor nights
                , a difference of <strong style="color: #CBD5E1;">{awake_diff:.0f} minutes</strong>.
            </span>
        </div>""", unsafe_allow_html=True)

    # ── SECTION 4: ACTIONABLE TAKEAWAY ──
    with st.container(border=True):
        st.markdown('<div style="font-size: 2rem; font-weight: 700; color: #D4A574; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(212, 165, 116, 0.20);">Actionable Takeaway</div>', unsafe_allow_html=True)

        env_correlations = {k: v for k, v in correlations.items() if k != "Sleep Awake Time"}
        strongest_col = max(env_correlations, key=lambda k: abs(env_correlations[k]["r"]))
        strongest = env_correlations[strongest_col]
        s_r = strongest["r"]
        s_title = strongest["title"]

        advice_map = {
            "avg_temp": {
                "neg": "Consider keeping your bedroom cooler at night. A fan, cracked window, or lower thermostat could help.",
                "pos": "Your data suggests warmer rooms helped, but sleep science generally favours 16–19°C. This may shift with more data.",
            },
            "avg_humidity": {
                "neg": "Lower humidity was associated with better sleep. A dehumidifier or improved ventilation could help.",
                "pos": "Slightly higher humidity seems to have helped. Dry winter air may be disrupting your sleep, so a humidifier could be worth trying.",
            },
            "avg_sound": {
                "neg": "Quieter nights correlated with better sleep. Earplugs, a white noise machine, or closing windows may help.",
                "pos": f"This is unusual: louder nights correlated with better scores. This may be coincidental with only {n_nights} nights of data.",
            },
            "avg_pm25": {
                "neg": "Lower PM2.5 was associated with better sleep. On high-pollution nights, keeping windows closed and using an air purifier could help.",
                "pos": "This correlation is likely coincidental. Higher pollution doesn't help sleep. More data should clarify.",
            },
            "avg_no2": {
                "neg": "Lower NO₂ was associated with better sleep. This is an outdoor pollutant you can't directly control, but closing windows on high-traffic nights may help.",
                "pos": "This correlation is likely coincidental and should resolve with more data.",
            },
            "std_sound": {
                "neg": "Noise variability had the strongest link to your sleep. Consider earplugs or a white noise machine to mask intermittent disruptions like traffic or neighbours.",
                "pos": f"This is unusual: more variable noise correlating with better sleep may be coincidental with only {n_nights} nights of data.",
            },
        }

        direction = "neg" if s_r < 0 else "pos"
        advice = advice_map.get(strongest_col, {}).get(direction, "More data will help clarify this pattern.")

        good_val = good[strongest_col].mean()
        poor_val = poor[strongest_col].mean()
        score_diff = good["Sleep Score"].mean() - poor["Sleep Score"].mean()

        st.markdown(f"""
        <div class="takeaway-box">
            <div class="takeaway-title">💡 Your strongest environmental sleep predictor is {s_title.lower()}</div>
            <div class="takeaway-text">
                With a correlation of <strong>r = {s_r:+.2f}</strong>, {s_title.lower()} showed the strongest
                link to your sleep score across {n_nights} nights. Your good nights (avg score
                {good["Sleep Score"].mean():.0f}) had an average {s_title.lower()} of
                <strong>{good_val:.1f}</strong>, compared to <strong>{poor_val:.1f}</strong>
                on your poor nights (avg score {poor["Sleep Score"].mean():.0f}), a
                <strong>{score_diff:.0f}-point</strong> sleep score difference.
                <br><br>
                {advice}
            </div>
        </div>""", unsafe_allow_html=True)

        awake_r = abs(correlations.get("Sleep Awake Time", {}).get("r", 0))
        if awake_r > abs(s_r):
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 0.8rem 1.2rem; background: rgba(107, 140, 174, 0.06);
                        border: 1px solid rgba(107, 140, 174, 0.12); border-radius: 10px;">
                <span style="font-size: 0.95rem; color: #94A3B8;">
                    <strong style="color: #CBD5E1;">Note:</strong> Awake time
                    (r = {correlations["Sleep Awake Time"]["r"]:+.2f}) is actually the strongest overall
                    predictor of your sleep score, but since it's a sleep metric rather than an environmental
                    factor, the recommendation above focuses on what you can change about your bedroom.
                </span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f'<div style="font-size: 0.85rem; color: #64748B; line-height: 1.5; margin-top: 1rem;"><em>These insights are based on {n_nights} nights. As your dataset grows, recommendations will become more reliable.</em></div>', unsafe_allow_html=True)
