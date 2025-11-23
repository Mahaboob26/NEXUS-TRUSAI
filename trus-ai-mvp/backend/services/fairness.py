from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from fairlearn.metrics import MetricFrame, selection_rate


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"


def _compute_fairness_overview(
    df_predictions: pd.DataFrame,
    sensitive_feature: str,
) -> Dict[str, Any]:
    """Compute simple fairness metrics using Fairlearn for a given DataFrame.

    Expects df_predictions with columns: y_true, y_pred, and sensitive_feature.
    """

    if sensitive_feature not in df_predictions.columns:
        return {"available": False, "reason": f"No '{sensitive_feature}' column"}

    y_true = df_predictions["y_true"].values
    y_pred = df_predictions["y_pred"].values
    sf = df_predictions[sensitive_feature].astype(str).values

    mf = MetricFrame(
        metrics={"selection_rate": selection_rate},
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sf,
    )

    return {
        "available": True,
        "sensitive_feature": sensitive_feature,
        "overall_selection_rate": float(selection_rate(y_true, y_pred)),
        "by_group": {k: float(v["selection_rate"]) for k, v in mf.by_group.iterrows()},
    }


def compute_dataset_fairness() -> Dict[str, Any]:
    """Load the training dataset and current model, compute fairness metrics.

    We treat the model's prediction as a selection indicator and measure selection
    rate by group (e.g. by 'sex' or 'personal_status').
    """

    from . import explain as _explain  # ensure dependencies are available
    import pickle

    data_path = DATA_DIR / "credit_data.csv"
    if not data_path.exists():
        return {"available": False, "reason": "credit_data.csv not found"}

    df = pd.read_csv(data_path)
    if "class" not in df.columns:
        return {"available": False, "reason": "No 'class' column in dataset"}

    y_true = (df["class"] == "good").astype(int)
    X = df.drop(columns=["class"])

    model_path = MODEL_DIR / "model.pkl"
    if not model_path.exists():
        return {"available": False, "reason": "model.pkl not found"}

    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    model = bundle["model"]

    y_pred_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    df_pred = pd.DataFrame({"y_true": y_true, "y_pred": y_pred})

    # Try common sensitive attributes in the German credit dataset
    sensitive_candidates = ["sex", "personal_status", "personal_status_sex"]
    for col in sensitive_candidates:
        if col in df.columns:
            df_pred[col] = df[col]
            return _compute_fairness_overview(df_pred, col)

    return {"available": False, "reason": "No suitable sensitive attribute found"}

