from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
df = pd.read_csv(ROOT / "data" / "O2_station-seasons_clean.csv")
df = df.dropna(subset=["station_id", "enso", "SWE", "zone_name"]).copy()
df["SWE"] = np.log1p(df["SWE"])
df["SWE"] = (df["SWE"] - df["SWE"].mean()) / df["SWE"].std()
df["enso"] = (df["enso"] - df["enso"].mean()) / df["enso"].std()

df = (
    df.groupby(["zone_name", "station_id", "enso"])["SWE"]
      .mean()
      .groupby(["zone_name", "enso"])
      .mean()
      .reset_index()
)

colors = dict(zip(
    df["zone_name"].unique(),
    plt.colormaps["Set3"](
        np.linspace(0, 1, df["zone_name"].nunique())
    ),
))

fig, ax = plt.subplots()

for zone, group in df.groupby("zone_name"):
    m, _ = np.polyfit(group["enso"], group["SWE"], 1)
    x = np.array([group["enso"].min(), group["enso"].max()])
    ax.plot(x, m * x, color=colors[zone], label=zone)

ax.axvline(0, color="gray", ls="--")
ax.axhline(0, color="gray", ls="--")
ax.set(xlabel="ENSO", ylabel="Standardized mean SWE")
ax.legend(title="Zone", fontsize=8, title_fontsize=9)

ax.legend(
    title="Zone",
    fontsize=8,
    title_fontsize=9,
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    borderaxespad=0,
)

plt.tight_layout()
plt.savefig(
    ROOT / "images" / "enso_vs_swe_by_zone.png",
    dpi=300,
    bbox_inches="tight",
)