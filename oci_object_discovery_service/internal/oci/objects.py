from __future__ import annotations

from typing import Iterable, List, Optional

from oci.object_storage.models import ListObjects

from .auth import get_clients
from oci_object_discovery_service.utils.logger import logger


def _iter_objects(namespace: str, bucket: str, prefix: str, region: str) -> Iterable[dict]:
    object_client, _, _ = get_clients(region)
    start = None
    while True:
        resp: ListObjects = object_client.list_objects(
            namespace,
            bucket,
            prefix=prefix or None,
            start=start,
        ).data
        for obj in resp.objects or []:
            yield {
                "bucket": bucket,
                "name": obj.name,
                "size": getattr(obj, "size", None),
                "etag": getattr(obj, "etag", None),
            }
        start = getattr(resp, "next_start_with", None)
        if not start:
            break


def list_objects(namespace: str, bucket: str, region: str, prefixes: Optional[List[str]] = None) -> list[dict]:
    """List all objects under optional prefixes with pagination support.

    For very large buckets, this will stream through all pages. Callers may
    want to process results incrementally instead of materializing the full list.
    """
    results: list[dict] = []
    try:
        for prefix in prefixes or [""]:
            for item in _iter_objects(namespace, bucket, prefix, region):
                results.append(item)
    except Exception as e:
        logger.warning(f"Error listing objects for bucket={bucket}: {e}")
    return results
