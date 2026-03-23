import streamlit as st
from utils.load_data import load_data

st.set_page_config(
    page_title="IRC Dashboard",
    layout="wide",
)

df, last_updated = load_data()

st.markdown("# IRC Utility Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

if df.empty:
    st.warning("No data available.")
else:
    st.markdown("### Data Preview")
    st.dataframe(df.head(), use_container_width=True)

st.markdown("""
Use the sidebar to navigate between:
- **Overview**
- **Dashboard**
""")
