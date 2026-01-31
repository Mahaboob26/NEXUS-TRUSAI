import requests
import streamlit as st

import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def register_user(username: str, password: str) -> tuple[bool, str]:
    """Register a new user via the backend API."""
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required"

    try:
        resp = requests.post(
            f"{BACKEND_URL}/auth/signup",
            json={"email": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return True, "Success"
        else:
            # Try to get detail from backend
            try:
                detail = resp.json().get("detail", resp.text)
            except:
                detail = resp.text
            print(f"Signup failed: {detail}")
            return False, f"Signup failed: {detail}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to Backend at {BACKEND_URL}. Is it running?"
    except Exception as e:
        print(f"Signup exception: {e}")
        return False, f"Error: {e}"


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
