import json
from pathlib import Path

import streamlit as st

USERS_PATH = Path(__file__).resolve().parent / "users.json"


def _load_users() -> dict:
    if not USERS_PATH.exists():
        return {}
    try:
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users: dict) -> None:
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_password(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    if not username or not password:
        return False

    users = _load_users()
    if username in users:
        return False

    users[username] = _hash_password(password)
    _save_users(users)
    return True


def user_exists(username: str) -> bool:
    username = username.strip().lower()
    users = _load_users()
    return username in users


def login_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return False
    return users[username] == _hash_password(password)


def set_session(username: str) -> None:
    st.session_state["username"] = username.strip().lower()
    st.session_state["logged_in"] = True


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in"))


def logout() -> None:
    st.session_state.clear()
