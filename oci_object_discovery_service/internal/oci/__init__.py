# Placeholder for OCI SDK integration.
# Replace with actual OCI Object Storage listing using the 'oci' Python SDK.
# This stub returns a few fake objects per prefix so the worker can persist into Redis.


def list_objects(bucket: str, prefixes: list[str]):
    results = []
    for p in prefixes or [""]:
        for i in range(3):
            results.append(
                {
                    "bucket": bucket,
                    "name": f"{p}file-{i}.txt",
                    "size": 1234 + i,
                    "etag": "dummy",
                    "contentType": "text/plain",
                }
            )
    return results
