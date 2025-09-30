from typing import List, Dict, Any

import httpx
from nicegui import ui

from oci_object_discovery_service.utils.logger import logger


API_BASE = "http://controller-api:8080/api/ui"


async def api_get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{API_BASE}{path}", params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}


async def fetch_buckets() -> List[Dict[str, Any]]:
    data = await api_get("/buckets")
    if "error" in data:
        return []
    return data.get("results", [])


async def fetch_objects(
    q: str | None = None, bucket: str | None = None, skip: int = 0, limit: int = 1000
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"skip": skip, "limit": limit}
    if q and q.strip():
        params["q"] = q.strip()
    if bucket and bucket.strip() and bucket != "All":
        params["bucket"] = bucket.strip()
    data = await api_get("/objects", params=params)
    if "error" in data:
        return {
            "results": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
            "error": data["error"],
        }
    return data


async def search_objects(keyword: str) -> List[Dict[str, Any]]:
    data = await api_get("/search", params={"q": keyword})
    if "error" in data:
        return []
    return data.get("results", [])


async def fetch_metrics() -> Dict[str, Any]:
    """Return dashboard metrics: bucket count, object count, total size in MB.

    - Bucket count and total size are derived from /buckets.
    - Object count uses /objects with limit=1 to read the total cheaply.
    """
    buckets = await fetch_buckets()
    bucket_count = len(buckets)
    
    total_size_mb = 0.0
    for b in buckets:
        try:
            size_bytes = b.get("data", {}).get("approximate_size")
            if size_bytes is None:
                continue
            total_size_mb += float(size_bytes) / (1024 * 1024)
        except Exception:
            continue

    obj_resp = await api_get("/objects", params={"skip": 0, "limit": 1})
    object_count = 0
    if isinstance(obj_resp, dict) and "error" not in obj_resp:
        object_count = int(obj_resp.get("total", 0) or 0)

    return {
        "bucket_count": bucket_count,
        "object_count": object_count,
        "total_size_mb": total_size_mb,
    }


def top_nav(active: str = "home") -> None:
    with ui.header().classes("items-center justify-between"):
        ui.label("OCI Object Discovery Service").classes("text-xl font-semibold")
        with ui.row().classes("items-center gap-4"):

            def link(label: str, path: str, key: str):
                style = (
                    "text-white font-bold"
                    if key == active
                    else "text-white/70 hover:text-white"
                )
                ui.link(label, path).classes(style)

            link("Home", "/", "home")
            link("Buckets", "/buckets", "buckets")
            link("Objects", "/objects", "objects")
