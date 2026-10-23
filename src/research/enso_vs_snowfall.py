from pathlib import Path
import pandas as pd
import numpy as np
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

fit = df0[["enso", "SNOW"]].dropna()
m, b = np.polyfit(fit["enso"], fit["snow"], 1)
r = fit["enso"].corr(fit["snow"])


fig, ax = plt.subplots()
ax.scatter(df0["enso"], df0["snow"])
ax.axvline(x=0, color="gray", linestyle="--")
ax.set_xlabel("Mean ENSO Index")
ax.set_ylabel("Yearly snowfall")

ax.plot(fit["enso"], m * fit["enso"] + b, color="red")
ax.text(0.05, 0.95, f"Pearson r = {r:.2f}", transform=ax.transAxes, va="top")

plt.show()