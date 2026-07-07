from fastapi import APIRouter, Depends, HTTPException
from api.deps import get_mongo_collection
from api.schemas import DateRangeQuery, TimeSeriesResponse
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/mongodb", tags=["MongoDB"])

@router.get("/latest")
def get_latest_record(collection = Depends(get_mongo_collection)):
    record = collection.find_one(sort=[("timestamp", -1)])
    if not record:
        raise HTTPException(status_code=404, detail="No records found")
    record["id"] = str(record.pop("_id"))
    return record

@router.get("/range")
def get_by_date_range(query: DateRangeQuery, collection = Depends(get_mongo_collection)):
    records = list(collection.find({
        "timestamp": {
            "$gte": query.start_date,
            "$lte": query.end_date
        }
    }).sort("timestamp", 1))
    
    for r in records:
        r["id"] = str(r.pop("_id"))
    return records