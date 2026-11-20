"""Executive SOC/AIOps UI/UX Design System for PRIVASCOPE."""
import streamlit as st

DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Deep Navy-Obsidian Enterprise Canvas */
    .stApp {
        background: radial-gradient(circle at 12% 8%, #132240 0%, #090F1E 48%, #050811 100%);
        color: #E2E8F0;
    }

    /* Sidebar Polish */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0C1426 0%, #070C17 100%);
        border-right: 1px solid rgba(56, 189, 248, 0.18);
    }
    .sidebar-brand {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.16), rgba(139, 92, 246, 0.14));
        border: 1px solid rgba(56, 189, 248, 0.30);
        border-radius: 12px;
        padding: 14px 14px 12px 14px;
        margin-bottom: 12px;
    }
    .sidebar-brand-title {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        background: linear-gradient(90deg, #38BDF8, #34D399, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .sidebar-section-label {
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        color: #64748B;
        margin: 14px 0 6px 2px;
    }

    /* Top Command Bar */
    .top-banner {
        background: linear-gradient(90deg, rgba(15, 23, 42, 0.90), rgba(17, 24, 39, 0.85));
        border: 1px solid rgba(56, 189, 248, 0.24);
        border-radius: 12px;
        padding: 10px 18px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(12px);
    }

    /* Page Hero Header */
    .page-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(30, 41, 59, 0.45));
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-left: 4px solid #38BDF8;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }
    .page-header-tier {
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: #38BDF8;
        margin-bottom: 4px;
    }
    .page-header-title {
        font-size: 1.55rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0 0 4px 0;
    }
    .page-header-sub {
        font-size: 0.88rem;
        color: #94A3B8;
        margin: 0;
    }

    /* Status Pills */
    .pill {
        display: inline-block;
        padding: 4px 11px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-right: 6px;
    }
    .pill-cyan { background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.38); }
    .pill-green { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.38); }
    .pill-purple { background: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.38); }
    .pill-amber { background: rgba(245, 158, 11, 0.16); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.42); }
    .pill-red { background: rgba(239, 68, 68, 0.18); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.45); }

    /* Elevated KPI Cards */
    .kpi-card {
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.94), rgba(30, 41, 59, 0.68));
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.28);
        transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.45);
        box-shadow: 0 12px 26px rgba(14, 165, 233, 0.14);
    }
    .kpi-label {
        font-size: 0.72rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 5px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.72rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.15;
    }
    .kpi-sub {
        font-size: 0.74rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* Tier 1 vs Tier 2 Split Panels */
    .panel-local {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.34), rgba(31, 18, 21, 0.92));
        border: 1px solid rgba(239, 68, 68, 0.48);
        border-radius: 10px;
        padding: 12px 16px;
        color: #FCA5A5;
        margin-bottom: 10px;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .panel-cloud {
        background: linear-gradient(135deg, rgba(6, 95, 70, 0.34), rgba(13, 31, 26, 0.92));
        border: 1px solid rgba(16, 185, 129, 0.48);
        border-radius: 10px;
        padding: 12px 16px;
        color: #6EE7B7;
        margin-bottom: 10px;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .pipeline-box {
        background: linear-gradient(90deg, rgba(14, 165, 233, 0.14), rgba(16, 185, 129, 0.10), rgba(168, 85, 247, 0.14));
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
        font-weight: 700;
        font-size: 0.84rem;
        color: #38BDF8;
        letter-spacing: 0.04em;
        margin: 8px 0 18px 0;
    }

    /* Login Hero */
    .login-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.90));
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 16px;
        padding: 30px 34px;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 20px 48px rgba(0, 0, 0, 0.50);
    }
    .login-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #34D399, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }

    /* Tabs & Buttons Polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.55);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(148, 163, 184, 0.14);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 10px;
        overflow: hidden;
    }
</style>
"""

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15, 23, 42, 0.65)",
    font=dict(color="#E2E8F0", size=12, family="Inter"),
    margin=dict(l=35, r=20, t=42, b=35),
    xaxis=dict(gridcolor="rgba(51, 65, 85, 0.42)", zerolinecolor="#1E293B"),
    yaxis=dict(gridcolor="rgba(51, 65, 85, 0.42)", zerolinecolor="#1E293B"),
    legend=dict(bgcolor="rgba(15, 23, 42, 0.6)", bordercolor="rgba(148, 163, 184, 0.15)", borderwidth=1),
)


def inject_css():
    st.markdown(DARK_CSS, unsafe_allow_html=True)


def page_header(tier_label: str, title: str, subtitle: str, accent: str = "#38BDF8"):
    st.markdown(
        f"""
        <div class="page-header" style="border-left-color: {accent};">
            <div class="page-header-tier" style="color: {accent};">{tier_label}</div>
            <div class="page-header-title">{title}</div>
            <div class="page-header-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value, sub: str = "", accent: str = "#38BDF8"):
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left: 4px solid {accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
