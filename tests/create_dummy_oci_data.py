from __future__ import annotations

import argparse
import io
import os
import sys
import time
from typing import List, Optional

from oci.core import models as core_models  # type: ignore
from oci.exceptions import ServiceError  # type: ignore
from oci.object_storage import models as os_models  # type: ignore

# Ensure project root is on sys.path when running from tests/
# This allows `python tests/create_dummy_oci_data.py` or running inside tests/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from oci_object_discovery_service.internal.oci.auth import get_clients
from oci_object_discovery_service.utils.logger import logger


def get_namespace_if_missing(object_client, provided: Optional[str]) -> str:
    if provided:
        return provided
    return object_client.get_namespace().data


def bucket_exists(object_client, namespace: str, name: str) -> bool:
    try:
        object_client.get_bucket(namespace, name)
        return True
    except ServiceError as e:
        if e.status == 404:
            return False
        raise


def ensure_bucket(object_client, namespace: str, compartment_id: str, name: str, kms_key_id: Optional[str] = None):
    if bucket_exists(object_client, namespace, name):
        logger.info(f"Bucket already exists: {name}")
        return
    details = os_models.CreateBucketDetails(
        name=name,
        compartment_id=compartment_id,
        public_access_type="NoPublicAccess",
        kms_key_id=kms_key_id,
        object_events_enabled=False,
    )
    object_client.create_bucket(namespace, details)
    logger.info(f"Created bucket: {name}")


def put_text_object(object_client, namespace: str, bucket: str, object_name: str, content: str):
    data = io.BytesIO(content.encode("utf-8"))
    object_client.put_object(namespace, bucket, object_name, data, content_type="text/plain")


def create_dummy_data(
    region: str,
    compartment_id: str,
    namespace: Optional[str],
    bucket_prefix: str,
    bucket_count: int,
    prefixes: List[str],
    per_prefix: int,
    suffix: Optional[str] = None,
    dry_run: bool = False,
):
    object_client, _, _ = get_clients(region)
    ns = get_namespace_if_missing(object_client, namespace)

    if not suffix:
        suffix = str(int(time.time()))

    buckets = [f"{bucket_prefix}{i}-{suffix}" for i in range(1, bucket_count + 1)]
    logger.info(f"Target namespace={ns} region={region} compartment={compartment_id}")
    logger.info(f"Buckets to ensure: {buckets}")

    if dry_run:
        logger.info("Dry-run mode: not creating resources")
        return

    for b in buckets:
        ensure_bucket(object_client, ns, compartment_id, b)
        for p in (prefixes or [""]):
            for i in range(per_prefix):
                key = f"{p}file-{i}.txt" if p else f"file-{i}.txt"
                content = f"dummy data for {b}/{key}\n"
                put_text_object(object_client, ns, b, key, content)
        logger.info(f"Uploaded {per_prefix * max(1, len(prefixes or []))} objects to {b}")


def parse_args(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(description="Create dummy OCI buckets and objects")
    ap.add_argument("--region", required=True, help="OCI region, e.g. us-ashburn-1")
    ap.add_argument("--compartment-id", required=True, help="Target compartment OCID")
    ap.add_argument("--namespace", help="Object Storage namespace (optional; auto-detect if omitted)")
    ap.add_argument("--bucket-prefix", default="ods-dummy-", help="Prefix for bucket names")
    ap.add_argument("--bucket-count", type=int, default=2, help="Number of buckets to create")
    ap.add_argument("--prefixes", default="dev/,prod/", help="Comma-separated object prefixes")
    ap.add_argument("--per-prefix", type=int, default=5, help="Objects to create per prefix per bucket")
    ap.add_argument("--suffix", help="Optional suffix for bucket names (default: current epoch seconds)")
    ap.add_argument("--dry-run", action="store_true", help="Print planned actions without executing")
    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    prefixes = [p for p in (args.prefixes.split(",") if args.prefixes else []) if p]
    try:
        create_dummy_data(
            region=args.region,
            compartment_id=args.compartment_id,
            namespace=args.namespace,
            bucket_prefix=args.bucket_prefix,
            bucket_count=args.bucket_count,
            prefixes=prefixes,
            per_prefix=args.per_prefix,
            suffix=args.suffix,
            dry_run=args.dry_run,
        )
        return 0
    except ServiceError as e:
        logger.error(f"OCI ServiceError: {e.status} {e.message}")
        return 2
    except Exception as e:
        logger.exception(f"Error creating dummy data: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
