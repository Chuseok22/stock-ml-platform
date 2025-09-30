# src/infrastructure/market/repository/market_repository.py
import logging
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Market, MarketType

log = logging.getLogger(__name__)


async def upsert_markets(session: AsyncSession, payloads: Iterable[dict]) -> int:
  """시장 기본 데이터 UPSERT"""
  payloads = list(payloads)
  if not payloads:
    return 0

  stmt = pg_insert(Market).values(payloads)

  excluded = stmt.excluded
  stmt = stmt.on_conflict_do_update(
      index_elements=[Market.market_code],
      set_={
        "market_name": excluded.market_name,
        "country_code": excluded.country_code,
        "currency": excluded.currency,
        "timezone": excluded.timezone,
        "trading_hours": excluded.trading_hours,
        "description": excluded.description,
        "updated_at": func.now(),  # 항상 갱신
      },
  )
  await session.execute(stmt)
  return len(payloads)


async def find_market_id_by_code(session: AsyncSession, market_code: MarketType) -> int | None:
  """market_code 로 market_id 조회 (없으면 None)"""
  query = select(Market.market_id).where(Market.market_code == market_code)
  return (await session.execute(query)).scalar_one_or_none()
