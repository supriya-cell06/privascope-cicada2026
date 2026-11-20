"""Page 10: Autonomous Operations (Human-in-the-Loop Safe Simulation + RBAC)."""
import pandas as pd
import streamlit as st

from autonomous_ops.actions import propose_action
from autonomous_ops.approval import approve_action, reject_action, rollback_action, simulate_execute_action
from utils.auth import has_permission


def render_autonomous_ops(db, tenant_id: str):
    st.caption("Human-Approved Simulated Remediation with Role-Based Access Control (RBAC)")

    user = st.session_state.get("auth_user")
    can_approve = has_permission(user, "approve_ops")
    if not can_approve:
        st.warning(
            f"RBAC Restricted Mode: Logged in as **{user['role']}**. "
            "Only **SOC_ADMIN** can approve, execute, or rollback autonomous remediation actions."
        )

    st.markdown(
        """
        <div class="pipeline-box">OBSERVE &nbsp;➜&nbsp; DETECT &nbsp;➜&nbsp; CORRELATE &nbsp;➜&nbsp; RECOMMEND &nbsp;➜&nbsp; ACT (RBAC HUMAN-APPROVED SIMULATION)</div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Propose Sample Safe Remediation Action", disabled=not can_approve):
        devices = db.get_devices(tenant_id)
        src = devices[0]["source_id"] if devices else "APP-01"
        propose_action(
            db, tenant_id, src,
            proposed_action=f"Simulate graceful service restart on {src}",
            reason="Proactive remediation drill for elevated response latency.",
            evidence="Latency spike > 200ms observed in simulated telemetry.",
            expected_outcome="Service worker pool resets cleanly with zero downtime.",
            risk_level="LOW",
        )
        st.rerun()

    actions = db.get_autonomous_actions(tenant_id)
    if not actions:
        st.info("No pending remediation actions. Trigger Scenario 2, 3, or 7 to generate AI-recommended actions.")
        return

    approver_name = user["full_name"] if user else "SOC-Lead"
    for act in actions:
        with st.expander(f"{act['action_id']} | {act['proposed_action']} — [{act['approval_status']} / {act['execution_status']}]", expanded=True):
            st.markdown(f"**Target Source:** `{act['source_id']}` | **Risk:** `{act['risk_level']}` | **Reversibility:** `{act['reversibility']}`")
            st.markdown(f"**Reason:** {act['reason']}")
            st.markdown(f"**Evidence:** `{act['evidence']}`")
            st.markdown(f"**Expected Outcome:** {act['expected_outcome']}")

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("APPROVE ACTION", key=f"app_{act['action_id']}", disabled=not can_approve, use_container_width=True):
                    approve_action(db, act["action_id"], tenant_id, approver=approver_name)
                    st.rerun()
            with b2:
                if st.button("REJECT ACTION", key=f"rej_{act['action_id']}", disabled=not can_approve, use_container_width=True):
                    reject_action(db, act["action_id"], tenant_id, approver=approver_name)
                    st.rerun()
            with b3:
                if st.button("SIMULATE EXECUTION", key=f"exe_{act['action_id']}", disabled=(not can_approve or act["approval_status"] != "APPROVED"), use_container_width=True):
                    simulate_execute_action(db, act["action_id"], tenant_id)
                    st.rerun()
            with b4:
                if st.button("ROLLBACK", key=f"rb_{act['action_id']}", disabled=(not can_approve or act["execution_status"] != "SIMULATED_SUCCESS"), use_container_width=True):
                    rollback_action(db, act["action_id"], tenant_id)
                    st.rerun()

    st.divider()
    st.subheader("Autonomous Operations Audit Log")
    st.dataframe(
        pd.DataFrame(actions)[[
            "action_id", "source_id", "proposed_action", "approval_status",
            "execution_status", "approved_by", "updated_at"
        ]],
        use_container_width=True,
        hide_index=True,
    )
