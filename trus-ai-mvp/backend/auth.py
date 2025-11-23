from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db.sqlite"

# Simple HMAC-based token secret for demo purposes
_SECRET_KEY = os.environ.get("TRUS_AI_AUTH_SECRET", "trus-ai-demo-secret")
_TOKEN_TTL_HOURS = 24


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _hash_password(password: str) -> str:
    # Use PBKDF2-HMAC-SHA256 for password hashing (no external deps)
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + dk.hex()


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, dk_hex = password_hash.split(":", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(dk_hex)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(candidate, expected)


def create_user(email: str, password: str) -> None:
    conn = _get_conn()
    try:
        password_hash = _hash_password(password)
        conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.lower(), password_hash, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> bool:
    conn = _get_conn()
    try:
        cur = conn.execute("SELECT password_hash FROM users WHERE email = ?", (email.lower(),))
        row = cur.fetchone()
        if not row:
            return False
        return _verify_password(password, row["password_hash"])
    finally:
        conn.close()


def create_session_token(email: str) -> str:
    """Create a simple signed session token with expiry.

    Token format (ASCII, not JWT): email|expiry_iso|signature
    signature = HMAC-SHA256(secret, email|expiry_iso)
    """

    expiry = (datetime.utcnow() + timedelta(hours=_TOKEN_TTL_HOURS)).isoformat() + "Z"
    payload = f"{email.lower()}|{expiry}"
    sig = hmac.new(_SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}|{sig}"


def verify_session_token(token: str) -> Optional[str]:
    try:
        email, expiry, sig = token.split("|", 3)
    except ValueError:
        return None

    payload = f"{email}|{expiry}"
    expected_sig = hmac.new(
        _SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return None

    try:
        expiry_dt = datetime.fromisoformat(expiry.replace("Z", ""))
    except Exception:
        return None
    if expiry_dt < datetime.utcnow():
        return None

    return email.lower()
