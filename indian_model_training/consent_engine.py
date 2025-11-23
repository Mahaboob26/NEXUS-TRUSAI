from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATASET_PATH = DATA_DIR / "indian_loan_dataset.csv"
CONSENT_STATE_PATH = BASE_DIR / ".consent_state.json"
USER_PROFILE_PATH = BASE_DIR / ".user_profile.json"
ACCESS_LOG_PATH = BASE_DIR / "access_log.json"

_FEATURE_GROUPS_CACHE: Dict[str, list[str]] | None = None


def get_feature_groups_from_dataset() -> Dict[str, list[str]]:
    """Build consent groups dynamically from the Indian loan dataset.

    Groups follow the prompt terminology (only populated if columns exist):

      - "Financial Data":
          ApplicantIncome, CoapplicantIncome, LoanAmount, Loan_Amount_Term,
          plus engineered: total_income, emi, income_to_emi_ratio, credit_utilization

      - "Credit History Data":
          Credit_History, cibil_proxy_score

      - "Demographic Data":
          Gender, Married, Dependents, Education, Self_Employed, Property_Area

      - "Behaviour / Digital Data":
          mobile_usage_score, transaction_stability_score, digital_footprint,
          transaction_score, stability_score

      - "Banking Behaviour Data":
          AvgBalance, TransactionScore (or similarly named columns, if present)
    """

    global _FEATURE_GROUPS_CACHE
    if _FEATURE_GROUPS_CACHE is not None:
        return _FEATURE_GROUPS_CACHE

    if not DATASET_PATH.exists():
        # Fallback: if dataset is not present, use static grouping
        groups = {
            "Financial Data": [
                "ApplicantIncome",
                "CoapplicantIncome",
                "LoanAmount",
                "Loan_Amount_Term",
                "total_income",
                "emi",
                "income_to_emi_ratio",
                "credit_utilization",
            ],
            "Credit History Data": ["Credit_History", "cibil_proxy_score"],
            "Demographic Data": [
                "Gender",
                "Married",
                "Dependents",
                "Education",
                "Self_Employed",
                "Property_Area",
            ],
            "Behaviour / Digital Data": [
                "mobile_usage_score",
                "transaction_stability_score",
                "stability_score",
            ],
            "Banking Behaviour Data": [
                "AvgBalance",
                "TransactionScore",
            ],
        }
        _FEATURE_GROUPS_CACHE = groups
        return groups

    df = pd.read_csv(DATASET_PATH, nrows=1000)
    cols = set(df.columns)

    groups: Dict[str, list[str]] = {
        "Financial Data": [],
        "Credit History Data": [],
        "Demographic Data": [],
        "Behaviour / Digital Data": [],
        "Banking Behaviour Data": [],
    }

    # Financial Data
    for col in [
        "ApplicantIncome",
        "CoapplicantIncome",
        "LoanAmount",
        "Loan_Amount_Term",
    ]:
        if col in cols:
            groups["Financial Data"].append(col)

    # Credit History Data
    if "Credit_History" in cols:
        groups["Credit History Data"].append("Credit_History")

    # Demographic Data
    for col in [
        "Gender",
        "Married",
        "Dependents",
        "Education",
        "Self_Employed",
        "Property_Area",
    ]:
        if col in cols:
            groups["Demographic Data"].append(col)

    # Behaviour / Digital Data if present
    for col in [
        "mobile_usage_score",
        "transaction_stability_score",
        "digital_footprint",
        "transaction_score",
    ]:
        if col in cols:
            groups["Behaviour / Digital Data"].append(col)

    # Banking Behaviour Data (if present in dataset)
    for col in ["AvgBalance", "TransactionScore"]:
        if col in cols:
            groups["Banking Behaviour Data"].append(col)

    # Attach engineered features to relevant groups as described in the prompt
    groups["Financial Data"].extend(
        ["total_income", "emi", "income_to_emi_ratio", "credit_utilization"]
    )
    groups["Behaviour / Digital Data"].extend(["stability_score"])
    groups["Credit History Data"].extend(["cibil_proxy_score"])

    # Remove any empty groups to keep UI tidy
    groups = {k: v for k, v in groups.items() if v}

    _FEATURE_GROUPS_CACHE = groups
    return groups


