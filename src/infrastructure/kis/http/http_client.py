# src/infrastructure/kis/http/http_client.py
import logging
from typing import Optional, Mapping, Any, Callable, Awaitable

import httpx

from src.config.settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
  global _http_client
  if _http_client is None:
    _http_client = httpx.AsyncClient(
        base_url=settings.kis_base_url.rstrip("/"),
        timeout=httpx.Timeout(10.0, read=20.0)
    )
  return _http_client


async def close_http_client() -> None:
  global _http_client
  if _http_client is not None:
    await _http_client.aclose()
    _http_client = None


class KISClient:
  """
  - 기본 헤더 (appkey/appsecret) 자동 설정
  - auth=True 시 Authorization Bearer 자동 주입
  """

  def __init__(self, token_provider: Callable[[], Awaitable[str]] | None = None) -> None:
    self._token_provider = token_provider

  async def request(
      self,
      method: str,
      path_or_url: str,
      *,
      tr_id: str | None = None,  # 거래 id
      auth: bool = True,
      headers: Mapping[str, str] | None = None,
      params: Mapping[str, str] | None = None,
      json: Any | None = None,
      data: Any | None = None,
  ) -> Any:
    # 기본 헤더
    request_header: dict[str, str] = {
      "content-type": "application/json",
      "appkey": settings.kis_app_key,
      "appsecret": settings.kis_app_secret,
      "custtype": "P"  # 고객 타입 (개인)
    }
    if tr_id:
      request_header["tr_id"] = tr_id

    # 토큰 주입
    if auth:
      if not self._token_provider:
        raise RuntimeError("auth=True 인 경우 token_provider가 필요합니다.")
      token = await self._token_provider()
      request_header["authorization"] = f"Bearer {token}"

    if headers:
      request_header.update(headers)

    client = get_http_client()
    response = await client.request(
        method=method.upper(),
        url=path_or_url,
        headers=request_header,
        params=params,
        json=json,
        data=data,
    )
    response.raise_for_status()

    # json 우선 반환
    if "application/json" in response.headers.get("Content-Type", ""):
      return response.json()
    return response.text

  async def get(self, path_or_url: str, **kwargs: Any) -> Any:
    return await self.request("GET", path_or_url, **kwargs)

  async def post(self, path_or_url: str, **kwargs: Any) -> Any:
    return await self.request("POST", path_or_url, **kwargs)
