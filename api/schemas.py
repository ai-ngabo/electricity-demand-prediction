from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class DateRangeQuery(BaseModel):
    start_date: datetime
    end_date: datetime

class TimeSeriesCreate(BaseModel):
    timestamp: datetime
    total_load_actual: float
    price_actual: Optional[float] = None
    # Add other fields as needed from your data
    temperature: Optional[float] = None

class TimeSeriesResponse(TimeSeriesCreate):
    id: Any
    class Config:
        from_attributes = True