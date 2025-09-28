from oci_object_discovery_service.internal.oci.buckets import list_buckets
from oci_object_discovery_service.internal.oci.objects import list_objects
from oci_object_discovery_service.internal.db import (
    buckets_collection,
    objects_collection,
    sessions_collection,
)
from datetime import datetime, timezone
from oci_object_discovery_service.utils.logger import logger
import time

def run_task_list_buckets(task: dict):
    tenancy_name = task["job"]["oci_tenancy_name"]
    namespace = task["job"]["oci_namespace"]
    region = task["job"]["oci_region"]
    logger.info(f"[worker] Listing buckets in tenancy={tenancy_name} region={region}")
    buckets = list_buckets(namespace, region)
    count = 0
    for bucket in buckets:
        buckets_collection.update_one(
            {"name": bucket["name"], "namespace": bucket["namespace"]},
            {
                "$set": {
                    "metadata": bucket,
                    "updated_at": datetime.now(timezone.utc),
                    "scan_id": task["_id"],
                }
            },
            upsert=True,
        )
        count += 1
    logger.info(f"[worker] Stored {count} buckets in MongoDB for tenancy={tenancy_name}")

def run_task_list_objects(task: dict):
    buckets = buckets_collection.find({"metadata.lifecycleState": "ACTIVE"})
    
    for bucket in buckets:
        logger.debug(f"[worker] Processing bucket: {bucket}")
        bucket_name = bucket.get("name")
        if not bucket_name:
            logger.warning(f"[worker] Skipping bucket without 'name': {bucket}")
            continue

        logger.info(f"[worker] Scanning bucket {bucket_name}")

        objects = list_objects(bucket_name)
        count = 0

        for obj in objects:
            objects_collection.update_one(
                {"bucket": obj["bucket"], "name": obj["name"]},
                {
                    "$set": {
                        "metadata": obj,
                        "updated_at": datetime.now(timezone.utc),
                        "scan_id": task.get("_id"),
                    }
                },
                upsert=True,
            )
            count += 1

        logger.info(f"[worker] Stored {count} objects in MongoDB for bucket {bucket_name}")

def process_task(task: dict):
    job_name = task["job"]["name"]
    if job_name == "list-buckets":
        run_task_list_buckets(task)
    
    if job_name == "list-objects":
        run_task_list_objects(task)

    sessions_collection.update_one(
        {"_id": task["_id"]},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc),
            }
        },
    )
    return    

def start_scan():
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
    start_scan()
