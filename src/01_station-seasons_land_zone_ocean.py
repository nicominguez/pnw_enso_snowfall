"""
- Filtrar estaciones candidatas por área de estudio y rango de elevación.
- Seleccionar variables 'TAVG', 'PRCP, y 'SNOW' además de las identificativas (id, nombre, coordenadas, elevación) para cada estación-mes en fechas límite seleccionadas.
- Añadir dimensión categórica para la temporada de la estación-mes según los meses seleccionados (e.g. [11, 12, 1, 2, 3]).
- Condensar estación-mes en estación-temporada, aplicando media para 'TAVG' y suma para 'PRCP' y 'SNOW'. Añadir variables 'n_*' para juzgar completitud. Una temporada sin datos para alguna variable numérica queda como 'NaN', no 0.
- Clasificar estación-temporada por zona geográfica con dimensiones 'huc8' y 'zone_name'.
- Descargar índice mensual de anomalía Niño 3.4 desde el año 1870. Valores faltantes quedan como 'NaN', no 0.
- Añadir dimension categórica para la temporada del mes a los índices mensuales y condensarlo a media por temporada. 'n_enso' indica número de meses con enso en una temporada.
- Agregar dimensión enso a cada estación-temporada según la temporada.
"""

from pathlib import Path
from urllib.parse import urlencode
import json
import pandas as pd
import geopandas as gpd


ROOT = Path(__file__).resolve().parent.parent
STATIONS_PATH = ROOT / "inventory/stations.txt"
URL_LAND = "https://www.ncei.noaa.gov/access/services/data/v1"
URL_OCEAN = "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.csv"
ZONES_PATH = ROOT / "data/geography/wbd_huc8_simplified.json"
OUT_PATH = ROOT / "data/station-seasons_land_zone_ocean.csv"
config = json.loads((ROOT / "config/station-year_filter.json").read_text())


# Station IDs inside study area and elevation range.
area, elev = config["study_area"], config["elevation_m"]
st = pd.read_fwf(STATIONS_PATH, widths=[11, 9, 10, 7], header=None,
                 names=["station_id", "latitude", "longitude", "elevation_m"])
ids = st.loc[
    st["latitude"].between(area["latitude_min"], area["latitude_max"])
    & st["longitude"].between(area["longitude_min"], area["longitude_max"])
    & st["elevation_m"].between(elev["min"], elev["max"]),
    "station_id",
].tolist()


# Pull all available station-months.
params = {
"dataset": "global-summary-of-the-month",
"dataTypes": ",".join(config["keep_elements"]),
"startDate": config["date_range"]["start"],
"endDate": config["date_range"]["end"],
"includeStationName": "true",
"includeStationLocation": "1",
"includeAttributes": "true",
"units": "metric",
"format": "csv",
}
chunks = (",".join(ids[i:i + 100]) for i in range(0, len(ids), 100))
raw = pd.concat((pd.read_csv(f"{URL_LAND}?{urlencode({**params, 'stations': c})}", parse_dates=["DATE"])
                 for c in chunks), ignore_index=True)
raw = raw.rename(columns={"STATION": "station_id", "DATE": "date", "NAME": "station_name",
"LATITUDE": "latitude", "LONGITUDE": "longitude", "ELEVATION": "elevation_m"})


# Season months, e.g. start=11, end=3 -> [11, 12, 1, 2, 3]. Months >= start belong to the following year's season.
ms, me = int(config["month_range"]["start"]), int(config["month_range"]["end"])
months = [(m - 1) % 12 + 1 for m in range(ms, ms + (me - ms) % 12 + 1)]


# Keep selected months, aggregate to seasons.
raw = raw[raw["date"].dt.month.isin(months)]
raw["season"] = raw["date"].dt.year + (raw["date"].dt.month >= ms)
seasons = (raw.groupby(["station_id", "season"])
              .agg(station_name=("station_name", "first"), latitude=("latitude", "first"),
                   longitude=("longitude", "first"), elevation_m=("elevation_m", "first"),
                   TAVG=("TAVG", "mean"), n_TAVG=("TAVG", "count"),
                   PRCP=("PRCP", lambda s: s.sum(min_count=1)), n_PRCP=("PRCP", "count"),
                   SNOW=("SNOW", lambda s: s.sum(min_count=1)), n_SNOW=("SNOW", "count"))
              .reset_index())


# Classify stations by zone.
zones = gpd.read_file(ZONES_PATH)[["huc8", "name", "geometry"]]
zones = zones.rename(columns={"name": "zone_name"})
points = gpd.GeoDataFrame(seasons, geometry=gpd.points_from_xy(seasons["longitude"], seasons["latitude"]), crs="EPSG:4326")
out = (gpd.sjoin(points, zones.to_crs(points.crs), how="left", predicate="within")
       .drop(columns=["index_right", "geometry"]))


# Aggregate seasonal Niño 3.4 anomalies (ENSO).
enso = pd.read_csv(URL_OCEAN, skiprows=1, names=["date", "nino34"], parse_dates=["date"], skipinitialspace=True)
enso = enso[enso["date"].dt.month.isin(months)]
enso["nino34"] = enso["nino34"].where(enso["nino34"] > -99)
enso["season"] = enso["date"].dt.year + (enso["date"].dt.month >= ms)
enso = enso.groupby("season")["nino34"].agg(enso="mean", n_enso="count").reset_index()
out = out.merge(enso, on="season", how="left").sort_values(["station_id", "season"])


# Export.
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_PATH, index=False)