import streamlit as st
import pandas as pd

from components.property_summary import render_property_summary


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # Replace with your actual data source
    return pd.read_csv("data/utility_data.csv")


# ---------------------------------------------------------
# Page Layout
# ---------------------------------------------------------
st.title("Property Detail")

df = load_data()

# Ensure Billing Date is datetime
df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

# Property selector
properties = sorted(df["Property Name"].dropna().unique())
selected_property = st.selectbox("Select Property", properties)


# ---------------------------------------------------------
# Render Summary Component
# ---------------------------------------------------------
if selected_property:
    render_property_summary(df, selected_property)
else:
    st.info("Please select a property to view details.")
