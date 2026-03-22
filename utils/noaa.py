import requests
import pandas as pd
import streamlit as st
from functools import lru_cache

NOAA_BASE = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
NOAA_TOKEN = st.secrets.get("NOAA_TOKEN", None)

@lru_cache(maxsize=256)
def get_noaa_daily(zip_code, start_date, end_date):
    """Fetch NOAA daily temperature data for a ZIP code and date range."""

    if NOAA_TOKEN is None:
        return None

    params = {
        "datasetid": "GHCND",
        "locationid": f"ZIP:{zip_code}",
        "startdate": start_date,
        "enddate": end_date,
        "units": "standard",
        "limit": 1000
    }

    headers = {"token": NOAA_TOKEN}

    try:
        r = requests.get(NOAA_BASE, params=params, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception:
        return None

    data = r.json().get("results", [])
    if not data:
        return None

    df = pd.DataFrame(data)

    # NOAA uses tenths of °C for TMAX/TMIN
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    temps = df[df["datatype"].isin(["TMAX", "TMIN"])]
    if temps.empty:
        return None

    pivot = temps.pivot_table(
        index="date",
        columns="datatype",
        values="value",
        aggfunc="mean"
    )

    # Convert to Fahrenheit
    pivot["TMAX_F"] = pivot["TMAX"] * 0.18 + 32
    pivot["TMIN_F"] = pivot["TMIN"] * 0.18 + 32
    pivot["AvgTemp"] = (pivot["TMAX_F"] + pivot["TMIN_F"]) / 2

    pivot.index = pd.to_datetime(pivot.index)

    return pivot
