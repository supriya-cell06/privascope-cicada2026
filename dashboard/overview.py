"""Page 1: Executive Overview Dashboard."""
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.styles import PLOTLY_DARK_LAYOUT, kpi_card
from monitoring.collector_health import evaluate_collectors
from monitoring.infrastructure import evaluate_devices


def render_overview(db, tenant_id: str):
    st.caption(f"Tenant: **{tenant_id}** | Real-time Privacy-First Observability & AIOps Command Center")

    devices = evaluate_devices(db, tenant_id)
    collectors = evaluate_collectors(db, tenant_id)
    alerts = [a for a in db.get_alerts(tenant_id) if a["status"] != "RESOLVED"]
    incidents = db.get_incidents(tenant_id)
    anomalies = db.get_anomalies(tenant_id)
    telemetry = db.get_telemetry(tenant_id, limit=250)
    sec_events = [t for t in telemetry if t["event_category"] == "security"]

    healthy = sum(1 for d in devices if d["health_status"] in ("EXCELLENT", "GOOD"))
    warning = sum(1 for d in devices if d["health_status"] == "FAIR")
    critical = sum(1 for d in devices if d["health_status"] == "POOR")
    col_online = sum(1 for c in collectors if c["effective_status"] == "ONLINE")
    col_offline = len(collectors) - col_online

    # Row 1 KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Monitored Sources", len(devices), "Active inventory", "#38BDF8")
    with c2: kpi_card("Healthy Sources", healthy, "EXCELLENT / GOOD", "#10B981")
    with c3: kpi_card("Warning Sources", warning, "FAIR state", "#F59E0B")
    with c4: kpi_card("Critical Sources", critical, "POOR / STALE", "#EF4444")
    with c5: kpi_card("Active Incidents", len(incidents), f"{len(alerts)} open alerts", "#F97316")

    # Row 2 KPIs
    c6, c7, c8, c9 = st.columns(4)
    with c6: kpi_card("Anomalies Detected", len(anomalies), "ML + Statistical", "#A855F7")
    with c7: kpi_card("Security Events", len(sec_events), "Sanitized metadata", "#EF4444")
    with c8: kpi_card("Collectors Online", col_online, "Heartbeat healthy", "#10B981")
    with c9: kpi_card("Collectors Offline/Degraded", col_offline, "60s detection target", "#EF4444" if col_offline else "#64748B")

    st.divider()

    # Charts organized into clean tabs for zero clutter
    if telemetry:
        df = pd.DataFrame(telemetry)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        infra_df = df[df["cpu_pct"].notna()]

        col_a, col_b = st.columns(2)
        with col_a:
            if not infra_df.empty:
                fig_cpu = px.line(infra_df, x="timestamp", y="cpu_pct", color="source_id", title="CPU Usage Over Time (%)")
                fig_cpu.update_layout(**PLOTLY_DARK_LAYOUT)
                st.plotly_chart(fig_cpu, use_container_width=True)
        with col_b:
            if not infra_df.empty:
                fig_mem = px.line(infra_df, x="timestamp", y="memory_pct", color="source_id", title="Memory Usage Over Time (%)")
                fig_mem.update_layout(**PLOTLY_DARK_LAYOUT)
                st.plotly_chart(fig_mem, use_container_width=True)

        col_c, col_d = st.columns(2)
        with col_c:
            if not infra_df.empty:
                fig_net = px.area(infra_df, x="timestamp", y="network_mbps", color="source_id", title="Network Traffic (Mbps)")
                fig_net.update_layout(**PLOTLY_DARK_LAYOUT)
                st.plotly_chart(fig_net, use_container_width=True)
        with col_d:
            if not infra_df.empty:
                fig_lat = px.line(infra_df, x="timestamp", y="latency_ms", color="source_id", title="Latency Over Time (ms)")
                fig_lat.update_layout(**PLOTLY_DARK_LAYOUT)
                st.plotly_chart(fig_lat, use_container_width=True)

        col_e, col_f = st.columns(2)
        with col_e:
            health_counts = pd.DataFrame([{"Health": d["health_status"]} for d in devices])
            fig_h = px.pie(
                health_counts, names="Health", title="Infrastructure Health Distribution",
                color="Health",
                color_discrete_map={"EXCELLENT": "#10B981", "GOOD": "#3B82F6", "FAIR": "#F59E0B", "POOR": "#EF4444"},
                hole=0.45,
            )
            fig_h.update_layout(**PLOTLY_DARK_LAYOUT)
            st.plotly_chart(fig_h, use_container_width=True)
        with col_f:
            if anomalies:
                adf = pd.DataFrame(anomalies)
                adf["timestamp"] = pd.to_datetime(adf["timestamp"])
                fig_an = px.scatter(adf, x="timestamp", y="anomaly_score", color="severity", hover_data=["source_id", "metric"], title="Anomaly Score Trend")
                fig_an.update_layout(**PLOTLY_DARK_LAYOUT)
                st.plotly_chart(fig_an, use_container_width=True)
            else:
                st.info("No anomalies detected in the current baseline. Trigger a scenario from the sidebar to see anomaly trends.")

    st.subheader("Infrastructure Health Matrix")
    if devices:
        dev_df = pd.DataFrame(devices)[[
            "device_name", "source_id", "environment", "region",
            "cpu_pct", "memory_pct", "disk_pct", "network_mbps",
            "latency_ms", "packet_loss_pct", "connectivity_status",
            "last_seen", "health_display",
        ]]
        dev_df.columns = [
            "Device", "Source ID", "Env", "Region", "CPU %", "Mem %", "Disk %",
            "Net Mbps", "Latency ms", "Loss %", "Connectivity", "Last Seen (UTC)", "Health",
        ]
        st.dataframe(dev_df, use_container_width=True, hide_index=True)
