"""Task 4: end-to-end next-hour demand forecast.

Consolidates the previous tasks into a single script:

1. fetches recent demand history from the Task 3 API
   (GET /postgres/latest and GET /postgres/range)
2. preprocesses it with the same pipeline as the Task 1 notebook
   (hourly grid, interpolation, lags, moving averages, calendar)
3. loads the trained model saved by train_model.py
4. prints a forecast for the hour after the latest record

Usage:
    python prediction/predict.py
    python prediction/predict.py --api-url https://your-deployment.onrender.com
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import requests

from features import FEATURES, MIN_HISTORY_HOURS, build_feature_frame, to_hourly_series

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / "models" / "demand_model.joblib"

DEFAULT_API_URL = "http://localhost:8000"
HISTORY_HOURS = MIN_HISTORY_HOURS + 48
REQUEST_TIMEOUT_SECONDS = 30


def get_json(url: str, params: dict[str, str] | None = None) -> Any:
    """GET a JSON payload, failing loudly on HTTP or connection errors."""
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)

    response.raise_for_status()

    return response.json()


def fetch_history(api_url: str) -> pd.Series:
    """Pull enough hourly history from the API to build every feature.

    Uses the two required time-series endpoints: /latest to anchor the
    window, then /range to fetch the preceding week plus a safety margin.
    """
    latest = get_json(f"{api_url}/postgres/latest")

    latest_ts = pd.Timestamp(latest["ts"])

    start_ts = latest_ts - pd.Timedelta(hours=HISTORY_HOURS)

    records = get_json(
        f"{api_url}/postgres/range",
        params={"start_date": start_ts.isoformat(), "end_date": latest_ts.isoformat()},
    )

    if len(records) <= MIN_HISTORY_HOURS:
        sys.exit(
            f"Not enough history: got {len(records)} records, "
            f"need more than {MIN_HISTORY_HOURS} to build the lag features."
        )

    frame = pd.DataFrame(records)

    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)

    load = frame.set_index("ts")["total_load_actual"].astype(float)

    return to_hourly_series(load)


def load_model_artifact() -> dict[str, Any]:
    """Load the persisted model plus its training metadata."""
    if not MODEL_PATH.exists():
        sys.exit(
            f"Model artifact not found at {MODEL_PATH}. "
            "Run 'python prediction/train_model.py' first."
        )

    return joblib.load(MODEL_PATH)


def forecast_next_hour(
    load: pd.Series, artifact: dict[str, Any]
) -> tuple[pd.Timestamp, float]:
    """Score the hour after the latest observation.

    Appends an empty row for the next hour so the shared feature
    builder fills its lags and moving averages from known history only.
    """
    next_ts = load.index[-1] + pd.Timedelta(hours=1)

    extended = load.reindex(load.index.append(pd.DatetimeIndex([next_ts])))

    feature_row = build_feature_frame(extended)[FEATURES].iloc[[-1]]

    if feature_row.isna().any(axis=None):
        sys.exit("Feature row has missing values, the fetched history is too short.")

    prediction = float(artifact["model"].predict(feature_row)[0])

    return next_ts, prediction


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Forecast next-hour electricity demand."
    )

    parser.add_argument(
        "--api-url", default=DEFAULT_API_URL, help="Base URL of the Task 3 API"
    )

    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")

    print(f"Fetching demand history from {api_url} ...")

    load = fetch_history(api_url)

    print(
        f"Received {len(load):,} hourly records "
        f"({load.index.min():%Y-%m-%d %H:%M} to {load.index.max():%Y-%m-%d %H:%M} UTC)"
    )

    artifact = load_model_artifact()

    print(
        f"Loaded model trained at {artifact['trained_at']} "
        f"(holdout MAE {artifact['holdout_metrics']['MAE']} MW)"
    )

    next_ts, prediction = forecast_next_hour(load, artifact)

    print("\n")

    print(
        f"Latest actual load : {load.iloc[-1]:>10,.2f} MW at {load.index[-1]:%Y-%m-%d %H:%M} UTC"
    )

    print(
        f"Forecast next hour : {prediction:>10,.2f} MW for {next_ts:%Y-%m-%d %H:%M} UTC"
    )


if __name__ == "__main__":
    main()
