from fastapi import APIRouter, Query
import redis.asyncio as redis
import json

router = APIRouter()

async def get_redis():
    return await redis.from_url("redis://redis:6379", decode_responses=True)


@router.get("/search")
async def search_keys(q: str = Query(..., min_length=1)):
    redis = await get_redis()
    keys = await redis.keys(f"*{q}*")
    return {"keys": keys[:10]}


@router.get("/value/{key}")
async def get_value(key: str):
    redis = await get_redis()
    val = await redis.get(key)
    try:
        return {"key": key, "value": json.loads(val)}
    except Exception:
        return {"key": key, "value": val}
