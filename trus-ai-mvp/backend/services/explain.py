import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import shap


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"


def load_explainer():
    explainer_path = MODEL_DIR / "explainer.pkl"
    if explainer_path.exists():
        try:
            with open(explainer_path, "rb") as f:
                obj = pickle.load(f)
            return obj.get("explainer"), obj.get("feature_names")
        except Exception:
            # If the explainer file is empty or corrupted, ignore it and
            # fall back to computing SHAP values dynamically.
            return None, None
    return None, None


def compute_shap_values(
    model,
    features_df: pd.DataFrame,
) -> Tuple[np.ndarray, List[str]]:
    """Compute SHAP values for a single-row dataframe."""

    explainer, feature_names = load_explainer()
    if explainer is not None and feature_names is not None:
        shap_values = explainer.shap_values(features_df)[0]
        return np.array(shap_values), feature_names

    # Fallback: use TreeExplainer or KernelExplainer directly on the model
    try:
        internal_model = getattr(model, "named_steps", {}).get("classifier", model)
        explainer = shap.Explainer(internal_model, features_df)
        shap_values = explainer(features_df).values[0]
        return np.array(shap_values), list(features_df.columns)
    except Exception:
        # Last resort: approximate by feature-wise contribution from coefficients
        if hasattr(model, "coef_"):
            coefs = model.coef_[0]
            shap_vals = coefs * features_df.values[0]
            return shap_vals, list(features_df.columns)
        return np.zeros(features_df.shape[1]), list(features_df.columns)


def shap_to_plain_english(
    shap_values: np.ndarray,
    feature_names: List[str],
    features_row: Dict[str, Any],
    decision_label: str,
) -> Dict[str, Any]:
    """Generate a human-readable SHAP explanation.

    Returns structure with top positive/negative contributors and
    a summary sentence like:
    "Loan denied because credit_amount (5000) and age (21) lowered your score the most."
    """

    impact = list(zip(feature_names, shap_values))
    impact_sorted = sorted(impact, key=lambda x: abs(x[1]), reverse=True)

    top_k = 5
    top_features = impact_sorted[:top_k]
    top_negative = [
        {"feature": f, "value": features_row.get(f), "shap": float(v)}
        for f, v in impact_sorted
        if v < 0
    ][:top_k]
    top_positive = [
        {"feature": f, "value": features_row.get(f), "shap": float(v)}
        for f, v in impact_sorted
        if v > 0
    ][:top_k]

    if decision_label == "approved":
        direction = "supported your approval"
    else:
        direction = "lowered your score the most"

    if top_negative:
        primary = top_negative[0]
    elif top_positive:
        primary = top_positive[0]
    else:
        primary = {"feature": None, "value": None}

    if primary["feature"] is not None:
        summary = (
            f"Loan {decision_label} because {primary['feature']} "
            f"({primary['value']}) {direction}."
        )
    else:
        summary = f"Loan {decision_label} based on the overall risk profile from your data."

    return {
        "summary": summary,
        "top_features": top_features,
        "top_negative": top_negative,
        "top_positive": top_positive,
    }

