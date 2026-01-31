import streamlit as st

from auth import is_logged_in, login_user, set_session, logout


from theme import apply_bank_theme


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
