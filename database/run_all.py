import runpy
from pathlib import Path

BASE = Path(__file__).resolve().parent

STEPS = [
    "sql/load_postgres.py",
    "mongodb/load_mongo.py",
    "sql/run_queries.py",
    "mongodb/run_queries.py",
]


def main():
    for step in STEPS:
        print("\n" + "#" * 78)
        print(f"# RUNNING {step}")
        print("#" * 78)
        runpy.run_path(str(BASE / step), run_name="__main__")


if __name__ == "__main__":
    main()
