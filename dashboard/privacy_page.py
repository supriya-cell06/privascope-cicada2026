"""Page 8: Egress Proof, Cryptographic Hash-Chain & Differential Privacy Audit."""
import pandas as pd
import streamlit as st

from collector.crypto_privacy import verify_audit_chain, verify_payload_signature
from utils.helpers import safe_json_dumps


def render_privacy_audit(db, tenant_id: str):
    st.caption(
        "Tamper-Evident SHA-256 Hash-Chained Ledger + HMAC-SHA256 Signed Tier 1 → Tier 2 Payloads + Differential Privacy"
    )

    # Differential Privacy Toggle & Cryptographic Chain Verification
    c_dp, c_ver = st.columns(2)
    with c_dp:
        dp_now = db.get_state("differential_privacy", "false").lower() == "true"
        dp_toggle = st.toggle(
            "Enable ε-Differential Privacy (Laplace Noise on Telemetry Metrics)",
            value=dp_now,
            help="Injects calibrated Laplace noise (ε=1.0) locally before metrics leave Tier 1 to prevent statistical inference.",
        )
        if dp_toggle != dp_now:
            db.set_state("differential_privacy", "true" if dp_toggle else "false")
            st.toast(f"Differential Privacy {'ENABLED' if dp_toggle else 'DISABLED'}")
            st.rerun()

    with c_ver:
        if st.button("Verify Cryptographic Hash-Chain Integrity", type="primary", use_container_width=True):
            chron = db.get_privacy_audits_chronological(tenant_id)
            ok, msg = verify_audit_chain(chron)
            if ok:
                st.success(f"VERIFIED: {msg}")
            else:
                st.error(f"INTEGRITY FAILURE: {msg}")

    audits = db.get_privacy_audits(tenant_id, limit=100)
    if not audits:
        st.info("No egress transmissions recorded yet.")
        return

    df = pd.DataFrame([
        {
            "Audit ID": a["audit_id"],
            "Timestamp (UTC)": a["timestamp"],
            "Source ID": a["source_id"],
            "Size (B)": a["payload_size_bytes"],
            "Allowed": len(a["allowed_fields"]),
            "Rejected": len(a["rejected_fields"]),
            "HMAC-SHA256": (a.get("payload_hmac") or "")[:14] + "...",
            "Chain Hash": (a.get("chain_hash") or "")[:14] + "...",
            "Policy": a["policy_status"],
            "Status": a["transmission_status"],
        }
        for a in audits
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Outbound Payload & Cryptographic Signature Inspector")
    selected_audit_id = st.selectbox("Inspect Audit Record", [a["audit_id"] for a in audits])
    rec = next(a for a in audits if a["audit_id"] == selected_audit_id)

    sig_valid = verify_payload_signature(rec["sanitized_payload"], rec.get("payload_hmac", ""))
    if sig_valid:
        st.success(f"HMAC-SHA256 Transport Signature VALID: `{rec.get('payload_hmac', '')}`")
    else:
        st.warning("Legacy record or unsigned payload.")
    st.caption(f"SHA-256 Chain Link: `{rec.get('chain_hash', 'N/A')}` (Prev: `{(rec.get('prev_hash') or '')[:16]}...`)")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Original Raw Telemetry (Local Only)**")
        st.json(rec["raw_telemetry"])
        st.error(f"Rejected Fields ({len(rec['rejected_fields'])}): {', '.join(rec['rejected_fields']) or 'None'}")
        if rec["redacted_fields"]:
            st.warning(f"Redacted String Fields: {', '.join(rec['redacted_fields'])}")
    with c2:
        st.markdown("**Actual Sanitized Outbound Payload (Sent to SaaS)**")
        st.json(rec["sanitized_payload"])
        st.success(f"Allow-Listed Fields ({len(rec['allowed_fields'])}): {', '.join(rec['allowed_fields'])}")

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Download Sanitized Payload (JSON)",
            data=safe_json_dumps(rec["sanitized_payload"]),
            file_name=f"{rec['audit_id']}_sanitized_payload.json",
            mime="application/json",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Download Full Privacy Audit Log (JSON)",
            data=safe_json_dumps(audits),
            file_name=f"privascope_privacy_audit_{tenant_id.replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
