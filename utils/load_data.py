import pandas as pd
import streamlit as st
import io
import requests
from datetime import datetime

@st.cache_data(ttl=60)
def load_data():
    # Google Sheets file ID
    file_id = "1_4coHOmEkzY9cLYRtqmnUJ51LuqeY6yz"

    # Direct Excel export link
    download_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

    # Google Drive metadata (for last updated timestamp)
    metadata_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=modifiedTime&key=AIzaSyDUMMYKEY"

    try:
        # ---- Get Last Updated Timestamp ----
        meta = requests.get(metadata_url, timeout=10).json()
        raw_time = meta.get("modifiedTime", None)

        if raw_time:
            last_updated = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            last_updated_str = last_updated.strftime("%B %d, %Y at %I:%M %p")
        else:
            last_updated_str = "Unknown"

        # ---- Download Excel File ----
        r = requests.get(download_url, timeout=10)

        if r.text.startswith("<"):
            st.error("❌ Google Sheets returned HTML instead of Excel. Make sure sharing is set to 'Anyone with the link can view'.")
            return pd.DataFrame(), last_updated_str

        df = pd.read_excel(
            io.BytesIO(r.content),
            sheet_name="Property",
            engine="openpyxl"
        )

        # ---- Clean Columns ----
        df.columns = df.columns.str.strip()

        # Convert dates
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

        return df, last_updated_str

    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        return pd.DataFrame(), "Unknown"
