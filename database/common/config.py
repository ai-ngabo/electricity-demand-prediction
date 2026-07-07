from pathlib import Path
import os

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = REPO_ROOT / "database"
ENERGY_CSV = REPO_ROOT / "energy_dataset.csv"
WEATHER_CSV = REPO_ROOT / "weather_features.csv"

load_dotenv(REPO_ROOT / ".env")

POSTGRES_URL = os.getenv("POSTGRES_URL")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "electricity_demand")

GENERATION_SOURCES = {
    "generation biomass": ("biomass", True),
    "generation fossil brown coal/lignite": ("fossil_brown_coal_lignite", False),
    "generation fossil gas": ("fossil_gas", False),
    "generation fossil hard coal": ("fossil_hard_coal", False),
    "generation fossil oil": ("fossil_oil", False),
    "generation hydro pumped storage consumption": ("hydro_pumped_storage_consumption", False),
    "generation hydro run-of-river and poundage": ("hydro_run_of_river", True),
    "generation hydro water reservoir": ("hydro_water_reservoir", True),
    "generation nuclear": ("nuclear", False),
    "generation other": ("other", False),
    "generation other renewable": ("other_renewable", True),
    "generation solar": ("solar", True),
    "generation waste": ("waste", True),
    "generation wind onshore": ("wind_onshore", True),
}

CITY_COORDS = {
    "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3874, 2.1686),
    "Valencia": (39.4699, -0.3763),
    "Seville": (37.3891, -5.9845),
    "Bilbao": (43.2630, -2.9350),
}


def require(value, name):
    if not value:
        raise RuntimeError(
            f"Missing {name}. Copy .env.example to .env at the repo root "
            f"and fill in your credentials."
        )
    return value


# Enforce required credentials
POSTGRES_URL = require(POSTGRES_URL, "POSTGRES_URL")
MONGODB_URI = require(MONGODB_URI, "MONGODB_URI")