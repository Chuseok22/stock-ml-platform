# src/infrastructure/kis/service/token_service.py
import logging
from typing import Any, Optional

from config.settings import settings
from infrastructure.kis.http.http_client import KISClient
from infrastructure.redis.redis_client import RedisClient

log = logging.getLogger(__name__)

# Redis KIS 토큰 Key
KIS_TOKEN_REDIS_KEY = "kis:access_token"


class KISTokenService:
  def __init__(self) -> None:
    self._redis = RedisClient()
    self.client = KISClient(token_provider=self.get_token)

  async def get_token(self) -> str:
    """
    Redis에서 토큰 조회(비동기). 없으면 새로 발급
    """
    token = await self._redis.get_value(KIS_TOKEN_REDIS_KEY)
    if token:
      log.debug("Redis에 저장된 토큰 사용")
      return token
    return await self.issue_and_save_token()

  async def issue_and_save_token(self) -> str:
    """
    KIS 토큰 신규 발급 후 Redis TTL 저장
    """
    log.info("KIS 토큰 발급 진행")
    payload: dict[str, Any] = {
      "grant_type": "client_credentials",
      "appkey": settings.kis_app_key,
      "appsecret": settings.kis_app_secret,
    }
    response = await self.client.post(
        "/oauth2/tokenP",
        auth=False,
        json=payload
    )
    token: Optional[str] = response.get("access_token")
    ttl: int = response.get("expires_in")

    if not token or not isinstance(token, str):
      log.error(f"KIS 토큰 발급 실패. 응답 스키마 확인 필요: %s", response)
      raise RuntimeError("KIS 토큰 발급 실패: access_token 없음")

    await self._redis.set_value(KIS_TOKEN_REDIS_KEY, token, ttl)
    return token

  async def get_ttl(self) -> Optional[int]:
    """Redis에 저장된 KIS 토큰 TTL 반환"""
    return await self._redis.get_ttl(KIS_TOKEN_REDIS_KEY)
