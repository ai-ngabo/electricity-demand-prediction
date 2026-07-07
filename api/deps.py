import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient

# Correct import from database/common/config.py
from database.common.config import POSTGRES_URL, MONGODB_URI, MONGODB_DB

# PostgreSQL
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_pg_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# MongoDB
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client[MONGODB_DB]
mongo_collection = mongo_db["hourly_records"]

def get_mongo_collection():
    return mongo_collection