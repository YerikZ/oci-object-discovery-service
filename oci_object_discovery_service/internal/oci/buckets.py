from __future__ import annotations

from typing import List

from oci import pagination
from oci.object_storage import ObjectStorageClient
from oci.identity import IdentityClient

from .auth import get_clients
from oci_object_discovery_service.utils.logger import logger


def _list_all_compartments(identity_client: IdentityClient, tenancy_ocid: str) -> List[str]:
    """Return all active compartment OCIDs including the root tenancy."""
    comp_ids: List[str] = [tenancy_ocid]
    resp = pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_ocid,
        compartment_id_in_subtree=True,
        access_level="ANY",
    )
    for c in resp.data:
        if getattr(c, "lifecycle_state", None) == "ACTIVE":
            comp_ids.append(c.id)
    return comp_ids


def list_buckets(namespace: str, region: str) -> list[dict]:
    """List buckets across all compartments for the tenancy in the given region.

    Note: OCI API requires a compartment OCID to list buckets; we enumerate
    all accessible compartments under the tenancy and aggregate results.
    """
    object_client, identity_client, tenancy = get_clients(region)
    if not tenancy:
        raise RuntimeError("Tenancy OCID not available; set OCI_TENANCY_OCID or use local config")

    results: list[dict] = []
    for comp_id in _list_all_compartments(identity_client, tenancy):
        try:
            resp = pagination.list_call_get_all_results(
                object_client.list_buckets, namespace, comp_id
            )
            for b in resp.data:
                # Map to our expected metadata shape; some fields may be None
                time_created = getattr(b, "time_created", None)
                lifecycle_state = getattr(b, "lifecycle_state", None)
                results.append(
                    {
                        "name": b.name,
                        "namespace": namespace,
                        "region": region,
                        "compartmentId": comp_id,
                        "timeCreated": time_created.isoformat() if time_created else None,
                        "lifecycleState": getattr(lifecycle_state, "value", lifecycle_state),
                    }
                )
        except Exception as e:
            logger.warning(f"Error listing buckets in compartment {comp_id}: {e}")
            continue
    return results
