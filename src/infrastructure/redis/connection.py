from typing import Optional

import aioredis

from src.config.settings import get_settings

_settings = get_settings()
_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
  global _redis
  if _redis is None:
    _redis = aioredis.Redis(
        host=_settings.redis_host,
        port=_settings.redis_port,
        db=_settings.redis_db,
        password=_settings.redis_password,
        decode_responses=True,
        health_check_interval=30,
    )
  return _redis


async def close_redis() -> None:
  global _redis
  if _redis is not None:
    await _redis.close()
    _redis = None
