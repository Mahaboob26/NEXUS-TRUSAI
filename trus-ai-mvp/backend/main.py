import pickle
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.chatbot import answer_question
from services.audit import (
    init_db,
    record_audit_entry,
    get_summary_stats,
    record_governance_event,
)
from services.fairness import compute_dataset_fairness
from auth import create_user, authenticate_user, create_session_token


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from indian_model_training.inference_pipeline import (  # type: ignore E402
    predict_with_explanation as indian_predict,
)
from indian_model_training.consent_engine import (  # type: ignore E402
    load_feature_groups,
    load_consent,
    save_consent,
    get_default_consent,
    load_user_profile,
)


def load_model_version() -> Dict[str, Any]:
    """Load model version metadata from modelVersion.json.

    Falls back to a minimal structure if the file is missing.
    """

    meta_path = BASE_DIR / "modelVersion.json"
    if not meta_path.exists():
        return {"version": "indian_v1"}
    try:
        import json

        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "indian_v1"}


def get_current_model_version() -> str:
    meta = load_model_version()
    return str(meta.get("version", "indian_v1"))


class LoanApplication(BaseModel):
    features: Dict[str, Any]
    consent: Dict[str, bool] | None = None


class ChatRequest(BaseModel):
    question: str
    context: Dict[str, Any] | None = None


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


app = FastAPI(title="TRUS.AI MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MODEL_VERSION = "indian_v1"

MODEL_ACTIVE = True

init_db()


@app.get("/health")
def health():
    return {"status": "ok", "model_active": MODEL_ACTIVE}


@app.post("/auth/signup")
def signup(req: SignupRequest):
    email = req.email.strip().lower()
    if not email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        create_user(email, req.password)
    except Exception as e:  # pragma: no cover - demo-friendly error handling
        # Most likely a duplicate email
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True}


@app.post("/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    if not email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    if not authenticate_user(email, req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_session_token(email)
    return {"ok": True, "token": token, "email": email}


@app.post("/predict")
def predict(app_input: LoanApplication):
    global MODEL_ACTIVE
    if not MODEL_ACTIVE:
        raise HTTPException(status_code=503, detail="Model is paused by administrator")

    features_raw = app_input.features

    # If explicit consent flags are provided in the request, honour them.
    # Otherwise fall back to the persisted consent state from the consent engine.
    consent = app_input.consent or load_consent()

    result = indian_predict(features_raw, consent)

    decision = result["decision"]
    score = float(result["score"])

    record_audit_entry(
        input_payload={"features": features_raw},
        output_payload={"decision": decision, "probability": score},
        shap_values=result.get("explanation", {}),
        consent_state=consent,
        model_version=get_current_model_version(),
    )

    return {
        "decision": decision,
        "probability": score,
        "explanation": result.get("explanation"),
        "remediation": result.get("remediation"),
    }


@app.get("/consent/state")
def get_consent_state():
    """Return current feature groups and consent state for the UI.

    This lets the Consent page build toggles dynamically based on the
    dataset-driven groups in the Indian consent engine.
    """

    groups = load_feature_groups()
    state = load_consent()
    return {"groups": groups, "consent": state}


@app.post("/consent/state")
def set_consent_state(new_state: Dict[str, bool]):
    """Persist consent state from the UI.

    The payload is expected to be a simple mapping of group name -> bool.
    """

    save_consent(new_state)
    return {"ok": True, "consent": load_consent()}


@app.post("/consent/reset")
def reset_consent_state():
    """Reset consent state to default (all groups allowed)."""

    default_state = get_default_consent()
    save_consent(default_state)
    return {"ok": True, "consent": default_state}


@app.get("/consent/knowledge")
def get_consent_knowledge():
    """Return the current stored feature/profile view ("what the AI knows").

    This is a minimal endpoint that simply exposes the JSON profile maintained
    by the Indian consent engine, without any schema redesign.
    """

    profile = load_user_profile()
    return {"profile": profile}


@app.post("/chat")
def chat(req: ChatRequest):
    answer = answer_question(req.question, req.context or {})
    return {"answer": answer}


@app.get("/api/governance/model")
def governance_model():
    """Return current model version metadata for governance dashboard."""

    meta = load_model_version()
    # Also surface current active/paused state
    return {"model": meta, "model_active": MODEL_ACTIVE}


def _check_bias_thresholds(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Derive simple bias alerts from fairness metrics.

    Uses selection rate by group as a proxy to compute:
      - disparate impact (min / max selection rate)
      - statistical parity difference (max - min selection rate)

    Flags biasDetected if thresholds are crossed.
    """

    alerts: Dict[str, Any] = {"biasDetected": False, "reasons": []}
    if not metrics.get("available"):
        return alerts

    by_group = metrics.get("by_group") or {}
    if not by_group:
        return alerts

    rates = list(by_group.values())
    max_sr = max(rates)
    min_sr = min(rates)
    if max_sr <= 0:
        return alerts

    disparate_impact = float(min_sr / max_sr)
    sp_diff = float(max_sr - min_sr)

    # Simple demo thresholds; in a real bank these would be configurable
    if disparate_impact < 0.8:
        alerts["biasDetected"] = True
        alerts["reasons"].append(
            {
                "metric": "disparate_impact",
                "value": disparate_impact,
                "threshold": 0.8,
            }
        )
    if sp_diff > 0.2:
        alerts["biasDetected"] = True
        alerts["reasons"].append(
            {
                "metric": "statistical_parity_difference",
                "value": sp_diff,
                "threshold": 0.2,
            }
        )

    return alerts


@app.get("/api/governance/fairness")
def governance_fairness():
    """Compute fairness metrics and emit bias alerts if thresholds crossed."""

    metrics = compute_dataset_fairness()
    alerts = _check_bias_thresholds(metrics)

    if alerts.get("biasDetected"):
        # Record a governance bias-alert event with a snapshot of metrics
        record_governance_event(
            event_type="bias-alert",
            details={"alerts": alerts.get("reasons", [])},
            model_version=get_current_model_version(),
            fairness_snapshot=metrics,
        )

    return {"metrics": metrics, **alerts}


@app.get("/dashboard/summary")
def dashboard_summary():
    from services.audit import get_request_volume, get_recent_decisions, get_risk_distribution
    
    stats = get_summary_stats()
    stats["volume"] = get_request_volume(days=7)
    stats["recent"] = get_recent_decisions(limit=10)
    stats["risk_distribution"] = get_risk_distribution()
    return stats


@app.get("/dashboard/fairness")
def dashboard_fairness():
    return compute_dataset_fairness()


@app.post("/model/pause")
def pause_model():
    global MODEL_ACTIVE
    MODEL_ACTIVE = False
    return {"model_active": MODEL_ACTIVE}


@app.post("/model/resume")
def resume_model():
    global MODEL_ACTIVE
    MODEL_ACTIVE = True
    return {"model_active": MODEL_ACTIVE}

