Typed models for MongoDB (overview)

This repository now includes typed models (Pydantic) and a small repository layer to keep MongoDB access type-safe and consistent across sync and async code.

Key files:
- `oci_object_discovery_service/internal/db/models.py`: Pydantic models for Buckets, Objects, and Scan Sessions with `_id` mapping and helpers to serialize to/from Mongo.
- `oci_object_discovery_service/internal/db/repository.py`: Minimal CRUD helpers used by the worker and session creator with typed inputs/outputs.

Why Pydantic instead of bare dataclasses:
- Runtime validation and parsing of nested data from Mongo/OCI responses.
- First-class integration with FastAPI (already used here).
- Simple `.model_validate()` and `.model_dump(by_alias=True)` for Mongo interop.

Validating the approach:
- Static: run `mypy` locally to verify types in worker and repository.
- Runtime: add a quick script to construct `BucketDoc`/`ObjectDoc` from sample OCI payloads and ensure `.to_mongo()` round-trips through Mongo.
- Integration: exercise `scanner_worker` against a local Mongo and check that documents match the shapes defined by the models.

Usage examples:
```
from datetime import datetime, timezone
from oci_object_discovery_service.internal.db.models import BucketDoc
from oci_object_discovery_service.internal.db.repository import upsert_bucket

payload = {"name": "b1", "namespace": "ns", "approximate_size": 10_485_760}
doc = BucketDoc(
    name=payload["name"],
    namespace=payload["namespace"],
    data=payload,
    updated_at=datetime.now(timezone.utc),
)
upsert_bucket(doc)
```

Notes:
- The UI routes still return plain dicts for simplicity, but can be upgraded to validate with `ObjectDoc.model_validate()` before response.
- The env var `database_name` in `internal/db/__init__.py` appears lowercase versus `DATABASE_NAME` in `ui/routes.py`. Consider aligning the name to avoid confusion.
