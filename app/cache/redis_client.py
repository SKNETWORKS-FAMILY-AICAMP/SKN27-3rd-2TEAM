import json
import logging
import time

import redis

from app.config.settings import REDIS_DB, REDIS_HOST, REDIS_PORT, REDIS_SESSION_TTL

logger = logging.getLogger("rimas.cache")

_pool: redis.ConnectionPool | None = None


def _get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


def get_client() -> redis.Redis:
    return redis.Redis(connection_pool=_get_pool())


def cache_get(key: str) -> dict | list | None:
    client = get_client()
    start = time.perf_counter()
    try:
        raw = client.get(key)
        ms = round((time.perf_counter() - start) * 1000, 1)
        if raw is None:
            logger.debug("cache_miss", extra={"key": key, "ms": ms})
            return None
        logger.debug("cache_hit", extra={"key": key, "ms": ms})
        return json.loads(raw)
    except Exception as exc:
        logger.error("cache_get_error", extra={"key": key, "error": str(exc)}, exc_info=True)
        return None


def cache_set(key: str, value, ttl: int = REDIS_SESSION_TTL) -> None:
    client = get_client()
    start = time.perf_counter()
    try:
        client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        ms = round((time.perf_counter() - start) * 1000, 1)
        logger.debug("cache_set", extra={"key": key, "ttl": ttl, "ms": ms})
    except Exception as exc:
        logger.error("cache_set_error", extra={"key": key, "error": str(exc)}, exc_info=True)


def cache_delete(key: str) -> None:
    client = get_client()
    try:
        client.delete(key)
        logger.debug("cache_delete", extra={"key": key})
    except Exception as exc:
        logger.error("cache_delete_error", extra={"key": key, "error": str(exc)}, exc_info=True)


def cache_lpush(key: str, value, ttl: int = REDIS_SESSION_TTL) -> None:
    """Prepend one item to a Redis list and reset TTL atomically."""
    client = get_client()
    try:
        pipe = client.pipeline()
        pipe.lpush(key, json.dumps(value, ensure_ascii=False))
        pipe.expire(key, ttl)
        pipe.execute()
        logger.debug("cache_lpush", extra={"key": key})
    except Exception as exc:
        logger.error("cache_lpush_error", extra={"key": key, "error": str(exc)}, exc_info=True)


def cache_lrange(key: str, start: int = 0, end: int = -1) -> list:
    client = get_client()
    try:
        items = client.lrange(key, start, end)
        return [json.loads(item) for item in items]
    except Exception as exc:
        logger.error("cache_lrange_error", extra={"key": key, "error": str(exc)}, exc_info=True)
        return []


def cache_llen(key: str) -> int:
    client = get_client()
    try:
        return client.llen(key)
    except Exception as exc:
        logger.error("cache_llen_error", extra={"key": key, "error": str(exc)}, exc_info=True)
        return 0


def is_healthy() -> bool:
    try:
        return get_client().ping()
    except Exception:
        return False
