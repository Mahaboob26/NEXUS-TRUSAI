from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

import pickle

from .consent_engine import apply_consent
from .remediation import remediation_suggestions
from .shap_explainer import (
    load_model_and_explainer,
    compute_shap_for_row,
    shap_to_reasons,
)


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"


def _ensure_engineered_features(row: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(row)

    applicant_income = float(data.get("ApplicantIncome", 0) or 0)
    co_income = float(data.get("CoapplicantIncome", 0) or 0)
    loan_amount = float(data.get("LoanAmount", 0) or 0)
    term = float(data.get("Loan_Amount_Term", 0) or 1)
    bank_balance = float(data.get("bank_balance", 0) or 0)
    credit_history = float(data.get("Credit_History", 0) or 0)
    mobile_score = float(data.get("mobile_usage_score", 0) or 0)
    txn_score = float(data.get("transaction_stability_score", 0) or 0)

    total_income = applicant_income + co_income
    emi = loan_amount / term if term else 0
    income_to_emi_ratio = total_income / (emi + 1) if total_income else 0
    credit_utilization = loan_amount / (bank_balance + 50000)
    stability_score = (
        0.4 * (txn_score / 950) + 0.3 * (mobile_score / 950) + 0.3 * credit_history
    )
    cibil_proxy_score = (
        0.35 * txn_score
        + 0.25 * mobile_score
        + 0.2 * (total_income * 1.0)
        + 0.2 * (credit_history * 900)
    ) / 2

    data.setdefault("total_income", total_income)
    data.setdefault("emi", emi)
    data.setdefault("income_to_emi_ratio", income_to_emi_ratio)
    data.setdefault("credit_utilization", credit_utilization)
    data.setdefault("stability_score", stability_score)
    data.setdefault("cibil_proxy_score", cibil_proxy_score)

    return data


def predict_with_explanation(input_json: Dict[str, Any], consent_flags: Dict[str, bool]):
    model, explainer, feature_names = load_model_and_explainer()

    # Ensure feature engineering
    base_features = _ensure_engineered_features(input_json)

    # Apply consent at group level
    features_after_consent = apply_consent(base_features, consent_flags)

    # Build dataframe in model feature order
    X = pd.DataFrame([features_after_consent], columns=feature_names)

    proba = float(model.predict_proba(X)[0, 1])
    label = "approved" if proba >= 0.5 else "denied"

    shap_vals = compute_shap_for_row(explainer, feature_names, X)
    shap_info = shap_to_reasons(shap_vals, feature_names, features_after_consent, label)

    remediation = remediation_suggestions(features_after_consent, shap_info)

    return {
        "decision": label,
        "score": proba,
        "explanation": shap_info,
        "remediation": remediation,
        "consent_applied": consent_flags,
    }

