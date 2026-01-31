import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from auth import is_logged_in, logout


import os
import sys
import threading
import time
import requests
import uvicorn

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# --- UI STATUS INDICATOR ---
def show_status():
    with st.sidebar:
        st.divider()
        st.markdown("### 🟢 System Status")
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=1)
            if resp.status_code == 200:
                st.success(f"Backend: Online (v{resp.json().get('version', '0.1')})")
            else:
                st.error(f"Backend: Error {resp.status_code}")
        except Exception as e:
            st.error("Backend: Offline")
            st.caption(f"Reason: {str(e)[:50]}...")
            if st.button("Try Restart Backend"):
                ensure_backend()
                st.rerun()

show_status()


def call_predict(features: dict, consent: dict):
    resp = requests.post(
        f"{BACKEND_URL}/predict",
        json={"features": features, "consent": consent},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


from theme import apply_bank_theme


def main():
    if not is_logged_in():
        st.set_page_config(page_title="TRUS.AI Loan Decision", layout="wide")
        st.title("TRUS.AI Login Required")
        st.warning("Please login first.")
        st.page_link("pages/Login.py", label="Go to Login")
        st.stop()

    apply_bank_theme()

    # Logout button (top-right)
    col_header, col_logout = st.columns([6, 1])
    with col_header:
        st.markdown(
            """
        <div class="trus-header">
            <div class="trus-tag">Real-time model sandbox</div>
            <h1>TRUS.AI Credit Desk</h1>
            <p>Simulate ethical, explainable loan decisions with bank-grade transparency.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col_logout:
        if st.button("Logout"):
            logout()
            st.rerun()

    st.markdown(
        """
        
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.header("Navigation")
    st.sidebar.write("Use the pages in the sidebar: Consent, Dashboard, Chatbot.")

    st.markdown("### Loan Application Simulator")
    st.write("Configure an applicant profile similar to Indian retail banking journeys.")

    # Map Indian-friendly labels to underlying model categories
    checking_options = {
        "No current account": "no checking",
        "Current balance < ₹25,000": "<0",
        "₹25,000 – ₹1,00,000": "0<=X<200",
        "> ₹1,00,000": ">=200",
    }

    purpose_options = {
        "Home / renovation loan": "domestic appliance",
        "Education loan": "education",
        "Consumer durable loan (electronics, appliances)": "radio/TV",
        "New car loan": "new car",
        "Used car / two-wheeler loan": "used car",
        "Business / working capital loan": "business",
        "Furniture / office setup loan": "furniture/equipment",
        "Home repair / upgrade loan": "repairs",
        "Other personal loan": "other",
    }

    savings_options = {
        "No savings account": "no known savings",
        "Savings < ₹25,000": "<100",
        "₹25,000 – ₹1,25,000": "100<=X<500",
        "₹1,25,000 – ₹2,50,000": "500<=X<1000",
        "> ₹2,50,000": ">=1000",
    }

    employment_options = {
        "Currently not employed": "unemployed",
        "< 1 year in current job": "<1",
        "1 – 4 years in current job": "1<=X<4",
        "4 – 7 years in current job": "4<=X<7",
        "> 7 years in current job": ">=7",
    }

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

    # Map UI inputs to Indian model feature names expected by the pipeline
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

    # Default consent: all allowed
    consent = {k: True for k in features.keys()}

    placeholder = st.empty()
    btn_col1, btn_col2 = st.columns([1, 3])
    with btn_col1:
        run_clicked = st.button("Run Decision", type="primary")

    if run_clicked:
        with placeholder.container():
            st.markdown(
                """
                <div class="trus-card">
                    <b>Credit engine is working...</b>
                    <p>Streaming account, credit bureau, and consented attributes through the risk model.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.spinner("Our digital credit officer is reviewing your application..."):
            try:
                result = call_predict(features, consent)
            except Exception as e:
                placeholder.empty()
                st.error(f"Error calling backend: {e}")
                return

        # Store last decision context for use in chatbot page
        st.session_state["last_decision"] = result

        placeholder.empty()

        st.markdown("### Decision")
        decision = result.get("decision")
        proba = result.get("probability")
        st.metric("Decision", decision.capitalize(), f"p(approve)={proba:.2f}")

        st.markdown("### Explanation")
        st.write(result.get("explanation", {}).get("summary"))

        with st.expander("Show detailed SHAP contributions"):
            expl = result.get("explanation", {})
            top_neg = expl.get("top_negative", [])
            top_pos = expl.get("top_positive", [])
            if top_neg:
                st.markdown("**Top Negative Factors**")
                st.dataframe(pd.DataFrame(top_neg))
            if top_pos:
                st.markdown("**Top Positive Factors**")
                st.dataframe(pd.DataFrame(top_pos))

        st.markdown("### Remediation Suggestions")
        for step in result.get("remediation", []):
            st.write("- " + step)


if __name__ == "__main__":
    main()

