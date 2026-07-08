from __future__ import annotations

from typing import Any

from bson import ObjectId
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


def row_to_dict(row: Any) -> dict[str, Any]:
	return dict(row._mapping)


def fetch_postgres_latest(db: Session) -> dict[str, Any] | None:
	result = db.execute(
		text(
			"""
			SELECT ts, total_load_actual, price_actual, price_day_ahead
			FROM energy_demand
			ORDER BY ts DESC
			LIMIT 1
			"""
		)
	)
	row = result.fetchone()
	return row_to_dict(row) if row else None


def fetch_postgres_range(db: Session, start_date, end_date) -> list[dict[str, Any]]:
	result = db.execute(
		text(
			"""
			SELECT ts, total_load_actual, price_actual, price_day_ahead
			FROM energy_demand
			WHERE ts BETWEEN :start_date AND :end_date
			ORDER BY ts
			"""
		),
		{"start_date": start_date, "end_date": end_date},
	)
	return [row_to_dict(row) for row in result.fetchall()]


def fetch_postgres_record(db: Session, ts) -> dict[str, Any] | None:
	result = db.execute(
		text(
			"""
			SELECT ts, total_load_actual, price_actual, price_day_ahead
			FROM energy_demand
			WHERE ts = :ts
			"""
		),
		{"ts": ts},
	)
	row = result.fetchone()
	return row_to_dict(row) if row else None


def create_postgres_record(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
	result = db.execute(
		text(
			"""
			INSERT INTO energy_demand (ts, total_load_actual, price_actual, price_day_ahead)
			VALUES (:ts, :total_load_actual, :price_actual, :price_day_ahead)
			RETURNING ts, total_load_actual, price_actual, price_day_ahead
			"""
		),
		payload,
	)
	return row_to_dict(result.fetchone())


def update_postgres_record(db: Session, ts, payload: dict[str, Any]) -> dict[str, Any] | None:
	if not payload:
		return fetch_postgres_record(db, ts)

	assignments = ", ".join(f"{column} = :{column}" for column in payload)
	parameters = {**payload, "ts": ts}
	result = db.execute(
		text(
			f"""
			UPDATE energy_demand
			SET {assignments}
			WHERE ts = :ts
			RETURNING ts, total_load_actual, price_actual, price_day_ahead
			"""
		),
		parameters,
	)
	row = result.fetchone()
	return row_to_dict(row) if row else None


def delete_postgres_record(db: Session, ts) -> bool:
	result = db.execute(text("DELETE FROM energy_demand WHERE ts = :ts"), {"ts": ts})
	return result.rowcount > 0


def mongo_document_to_dict(document: dict[str, Any] | None) -> dict[str, Any] | None:
	if not document:
		return None
	document["id"] = str(document.pop("_id"))
	return document


def parse_object_id(record_id: str) -> ObjectId:
	try:
		return ObjectId(record_id)
	except Exception as exc:
		raise HTTPException(status_code=400, detail="Invalid record id") from exc


def create_mongo_record(collection, payload: dict[str, Any]) -> dict[str, Any]:
	result = collection.insert_one(payload)
	document = collection.find_one({"_id": result.inserted_id})
	return mongo_document_to_dict(document)


def fetch_mongo_record(collection, record_id: str) -> dict[str, Any] | None:
	document = collection.find_one({"_id": parse_object_id(record_id)})
	return mongo_document_to_dict(document)


def fetch_mongo_latest(collection) -> dict[str, Any] | None:
	document = collection.find_one(sort=[("timestamp", -1)])
	return mongo_document_to_dict(document)


def fetch_mongo_range(collection, start_date, end_date) -> list[dict[str, Any]]:
	documents = list(
		collection.find({"timestamp": {"$gte": start_date, "$lte": end_date}}).sort("timestamp", 1)
	)
	return [mongo_document_to_dict(document) for document in documents]


def update_mongo_record(collection, record_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
	if not payload:
		return fetch_mongo_record(collection, record_id)

	collection.update_one(
		{"_id": parse_object_id(record_id)},
		{"$set": payload},
	)
	return fetch_mongo_record(collection, record_id)


def delete_mongo_record(collection, record_id: str) -> bool:
	result = collection.delete_one({"_id": parse_object_id(record_id)})
	return result.deleted_count > 0
