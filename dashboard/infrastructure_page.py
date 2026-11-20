"""Page 2: Infrastructure Monitoring."""
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.styles import PLOTLY_DARK_LAYOUT
from monitoring.infrastructure import evaluate_devices


def render_infrastructure(db, tenant_id: str):
    st.caption("Servers, VMs, Containers, Applications, Databases & Cloud Resources")

    devices = evaluate_devices(db, tenant_id)
    if not devices:
        st.warning("No devices found for this tenant.")
        return

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        search = st.text_input("Search device / Source ID", "")
    with f2:
        regions = ["All"] + sorted({d["region"] for d in devices})
        sel_region = st.selectbox("Region", regions)
    with f3:
        healths = ["All", "EXCELLENT", "GOOD", "FAIR", "POOR"]
        sel_health = st.selectbox("Health Status", healths)
    with f4:
        sort_by = st.selectbox("Sort By", ["cpu_pct", "memory_pct", "latency_ms", "source_id"])

    filtered = [
        d for d in devices
        if (search.lower() in d["device_name"].lower() or search.lower() in d["source_id"].lower())
        and (sel_region == "All" or d["region"] == sel_region)
        and (sel_health == "All" or d["health_status"] == sel_health)
    ]
    filtered = sorted(filtered, key=lambda x: x[sort_by], reverse=(sort_by != "source_id"))

    st.dataframe(
        pd.DataFrame(filtered)[[
            "source_id", "device_name", "device_type", "environment", "region",
            "cpu_pct", "memory_pct", "disk_pct", "response_time_ms", "health_display"
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("Source-Specific Deep Dive")
    selected_id = st.selectbox("Select Device", [d["source_id"] for d in devices])
    dev = next(d for d in devices if d["source_id"] == selected_id)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("CPU", f"{dev['cpu_pct']:.1f}%")
    m2.metric("Memory", f"{dev['memory_pct']:.1f}%")
    m3.metric("Disk", f"{dev['disk_pct']:.1f}%")
    m4.metric("Response Time", f"{dev['response_time_ms']:.0f} ms")
    m5.metric("Health", dev["health_display"])

    telemetry = db.get_telemetry(tenant_id, source_id=selected_id, limit=60)
    if telemetry:
        tdf = pd.DataFrame(telemetry)
        tdf["timestamp"] = pd.to_datetime(tdf["timestamp"])
        tdf = tdf.sort_values("timestamp")
        fig = px.line(
            tdf, x="timestamp", y=["cpu_pct", "memory_pct", "disk_pct"],
            title=f"Resource Utilization Trend — {selected_id} ({dev['region']})",
        )
        fig.update_layout(**PLOTLY_DARK_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
