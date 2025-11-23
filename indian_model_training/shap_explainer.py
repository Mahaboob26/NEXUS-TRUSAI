from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import shap

import pickle


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"


def load_model_and_explainer():
    """Load trained model and build a SHAP explainer dynamically.

    We avoid pickling the explainer (KernelExplainer with lambdas is not
    picklable across processes). Instead, we rebuild it on demand using a
    small background sample from the training data.
    """

    model_path = MODELS_DIR / "model.pkl"
    with open(model_path, "rb") as f:
        model_bundle = pickle.load(f)

    model = model_bundle["model"]
    feature_names = model_bundle["feature_names"]

    # Load background data from CSV and align columns
    csv_path = DATA_DIR / "indian_loan_dataset.csv"
    df = pd.read_csv(csv_path)
    if "Approved" in df.columns:
        df = df.drop(columns=["Approved"])

    background = df[feature_names].sample(min(200, len(df)), random_state=42)

    explainer = shap.KernelExplainer(
        lambda data: model.predict_proba(pd.DataFrame(data, columns=feature_names))[:, 1],
        shap.sample(background, min(100, len(background))),
    )

    return model, explainer, feature_names


def compute_shap_for_row(
    explainer, feature_names: List[str], row_df: pd.DataFrame
) -> np.ndarray:
    shap_vals = explainer.shap_values(row_df)[0]
    return np.array(shap_vals)


def shap_to_reasons(
    shap_values: np.ndarray,
    feature_names: List[str],
    row: Dict[str, Any],
    decision_label: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    impact = list(zip(feature_names, shap_values))
    impact_sorted = sorted(impact, key=lambda x: abs(x[1]), reverse=True)

    top_features = impact_sorted[:top_k]
    top_negative = [
        {"feature": f, "value": row.get(f), "shap": float(v)}
        for f, v in impact_sorted
        if v < 0
    ][:top_k]
    top_positive = [
        {"feature": f, "value": row.get(f), "shap": float(v)}
        for f, v in impact_sorted
        if v > 0
    ][:top_k]

    if decision_label == "approved":
        direction = "supported your approval"
    else:
        direction = "reduced your approval score"

    if top_negative:
        main = top_negative[0]
    elif top_positive:
        main = top_positive[0]
    else:
        main = {"feature": None, "value": None, "shap": 0.0}

    if main["feature"]:
        summary = (
            f"Loan {decision_label} because {main['feature']} ({main['value']}) "
            f"{direction} by {main['shap']:.2f}."
        )
    else:
        summary = f"Loan {decision_label} based on the overall risk profile of your application."

    return {
        "summary": summary,
        "top_features": top_features,
        "top_negative": top_negative,
        "top_positive": top_positive,
    }

