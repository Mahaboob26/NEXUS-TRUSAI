import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import shap


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"


def load_or_download_data() -> pd.DataFrame:
    """Load credit dataset, downloading from OpenML if not already saved.

    Uses the German Credit dataset (OpenML id "credit-g"). Saves a local CSV
    to backend/data/credit_data.csv for reproducibility.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / "credit_data.csv"

    if csv_path.exists():
        return pd.read_csv(csv_path)

    dataset = fetch_openml("credit-g", version=1, as_frame=True)
    df = dataset.frame
    df.to_csv(csv_path, index=False)
    return df


def build_pipeline(df: pd.DataFrame):
    """Create preprocessing + model pipeline for binary classification."""

    target_col = "class"
    X = df.drop(columns=[target_col])
    y = (df[target_col] == "good").astype(int)

    numeric_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    numeric_transformer = "passthrough"
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ]
    )

    clf = LogisticRegression(max_iter=1000)

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ]
    )

    return model, X, y, numeric_cols, categorical_cols


def train_and_save():
    df = load_or_download_data()
    model, X, y, numeric_cols, categorical_cols = build_pipeline(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model.fit(X_train, y_train)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(
            {
                "model": model,
                "numeric_cols": numeric_cols,
                "categorical_cols": categorical_cols,
                "feature_names": X.columns.tolist(),
            },
            f,
        )

    # We no longer persist a SHAP explainer here because certain explainer
    # objects (especially those built around local functions) are not
    # picklable across processes. Instead, SHAP explanations are computed
    # on demand in services.explain using the trained model pipeline.

    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    train_and_save()

