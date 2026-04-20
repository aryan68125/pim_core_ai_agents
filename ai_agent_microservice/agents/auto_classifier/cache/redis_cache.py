from __future__ import annotations

import hashlib
import json

import redis.asyncio as aioredis

from agents.auto_classifier.config import settings

_redis: aioredis.Redis | None = None


async def init_redis(url: str) -> aioredis.Redis:
    global _redis
    _redis = aioredis.from_url(url, decode_responses=True)
    return _redis


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialised — call init_redis() at startup")
    return _redis


def _key(product_id: str, taxonomy_type: str) -> str:
    raw = f"{product_id}:{taxonomy_type}"
    return "auto_classifier:" + hashlib.sha256(raw.encode()).hexdigest()


async def get_cached(product_id: str, taxonomy_type: str) -> dict | None:
    try:
        data = await get_redis().get(_key(product_id, taxonomy_type))
        return json.loads(data) if data else None
    except Exception:
        return None


async def set_cached(
    product_id: str,
    taxonomy_type: str,
    value: dict,
    ttl: int = settings.cache_ttl_seconds,
) -> None:
    try:
        await get_redis().setex(_key(product_id, taxonomy_type), ttl, json.dumps(value))
    except Exception:
        pass
