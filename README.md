# Electricity Demand Prediction: A Time Series Pipeline

This project predicts Spain's national electricity demand one hour ahead. It covers the whole chain: exploratory analysis and modelling in a notebook, the same data modelled in both PostgreSQL and MongoDB, a FastAPI service on top of both databases, and a script that pulls history from the API and produces a forecast.

## Problem and Dataset

Grid operators have to anticipate demand to schedule generation, since too little supply causes shortfalls and too much wastes money. We predict the next hour of Spain's total electricity load from its recent history and calendar context.

Dataset: [Hourly energy demand, generation, prices and weather](https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather) (Kaggle)

- 35,064 hourly records from 2015-01-01 to 2018-12-31 (UTC)
- Target: `total load actual` (MW)
- Covariates: generation by source, day-ahead and actual prices, and weather observations for 5 Spanish cities

## Repository Structure

```
├── notebook/
│   └── electricity-demand-prediction.ipynb   Task 1: EDA, analytical questions, model experiments
├── database/
│   ├── sql/            Task 2: PostgreSQL schema, loader, queries
│   ├── mongodb/        Task 2: MongoDB loader and queries
│   ├── common/         Shared config and cleaning helpers
│   └── run_all.py      Loads both databases end to end
├── api/                Task 3: FastAPI CRUD + time-series endpoints
├── prediction/         Task 4: training and forecast scripts
│   ├── features.py     Feature engineering shared by both scripts
│   ├── train_model.py  Trains and saves the tuned model
│   └── predict.py      Fetches from the API and forecasts the next hour
├── models/             Saved model artifact (joblib)
├── energy_dataset.csv
└── weather_features.csv
```

## Setup

```bash
git clone https://github.com/ai-ngabo/electricity-demand-prediction.git
cd electricity-demand-prediction
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your PostgreSQL and MongoDB credentials
```

## Task 1: EDA and Modelling

The [notebook](notebook/electricity-demand-prediction.ipynb) cleans both datasets (time-based interpolation for gaps, outlier removal on pressure and wind speed), answers 6 analytical questions with visualizations (trend, seasonality, temperature effects, lag autocorrelation, moving averages, renewables vs price), then runs 8 forecasting experiments with hyperparameter tuning:

| Experiment | MAE (MW) | RMSE | MAPE % | R² |
|---|---|---|---|---|
| Persistence baseline (lag 1) | 1076.0 | 1438.0 | 3.78 | 0.9034 |
| Linear Regression | 861.3 | 1144.6 | 2.96 | 0.9388 |
| Ridge (tuned) | 861.3 | 1144.6 | 2.96 | 0.9388 |
| KNN (tuned) | 915.1 | 1326.1 | 3.18 | 0.9179 |
| Random Forest (tuned) | 368.0 | 590.0 | 1.28 | 0.9837 |
| HistGradientBoosting (tuned) | 361.1 | 572.0 | 1.25 | 0.9847 |
| MLP dense NN | 517.4 | 740.9 | 1.81 | 0.9744 |
| LSTM (24h sequence) | 332.8 | 566.9 | 1.16 | 0.9850 |

Models train on 2015-2017 and are evaluated on a held-out 2018.

## Task 2: Databases

PostgreSQL schema (5 tables: `cities`, `generation_sources`, `energy_demand`, `energy_generation`, `weather_observations`) lives in [database/sql/schema.sql](database/sql/schema.sql). MongoDB stores one document per hour in `hourly_records` with nested `demand`, `generation`, and `weather` subdocuments.

```bash
python database/run_all.py        # create schema and load both databases
python database/sql/run_queries.py
python database/mongodb/run_queries.py
```

Or with Docker: `docker compose up --build`

## Task 3: API

```bash
uvicorn api.main:app --reload     # interactive docs at http://localhost:8000/docs
```

A live instance is deployed at https://electricity-demand-prediction.onrender.com (free tier, so the first request after a while is slow while it wakes up).

Full CRUD for both databases, plus the required time-series queries:

| Endpoint | Description |
|---|---|
| `GET /postgres/latest`, `GET /mongodb/latest` | Latest record |
| `GET /postgres/range`, `GET /mongodb/range` | Records by date range |
| `GET/POST /postgres/records`, `GET/POST /mongodb/records` | List and create |
| `GET/PUT/PATCH/DELETE .../records/{id}` | Read, update, delete one record |

## Task 4: Forecast Script

`prediction/train_model.py` reproduces the winning tabular experiment (tuned HistGradientBoostingRegressor) on lagged loads, moving averages, and cyclical calendar features, and saves it to `models/demand_model.joblib`. Retrained without the temperature feature (the API serves no weather for this path) it scores MAE 363.7 MW, R² 0.9845 on the 2018 holdout, within 3 MW of the notebook result.

`prediction/predict.py` runs the full pipeline: fetch history from the API, preprocess exactly as in Task 1, load the saved model, forecast the next hour.

```bash
python prediction/train_model.py                 # one-time, artifact is also committed
python prediction/predict.py                     # against a local API
python prediction/predict.py --api-url https://electricity-demand-prediction.onrender.com
```

Sample output from the deployed API:

```
Fetching demand history from https://electricity-demand-prediction.onrender.com ...
Received 217 hourly records (2018-12-22 22:00 to 2018-12-31 22:00 UTC)
Loaded model trained at 2026-07-09 (holdout MAE 363.7 MW)

Latest actual load :  24,455.00 MW at 2018-12-31 22:00 UTC
Forecast next hour :  23,305.10 MW for 2018-12-31 23:00 UTC
```

## Team

| Member | Major components |
|---|---|
| Alain Ngbao | Task 1: notebook, EDA, and model experiments |
| James Mukunzi | Task 3: API CRUD endpoints |
| Silver JR Nshuti | Task 2: databases, deployment |
| Michael Nwuju | Task 4: forecast script, project report |
