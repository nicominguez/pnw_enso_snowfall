from pathlib import Path
import json
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "O1_station-seasons_raw.csv"
CONFIG_PATH = ROOT / "config" / "station-year_filter.json"

df = pd.read_csv(DATA)
config = json.loads(CONFIG_PATH.read_text())


# Retain stations with enough SWE completion.
df = df[df["n_SWE"] == 5]


# Retain stations with enough seasons.
stations = (
    df.groupby("station_id")["season"]
    .nunique()
    .loc[lambda x: x >= config["minimum_station_seasons"]]
    .index
)
df = df[df["station_id"].isin(stations)].sort_values(["station_id", "season"])


# Export.
df.to_csv(ROOT / "data" / "O2_station-seasons_clean.csv", index=False)