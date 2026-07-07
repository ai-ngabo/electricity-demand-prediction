import io
import sys
from pathlib import Path

import psycopg2

sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))
from config import POSTGRES_URL, GENERATION_SOURCES, CITY_COORDS, require
from preprocess import clean_energy_frames, clean_weather_frame

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def _copy(cur, df, table, columns):
    buf = io.StringIO()
    df[columns].to_csv(buf, index=False, header=False, na_rep="")
    buf.seek(0)
    cols = ", ".join(columns)
    cur.copy_expert(f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, NULL '')", buf)


def main():
    require(POSTGRES_URL, "POSTGRES_URL")

    print("Preprocessing CSVs ...")
    demand, generation = clean_energy_frames()
    weather = clean_weather_frame()

    conn = psycopg2.connect(POSTGRES_URL)
    conn.autocommit = False
    cur = conn.cursor()

    print("Creating schema ...")
    cur.execute(SCHEMA_FILE.read_text())

    print("Loading dimension tables ...")
    for name, (lat, lon) in CITY_COORDS.items():
        cur.execute(
            "INSERT INTO cities (city_name, latitude, longitude) VALUES (%s, %s, %s)",
            (name, lat, lon),
        )
    for _, (name, is_renew) in GENERATION_SOURCES.items():
        cur.execute(
            "INSERT INTO generation_sources (source_name, is_renewable) VALUES (%s, %s)",
            (name, is_renew),
        )

    cur.execute("SELECT city_id, city_name FROM cities")
    city_id = {n: i for i, n in cur.fetchall()}
    cur.execute("SELECT source_id, source_name FROM generation_sources")
    source_id = {n: i for i, n in cur.fetchall()}

    print(f"Loading energy_demand ({len(demand):,} rows) ...")
    _copy(cur, demand, "energy_demand",
          ["ts", "total_load_actual", "price_actual", "price_day_ahead"])

    generation = generation.copy()
    generation["source_id"] = generation["source_name"].map(source_id)
    print(f"Loading energy_generation ({len(generation):,} rows) ...")
    _copy(cur, generation, "energy_generation", ["ts", "source_id", "generation_mw"])

    weather = weather.copy()
    weather["city_id"] = weather["city_name"].map(city_id)
    print(f"Loading weather_observations ({len(weather):,} rows) ...")
    _copy(cur, weather, "weather_observations",
          ["ts", "city_id", "temp", "pressure", "humidity", "wind_speed", "clouds_all"])

    conn.commit()

    for tbl in ["cities", "generation_sources", "energy_demand",
                "energy_generation", "weather_observations"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"  {tbl:<22}: {cur.fetchone()[0]:>8,} rows")

    cur.close()
    conn.close()
    print("PostgreSQL load complete.")


if __name__ == "__main__":
    main()
