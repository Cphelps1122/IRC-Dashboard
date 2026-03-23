import streamlit as st

PASSCODE = "1234"

def check_auth():
    """Return True if user is authenticated."""
    return st.session_state.get("authenticated", False)

def require_auth():
    """Redirect to Welcome page if not authenticated."""
    if not check_auth():
        st.switch_page("pages/0_Welcome.py")

def authenticate(passcode_input):
    """Validate passcode and set session state."""
    if passcode_input == PASSCODE:
        st.session_state["authenticated"] = True
        return True
    return False
