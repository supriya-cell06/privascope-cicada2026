"""PRIVASCOPE — Privacy-First Intelligent Observability & AIOps Platform."""
import time
import streamlit as st

from config import APP_NAME, APP_SUBTITLE, TENANTS
from dashboard.aiops_page import render_aiops
from dashboard.autonomous_page import render_autonomous_ops
from dashboard.collector_page import render_collector_fleet, render_local_collector
from dashboard.incident_page import render_incidents
from dashboard.infrastructure_page import render_infrastructure
from dashboard.network_page import render_network
from dashboard.overview import render_overview
from dashboard.privacy_page import render_privacy_audit
from dashboard.security_page import render_security
from dashboard.settings_page import render_settings
from dashboard.styles import inject_css, page_header
from dashboard.tenant_page import render_tenant_management
from data.simulation import SCENARIO_NAMES, TelemetrySimulator
from database.db import DatabaseManager
from utils.auth import (
    USERS_DB,
    authenticate_api_key,
    authenticate_password_mfa,
    generate_totp,
)

st.set_page_config(
    page_title=f"{APP_NAME} | {APP_SUBTITLE}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


@st.cache_resource
def get_services():
    db = DatabaseManager()
    sim = TelemetrySimulator(db)
    sim.ensure_seeded()
    return db, sim


db, simulator = get_services()


def render_login_gate():
    st.markdown(
        f"""
        <div class="login-hero">
            <div class="login-title">🛡️ {APP_NAME}</div>
            <div style="color:#94A3B8; font-size:1.04rem; margin-bottom:14px;">{APP_SUBTITLE}</div>
            <div>
                <span class="pill pill-cyan">TWO-TIER PRIVACY ARCHITECTURE</span>
                <span class="pill pill-green">HMAC-SHA256 + HASH-CHAINED LEDGER</span>
                <span class="pill pill-purple">ISOLATION FOREST AIOPS</span>
                <span class="pill pill-amber">MFA + RBAC ZERO-TRUST</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 2, 1])
    with center:
        tab1, tab2, tab3 = st.tabs([
            "🔐 Password + TOTP MFA",
            "🔑 Enterprise API Key",
            "⚡ Judge Quick-Login",
        ])

        with tab1:
            st.caption("PBKDF2-SHA256 Password Verification + Live RFC 6238 6-Digit TOTP Authenticator")
            uname = st.selectbox("Account", ["admin", "analyst", "auditor"])
            live_code = generate_totp(USERS_DB[uname]["totp_secret"])
            st.info(f"📱 **Demo Authenticator App (Live TOTP for `{uname}`):** `{live_code}` (refreshes every 30s)")

            pwd = st.text_input(
                "Password",
                type="password",
                value="Admin@2026" if uname == "admin" else ("Analyst@2026" if uname == "analyst" else "Auditor@2026"),
            )
            otp = st.text_input("6-Digit MFA Code", value=live_code, max_chars=6)
            if st.button("Authenticate with MFA", type="primary", use_container_width=True):
                user, msg = authenticate_password_mfa(uname, pwd, otp)
                if user:
                    st.session_state["auth_user"] = user
                    st.rerun()
                else:
                    st.error(msg)

        with tab2:
            st.caption("Service-to-Service / CLI Token Authentication")
            api_key = st.text_input("Enterprise API Key", type="password", placeholder="pk_live_soc_admin_2026")
            st.caption("Demo Keys: `pk_live_soc_admin_2026` (Admin) | `pk_live_sec_analyst_2026` (Analyst) | `pk_live_priv_auditor_2026` (Auditor)")
            if st.button("Authenticate with API Key", type="primary", use_container_width=True):
                user, msg = authenticate_api_key(api_key)
                if user:
                    st.session_state["auth_user"] = user
                    st.rerun()
                else:
                    st.error(msg)

        with tab3:
            st.caption("One-click role switching for live hackathon presentation")
            q1, q2, q3 = st.columns(3)
            with q1:
                if st.button("SOC Admin", type="primary", use_container_width=True):
                    u = USERS_DB["admin"]
                    st.session_state["auth_user"] = {
                        "username": u["username"], "full_name": u["full_name"],
                        "role": u["role"], "permissions": u["permissions"],
                        "auth_method": "Quick-Login (SOC Admin)",
                    }
                    st.rerun()
            with q2:
                if st.button("Security Analyst", use_container_width=True):
                    u = USERS_DB["analyst"]
                    st.session_state["auth_user"] = {
                        "username": u["username"], "full_name": u["full_name"],
                        "role": u["role"], "permissions": u["permissions"],
                        "auth_method": "Quick-Login (Analyst)",
                    }
                    st.rerun()
            with q3:
                if st.button("Privacy Auditor", use_container_width=True):
                    u = USERS_DB["auditor"]
                    st.session_state["auth_user"] = {
                        "username": u["username"], "full_name": u["full_name"],
                        "role": u["role"], "permissions": u["permissions"],
                        "auth_method": "Quick-Login (Auditor)",
                    }
                    st.rerun()


if "auth_user" not in st.session_state or not st.session_state["auth_user"]:
    render_login_gate()
    st.stop()

user = st.session_state["auth_user"]

# ---- CLEAN 4-DOMAIN FEATURE SEPARATION ----
NAV_DOMAINS = {
    "📊 Tier 2 — Observability": [
        "1. Executive Overview",
        "2. Infrastructure Monitoring",
        "3. Network Monitoring",
        "4. Security Monitoring",
    ],
    "🧠 Tier 2 — AIOps & Automation": [
        "5. AIOps Intelligence",
        "6. Incident Correlation",
        "10. Autonomous Operations",
    ],
    "🛡️ Tier 1 — Privacy & Collectors": [
        "7. Local Privacy Collector",
        "8. Egress Proof & Privacy Audit",
        "9. Collector Fleet Health",
    ],
    "⚙️ Governance & Platform": [
        "11. Tenant Management",
        "12. System Settings",
    ],
}

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">🛡️ {APP_NAME}</div>
            <div style="font-size:0.74rem; color:#94A3B8; margin-top:4px;">
                👤 <b>{user['full_name']}</b><br/>
                Role: <code>{user['role']}</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Sign Out", use_container_width=True):
        st.session_state["auth_user"] = None
        st.rerun()

    st.markdown('<div class="sidebar-section-label">Tenant Boundary</div>', unsafe_allow_html=True)
    selected_tenant = st.selectbox("Active Tenant", TENANTS, index=0, label_visibility="collapsed")

    st.markdown('<div class="sidebar-section-label">Workspace Module</div>', unsafe_allow_html=True)
    selected_domain = st.selectbox("Module", list(NAV_DOMAINS.keys()), label_visibility="collapsed")
    selected_page = st.radio("Pages", NAV_DOMAINS[selected_domain], label_visibility="collapsed")

    st.divider()
    st.markdown('<div class="sidebar-section-label">Hackathon Demo Scenarios</div>', unsafe_allow_html=True)
    selected_scenario = st.selectbox("Scenario", SCENARIO_NAMES, label_visibility="collapsed")
    sc1, sc2 = st.columns(2)
    with sc1:
        if st.button("Run Scenario", type="primary", use_container_width=True):
            simulator.run_scenario(selected_scenario, selected_tenant)
            st.rerun()
    with sc2:
        if st.button("Reset Demo", use_container_width=True):
            simulator.seed_baseline()
            st.rerun()

    st.divider()
    st.markdown('<div class="sidebar-section-label">Real-Time Engine</div>', unsafe_allow_html=True)
    live_mode = st.toggle("Live Auto-Stream (5s)", value=False)
    if st.button("Generate Telemetry Tick", use_container_width=True):
        simulator.generate_tick(selected_tenant)
        st.rerun()

# ---- TOP SECURITY & ARCHITECTURE STATUS BAR ----
saas_online = simulator.collector.transmitter.is_saas_online()
dp_on = db.get_state("differential_privacy", "false").lower() == "true"
st.markdown(
    f"""
    <div class="top-banner">
        <div>
            <span class="pill pill-cyan">TENANT: {selected_tenant.upper()}</span>
            <span class="pill {'pill-green' if saas_online else 'pill-red'}">SAAS LINK: {'ONLINE' if saas_online else 'OFFLINE (BUFFERING)'}</span>
            <span class="pill pill-green">HMAC-SHA256 SIGNED</span>
            <span class="pill pill-purple">{'ε-DIFF PRIVACY: ON' if dp_on else 'ALLOW-LIST: STRICT'}</span>
        </div>
        <div style="font-size:0.78rem; color:#94A3B8;">
            Auth: <b>{user['auth_method']}</b> &nbsp;|&nbsp; Role: <b>{user['role']}</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- PAGE ROUTING WITH TIERED HEADERS ----
if selected_page == "1. Executive Overview":
    page_header("TIER 2 • CENTRAL SAAS OBSERVABILITY", "Executive Overview", f"Real-time health, telemetry trends, and active incident posture for {selected_tenant}", "#38BDF8")
    render_overview(db, selected_tenant)
elif selected_page == "2. Infrastructure Monitoring":
    page_header("TIER 2 • CENTRAL SAAS OBSERVABILITY", "Infrastructure Monitoring", "Servers, VMs, containers, applications, databases, and stale-data detection", "#38BDF8")
    render_infrastructure(db, selected_tenant)
elif selected_page == "3. Network Monitoring":
    page_header("TIER 2 • CENTRAL SAAS OBSERVABILITY", "Network Monitoring", "Bandwidth, inbound/outbound traffic, latency, packet loss, and outage impact analysis", "#38BDF8")
    render_network(db, simulator, selected_tenant)
elif selected_page == "4. Security Monitoring":
    page_header("TIER 2 • CENTRAL SAAS OBSERVABILITY", "Security Monitoring", "Privacy-preserving threat visibility — raw passwords & PII never leave Tier 1", "#EF4444")
    render_security(db, simulator, selected_tenant)
elif selected_page == "5. AIOps Intelligence":
    page_header("TIER 2 • AIOPS ENGINE", "AIOps Intelligence", "Explainable Scikit-learn Isolation Forest anomaly detection with statistical Z-score fallback", "#A855F7")
    render_aiops(db, selected_tenant)
elif selected_page == "6. Incident Correlation":
    page_header("TIER 2 • AIOPS ENGINE", "Incident Correlation & Alert Queue", "Correlates multi-signal alerts into root-cause incidents with confidence scoring", "#A855F7")
    render_incidents(db, selected_tenant)
elif selected_page == "7. Local Privacy Collector":
    page_header("TIER 1 • ON-PREMISE PRIVACY BOUNDARY", "Local Privacy Collector", "Side-by-side Local vs. Cloud proof, strict allow-list enforcement, and SQLite outage buffering", "#10B981")
    render_local_collector(db, simulator, selected_tenant)
elif selected_page == "8. Egress Proof & Privacy Audit":
    page_header("TIER 1 • CRYPTOGRAPHIC EGRESS PROOF", "Egress Proof & Privacy Audit", "Tamper-evident SHA-256 hash-chained ledger, HMAC-SHA256 verification, and ε-Differential Privacy", "#10B981")
    render_privacy_audit(db, selected_tenant)
elif selected_page == "9. Collector Fleet Health":
    page_header("TIER 1 • AGENT FLEET", "Collector Fleet Health", "Heartbeat monitoring with 60-second offline detection target and recovery controls", "#10B981")
    render_collector_fleet(db, simulator, selected_tenant)
elif selected_page == "10. Autonomous Operations":
    page_header("TIER 2 • HUMAN-IN-THE-LOOP AUTOMATION", "Autonomous Operations", "RBAC-gated remediation proposals with Approve, Reject, Simulate Execute, and Rollback", "#F59E0B")
    render_autonomous_ops(db, selected_tenant)
elif selected_page == "11. Tenant Management":
    page_header("GOVERNANCE • MULTI-TENANT ISOLATION", "Tenant Management", "Strict SQL-level tenant isolation across Tenant Alpha, Tenant Beta, and Tenant Gamma", "#38BDF8")
    render_tenant_management(db, selected_tenant)
elif selected_page == "12. System Settings":
    page_header("GOVERNANCE • PLATFORM CONFIGURATION", "System Settings & Performance Targets", "Dynamic health thresholds and live prototype performance measurements", "#38BDF8")
    render_settings(db, selected_tenant)

# Real-time streaming refresh loop
if live_mode:
    time.sleep(5)
    simulator.generate_tick(selected_tenant)
    st.rerun()
