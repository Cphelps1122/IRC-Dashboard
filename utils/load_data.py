import pandas as pd
import streamlit as st
import io
import requests

@st.cache_data(ttl=60)
def load_data():
    # ---------------------------------------------------------
    # GOOGLE SHEETS FILE ID FOR THIS CLIENT
    # ---------------------------------------------------------
    file_id = "1_4coHOmEkzY9cLYRtqmnUJ51LuqeY6yz"

    # Direct Excel export link
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

    try:
        # Download the Excel file
        r = requests.get(url, timeout=10)

        # If Google returns HTML instead of Excel
        if r.text.startswith("<"):
            st.error("❌ Google Sheets returned HTML instead of Excel. Make sure sharing is set to 'Anyone with the link can view'.")
            return pd.DataFrame()

        # ---------------------------------------------------------
        # LOAD THE PROPERTY TAB
        # ---------------------------------------------------------
        df = pd.read_excel(
            io.BytesIO(r.content),
            sheet_name="Property",
            engine="openpyxl"
        )

        # ---------------------------------------------------------
        # CLEAN + STANDARDIZE COLUMNS
        # ---------------------------------------------------------
        df.columns = df.columns.str.strip()

        # Convert date columns
        date_cols = ["Billing Date", "Due Date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert numeric columns
        numeric_cols = [
            "# Treatments",
            "Number Days Billed",
            "Previous Reading",
            "Current Reading",
            "Usage",
            "$ Amount"
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame()
