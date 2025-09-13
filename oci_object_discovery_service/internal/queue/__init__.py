import os, json, redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
QUEUE_KEY = os.getenv("SCAN_QUEUE", "scan-queue")

_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def enqueue(job: dict):
    _r.rpush(QUEUE_KEY, json.dumps(job))
    return True
