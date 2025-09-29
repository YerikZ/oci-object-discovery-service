from oci_object_discovery_service.internal.db.repository import (
    create_session as _create_session,
)


def create_session(job: dict) -> bool:
    _create_session(job)
    return True
