import streamlit as st
from load_data import load_data

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="IRC Dashboard",
    layout="wide",
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
df, last_updated = load_data()

# ---------------------------------------------------------
# MAIN APP HEADER
# ---------------------------------------------------------
st.markdown("# IRC Utility Dashboard")
st.markdown(f"**Last Updated:** {last_updated}")
st.write("")

# ---------------------------------------------------------
# SIMPLE HOME PAGE CONTENT
# ---------------------------------------------------------
st.markdown("### Welcome")
st.write(
    """
    Use the sidebar to navigate between:
    - **Overview** (KPIs + monthly trends)
    - **Dashboard** (filters, charts, raw data)
    """
)

# Show a preview of the data
if df.empty:
    st.warning("No data available.")
else:
    st.write("### Data Preview")
    st.dataframe(df.head(), use_container_width=True)
