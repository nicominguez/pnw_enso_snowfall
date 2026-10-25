from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
df = pd.read_csv(ROOT / "data/O2_station-seasons_clean.csv")

df = df[df["station_id"] == "788:WA:SNTL"]

colors = df["enso"].map(lambda x: "red" if x >= 1 else "blue" if x <= -1 else "gray")

fig, ax = plt.subplots()
ax.grid()
ax.scatter(df["season"], df["SWE"], s=25, c=colors, alpha=0.5)
ax.set_xlabel("Season")
ax.set_ylabel("SWE")
ax.legend(handles=[
    ax.scatter([], [], s=25, alpha=0.5, marker="o", color="red", label="El Niño"),
    ax.scatter([], [], s=25, alpha=0.5, marker="o", color="blue", label="La Niña"),
    ax.scatter([], [], s=25, alpha=0.5, marker="o", color="gray", label="Neutral")
])
ax.legend()
plt.savefig(ROOT / "images" / "year_enso_vs_swe.png")
plt.show()
