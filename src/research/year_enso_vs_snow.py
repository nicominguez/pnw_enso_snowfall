from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
df = pd.read_csv(ROOT / "data/station-seasons_land_zone_ocean.csv")

df = df[df["station_id"] == "CAN01133270"]

colors = df["enso"].map(lambda x: "red" if x >= 1 else "blue" if x <= -1 else "gray")

fig, ax = plt.subplots()
ax.scatter(df["season"], df["SNOW"], c=colors)
ax.set_xlabel("Season")
ax.set_ylabel("SNOW")
plt.show()
