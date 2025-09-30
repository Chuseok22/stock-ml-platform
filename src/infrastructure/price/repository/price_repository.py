# src/infrastructure/price/repository/price_repository.py
from typing import List, Dict, Tuple

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import MarketType, Stock, Market, DailyPrice
from infrastructure.price.service.price_api import DailyPriceDTO


async def get_stock_id_map_by_market(
    session: AsyncSession,
    *,
    market_codes: List[MarketType]
) -> Dict[str, int]:
  """
  ticker -> stock_id 매핑 반환
  - market_codes 에 해당하는 시장의 활성 종목만 조회
  - KOSPI/KOSDAQ 동시 매핑 가능
  """
  query = (
    select(Stock.ticker, Stock.stock_id)
    .join(Market, Stock.market_id == Market.market_id)
    .where(Market.market_code.in_(market_codes))
    .where(Stock.is_active.is_(True))
  )
  rows = (await session.execute(query)).all()
  return { t: sid for (t, sid) in rows }


async def upsert_daily_prices(
    session: AsyncSession,
    rows: List[Tuple[int, DailyPriceDTO]]
) -> int:
  """
  DailyPrice upsert (PostgreSQL ON CONFLICT UPDATE)
  """
  if not rows:
    return 0

  payload = []
  for stock_id, dto in rows:
    payload.append(
        dict(
            stock_id=stock_id,
            trade_date=dto.trade_date,
            open_price=dto.open_price,
            high_price=dto.high_price,
            low_price=dto.low_price,
            close_price=dto.close_price,
            volume=dto.volume,
            trading_value=dto.trading_value,
            adjusted_close=dto.adjusted_close,
            change_rate=dto.change_rate,
            change_amount=dto.change_amount,
            market_cap=dto.market_cap,
            shares_outstanding=dto.shares_outstanding,
        )
    )

  stmt = pg_insert(DailyPrice).values(payload)

  update_cols = {
    c.name: getattr(stmt.excluded, c.name)
    for c in DailyPrice.__table__.columns
    if c.name not in ("stock_id", "trade_date", "created_at")
  }
  update_cols["updated_at"] = func.now()

  stmt = stmt.on_conflict_do_update(
      index_elements=[DailyPrice.stock_id, DailyPrice.trade_date],
      set_=update_cols,
  )

  await session.execute(stmt)
  return len(payload)
