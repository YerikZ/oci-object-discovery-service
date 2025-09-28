## Mock implementation of list_objects for testing purposes.
# Placeholder for OCI SDK integration.
# Replace with actual OCI Object Storage listing using the 'oci' Python SDK.


def list_objects(bucket: str, prefixes: list[str] = None) -> list[dict]:
    results = []
    for p in prefixes or [""]:
        for i in range(5):
            for env in ["dev", "prod"]:
                results.append(
                    {
                        "bucket": bucket,
                        "name": f"{env}/{p}file-{i}.txt",
                        "size": 1234 + i,
                        "etag": "dummy",
                        "contentType": "text/plain",
                    }
                )
    return results