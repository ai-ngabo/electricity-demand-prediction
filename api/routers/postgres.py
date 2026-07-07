from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_pg_db
from api.schemas import TimeSeriesCreate, DateRangeQuery

router = APIRouter(prefix="/postgres", tags=["PostgreSQL"])

@router.post("/records/", response_model=dict)
def create_record(record: TimeSeriesCreate, db: Session = Depends(get_pg_db)):
    try:
        result = db.execute("""
            INSERT INTO energy_demand (timestamp, total_load_actual, price_actual)
            VALUES (:timestamp, :total_load_actual, :price_actual)
            RETURNING *
        """, record.dict())
        db.commit()
        return dict(result.fetchone())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
def get_latest_record(db: Session = Depends(get_pg_db)):
    try:
        result = db.execute("""
            SELECT * FROM energy_demand 
            ORDER BY timestamp DESC LIMIT 1
        """)
        row = result.fetchone()
        return dict(row) if row else {"message": "No records found"}
    except Exception as e:
        print("Error in postgres/latest:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/range")
def get_by_date_range(query: DateRangeQuery, db: Session = Depends(get_pg_db)):
    try:
        result = db.execute("""
            SELECT * FROM energy_demand 
            WHERE timestamp BETWEEN :start AND :end 
            ORDER BY timestamp
        """, {"start": query.start_date, "end": query.end_date})
        return [dict(row) for row in result.fetchall()]
    except Exception as e:
        print("Error in postgres/range:", str(e))
        raise HTTPException(status_code=500, detail=str(e))