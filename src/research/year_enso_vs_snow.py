from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
df = pd.read_csv(ROOT / "data/station-seasons_land_zone_ocean.csv")

df0 = (
    df[df["station_id"] == "USC00049053"]
    .groupby("season")
    .agg(
        enso=("enso", "mean"), 
        snow=("SNOW", "sum")
    )
    .reset_index()
)

colors = df0["enso"].map(lambda x: "red" if x >= 1 else "blue" if x <= -1 else "gray")

fig, ax = plt.subplots()
ax.scatter(df0["season"], df0["snow"], c=colors)
ax.set_xlabel("Season")
ax.set_ylabel("SWE")
plt.show()
