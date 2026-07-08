from fastapi import APIRouter, Depends, HTTPException
from api.deps import get_mongo_collection
from api.crud import (
    create_mongo_record,
    delete_mongo_record,
    fetch_mongo_latest,
    fetch_mongo_range,
    fetch_mongo_record,
    update_mongo_record,
)
from api.schemas import MongoRecordCreate, MongoRecordResponse, MongoRecordUpdate
from datetime import datetime
from fastapi import Query, status

router = APIRouter(prefix="/mongodb", tags=["MongoDB"])

@router.get("/records", response_model=list[MongoRecordResponse])
def list_records(collection = Depends(get_mongo_collection)):
    records = list(collection.find().sort("timestamp", 1))
    return [{**record, "id": str(record.pop("_id"))} for record in records]

@router.get("/latest")
def get_latest_record(collection = Depends(get_mongo_collection)):
    record = fetch_mongo_latest(collection)
    if not record:
        raise HTTPException(status_code=404, detail="No records found")
    return record

@router.get("/range")
def get_by_date_range(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    collection = Depends(get_mongo_collection),
):
    return fetch_mongo_range(collection, start_date, end_date)

@router.get("/records/{record_id}", response_model=MongoRecordResponse)
def get_record(record_id: str, collection = Depends(get_mongo_collection)):
    record = fetch_mongo_record(collection, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.post("/records", response_model=MongoRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(record: MongoRecordCreate, collection = Depends(get_mongo_collection)):
    return create_mongo_record(collection, record.model_dump())

@router.put("/records/{record_id}", response_model=MongoRecordResponse)
def update_record(record_id: str, record: MongoRecordUpdate, collection = Depends(get_mongo_collection)):
    updated = update_mongo_record(collection, record_id, record.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return updated

@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: str, collection = Depends(get_mongo_collection)):
    deleted = delete_mongo_record(collection, record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return None