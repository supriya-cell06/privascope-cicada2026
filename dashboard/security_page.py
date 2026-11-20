"""Page 4: Security Monitoring."""
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.styles import PLOTLY_DARK_LAYOUT, kpi_card
from monitoring.security import get_security_events, suggested_investigation_steps


def render_security(db, simulator, tenant_id: str):
    st.caption("Privacy-Preserving Security Observability — Raw credentials never leave Tier 1")

    if st.button("Simulate Repeated Failed Login Attack (DB-01)", type="primary"):
        simulator.trigger_security_event(tenant_id)
        st.success("Security attack simulated. Raw password remained local; sanitized metadata transmitted.")
        st.rerun()

    events = get_security_events(db, tenant_id)
    high_crit = sum(1 for e in events if e["severity"] in ("HIGH", "CRITICAL"))
    total_attempts = sum(int(e.get("failed_attempts") or 0) for e in events)

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Security Events", len(events), "Sanitized cloud events", "#EF4444")
    with c2: kpi_card("High / Critical Threats", high_crit, "Immediate triage", "#F97316")
    with c3: kpi_card("Failed Auth Attempts", total_attempts, "Aggregated safely", "#F59E0B")

    if not events:
        st.info("No security events recorded for this tenant yet. Click the button above or run Scenario 3.")
        return

    df = pd.DataFrame(events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    fig = px.bar(df, x="timestamp", y="failed_attempts", color="severity", hover_data=["source_id", "event_type"], title="Failed Authentication Attempts Over Time")
    fig.update_layout(**PLOTLY_DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sanitized Security Event Feed (Zero Passwords / Zero PII)")
    st.dataframe(
        df[["timestamp", "event_id", "source_id", "event_type", "severity", "failed_attempts", "sanitized_summary"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Suggested Investigation Steps")
    latest_type = events[0].get("event_type", "repeated_authentication_failure")
    for idx, step in enumerate(suggested_investigation_steps(latest_type), start=1):
        st.markdown(f"{idx}. {step}")
