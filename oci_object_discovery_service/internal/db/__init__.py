from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
database_name = os.getenv("database_name", "ods")
objects_collection_name = os.getenv("OBJECTS_COLLECTION", "objects")
sessions_collection_name = os.getenv("SESSIONS_COLLECTION", "scan_sessions")

client = MongoClient(mongo_uri)
db = client[database_name]
objects_collection = db[objects_collection_name]
objects_collection.create_index([("bucket", 1), ("name", 1)], unique=True)

sessions_collection = db[sessions_collection_name]