def load_feature_groups() -> Dict[str, list[str]]:
    """Public helper to get cached/dynamic feature groups."""

    return get_feature_groups_from_dataset()


def get_default_consent() -> Dict[str, bool]:
    """Default consent: all discovered groups allowed."""

    groups = load_feature_groups()
    return {name: True for name in groups.keys()}


def save_consent(consent_state: Dict[str, bool]) -> None:
    """Persist consent state to a local JSON file.

    This allows the UI to save user choices and prediction code to reuse the
    same state across sessions.
    """

    with open(CONSENT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(consent_state, f)


def load_consent() -> Dict[str, bool]:
    """Load consent state from JSON or return default if not set."""

    if CONSENT_STATE_PATH.exists():
        try:
            with open(CONSENT_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure we only keep known groups, fill missing with True
            groups = load_feature_groups()
            cleaned: Dict[str, bool] = {}
            for name in groups.keys():
                cleaned[name] = bool(data.get(name, True))
            return cleaned
        except Exception:
            # On any error, fall back to default
            return get_default_consent()


def load_user_profile() -> Dict[str, Any]:
    """Load stored user profile or return a reasonable default.

    The default roughly matches the Indian feature schema and uses
    mid-range values so the UI can display something meaningful even
    before the user edits their data.
    """

    if USER_PROFILE_PATH.exists():
        try:
            with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback defaults
    return {
        "ApplicantIncome": 60000,
        "CoapplicantIncome": 10000,
        "LoanAmount": 800000,
        "Loan_Amount_Term": 180,
        "Credit_History": 1,
        "Gender": "Male",
        "Married": "Yes",
        "Dependents": "0",
        "Education": "Graduate",
        "Self_Employed": "No",
        "Property_Area": "Urban",
        "mobile_usage_score": 700,
        "transaction_stability_score": 750,
        "bank_balance": 150000,
    }


def save_user_profile(profile: Dict[str, Any]) -> None:
    """Persist user profile to a local JSON file."""

    with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False)


def record_access(feature: str, allowed: bool, model_version: str) -> None:
    """Append a single feature-access record to the access log.

    The log is a JSON-lines style file (one JSON object per line).
    """

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "feature": feature,
        "allowed": bool(allowed),
        "model_version": model_version,
    }
    try:
        with open(ACCESS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # Logging must never break prediction; fail silently.
        return


def get_access_log(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent access log entries (up to `limit`)."""

    if not ACCESS_LOG_PATH.exists():
        return []

    entries: List[Dict[str, Any]] = []
    try:
        with open(ACCESS_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []

    # most recent last in file; return reversed, limited
    return list(reversed(entries))[:limit]

    return get_default_consent()


def apply_consent(features: Dict[str, Any], consent_flags: Dict[str, bool]) -> Dict[str, Any]:
    """Apply consent at group level and record feature accesses.

    For disabled groups we follow the prompt semantics and *remove* those
    features from the input dictionary. For enabled groups we keep the
    original values intact.

    We also record every feature access via `record_access`, marking whether
    it was effectively allowed or blocked by consent.
    """

    groups = load_feature_groups()
    group_allowed = {g: bool(consent_flags.get(g, True)) for g in groups.keys()}

    result: Dict[str, Any] = dict(features)

    # Build reverse map: feature -> group name (first match wins)
    feature_to_group: Dict[str, str] = {}
    for gname, cols in groups.items():
        for c in cols:
            feature_to_group.setdefault(c, gname)

    # Apply consent and log access
    for feature_name in list(result.keys()):
        group_name = feature_to_group.get(feature_name)
        if group_name is None:
            # Feature not in any group; treat as allowed but still log
            record_access(feature_name, True, model_version="indian_v1")
            continue

        allowed = group_allowed.get(group_name, True)
        record_access(feature_name, allowed, model_version="indian_v1")

        if not allowed:
            # Remove feature entirely from the model input
            result.pop(feature_name, None)

    return result

