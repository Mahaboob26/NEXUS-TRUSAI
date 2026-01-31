import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"


def register_user(username: str, password: str) -> bool:
    """Register a new user via the backend API."""
    username = username.strip().lower()
    if not username or not password:
        return False

    try:
        resp = requests.post(
            f"{BACKEND_URL}/auth/signup",
            json={"email": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return True
        else:
            # You might want to log the error reason here
            print(f"Signup failed: {resp.text}")
            return False
    except Exception as e:
        print(f"Signup exception: {e}")
        return False


def login_user(username: str, password: str) -> bool:
    """Login user via backend API and store token if successful."""
    username = username.strip().lower()
    try:
        resp = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                # Store token in session state for use in other requests
                st.session_state["auth_token"] = data.get("token")
                return True
    except Exception as e:
        print(f"Login exception: {e}")
        return False
    
    return False


def set_session(username: str) -> None:
    st.session_state["username"] = username.strip().lower()
    st.session_state["logged_in"] = True


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in"))


def logout() -> None:
    st.session_state.clear()
