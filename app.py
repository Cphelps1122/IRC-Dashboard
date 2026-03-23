import streamlit as st
from auth import require_auth
from utils.load_data import load_data

st.set_page_config(page_title="IRC Dashboard", layout="wide")

# Require authentication
require_auth()

df, last_updated = load_data()

st.markdown("# IRC Utility Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

st.markdown("""
Use the sidebar to navigate between:
- **Overview**
- **Dashboard**
- **Property Detail**
- **Billing Health**
- **Benchmarking**
- **Rate Change Detector**
""")
