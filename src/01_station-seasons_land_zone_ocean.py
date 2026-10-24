from pathlib import Path
import json
import pandas as pd
import requests
import requests
for el in ["TAVG", "PRCP", "WTEQ"]:
    for sid in ["770:ID:SNTL", "985:WA:SNTL"]:
        r = requests.get("https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data",
                         params=dict(stationTriplets=sid, elements=el, duration="MONTHLY",
                                     beginDate="1981-01-01", endDate="1983-12-31"))
        print(el, sid, r.status_code, r.text[:300])

ROOT = Path(__file__).resolve().parent.parent
URL_LAND = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
URL_OCEAN = "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.csv"
ZONES_PATH = ROOT / "data/geography/huc6_names.csv"
OUT_PATH = ROOT / "data/station-seasons_land_zone_ocean.csv"
config = json.loads((ROOT / "config/station-year_filter.json").read_text())


def get(path, **params):
    r = requests.get(f"{URL_LAND}/{path}", params=params, timeout=120)
    if not r.ok:
        raise RuntimeError(
            f"AWDB request failed: HTTP {r.status_code}\n"
            f"URL: {r.url}\n"
            f"Response: {r.text[:1000]}"
        )
    return r.json()


# Stations inside HUC2 17 and elevation range in meters.
st = pd.DataFrame(get("stations", stationTriplets="*:*:SNTL", hucs="17*", activeOnly="false"))
st = st.rename(columns={"stationTriplet": "station_id", "name": "station_name", "elevation": "elevation_m"})
st["elevation_m"] *= 0.3048
st = st[st["elevation_m"].between(config["elevation_m"]["min"], config["elevation_m"]["max"])]
st["huc6"] = st["huc"].str[:6]
ids = st["station_id"].tolist()


# Season months, e.g. start=11, end=3 -> [11, 12, 1, 2, 3]. Months >= start belong to the following year's season.
ms, me = int(config["month_range"]["start"]), int(config["month_range"]["end"])
months = [(m - 1) % 12 + 1 for m in range(ms, ms + (me - ms) % 12 + 1)]


def seasonal(df):
    df = df[df["date"].dt.month.isin(months)]
    return df.assign(season=df["date"].dt.year + (df["date"].dt.month >= ms))


# Pull station-months and keep selected months.
rows = []

for i in range(0, len(ids), 10):
    response = get(
        "data",
        stationTriplets=",".join(ids[i:i + 10]),
        elements="TAVG,PRCP,WTEQ",
        duration="MONTHLY",
        beginDate=config["date_range"]["start"],
        endDate=config["date_range"]["end"],
        periodRef="END",
        returnFlags="false",
    )

    for station in response:
        for element_data in station.get("data", []):
            element = element_data["stationElement"]["elementCode"]

            for value in element_data.get("values", []):
                if "date" in value:
                    date = value["date"]
                else:
                    date = f'{value["year"]}-{int(value["month"]):02d}-01'

                rows.append({
                    "station_id": station["stationTriplet"],
                    "element": element,
                    "date": date,
                    "value": value.get("value"),
                })

raw = pd.DataFrame(rows)
raw["date"] = pd.to_datetime(raw["date"])
raw = seasonal(raw)


# Aggregate to seasons.
seasons = (raw.pivot(index=["station_id", "season", "date"], columns="element", values="value")
              .groupby(["station_id", "season"])
              .agg(TAVG=("TAVG", "mean"), n_TAVG=("TAVG", "count"),
                   PRCP=("PRCP", lambda s: s.sum(min_count=1)), n_PRCP=("PRCP", "count"),
                   SWE=("WTEQ", "max"), n_SWE=("WTEQ", "count"))
              .reset_index())
seasons["TAVG"] = (seasons["TAVG"] - 32) / 1.8
seasons[["PRCP", "SWE"]] *= 25.4


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