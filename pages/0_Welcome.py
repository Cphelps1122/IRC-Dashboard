import streamlit as st
from auth import authenticate, check_auth

st.set_page_config(page_title="Welcome", layout="centered")

# If already authenticated, redirect to Overview
if check_auth():
    st.switch_page("pages/1_Overview.py")

st.markdown("## IRC Utility Dashboard")
st.markdown("### Secure Access Portal")
st.write("Please enter your passcode to continue.")

passcode_input = st.text_input("Passcode", type="password")

if st.button("Login"):
    if authenticate(passcode_input):
        st.success("Access granted.")
        st.switch_page("pages/1_Overview.py")
    else:
        st.error("Incorrect passcode.")
