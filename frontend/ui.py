import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────────

_DEFAULT_API_URL = "http://127.0.0.1:8000"


def _api_url() -> str:
    return st.session_state.get("api_url", _DEFAULT_API_URL)

st.set_page_config(
    page_title="Smart Energy Auditor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

<style>
/* Fix Material Icons so expander arrows render as icons, not raw text */
.material-icons {
    font-family: 'Material Icons' !important;
    font-style: normal !important; font-weight: normal !important;
    display: inline-block !important; line-height: 1 !important;
    text-transform: none !important; letter-spacing: normal !important;
    white-space: nowrap !important; direction: ltr !important;
    -webkit-font-smoothing: antialiased !important;
}

*, *::before, *::after { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
.material-icons { font-family: 'Material Icons' !important; }

/* ── App shell ── */
.stApp { background: #060B17; color: #E2E8F0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; }

/* Native sidebar toggle buttons: invisible but clickable via JS */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    position: fixed !important;
    top: 0 !important; left: 0 !important;
    width: 1px !important; height: 1px !important;
    opacity: 0 !important; z-index: -1 !important;
    overflow: hidden !important;
}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {
    width: 1px !important; height: 1px !important;
    min-width: unset !important; padding: 0 !important;
    border: none !important; background: transparent !important;
}

/* Custom hamburger toggle button */
.sidebar-toggle-btn button {
    background: #0C1525 !important;
    border: 1px solid #1A2840 !important;
    border-radius: 10px !important;
    color: #CBD5E1 !important;
    font-size: 1.1rem !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    line-height: 1 !important;
    transition: background 0.15s, border-color 0.15s !important;
}
.sidebar-toggle-btn button:hover {
    background: #1A2840 !important;
    border-color: #00C9B8 !important;
    color: #00C9B8 !important;
}
.block-container { padding: 1.5rem 2.2rem 3rem; max-width: 1300px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #080D1A !important;
    border-right: 1px solid #1A2840;
    min-width: 244px !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.4rem 0.9rem; }

/* ── Generic card ── */
.card {
    background: #0C1525;
    border: 1px solid #1A2840;
    border-radius: 16px;
    padding: 22px 24px;
}
.card-sm {
    background: #0C1525;
    border: 1px solid #1A2840;
    border-radius: 12px;
    padding: 16px 20px;
}

/* ── KPI cards ── */
.kpi { background: #0C1525; border: 1px solid #1A2840; border-radius: 16px; padding: 22px 24px; height: 100%; }
.kpi-icon { font-size: 1.4rem; margin-bottom: 10px; }
.kpi-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: #4B6280; margin-bottom: 6px; }
.kpi-val { font-size: 2rem; font-weight: 800; color: #F1F5F9; line-height: 1; margin-bottom: 6px; }
.kpi-sub { font-size: 0.78rem; color: #4B6280; }
.kpi-pos { color: #10B981; font-size: 0.78rem; font-weight: 600; }
.kpi-neg { color: #EF4444; font-size: 0.78rem; font-weight: 600; }

/* ── Streamlit metric overrides ── */
[data-testid="stMetric"] {
    background: #0C1525;
    border: 1px solid #1A2840;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetricLabel"] p { color: #4B6280 !important; font-size: 0.75rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.07em; }
[data-testid="stMetricValue"] { color: #F1F5F9 !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #00C9B8, #1D4ED8);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.6rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: opacity 0.18s, transform 0.12s;
}
.stButton > button:hover { opacity: 0.88; transform: translateY(-1px); }
.stButton > button:active { transform: translateY(0); }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #0C1525;
    border: 2px dashed #1A2840;
    border-radius: 14px;
    padding: 0.8rem;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #0C1525 !important;
    border: 1px solid #1A2840 !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: #CBD5E1 !important; }

/* Suppress raw "keyboard_arrow_right" text when Material Icons font is unavailable.
   Set font-size:0 so the text takes no space; use ::before to render a plain Unicode arrow. */
[data-testid="stExpander"] summary span.material-icons,
[data-testid="stExpander"] summary span[class*="material"] {
    font-size: 0 !important;
    color: transparent !important;
    width: 18px !important;
    min-width: 18px !important;
    display: inline-flex !important;
    align-items: center !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary span.material-icons::before,
[data-testid="stExpander"] summary span[class*="material"]::before {
    content: "▶";
    font-size: 11px !important;
    color: #4B6280 !important;
    font-family: sans-serif !important;
    display: inline-block !important;
    transition: transform 0.2s ease !important;
}
[data-testid="stExpander"] details[open] summary span.material-icons::before,
[data-testid="stExpander"] details[open] summary span[class*="material"]::before {
    transform: rotate(90deg) !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input {
    background: #0C1525 !important;
    border: 1px solid #1A2840 !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

/* ── Alerts ── */
.info-box {
    background: rgba(0,201,184,0.06);
    border: 1px solid rgba(0,201,184,0.18);
    border-radius: 10px;
    padding: 14px 18px;
    color: #94A3B8;
    font-size: 0.87rem;
    line-height: 1.6;
    margin: 0.5rem 0;
}
.warn-box {
    background: rgba(245,158,11,0.07);
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 10px;
    padding: 14px 18px;
    color: #94A3B8;
    font-size: 0.87rem;
}

/* ── Section headings ── */
.sec-head { font-size: 1rem; font-weight: 700; color: #CBD5E1; margin: 0 0 2px 0; }
.sec-sub  { font-size: 0.81rem; color: #4B6280; margin: 0 0 14px 0; }

/* ── Tip cards ── */
.tip {
    background: rgba(29,78,216,0.08);
    border: 1px solid rgba(29,78,216,0.2);
    border-left: 3px solid #1D4ED8;
    border-radius: 10px;
    padding: 11px 15px;
    margin-bottom: 9px;
    font-size: 0.86rem;
    color: #CBD5E1;
    line-height: 1.55;
}

/* ── Coming-soon block ── */
.coming {
    background: #0C1525;
    border: 1px solid #1A2840;
    border-radius: 20px;
    padding: 72px 40px;
    text-align: center;
}
.coming-icon  { font-size: 3rem; margin-bottom: 16px; }
.coming-title { font-size: 1.4rem; font-weight: 700; color: #CBD5E1; margin-bottom: 8px; }
.coming-sub   { color: #4B6280; font-size: 0.88rem; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #060B17; }
::-webkit-scrollbar-thumb { background: #1A2840; border-radius: 4px; }


/* ── Hero ── */
.hero {
    background: linear-gradient(140deg, #060B17 0%, #09132B 45%, #061820 100%);
    border: 1px solid #1A2840;
    border-radius: 22px;
    padding: 54px 52px 54px 52px;
    position: relative;
    overflow: hidden;
    margin-bottom: 1.6rem;
}
.hero-glow-a {
    position: absolute; top: -120px; right: -100px;
    width: 480px; height: 480px;
    background: radial-gradient(circle, rgba(0,201,184,0.13) 0%, transparent 65%);
    border-radius: 50%; pointer-events: none;
}
.hero-glow-b {
    position: absolute; bottom: -140px; left: 28%;
    width: 380px; height: 380px;
    background: radial-gradient(circle, rgba(29,78,216,0.11) 0%, transparent 65%);
    border-radius: 50%; pointer-events: none;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: rgba(0,201,184,0.1); border: 1px solid rgba(0,201,184,0.28);
    color: #00C9B8; font-size: 0.75rem; font-weight: 700;
    letter-spacing: 0.06em; padding: 5px 14px; border-radius: 999px; margin-bottom: 20px;
}
.hero-title {
    font-size: 3rem; font-weight: 800; line-height: 1.1;
    color: #F1F5F9; margin: 0 0 16px 0;
}
.hero-title span { color: #00C9B8; }
.hero-sub {
    font-size: 1rem; color: #64748B; margin-bottom: 34px;
    line-height: 1.65; max-width: 500px;
}
.hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.hero-stat-val   { display: block; font-size: 1.5rem; font-weight: 800; color: #F1F5F9; }
.hero-stat-label { display: block; font-size: 0.72rem; color: #4B6280; margin-top: 2px; font-weight: 500; }
.hero-sep { color: #1A2840; font-size: 2rem; align-self: center; }
</style>
""", unsafe_allow_html=True)

# ─── LIGHTNING BOLT SVG ────────────────────────────────────────────────────────

_BOLT = """
<svg width="190" height="250" viewBox="0 0 190 250" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="95" cy="125" r="95" fill="url(#rg)" opacity="0.18"/>
  <path d="M112 12L44 135H92L64 238L152 98H104L112 12Z" fill="url(#lg)" filter="url(#gf)" opacity="0.55"/>
  <path d="M112 12L44 135H92L64 238L152 98H104L112 12Z" fill="url(#lg2)"/>
  <line x1="12" y1="70" x2="38" y2="70" stroke="#00C9B8" stroke-width="1.4" opacity="0.55"/>
  <line x1="38" y1="70" x2="38" y2="105" stroke="#00C9B8" stroke-width="1.4" opacity="0.55"/>
  <circle cx="38" cy="70" r="3" fill="#00C9B8" opacity="0.9"/>
  <circle cx="12" cy="70" r="2" fill="#00C9B8" opacity="0.35"/>
  <line x1="152" y1="165" x2="178" y2="165" stroke="#1D4ED8" stroke-width="1.4" opacity="0.55"/>
  <line x1="152" y1="165" x2="152" y2="130" stroke="#1D4ED8" stroke-width="1.4" opacity="0.55"/>
  <circle cx="152" cy="165" r="3" fill="#1D4ED8" opacity="0.9"/>
  <circle cx="178" cy="165" r="2" fill="#1D4ED8" opacity="0.35"/>
  <circle cx="20"  cy="185" r="2.5" fill="#00C9B8" opacity="0.2"/>
  <circle cx="170" cy="42"  r="2.5" fill="#00C9B8" opacity="0.2"/>
  <circle cx="160" cy="210" r="2"   fill="#1D4ED8" opacity="0.2"/>
  <circle cx="28"  cy="40"  r="1.8" fill="#1D4ED8" opacity="0.2"/>
  <defs>
    <radialGradient id="rg" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="#00C9B8"/>
      <stop offset="100%" stop-color="#1D4ED8" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="lg" x1="0%" y1="0%" x2="70%" y2="100%">
      <stop offset="0%"   stop-color="#00C9B8"/>
      <stop offset="100%" stop-color="#1D4ED8"/>
    </linearGradient>
    <linearGradient id="lg2" x1="0%" y1="0%" x2="60%" y2="100%">
      <stop offset="0%"   stop-color="#14F1DF" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.8"/>
    </linearGradient>
    <filter id="gf" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="9" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
</svg>
"""

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _auth_headers() -> dict:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _get(path: str, timeout: int = 4):
    try:
        r = requests.get(f"{_api_url()}{path}", headers=_auth_headers(), timeout=timeout)
        if r.status_code == 401:
            return None, "unauthorized"
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "offline"
    except Exception as e:
        return None, str(e)


def _chart_layout(height: int = 260, margin_top: int = 10) -> dict:
    return dict(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#4B6280", size=11),
        margin=dict(l=0, r=0, t=margin_top, b=0),
        height=height,
        showlegend=False,
        xaxis=dict(gridcolor="#12202E", linecolor="#12202E", zeroline=False),
        yaxis=dict(gridcolor="#12202E", linecolor="#12202E", zeroline=False),
    )


def _offline_banner():
    st.markdown(
        '<div class="warn-box">⚠️ Backend offline — run: '
        '<code>uvicorn backend.app:app --reload --port 8000</code></div>',
        unsafe_allow_html=True,
    )


# ─── AUTH: handle Google callback token ───────────────────────────────────────
_params = st.query_params
if "token" in _params:
    st.session_state["token"] = _params["token"]
    st.query_params.clear()
    st.rerun()

# Force-clear any legacy/fake tokens immediately
if st.session_state.get("token") == "no-auth":
    st.session_state.pop("token", None)
    st.rerun()

# Validate real tokens against backend — clear if expired/invalid
if st.session_state.get("token"):
    _check, _cerr = _get("/auth/me", timeout=3)
    if _cerr == "unauthorized":
        st.session_state.pop("token", None)
        st.session_state.pop("me", None)
        st.rerun()



# ─── LOGIN PAGE ────────────────────────────────────────────────────────────────

_GOOGLE_ICON = (
    '<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" '
    'style="vertical-align:middle;margin-right:10px;flex-shrink:0;">'
    '<path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078'
    '-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>'
    '<path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86'
    '-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/>'
    '<path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71 0-.593.102-1.17.282-1.71V4.958H.957'
    'C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>'
    '<path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0'
    ' 5.482 0 2.438 2.017.957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>'
    '</svg>'
)


_ENERGY_SVG = """
<svg viewBox="0 0 420 540" fill="none" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;display:block;">
  <defs>
    <linearGradient id="boltG" x1="0%" y1="0%" x2="60%" y2="100%">
      <stop offset="0%" stop-color="#14F1DF"/>
      <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.75"/>
    </linearGradient>
    <radialGradient id="tealGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00C9B8" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#00C9B8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="blueGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1D4ED8" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#1D4ED8" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow3">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow7">
      <feGaussianBlur stdDeviation="7" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Ambient glows -->
  <ellipse cx="210" cy="100" rx="160" ry="120" fill="url(#tealGlow)"/>
  <ellipse cx="60"  cy="460" rx="120" ry="100" fill="url(#blueGlow)"/>
  <ellipse cx="380" cy="350" rx="100" ry="90"  fill="url(#tealGlow)"/>

  <!-- Grid lines -->
  <line x1="0" y1="135" x2="420" y2="135" stroke="#1A2840" stroke-width="0.6" stroke-dasharray="5 10" opacity="0.7"/>
  <line x1="0" y1="270" x2="420" y2="270" stroke="#1A2840" stroke-width="0.6" stroke-dasharray="5 10" opacity="0.7"/>
  <line x1="0" y1="405" x2="420" y2="405" stroke="#1A2840" stroke-width="0.6" stroke-dasharray="5 10" opacity="0.7"/>
  <line x1="105" y1="0" x2="105" y2="540" stroke="#1A2840" stroke-width="0.6" stroke-dasharray="5 10" opacity="0.7"/>
  <line x1="210" y1="0" x2="210" y2="540" stroke="#1A2840" stroke-width="0.6" stroke-dasharray="5 10" opacity="0.7"/>
  <line x1="315" y1="0" x2="315" y2="540" stroke="#1A2840" stroke-width="0.6" stroke-dasharray="5 10" opacity="0.7"/>

  <!-- City skyline -->
  <rect x="0"   y="420" width="45" height="120" rx="2" fill="#0B1322"/>
  <rect x="12"  y="395" width="22" height="145" rx="2" fill="#0D1728"/>
  <rect x="48"  y="430" width="38" height="110" rx="2" fill="#0B1322"/>
  <rect x="90"  y="408" width="30" height="132" rx="2" fill="#0D1728"/>
  <rect x="125" y="438" width="22" height="102" rx="2" fill="#0B1322"/>
  <rect x="290" y="415" width="40" height="125" rx="2" fill="#0B1322"/>
  <rect x="335" y="395" width="26" height="145" rx="2" fill="#0D1728"/>
  <rect x="365" y="425" width="55" height="115" rx="2" fill="#0B1322"/>

  <!-- Building windows -->
  <rect x="16"  y="405" width="7" height="5" rx="1" fill="rgba(0,201,184,0.35)"/>
  <rect x="27"  y="405" width="7" height="5" rx="1" fill="rgba(29,78,216,0.3)"/>
  <rect x="16"  y="418" width="7" height="5" rx="1" fill="rgba(0,201,184,0.2)"/>
  <rect x="27"  y="418" width="7" height="5" rx="1" fill="rgba(0,201,184,0.35)"/>
  <rect x="97"  y="418" width="7" height="5" rx="1" fill="rgba(29,78,216,0.35)"/>
  <rect x="109" y="418" width="7" height="5" rx="1" fill="rgba(0,201,184,0.25)"/>
  <rect x="340" y="405" width="7" height="5" rx="1" fill="rgba(0,201,184,0.3)"/>
  <rect x="352" y="405" width="7" height="5" rx="1" fill="rgba(29,78,216,0.35)"/>
  <rect x="340" y="420" width="7" height="5" rx="1" fill="rgba(0,201,184,0.2)"/>
  <rect x="375" y="435" width="7" height="5" rx="1" fill="rgba(0,201,184,0.35)"/>
  <rect x="388" y="435" width="7" height="5" rx="1" fill="rgba(29,78,216,0.3)"/>

  <!-- Power tower LEFT -->
  <line x1="72" y1="168" x2="72" y2="410" stroke="#1E3A5F" stroke-width="2.5"/>
  <line x1="44" y1="198" x2="100" y2="198" stroke="#1E3A5F" stroke-width="2"/>
  <line x1="50" y1="238" x2="94"  y2="238" stroke="#1E3A5F" stroke-width="1.8"/>
  <line x1="56" y1="272" x2="88"  y2="272" stroke="#1E3A5F" stroke-width="1.5"/>
  <line x1="62" y1="168" x2="72"  y2="198" stroke="#1E3A5F" stroke-width="1.2"/>
  <line x1="82" y1="168" x2="72"  y2="198" stroke="#1E3A5F" stroke-width="1.2"/>
  <circle cx="44"  cy="198" r="3.5" fill="#1D4ED8" opacity="0.8"/>
  <circle cx="100" cy="198" r="3.5" fill="#1D4ED8" opacity="0.8"/>
  <circle cx="50"  cy="238" r="2.5" fill="#00C9B8" opacity="0.6"/>
  <circle cx="94"  cy="238" r="2.5" fill="#00C9B8" opacity="0.6"/>

  <!-- Power tower RIGHT -->
  <line x1="348" y1="148" x2="348" y2="395" stroke="#1E3A5F" stroke-width="2.5"/>
  <line x1="320" y1="178" x2="376" y2="178" stroke="#1E3A5F" stroke-width="2"/>
  <line x1="326" y1="218" x2="370" y2="218" stroke="#1E3A5F" stroke-width="1.8"/>
  <line x1="332" y1="252" x2="364" y2="252" stroke="#1E3A5F" stroke-width="1.5"/>
  <line x1="338" y1="148" x2="348" y2="178" stroke="#1E3A5F" stroke-width="1.2"/>
  <line x1="358" y1="148" x2="348" y2="178" stroke="#1E3A5F" stroke-width="1.2"/>
  <circle cx="320" cy="178" r="3.5" fill="#1D4ED8" opacity="0.8"/>
  <circle cx="376" cy="178" r="3.5" fill="#1D4ED8" opacity="0.8"/>
  <circle cx="326" cy="218" r="2.5" fill="#00C9B8" opacity="0.6"/>
  <circle cx="370" cy="218" r="2.5" fill="#00C9B8" opacity="0.6"/>

  <!-- Power lines (catenary curves) -->
  <path d="M44 198 Q210 172 320 178" stroke="#00C9B8" stroke-width="1.6" fill="none" opacity="0.55"/>
  <path d="M100 198 Q210 176 376 178" stroke="#00C9B8" stroke-width="1.2" fill="none" opacity="0.35"/>
  <path d="M50 238 Q210 216 326 218" stroke="#1D4ED8" stroke-width="1.2" fill="none" opacity="0.4"/>
  <path d="M94 238 Q210 220 370 218" stroke="#1D4ED8" stroke-width="0.9" fill="none" opacity="0.25"/>

  <!-- Animated energy pulse on main line -->
  <circle r="5" fill="#00C9B8" opacity="0.9" filter="url(#glow3)">
    <animateMotion dur="3s" repeatCount="indefinite"
      path="M44 198 Q210 172 320 178"/>
  </circle>
  <circle r="4" fill="#14F1DF" opacity="0.7" filter="url(#glow3)">
    <animateMotion dur="3s" begin="1.5s" repeatCount="indefinite"
      path="M44 198 Q210 172 320 178"/>
  </circle>
  <circle r="3.5" fill="#3B82F6" opacity="0.8" filter="url(#glow3)">
    <animateMotion dur="4s" repeatCount="indefinite"
      path="M50 238 Q210 216 326 218"/>
  </circle>

  <!-- Wind turbine 1 -->
  <line x1="158" y1="345" x2="158" y2="415" stroke="#1E3A5F" stroke-width="3"/>
  <rect x="150" y="412" width="16" height="5" rx="2" fill="#1A2840"/>
  <circle cx="158" cy="340" r="5" fill="#1D4ED8" opacity="0.85" filter="url(#glow3)"/>
  <g transform-origin="158 340">
    <line x1="158" y1="340" x2="158" y2="298" stroke="#00C9B8" stroke-width="2.2" stroke-linecap="round" opacity="0.85"/>
    <line x1="158" y1="340" x2="122" y2="361" stroke="#00C9B8" stroke-width="2.2" stroke-linecap="round" opacity="0.85"/>
    <line x1="158" y1="340" x2="194" y2="361" stroke="#00C9B8" stroke-width="2.2" stroke-linecap="round" opacity="0.85"/>
    <animateTransform attributeName="transform" type="rotate"
      from="0 158 340" to="360 158 340" dur="6s" repeatCount="indefinite"/>
  </g>

  <!-- Wind turbine 2 (smaller) -->
  <line x1="258" y1="362" x2="258" y2="415" stroke="#1E3A5F" stroke-width="2.5"/>
  <rect x="251" y="412" width="14" height="4" rx="2" fill="#1A2840"/>
  <circle cx="258" cy="357" r="4" fill="#1D4ED8" opacity="0.8" filter="url(#glow3)"/>
  <g transform-origin="258 357">
    <line x1="258" y1="357" x2="258" y2="323" stroke="#00C9B8" stroke-width="1.8" stroke-linecap="round" opacity="0.75"/>
    <line x1="258" y1="357" x2="229" y2="374" stroke="#00C9B8" stroke-width="1.8" stroke-linecap="round" opacity="0.75"/>
    <line x1="258" y1="357" x2="287" y2="374" stroke="#00C9B8" stroke-width="1.8" stroke-linecap="round" opacity="0.75"/>
    <animateTransform attributeName="transform" type="rotate"
      from="120 258 357" to="480 258 357" dur="5s" repeatCount="indefinite"/>
  </g>

  <!-- Solar panel array -->
  <g opacity="0.85">
    <rect x="175" y="405" width="22" height="12" rx="1.5" fill="#0D1A30" stroke="#1D4ED8" stroke-width="1"/>
    <line x1="175" y1="411" x2="197" y2="411" stroke="#1D4ED8" stroke-width="0.5" opacity="0.6"/>
    <line x1="186" y1="405" x2="186" y2="417" stroke="#1D4ED8" stroke-width="0.5" opacity="0.6"/>
    <rect x="200" y="405" width="22" height="12" rx="1.5" fill="#0D1A30" stroke="#1D4ED8" stroke-width="1"/>
    <line x1="200" y1="411" x2="222" y2="411" stroke="#1D4ED8" stroke-width="0.5" opacity="0.6"/>
    <line x1="211" y1="405" x2="211" y2="417" stroke="#1D4ED8" stroke-width="0.5" opacity="0.6"/>
    <rect x="225" y="405" width="22" height="12" rx="1.5" fill="#0D1A30" stroke="#1D4ED8" stroke-width="1"/>
    <line x1="225" y1="411" x2="247" y2="411" stroke="#1D4ED8" stroke-width="0.5" opacity="0.6"/>
    <line x1="236" y1="405" x2="236" y2="417" stroke="#1D4ED8" stroke-width="0.5" opacity="0.6"/>
    <!-- Solar shine pulse -->
    <rect x="175" y="405" width="72" height="12" rx="1.5" fill="rgba(29,78,216,0.08)" opacity="0">
      <animate attributeName="opacity" values="0;0.5;0" dur="3s" repeatCount="indefinite"/>
    </rect>
  </g>
  <!-- Solar connections -->
  <line x1="211" y1="405" x2="211" y2="390" stroke="#1D4ED8" stroke-width="1" opacity="0.4"/>
  <line x1="158" y1="390" x2="258" y2="390" stroke="#1D4ED8" stroke-width="0.8" stroke-dasharray="3 5" opacity="0.35"/>

  <!-- Central lightning bolt (hero element) -->
  <path d="M225 28 L186 108 H214 L178 192 L238 94 H210 L250 28 Z"
        fill="url(#boltG)" filter="url(#glow7)" opacity="0.9"/>
  <!-- Bolt glow ring -->
  <circle cx="214" cy="110" r="38" fill="none" stroke="#00C9B8" stroke-width="1" opacity="0.2">
    <animate attributeName="r" values="38;52;38" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.2;0.05;0.2" dur="3s" repeatCount="indefinite"/>
  </circle>
  <circle cx="214" cy="110" r="22" fill="none" stroke="#00C9B8" stroke-width="1.5" opacity="0.35">
    <animate attributeName="r" values="22;32;22" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.35;0.1;0.35" dur="3s" repeatCount="indefinite"/>
  </circle>

  <!-- Connection lines from bolt to towers -->
  <line x1="195" y1="145" x2="72"  y2="198" stroke="#00C9B8" stroke-width="1" stroke-dasharray="5 7" opacity="0.3"/>
  <line x1="233" y1="145" x2="348" y2="178" stroke="#00C9B8" stroke-width="1" stroke-dasharray="5 7" opacity="0.3"/>
  <line x1="214" y1="148" x2="158" y2="345" stroke="#1D4ED8" stroke-width="0.8" stroke-dasharray="4 8" opacity="0.25"/>

  <!-- Floating data nodes -->
  <circle cx="72"  cy="168" r="5" fill="#00C9B8" opacity="0.85" filter="url(#glow3)"/>
  <circle cx="348" cy="148" r="5" fill="#1D4ED8" opacity="0.85" filter="url(#glow3)"/>
  <circle cx="158" cy="390" r="4" fill="#00C9B8" opacity="0.7"  filter="url(#glow3)"/>
  <circle cx="258" cy="390" r="4" fill="#1D4ED8" opacity="0.7"  filter="url(#glow3)"/>

  <!-- Decorative small dots -->
  <circle cx="28"  cy="320" r="2"   fill="#00C9B8" opacity="0.25"/>
  <circle cx="395" cy="280" r="2"   fill="#1D4ED8" opacity="0.3"/>
  <circle cx="175" cy="290" r="1.5" fill="#00C9B8" opacity="0.2"/>
  <circle cx="310" cy="310" r="1.5" fill="#00C9B8" opacity="0.2"/>
  <circle cx="38"  cy="190" r="1.5" fill="#1D4ED8" opacity="0.25"/>
  <circle cx="390" cy="130" r="2"   fill="#00C9B8" opacity="0.2"/>

  <!-- Stars / background sparkles -->
  <circle cx="50"  cy="45"  r="1.2" fill="#94A3B8" opacity="0.4"/>
  <circle cx="132" cy="22"  r="1"   fill="#94A3B8" opacity="0.3"/>
  <circle cx="290" cy="50"  r="1.2" fill="#94A3B8" opacity="0.35"/>
  <circle cx="378" cy="30"  r="1"   fill="#94A3B8" opacity="0.3"/>
  <circle cx="400" cy="80"  r="1.5" fill="#94A3B8" opacity="0.25"/>
  <circle cx="20"  cy="110" r="1"   fill="#94A3B8" opacity="0.3"/>
</svg>
"""


def page_login():
    auth_data, err = _get("/auth/google")
    url = auth_data.get("url") if auth_data else None

    if err == "offline":
        auth_block = (
            '<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);'
            'border-radius:12px;padding:14px;color:#EF4444;font-size:0.85rem;text-align:center;margin-bottom:12px;">'
            '&#9888; Backend offline &#8212; start the FastAPI server first.</div>'
        )
    elif url:
        _btn_base = (
            'display:flex;align-items:center;justify-content:center;gap:10px;'
            'width:100%;border-radius:12px;padding:13px 20px;'
            'font-size:0.9rem;font-weight:600;text-decoration:none;cursor:pointer;'
            'transition:opacity 0.15s,box-shadow 0.15s;'
        )
        signin_btn = (
            '<a href="' + url + '" target="_self" style="'
            + _btn_base +
            'background:#ffffff;color:#1f1f1f;border:1px solid #e0e0e0;'
            'box-shadow:0 2px 8px rgba(0,0,0,0.25);">'
            + _GOOGLE_ICON + 'Sign in with Google</a>'
        )
        signup_btn = (
            '<a href="' + url + '" target="_self" style="'
            + _btn_base +
            'background:linear-gradient(135deg,rgba(0,201,184,0.12),rgba(29,78,216,0.12));'
            'color:#CBD5E1;border:1px solid rgba(0,201,184,0.3);">'
            + _GOOGLE_ICON + 'Create free account</a>'
        )
        auth_block = (
            # Sign in row
            '<p style="color:#64748B;font-size:0.75rem;font-weight:600;'
            'letter-spacing:0.06em;text-transform:uppercase;margin:0 0 10px;">Welcome back</p>'
            + signin_btn +
            # Divider
            '<div style="display:flex;align-items:center;gap:12px;margin:18px 0;">'
            '<div style="flex:1;height:1px;background:#1A2840;"></div>'
            '<span style="color:#2D3F55;font-size:0.75rem;">New here?</span>'
            '<div style="flex:1;height:1px;background:#1A2840;"></div>'
            '</div>'
            # Sign up row
            '<p style="color:#64748B;font-size:0.75rem;font-weight:600;'
            'letter-spacing:0.06em;text-transform:uppercase;margin:0 0 10px;">Create account</p>'
            + signup_btn +
            '<p style="color:#2D3F55;font-size:0.71rem;margin-top:10px;text-align:center;">'
            'Free forever &nbsp;&#183;&nbsp; No credit card &nbsp;&#183;&nbsp; UK bills only</p>'
        )
    else:
        auth_block = '<div style="color:#4B6280;font-size:0.85rem;text-align:center;">Could not load sign-in.</div>'

    st.markdown(
        # ── Animated background ──────────────────────────────────────────
        '<style>'
        '@keyframes pulse-glow{'
        '0%,100%{opacity:0.5;transform:scale(1);}'
        '50%{opacity:0.8;transform:scale(1.04);}'
        '}'
        '.login-glow-a{animation:pulse-glow 6s ease-in-out infinite;}'
        '.login-glow-b{animation:pulse-glow 8s ease-in-out 2s infinite;}'
        '</style>'

        '<div style="position:fixed;inset:0;background:#060B17;z-index:0;overflow:hidden;">'
        # Glow blobs
        '<div class="login-glow-a" style="position:absolute;top:-15%;left:-10%;'
        'width:55%;height:55%;border-radius:50%;pointer-events:none;'
        'background:radial-gradient(circle,rgba(0,201,184,0.07) 0%,transparent 70%);"></div>'
        '<div class="login-glow-b" style="position:absolute;bottom:-15%;right:-10%;'
        'width:55%;height:55%;border-radius:50%;pointer-events:none;'
        'background:radial-gradient(circle,rgba(29,78,216,0.07) 0%,transparent 70%);"></div>'
        # Subtle dot grid
        '<div style="position:absolute;inset:0;pointer-events:none;'
        'background-image:radial-gradient(circle,#1A2840 1px,transparent 1px);'
        'background-size:32px 32px;opacity:0.35;"></div>'
        '</div>'

        # ── Outer wrapper ────────────────────────────────────────────────
        '<div style="position:fixed;inset:0;z-index:1;display:flex;align-items:center;'
        'justify-content:center;padding:1rem;overflow-y:auto;">'

        # ── Split card ──────────────────────────────────────────────────
        '<div style="display:flex;width:100%;max-width:940px;'
        'background:#0C1525;border:1px solid #1A2840;border-radius:26px;'
        'overflow:hidden;box-shadow:0 0 0 1px rgba(0,201,184,0.05),'
        '0 30px 80px rgba(0,0,0,0.55);">'

        # ── LEFT PANEL: marketing content ───────────────────────────────
        '<div style="flex:1;min-width:0;padding:28px 28px;overflow-y:auto;'
        'background:linear-gradient(155deg,#080E1E 0%,#091428 55%,#070E1C 100%);'
        'border-right:1px solid #1A2840;display:flex;flex-direction:column;gap:20px;">'

        # Badge + Hero
        '<div>'
        '<div style="display:inline-flex;align-items:center;gap:7px;'
        'background:rgba(0,201,184,0.09);border:1px solid rgba(0,201,184,0.25);'
        'color:#00C9B8;font-size:0.7rem;font-weight:700;letter-spacing:0.07em;'
        'padding:5px 13px;border-radius:999px;margin-bottom:14px;">&#9889; AI-POWERED · UK ENERGY</div>'
        '<h2 style="font-size:1.55rem;font-weight:800;color:#F1F5F9;margin:0 0 10px;line-height:1.25;">'
        'Stop overpaying for energy.<br/><span style="color:#00C9B8;">Let AI show you how.</span></h2>'
        '<p style="color:#64748B;font-size:0.82rem;line-height:1.75;margin:0;">'
        'Upload your UK electricity or gas bills as PDF, JPG, or PNG. '
        'OCR extracts all the data instantly &#8212; then ML models analyse your usage, '
        'predict next month&#8217;s cost, and give you personalised savings tips.</p>'
        '</div>'

        # Energy SVG (smaller)
        '<div style="display:flex;align-items:center;justify-content:center;'
        'max-height:200px;overflow:hidden;opacity:0.9;">'
        + _ENERGY_SVG +
        '</div>'

        # How it works steps
        '<div>'
        '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.09em;'
        'text-transform:uppercase;color:#2D3F55;margin-bottom:10px;">How it works</div>'
        '<div style="display:flex;flex-direction:column;gap:8px;">'

        '<div style="display:flex;align-items:flex-start;gap:12px;">'
        '<div style="width:26px;height:26px;border-radius:50%;flex-shrink:0;'
        'background:linear-gradient(135deg,#00C9B8,#0891b2);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:0.7rem;font-weight:800;color:#fff;">1</div>'
        '<div><div style="font-size:0.82rem;font-weight:600;color:#CBD5E1;">Upload your bill</div>'
        '<div style="font-size:0.75rem;color:#4B6280;line-height:1.5;">PDF, JPG or PNG from any UK provider</div></div>'
        '</div>'

        '<div style="display:flex;align-items:flex-start;gap:12px;">'
        '<div style="width:26px;height:26px;border-radius:50%;flex-shrink:0;'
        'background:linear-gradient(135deg,#1D4ED8,#7C3AED);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:0.7rem;font-weight:800;color:#fff;">2</div>'
        '<div><div style="font-size:0.82rem;font-weight:600;color:#CBD5E1;">AI extracts the data</div>'
        '<div style="font-size:0.75rem;color:#4B6280;line-height:1.5;">OCR + smart parsers pull kWh, cost, rates &amp; dates</div></div>'
        '</div>'

        '<div style="display:flex;align-items:flex-start;gap:12px;">'
        '<div style="width:26px;height:26px;border-radius:50%;flex-shrink:0;'
        'background:linear-gradient(135deg,#10B981,#059669);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:0.7rem;font-weight:800;color:#fff;">3</div>'
        '<div><div style="font-size:0.82rem;font-weight:600;color:#CBD5E1;">Get ML insights &amp; savings tips</div>'
        '<div style="font-size:0.75rem;color:#4B6280;line-height:1.5;">Forecasts, anomaly detection, carbon tracking</div></div>'
        '</div>'

        '</div>'
        '</div>'

        # Feature pills row
        '<div style="display:flex;flex-wrap:wrap;gap:6px;">'
        '<span style="background:rgba(0,201,184,0.07);border:1px solid rgba(0,201,184,0.2);'
        'color:#00C9B8;font-size:0.68rem;padding:4px 10px;border-radius:999px;">&#128202; Prophet Forecasting</span>'
        '<span style="background:rgba(29,78,216,0.07);border:1px solid rgba(29,78,216,0.2);'
        'color:#60A5FA;font-size:0.68rem;padding:4px 10px;border-radius:999px;">&#129302; Anomaly Detection</span>'
        '<span style="background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.2);'
        'color:#34D399;font-size:0.68rem;padding:4px 10px;border-radius:999px;">&#127807; CO&#8322; Tracking</span>'
        '<span style="background:rgba(139,92,246,0.07);border:1px solid rgba(139,92,246,0.2);'
        'color:#A78BFA;font-size:0.68rem;padding:4px 10px;border-radius:999px;">&#128200; Budget Alerts</span>'
        '<span style="background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);'
        'color:#FCD34D;font-size:0.68rem;padding:4px 10px;border-radius:999px;">&#128240; PDF Reports</span>'
        '<span style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);'
        'color:#FCA5A5;font-size:0.68rem;padding:4px 10px;border-radius:999px;">&#128680; Email Alerts</span>'
        '</div>'

        # Stats row
        '<div style="display:flex;gap:0;border:1px solid #1A2840;border-radius:14px;overflow:hidden;">'
        '<div style="flex:1;padding:12px 0;text-align:center;border-right:1px solid #1A2840;">'
        '<div style="font-size:1.1rem;font-weight:800;color:#F1F5F9;">9</div>'
        '<div style="font-size:0.67rem;color:#4B6280;margin-top:2px;">UK Providers</div></div>'
        '<div style="flex:1;padding:12px 0;text-align:center;border-right:1px solid #1A2840;">'
        '<div style="font-size:1.1rem;font-weight:800;color:#F1F5F9;">5+</div>'
        '<div style="font-size:0.67rem;color:#4B6280;margin-top:2px;">ML Models</div></div>'
        '<div style="flex:1;padding:12px 0;text-align:center;border-right:1px solid #1A2840;">'
        '<div style="font-size:1.1rem;font-weight:800;color:#F1F5F9;">71</div>'
        '<div style="font-size:0.67rem;color:#4B6280;margin-top:2px;">Tests Passing</div></div>'
        '<div style="flex:1;padding:12px 0;text-align:center;">'
        '<div style="font-size:1.1rem;font-weight:800;color:#00C9B8;">Free</div>'
        '<div style="font-size:0.67rem;color:#4B6280;margin-top:2px;">Always</div></div>'
        '</div>'

        '</div>'  # end left panel

        # ── RIGHT PANEL: auth ────────────────────────────────────────────
        '<div style="width:360px;flex-shrink:0;padding:32px 32px;'
        'display:flex;flex-direction:column;justify-content:center;">'

        # Icon + title
        '<div style="width:52px;height:52px;margin:0 auto 14px;'
        'background:linear-gradient(135deg,rgba(0,201,184,0.15),rgba(29,78,216,0.15));'
        'border:1px solid rgba(0,201,184,0.25);border-radius:14px;'
        'display:flex;align-items:center;justify-content:center;font-size:1.5rem;">&#9889;</div>'
        '<h1 style="font-size:1.3rem;font-weight:800;color:#F1F5F9;text-align:center;margin:0 0 6px;">'
        'Smart Energy Auditor</h1>'
        '<p style="color:#4B6280;font-size:0.8rem;text-align:center;line-height:1.5;margin:0 0 18px;">'
        'Analyse your UK energy bills with AI</p>'

        # Feature pills
        '<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:18px;">'
        '<span style="background:rgba(0,201,184,0.08);border:1px solid rgba(0,201,184,0.2);'
        'color:#00C9B8;font-size:0.68rem;padding:3px 10px;border-radius:999px;">&#9889; OCR</span>'
        '<span style="background:rgba(29,78,216,0.08);border:1px solid rgba(29,78,216,0.2);'
        'color:#60A5FA;font-size:0.68rem;padding:3px 10px;border-radius:999px;">&#128202; ML Insights</span>'
        '<span style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);'
        'color:#34D399;font-size:0.68rem;padding:3px 10px;border-radius:999px;">&#127807; Carbon</span>'
        '<span style="background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.2);'
        'color:#A78BFA;font-size:0.68rem;padding:3px 10px;border-radius:999px;">&#128274; Secure</span>'
        '</div>'

        # Divider
        '<div style="height:1px;background:#1A2840;margin-bottom:16px;"></div>'

        # Auth buttons block
        + auth_block +

        # Footer
        '<p style="color:#1E2D40;font-size:0.7rem;text-align:center;margin-top:20px;line-height:1.6;">'
        'By signing in you agree to our terms.<br/>Your data is encrypted and private.</p>'

        '</div>'  # end right panel

        '</div>'  # end split card
        '</div>',  # end outer wrapper
        unsafe_allow_html=True,
    )


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────

_is_logged_in = bool(st.session_state.get("token"))

# Inject persistent JS hamburger toggle into parent page
if _is_logged_in:
    components.html(
        """<script>
        (function(){
            var doc  = window.parent.document;
            var win  = window.parent;

            /* ── detect sidebar state ── */
            function sidebarOpen(){
                var sb = doc.querySelector('[data-testid="stSidebar"]');
                if(!sb) return false;
                var cs = win.getComputedStyle(sb);
                if(cs.display === 'none' || cs.visibility === 'hidden') return false;
                var tx = cs.transform || '';
                if(tx && tx !== 'none'){
                    var m = tx.match(/matrix\([^,]+,[^,]+,[^,]+,[^,]+,\s*([^,]+),/);
                    if(m && parseFloat(m[1]) < -30) return false;
                }
                /* also check collapsed control visibility as a fallback */
                var cc = doc.querySelector('[data-testid="stSidebarCollapsedControl"]');
                if(cc && win.getComputedStyle(cc).display !== 'none' && cc.offsetWidth > 5) return false;
                return true;
            }

            /* ── click whichever native button exists (works even when 1px/opacity:0) ── */
            function nativeClick(){
                var hits = [
                    '[data-testid="stSidebarCollapseButton"] button',
                    '[data-testid="stSidebarCollapsedControl"] button',
                    '[data-testid="collapsedControl"] button',
                    '[data-testid="stSidebarCollapseButton"]',
                    '[data-testid="stSidebarCollapsedControl"]',
                    '[data-testid="collapsedControl"]'
                ];
                for(var i=0;i<hits.length;i++){
                    var el = doc.querySelector(hits[i]);
                    if(el){ el.click(); return true; }
                }
                return false;
            }

            /* ── create our ☰ button once ── */
            function makeBtn(){
                if(doc.getElementById('_sea_ham')) return;
                var b = doc.createElement('button');
                b.id = '_sea_ham';
                b.title = 'Toggle sidebar';
                b.setAttribute('aria-label','Toggle sidebar');
                Object.assign(b.style,{
                    position:'fixed', top:'8px', zIndex:'2147483647',
                    width:'36px', height:'36px', padding:'0',
                    background:'#0C1525', borderRadius:'9px',
                    fontSize:'18px', cursor:'pointer', lineHeight:'1',
                    fontFamily:'sans-serif', transition:'all 0.15s',
                    display:'flex', alignItems:'center', justifyContent:'center',
                });
                b.onclick = function(){ nativeClick(); };
                b.onmouseenter = function(){
                    b.style.background='#0F1E35';
                    b.style.boxShadow='0 0 22px rgba(0,201,184,0.35)';
                };
                b.onmouseleave = function(){
                    b.style.background='#0C1525';
                    b.style.boxShadow= sidebarOpen()
                        ? '0 0 10px rgba(0,0,0,0.3)'
                        : '0 0 16px rgba(0,201,184,0.2)';
                };
                doc.body.appendChild(b);
            }

            /* ── update button appearance every 400ms ── */
            function tick(){
                makeBtn();
                var b = doc.getElementById('_sea_ham');
                if(!b) return;
                var open = sidebarOpen();
                /* position: inside sidebar (right-aligned) when open, else left edge */
                if(open){
                    b.innerHTML = '&#10005;';          /* ✕ */
                    b.style.left = '172px';
                    b.style.border = '1px solid #1A2840';
                    b.style.color  = '#64748B';
                    b.style.boxShadow = '0 0 10px rgba(0,0,0,0.3)';
                } else {
                    b.innerHTML = '&#9776;';           /* ☰ */
                    b.style.left = '10px';
                    b.style.border = '1px solid #00C9B8';
                    b.style.color  = '#00C9B8';
                    b.style.boxShadow = '0 0 16px rgba(0,201,184,0.2)';
                }
            }

            makeBtn();
            setInterval(tick, 400);
        })();
        </script>""",
        height=0,
        scrolling=False,
    )

# Hide sidebar and its toggle buttons on the login screen; reset block-container
if not _is_logged_in:
    st.session_state.pop("_sb_expanded", None)
    st.markdown(
        "<style>"
        "[data-testid='stSidebar'],"
        "[data-testid='stSidebarCollapseButton'],"
        "[data-testid='stSidebarCollapsedControl'],"
        "[data-testid='collapsedControl']"
        "{display:none!important;}"
        ".block-container{padding:0!important;max-width:100%!important;margin-top:0!important;}"
        "[data-testid='stMain']{padding:0!important;}"
        "</style>",
        unsafe_allow_html=True,
    )

# Fetch current user once and cache in session state to avoid repeated API calls
if _is_logged_in and "me" not in st.session_state:
    _me_data, _ = _get("/auth/me", timeout=3)
    st.session_state["me"] = _me_data or {}

_current_user = st.session_state.get("me", {}) if _is_logged_in else {}
_is_admin = _current_user.get("is_admin", False)

# Build nav items based on role
_nav_items  = ["Dashboard", "Upload Bill", "History", "Insights", "Alerts", "Profile", "Settings"]
_nav_icons  = ["speedometer2", "cloud-upload-fill", "clock-history", "graph-up-arrow", "bell-fill", "person-circle", "gear-fill"]
if _is_admin:
    _nav_items.append("Admin")
    _nav_icons.append("shield-lock-fill")

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:8px 0 16px;'>
        <div style='font-size:2.2rem; line-height:1;'>⚡</div>
        <div style='font-size:1.05rem; font-weight:800; color:#F1F5F9; margin-top:6px; letter-spacing:-0.02em;'>Smart Energy</div>
        <div style='font-size:0.72rem; color:#4B6280; margin-top:2px; letter-spacing:0.05em; text-transform:uppercase;'>Auditor</div>
    </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
        None,
        _nav_items,
        icons=_nav_icons,
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0"},
            "icon": {"color": "#4B6280", "font-size": "0.88rem"},
            "nav-link": {
                "font-size": "0.87rem", "color": "#64748B",
                "border-radius": "9px", "margin": "2px 0", "padding": "9px 13px",
            },
            "nav-link-selected": {
                "background-color": "rgba(0,201,184,0.1)",
                "color": "#00C9B8", "font-weight": "700",
            },
        },
    )

    st.markdown("<div style='margin-top:2rem;'>", unsafe_allow_html=True)

    # Live backend status pill
    _, _health_err = _get("/health", timeout=2)
    if _health_err == "offline":
        st.markdown("""<div style='background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
            border-radius:8px; padding:8px 12px; font-size:0.75rem; color:#EF4444; text-align:center;'>
            ● Backend offline</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style='background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2);
            border-radius:8px; padding:8px 12px; font-size:0.75rem; color:#10B981; text-align:center;'>
            ● Backend online</div>""", unsafe_allow_html=True)

    if _is_logged_in and _current_user:
        _display = _current_user.get("name") or _current_user.get("email", "User")
        _email   = _current_user.get("email", "")
        st.markdown(f"""<div style='margin-top:1.4rem; padding:10px 12px;
            background:#0A1220; border:1px solid #1A2840; border-radius:10px;'>
            <div style='font-size:0.78rem; font-weight:600; color:#CBD5E1;
                white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>
                {_display}</div>
            <div style='font-size:0.7rem; color:#4B6280; margin-top:2px;
                white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>
                {_email}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True, key="logout_btn"):
            st.session_state.pop("token", None)
            st.session_state.pop("me", None)
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ─── PAGE: DASHBOARD ───────────────────────────────────────────────────────────

def page_dashboard():
    with st.spinner("Loading your dashboard…"):
        stats, err   = _get("/stats")
        bills, _     = _get("/bills")
        recs, _      = _get("/ml/recommendations")
        upcoming, _  = _get("/alerts/upcoming-dues")
        goal, _      = _get("/goal")

    total_spend  = stats["total_spend"]       if stats else 0.0
    total_bills  = stats["total_bills"]       if stats else 0
    avg_kwh      = stats["avg_monthly_kwh"]   if stats else 0.0
    avg_cost     = stats["avg_monthly_cost"]  if stats else 0.0
    total_carbon = stats["total_carbon_kg"]   if stats else 0.0
    providers    = stats["providers"]          if stats else {}

    # ── Hero ──
    st.markdown(f"""
    <div class="hero">
        <div class="hero-glow-a"></div>
        <div class="hero-glow-b"></div>
        <div style="display:flex; align-items:center; justify-content:space-between; gap:24px;">
            <div style="flex:1; min-width:0;">
                <div class="hero-badge">⚡ AI-Powered Energy Analysis</div>
                <h1 class="hero-title">Know exactly where your<br/><span>energy money goes.</span></h1>
                <p class="hero-sub">Upload your UK electricity or gas bill. Our AI extracts usage,
                costs and carbon data in seconds — then shows you exactly how to save.</p>
                <div class="hero-stats">
                    <div>
                        <span class="hero-stat-val">£{total_spend:,.2f}</span>
                        <span class="hero-stat-label">Total spend tracked</span>
                    </div>
                    <span class="hero-sep">|</span>
                    <div>
                        <span class="hero-stat-val">{total_bills}</span>
                        <span class="hero-stat-label">Bills analysed</span>
                    </div>
                    <span class="hero-sep">|</span>
                    <div>
                        <span class="hero-stat-val">5+</span>
                        <span class="hero-stat-label">Providers supported</span>
                    </div>
                </div>
            </div>
            <div style="flex-shrink:0; opacity:0.92;">{_BOLT}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if err == "offline":
        _offline_banner()

    # ── Budget warning banner ──
    budget_status, _ = _get("/budget/status")
    if budget_status:
        _cost_st = budget_status.get("cost_status", "ok")
        _kwh_st  = budget_status.get("kwh_status",  "ok")
        _alerts  = []
        if _cost_st == "exceeded" and budget_status.get("latest_cost") and budget_status.get("budget_monthly_gbp"):
            _alerts.append(f"🚨 Latest bill <b>£{budget_status['latest_cost']:.2f}</b> exceeds your £{budget_status['budget_monthly_gbp']:.0f} monthly budget.")
        elif _cost_st == "warning" and budget_status.get("cost_pct"):
            _alerts.append(f"⚠️ Latest bill at <b>£{budget_status['latest_cost']:.2f}</b> is {budget_status['cost_pct']:.0f}% of your £{budget_status['budget_monthly_gbp']:.0f} monthly budget.")
        if _kwh_st == "exceeded" and budget_status.get("latest_kwh") and budget_status.get("budget_monthly_kwh"):
            _alerts.append(f"🚨 Latest usage <b>{budget_status['latest_kwh']} kWh</b> exceeds your {budget_status['budget_monthly_kwh']} kWh monthly limit.")
        elif _kwh_st == "warning" and budget_status.get("kwh_pct"):
            _alerts.append(f"⚠️ Latest usage at <b>{budget_status['latest_kwh']} kWh</b> is {budget_status['kwh_pct']:.0f}% of your {budget_status['budget_monthly_kwh']} kWh limit.")
        for _msg in _alerts:
            _bg    = "rgba(239,68,68,0.07)"  if "🚨" in _msg else "rgba(245,158,11,0.07)"
            _bdr   = "rgba(239,68,68,0.3)"   if "🚨" in _msg else "rgba(245,158,11,0.3)"
            st.markdown(f"""<div style="background:{_bg}; border:1px solid {_bdr};
                border-radius:10px; padding:12px 18px; margin-bottom:8px; font-size:0.87rem; color:#CBD5E1;">
                {_msg} &nbsp;<a href="?page=Settings" style="color:#4B6280; font-size:0.78rem;">Edit budget →</a>
            </div>""", unsafe_allow_html=True)

    # ── Upcoming due dates ──
    if upcoming:
        for due in upcoming:
            _dl = due["days_left"]
            _dc = "#EF4444" if _dl == 0 else "#F59E0B" if _dl <= 2 else "#1D4ED8"
            _dw = "due TODAY" if _dl == 0 else "due TOMORROW" if _dl == 1 else f"due in {_dl} days"
            st.markdown(f"""<div style="background:{_dc}11; border:1px solid {_dc}44;
                border-radius:10px; padding:11px 18px; margin-bottom:8px; font-size:0.87rem; color:#CBD5E1;">
                💳 <b>{due['provider']}</b> bill <b style="color:{_dc};">{_dw}</b>
                — £{due['amount_due']:.2f} &nbsp;·&nbsp; Due: {due['due_date']}
            </div>""", unsafe_allow_html=True)

    # ── KPI row ──
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-icon">💷</div>
            <div class="kpi-label">Total Spend</div>
            <div class="kpi-val">£{total_spend:,.2f}</div>
            <div class="kpi-sub">Across {total_bills} bill{'s' if total_bills != 1 else ''}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-icon">⚡</div>
            <div class="kpi-label">Avg Usage / Bill</div>
            <div class="kpi-val">{avg_kwh:.0f} kWh</div>
            <div class="kpi-sub">Per bill uploaded</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-icon">📋</div>
            <div class="kpi-label">Avg Cost / Bill</div>
            <div class="kpi-val">£{avg_cost:.2f}</div>
            <div class="kpi-sub">Based on your data</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-icon">🌿</div>
            <div class="kpi-label">CO₂ Footprint</div>
            <div class="kpi-val">{total_carbon:.1f} kg</div>
            <div class="kpi-sub">UK grid: 0.197 kg/kWh</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Charts + Tips ──
    chart_col, tip_col = st.columns((2.3, 1))

    with chart_col:
        if bills:
            df = pd.DataFrame(bills)
            df["_x_label"] = df["bill_date"].fillna("").apply(
                lambda d: d if d else None
            )
            # Sort chronologically when dates exist
            df_sorted = df.copy()
            has_dates = df_sorted["bill_date"].notna().any()
            if has_dates:
                df_sorted["_sort_date"] = pd.to_datetime(
                    df_sorted["bill_date"], dayfirst=True, errors="coerce"
                )
                df_sorted = df_sorted.sort_values("_sort_date", na_position="last")

            # Usage trend
            df_kwh = df_sorted[df_sorted["usage_kwh"].notna()].copy()
            if not df_kwh.empty:
                x_kwh = df_kwh["bill_date"].where(df_kwh["bill_date"].notna(), other=None).tolist()
                x_kwh = [v if v else f"Bill #{i+1}" for i, v in enumerate(x_kwh)]
                st.markdown('<div class="sec-head">Energy Usage Over Time</div>', unsafe_allow_html=True)
                st.markdown('<div class="sec-sub">kWh consumed per bill — oldest to newest</div>', unsafe_allow_html=True)
                fig = go.Figure(go.Scatter(
                    x=x_kwh,
                    y=df_kwh["usage_kwh"],
                    mode="lines+markers",
                    fill="tozeroy",
                    line=dict(color="#00C9B8", width=2.5),
                    marker=dict(color="#00C9B8", size=6),
                    fillcolor="rgba(0,201,184,0.07)",
                    hovertemplate="%{x}<br>%{y} kWh<extra></extra>",
                ))
                fig.update_layout(**_chart_layout(240))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Cost bars
            df_cost = df_sorted[df_sorted["amount_due"].notna()].copy()
            if not df_cost.empty:
                x_cost = df_cost["bill_date"].where(df_cost["bill_date"].notna(), other=None).tolist()
                x_cost = [v if v else f"Bill #{i+1}" for i, v in enumerate(x_cost)]
                st.markdown('<div class="sec-head">Bill Costs Over Time</div>', unsafe_allow_html=True)
                st.markdown('<div class="sec-sub">£ per bill — oldest to newest</div>', unsafe_allow_html=True)
                fig2 = go.Figure(go.Bar(
                    x=x_cost,
                    y=df_cost["amount_due"],
                    marker_color="#1D4ED8",
                    marker_opacity=0.85,
                    hovertemplate="%{x}<br>£%{y:.2f}<extra></extra>",
                ))
                fig2.update_layout(**_chart_layout(200))
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            # ── Monthly usage heatmap ──
            df_heat = df_sorted[df_sorted["usage_kwh"].notna() & df_sorted["bill_date"].notna()].copy()
            if len(df_heat) >= 3:
                df_heat["_dt"] = pd.to_datetime(df_heat["bill_date"], dayfirst=True, errors="coerce")
                df_heat = df_heat.dropna(subset=["_dt"])
                df_heat["_month"] = df_heat["_dt"].dt.strftime("%b")
                df_heat["_year"]  = df_heat["_dt"].dt.year.astype(str)
                _month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                df_heat["_month"] = pd.Categorical(df_heat["_month"], categories=_month_order, ordered=True)
                df_pivot = df_heat.pivot_table(index="_year", columns="_month", values="usage_kwh", aggfunc="mean")
                df_pivot = df_pivot.reindex(columns=[m for m in _month_order if m in df_pivot.columns])
                st.markdown('<div class="sec-head">Monthly Usage Heatmap</div>', unsafe_allow_html=True)
                st.markdown('<div class="sec-sub">Average kWh per month — darker = higher usage</div>', unsafe_allow_html=True)
                fig_heat = go.Figure(go.Heatmap(
                    z=df_pivot.values.tolist(),
                    x=df_pivot.columns.tolist(),
                    y=df_pivot.index.tolist(),
                    colorscale=[[0, "#0C1525"], [0.5, "#1D4ED8"], [1, "#00C9B8"]],
                    hovertemplate="%{y} %{x}: %{z:.0f} kWh<extra></extra>",
                    showscale=True,
                    colorbar=dict(thickness=12, len=0.8,
                                  tickfont=dict(color="#4B6280", size=9),
                                  outlinewidth=0),
                ))
                fig_heat.update_layout(**_chart_layout(180))
                st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("""
            <div style="text-align:center; padding:48px 24px; background:#0C1525;
                border:1px solid #1A2840; border-radius:16px; margin-top:1rem;">
                <div style="font-size:2.8rem; margin-bottom:14px;">📂</div>
                <div style="font-size:1.1rem; font-weight:700; color:#CBD5E1; margin-bottom:8px;">
                    No bills analysed yet</div>
                <div style="font-size:0.85rem; color:#4B6280; line-height:1.7; max-width:380px; margin:0 auto 20px;">
                    Upload your first UK energy bill and AI will extract usage,
                    costs and carbon data in seconds. Charts will appear here automatically.
                </div>
                <a href="javascript:void(0)" onclick="
                    window.parent.document.querySelectorAll('[data-testid=stSidebar] li')
                    .forEach(function(el){if(el.innerText.trim()==='Upload Bill') el.click();})
                " style="display:inline-block; background:linear-gradient(135deg,#00C9B8,#1D4ED8);
                    color:#fff; font-weight:600; font-size:0.88rem; padding:10px 24px;
                    border-radius:10px; text-decoration:none;">
                    ⚡ Upload your first bill
                </a>
            </div>""", unsafe_allow_html=True)

    with tip_col:
        # Provider donut
        if providers:
            st.markdown('<div class="sec-head">Provider Breakdown</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-sub">Bills by supplier</div>', unsafe_allow_html=True)
            fig_p = go.Figure(go.Pie(
                labels=list(providers.keys()),
                values=list(providers.values()),
                hole=0.62,
                marker_colors=["#00C9B8", "#1D4ED8", "#8B5CF6", "#F59E0B", "#EF4444"],
                textinfo="label+percent",
                textfont=dict(size=10, color="#94A3B8"),
            ))
            fig_p.update_traces(hovertemplate="%{label}: %{value} bill(s)<extra></extra>")
            fig_p.update_layout(**_chart_layout(200, margin_top=0))
            st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

        st.markdown('<div class="sec-head">Smart Recommendations</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Personalised actions from your data</div>', unsafe_allow_html=True)
        if recs:
            # Show top 4 recommendations
            for rec in recs[:4]:
                bg, border, icon = _rec_style(rec.get("type", "info"))
                st.markdown(f"""<div style="background:{bg}; border:1px solid {border};
                    border-radius:10px; padding:11px 14px; margin-bottom:8px;
                    font-size:0.82rem; line-height:1.5;">
                    <span style="font-weight:700; color:#CBD5E1;">{icon} {rec['title']}</span><br/>
                    <span style="color:#64748B; font-size:0.78rem;">{rec['detail']}</span>
                </div>""", unsafe_allow_html=True)
            if len(recs) > 4:
                st.markdown(
                    f'<div style="color:#4B6280; font-size:0.75rem; text-align:center; '
                    f'margin-top:4px;">+{len(recs)-4} more in Insights →</div>',
                    unsafe_allow_html=True,
                )
        else:
            for tip in [
                "💡 Drop your thermostat by 1°C — saves up to £115/year.",
                "🌙 Run washing machines off-peak (after 10pm) to cut costs.",
                "🔌 Switching off standby devices saves £55–£80/year.",
                "🚿 A 4-min shower instead of a bath saves ~£85/year.",
            ]:
                st.markdown(f'<div class="tip">{tip}</div>', unsafe_allow_html=True)

        # ── Usage Goal Tracker widget ──
        if goal and goal.get("goal_reduction_pct"):
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-head">Usage Goal</div>', unsafe_allow_html=True)
            _gpct   = goal.get("progress_pct") or 0
            _gtgt   = goal.get("target_kwh")
            _gcurr  = goal.get("current_avg_kwh")
            _gred   = goal.get("goal_reduction_pct")
            _on     = goal.get("on_track")
            _gc     = "#10B981" if _on else "#F59E0B"
            _gbar   = min(_gpct, 100)
            st.markdown(f"""<div style="background:#0C1525; border:1px solid #1A2840;
                border-radius:12px; padding:14px 16px;">
                <div style="font-size:0.75rem; color:#4B6280; margin-bottom:6px;">
                    🎯 Reduce usage by <b style="color:#F1F5F9;">{_gred:.0f}%</b>
                    · Target: <b style="color:{_gc};">{_gtgt:.0f} kWh</b>
                    · Current avg: <b style="color:#F1F5F9;">{_gcurr:.0f} kWh</b>
                </div>
                <div style="background:#1A2840; border-radius:20px; height:10px; overflow:hidden; margin-bottom:6px;">
                    <div style="background:{_gc}; width:{_gbar}%; height:100%; border-radius:20px;"></div>
                </div>
                <div style="font-size:0.72rem; color:{_gc}; font-weight:600;">
                    {_gpct:.0f}% progress {'✅ On track!' if _on else '— keep reducing usage'}
                </div>
            </div>""", unsafe_allow_html=True)


# ─── PAGE: UPLOAD BILL ─────────────────────────────────────────────────────────

def page_upload():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>Upload Your Energy Bill</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>
            Supports PDF, JPG, PNG · British Gas · Scottish Power · Octopus Energy · E.ON Next · OVO Energy · EDF Energy · nPower · Utilita · Shell Energy
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_ocr, tab_manual = st.tabs(["📄 Scan a Bill (OCR)", "✏️ Enter Manually"])

    with tab_ocr:
        col_file, col_cam = st.columns(2)
        with col_file:
            st.markdown('<div class="sec-head">Upload from device</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader(
                "Drop your bill here", type=["jpg", "jpeg", "png", "pdf"],
                label_visibility="collapsed",
            )
            if uploaded and uploaded.type != "application/pdf":
                st.image(uploaded, caption="Preview", use_container_width=True)

        with col_cam:
            st.markdown('<div class="sec-head">Take a photo</div>', unsafe_allow_html=True)
            photo = st.camera_input("Camera", label_visibility="collapsed")

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        btn_col, _ = st.columns([1, 3])
        with btn_col:
            analyse = st.button("⚡ Analyse Bill", use_container_width=True)

        if analyse:
            file_to_send = uploaded or photo
            if not file_to_send:
                st.warning("Please upload a bill or take a photo first.")
            else:
                with st.spinner("Running OCR and extracting bill data…"):
                    try:
                        r = requests.post(
                            f"{_api_url()}/upload-bill",
                            files={"file": (file_to_send.name, file_to_send.getvalue())},
                            headers=_auth_headers(),
                            timeout=30,
                        )
                        if r.status_code == 200:
                            res = r.json()
                            st.success("✅ Bill analysed successfully!")
                            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Provider",    res.get("provider", "Unknown"))
                            m2.metric("Amount Due",  f"£{res['amount_due']:.2f}" if res.get("amount_due") else "N/A")
                            m3.metric("Usage",       f"{res['usage_kwh']} kWh"   if res.get("usage_kwh")  else "N/A")
                            m4.metric("CO₂",         f"{res['carbon_kg']} kg"    if res.get("carbon_kg")  else "N/A")

                            extra_cols = st.columns(2)
                            with extra_cols[0]:
                                if res.get("bill_date"):   st.info(f"📅 Bill date: {res['bill_date']}")
                                if res.get("tariff_name"): st.info(f"📋 Tariff: {res['tariff_name']}")
                                if res.get("unit_rate"):   st.info(f"⚡ Unit rate: {res['unit_rate']}p/kWh")
                            with extra_cols[1]:
                                if res.get("due_date"):         st.info(f"⏰ Due: {res['due_date']}")
                                if res.get("account_number"):   st.info(f"🔢 Account: {res['account_number']}")
                                if res.get("standing_charge"):  st.info(f"📊 Standing charge: {res['standing_charge']}p/day")

                            with st.expander("📄 Raw OCR Text"):
                                st.code(res.get("extracted_text", "No text extracted."))
                        else:
                            detail = ""
                            try:
                                detail = r.json().get("detail", r.text)
                            except Exception:
                                detail = r.text
                            st.error(f"Error {r.status_code}: {detail}")
                    except requests.exceptions.ConnectionError:
                        _offline_banner()
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

    with tab_manual:
        st.markdown('<div class="sec-head">Enter bill details by hand</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">No bill scan needed — type the numbers from your paper bill</div>',
                    unsafe_allow_html=True)

        _PROVIDERS = ["British Gas", "Scottish Power", "Octopus Energy", "E.ON",
                      "OVO Energy", "EDF Energy", "nPower", "Shell Energy", "Bulb Energy", "So Energy", "Other"]

        with st.form("manual_bill_form"):
            mc1, mc2 = st.columns(2)
            with mc1:
                m_provider    = st.selectbox("Provider *", _PROVIDERS)
                m_bill_date   = st.text_input("Bill date (e.g. 1 January 2025)")
                m_amount      = st.number_input("Amount due (£)", min_value=0.0, step=0.01, format="%.2f")
                m_usage       = st.number_input("Usage (kWh)", min_value=0, step=1)
                m_unit_rate   = st.number_input("Unit rate (p/kWh)", min_value=0.0, step=0.1, format="%.2f")
            with mc2:
                m_account     = st.text_input("Account number")
                m_due_date    = st.text_input("Due date (e.g. 15 January 2025)")
                m_standing    = st.number_input("Standing charge (p/day)", min_value=0.0, step=0.1, format="%.2f")
                m_tariff      = st.text_input("Tariff name")
                m_meter       = st.text_input("Meter serial number")

            submitted = st.form_submit_button("💾 Save Bill", use_container_width=True)

        if submitted:
            if m_amount == 0.0 and m_usage == 0:
                st.warning("Enter at least an amount due or usage in kWh.")
            else:
                payload = {
                    "provider": m_provider,
                    "account_number": m_account or None,
                    "bill_date": m_bill_date or None,
                    "due_date": m_due_date or None,
                    "amount_due": m_amount if m_amount > 0 else None,
                    "usage_kwh": int(m_usage) if m_usage > 0 else None,
                    "standing_charge": m_standing if m_standing > 0 else None,
                    "unit_rate": m_unit_rate if m_unit_rate > 0 else None,
                    "tariff_name": m_tariff or None,
                    "meter_serial": m_meter or None,
                }
                try:
                    r = requests.post(
                        f"{_api_url()}/bills/manual",
                        json=payload,
                        headers=_auth_headers(),
                        timeout=10,
                    )
                    if r.status_code == 200:
                        res = r.json()
                        st.success(f"✅ Bill saved! ID #{res['id']} · {res['provider']} · "
                                   f"{'£' + str(res['amount_due']) if res.get('amount_due') else 'No amount'}")
                    else:
                        st.error(f"Error {r.status_code}: {r.json().get('detail', r.text)}")
                except requests.exceptions.ConnectionError:
                    _offline_banner()
                except Exception as e:
                    st.error(f"Unexpected error: {e}")


# ─── PAGE: HISTORY ─────────────────────────────────────────────────────────────

def page_history():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>Bill History</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>All uploaded and analysed energy bills</div>
    </div>
    """, unsafe_allow_html=True)

    rc, ec, cmp_col, csv_col, _ = st.columns([1, 1, 1, 1, 2])
    with rc:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with cmp_col:
        compare_mode = st.button("⚖️ Compare Bills", use_container_width=True)
        if compare_mode:
            st.session_state["compare_mode"] = not st.session_state.get("compare_mode", False)
    with csv_col:
        if st.button("⬇ Export CSV", use_container_width=True):
            try:
                r = requests.get(f"{_api_url()}/bills/export/csv", headers=_auth_headers(), timeout=10)
                if r.status_code == 200:
                    st.download_button(
                        "💾 Save CSV",
                        data=r.content,
                        file_name="energy_bills.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.error("Export failed.")
            except requests.exceptions.ConnectionError:
                _offline_banner()

    bills, err = _get("/bills")
    if err == "offline":
        _offline_banner()
        return
    if not bills:
        st.markdown('<div class="info-box">No bills uploaded yet. Go to <b>Upload Bill</b> to get started.</div>',
                    unsafe_allow_html=True)
        return

    # ── Comparison mode ──
    if st.session_state.get("compare_mode") and len(bills) >= 2:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Bill Comparison</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Select any two bills to compare side by side</div>', unsafe_allow_html=True)
        bill_labels = {b["id"]: f"#{b['id']} · {b.get('provider','?')} · {b.get('bill_date','No date')} · £{b['amount_due']:.2f}" if b.get('amount_due') else f"#{b['id']} · {b.get('provider','?')}" for b in bills}
        cmp1, cmp2 = st.columns(2)
        with cmp1:
            sel_a = st.selectbox("Bill A", options=list(bill_labels.keys()), format_func=lambda x: bill_labels[x], key="cmp_a")
        with cmp2:
            remaining = [b for b in bill_labels.keys() if b != sel_a]
            sel_b = st.selectbox("Bill B", options=remaining, format_func=lambda x: bill_labels[x], key="cmp_b")

        ba = next((b for b in bills if b["id"] == sel_a), None)
        bb = next((b for b in bills if b["id"] == sel_b), None)

        if ba and bb:
            def _diff_color(a, b, higher_is_worse=True):
                if a is None or b is None: return "#4B6280"
                return ("#EF4444" if a > b else "#10B981") if higher_is_worse else ("#10B981" if a > b else "#EF4444")

            def _diff_str(a, b, fmt=".1f", unit=""):
                if a is None or b is None: return "N/A"
                d = a - b
                sign = "+" if d > 0 else ""
                return f"{sign}{d:{fmt}}{unit}"

            fields = [
                ("Amount Due",      ba.get("amount_due"),      bb.get("amount_due"),      "£",      ".2f", True),
                ("Usage (kWh)",     ba.get("usage_kwh"),       bb.get("usage_kwh"),       " kWh",   ".0f", True),
                ("Carbon (kg CO₂)", ba.get("carbon_kg"),       bb.get("carbon_kg"),       " kg",    ".1f", True),
                ("Unit Rate",       ba.get("unit_rate"),       bb.get("unit_rate"),       "p/kWh",  ".1f", True),
                ("Standing Charge", ba.get("standing_charge"), bb.get("standing_charge"), "p/day",  ".1f", True),
            ]

            header_cols = st.columns([2, 2, 2, 1])
            header_cols[0].markdown(f"<div style='color:#4B6280; font-size:0.75rem; font-weight:700;'>FIELD</div>", unsafe_allow_html=True)
            header_cols[1].markdown(f"<div style='color:#00C9B8; font-size:0.75rem; font-weight:700;'>BILL A #{ba['id']}</div>", unsafe_allow_html=True)
            header_cols[2].markdown(f"<div style='color:#1D4ED8; font-size:0.75rem; font-weight:700;'>BILL B #{bb['id']}</div>", unsafe_allow_html=True)
            header_cols[3].markdown(f"<div style='color:#4B6280; font-size:0.75rem; font-weight:700;'>DIFF</div>", unsafe_allow_html=True)

            for label, va, vb, unit, fmt, higher_bad in fields:
                dc = _diff_color(va, vb, higher_bad)
                ds = _diff_str(va, vb, fmt.strip(".0f2"), unit)
                fa = f"{va:{fmt.lstrip('.')}}" if va is not None else "N/A"
                fb = f"{vb:{fmt.lstrip('.')}}" if vb is not None else "N/A"
                row = st.columns([2, 2, 2, 1])
                row[0].markdown(f"<div style='font-size:0.83rem; color:#94A3B8; padding:4px 0;'>{label}</div>", unsafe_allow_html=True)
                row[1].markdown(f"<div style='font-size:0.88rem; color:#F1F5F9; font-weight:600; padding:4px 0;'>{unit if len(unit)==1 else ''}{fa}{unit if len(unit)>1 else ''}</div>", unsafe_allow_html=True)
                row[2].markdown(f"<div style='font-size:0.88rem; color:#F1F5F9; font-weight:600; padding:4px 0;'>{unit if len(unit)==1 else ''}{fb}{unit if len(unit)>1 else ''}</div>", unsafe_allow_html=True)
                row[3].markdown(f"<div style='font-size:0.82rem; color:{dc}; font-weight:700; padding:4px 0;'>{ds}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    with ec:
        _csv_cols = ["id","provider","bill_date","due_date","amount_due","usage_kwh",
                     "carbon_kg","unit_rate","standing_charge","tariff_name","account_number","meter_serial","filename"]
        _csv_df = pd.DataFrame(bills)[[c for c in _csv_cols if c in pd.DataFrame(bills).columns]]
        st.download_button(
            "⬇ Export CSV",
            data=_csv_df.to_csv(index=False).encode("utf-8"),
            file_name="energy_bills.csv",
            mime="text/csv",
            use_container_width=True,
        )

    for bill in bills:
        provider = bill.get("provider", "Unknown")
        amount   = f"£{bill['amount_due']:.2f}" if bill.get("amount_due") else "N/A"
        kwh      = f"{bill['usage_kwh']} kWh"   if bill.get("usage_kwh")  else "N/A"
        date     = bill.get("bill_date") or "No date"

        with st.expander(f"#{bill['id']}  ·  {provider}  ·  {amount}  ·  {date}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Amount Due", amount)
            c2.metric("Usage", kwh)
            c3.metric("Carbon", f"{bill['carbon_kg']} kg" if bill.get("carbon_kg") else "N/A")
            c4.metric("Bill Date", date)

            details = []
            if bill.get("tariff_name"):     details.append(f"**Tariff:** {bill['tariff_name']}")
            if bill.get("unit_rate"):       details.append(f"**Unit rate:** {bill['unit_rate']}p/kWh")
            if bill.get("standing_charge"): details.append(f"**Standing charge:** {bill['standing_charge']}p/day")
            if bill.get("account_number"):  details.append(f"**Account:** {bill['account_number']}")
            if bill.get("meter_serial"):    details.append(f"**Meter:** {bill['meter_serial']}")
            if bill.get("due_date"):        details.append(f"**Due date:** {bill['due_date']}")
            if details:
                st.markdown("  ·  ".join(details))

            st.caption(f"File: {bill.get('filename', 'N/A')}")

            edit_col, del_col = st.columns([1, 1])
            with del_col:
                if st.button("🗑 Delete", key=f"del_{bill['id']}", help="Delete this bill", use_container_width=True):
                    r = requests.delete(
                        f"{_api_url()}/bills/{bill['id']}",
                        headers=_auth_headers(),
                    )
                    if r.status_code == 200:
                        st.success("Bill deleted.")
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Delete failed."))

            with edit_col:
                if st.button("✏️ Edit", key=f"edit_toggle_{bill['id']}", use_container_width=True):
                    key = f"editing_{bill['id']}"
                    st.session_state[key] = not st.session_state.get(key, False)

            if st.session_state.get(f"editing_{bill['id']}", False):
                _PROVIDERS_EDIT = ["British Gas", "Scottish Power", "Octopus Energy", "E.ON",
                                   "OVO Energy", "EDF Energy", "nPower", "Shell Energy",
                                   "Bulb Energy", "So Energy", "Unknown"]
                with st.form(key=f"edit_form_{bill['id']}"):
                    st.markdown("**Edit bill details**")
                    ea, eb = st.columns(2)
                    with ea:
                        e_provider  = st.selectbox("Provider", _PROVIDERS_EDIT,
                                                   index=_PROVIDERS_EDIT.index(bill.get("provider", "Unknown"))
                                                   if bill.get("provider") in _PROVIDERS_EDIT else 0)
                        e_bill_date = st.text_input("Bill date", value=bill.get("bill_date") or "")
                        e_amount    = st.number_input("Amount due (£)", value=float(bill.get("amount_due") or 0), min_value=0.0, step=0.01, format="%.2f")
                        e_usage     = st.number_input("Usage (kWh)", value=int(bill.get("usage_kwh") or 0), min_value=0, step=1)
                        e_unit_rate = st.number_input("Unit rate (p/kWh)", value=float(bill.get("unit_rate") or 0), min_value=0.0, step=0.1, format="%.2f")
                    with eb:
                        e_account   = st.text_input("Account number", value=bill.get("account_number") or "")
                        e_due_date  = st.text_input("Due date", value=bill.get("due_date") or "")
                        e_standing  = st.number_input("Standing charge (p/day)", value=float(bill.get("standing_charge") or 0), min_value=0.0, step=0.1, format="%.2f")
                        e_tariff    = st.text_input("Tariff name", value=bill.get("tariff_name") or "")
                        e_meter     = st.text_input("Meter serial", value=bill.get("meter_serial") or "")
                    if st.form_submit_button("💾 Save changes", use_container_width=True):
                        patch = {
                            "provider":        e_provider,
                            "bill_date":       e_bill_date or None,
                            "due_date":        e_due_date or None,
                            "amount_due":      e_amount if e_amount > 0 else None,
                            "usage_kwh":       int(e_usage) if e_usage > 0 else None,
                            "unit_rate":       e_unit_rate if e_unit_rate > 0 else None,
                            "standing_charge": e_standing if e_standing > 0 else None,
                            "tariff_name":     e_tariff or None,
                            "account_number":  e_account or None,
                            "meter_serial":    e_meter or None,
                        }
                        r = requests.patch(
                            f"{_api_url()}/bills/{bill['id']}",
                            json=patch,
                            headers=_auth_headers(),
                        )
                        if r.status_code == 200:
                            st.success("Bill updated.")
                            st.session_state.pop(f"editing_{bill['id']}", None)
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Update failed."))


# ─── PAGE: INSIGHTS ────────────────────────────────────────────────────────────

def _rec_style(rec_type: str) -> tuple[str, str, str]:
    if rec_type == "warning":
        return "rgba(245,158,11,0.07)", "rgba(245,158,11,0.25)", "⚠️"
    if rec_type == "success":
        return "rgba(16,185,129,0.07)", "rgba(16,185,129,0.25)", "✅"
    return "rgba(29,78,216,0.07)", "rgba(29,78,216,0.22)", "💡"


def page_insights():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>Energy Insights</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>ML-powered predictions, anomaly detection, and personalised recommendations</div>
    </div>
    """, unsafe_allow_html=True)

    bills, err = _get("/bills")
    if err == "offline":
        _offline_banner()
        return
    if not bills:
        st.markdown("""<div class="coming">
            <div class="coming-icon">📊</div>
            <div class="coming-title">No bills yet</div>
            <div class="coming-sub">Upload your first bill to unlock AI-powered insights.</div>
        </div>""", unsafe_allow_html=True)
        return

    df = pd.DataFrame(bills)

    # ── ML data ──
    with st.spinner("Running ML models…"):
        pred, _        = _get("/ml/predictions")
        anomalies, _   = _get("/ml/anomalies")
        classify, _    = _get("/ml/classify")
        recs, _        = _get("/ml/recommendations")
        clusters, _    = _get("/ml/clusters")
        changepoints_data, _ = _get("/ml/changepoints")
        cost_pred, _   = _get("/ml/cost-prediction")

    # ── Section 1: Prediction + Classification ──
    p_col, c_col = st.columns(2)

    with p_col:
        st.markdown('<div class="sec-head">Next Month Forecast</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Prophet seasonal model · Gradient Boosting cost estimate</div>', unsafe_allow_html=True)
        if pred and pred.get("status") == "ok":
            trend_icon = "📈" if pred["trend"] == "increasing" else "📉"
            trend_color = "#EF4444" if pred["trend"] == "increasing" else "#10B981"
            st.markdown(f"""<div class="card">
                <div style="display:flex; gap:24px; flex-wrap:wrap; margin-bottom:16px;">
                    <div>
                        <div class="kpi-label">Predicted Usage</div>
                        <div style="font-size:1.8rem; font-weight:800; color:#F1F5F9;">{pred['predicted_kwh']} kWh</div>
                    </div>
                    <div>
                        <div class="kpi-label">Predicted Cost</div>
                        <div style="font-size:1.8rem; font-weight:800; color:#F1F5F9;">£{pred['predicted_cost']:.2f}</div>
                    </div>
                    <div>
                        <div class="kpi-label">Predicted CO₂</div>
                        <div style="font-size:1.8rem; font-weight:800; color:#F1F5F9;">{pred['predicted_carbon_kg']} kg</div>
                    </div>
                </div>
                <div style="display:flex; gap:16px; align-items:center; font-size:0.83rem; color:#4B6280; flex-wrap:wrap;">
                    <span>{trend_icon} Trend: <b style="color:{trend_color};">{pred['trend'].title()}</b>
                    ({pred['monthly_change_kwh']:+.1f} kWh/month)</span>
                    <span>·</span>
                    <span>For: <b style="color:#CBD5E1;">{pred.get('next_period', 'next period')}</b></span>
                    <span>·</span>
                    <span>Model: <b style="color:#CBD5E1;">{'Prophet (seasonal)' if pred.get('model') == 'prophet' else 'Linear regression'}</b></span>
                    {f"<span>· R² = {pred['model_r2']} ({pred['data_points']} pts)</span>" if pred.get('model_r2') is not None else f"<span>({pred['data_points']} data points)</span>"}
                </div>
            </div>""", unsafe_allow_html=True)

            # Trend chart — historical + 1 prediction bar, sorted by date
            df_pred_src = df[df["usage_kwh"].notna()].copy()
            df_pred_src["_sd"] = pd.to_datetime(df_pred_src["bill_date"], dayfirst=True, errors="coerce")
            df_pred_src = df_pred_src.sort_values("_sd", na_position="last")
            kwh_data = df_pred_src["usage_kwh"].tolist()
            x_dates  = df_pred_src["bill_date"].tolist()
            hist_labels = [d if d else f"Bill #{i+1}" for i, d in enumerate(x_dates)]
            labels  = hist_labels + ["Next (forecast)"]
            colors  = ["#00C9B8"] * len(kwh_data) + ["#F59E0B"]
            fig_pred = go.Figure(go.Bar(
                x=labels, y=kwh_data + [pred["predicted_kwh"]],
                marker_color=colors, marker_opacity=0.85,
                hovertemplate="%{x}<br>%{y} kWh<extra></extra>",
            ))
            fig_pred.update_layout(**_chart_layout(220))
            st.plotly_chart(fig_pred, use_container_width=True, config={"displayModeBar": False})

            # GBR cost prediction card
            if cost_pred and cost_pred.get("status") == "ok":
                imp = cost_pred.get("feature_importances", {})
                top_feature = max(imp, key=imp.get) if imp else "usage_kwh"
                top_pct = round(imp.get(top_feature, 0) * 100)
                st.markdown(f"""<div style="background:#0A1220; border:1px solid #1A2840;
                    border-left:3px solid #F59E0B; border-radius:10px; padding:13px 18px; margin-top:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:0.72rem; color:#4B6280; text-transform:uppercase; letter-spacing:0.06em;">
                                GBR Cost Forecast · {cost_pred.get('next_period','next month')}</div>
                            <div style="font-size:1.5rem; font-weight:800; color:#F59E0B; margin-top:2px;">
                                £{cost_pred['predicted_cost']:.2f}</div>
                        </div>
                        <div style="text-align:right; font-size:0.78rem; color:#4B6280;">
                            <div>CV R² = <b style="color:#CBD5E1;">{cost_pred['cv_r2']}</b></div>
                            <div style="margin-top:3px;">Top driver: <b style="color:#CBD5E1;">{top_feature.replace('_',' ')} ({top_pct}%)</b></div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            msg = pred.get("message", "Not enough data.") if pred else "Could not load prediction."
            st.markdown(f'<div class="info-box">🔮 {msg}</div>', unsafe_allow_html=True)

    with c_col:
        st.markdown('<div class="sec-head">Usage Classification</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Your household vs UK Ofgem averages</div>', unsafe_allow_html=True)
        if classify and classify.get("classification") != "Unknown":
            color = classify.get("color", "#4B6280")
            cls   = classify["classification"]
            ann   = classify["estimated_annual_kwh"]
            uk    = classify["uk_average_annual_kwh"]
            pct   = classify["pct_vs_uk_avg"]
            pct_str = f"+{pct}%" if pct > 0 else f"{pct}%"
            pct_col = "#EF4444" if pct > 0 else "#10B981"

            st.markdown(f"""<div class="card">
                <div style="display:flex; align-items:center; gap:18px; margin-bottom:18px;">
                    <div style="background:{color}22; border:1.5px solid {color}55;
                        border-radius:14px; padding:14px 22px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:800; color:{color};">{cls}</div>
                        <div style="font-size:0.7rem; color:#4B6280; margin-top:2px;">USAGE BAND</div>
                    </div>
                    <div>
                        <div style="font-size:0.83rem; color:#CBD5E1; margin-bottom:8px;">{classify['description']}</div>
                        <div style="font-size:0.78rem; color:#4B6280;">
                            Est. annual: <b style="color:#F1F5F9;">{ann:,} kWh</b> &nbsp;·&nbsp;
                            UK avg: <b style="color:#F1F5F9;">{uk:,} kWh</b> &nbsp;·&nbsp;
                            <b style="color:{pct_col};">{pct_str} vs UK avg</b>
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Gauge-style bar
            fig_gauge = go.Figure(go.Bar(
                x=["Your usage", "UK Average"],
                y=[ann, uk],
                marker_color=["#F59E0B" if cls == "High" else color, "#1D4ED8"],
                marker_opacity=0.85,
                hovertemplate="%{y:,} kWh/year<extra></extra>",
                text=[f"{ann:,} kWh", f"{uk:,} kWh"],
                textposition="outside",
                textfont=dict(color="#94A3B8", size=11),
            ))
            fig_gauge.update_layout(**_chart_layout(220))
            st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="info-box">📊 Upload bills with kWh readings to classify your usage.</div>',
                        unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Section 2: Anomalies ──
    st.markdown('<div class="sec-head">Anomaly Detection</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Bills flagged as unusually high or low by the ML model</div>', unsafe_allow_html=True)

    if anomalies:
        for a in anomalies:
            pct = a["pct_diff_from_mean"]
            color = "#EF4444" if pct > 0 else "#10B981"
            sign  = "+" if pct > 0 else ""
            st.markdown(f"""<div style="background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.18);
                border-left:3px solid {color}; border-radius:10px; padding:13px 18px; margin-bottom:8px;
                display:flex; align-items:center; justify-content:space-between; font-size:0.87rem;">
                <div>
                    <span style="color:#F1F5F9; font-weight:600;">Bill #{a['id']} — {a['provider']}</span>
                    &nbsp;·&nbsp; <span style="color:#4B6280;">{a.get('bill_date') or 'No date'}</span>
                    &nbsp;·&nbsp; <span style="color:#4B6280;">{a['reason'].title()}</span>
                </div>
                <div style="text-align:right;">
                    <span style="color:#F1F5F9; font-weight:700;">{a['usage_kwh']} kWh</span>
                    &nbsp;
                    <span style="color:{color}; font-weight:600;">({sign}{pct}% vs avg)</span>
                </div>
            </div>""", unsafe_allow_html=True)
    elif len(bills) < 3:
        st.markdown('<div class="info-box">🔍 Upload at least 3 bills to enable anomaly detection.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box" style="border-color:rgba(16,185,129,0.25); background:rgba(16,185,129,0.05);">'
                    '✅ No anomalies detected — your usage looks consistent.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Section 3: Recommendations ──
    _n_recs = len(recs) if recs else 0
    _badge  = (f'<span style="background:#1D4ED8; color:#fff; font-size:0.65rem; font-weight:700; '
               f'padding:2px 8px; border-radius:20px; margin-left:8px; vertical-align:middle;">'
               f'{_n_recs}</span>') if _n_recs else ""
    st.markdown(f'<div class="sec-head">Smart Recommendations{_badge}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Personalised actions — highest priority first</div>', unsafe_allow_html=True)

    _type_labels = {"warning": "ACTION", "success": "WIN", "info": "TIP"}
    _type_colors = {"warning": "#F59E0B", "success": "#10B981", "info": "#1D4ED8"}

    if recs:
        for rec in recs:
            t = rec.get("type", "info")
            bg, border, icon = _rec_style(t)
            label       = _type_labels.get(t, "TIP")
            label_color = _type_colors.get(t, "#1D4ED8")
            st.markdown(f"""<div style="background:{bg}; border:1px solid {border};
                border-radius:10px; padding:14px 18px; margin-bottom:10px;
                font-size:0.87rem; line-height:1.55; position:relative;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                    <span style="font-weight:700; color:#CBD5E1; font-size:0.88rem;">{icon} {rec['title']}</span>
                    <span style="background:{label_color}22; color:{label_color}; font-size:0.6rem;
                        font-weight:800; padding:1px 7px; border-radius:20px; letter-spacing:0.04em;
                        border:1px solid {label_color}44;">{label}</span>
                </div>
                <span style="color:#64748B; font-size:0.82rem;">{rec['detail']}</span>
            </div>""", unsafe_allow_html=True)

    # ── Section 4: Usage Clustering ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Usage Pattern Clustering</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">KMeans groups your bills by consumption pattern</div>', unsafe_allow_html=True)

    if clusters and clusters.get("status") == "ok":
        cl_col1, cl_col2 = st.columns([1.4, 1])
        with cl_col1:
            cl_df = pd.DataFrame(clusters["bills"])
            if not cl_df.empty:
                fig_cl = px.scatter(
                    cl_df, x="usage_kwh", y="amount_due",
                    color="cluster_name",
                    color_discrete_map={r["name"]: r["color"] for r in clusters["summary"]},
                    hover_data=["bill_date", "provider"],
                    labels={"usage_kwh": "Usage (kWh)", "amount_due": "Cost (£)", "cluster_name": "Pattern"},
                )
                fig_cl.update_traces(marker=dict(size=11, opacity=0.85))
                fig_cl.update_layout(**_chart_layout(260))
                st.plotly_chart(fig_cl, use_container_width=True, config={"displayModeBar": False})
        with cl_col2:
            for s in clusters["summary"]:
                st.markdown(f"""<div style="background:{s['color']}15; border:1px solid {s['color']}40;
                    border-left:3px solid {s['color']}; border-radius:10px;
                    padding:12px 16px; margin-bottom:10px;">
                    <div style="font-weight:700; color:{s['color']}; font-size:0.88rem;">{s['name']}</div>
                    <div style="color:#94A3B8; font-size:0.8rem; margin-top:4px;">
                        {s['count']} bill(s) · avg {s['avg_kwh']} kWh · avg £{s['avg_cost']:.2f}
                    </div>
                </div>""", unsafe_allow_html=True)
    else:
        msg = clusters.get("message", "Not enough data.") if clusters else "Could not load clusters."
        st.markdown(f'<div class="info-box">🔵 {msg}</div>', unsafe_allow_html=True)

    # ── Section 5: Changepoint Detection ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Usage Shift Detection</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Permanent changes in your consumption pattern</div>', unsafe_allow_html=True)

    if changepoints_data and changepoints_data.get("status") == "ok":
        cps = changepoints_data.get("changepoints", [])
        if cps:
            for cp in cps:
                direction = cp["direction"]
                color = "#EF4444" if direction == "increase" else "#10B981"
                icon  = "📈" if direction == "increase" else "📉"
                pct   = cp["pct_change"]
                st.markdown(f"""<div style="background:{color}08; border:1px solid {color}30;
                    border-left:3px solid {color}; border-radius:10px;
                    padding:13px 18px; margin-bottom:8px; font-size:0.87rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color:#F1F5F9; font-weight:700;">{icon} Shift detected at bill #{cp['bill_id']}</span>
                            &nbsp;·&nbsp; <span style="color:#4B6280;">{cp.get('bill_date') or 'No date'}</span>
                        </div>
                        <span style="color:{color}; font-weight:700; font-size:1rem;">{'+' if pct > 0 else ''}{pct}%</span>
                    </div>
                    <div style="color:#64748B; margin-top:6px; font-size:0.82rem;">
                        Before: avg {cp['before_avg_kwh']} kWh &nbsp;→&nbsp; After: avg {cp['after_avg_kwh']} kWh
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box" style="border-color:rgba(16,185,129,0.25); '
                        'background:rgba(16,185,129,0.05);">✅ No significant usage shifts detected — '
                        'your consumption pattern has been stable.</div>', unsafe_allow_html=True)
    else:
        msg = changepoints_data.get("message", "Not enough data.") if changepoints_data else "Could not load changepoint data."
        st.markdown(f'<div class="info-box">📍 {msg}</div>', unsafe_allow_html=True)

    # ── Section 6: Tariff Comparison ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Tariff Comparison & Savings Calculator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">How your current rate compares to the best available tariffs</div>', unsafe_allow_html=True)

    # Ofgem Q1 2025 price cap reference rates (pence/kWh)
    _TARIFFS = [
        {"name": "Ofgem Price Cap (standard)",  "rate": 24.50, "standing": 61.0,  "color": "#4B6280", "tag": ""},
        {"name": "Octopus Tracker",             "rate": 21.8,  "standing": 47.0,  "color": "#00C9B8", "tag": "Variable"},
        {"name": "Octopus Agile (avg off-peak)", "rate": 18.5, "standing": 47.0,  "color": "#10B981", "tag": "Smart meter"},
        {"name": "EDF Simply Fixed",            "rate": 23.9,  "standing": 56.0,  "color": "#1D4ED8", "tag": "Fixed"},
        {"name": "British Gas Fixed",           "rate": 24.1,  "standing": 59.0,  "color": "#3B82F6", "tag": "Fixed"},
        {"name": "OVO Better Energy",           "rate": 22.5,  "standing": 52.0,  "color": "#8B5CF6", "tag": "Green"},
    ]

    _ur_vals = [b.get("unit_rate") for b in bills if b.get("unit_rate")]
    _user_rate = round(sum(_ur_vals) / len(_ur_vals), 2) if _ur_vals else None
    _avg_kwh_month = (df["usage_kwh"].dropna().mean() or 0)

    if _user_rate:
        st.markdown(f'<div class="info-box">Your average unit rate: <b style="color:#F1F5F9;">{_user_rate}p/kWh</b> '
                    f'· Avg monthly usage: <b style="color:#F1F5F9;">{_avg_kwh_month:.0f} kWh</b></div>',
                    unsafe_allow_html=True)

    tc1, tc2 = st.columns([1.6, 1])
    with tc1:
        tariff_rows = ""
        for t in _TARIFFS:
            monthly_cost = (_avg_kwh_month * t["rate"] / 100 + t["standing"] / 100 * 30.5) if _avg_kwh_month else None
            annual_cost  = monthly_cost * 12 if monthly_cost else None
            user_annual  = (_avg_kwh_month * (_user_rate or t["rate"]) / 100 + t["standing"] / 100 * 30.5) * 12 if _avg_kwh_month else None
            saving       = round(user_annual - annual_cost, 0) if (user_annual and annual_cost) else None
            saving_html  = (f'<span style="color:#10B981; font-weight:700;">Save £{saving:.0f}/yr</span>'
                           if saving and saving > 5 else
                           f'<span style="color:#EF4444; font-weight:600;">+£{abs(saving):.0f}/yr more</span>'
                           if saving and saving < -5 else
                           '<span style="color:#4B6280;">Similar to yours</span>') if saving is not None else ""
            tag_html = (f'<span style="background:{t["color"]}22; color:{t["color"]}; '
                       f'font-size:0.68rem; padding:2px 7px; border-radius:99px; margin-left:6px;">'
                       f'{t["tag"]}</span>') if t["tag"] else ""
            tariff_rows += f"""
            <tr style="border-bottom:1px solid #1A2840;">
              <td style="padding:10px 8px; color:#CBD5E1; font-weight:500;">{t['name']}{tag_html}</td>
              <td style="padding:10px 8px; color:#F1F5F9; text-align:right;">{t['rate']}p</td>
              <td style="padding:10px 8px; color:#94A3B8; text-align:right;">{t['standing']}p/day</td>
              <td style="padding:10px 8px; text-align:right;">{'£' + f'{annual_cost:.0f}/yr' if annual_cost else '—'}</td>
              <td style="padding:10px 8px; text-align:right;">{saving_html}</td>
            </tr>"""
        st.markdown(f"""<div style="background:#0C1525; border:1px solid #1A2840; border-radius:12px; overflow:hidden;">
            <table style="width:100%; border-collapse:collapse; font-size:0.83rem;">
              <thead><tr style="background:#080D1A; color:#4B6280; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em;">
                <th style="padding:10px 8px; text-align:left;">Tariff</th>
                <th style="padding:10px 8px; text-align:right;">Unit rate</th>
                <th style="padding:10px 8px; text-align:right;">Standing</th>
                <th style="padding:10px 8px; text-align:right;">Est. annual</th>
                <th style="padding:10px 8px; text-align:right;">vs your bills</th>
              </tr></thead>
              <tbody>{tariff_rows}</tbody>
            </table></div>""", unsafe_allow_html=True)

    with tc2:
        st.markdown('<div class="sec-head" style="margin-top:0">Savings Calculator</div>', unsafe_allow_html=True)
        calc_kwh    = st.number_input("Monthly usage (kWh)", value=int(_avg_kwh_month) if _avg_kwh_month else 250, min_value=1, step=10, key="calc_kwh")
        calc_rate   = st.number_input("Your current rate (p/kWh)", value=float(_user_rate or 24.5), min_value=1.0, step=0.1, format="%.1f", key="calc_rate")
        calc_target = st.number_input("Target rate (p/kWh)", value=21.8, min_value=1.0, step=0.1, format="%.1f", key="calc_target")
        current_annual = calc_kwh * calc_rate / 100 * 12
        target_annual  = calc_kwh * calc_target / 100 * 12
        saving_calc    = current_annual - target_annual
        color_calc = "#10B981" if saving_calc > 0 else "#EF4444"
        st.markdown(f"""<div style="background:#0A1220; border:1px solid #1A2840; border-radius:10px; padding:16px; margin-top:8px; text-align:center;">
            <div style="color:#4B6280; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">Annual saving</div>
            <div style="font-size:2rem; font-weight:800; color:{color_calc};">{'£' + f'{saving_calc:.0f}' if saving_calc >= 0 else '−£' + f'{abs(saving_calc):.0f}'}</div>
            <div style="color:#4B6280; font-size:0.78rem; margin-top:6px;">£{current_annual:.0f} → £{target_annual:.0f}/yr</div>
        </div>""", unsafe_allow_html=True)
        st.caption("Compare at [Ofgem's energy price cap page](https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you)")

    # ── Section 7: Carbon Offset Tracker ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Carbon Footprint Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Your CO₂ vs UK household average — and what it would take to offset it</div>', unsafe_allow_html=True)

    _co2_vals = df["carbon_kg"].dropna()
    if not _co2_vals.empty:
        _total_co2   = float(_co2_vals.sum())
        _uk_avg_co2_annual = 3100 * 0.197       # UK avg household annual kWh × carbon factor
        _bills_count = len(_co2_vals)
        _user_annual_co2 = (_total_co2 / _bills_count) * 12
        _pct_vs_uk = round((_user_annual_co2 - _uk_avg_co2_annual) / _uk_avg_co2_annual * 100, 1)
        _trees_to_offset = round(_total_co2 / 21.7, 1)   # avg tree absorbs 21.7 kg CO₂/yr
        _km_driven       = round(_total_co2 / 0.17, 0)   # 170g CO₂/km petrol car
        _flights_lhr_nyc = round(_total_co2 / 1000, 2)   # ~1000 kg CO₂ per LHR–JFK flight

        co2a, co2b, co2c, co2d = st.columns(4)
        co2a.metric("Total CO₂ (bills)", f"{_total_co2:.1f} kg")
        co2b.metric("Est. annual CO₂", f"{_user_annual_co2:.0f} kg",
                    delta=f"{'+' if _pct_vs_uk > 0 else ''}{_pct_vs_uk}% vs UK avg",
                    delta_color="inverse")
        co2c.metric("Trees to offset", f"{_trees_to_offset}")
        co2d.metric("Equiv. km driven", f"{_km_driven:,.0f} km")

        # Carbon trend chart
        _co2_src = df[df["carbon_kg"].notna()].copy()
        _co2_src["_sd"] = pd.to_datetime(_co2_src["bill_date"], dayfirst=True, errors="coerce")
        _co2_src = _co2_src.sort_values("_sd", na_position="last")
        _x_co2 = [d if d else f"Bill #{i+1}" for i, d in enumerate(_co2_src["bill_date"].tolist())]
        _cumulative = _co2_src["carbon_kg"].cumsum().tolist()

        fig_co2 = go.Figure()
        fig_co2.add_trace(go.Bar(
            x=_x_co2, y=_co2_src["carbon_kg"].tolist(),
            name="Per bill", marker_color="#8B5CF6", marker_opacity=0.8,
            hovertemplate="%{x}<br>%{y:.1f} kg CO₂<extra></extra>",
        ))
        fig_co2.add_trace(go.Scatter(
            x=_x_co2, y=_cumulative,
            name="Cumulative", mode="lines+markers",
            line=dict(color="#F59E0B", width=2), marker=dict(size=5),
            hovertemplate="%{x}<br>Total: %{y:.1f} kg CO₂<extra></extra>",
            yaxis="y2",
        ))
        fig_co2.update_layout(**_chart_layout(260))
        fig_co2.update_layout(
            showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0, font=dict(size=10, color="#4B6280")),
            yaxis2=dict(overlaying="y", side="right", gridcolor="#12202E",
                       linecolor="#12202E", zeroline=False, tickfont=dict(color="#4B6280", size=10)),
        )
        st.plotly_chart(fig_co2, use_container_width=True, config={"displayModeBar": False})

        pct_color = "#EF4444" if _pct_vs_uk > 0 else "#10B981"
        pct_word  = "above" if _pct_vs_uk > 0 else "below"
        st.markdown(f"""<div class="info-box">
            🌿 Your estimated annual carbon from energy bills is <b style="color:#F1F5F9;">{_user_annual_co2:.0f} kg CO₂</b> —
            <b style="color:{pct_color};">{abs(_pct_vs_uk)}% {pct_word}</b> the UK household average ({_uk_avg_co2_annual:.0f} kg/yr).
            That's equivalent to <b style="color:#F1F5F9;">{_km_driven:,.0f} km</b> driven or
            <b style="color:#F1F5F9;">{_flights_lhr_nyc}</b> London–New York flights.
            Planting <b style="color:#10B981;">{_trees_to_offset} trees</b> would offset your tracked bills.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">🌿 Upload bills with kWh usage to track your carbon footprint.</div>',
                    unsafe_allow_html=True)

    # ── Section 8: Charts ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Usage vs Cost & Carbon</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec-sub">Correlation between kWh consumed and £ charged</div>', unsafe_allow_html=True)
        valid = df[df["usage_kwh"].notna() & df["amount_due"].notna()]
        if not valid.empty:
            fig = px.scatter(
                valid, x="usage_kwh", y="amount_due",
                color_discrete_sequence=["#00C9B8"],
                labels={"usage_kwh": "kWh used", "amount_due": "Amount (£)"},
                hover_data=["provider"],
            )
            fig.update_traces(marker=dict(size=11, opacity=0.85))
            fig.update_layout(**_chart_layout(260))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown('<div class="sec-sub">Carbon footprint of each uploaded bill</div>', unsafe_allow_html=True)
        valid_c = df[df["carbon_kg"].notna()].copy()
        if not valid_c.empty:
            valid_c["_sd"] = pd.to_datetime(valid_c["bill_date"], dayfirst=True, errors="coerce")
            valid_c = valid_c.sort_values("_sd", na_position="last")
            x_co2 = [d if d else f"Bill #{i+1}" for i, d in enumerate(valid_c["bill_date"].tolist())]
            fig2 = go.Figure(go.Bar(
                x=x_co2,
                y=valid_c["carbon_kg"],
                marker_color="#8B5CF6",
                marker_opacity=0.85,
                hovertemplate="%{x}<br>%{y:.1f} kg CO₂<extra></extra>",
            ))
            fig2.update_layout(**_chart_layout(260))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Summary stats ──
    kwh_vals  = df["usage_kwh"].dropna()
    cost_vals = df["amount_due"].dropna()
    co2_vals  = df["carbon_kg"].dropna()

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Highest Bill",  f"£{cost_vals.max():.2f}"    if not cost_vals.empty else "N/A")
    s2.metric("Lowest Bill",   f"£{cost_vals.min():.2f}"    if not cost_vals.empty else "N/A")
    s3.metric("Peak Usage",    f"{int(kwh_vals.max())} kWh"  if not kwh_vals.empty else "N/A")
    avg_unit = (cost_vals.sum() / kwh_vals.sum() * 100) if (not kwh_vals.empty and kwh_vals.sum() > 0) else None
    s4.metric("Avg Unit Cost", f"{avg_unit:.1f}p/kWh" if avg_unit else "N/A")

    if not co2_vals.empty:
        total_co2 = co2_vals.sum()
        st.markdown(f"""<div class="info-box" style="margin-top:1rem;">
            🌿 <b>Carbon context:</b> Your {len(co2_vals)} bill(s) generated an estimated
            <b>{total_co2:.1f} kg CO₂</b> — equivalent to driving approximately
            <b>{total_co2 / 0.17:.0f} km</b> in an average petrol car (170g CO₂/km).
        </div>""", unsafe_allow_html=True)

    # ── Export ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    _ex_col, _ = st.columns([1, 3])
    with _ex_col:
        _ins_cols = ["id","provider","bill_date","amount_due","usage_kwh","carbon_kg","unit_rate","standing_charge","tariff_name"]
        _ins_df = df[[c for c in _ins_cols if c in df.columns]]
        st.download_button(
            "⬇ Export Insights CSV",
            data=_ins_df.to_csv(index=False).encode("utf-8"),
            file_name="energy_insights.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ─── PAGE: ALERTS ──────────────────────────────────────────────────────────────

def page_alerts():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>Alerts & Budget</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>
            Set spending limits and get email notifications when your usage spikes
        </div>
    </div>
    """, unsafe_allow_html=True)

    budget_data, err = _get("/budget")
    if err == "offline":
        _offline_banner()
        return

    budget_data = budget_data or {}

    # ── Budget limits ──
    st.markdown('<div class="sec-head">Monthly Budget Limits</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">A warning banner appears on your dashboard when your latest bill approaches or exceeds these limits</div>', unsafe_allow_html=True)

    with st.form("budget_form"):
        b1, b2 = st.columns(2)
        with b1:
            gbp_limit = st.number_input(
                "Monthly £ limit",
                min_value=0.0, step=10.0,
                value=float(budget_data.get("budget_monthly_gbp") or 0),
                help="Leave 0 to disable cost alerts",
            )
        with b2:
            kwh_limit = st.number_input(
                "Monthly kWh limit",
                min_value=0, step=50,
                value=int(budget_data.get("budget_monthly_kwh") or 0),
                help="Leave 0 to disable usage alerts",
            )
        saved = st.form_submit_button("💾 Save Budget Limits", use_container_width=True)
        if saved:
            payload = {
                "budget_monthly_gbp": gbp_limit if gbp_limit > 0 else None,
                "budget_monthly_kwh": kwh_limit if kwh_limit > 0 else None,
            }
            r = requests.put(f"{_api_url()}/budget", json=payload, headers=_auth_headers())
            if r.status_code == 200:
                st.success("Budget limits saved. The dashboard will now show a warning if your latest bill gets close.")
            else:
                st.error(r.json().get("detail", "Could not save."))

    # ── Live status ──
    status, _ = _get("/budget/status")
    if status and (status.get("budget_monthly_gbp") or status.get("budget_monthly_kwh")):
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Current Status</div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)
        for col, label, val, limit, pct, status_key in [
            (sc1, "Cost (£)", status.get("latest_cost"), status.get("budget_monthly_gbp"),
             status.get("cost_pct"), status.get("cost_status")),
            (sc2, "Usage (kWh)", status.get("latest_kwh"), status.get("budget_monthly_kwh"),
             status.get("kwh_pct"), status.get("kwh_status")),
        ]:
            if limit:
                color = "#EF4444" if status_key == "exceeded" else "#F59E0B" if status_key == "warning" else "#10B981"
                bar_pct = min(pct or 0, 100)
                with col:
                    st.markdown(f"""<div style="background:#0C1525; border:1px solid #1A2840;
                        border-radius:12px; padding:16px 18px;">
                        <div style="font-size:0.75rem; color:#4B6280; text-transform:uppercase;
                            letter-spacing:0.05em; margin-bottom:6px;">{label}</div>
                        <div style="font-size:1.4rem; font-weight:800; color:#F1F5F9; margin-bottom:8px;">
                            {f'£{val:.2f}' if '£' in label else f'{val} kWh'} <span style="font-size:0.75rem;
                            color:#4B6280;">/ {f'£{limit:.0f}' if '£' in label else f'{limit} kWh'}</span>
                        </div>
                        <div style="background:#1A2840; border-radius:20px; height:8px; overflow:hidden;">
                            <div style="background:{color}; width:{bar_pct}%; height:100%;
                                border-radius:20px; transition:width 0.4s;"></div>
                        </div>
                        <div style="font-size:0.75rem; color:{color}; margin-top:6px; font-weight:600;">
                            {pct:.0f}% used {'— EXCEEDED' if status_key == 'exceeded' else '— approaching limit' if status_key == 'warning' else '— within budget'}
                        </div>
                    </div>""" if val else f"""<div style="background:#0C1525; border:1px solid #1A2840;
                        border-radius:12px; padding:16px 18px; color:#4B6280; font-size:0.85rem;">
                        No recent {label.split()[0].lower()} data yet.</div>""",
                        unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Email alerts ──
    st.markdown('<div class="sec-head">Email Alerts</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Get notified automatically when your usage spikes on a new bill</div>', unsafe_allow_html=True)

    email_on = bool(budget_data.get("email_alerts", False))

    smtp_configured = True  # optimistic; actual send will reveal if not

    al1, al2 = st.columns([2, 1])
    with al1:
        st.markdown(f"""<div style="background:#0C1525; border:1px solid #1A2840; border-radius:12px; padding:18px 20px;">
            <div style="font-size:0.88rem; color:#CBD5E1; font-weight:700; margin-bottom:6px;">
                {'🔔 Email alerts are <span style="color:#10B981;">ON</span>' if email_on
                 else '🔕 Email alerts are <span style="color:#4B6280;">OFF</span>'}
            </div>
            <div style="font-size:0.8rem; color:#64748B; line-height:1.6;">
                When enabled:<br/>
                • <b style="color:#94A3B8;">Spike alert</b> — sent automatically when you upload a bill with &gt;15% more usage than your previous bill<br/>
                • <b style="color:#94A3B8;">Weekly summary</b> — send manually below, or trigger from here anytime
            </div>
        </div>""", unsafe_allow_html=True)
    with al2:
        toggle_label = "🔕 Disable Alerts" if email_on else "🔔 Enable Alerts"
        toggle_color = "#EF4444" if email_on else "#10B981"
        if st.button(toggle_label, use_container_width=True):
            r = requests.put(
                f"{_api_url()}/budget",
                json={"email_alerts": not email_on},
                headers=_auth_headers(),
            )
            if r.status_code == 200:
                st.rerun()
            else:
                st.error("Could not update.")

    if email_on:
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Send a Test Email</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Sends a weekly summary email to your Google account right now</div>', unsafe_allow_html=True)
        if st.button("📧 Send Weekly Summary Now", use_container_width=True):
            with st.spinner("Sending email…"):
                r = requests.post(f"{_api_url()}/alerts/weekly-summary", headers=_auth_headers())
                if r.status_code == 200:
                    user_email = st.session_state.get("user", {}).get("email", "your inbox")
                    st.success(f"Email sent! Check {user_email}.")
                else:
                    detail = r.json().get("detail", "Failed.")
                    if "SMTP" in detail:
                        st.error("Email service is not configured yet. Please contact the administrator.")
                    else:
                        st.error(detail)
    else:
        st.markdown("""<div class="info-box" style="margin-top:12px;">
            🔕 Enable alerts above, then configure SMTP in your <code>.env</code> file to receive emails.
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Due date reminders ──
    st.markdown('<div class="sec-head">Bill Due Date Reminders</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Check for bills due soon and send reminder emails</div>', unsafe_allow_html=True)

    upcoming_data, _ = _get("/alerts/upcoming-dues?days_ahead=7")
    if upcoming_data:
        for due in upcoming_data:
            _dl = due["days_left"]
            _dc = "#EF4444" if _dl == 0 else "#F59E0B" if _dl <= 2 else "#1D4ED8"
            _dw = "TODAY" if _dl == 0 else "TOMORROW" if _dl == 1 else f"in {_dl} days"
            st.markdown(f"""<div style="background:{_dc}11; border:1px solid {_dc}44;
                border-left:3px solid {_dc}; border-radius:10px;
                padding:12px 16px; margin-bottom:8px; font-size:0.87rem; color:#CBD5E1;">
                💳 <b>{due['provider']}</b> · £{due['amount_due']:.2f}
                · Due <b style="color:{_dc};">{_dw}</b> ({due['due_date']})
            </div>""", unsafe_allow_html=True)
        if email_on:
            remind_col, _ = st.columns([1, 2])
            with remind_col:
                if st.button("📧 Send Reminders Now", use_container_width=True):
                    with st.spinner("Sending…"):
                        r = requests.post(f"{_api_url()}/alerts/check-due-dates?days_ahead=7", headers=_auth_headers())
                        if r.status_code == 200:
                            d = r.json()
                            st.success(f"Sent {d['reminders_sent']} reminder(s).")
                        else:
                            st.error(r.json().get("detail", "Failed."))
    else:
        st.markdown('<div class="info-box">✅ No bills due in the next 7 days.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Usage Goal Tracker ──
    st.markdown('<div class="sec-head">Usage Reduction Goal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Set a target and track your progress on the dashboard</div>', unsafe_allow_html=True)

    goal_data, _ = _get("/goal")
    goal_data = goal_data or {}

    with st.form("goal_form"):
        gc1, gc2 = st.columns(2)
        with gc1:
            goal_pct = st.number_input(
                "Reduction target (%)",
                min_value=1, max_value=50, step=1,
                value=int(goal_data.get("goal_reduction_pct") or 10),
                help="e.g. 10 = reduce your average monthly usage by 10%",
            )
        with gc2:
            baseline = goal_data.get("goal_baseline_kwh")
            st.metric("Baseline avg kWh", f"{baseline:.0f} kWh" if baseline else "Auto-set on save")
        if st.form_submit_button("🎯 Set Goal", use_container_width=True):
            r = requests.put(f"{_api_url()}/goal", json={"goal_reduction_pct": float(goal_pct)}, headers=_auth_headers())
            if r.status_code == 200:
                d = r.json()
                _base = d.get("goal_baseline_kwh")
                _tgt  = d.get("target_kwh")
                if _base and _tgt:
                    st.success(f"Goal set: reduce by {goal_pct}% from {_base:.0f} kWh baseline → target {_tgt:.0f} kWh/bill.")
                else:
                    st.success(f"Goal set to {goal_pct}% reduction. Upload bills with kWh data to track progress.")
                st.rerun()
            else:
                st.error(r.json().get("detail", "Could not save goal."))

    if goal_data.get("goal_reduction_pct"):
        _gpct  = goal_data.get("progress_pct") or 0
        _gtgt  = goal_data.get("target_kwh")
        _gcurr = goal_data.get("current_avg_kwh")
        _on    = goal_data.get("on_track")
        _gc    = "#10B981" if _on else "#F59E0B"
        st.markdown(f"""<div style="background:#0C1525; border:1px solid #1A2840; border-radius:12px; padding:16px 18px; margin-top:12px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="color:#94A3B8; font-size:0.85rem;">Current avg: <b style="color:#F1F5F9;">{_gcurr:.0f} kWh</b></span>
                <span style="color:#94A3B8; font-size:0.85rem;">Target: <b style="color:{_gc};">{_gtgt:.0f} kWh</b></span>
                <span style="color:{_gc}; font-size:0.85rem; font-weight:700;">{_gpct:.0f}% complete {'✅' if _on else ''}</span>
            </div>
            <div style="background:#1A2840; border-radius:20px; height:12px; overflow:hidden;">
                <div style="background:{_gc}; width:{min(_gpct,100):.0f}%; height:100%; border-radius:20px;"></div>
            </div>
        </div>""" if _gcurr and _gtgt else "", unsafe_allow_html=True)


# ─── PAGE: SETTINGS ────────────────────────────────────────────────────────────

def page_settings():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>Settings</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>Configure your Smart Energy Auditor</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Backend</div>', unsafe_allow_html=True)
    current_url = _api_url()
    with st.form("settings"):
        new_url = st.text_input("API URL", value=current_url)
        if st.form_submit_button("Save"):
            st.session_state["api_url"] = new_url.rstrip("/")
            st.success(f"API URL updated to {new_url.rstrip('/')} for this session.")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Reports</div>', unsafe_allow_html=True)
    rep_col, _ = st.columns([1, 2])
    with rep_col:
        if st.button("📄 Download PDF Report", use_container_width=True):
            with st.spinner("Generating PDF…"):
                try:
                    r = requests.get(
                        f"{_api_url()}/report/pdf",
                        headers=_auth_headers(),
                        timeout=20,
                    )
                    if r.status_code == 200:
                        st.download_button(
                            "⬇ Save PDF",
                            data=r.content,
                            file_name="energy_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    else:
                        st.error(r.json().get("detail", "Could not generate report."))
                except requests.exceptions.ConnectionError:
                    _offline_banner()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">About</div>', unsafe_allow_html=True)
    st.markdown("""<div class="card-sm" style="color:#64748B; font-size:0.86rem; line-height:2;">
        <b style="color:#CBD5E1;">Smart Energy Auditor</b> v0.3.0<br/>
        Stack: FastAPI · SQLAlchemy · Tesseract OCR · pdf2image · Streamlit · Plotly<br/>
        ML: Prophet · Gradient Boosting · KMeans · IsolationForest · Ruptures PELT<br/>
        Providers: British Gas · Scottish Power · Octopus Energy · E.ON Next · OVO Energy · EDF Energy · nPower · Utilita · Shell Energy<br/>
        Carbon intensity: <b style="color:#10B981;">0.197 kg CO₂/kWh</b> (UK National Grid 2024)
    </div>""", unsafe_allow_html=True)


# ─── PAGE: PROFILE ─────────────────────────────────────────────────────────────

def page_profile():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>My Profile</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>Manage your account and view personal stats</div>
    </div>
    """, unsafe_allow_html=True)

    me = st.session_state.get("me", {})
    stats, _ = _get("/stats")

    # ── Account card ──
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="sec-head">Account Details</div>', unsafe_allow_html=True)

        avatar_letter = (me.get("name") or me.get("email", "U"))[0].upper()
        st.markdown(f"""
        <div class="card" style="display:flex;align-items:center;gap:20px;margin-bottom:1rem;">
            <div style="width:64px;height:64px;border-radius:50%;
                background:linear-gradient(135deg,#00C9B8,#1D4ED8);
                display:flex;align-items:center;justify-content:center;
                font-size:1.6rem;font-weight:800;color:#fff;flex-shrink:0;">
                {avatar_letter}
            </div>
            <div>
                <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;">
                    {me.get('name') or 'No name set'}
                </div>
                <div style="font-size:0.82rem;color:#4B6280;margin-top:3px;">{me.get('email','')}</div>
                <div style="font-size:0.72rem;color:#1D4ED8;margin-top:5px;
                    background:rgba(29,78,216,0.1);border:1px solid rgba(29,78,216,0.25);
                    border-radius:999px;padding:2px 10px;display:inline-block;">
                    {'Admin' if me.get('is_admin') else 'Standard user'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-head">Edit Display Name</div>', unsafe_allow_html=True)
        with st.form("update_name_form"):
            new_name = st.text_input("Display name", value=me.get("name") or "", placeholder="e.g. Sami Shemanto")
            if st.form_submit_button("💾 Save name", use_container_width=True):
                if new_name.strip():
                    r = requests.put(
                        f"{_api_url()}/auth/me/name",
                        json={"name": new_name.strip()},
                        headers=_auth_headers(),
                        timeout=8,
                    )
                    if r.status_code == 200:
                        st.session_state["me"]["name"] = r.json()["name"]
                        st.success("Name updated!")
                        st.rerun()
                    else:
                        st.error("Could not update name.")
                else:
                    st.warning("Name cannot be empty.")

    with col_right:
        st.markdown('<div class="sec-head">Your Stats</div>', unsafe_allow_html=True)

        total_bills  = stats["total_bills"]      if stats else 0
        total_spend  = stats["total_spend"]      if stats else 0.0
        avg_kwh      = stats["avg_monthly_kwh"]  if stats else 0.0
        total_carbon = stats["total_carbon_kg"]  if stats else 0.0

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:1rem;">
            <div class="kpi">
                <div class="kpi-icon">📄</div>
                <div class="kpi-label">Bills Uploaded</div>
                <div class="kpi-val">{total_bills}</div>
            </div>
            <div class="kpi">
                <div class="kpi-icon">💷</div>
                <div class="kpi-label">Total Spend</div>
                <div class="kpi-val">£{total_spend:,.2f}</div>
            </div>
            <div class="kpi">
                <div class="kpi-icon">⚡</div>
                <div class="kpi-label">Avg Monthly kWh</div>
                <div class="kpi-val">{avg_kwh:,.0f}</div>
            </div>
            <div class="kpi">
                <div class="kpi-icon">🌿</div>
                <div class="kpi-label">Total CO₂</div>
                <div class="kpi-val">{total_carbon:.0f} kg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Provider breakdown ──
        providers = stats.get("providers", {}) if stats else {}
        if providers:
            st.markdown('<div class="sec-head">Providers Used</div>', unsafe_allow_html=True)
            for prov, cnt in sorted(providers.items(), key=lambda x: -x[1]):
                pct = cnt / total_bills * 100 if total_bills else 0
                st.markdown(f"""
                <div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;
                        font-size:0.82rem;color:#94A3B8;margin-bottom:4px;">
                        <span>{prov}</span><span>{cnt} bill{'s' if cnt != 1 else ''}</span>
                    </div>
                    <div style="background:#0A1018;border-radius:999px;height:6px;overflow:hidden;">
                        <div style="background:linear-gradient(90deg,#00C9B8,#1D4ED8);
                            width:{pct:.0f}%;height:100%;border-radius:999px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Danger zone ──
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head" style="color:#EF4444;">Danger Zone</div>', unsafe_allow_html=True)
    with st.expander("Delete my account"):
        st.markdown("""
        <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);
            border-radius:10px;padding:14px;color:#EF4444;font-size:0.85rem;margin-bottom:12px;">
            ⚠️ This will permanently delete your account and <b>all your bills</b>.
            This action cannot be undone.
        </div>
        """, unsafe_allow_html=True)
        confirm = st.text_input("Type DELETE to confirm", key="delete_confirm_input")
        if st.button("🗑 Permanently delete my account", type="primary", use_container_width=True):
            if confirm == "DELETE":
                r = requests.delete(f"{_api_url()}/auth/me", headers=_auth_headers(), timeout=8)
                if r.status_code == 200:
                    st.session_state.pop("token", None)
                    st.session_state.pop("me", None)
                    st.success("Account deleted. Redirecting…")
                    st.rerun()
                else:
                    st.error("Could not delete account.")
            else:
                st.error("Please type DELETE (in caps) to confirm.")


# ─── PAGE: ADMIN ───────────────────────────────────────────────────────────────

def page_admin():
    st.markdown("""
    <div style='margin-bottom:1.4rem;'>
        <div style='font-size:1.7rem; font-weight:800; color:#F1F5F9;'>Admin Control Panel</div>
        <div style='color:#4B6280; font-size:0.88rem; margin-top:5px;'>System-wide overview — visible only to admins</div>
    </div>
    """, unsafe_allow_html=True)

    # ── System stats ──
    stats, err = _get("/admin/stats")
    if err == "offline":
        _offline_banner()
        return
    if err:
        st.error(f"Access denied or error: {err}")
        return

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi"><div class="kpi-icon">👥</div>
            <div class="kpi-label">Total Users</div>
            <div class="kpi-val">{stats['total_users']}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi"><div class="kpi-icon">📄</div>
            <div class="kpi-label">Total Bills</div>
            <div class="kpi-val">{stats['total_bills']}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi"><div class="kpi-icon">💷</div>
            <div class="kpi-label">Total Spend</div>
            <div class="kpi-val">£{stats['total_spend']:,.2f}</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi"><div class="kpi-icon">🌿</div>
            <div class="kpi-label">Total CO₂</div>
            <div class="kpi-val">{stats['total_carbon_kg']} kg</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Users table ──
    st.markdown('<div class="sec-head">All Users</div>', unsafe_allow_html=True)
    users, _ = _get("/admin/users")
    if users:
        for u in users:
            admin_tag = " 🔴 ADMIN" if u.get("is_admin") else ""
            joined = u.get("created_at", "")[:10] if u.get("created_at") else "N/A"
            with st.expander(f"#{u['id']}  ·  {u.get('name') or u['email']}{admin_tag}  ·  {u['bill_count']} bill(s)  ·  Joined {joined}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"""
                    <div style="font-size:0.85rem; color:#94A3B8; line-height:2;">
                        <b style="color:#CBD5E1;">Email:</b> {u['email']}<br/>
                        <b style="color:#CBD5E1;">Name:</b> {u.get('name') or 'N/A'}<br/>
                        <b style="color:#CBD5E1;">Bills:</b> {u['bill_count']}<br/>
                        <b style="color:#CBD5E1;">Admin:</b> {'Yes' if u.get('is_admin') else 'No'}
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if not u.get("is_admin"):
                        if st.button(f"🗑 Delete user #{u['id']}", key=f"del_user_{u['id']}"):
                            r = requests.delete(
                                f"{_api_url()}/admin/users/{u['id']}",
                                headers=_auth_headers(),
                            )
                            if r.status_code == 200:
                                st.success("User deleted.")
                                st.rerun()
                            else:
                                st.error(r.json().get("detail", "Error"))
    else:
        st.markdown('<div class="info-box">No users found.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── All bills table ──
    st.markdown('<div class="sec-head">All Bills</div>', unsafe_allow_html=True)
    all_bills, _ = _get("/admin/bills")
    if all_bills:
        for b in all_bills:
            amount = f"£{b['amount_due']:.2f}" if b.get("amount_due") else "N/A"
            kwh    = f"{b['usage_kwh']} kWh" if b.get("usage_kwh") else "N/A"
            with st.expander(f"#{b['id']}  ·  {b['provider']}  ·  {amount}  ·  {b.get('user_email','?')}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"""
                    <div style="font-size:0.85rem; color:#94A3B8; line-height:2;">
                        <b style="color:#CBD5E1;">Provider:</b> {b['provider']}<br/>
                        <b style="color:#CBD5E1;">Amount:</b> {amount}<br/>
                        <b style="color:#CBD5E1;">Usage:</b> {kwh}<br/>
                        <b style="color:#CBD5E1;">CO₂:</b> {b.get('carbon_kg') or 'N/A'} kg<br/>
                        <b style="color:#CBD5E1;">Owner:</b> {b.get('user_email','Unknown')}
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button(f"🗑 Delete bill #{b['id']}", key=f"del_bill_{b['id']}"):
                        r = requests.delete(
                            f"{_api_url()}/admin/bills/{b['id']}",
                            headers=_auth_headers(),
                        )
                        if r.status_code == 200:
                            st.success("Bill deleted.")
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Error"))
    else:
        st.markdown('<div class="info-box">No bills in the system.</div>', unsafe_allow_html=True)


# ─── ROUTING ───────────────────────────────────────────────────────────────────

if not _is_logged_in:
    page_login()
else:
    pages = {
        "Dashboard":   page_dashboard,
        "Upload Bill": page_upload,
        "History":     page_history,
        "Insights":    page_insights,
        "Alerts":      page_alerts,
        "Profile":     page_profile,
        "Settings":    page_settings,
        "Admin":       page_admin,
    }
    pages.get(selected, page_dashboard)()
