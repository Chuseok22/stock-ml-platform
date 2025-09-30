# src/infrastructure/price/service/price_service.py
import logging
from datetime import date
from typing import List, Tuple

from core.models import MarketType
from infrastructure.db.session import get_session
from infrastructure.kis.http.http_client import KISClient
from infrastructure.kis.service.token_service import KISTokenService
from infrastructure.price.dto.daily_price_dto import DailyPriceDTO
from infrastructure.price.repository.price_repository import get_stock_id_map_by_market, upsert_daily_prices
from infrastructure.price.service.price_api import KISPriceAPI
from utils.partition import ensure_daily_price_partitions

log = logging.getLogger(__name__)


async def save_daily_prices(
    *,
    market_codes: List[MarketType],
    start: date,
    end: date,
) -> int:
  """daily_price UPSERT"""
  kis_token_service = KISTokenService()
  kis_client = KISClient(token_provider=kis_token_service.get_token)
  kis_price_api = KISPriceAPI(kis_client)

  async with get_session() as session:
    ticker_to_id = await get_stock_id_map_by_market(session, market_codes=market_codes)
    # 파티션 미리 생성 (존재하면 skip)
    await ensure_daily_price_partitions(session, start=start, end=end)
    await session.commit()

  if not ticker_to_id:
    log.warning("[PRICE SERVICE] 활성화된 종목이 없습니다. market_codes=%s", [m.value for m in market_codes])
    return 0

  rows: List[Tuple[int, DailyPriceDTO]] = []  # (stock_id, dto) 누적 버퍼
  for ticker, stock_id in ticker_to_id.items():
    try:
      dtos = await kis_price_api.fetch_domestic_daily(ticker=ticker, start=start, end=end)
      if not dtos:
        log.info("[PRICE SERVICE] 데이터 없음 ticker=%s (%s~%s)", ticker, start, end)
        continue
      for dto in dtos:
        rows.append((stock_id, dto))
    except Exception:
      log.exception("[PRICE SERVICE] KIS fetch 실패 ticker=%s", ticker)
      continue

  if not rows:
    log.info("[PRICE SERVICE] 저장할 데이터가 없습니다. market=%s, 기간=%s~%s",
             [m.value for m in market_codes], start, end)
    return 0

  async with get_session() as session:
    try:
      upserted = await upsert_daily_prices(session, rows)
      await session.commit()
    except Exception:
      await session.rollback()
      log.exception("[PRICE SERVICE] upsert 트랜잭션 실패 (rollback)")
      raise

  log.info("[PRICE SERVICE] 완료 market=%s, upserted=%s",
           [m.value for m in market_codes], upserted)
  return upserted
