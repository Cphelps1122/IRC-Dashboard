import streamlit as st
import pandas as pd

# Import your Google Sheets loader from util/
from utils.load_data import load_data

# Import your summary component
from components.property_summary import render_property_summary


# ---------------------------------------------------------
# Page Layout
# ---------------------------------------------------------
st.title("Property Detail")

# Load Google Sheets data + last updated timestamp
df, last_updated = load_data()

# Ensure Billing Date is datetime
if "Billing Date" in df.columns:
    df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

# Property selector
properties = sorted(df["Property Name"].dropna().unique())
selected_property = st.selectbox("Select Property", properties)

# Last updated info
st.caption(f"Last updated: {last_updated}")

# ---------------------------------------------------------
# Render Summary Component
# ---------------------------------------------------------
if selected_property:
    render_property_summary(df, selected_property)
else:
    st.info("Please select a property to view details.")
