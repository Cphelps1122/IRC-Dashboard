import pandas as pd
import requests
from datetime import timedelta
import streamlit as st

NOAA_TOKEN = st.secrets.get("NOAA_TOKEN", None)
BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
HEADERS = {"token": NOAA_TOKEN} if NOAA_TOKEN else {}

def fetch_weather(station_id, start_date, end_date):
    if not NOAA_TOKEN:
        return pd.DataFrame()

    params = {
        "datasetid": "GHCND",
        "stationid": station_id,
        "startdate": start_date,
        "enddate": end_date,
        "units": "standard",
        "limit": 1000
    }

    r = requests.get(BASE_URL, headers=HEADERS, params=params)
    if r.status_code != 200:
        return pd.DataFrame()

    data = r.json().get("results", [])
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df = df[df["datatype"].isin(["TMAX", "TMIN"])]
    df["date"] = pd.to_datetime(df["date"]).dt.date

    pivot = df.pivot_table(index="date", columns="datatype", values="value", aggfunc="mean")
    pivot["TAVG"] = (pivot["TMAX"] + pivot["TMIN"]) / 2
    pivot["HDD"] = (65 - pivot["TAVG"]).clip(lower=0)
    pivot["CDD"] = (pivot["TAVG"] - 65).clip(lower=0)

    return pivot.reset_index()

def add_weather_normalization(df, station_id):
    df = df.copy()
    df["HDD"] = 0.0
    df["CDD"] = 0.0

    if not NOAA_TOKEN:
        df["Usage_per_HDD"] = pd.NA
        df["Usage_per_CDD"] = pd.NA
        return df

    for idx, row in df.iterrows():
        start = row["Billing Date"] - timedelta(days=row["Number Days Billed"])
        end = row["Billing Date"]

        weather = fetch_weather(
            station_id,
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        )

        if not weather.empty:
            df.at[idx, "HDD"] = weather["HDD"].sum()
            df.at[idx, "CDD"] = weather["CDD"].sum()

    df["Usage_per_HDD"] = df["Usage"] / df["HDD"].replace(0, pd.NA)
    df["Usage_per_CDD"] = df["Usage"] / df["CDD"].replace(0, pd.NA)

    return df