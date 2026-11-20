"""Page 5: AIOps Intelligence — Explainable Anomaly Detection."""
import pandas as pd
import plotly.express as px
import streamlit as st

from aiops.anomaly_detection import AnomalyDetector, SKLEARN_AVAILABLE
from dashboard.styles import PLOTLY_DARK_LAYOUT


def render_aiops(db, tenant_id: str):
    st.caption(
        f"Explainable Anomaly Detection | Engine: **{'Scikit-learn IsolationForest + Statistical Z-Score' if SKLEARN_AVAILABLE else 'Statistical Baseline Fallback'}**"
    )

    if st.button("Run Anomaly Detection Scan", type="primary"):
        detector = AnomalyDetector(db)
        found = detector.detect_for_tenant(tenant_id)
        st.success(f"Scan complete: {len(found)} anomaly signal(s) detected.")
        st.rerun()

    anomalies = db.get_anomalies(tenant_id)
    if not anomalies:
        st.info("No anomalies detected yet. Trigger Scenario 2 (CPU Anomaly) or Scenario 4 (Network Failure) to see explainable ML detections.")
        return

    df = pd.DataFrame(anomalies)
    fig = px.scatter(
        df, x="timestamp", y="anomaly_score", color="severity", size="anomaly_score",
        hover_data=["source_id", "metric", "current_value", "expected_baseline"],
        title="Detected Anomalies by Score & Severity",
    )
    fig.update_layout(**PLOTLY_DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Explainable Anomaly Log")
    for a in anomalies[:15]:
        with st.expander(f"[{a['severity']}] {a['source_id']} — {a['metric']} (Score: {a['anomaly_score']})"):
            st.markdown(f"**Explanation:** {a['explanation']}")
            st.markdown(f"**Current Value:** `{a['current_value']}` | **Expected Baseline:** `{a['expected_baseline']}`")
            st.markdown(f"**Detection Method:** `{a['method']}` | **Timestamp (UTC):** `{a['timestamp']}`")
