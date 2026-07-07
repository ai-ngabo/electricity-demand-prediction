import sys
from pathlib import Path

import pandas as pd
from pymongo import MongoClient, ASCENDING

sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))
from config import MONGODB_URI, MONGODB_DB, require
from preprocess import clean_energy_frames, clean_weather_frame

COLLECTION = "hourly_records"
BATCH = 2000


def _to_dt(ts):
    return pd.Timestamp(ts).to_pydatetime()


def build_documents():
    demand, generation = clean_energy_frames()
    weather = clean_weather_frame()

    gen_wide = generation.pivot(index="ts", columns="source_name", values="generation_mw")

    weather_by_ts = {}
    for row in weather.itertuples(index=False):
        weather_by_ts.setdefault(row.ts, []).append({
            "city": row.city_name,
            "temp": None if pd.isna(row.temp) else float(row.temp),
            "pressure": None if pd.isna(row.pressure) else float(row.pressure),
            "humidity": None if pd.isna(row.humidity) else float(row.humidity),
            "wind_speed": None if pd.isna(row.wind_speed) else float(row.wind_speed),
            "clouds_all": None if pd.isna(row.clouds_all) else float(row.clouds_all),
        })

    for row in demand.itertuples(index=False):
        ts = row.ts
        dt = _to_dt(ts)
        gen = gen_wide.loc[ts]
        yield {
            "_id": dt,
            "timestamp": dt,
            "demand": {
                "total_load_actual": float(row.total_load_actual),
                "price_actual": None if pd.isna(row.price_actual) else float(row.price_actual),
                "price_day_ahead": None if pd.isna(row.price_day_ahead) else float(row.price_day_ahead),
            },
            "generation": {k: (None if pd.isna(v) else float(v)) for k, v in gen.items()},
            "weather": weather_by_ts.get(ts, []),
        }


def main():
    require(MONGODB_URI, "MONGODB_URI")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    print(f"Dropping existing collection '{COLLECTION}' (if any) ...")
    db[COLLECTION].drop()
    col = db[COLLECTION]

    print("Building & inserting documents ...")
    batch, total = [], 0
    for doc in build_documents():
        batch.append(doc)
        if len(batch) >= BATCH:
            col.insert_many(batch)
            total += len(batch)
            batch = []
            print(f"  inserted {total:,} ...", end="\r")
    if batch:
        col.insert_many(batch)
        total += len(batch)

    col.create_index([("timestamp", ASCENDING)])
    print(f"\nInserted {total:,} documents into {MONGODB_DB}.{COLLECTION}")
    print("Created index on 'timestamp'.")
    client.close()


if __name__ == "__main__":
    main()
