# src/infrastructure/stock/repository/stock_repository.py
from typing import Iterable

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import MarketType, Market, Stock
from infrastructure.stock.dto.stock_seed import StockSeed


async def find_market_id_by_market_code(session: AsyncSession, market_code: MarketType) -> int:
  """market_code로 market_id 조회"""
  query = select(Market.market_id).where(Market.market_code == market_code)
  row = (await session.execute(query)).scalar_one_or_none()
  if row is None:
    raise RuntimeError(f"[STOCK_REPOSITORY] 시장 {market_code.value} 가 존재하지 않습니다.")
  return int(row)


async def save_stocks(
    session: AsyncSession,
    *,
    market_id: int,
    seeds: Iterable[StockSeed],
) -> int:
  """StockSeed 저장 (stock 테이블)"""
  payload = []
  for seed in seeds:
    payload.append(
        dict(
            ticker=seed.ticker,
            market_id=market_id,
            stock_name=seed.stock_name,
            stock_name_en=None,  # mst에는 영문명이 없음(필요시 후처리)
            sector_id=None,  # mst에는 정확 섹터 매핑 정보 부재
            listing_date=seed.listing_date,
            listing_shares=seed.listing_shares,
            face_value=seed.face_value,
            is_active=True,  # 거래정지/관리종목은 별도 정책으로 다루는게 안전
            delisting_date=None,
            description=None,
            website=None,
        )
    )

  if not payload:
    return 0

  stmt = pg_insert(Stock).values(payload)

  update_cols = {
    # PK/created_at 제외하고 갱신
    "stock_name": stmt.excluded.stock_name,
    "listing_date": stmt.excluded.listing_date,
    "listing_shares": stmt.excluded.listing_shares,
    "face_value": stmt.excluded.face_value,
    "is_active": stmt.excluded.is_active,
    "delisting_date": stmt.excluded.delisting_date,
    "description": stmt.excluded.description,
    "website": stmt.excluded.website,
    "updated_at": func.now(),  # ✅ 항상 갱신
  }

  stmt = stmt.on_conflict_do_update(
      index_elements=[Stock.ticker, Stock.market_id],
      set_=update_cols,
  )

  await session.execute(stmt)
  return len(payload)
