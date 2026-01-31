import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"


def simulate_indian_dataset(csv_path: Path, n: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(42)

    data = {
        "ApplicantIncome": rng.integers(15000, 200000, size=n),
        "CoapplicantIncome": rng.integers(0, 150000, size=n),
        "LoanAmount": rng.integers(50000, 2500000, size=n),
        "Loan_Amount_Term": rng.integers(12, 360, size=n),
        "Credit_History": rng.choice([0, 1], size=n, p=[0.25, 0.75]),
        "Gender": rng.choice(["Male", "Female"], size=n, p=[0.7, 0.3]),
        "Married": rng.choice(["Yes", "No"], size=n, p=[0.6, 0.4]),
        "Dependents": rng.choice(["0", "1", "2", "3+"], size=n, p=[0.5, 0.2, 0.2, 0.1]),
        "Education": rng.choice(["Graduate", "Not Graduate"], size=n, p=[0.7, 0.3]),
        "Self_Employed": rng.choice(["Yes", "No"], size=n, p=[0.2, 0.8]),
        "Property_Area": rng.choice(["Urban", "Semiurban", "Rural"], size=n, p=[0.4, 0.35, 0.25]),
        "mobile_usage_score": rng.integers(300, 950, size=n),
        "transaction_stability_score": rng.integers(300, 950, size=n),
        "bank_balance": rng.integers(0, 800000, size=n),
    }

    df = pd.DataFrame(data)

    # Engineered features
    df["total_income"] = df["ApplicantIncome"] + df["CoapplicantIncome"]
    df["emi"] = df["LoanAmount"] / df["Loan_Amount_Term"]
    df["income_to_emi_ratio"] = df["total_income"] / (df["emi"] + 1)
    df["credit_utilization"] = df["LoanAmount"] / (df["bank_balance"] + 50000)
    df["stability_score"] = (
        0.4 * (df["transaction_stability_score"] / 950)
        + 0.3 * (df["mobile_usage_score"] / 950)
        + 0.3 * df["Credit_History"]
    )
    df["cibil_proxy_score"] = (
        0.35 * (df["transaction_stability_score"])
        + 0.25 * (df["mobile_usage_score"])
        + 0.2 * (df["total_income"] / df["total_income"].max() * 900)
        + 0.2 * (df["Credit_History"] * 900)
    ) / 2

    # Risk / approval label (1=approved, 0=rejected)
    score = (
        0.3 * (df["cibil_proxy_score"] / 900)
        + 0.25 * (df["income_to_emi_ratio"] / (df["income_to_emi_ratio"].quantile(0.9) + 1))
        + 0.2 * df["Credit_History"]
        + 0.15 * (df["bank_balance"] / (df["bank_balance"].quantile(0.9) + 1))
        - 0.1 * df["credit_utilization"]
    )

    approval_prob = (score - score.min()) / (score.max() - score.min() + 1e-6)
    approved = rng.binomial(1, np.clip(approval_prob, 0.05, 0.95))
    df["Approved"] = approved

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return df


def load_data() -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / "indian_loan_dataset.csv"
    if csv_path.exists() and csv_path.stat().st_size > 0:
        return pd.read_csv(csv_path)
    return simulate_indian_dataset(csv_path)



def build_pipeline(df: pd.DataFrame):
    target_col = "Approved"

    X_full = df.drop(columns=[target_col])
    y = df[target_col]

    # Define feature groups
    numeric_cols = [
        "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
        "mobile_usage_score", "transaction_stability_score", "bank_balance",
        "total_income", "emi", "income_to_emi_ratio", "credit_utilization",
        "stability_score", "cibil_proxy_score"
    ]
    
    # Selecting columns that exist in the dataframe (in case simulation changes)
    numeric_cols = [c for c in numeric_cols if c in X_full.columns]
    
    categorical_cols = [
        "Gender", "Married", "Dependents", "Education", 
        "Self_Employed", "Property_Area", "Credit_History"
    ]
    categorical_cols = [c for c in categorical_cols if c in X_full.columns]

    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder

    # Build the column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]), numeric_cols),
            ("cat", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore"))
            ]), categorical_cols),
        ]
    )

    log_reg = Pipeline(
        steps=[("preprocessor", preprocessor), ("model", LogisticRegression(max_iter=1000))]
    )

    rf = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42)),
        ]
    )

    # Return only the subset of columns used (for feature naming later)
    X = X_full[numeric_cols + categorical_cols]
    
    return (log_reg, rf), X, y, numeric_cols + categorical_cols


def evaluate_model(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    try:
        auc = roc_auc_score(y_test, y_proba)
    except ValueError:
        auc = 0.0

    return {"model": model, "accuracy": acc, "f1": f1, "auc": auc}


def train_and_save():
    df = load_data()
    (log_reg, rf), X, y, numeric_cols = build_pipeline(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = []
    for name, model in [("logistic", log_reg), ("random_forest", rf)]:
        metrics = evaluate_model(model, X_train, X_test, y_train, y_test)
        metrics["name"] = name
        results.append(metrics)

    # Select by AUC, then F1
    best = sorted(results, key=lambda m: (m["auc"], m["f1"]), reverse=True)[0]
    best_model = best["model"]

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "model.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(
            {
                "model": best_model,
                "feature_names": X.columns.tolist(),
                "metrics": best,
            },
            f,
        )

    print("=== Training summary ===")
    for r in results:
        print(
            f"{r['name']}: acc={r['accuracy']:.3f}, f1={r['f1']:.3f}, auc={r['auc']:.3f}"
        )
    print(f"Best model: {best['name']}")
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    train_and_save()

