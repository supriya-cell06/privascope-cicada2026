"""Page 7 (Local Privacy Collector) & Page 9 (Collector Fleet Health)."""
import json
import pandas as pd
import streamlit as st

from dashboard.styles import kpi_card
from monitoring.collector_health import evaluate_collectors
from utils.timestamps import utc_now_iso


def render_local_collector(db, simulator, tenant_id: str):
    st.caption("Raw telemetry is processed, filtered, and redacted locally. Only allow-listed metadata leaves Tier 1.")

    # Visual Pipeline
    st.markdown(
        """
        <div class="pipeline-box">RAW TELEMETRY &nbsp;➜&nbsp; LOCAL PROCESSING &nbsp;➜&nbsp; FILTERING & REDACTION &nbsp;➜&nbsp; ALLOW-LIST VALIDATION &nbsp;➜&nbsp; APPROVED METADATA &nbsp;➜&nbsp; CENTRAL SAAS</div>
        """,
        unsafe_allow_html=True,
    )

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        gen_demo = st.button("GENERATE PRIVACY DEMO", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("SIMULATE SAAS OUTAGE", use_container_width=True):
            simulator.collector.transmitter.set_saas_online(False)
            st.warning("Central SaaS connection set to OFFLINE. Outbound metadata will buffer locally in SQLite.")
            st.rerun()
    with col_btn3:
        if st.button("RESTORE CONNECTION", use_container_width=True):
            simulator.collector.transmitter.set_saas_online(True)
            flush_res = simulator.collector.transmitter.flush_buffer(tenant_id)
            st.success(
                f"SaaS RESTORED! Delivered: {flush_res['delivered']}, "
                f"Duplicates Prevented: {flush_res['duplicates_prevented']}, Remaining: {flush_res['remaining']}"
            )
            st.rerun()

    saas_online = simulator.collector.transmitter.is_saas_online()
    pending_buf = simulator.collector.transmitter.buffer.get_pending(tenant_id)
    k1, k2, k3 = st.columns(3)
    with k1: kpi_card("Central SaaS Link", "ONLINE" if saas_online else "OFFLINE", "Tier 1 -> Tier 2 transport", "#10B981" if saas_online else "#EF4444")
    with k2: kpi_card("Local SQLite Buffer", len(pending_buf), "Pending metadata events", "#F59E0B" if pending_buf else "#38BDF8")
    with k3: kpi_card("Privacy Policy", "STRICT ALLOW-LIST", "Zero raw secrets egress", "#10B981")

    if gen_demo:
        res = simulator.trigger_security_event(tenant_id)
        st.session_state["last_privacy_demo"] = res

    audits = db.get_privacy_audits(tenant_id, limit=1)
    demo = st.session_state.get("last_privacy_demo")
    if not demo and audits:
        a = audits[0]
        demo = {
            "raw_telemetry": a["raw_telemetry"],
            "sanitized_payload": a["sanitized_payload"],
            "rejected_fields": a["rejected_fields"],
            "redacted_fields": a["redacted_fields"],
            "policy_status": a["policy_status"],
            "transmission": {"status": a["transmission_status"]},
        }

    if demo:
        st.subheader("Side-by-Side: Local Environment vs Cloud Environment")
        left, right = st.columns(2)
        with left:
            st.markdown('<div class="panel-local"><b>LOCAL ENVIRONMENT (TIER 1 — NEVER LEAVES HOST)</b></div>', unsafe_allow_html=True)
            st.json(demo["raw_telemetry"])
            st.error(f"Rejected Sensitive / Non-Allow-Listed Fields: {', '.join(demo['rejected_fields']) or 'None'}")
        with right:
            st.markdown('<div class="panel-cloud"><b>CLOUD ENVIRONMENT (TIER 2 — APPROVED METADATA ONLY)</b></div>', unsafe_allow_html=True)
            st.json(demo["sanitized_payload"])
            st.success(f"Policy: {demo['policy_status']} | Status: {demo['transmission']['status']}")


def render_collector_fleet(db, simulator, tenant_id: str):
    st.caption("Monitors Tier 1 collector agents with a 60-second offline detection target")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Simulate Collector Offline", use_container_width=True):
            simulator.trigger_collector_offline(tenant_id)
            st.rerun()
    with b2:
        if st.button("Recover All Collectors", use_container_width=True):
            now = utc_now_iso()
            for c in db.get_collectors(tenant_id):
                c_upd = dict(c)
                c_upd.update({
                    "status": "ONLINE", "last_heartbeat": now,
                    "connectivity": "CONNECTED", "collection_status": "ACTIVE",
                })
                db.upsert_collector(c_upd)
            st.success("All collectors recovered to ONLINE.")
            st.rerun()

    collectors = evaluate_collectors(db, tenant_id)
    if not collectors:
        st.info("No collectors registered for this tenant.")
        return

    online = sum(1 for c in collectors if c["effective_status"] == "ONLINE")
    offline = sum(1 for c in collectors if c["effective_status"] == "OFFLINE")
    stale = sum(1 for c in collectors if c["effective_status"] in ("STALE", "DEGRADED"))

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Online Collectors", online, "Active & streaming", "#10B981")
    with c2: kpi_card("Degraded / Stale", stale, "Approaching threshold", "#F59E0B")
    with c3: kpi_card("Offline Collectors", offline, "Heartbeat > 60s", "#EF4444" if offline else "#64748B")

    df = pd.DataFrame(collectors)[[
        "collector_id", "source_id", "version", "effective_status",
        "seconds_since_heartbeat", "cpu_pct", "memory_pct",
        "config_status", "connectivity", "last_transmission"
    ]]
    df.columns = [
        "Collector ID", "Source", "Version", "Status", "Sec Since Heartbeat",
        "CPU %", "Mem %", "Config", "Connectivity", "Last Transmission (UTC)"
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)
