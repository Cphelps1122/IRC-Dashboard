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
        # LOAD THE CORRECT TAB FOR THIS CLIENT
        # ---------------------------------------------------------
        df = pd.read_excel(
            io.BytesIO(r.content),
            sheet_name="Property",   # <-- Your tab name
            engine="openpyxl"
        )

        return df

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame()
