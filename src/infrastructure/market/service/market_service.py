# src/infrastructure/market/service/market_service.py
import logging
from typing import Any, List

from core.models import MarketType, CountryCode, CurrencyType
from infrastructure.db.session import get_session
from infrastructure.market.repository.market_repository import upsert_markets

log = logging.getLogger(__name__)


def _default_market_seeds() -> List[dict[str, Any]]:
  return [
    # KOSPI
    {
      "market_code": MarketType.KOSPI,
      "market_name": "KOSPI",
      "country_code": CountryCode.KOR,
      "currency": CurrencyType.KRW,
      "timezone": "Asia/Seoul",
      "trading_hours": {
        "regular": { "open": "09:00", "close": "15:30" },
        "pre_open": { "open": "08:30", "close": "09:00" },
        "after": { "open": "15:40", "close": "18:00" },
      },
      "description": "코스피",
    },
  ]


async def seed_default_markets() -> int:
  """Market UPSERT"""
  seeds = _default_market_seeds()
  async with get_session() as session:
    try:
      upserted = await upsert_markets(session, seeds)
      await session.commit()
      log.info("[MARKET_SERVICE] 기본 시장 데이터 UPSERT 완료: %s 건", upserted)
      return upserted
    except Exception:
      await session.rollback()
      log.exception("[MARKET_SERVICE] 기본 시장 데이터 UPSERT 중 오류 발생(rollback)")
      raise
