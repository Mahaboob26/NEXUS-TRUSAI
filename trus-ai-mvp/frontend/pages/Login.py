import streamlit as st

from auth import is_logged_in, login_user, set_session, logout


def apply_bank_theme():
    st.set_page_config(page_title="TRUS.AI – Login", layout="wide")
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; background: #f3f4f6; }
        .trus-header {
            background: linear-gradient(90deg, #0d47a1, #1976d2);
            padding: 1.5rem 2rem;
            border-radius: 0 0 18px 18px;
            color: #f9fafb !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
        }
        .trus-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 1.5rem 1.75rem;
            box-shadow: 0 6px 20px rgba(15, 23, 42, 0.10);
            border: 1px solid rgba(148, 163, 184, 0.4);
            color: #111827;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_bank_theme()

st.markdown(
    """
    <div class="trus-header">
        <h1>TRUS.AI Account</h1>
        <p>Login to access TRUS.AI loan simulator, consent dashboard and chatbot.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if is_logged_in():
    st.success(f"Already logged in as {st.session_state.get('username')}")
    if st.button("Go to Home"):
        st.switch_page("streamlit_app.py")
else:
    st.markdown("### Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.warning("Please enter username and password.")
        else:
            if login_user(username, password):
                set_session(username)
                st.success(f"Logged in as {username}")
                st.rerun()
            else:
                st.error("Invalid username or password.")

st.markdown("---")
st.info("Don't have an account? Go to the Signup page in the sidebar.")

if is_logged_in():
    if st.button("Logout"):
        logout()
        st.success("Logged out.")
        st.rerun()
