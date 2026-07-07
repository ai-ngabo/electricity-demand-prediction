from __future__ import annotations

import numpy as np
import pandas as pd

from config import ENERGY_CSV, WEATHER_CSV, GENERATION_SOURCES


def _load_energy_raw() -> pd.DataFrame:
    df = pd.read_csv(ENERGY_CSV)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time").sort_index()
    return df


def clean_energy_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = _load_energy_raw()

    keep_cols = list(GENERATION_SOURCES.keys()) + [
        "total load actual",
        "price actual",
        "price day ahead",
    ]
    df = raw[keep_cols].copy()
    df = df.interpolate(method="time", limit_direction="both")

    demand = df[["total load actual", "price actual", "price day ahead"]].rename(
        columns={
            "total load actual": "total_load_actual",
            "price actual": "price_actual",
            "price day ahead": "price_day_ahead",
        }
    )

    rename_gen = {raw_col: name for raw_col, (name, _) in GENERATION_SOURCES.items()}
    generation = df[list(GENERATION_SOURCES.keys())].rename(columns=rename_gen)
    generation_long = (
        generation.reset_index()
        .melt(id_vars="time", var_name="source_name", value_name="generation_mw")
        .rename(columns={"time": "ts"})
    )

    demand = demand.reset_index().rename(columns={"time": "ts"})
    return demand, generation_long


def clean_weather_frame() -> pd.DataFrame:
    df = pd.read_csv(WEATHER_CSV)
    df["time"] = pd.to_datetime(df["dt_iso"], utc=True)

    cols = ["time", "city_name", "temp", "pressure", "humidity", "wind_speed", "clouds_all"]
    df = df[cols].copy()
    df["city_name"] = df["city_name"].str.strip()
    df = df.drop_duplicates(subset=["time", "city_name"], keep="first")

    df.loc[df["pressure"] > 1051, "pressure"] = np.nan
    df.loc[df["pressure"] < 931, "pressure"] = np.nan
    df.loc[df["wind_speed"] > 50, "wind_speed"] = np.nan

    df = df.sort_values(["city_name", "time"])
    num_cols = ["temp", "pressure", "humidity", "wind_speed", "clouds_all"]

    def _interp(g):
        g = g.set_index("time")
        g[num_cols] = g[num_cols].interpolate(method="time", limit_direction="both")
        return g.reset_index()

    df = df.groupby("city_name", group_keys=False)[df.columns].apply(_interp)
    df["temp"] = (df["temp"] - 273.15).round(2)
    df = df.rename(columns={"time": "ts"})
    return df[["ts", "city_name", "temp", "pressure", "humidity", "wind_speed", "clouds_all"]]


if __name__ == "__main__":
    demand, generation = clean_energy_frames()
    weather = clean_weather_frame()
    print("demand      :", demand.shape)
    print("generation  :", generation.shape)
    print("weather     :", weather.shape)
