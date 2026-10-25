from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
df = pd.read_csv(ROOT / "data" / "O2_station-seasons_clean.csv")
seasons = df.drop_duplicates("season")
stations = df.drop_duplicates("station_id")

fig, axes = plt.subplots(2, 2, figsize=(10, 7))

zone_counts = stations["zone_name"].value_counts().sort_values()
axes[0, 0].barh(zone_counts.index, zone_counts.values, color="#8ecae6")
axes[0, 0].set(xlabel="Estaciones", ylabel="Zona")

axes[0, 1].hist(stations["elevation_m"].dropna(), bins=15, color="#90be6d")
axes[0, 1].set(xlabel="Elevación (m)", ylabel="Estaciones")

axes[1, 0].hist(seasons["enso"].dropna(), bins=12, color="#f4a261")
axes[1, 0].set(xlabel="ENSO por temporada", ylabel="Temporadas")

axes[1, 1].hist(np.log1p(df["SWE"].dropna()), bins=20, color="#e76f51")
axes[1, 1].set(xlabel=r"$\log(1+\mathrm{SWE})$",
                ylabel="Estaciones-temporadas")

fig.tight_layout()
fig.savefig(ROOT / "images" / "objective2_distributions.png", dpi=300)
