import requests
import streamlit as st

from auth import is_logged_in, logout


BACKEND_URL = "http://localhost:8000"


def call_chat(question: str, context: dict | None = None):
    resp = requests.post(
        f"{BACKEND_URL}/chat",
        json={"question": question, "context": context or {}},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


from theme import apply_bank_theme


if not is_logged_in():
    apply_bank_theme()
    st.warning("Please login first.")
    st.page_link("pages/Login.py", label="Go to Login")
    st.stop()

apply_bank_theme()

col_header, col_logout = st.columns([6, 1])
with col_header:
    st.markdown(
        """
    <div class="trus-header">
        <h1>Loan Advisor Chatbot</h1>
        <p>Ask policy-safe questions about improving approval chances and understanding decisions.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
with col_logout:
    if st.button("Logout"):
        logout()
        st.rerun()

st.markdown("### Ask a question")
question = st.text_area(
    "Your question",
    value="How can I improve my chances of loan approval?",
    height=100,
)

last_decision = st.session_state.get("last_decision")
if last_decision:
    st.info("Using your last model decision as context for this conversation.")

placeholder = st.empty()

if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    with placeholder.container():
        st.markdown('<div class="trus-card">', unsafe_allow_html=True)
        with st.spinner("Thinking through your query and checking policy-safe guidance…"):
            try:
                result = call_chat(question, context=last_decision)
            except Exception as e:
                st.error(f"Error calling chatbot: {e}")
                st.markdown('</div>', unsafe_allow_html=True)
                st.stop()
        st.markdown("### Answer")
        st.write(result.get("answer"))
        st.markdown('</div>', unsafe_allow_html=True)

