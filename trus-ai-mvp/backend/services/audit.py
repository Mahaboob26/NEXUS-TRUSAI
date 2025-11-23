import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db.sqlite"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    input_hash = Column(String(64), nullable=False)
    output_hash = Column(String(64), nullable=False, unique=True)
    previous_hash = Column(String(64), nullable=True)
    shap_values = Column(Text, nullable=True)
    consent_state = Column(Text, nullable=True)
    model_version = Column(String(64), nullable=False)
    decision = Column(String(32), nullable=False)
    probability = Column(String(32), nullable=False)


class GovernanceAudit(Base):
    """Separate table for governance audit events with richer payload.

    This keeps the original AuditLog schema intact, while providing an
    extensible, event-typed hash chain for governance use cases.
    """

    __tablename__ = "governance_audit"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(32), nullable=False)
    model_version = Column(String(64), nullable=True)
    input_features = Column(Text, nullable=True)
    output_decision = Column(Text, nullable=True)
    fairness_snapshot = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=True)
    output_hash = Column(String(64), nullable=False, unique=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def compute_sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_last_output_hash(session) -> Optional[str]:
    last = session.query(AuditLog).order_by(AuditLog.id.desc()).first()
    return last.output_hash if last else None


def get_last_governance_hash(session) -> Optional[str]:
    last = session.query(GovernanceAudit).order_by(GovernanceAudit.id.desc()).first()
    return last.output_hash if last else None


def record_audit_entry(
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    shap_values: Any,
    consent_state: Dict[str, Any],
    model_version: str,
) -> None:
    session = SessionLocal()
    try:
        input_str = json.dumps(input_payload, sort_keys=True)
        output_str = json.dumps(output_payload, sort_keys=True)
        shap_str = json.dumps(shap_values, default=float)
        consent_str = json.dumps(consent_state, sort_keys=True)

        input_hash = compute_sha256(input_str)

        previous_hash = get_last_output_hash(session)
        chain_payload = json.dumps(
            {
                "input_hash": input_hash,
                "output": output_payload,
                "previous_hash": previous_hash,
            },
            sort_keys=True,
        )
        output_hash = compute_sha256(chain_payload)

        log = AuditLog(
            input_hash=input_hash,
            output_hash=output_hash,
            previous_hash=previous_hash,
            shap_values=shap_str,
            consent_state=consent_str,
            model_version=model_version,
            decision=str(output_payload.get("decision")),
            probability=str(output_payload.get("probability")),
        )
        session.add(log)
        session.commit()
    finally:
        session.close()


def record_governance_event(
    event_type: str,
    details: Dict[str, Any],
    model_version: Optional[str] = None,
    input_features: Optional[Dict[str, Any]] = None,
    output_decision: Optional[Dict[str, Any]] = None,
    fairness_snapshot: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a governance-related event into a separate hash-chained table.

    Event types include: "decision", "bias-alert", "model-update",
    "override", "consent-change".
    """

    session = SessionLocal()
    try:
        input_str = json.dumps(input_features or {}, sort_keys=True)
        output_str = json.dumps(output_decision or {}, sort_keys=True)
        fair_str = json.dumps(fairness_snapshot or {}, sort_keys=True)
        details_str = json.dumps(details or {}, sort_keys=True)

        previous_hash = get_last_governance_hash(session)
        chain_payload = json.dumps(
            {
                "event_type": event_type,
                "model_version": model_version,
                "input_features": input_str,
                "output_decision": output_str,
                "fairness_snapshot": fair_str,
                "details": details_str,
                "previous_hash": previous_hash,
            },
            sort_keys=True,
        )
        output_hash = compute_sha256(chain_payload)

        log = GovernanceAudit(
            event_type=event_type,
            model_version=model_version or "unknown",
            input_features=input_str,
            output_decision=output_str,
            fairness_snapshot=fair_str,
            details=details_str,
            previous_hash=previous_hash,
            output_hash=output_hash,
        )
        session.add(log)
        session.commit()
    finally:
        session.close()


def list_governance_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent governance events for the dashboard (most recent first)."""

    session = SessionLocal()
    try:
        q = session.query(GovernanceAudit).order_by(GovernanceAudit.id.desc()).limit(limit)
        rows = []
        for row in q:
            rows.append(
                {
                    "id": row.id,
                    "timestamp": row.timestamp.isoformat() + "Z",
                    "eventType": row.event_type,
                    "modelVersion": row.model_version,
                    "previousHash": row.previous_hash,
                    "outputHash": row.output_hash,
                    "inputFeatures": json.loads(row.input_features or "{}"),
                    "outputDecision": json.loads(row.output_decision or "{}"),
                    "fairnessSnapshot": json.loads(row.fairness_snapshot or "{}"),
                    "details": json.loads(row.details or "{}"),
                }
            )
        return rows
    finally:
        session.close()


def verify_governance_chain() -> bool:
    """Verify integrity of the governance hash chain.

    Recomputes hashes over GovernanceAudit rows and checks that each
    previous_hash matches the actual previous output_hash.
    """

    session = SessionLocal()
    try:
        rows = session.query(GovernanceAudit).order_by(GovernanceAudit.id.asc()).all()
        last_hash: Optional[str] = None
        for row in rows:
            # Rebuild payload exactly as in record_governance_event
            chain_payload = json.dumps(
                {
                    "event_type": row.event_type,
                    "model_version": row.model_version,
                    "input_features": row.input_features or "{}",
                    "output_decision": row.output_decision or "{}",
                    "fairness_snapshot": row.fairness_snapshot or "{}",
                    "details": row.details or "{}",
                    "previous_hash": row.previous_hash,
                },
                sort_keys=True,
            )
            expected_hash = compute_sha256(chain_payload)
            if expected_hash != row.output_hash:
                return False
            if row.previous_hash != last_hash:
                # Chain linkage broken
                if last_hash is not None:
                    return False
            last_hash = row.output_hash
        return True
    finally:
        session.close()


def get_summary_stats() -> Dict[str, Any]:
    session = SessionLocal()
    try:
        total = session.query(AuditLog).count()
        approvals = (
            session.query(AuditLog).filter(AuditLog.decision == "approved").count()
        )
        denials = (
            session.query(AuditLog).filter(AuditLog.decision == "denied").count()
        )

        return {
            "total": total,
            "approvals": approvals,
            "denials": denials,
        }
    finally:
        session.close()

