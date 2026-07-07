import json
import sys
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient, DESCENDING

sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))
from config import MONGODB_URI, MONGODB_DB, require

COLLECTION = "hourly_records"


def dumps(obj):
    return json.dumps(obj, indent=2, default=str)


def _iso(s):
    return datetime.fromisoformat(s)


def main():
    require(MONGODB_URI, "MONGODB_URI")
    client = MongoClient(MONGODB_URI)
    col = client[MONGODB_DB][COLLECTION]

    print("=" * 78)
    print("MongoDB (Atlas) - Task 2 query results")
    print("=" * 78)

    def show(title, code, result):
        print(f"\n### {title}\n{code.strip()}\n\nResult:\n{dumps(result)}\n")

    code = "db.hourly_records.find().sort({timestamp: -1}).limit(1)"
    doc = col.find_one(sort=[("timestamp", DESCENDING)])
    show("Q1 - Latest record", code, doc)

    code = ("db.hourly_records.find({timestamp: {$gte: ISODate('2018-06-01'),"
            " $lte: ISODate('2018-06-01T23:00:00Z')}}, "
            "{timestamp:1, 'demand.total_load_actual':1}).limit(10)")
    rng = list(col.find(
        {"timestamp": {"$gte": _iso("2018-06-01"), "$lte": _iso("2018-06-01T23:00:00")}},
        {"timestamp": 1, "demand.total_load_actual": 1, "_id": 0},
    ).limit(10))
    show("Q2 - Records by date range (2018-06-01)", code, rng)

    code = """db.hourly_records.aggregate([
  { $group: {
      _id: { $dateToString: { format: '%Y-%m', date: '$timestamp' } },
      avg_load_mw: { $avg: '$demand.total_load_actual' },
      avg_price:   { $avg: '$demand.price_actual' } } },
  { $sort: { _id: 1 } }, { $limit: 12 }
])"""
    monthly = list(col.aggregate([
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
            "avg_load_mw": {"$avg": "$demand.total_load_actual"},
            "avg_price": {"$avg": "$demand.price_actual"}}},
        {"$sort": {"_id": 1}}, {"$limit": 12},
    ]))
    for m in monthly:
        m["avg_load_mw"] = round(m["avg_load_mw"], 0)
        m["avg_price"] = round(m["avg_price"], 2)
    show("Q3 - Monthly average demand & price (aggregation)", code, monthly)

    code = """db.hourly_records.aggregate([
  { $unwind: '$weather' },
  { $group: { _id: '$weather.city', avg_temp_c: { $avg: '$weather.temp' } } },
  { $sort: { avg_temp_c: -1 } }
])"""
    by_city = list(col.aggregate([
        {"$unwind": "$weather"},
        {"$group": {"_id": "$weather.city", "avg_temp_c": {"$avg": "$weather.temp"}}},
        {"$sort": {"avg_temp_c": -1}},
    ]))
    for c in by_city:
        c["avg_temp_c"] = round(c["avg_temp_c"], 2)
    show("Q4 - Average temperature per city (unwind embedded array)", code, by_city)

    code = """db.hourly_records.aggregate([
  { $project: { timestamp: 1, load: '$demand.total_load_actual' } },
  { $sort: { load: -1 } }, { $limit: 5 }
])"""
    peaks = list(col.aggregate([
        {"$project": {"_id": 0, "timestamp": 1, "load": "$demand.total_load_actual"}},
        {"$sort": {"load": -1}}, {"$limit": 5},
    ]))
    show("Q5 - Top 5 peak demand hours", code, peaks)

    client.close()


if __name__ == "__main__":
    main()
