from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class MongoBase(BaseModel):
    """Base model with Mongo `_id` mapping and sensible defaults."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: Optional[ObjectId] = Field(default=None, alias="_id")

    def to_mongo(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

    @classmethod
    def from_mongo(cls, data: dict[str, Any] | None) -> Optional["MongoBase"]:
        if not data:
            return None
        return cls.model_validate(data)


class Job(MongoBase):
    name: str
    oci_tenancy_name: str
    oci_namespace: str
    oci_region: str
    frequency_minutes: Optional[int] = None


class BucketDoc(MongoBase):
    name: str
    namespace: str
    data: dict[str, Any]
    updated_at: Optional[datetime] = None
    scan_id: Optional[ObjectId] = None


class ObjectDoc(MongoBase):
    bucket: str
    name: str
    data: dict[str, Any]
    updated_at: Optional[datetime] = None
    scan_id: Optional[ObjectId] = None


class ScanSession(MongoBase):
    job: Job | dict[str, Any]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
