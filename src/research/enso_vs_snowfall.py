from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
df = pd.read_csv(ROOT / "data/station-seasons_land_zone_ocean.csv")

df = df[df["station_id"] == "788:WA:SNTL"]

fit = df[["enso", "SWE"]].dropna()
m, b = np.polyfit(fit["enso"], fit["SWE"], 1)
r = fit["enso"].corr(fit["SWE"])


fig, ax = plt.subplots()
ax.scatter(df["enso"], df["SWE"], s=25, c="gray", alpha=0.5)
ax.axvline(x=0, color="gray", linestyle="--")
ax.set_xlabel("ENSO")
ax.set_ylabel("SWE")

ax.plot(fit["enso"], m * fit["enso"] + b, color="red", alpha=0.5)
ax.text(0.05, 0.95, f"Pearson r = {r:.2f}", transform=ax.transAxes, va="top")

plt.savefig(ROOT / "images" / "enso_vs_swe.png")
plt.show()