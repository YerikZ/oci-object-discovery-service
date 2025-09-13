from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")

client = MongoClient(MONGO_URI)
db = client["ods"]
objects_collection = db["objects"]
objects_collection.create_index(
    [("bucket", 1), ("name", 1)],
    unique=True
)

sessions_collection = db["scan_sessions"]
