from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
df = pd.read_csv(ROOT / "data" / "O2_station-seasons_clean.csv")
df = df.dropna(subset=["station_id", "enso", "SWE", "elevation_m"])

bins = [0, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500,
        2750, 3000, 3250, 3500, 3750, 4000, np.inf]

labels = [
    "<500 m", "500–750 m", "750–1000 m", "1000–1250 m",
    "1250–1500 m", "1500–1750 m", "1750–2000 m", "2000–2250 m",
    "2250–2500 m", "2500–2750 m", "2750–3000 m", "3000–3250 m",
    "3250–3500 m", "3500–3750 m", "3750–4000 m", ">4000 m",
]

df["elevation_band"] = pd.cut(
    df["elevation_m"],
    bins=bins,
    labels=labels,
    right=False,
)

df = (
    df.groupby(["elevation_band", "station_id", "enso"], observed=True)["SWE"]
      .mean()
      .groupby(["elevation_band", "enso"], observed=True)
      .mean()
      .reset_index()
)

colors = dict(zip(
    df["elevation_band"].unique(),
    plt.colormaps["BrBG"](np.linspace(.2, .8, df["elevation_band"].nunique())),
))

fig, ax = plt.subplots()

for band, group in df.groupby("elevation_band", observed=True):
    m, _ = np.polyfit(group["enso"], group["SWE"], 1)
    x = np.array([group["enso"].min(), group["enso"].max()])
    ax.plot(x, m * x, color=colors[band], label=band)

ax.axvline(0, color="gray", ls="--")
ax.axhline(0, color="gray", ls="--")
ax.set(xlabel="ENSO", ylabel="Standardized mean SWE")

x = max(abs(np.array(ax.get_xlim())))
y = max(abs(np.array(ax.get_ylim())))
ax.set_xlim(-x, x)
ax.set_ylim(-y, y)

ax.legend(title="Elevation", fontsize=8, title_fontsize=9)

plt.tight_layout()
plt.savefig(ROOT / "images" / "enso_vs_swe_by_elevation.png", dpi=300)
plt.show()