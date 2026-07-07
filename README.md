# Task 2 — Database Design (SQL + MongoDB)

Task 2 of the Time-Series Pipeline formative for the *Spain hourly electricity
demand* dataset (2015–2018). It designs, implements and queries the **same
time-series data** in two complementary databases:

- a **relational** database (PostgreSQL / Neon) — normalised star schema
- a **non-relational** database (MongoDB / Atlas) — embedded time-series documents

> The brief mentions MySQL; we use **PostgreSQL**, an equivalent relational
> database. All schema scripts are standard SQL DDL.

## Project structure

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── energy_dataset.csv
├── weather_features.csv
├── notebook/                  # Task 1
└── database/                  # Task 2
    ├── common/
    │   ├── config.py          # loads .env, shared metadata (sources, cities)
    │   └── preprocess.py      # Task 1 cleaning pipeline -> DB-ready frames
    ├── sql/
    │   ├── schema.sql         # PostgreSQL DDL (5 tables, FKs, indexes)
    │   ├── load_postgres.py   # creates schema + bulk-loads via COPY
    │   ├── queries.sql        # 5 demonstration queries (raw SQL)
    │   └── run_queries.py     # runs the queries and prints results
    ├── mongodb/
    │   ├── load_mongo.py      # builds one document per hour + inserts
    │   └── run_queries.py     # 5 demonstration queries + prints results
    └── run_all.py             # loads both DBs then runs all queries
```

## Relational schema (5 tables)

A **star schema** anchored on `energy_demand` (the time-series spine, one row per
hour); the two other fact tables reference its `ts` so every reading is tied to a
valid demand hour.

| Table | Type | Grain | Key columns |
|-------|------|-------|-------------|
| `cities` | dimension | 1 row / city | `city_id` PK |
| `generation_sources` | dimension | 1 row / technology | `source_id` PK, `is_renewable` |
| `energy_demand` | fact | 1 row / hour | `ts` PK |
| `energy_generation` | fact | 1 row / (hour, source) | (`ts`, `source_id`) PK/FK |
| `weather_observations` | fact | 1 row / (hour, city) | (`ts`, `city_id`) PK/FK |

The ERD is provided separately in the report (drawn in draw.io).

## MongoDB design (1 collection)

`hourly_records` — one embedded document per hour containing `demand`,
`generation` (sub-document) and `weather` (array of 5 city sub-documents). The
whole hour lives in a single document, matching the natural time-series read
pattern (fetch everything for a timestamp in one query). The document structure
is defined in `database/mongodb/load_mongo.py`, and a complete sample document is
returned by the *latest record* query in `database/mongodb/run_queries.py`.

## Run everything with Docker (recommended)

The whole pipeline runs in one container. It reads credentials from the
repo-root `.env` and connects to the configured PostgreSQL and MongoDB.

```bash
# from the repo root: create your .env first
cp .env.example .env      # then edit .env with your credentials

# build the image and run load + queries for BOTH databases
docker compose up --build
```

Run an individual step instead of the full pipeline:

```bash
docker compose run --rm task2 python database/sql/load_postgres.py
docker compose run --rm task2 python database/mongodb/load_mongo.py
docker compose run --rm task2 python database/sql/run_queries.py
docker compose run --rm task2 python database/mongodb/run_queries.py
```

### Run without Docker (optional)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python database/run_all.py
```

## Queries (≥3 per database)

Both databases answer the same five questions, including the two required
time-series endpoints (**latest record** and **records by date range**). Results
print to the console (Docker logs).

| # | Query | SQL | MongoDB |
|---|-------|-----|---------|
| 1 | Latest record | `WHERE ts = MAX(ts)` + joins | `sort({timestamp:-1}).limit(1)` |
| 2 | Records by date range | `WHERE ts BETWEEN … AND …` | `find({timestamp:{$gte,$lte}})` |
| 3 | Monthly avg demand & price | `GROUP BY date_trunc('month')` | `$group` + `$dateToString` |
| 4 | Renewable mix / temp by city | join on `is_renewable` | `$unwind` weather + `$group` |
| 5 | Top-5 peak demand hours | `ORDER BY … DESC LIMIT 5` | `$sort` + `$limit` |

Both databases return identical figures (e.g. peak demand of **41,015 MW** on
2017-01-18 19:00), confirming the two implementations are consistent.

## Data volumes loaded

| | rows / documents |
|---|---|
| PostgreSQL `energy_demand` | 35,064 |
| PostgreSQL `energy_generation` | 490,896 |
| PostgreSQL `weather_observations` | 175,320 |
| MongoDB `hourly_records` | 35,064 documents |
