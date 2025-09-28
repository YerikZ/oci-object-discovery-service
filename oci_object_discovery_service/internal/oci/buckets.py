## Mock implementation of list_objects for testing purposes.
# Placeholder for OCI SDK integration.
# Replace with actual OCI Object Storage listing using the 'oci' Python SDK.


def list_buckets(namespace: str, region: str) -> list[dict]:
    results = []
    for i in range(2):
        results.append(
            {
                "name": f"test-bucket-{i + 1}",
                "namespace": namespace,
                "region": region,
                "compartmentId": "dummy_compartment_id",
                "sizeInMB": 2048,
                "timeCreated": "2021-01-01T00:00:00.000Z",
                "lifecycleState": "ACTIVE",
                "etag": "dummy_etag"
        }
    )
    return results