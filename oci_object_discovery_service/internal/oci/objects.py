from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator, Iterable, Iterator, List, Optional, Tuple

from oci.exceptions import ServiceError
from oci.object_storage.models import ListObjects

from .auth import get_clients
from oci_object_discovery_service.utils.logger import logger


RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _call_with_retries(func, *args, max_retries: int = 5, base_delay: float = 0.5, factor: float = 2.0, **kwargs):
    """Call SDK function with exponential backoff on retryable ServiceError."""
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except ServiceError as e:
            if e.status in RETRYABLE_STATUS and attempt < max_retries:
                delay = base_delay * (factor ** attempt)
                logger.warning(f"Retryable OCI error {e.status}; retrying in {delay:.2f}s (attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
                attempt += 1
                continue
            raise


def _iter_objects(namespace: str, bucket: str, prefix: str, region: str, *, limit: int = 1000, timeout: Tuple[float, float] = (5.0, 60.0), max_retries: int = 5, backoff_base: float = 0.5, backoff_factor: float = 2.0) -> Iterator[dict]:
    object_client, _, _ = get_clients(region)
    start = None
    while True:
        resp: ListObjects = _call_with_retries(
            object_client.list_objects,
            namespace,
            bucket,
            prefix=prefix or None,
            start=start,
            limit=limit,
            timeout=timeout,
            max_retries=max_retries,
            base_delay=backoff_base,
            factor=backoff_factor,
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


def list_objects(
    namespace: str,
    bucket: str,
    region: str,
    prefixes: Optional[List[str]] = None,
    *,
    limit: int = 1000,
    timeout: Tuple[float, float] = (5.0, 60.0),
    max_retries: int = 5,
    backoff_base: float = 0.5,
    backoff_factor: float = 2.0,
    concurrency: int = 0,
) -> Iterable[dict]:
    """Stream objects under optional prefixes with pagination, retries, and timeouts.

    - Streams results (iterator) instead of returning a materialized list.
    - Adds exponential backoff for retryable errors.
    - Applies timeouts per API call.
    - Optional `concurrency` executes per-prefix scans in parallel threads.
    """
    selected_prefixes = prefixes or [""]

    if concurrency and concurrency > 1 and len(selected_prefixes) > 1:
        # Concurrent scan per prefix; stream results via a queue to avoid materializing.
        import queue

        def generator() -> Iterator[dict]:
            q: "queue.Queue[Optional[dict]]" = queue.Queue(maxsize=concurrency * 2)
            sentinel = object()

            def worker(pfx: str):
                try:
                    for item in _iter_objects(
                        namespace,
                        bucket,
                        pfx,
                        region,
                        limit=limit,
                        timeout=timeout,
                        max_retries=max_retries,
                        backoff_base=backoff_base,
                        backoff_factor=backoff_factor,
                    ):
                        q.put(item)
                finally:
                    q.put(sentinel)  # signal completion of this worker

            # Launch workers
            with ThreadPoolExecutor(max_workers=concurrency) as ex:
                for p in selected_prefixes:
                    ex.submit(worker, p)

                completed = 0
                total = len(selected_prefixes)
                while completed < total:
                    item = q.get()
                    if item is sentinel:
                        completed += 1
                    else:
                        yield item  # stream to caller

        return generator()

    # Sequential (streaming) over a single or multiple prefixes
    def generator_seq() -> Iterator[dict]:
        for p in selected_prefixes:
            yield from _iter_objects(
                namespace,
                bucket,
                p,
                region,
                limit=limit,
                timeout=timeout,
                max_retries=max_retries,
                backoff_base=backoff_base,
                backoff_factor=backoff_factor,
            )

    return generator_seq()
