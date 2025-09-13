from oci_object_discovery_service.internal import oci
from oci_object_discovery_service.internal.db import (
    objects_collection,
    sessions_collection,
)
from datetime import datetime, timezone
from oci_object_discovery_service.utils.logger import logger
import time


def process_task(task: dict):
    bucket = task["job"]["bucket"]
    prefixes = task["job"].get("prefixes", [])
    logger.info(f"[worker] Scanning bucket {bucket} prefixes={prefixes}")
    objects = oci.list_objects(bucket, prefixes)
    count = 0
    for obj in objects:
        objects_collection.update_one(
            {
                "bucket": bucket,
                "name": obj["name"]
            },
            {"$set": {"metadata": obj,
                      "updated_at": datetime.now(timezone.utc),
                      "scan_id": task["_id"]
                      }},
            upsert=True,
        )
        count += 1
    sessions_collection.update_one(
        {"_id": task["_id"]},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc),
                "object_count": count,
            }
        },
    )
    logger.info(f"[worker] Stored {count} objects in MongoDB for bucket {bucket}")


def main():
    logger.info(f"[worker] listening on MongoDB collection {sessions_collection.name}")
    while True:
        task = sessions_collection.find_one_and_update(
            {"status": "pending"},
            {
                "$set": {
                    "status": "in_progress",
                    "started_at": datetime.now(timezone.utc),
                }
            },
        )
        if task:
            process_task(task)
        else:
            logger.info("[worker] no task found, sleeping...")
            time.sleep(30)


if __name__ == "__main__":
    main()
