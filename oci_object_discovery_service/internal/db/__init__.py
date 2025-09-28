from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
database_name = os.getenv("database_name", "ods")
buckets_collection_name = os.getenv("BUCKETS_COLLECTION", "buckets")
objects_collection_name = os.getenv("OBJECTS_COLLECTION", "objects")
sessions_collection_name = os.getenv("SESSIONS_COLLECTION", "scan_sessions")

client = MongoClient(mongo_uri)
db = client[database_name]
buckets_collection = db[buckets_collection_name]
buckets_collection.create_index([("name", 1), ("namespace", 1)], unique=True)

objects_collection = db[objects_collection_name]
objects_collection.create_index([("bucket", 1), ("name", 1)], unique=True)

sessions_collection = db[sessions_collection_name]
