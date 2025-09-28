from fastapi import APIRouter, Query
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import re
from bson import ObjectId

load_dotenv()
database_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
database_name = os.getenv("DATABASE_NAME", "ods")
buckets_collection_name = os.getenv("BUCKETS_COLLECTION", "buckets")
objects_collection_name = os.getenv("OBJECTS_COLLECTION", "objects")

router = APIRouter()
client = AsyncIOMotorClient(database_uri)
db = client[database_name]
objects_collection = db[objects_collection_name]
buckets_collection = db[buckets_collection_name]


def serialize_doc(doc):
    """Recursively convert ObjectId to str in a MongoDB document."""
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc

@router.get("/objects")
async def list_objects(
    bucket: str | None = Query(default=None),
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=1000),
):
    """
    List objects with optional bucket filter and keyword search.
    Pagination via skip/limit. Returns total for client-side pagination if desired.
    """
    query: dict = {}
    if bucket:
        query["bucket"] = bucket
    if q and q.strip():
        query["name"] = {"$regex": re.escape(q.strip()), "$options": "i"}

    total = await objects_collection.count_documents(query)
    cursor = objects_collection.find(query).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    return {
        "results": serialize_doc(results),
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(results) < total,
    }

@router.get("/buckets")
async def list_buckets():
    results = await buckets_collection.find().to_list(length=100)
    return {"results": serialize_doc(results)}

@router.get("/search")
async def search_objects(q: str = Query(..., min_length=1)):
    regex = re.escape(q)  # prevent regex injection
    cursor = objects_collection.find(
        {"name": {"$regex": regex, "$options": "i"}}
    ).limit(50)
    results = await cursor.to_list(length=50)
    return {"results": serialize_doc(results)}
