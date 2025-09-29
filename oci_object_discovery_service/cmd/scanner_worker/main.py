from oci_object_discovery_service.internal.oci.buckets import list_buckets
from oci_object_discovery_service.internal.oci.objects import list_objects
from oci_object_discovery_service.internal.db.repository import (
    upsert_bucket,
    upsert_object,
    find_active_buckets,
    claim_next_pending_session,
    mark_session_completed,
)
from oci_object_discovery_service.internal.db.models import BucketDoc, ObjectDoc
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
        doc = BucketDoc(
            name=bucket["name"],
            namespace=bucket["namespace"],
            metadata=bucket,
            updated_at=datetime.now(timezone.utc),
            scan_id=task["_id"],
        )
        upsert_bucket(doc)
        count += 1
    logger.info(
        f"[worker] Stored {count} buckets in MongoDB for tenancy={tenancy_name}"
    )


def run_task_list_objects(task: dict):
    for bucket in find_active_buckets():
        logger.debug(f"[worker] Processing bucket: {bucket}")
        bucket_name = bucket.name
        if not bucket_name:
            logger.warning(f"[worker] Skipping bucket without 'name': {bucket}")
            continue

        logger.info(f"[worker] Scanning bucket {bucket_name}")

        # Use real OCI SDK pagination, using the bucket's namespace and region from job
        job_region = task["job"].get("oci_region")
        objects = list_objects(bucket.namespace, bucket_name, job_region)
        count = 0

        for obj in objects:
            doc = ObjectDoc(
                bucket=obj["bucket"],
                name=obj["name"],
                metadata=obj,
                updated_at=datetime.now(timezone.utc),
                scan_id=task.get("_id"),
            )
            upsert_object(doc)
            count += 1

        logger.info(
            f"[worker] Stored {count} objects in MongoDB for bucket {bucket_name}"
        )


def process_task(task: dict):
    job_name = task["job"]["name"]
    if job_name == "list-buckets":
        run_task_list_buckets(task)

    if job_name == "list-objects":
        run_task_list_objects(task)

    mark_session_completed(task["_id"])
    return


def start_scan():
    logger.info("[worker] listening for pending scan sessions")
    while True:
        task = claim_next_pending_session()
        if task:
            process_task(task.model_dump(by_alias=True))
        else:
            logger.info("[worker] no task found, sleeping...")
            time.sleep(30)


if __name__ == "__main__":
    start_scan()
