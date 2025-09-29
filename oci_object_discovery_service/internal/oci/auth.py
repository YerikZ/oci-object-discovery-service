from __future__ import annotations

import os
from typing import Optional, Tuple

from oci import config as oci_config
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from oci.object_storage import ObjectStorageClient
from oci.identity import IdentityClient

from oci_object_discovery_service.utils.logger import logger


def get_clients(region: str, profile: Optional[str] = None) -> Tuple[ObjectStorageClient, IdentityClient, Optional[str]]:
    """Return OCI clients (ObjectStorage, Identity) and the tenancy OCID.

    Prefers local config (default or profile), falls back to instance principals.
    Region is required for both modes. Tenancy OCID is taken from config when
    available, otherwise from the signer if present, otherwise from env
    `OCI_TENANCY_OCID`.
    """
    # Try local config first
    try:
        profile = profile or os.getenv("OCI_PROFILE")
        cfg = oci_config.from_file(profile_name=profile)  # raises if not present
        cfg["region"] = region or cfg.get("region")
        object_client = ObjectStorageClient(cfg)
        identity_client = IdentityClient(cfg)
        tenancy = cfg.get("tenancy")
        logger.info("Using OCI local config%s" % (f" profile={profile}" if profile else ""))
        return object_client, identity_client, tenancy
    except Exception as e:
        logger.info(f"Falling back to Instance Principals signer: {e}")

    # Fallback: Instance Principals
    signer = InstancePrincipalsSecurityTokenSigner()
    cfg = {"region": region}
    object_client = ObjectStorageClient(config=cfg, signer=signer)
    identity_client = IdentityClient(config=cfg, signer=signer)
    tenancy = getattr(signer, "tenancy_id", None) or os.getenv("OCI_TENANCY_OCID")
    if not tenancy:
        logger.warning("Unable to determine tenancy OCID; set OCI_TENANCY_OCID env if needed")
    return object_client, identity_client, tenancy

