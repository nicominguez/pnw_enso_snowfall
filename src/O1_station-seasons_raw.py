from pathlib import Path
import json
import requests
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
URL_LAND = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
URL_OCEAN = "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.csv"
ZONES_PATH = ROOT / "data/geography/huc6_names.csv"
OUT_PATH = ROOT / "data/O1_station-seasons_raw.csv"
CONFIG_PATH = ROOT / "config" / "station-year_filter.json"

config = json.loads((CONFIG_PATH).read_text())


# Define season months, e.g. start=12, end=4 -> [12, 1, 2, 3, 4]
ms, me = int(config["month_range"]["start"]), int(config["month_range"]["end"])
months = [(m - 1) % 12 + 1 for m in range(ms, ms + (me - ms) % 12 + 1)]


def seasonal(df):
    df = df[df["date"].dt.month.isin(months)]
    return df.assign(season=df["date"].dt.year + (df["date"].dt.month >= ms))


# Obtain SNOTEL (SNTL) stations within HUC2 17 and elevation range in meters.
st = pd.DataFrame(
    requests.get(
        f"{URL_LAND}/stations", 
        params={
            "stationTriplets": "*:*:SNTL",
            "hucs": "17*",
            "activeOnly": "false"}
        ).json()
    )
st = st.rename(columns={"stationTriplet": "station_id", "name": "station_name", "elevation": "elevation_m"})
st["huc6"] = st["huc"].str[:6]
st["elevation_m"] *= 0.3048
st = st[st["elevation_m"].between(config["elevation_m"]["min"], config["elevation_m"]["max"])]


# Pull station-months and keep selected months.
ids = st["station_id"].tolist()
response = requests.get(
    f"{URL_LAND}/data",
    params={
        "stationTriplets": ",".join(ids),
        "elements": ",".join(config["keep_elements"]),
        "duration": "MONTHLY",
        "beginDate": config["date_range"]["start"],
        "endDate": config["date_range"]["end"],
        "periodRef": "START"
    },
).json()

rows = []
for station in response:
    for element in station.get("data", []):
        code = element["stationElement"]["elementCode"]
        for value in element.get("values", []):
            rows.append({
                "station_id": station["stationTriplet"],
                "element": code,
                "date": f'{value["year"]}-{int(value["month"]):02d}-01',
                "value": value.get("value")
            })
raw = pd.DataFrame(rows)
raw["date"] = pd.to_datetime(raw["date"])
raw = seasonal(raw)


# Aggregate station data to seasons.
seasons = (
    raw.pivot(index=["station_id", "season", "date"], columns="element", values="value")
    .groupby(["station_id", "season"])
    .agg(
        TAVG=("TAVG", "mean"), n_TAVG=("TAVG", "count"),
        PRCP=("PRCP", lambda s: s.sum(min_count=1)), n_PRCP=("PRCP", "count"),
        SWE=("WTEQ", "max"), n_SWE=("WTEQ", "count")
    )
    .reset_index()
)


# Add station metadata and zone.
out = (seasons.merge(st[["station_id", "station_name", "latitude", "longitude", "elevation_m", "huc6"]], on="station_id")
              .merge(pd.read_csv(ZONES_PATH, dtype=str), on="huc6", how="left"))


# Aggregate seasonal Niño 3.4 anomalies (ENSO).
enso = pd.read_csv(URL_OCEAN, skiprows=1, names=["date", "nino34"], parse_dates=["date"], skipinitialspace=True)
enso = seasonal(enso[enso["nino34"] > -99]).groupby("season")["nino34"].agg(enso="mean", n_enso="count").reset_index()
out = out.merge(enso, on="season", how="left").sort_values(["station_id", "season"])


# Export.
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_PATH, index=False)