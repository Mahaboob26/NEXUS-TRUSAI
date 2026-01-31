import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from auth import is_logged_in, logout


BACKEND_URL = "http://localhost:8000"


# Allow direct import of the consent engine so we can read profile and access logs
# File layout:
#   TRUS_AI/
#     indian_model_training/
#     trus-ai-mvp/
#       frontend/pages/Consent.py (this file)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from indian_model_training.consent_engine import (  # type: ignore E402
    save_user_profile,
    get_access_log,
)


def call_predict(features: dict, consent: dict):
    resp = requests.post(
        f"{BACKEND_URL}/predict",
        json={"features": features, "consent": consent},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_profile_from_backend() -> dict:
    """Fetch 'what the AI knows about you' from the backend API.

    Uses the new /consent/knowledge endpoint instead of importing the
    profile directly in the frontend. Falls back to an empty dict on
    error so the UI can handle gracefully.
    """

    try:
        resp = requests.get(f"{BACKEND_URL}/consent/knowledge", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("profile", {})
    except Exception:
        return {}


def fetch_consent_state():
    resp = requests.get(f"{BACKEND_URL}/consent/state", timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_consent_state(consent: dict):
    resp = requests.post(
        f"{BACKEND_URL}/consent/state",
        json=consent,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def reset_consent_state():
    resp = requests.post(f"{BACKEND_URL}/consent/reset", timeout=30)
    resp.raise_for_status()
    return resp.json()


from theme import apply_bank_theme


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
        <div class="trus-tag">Consent sandbox</div>
        <h1>Dynamic Consent Simulator</h1>
        <p>See how restricting data usage changes automated credit decisions.</p>
    </div>
    """,
    unsafe_allow_html=True,
    )
with col_logout:
    if st.button("Logout"):
        logout()
        st.rerun()

st.write(
    """Toggle which *groups* of data the AI is allowed to use. We will recompute the decision
    and show how much the approval probability changes."""
)

# Surface last accessed time from the existing access log for transparency
recent_access = get_access_log(limit=1)
if recent_access:
    last_ts = recent_access[0].get("timestamp")
    if last_ts:
        try:
            # Convert stored UTC timestamps to local IST for display
            ts_local = (
                pd.to_datetime(last_ts, utc=True)
                .tz_convert("Asia/Kolkata")
                .strftime("%Y-%m-%d %H:%M:%S %Z")
            )
            st.caption(f"Last AI access to your data: {ts_local}")
        except Exception:
            st.caption(f"Last AI access to your data: {last_ts}")
else:
    st.caption("Last AI access to your data: not yet accessed in this session")

st.markdown('<div class="trus-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    applicant_income = st.number_input(
        "Applicant monthly income (₹)",
        min_value=5000,
        max_value=300000,
        value=60000,
        step=5000,
    )
    coapplicant_income = st.number_input(
        "Co-applicant monthly income (₹)",
        min_value=0,
        max_value=300000,
        value=10000,
        step=5000,
    )
    loan_amount = st.number_input(
        "Requested loan amount (₹)",
        min_value=50000,
        max_value=3000000,
        value=800000,
        step=50000,
    )
    loan_term = st.number_input(
        "Loan tenure (months)", min_value=6, max_value=360, value=180, step=6
    )
with col2:
    credit_history_label = st.selectbox(
        "Credit history", ["Good (no major defaults)", "Weak / past defaults"]
    )
    credit_history = 1 if "Good" in credit_history_label else 0
    gender = st.selectbox("Applicant gender", ["Male", "Female"])
    married = st.selectbox("Marital status", ["Yes", "No"])
    dependents = st.selectbox("Number of dependents", ["0", "1", "2", "3+"])
    education = st.selectbox("Education", ["Graduate", "Not Graduate"])
with col3:
    self_employed = st.selectbox("Self employed", ["No", "Yes"])
    property_area = st.selectbox("Property area", ["Urban", "Semiurban", "Rural"])
    mobile_usage_score = st.slider(
        "Mobile usage / digital footprint score", 300, 950, 700
    )
    transaction_stability_score = st.slider(
        "Transaction stability score", 300, 950, 750
    )
    bank_balance = st.number_input(
        "Average bank balance (₹)",
        min_value=0,
        max_value=1000000,
        value=150000,
        step=10000,
    )

st.markdown('</div>', unsafe_allow_html=True)

features = {
    "ApplicantIncome": applicant_income,
    "CoapplicantIncome": coapplicant_income,
    "LoanAmount": loan_amount,
    "Loan_Amount_Term": loan_term,
    "Credit_History": credit_history,
    "Gender": gender,
    "Married": married,
    "Dependents": dependents,
    "Education": education,
    "Self_Employed": self_employed,
    "Property_Area": property_area,
    "mobile_usage_score": mobile_usage_score,
    "transaction_stability_score": transaction_stability_score,
    "bank_balance": bank_balance,
}

st.subheader("Consent Controls")

try:
    state_payload = fetch_consent_state()
    feature_groups = state_payload.get("groups", {})
    current_consent = state_payload.get("consent", {})
except Exception as e:
    st.error(f"Error loading consent state: {e}")
    feature_groups = {}
    current_consent = {}

st.markdown("**Data groups and toggles**")

updated_consent: dict[str, bool] = {}
for group_name, cols in feature_groups.items():
    default_val = bool(current_consent.get(group_name, True))
    checkbox = st.checkbox(
        f"Allow {group_name} data",
        value=default_val,
    )
    updated_consent[group_name] = checkbox
    with st.expander(f"Features in '{group_name}' group"):
        st.write(", ".join(cols))

# Show immediate feedback when groups are enabled/disabled compared to
# the last saved consent state from the backend.
enabled_now = [
    name
    for name, val in updated_consent.items()
    if val and not current_consent.get(name, True)
]
disabled_now = [
    name
    for name, val in updated_consent.items()
    if (not val) and current_consent.get(name, True)
]
if enabled_now:
    msg = "Consent enabled for: " + ", ".join(enabled_now)
    st.success(msg)
    try:
        st.toast(msg)
    except Exception:
        pass
if disabled_now:
    msg = "Consent disabled for: " + ", ".join(disabled_now)
    st.warning(msg)
    try:
        st.toast(msg)
    except Exception:
        pass

col_save, col_reset = st.columns(2)
with col_save:
    if st.button("Save consent settings"):
        try:
            save_consent_state(updated_consent)
            st.success("Consent settings saved. New predictions will honour these groups by default.")
        except Exception as e:
            st.error(f"Error saving consent state: {e}")

with col_reset:
    if st.button("Reset to all allowed"):
        try:
            reset_consent_state()
            st.success("Consent reset to default (all groups allowed).")
        except Exception as e:
            st.error(f"Error resetting consent state: {e}")

if st.button("Evaluate with and without consent changes", type="primary"):
    try:
        # Baseline: all consent groups allowed
        baseline_consent = {name: True for name in feature_groups.keys()}
        baseline = call_predict(features, baseline_consent)
        modified = call_predict(features, updated_consent)
    except Exception as e:
        st.error(f"Error calling backend: {e}")
        st.stop()

    # Store baseline decision as last_decision context
    st.session_state["last_decision"] = baseline

    # If consent is insufficient in either scenario, surface the message
    if "probability" not in baseline or baseline.get("decision") == "insufficient_consent":
        st.warning(baseline.get("message", "Consent is insufficient to run the model for the baseline scenario."))
        st.stop()

    if "probability" not in modified or modified.get("decision") == "insufficient_consent":
        st.warning(modified.get("message", "Consent is insufficient to run the model with the current settings."))
        st.stop()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### Baseline (all fields allowed)")
        st.metric(
            "Decision",
            baseline["decision"].capitalize(),
            f"p(approve)={baseline['probability']:.2f}",
        )
    with col_b:
        st.markdown("### With Consent Settings Applied")
        st.metric(
            "Decision",
            modified["decision"].capitalize(),
            f"p(approve)={modified['probability']:.2f}",
        )

    delta = modified["probability"] - baseline["probability"]
    st.markdown("### Decision Delta")
    st.write(f"Change in approval probability: {delta:+.3f}")


st.markdown("---")
st.subheader("What the AI knows about you")

profile = fetch_profile_from_backend()

with st.form("profile_form"):
    edited_profile: dict[str, object] = {}
    col_p1, col_p2 = st.columns(2)
    items = list(profile.items())
    half = (len(items) + 1) // 2
    with col_p1:
        for key, value in items[:half]:
            if isinstance(value, (int, float)):
                edited_profile[key] = st.number_input(key, value=float(value))
            else:
                edited_profile[key] = st.text_input(key, value=str(value))
    with col_p2:
        for key, value in items[half:]:
            if isinstance(value, (int, float)):
                edited_profile[key] = st.number_input(key, value=float(value))
            else:
                edited_profile[key] = st.text_input(key, value=str(value))

    if st.form_submit_button("Update Profile"):
        save_user_profile(edited_profile)
        st.success("Profile updated. Future explanations and consent previews will use this view of your data.")


st.markdown("---")
st.subheader("AI data access log")

if st.button("Refresh access log"):
    access_entries = get_access_log(limit=50)
else:
    access_entries = get_access_log(limit=20)

if not access_entries:
    st.info("No feature access has been logged yet. Run a decision first.")
else:
    log_rows = []
    for e in access_entries:
        log_rows.append(
            {
                "time": e.get("timestamp"),
                "feature": e.get("feature"),
                "allowed": e.get("allowed"),
                "model_version": e.get("model_version"),
            }
        )
    df_log = pd.DataFrame(log_rows)
    # Format time nicely in local IST; keep latest entries first (backend
    # already returns most recent first).
    if not df_log.empty and "time" in df_log.columns:
        try:
            df_log["time"] = (
                pd.to_datetime(df_log["time"], utc=True)
                .dt.tz_convert("Asia/Kolkata")
                .dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            )
        except Exception:
            pass
    st.table(df_log)

