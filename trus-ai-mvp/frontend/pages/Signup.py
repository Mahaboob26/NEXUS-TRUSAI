import streamlit as st

from auth import register_user


def main():
    st.set_page_config(page_title="TRUS.AI – Signup", layout="wide")

    st.markdown(
        """
        <h1>Sign up</h1>
        <p>Create an account to use TRUS.AI.</p>
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")

    if st.button("Sign up"):
        if not username or not password:
            st.warning("Please enter username and password.")
        else:
            success, msg = register_user(username, password)
            if success:
                st.success("Signup successful. You can now log in from the Login page.")
            else:
                st.error(msg)


if __name__ == "__main__":
    main()
