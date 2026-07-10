"""Feature engineering shared by train_model.py and predict.py.

Mirrors the preprocessing pipeline from the Task 1 notebook so that the
model sees identical inputs at training time and at prediction time:

- hourly grid with time-based interpolation for missing values
- lagged loads (1h, 24h, 168h)
- moving averages of the load (24h, 168h), shifted by one hour so they
  only ever use information available before the hour being predicted
- cyclical calendar encodings (hour of day, day of week, month)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TARGET = "total_load_actual"

LAG_HOURS: list[int] = [1, 24, 168]

MA_WINDOWS: list[int] = [24, 168]

FEATURES: list[str] = [
    "load_lag1",
    "load_lag24",
    "load_lag168",
    "load_ma24",
    "load_ma168",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",
]

MIN_HISTORY_HOURS: int = max(max(LAG_HOURS), max(MA_WINDOWS))


def to_hourly_series(load: pd.Series) -> pd.Series:
    """Sort onto a strict hourly grid and interpolate any gaps.

    Uses the same missing-value strategy as the Task 1 notebook:
    time-weighted interpolation in both directions.
    """
    hourly = load.sort_index().resample("1h").mean()

    return hourly.interpolate(method="time", limit_direction="both")


def build_feature_frame(load: pd.Series) -> pd.DataFrame:
    """Turn an hourly load series into a model-ready feature frame.

    The input index must be a tz-aware hourly DatetimeIndex. The value
    for the final timestamp may be NaN: its feature row is still fully
    populated from earlier hours, which is exactly what predict.py
    needs to score the next, not yet observed, hour.
    """
    frame = load.to_frame(TARGET)

    for lag in LAG_HOURS:
        frame[f"load_lag{lag}"] = frame[TARGET].shift(lag)

    for window in MA_WINDOWS:
        frame[f"load_ma{window}"] = frame[TARGET].shift(1).rolling(window).mean()

    index = frame.index

    frame["is_weekend"] = (index.dayofweek >= 5).astype(int)

    frame["hour_sin"] = np.sin(2 * np.pi * index.hour / 24)

    frame["hour_cos"] = np.cos(2 * np.pi * index.hour / 24)

    frame["dow_sin"] = np.sin(2 * np.pi * index.dayofweek / 7)

    frame["dow_cos"] = np.cos(2 * np.pi * index.dayofweek / 7)

    frame["month_sin"] = np.sin(2 * np.pi * index.month / 12)

    frame["month_cos"] = np.cos(2 * np.pi * index.month / 12)

    return frame
