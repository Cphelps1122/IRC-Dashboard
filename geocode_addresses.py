import pandas as pd
import requests
import time
import os

df = pd.read_excel("data/mcneill.xlsx", sheet_name="Raw Data")
df.columns = df.columns.str.strip()

df["full_address"] = (
    df["Property Name"].astype(str)
    + ", "
    + df["City"].astype(str)
    + ", "
    + df["State"].astype(str)
    + " "
    + df["ZIP Code"].astype(str)
)

CACHE_PATH = "data/geocode_cache.csv"

if os.path.exists(CACHE_PATH):
    cache = pd.read_csv(CACHE_PATH)
else:
    cache = pd.DataFrame(columns=["full_address", "Latitude", "Longitude"])

already = set(cache["full_address"])
to_geo = [a for a in df["full_address"].unique() if a not in already]

print("Need to geocode:", len(to_geo))

def geocode(addr):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": addr, "format": "json", "limit": 1}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=10,
                             headers={"User-Agent": "batch-geocoder"})
            r.raise_for_status()
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except:
            time.sleep(2)
    return None, None

new_rows = []
for addr in to_geo:
    lat, lon = geocode(addr)
    print("Geocoded:", addr, lat, lon)
    new_rows.append({"full_address": addr, "Latitude": lat, "Longitude": lon})
    time.sleep(1)

cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
cache.to_csv(CACHE_PATH, index=False)

print("DONE")
