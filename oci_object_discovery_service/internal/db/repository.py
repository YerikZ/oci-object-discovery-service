from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional

from bson import ObjectId

from . import buckets_collection, objects_collection, sessions_collection
from .models import BucketDoc, ObjectDoc, ScanSession


# -------- Buckets --------


def upsert_bucket(doc: BucketDoc) -> None:
    buckets_collection.update_one(
        {"name": doc.name, "namespace": doc.namespace},
        {"$set": doc.to_mongo()},
        upsert=True,
    )


def find_active_buckets() -> Iterable[BucketDoc]:
    # Return all buckets; the real API payload does not expose lifecycleState
    # as used previously under metadata.*. If needed, filter using fields in
    # BucketDoc.data.
    cursor = buckets_collection.find()
    for raw in cursor:
        yield BucketDoc.from_mongo(raw)  # type: ignore[return-value]


# -------- Objects --------


def upsert_object(doc: ObjectDoc) -> None:
    objects_collection.update_one(
        {"bucket": doc.bucket, "name": doc.name},
        {"$set": doc.to_mongo()},
        upsert=True,
    )


# -------- Scan Sessions --------


def create_session(job: dict) -> ObjectId:
    now = datetime.now(timezone.utc)
    session = ScanSession(job=job, status="pending", created_at=now)
    res = sessions_collection.insert_one(session.to_mongo())
    return res.inserted_id


def claim_next_pending_session() -> Optional[ScanSession]:
    raw = sessions_collection.find_one_and_update(
        {"status": "pending"},
        {"$set": {"status": "in_progress", "started_at": datetime.now(timezone.utc)}},
    )
    return ScanSession.from_mongo(raw)  # type: ignore[return-value]


def mark_session_completed(session_id: ObjectId) -> None:
    sessions_collection.update_one(
        {"_id": session_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc)}},
    )
