from oci_object_discovery_service.internal.db import sessions_collection
from datetime import datetime, timezone


def create_session(job: dict) -> bool:
    sessions_collection.insert_one(
        {
            "job": job,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
    )
    return True
