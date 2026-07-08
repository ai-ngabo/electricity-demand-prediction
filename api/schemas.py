from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class DateRangeQuery(BaseModel):
    start_date: datetime
    end_date: datetime


class PostgresRecordBase(BaseModel):
    ts: datetime = Field(alias="timestamp")
    total_load_actual: float
    price_actual: Optional[float] = None
    price_day_ahead: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class PostgresRecordCreate(PostgresRecordBase):
    pass


class PostgresRecordUpdate(BaseModel):
    total_load_actual: Optional[float] = None
    price_actual: Optional[float] = None
    price_day_ahead: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class PostgresRecordResponse(PostgresRecordBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MongoRecordBase(BaseModel):
    timestamp: datetime
    demand: dict[str, Any]
    generation: Optional[dict[str, Any]] = None
    weather: list[dict[str, Any]] = Field(default_factory=list)


class MongoRecordCreate(MongoRecordBase):
    pass


class MongoRecordUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    demand: Optional[dict[str, Any]] = None
    generation: Optional[dict[str, Any]] = None
    weather: Optional[list[dict[str, Any]]] = None


class MongoRecordResponse(MongoRecordBase):
    id: Any

    model_config = ConfigDict(from_attributes=True)