import requests
import streamlit as st

from auth import is_logged_in, logout
from components.charts import approval_pie_chart


BACKEND_URL = "http://localhost:8000"


def get_summary():
    resp = requests.get(f"{BACKEND_URL}/dashboard/summary", timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_legacy_fairness():
    """Fallback to the original dashboard fairness endpoint if needed."""

    resp = requests.get(f"{BACKEND_URL}/dashboard/fairness", timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_governance_model():
    resp = requests.get(f"{BACKEND_URL}/api/governance/model", timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_governance_fairness():
    resp = requests.get(f"{BACKEND_URL}/api/governance/fairness", timeout=60)
    resp.raise_for_status()
    return resp.json()


def toggle_model(active: bool):
    endpoint = "resume" if active else "pause"
    resp = requests.post(f"{BACKEND_URL}/model/{endpoint}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def apply_bank_theme():
    st.set_page_config(page_title="TRUS.AI – Dashboard", layout="wide")
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; background: #f3f4f6; }
        .trus-header {
            background: linear-gradient(90deg, #0d47a1, #1976d2);
            padding: 1.5rem 2rem;
            border-radius: 0 0 18px 18px;
            color: #f9fafb !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
        }
        .trus-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 1.5rem 1.75rem;
            box-shadow: 0 6px 20px rgba(15, 23, 42, 0.10);
            border: 1px solid rgba(148, 163, 184, 0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if not is_logged_in():
    apply_bank_theme()
    st.warning("Please login first.")
    st.page_link("pages/Login.py", label="Go to Login")
    st.stop()

apply_bank_theme()

col_header, col_logout = st.columns([6, 1])
with col_header:
    st.markdown(
        """
    <div class="trus-header">
        <h1>Responsible AI Governance</h1>
        <p>Monitor model status, fairness, and immutable audit signals in one place.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
with col_logout:
    if st.button("Logout"):
        logout()
        st.rerun()

# Model status + version panel
st.markdown("### Model Status & Version")
model_col, status_col = st.columns([2, 1])
with model_col:
    try:
        gm = get_governance_model()
    except Exception as e:
        st.error(f"Error loading model metadata: {e}")
        gm = {}

    meta = gm.get("model", {}) if isinstance(gm, dict) else {}
    active = gm.get("model_active", True)

    st.write(f"**Version:** {meta.get('version', 'unknown')}")
    st.write(f"**Dataset:** {meta.get('dataset', 'N/A')}")
    st.write(f"**Trained on:** {meta.get('trainingDate', 'N/A')}")
    metrics = meta.get("metrics", {})
    if metrics:
        st.write(
            "**Key metrics:** "
            + ", ".join(f"{k}={v}" for k, v in metrics.items())
        )

with status_col:
    state_label = "Active" if gm.get("model_active", True) else "Paused by compliance"
    st.metric("Model Status", state_label)

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Portfolio Overview")
    try:
        summary = get_summary()
    except Exception as e:
        st.error(f"Error loading summary: {e}")
        st.stop()

    approvals = summary.get("approvals", 0)
    denials = summary.get("denials", 0)
    total = summary.get("total", 0)

    approval_pie_chart(approvals, denials)

    st.write(f"Total decisions: **{total}**")
    st.write(f"Approvals: **{approvals}**, Denials: **{denials}**")

    st.markdown("### Fairness Metrics (Governance View)")
    try:
        gfair = get_governance_fairness()
        fairness = gfair.get("metrics", {})
    except Exception as e:
        st.error(f"Error loading governance fairness metrics: {e}")
    else:
        if not fairness.get("available", False):
            st.info(f"Fairness metrics not available: {fairness.get('reason')}")
        else:
            sf = fairness.get("sensitive_feature")
            st.write(f"Sensitive feature: **{sf}**")
            st.write(
                f"Overall selection rate (approval rate): **{fairness.get('overall_selection_rate', 0.0):.3f}**"
            )
            by_group = fairness.get("by_group", {})
            if by_group:
                st.write("Selection rate by group:")
                for group, value in by_group.items():
                    st.write(f"- {group}: {value:.3f}")

            # Bias alerts from governance layer
            if gfair.get("biasDetected"):
                st.error("Bias detected by governance thresholds.")
                for r in gfair.get("reasons", []):
                    st.write(
                        f"- {r.get('metric')}: value={r.get('value')}, threshold={r.get('threshold')}"
                    )

with col2:
    st.markdown("### Model Control")
    st.write("Pause or resume the model for regulatory interventions.")

    current_state = st.radio("Desired state", ["Active", "Paused"], index=0)
    if st.button("Apply State", type="primary"):
        target_active = current_state == "Active"
        try:
            result = toggle_model(target_active)
            st.success(f"Model active: {result.get('model_active')}")
        except Exception as e:
            st.error(f"Error toggling model state: {e}")

