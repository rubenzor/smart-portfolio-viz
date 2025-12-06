import os
import json
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

_redis = None

def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            _redis.ping()
        except Exception:
            _redis = None
    return _redis

def cache_get(key: str):
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None

def cache_set(key: str, value, ex: int = 600):
    r = get_redis()
    if not r:
        return
    try:
        r.set(key, json.dumps(value), ex=ex)
    except Exception:
        pass
