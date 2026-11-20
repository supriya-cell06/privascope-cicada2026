"""Page 3: Network Monitoring."""
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.styles import PLOTLY_DARK_LAYOUT, kpi_card
from monitoring.network import get_network_summary


def render_network(db, simulator, tenant_id: str):
    st.caption("Bandwidth, Inbound/Outbound Traffic, Latency, Packet Loss & Outage Simulation")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Simulate High Latency & Packet Loss", use_container_width=True):
            simulator.trigger_network_issue(tenant_id, outage=False)
            st.rerun()
    with b2:
        if st.button("Simulate Network Outage", use_container_width=True):
            simulator.trigger_network_issue(tenant_id, outage=True)
            st.rerun()
    with b3:
        if st.button("Restore Normal Network", use_container_width=True):
            simulator.seed_baseline()
            st.rerun()

    summary = get_network_summary(db, tenant_id)
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Avg Latency", f"{summary['avg_latency_ms']} ms", "Across all nodes", "#38BDF8")
    with k2: kpi_card("Avg Packet Loss", f"{summary['avg_packet_loss_pct']}%", "Target < 1.0%", "#F59E0B" if summary["avg_packet_loss_pct"] > 1 else "#10B981")
    with k3: kpi_card("Total Bandwidth", f"{summary['total_bandwidth_mbps']} Mbps", "Combined throughput", "#A855F7")
    with k4: kpi_card("Degraded Links", summary["degraded_links"], "Interfaces above threshold", "#EF4444" if summary["degraded_links"] else "#10B981")

    st.info(f"**Operational Impact Assessment:** {summary['impact_summary']}")

    telemetry = db.get_telemetry(tenant_id, limit=200)
    if telemetry:
        df = pd.DataFrame(telemetry)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        c1, c2 = st.columns(2)
        with c1:
            fig_lat = px.line(df, x="timestamp", y="latency_ms", color="source_id", title="Network Latency (ms)")
            fig_lat.update_layout(**PLOTLY_DARK_LAYOUT)
            st.plotly_chart(fig_lat, use_container_width=True)
        with c2:
            fig_loss = px.line(df, x="timestamp", y="packet_loss_pct", color="source_id", title="Packet Loss (%)")
            fig_loss.update_layout(**PLOTLY_DARK_LAYOUT)
            st.plotly_chart(fig_loss, use_container_width=True)

        fig_bw = px.bar(df.tail(30), x="source_id", y=["inbound_mbps", "outbound_mbps"], barmode="group", title="Inbound vs Outbound Traffic (Mbps)")
        fig_bw.update_layout(**PLOTLY_DARK_LAYOUT)
        st.plotly_chart(fig_bw, use_container_width=True)
