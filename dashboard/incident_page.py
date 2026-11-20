"""Page 6: Incident Correlation & Alert Management."""
import pandas as pd
import streamlit as st

from aiops.correlation import CorrelationEngine


def render_incidents(db, tenant_id: str):
    st.caption("Groups related alerts across infrastructure, network, and security into explainable incidents")

    if st.button("Run Correlation Engine", type="primary"):
        eng = CorrelationEngine(db)
        incs = eng.correlate_alerts(tenant_id)
        st.success(f"Correlated {len(incs)} active incident(s).")
        st.rerun()

    st.subheader("Correlated Incidents")
    incidents = db.get_incidents(tenant_id)
    if not incidents:
        st.info("No correlated incidents yet. Run Scenario 2, 3, 4, or 6 from the sidebar.")
    else:
        for inc in incidents:
            with st.expander(f"[{inc['severity']}] {inc['incident_id']} — {inc['title']} (Confidence: {inc['confidence_pct']:.0f}%)", expanded=True):
                st.markdown(f"**Root Cause Hypothesis:** {inc['root_cause_hypothesis']}")
                st.markdown(f"**Impact:** {inc['impact']}")
                st.markdown(f"**Confidence Explanation:** {inc['confidence_explanation']}")
                st.markdown("**Supporting Evidence:**")
                for ev in inc["evidence"]:
                    st.markdown(f"- {ev}")
                rec = inc.get("recommendations") or {}
                if rec:
                    st.markdown("**Explainable Recommendation:**")
                    st.markdown(f"- *What was detected:* {rec.get('what_detected', '')}")
                    st.markdown(f"- *Why it matters:* {rec.get('why_it_matters', '')}")
                    st.markdown(f"- *Action Risk:* {rec.get('action_risk', '')}")
                    for step in rec.get("suggested_next_steps", []):
                        st.markdown(f"  - {step}")

    st.divider()
    st.subheader("Alert Management Queue (Deduplicated & Prioritized)")
    alerts = db.get_alerts(tenant_id)
    if not alerts:
        st.info("No alerts for this tenant.")
        return

    c1, c2 = st.columns(2)
    with c1:
        sev_filter = st.selectbox("Filter Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"])
    with c2:
        status_filter = st.selectbox("Filter Status", ["All", "OPEN", "ACKNOWLEDGED", "RESOLVED"])

    filtered = [
        a for a in alerts
        if (sev_filter == "All" or a["severity"] == sev_filter)
        and (status_filter == "All" or a["status"] == status_filter)
    ]
    if filtered:
        df = pd.DataFrame(filtered)[[
            "alert_id", "severity", "status", "source_id", "category",
            "title", "occurrence_count", "assigned_to", "updated_at"
        ]]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("**Alert Actions**")
        sel_alert = st.selectbox("Select Alert ID", [a["alert_id"] for a in filtered])
        assignee = st.text_input("Assign To", "SRE-OnCall")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Acknowledge Alert", use_container_width=True):
                db.update_alert_status(sel_alert, tenant_id, "ACKNOWLEDGED", assignee)
                st.rerun()
        with b2:
            if st.button("Resolve Alert", use_container_width=True):
                db.update_alert_status(sel_alert, tenant_id, "RESOLVED", assignee)
                st.rerun()
        with b3:
            if st.button("Reopen Alert", use_container_width=True):
                db.update_alert_status(sel_alert, tenant_id, "OPEN", assignee)
                st.rerun()
