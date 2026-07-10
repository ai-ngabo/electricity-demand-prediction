"""Trains the demand forecasting model and saves it to models/.

Reproduces the winning tabular experiment from the Task 1 notebook,
a HistGradientBoostingRegressor tuned with time-series cross
validation, then persists the fitted model plus its metadata so that
predict.py can load a ready artifact instead of retraining.

The temperature feature from the notebook is intentionally dropped:
the API only serves demand and price data, and the notebook's feature
importance showed load_lag1 carries almost all of the signal.

Usage:
    python prediction/train_model.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

from features import FEATURES, TARGET, build_feature_frame, to_hourly_series

REPO_ROOT = Path(__file__).resolve().parents[1]

ENERGY_CSV = REPO_ROOT / "energy_dataset.csv"

MODEL_PATH = REPO_ROOT / "models" / "demand_model.joblib"

TRAIN_TEST_SPLIT = "2018-01-01"

PARAM_GRID: dict[str, list[Any]] = {
    "learning_rate": [0.05, 0.1],
    "max_iter": [300, 500],
    "max_depth": [None, 8],
}


def load_demand_series() -> pd.Series:
    """Load the raw Kaggle energy dataset and return the hourly target."""
    raw = pd.read_csv(ENERGY_CSV, usecols=["time", "total load actual"])

    raw["time"] = pd.to_datetime(raw["time"], utc=True)

    load = raw.set_index("time")["total load actual"].rename(TARGET)

    return to_hourly_series(load)


def split_train_test(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological split: 2015-2017 for training, 2018 held out."""
    frame = frame.dropna(subset=FEATURES + [TARGET])

    train = frame[frame.index < TRAIN_TEST_SPLIT]

    test = frame[frame.index >= TRAIN_TEST_SPLIT]

    return train, test


def tune_model(x_train: pd.DataFrame, y_train: pd.Series) -> GridSearchCV:
    """Grid search over the notebook's hyperparameter grid.

    TimeSeriesSplit keeps every validation fold strictly after its
    training fold, so the tuning never peeks into the future.
    """
    search = GridSearchCV(
        HistGradientBoostingRegressor(random_state=42),
        PARAM_GRID,
        cv=TimeSeriesSplit(n_splits=3),
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )

    search.fit(x_train, y_train)

    return search


def evaluate(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    """Holdout metrics matching the notebook's experiment table."""

    return {
        "MAE": round(mean_absolute_error(y_true, y_pred), 1),
        "RMSE": round(mean_squared_error(y_true, y_pred) ** 0.5, 1),
        "MAPE_%": round(float(np.abs((y_true - y_pred) / y_true).mean() * 100), 2),
        "R2": round(r2_score(y_true, y_pred), 4),
    }


def main() -> None:
    load = load_demand_series()

    print(
        f"Loaded {len(load):,} hourly records "
        f"({load.index.min():%Y-%m-%d} to {load.index.max():%Y-%m-%d})"
    )

    frame = build_feature_frame(load)

    train, test = split_train_test(frame)

    print(f"Train rows: {len(train):,} | Test rows (2018 holdout): {len(test):,}")

    print(
        "Tuning HistGradientBoostingRegressor "
        f"({len(PARAM_GRID['learning_rate']) * len(PARAM_GRID['max_iter']) * len(PARAM_GRID['max_depth'])} "
        "combinations, 3 time-series folds)..."
    )

    search = tune_model(train[FEATURES], train[TARGET])

    print(f"Best params: {search.best_params_}")

    metrics = evaluate(test[TARGET], search.predict(test[FEATURES]))

    print(f"Holdout metrics: {metrics}")

    artifact = {
        "model": search.best_estimator_,
        "features": FEATURES,
        "target": TARGET,
        "best_params": search.best_params_,
        "holdout_metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    MODEL_PATH.parent.mkdir(exist_ok=True)

    joblib.dump(artifact, MODEL_PATH)

    print(f"Saved model artifact to {MODEL_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
