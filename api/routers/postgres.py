from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from api.deps import get_pg_db
from sqlalchemy import text

from api.crud import (
    create_postgres_record,
    delete_postgres_record,
    fetch_postgres_latest,
    fetch_postgres_range,
    fetch_postgres_record,
    update_postgres_record,
)
from api.schemas import PostgresRecordCreate, PostgresRecordResponse, PostgresRecordUpdate

router = APIRouter(prefix="/postgres", tags=["PostgreSQL"])

@router.get("/records", response_model=list[PostgresRecordResponse], response_model_by_alias=False)
def list_records(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_pg_db),
):
    try:
        if start_date and end_date:
            return fetch_postgres_range(db, start_date, end_date)

        result = db.execute(
            text(
                """
                SELECT ts, total_load_actual, price_actual, price_day_ahead
                FROM energy_demand
                ORDER BY ts
                """
            )
        )
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        print("Error in /postgres/records:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
def get_latest_record(db: Session = Depends(get_pg_db)):
    try:
        record = fetch_postgres_latest(db)
        if record:
            return record
        raise HTTPException(status_code=404, detail="No records found")
    except HTTPException:
        raise
    except Exception as e:
        print("Error in /postgres/latest:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/range")
def get_by_date_range(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_pg_db),
):
    try:
        return fetch_postgres_range(db, start_date, end_date)
    except Exception as e:
        print("Error in /postgres/range:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/records/{ts}", response_model=PostgresRecordResponse, response_model_by_alias=False)
def get_record(ts: datetime, db: Session = Depends(get_pg_db)):
    try:
        record = fetch_postgres_record(db, ts)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        print("Error in /postgres/records/{ts}:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/records",
    response_model=PostgresRecordResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
)
def create_record(record: PostgresRecordCreate, db: Session = Depends(get_pg_db)):
    try:
        created = create_postgres_record(db, record.model_dump())
        db.commit()
        return created
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Error in create_record:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/records/{ts}", response_model=PostgresRecordResponse, response_model_by_alias=False)
@router.patch("/records/{ts}", response_model=PostgresRecordResponse, response_model_by_alias=False)
def update_record(ts: datetime, record: PostgresRecordUpdate, db: Session = Depends(get_pg_db)):
    try:
        updated = update_postgres_record(db, ts, record.model_dump(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=404, detail="Record not found")
        db.commit()
        return updated
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Error in update_record:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/records/{ts}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(ts: datetime, db: Session = Depends(get_pg_db)):
    try:
        deleted = delete_postgres_record(db, ts)
        if not deleted:
            raise HTTPException(status_code=404, detail="Record not found")
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Error in delete_record:", str(e))
        raise HTTPException(status_code=500, detail=str(e))