import json, time, os
import redis
from oci_object_discovery_service.internal import oci

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

QUEUE_KEY = os.getenv("SCAN_QUEUE", "scan-queue")

def process_task(task):
    bucket = task["bucket"]
    prefixes = task.get("prefixes", [])
    print(f"[worker] Scanning bucket {bucket} prefixes={prefixes}")
    objects = oci.list_objects(bucket, prefixes)
    count = 0
    for obj in objects:
        key = f"obj:{bucket}:{obj['name']}"
        r.set(key, json.dumps(obj))
        count += 1
    print(f"[worker] Stored {count} objects in Redis")

def main():
    print(f"[worker] listening on Redis list {QUEUE_KEY} at {REDIS_HOST}:{REDIS_PORT}")
    while True:
        task = r.blpop(QUEUE_KEY, timeout=5)
        if task:
            _, payload = task
            process_task(json.loads(payload))

if __name__ == "__main__":
    main()
