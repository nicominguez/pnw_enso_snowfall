from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
df = pd.read_csv(ROOT / "data/station-seasons_land_zone_ocean.csv")

df = df[df["station_id"] == "CAN01133270"]

fit = df[["enso", "SNOW"]].dropna()
m, b = np.polyfit(fit["enso"], fit["SNOW"], 1)
r = fit["enso"].corr(fit["SNOW"])


fig, ax = plt.subplots()
ax.scatter(df["enso"], df["SNOW"], s=25, alpha=0.5)
ax.axvline(x=0, color="gray", linestyle="--")
ax.set_xlabel("Mean ENSO Index")
ax.set_ylabel("SNOW")

ax.plot(fit["enso"], m * fit["enso"] + b, color="red")
ax.text(0.05, 0.95, f"Pearson r = {r:.2f}", transform=ax.transAxes, va="top")

plt.show()