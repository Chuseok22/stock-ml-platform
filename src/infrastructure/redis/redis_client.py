# src/infrastructure/redis/redis_client.py
import logging
from typing import Optional

import redis.asyncio as redis

from config.settings import settings

log = logging.getLogger(__name__)


class RedisClient:
  def __init__(self):
    """Redis Client 연결(비동기)"""
    self.client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )

  async def ping(self) -> bool:
    """연결 테스트(비동기)"""
    try:
      await self.client.ping()
      log.debug("Redis 연결 성공")
      return True
    except Exception:
      log.exception("Redis 연결 실패")
      raise

  async def get_value(self, key: str) -> Optional[str]:
    """Redis에 저장된 값 조회(비동기)"""
    try:
      return await self.client.get(key)
    except Exception as e:
      log.error("Key: %s 에 해당하는 값 조회 실패: %s", key, e)
      return None

  async def set_value(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
    """Redis TTL 저장(비동기)"""
    try:
      if ttl:
        log.debug("Redis TTL 저장 key:%s, ttl:%s", key, ttl)
        return bool(await self.client.setex(key, ttl, value))
      else:
        log.debug("Redis 저장 (TTL 미설정) key:%s", key)
        return bool(await self.client.set(key, value))
    except Exception as e:
      log.error("Redis TTL 저장 실패 key:%s, ttl:%s, 오류:%s", key, ttl, e)
      return False

  async def delete_value(self, key: str) -> bool:
    """Redis 데이터 삭제(비동기)"""
    try:
      return bool(await self.client.delete(key))
    except Exception as e:
      log.error("Key: %s 에 해당하는 데이터 삭제 실패: %s", key, e)
      return False

  async def get_ttl(self, key: str) -> Optional[int]:
    """TTL 조회(초). 없으면 -2, 무제한이면 -1"""
    try:
      return await self.client.ttl(key)
    except Exception:
      return None

  async def close(self) -> None:
    """Redis 연결 종료"""
    try:
      await self.client.close()
    except Exception:
      pass
