import pandas as pd
from pathlib import Path

def load_property_ledger():
    data_folder = Path("data")

    excel_files = list(data_folder.glob("*.xlsx"))
    if not excel_files:
        return None, None

    newest_file = max(excel_files, key=lambda f: f.stat().st_mtime)

    df = pd.read_excel(newest_file, sheet_name="Raw Data")

    # -----------------------------
    # CORE CLEANUP
    # -----------------------------
    if "Billing Date" in df.columns:
        df["Billing Date"] = pd.to_datetime(df["Billing Date"], errors="coerce")

    # Ensure Year / Month exist
    if "Year" not in df.columns and "Billing Date" in df.columns:
        df["Year"] = df["Billing Date"].dt.year

    if "Month" not in df.columns and "Billing Date" in df.columns:
        df["Month"] = df["Billing Date"].dt.month_name()

    if "Billing Date" in df.columns:
        df["Month_Num"] = df["Billing Date"].dt.month
    else:
        df["Month_Num"] = pd.NA

    # -----------------------------
    # DERIVED METRICS
    # -----------------------------
    if "Usage" in df.columns and "$ Amount" in df.columns:
        df["Cost_per_Unit"] = df["$ Amount"] / df["Usage"].replace(0, pd.NA)

    if "Occupied Rooms" in df.columns and "$ Amount" in df.columns:
        df["CPOR"] = df["$ Amount"] / df["Occupied Rooms"].replace(0, pd.NA)

    if "# Units" in df.columns and "$ Amount" in df.columns:
        df["CPAR"] = df["$ Amount"] / df["# Units"].replace(0, pd.NA)

    if "Usage" in df.columns and "Occupied Rooms" in df.columns:
        df["Usage_per_Occupied_Room"] = df["Usage"] / df["Occupied Rooms"].replace(0, pd.NA)

    if "Usage" in df.columns and "# Units" in df.columns:
        df["Usage_per_Available_Room"] = df["Usage"] / df["# Units"].replace(0, pd.NA)

    month_order = (
        sorted(df["Month_Num"].dropna().unique())
        if "Month_Num" in df.columns
        else None
    )

    return df, month_order
