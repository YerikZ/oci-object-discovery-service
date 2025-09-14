from fastapi import APIRouter, Query
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import re
from bson import ObjectId

load_dotenv()
database_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
database_name = os.getenv("DATABASE_NAME", "ods")
objects_collection_name = os.getenv("OBJECTS_COLLECTION", "objects")
sessions_collection_name = os.getenv("SESSIONS_COLLECTION", "scan_sessions")

router = APIRouter()
client = AsyncIOMotorClient(database_uri)
db = client[database_name]
objects_collection = db[objects_collection_name]


def serialize_doc(doc):
    """Recursively convert ObjectId to str in a MongoDB document."""
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


@router.get("/search")
async def search_objects(q: str = Query(..., min_length=1)):
    regex = re.escape(q)  # prevent regex injection
    cursor = objects_collection.find(
        {"name": {"$regex": regex, "$options": "i"}}
    ).limit(50)
    results = await cursor.to_list(length=50)
    return {"results": serialize_doc(results)}
