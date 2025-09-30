# src/infrastructure/price/service/price_service.py
import logging
from datetime import date
from typing import List, Optional, Tuple

from core.models import MarketType
from infrastructure.db.session import get_session
from infrastructure.kis.http.http_client import KISClient
from infrastructure.kis.service.token_service import KISTokenService
from infrastructure.price.dto.daily_price_dto import DailyPriceDTO
from infrastructure.price.repository.price_repository import get_stock_id_map_by_market, upsert_daily_prices
from infrastructure.price.service.price_api import KISPriceAPI

log = logging.getLogger(__name__)


async def save_daily_prices(
    *,
    market_codes: List[MarketType],
    start: date,
    end: date,
    limit_stocks: Optional[int] = None,
    batch_size: int = 1000,
) -> int:
  """daily_price UPSERT"""
  kis_token_service = KISTokenService()
  kis_client = KISClient(token_provider=kis_token_service.get_token)
  kis_price_api = KISPriceAPI(kis_client)

  async with get_session() as session:
    ticker_to_id = await get_stock_id_map_by_market(session, market_codes=market_codes)

  if not ticker_to_id:
    log.warning("[PRICE SERVICE] 활성화된 종목이 없습니다. market_codes=%s", [m.value for m in market_codes])
    return 0

  items = list(ticker_to_id.items())
  if limit_stocks is not None and limit_stocks > 0:
    items = items[:limit_stocks]

  total_upserted = 0
  buffer: List[Tuple[int, DailyPriceDTO]] = []

  for idx, (ticker, stock_id) in enumerate(items, start=1):
    try:
      dtos = await kis_price_api.fetch_domestic_daily(ticker=ticker, start=start, end=end)
    except Exception:
      log.exception("[PRICE SERVICE] KIS fetch 실패 ticker=%s", ticker)
      continue

    if not dtos:
      log.info("[PRICE SERVICE] 데이터 없음 ticker=%s (%s~%s)", ticker, start, end)
      continue

    for dto in dtos:
      buffer.append((stock_id, dto))

    # 배치 업서트
    if len(buffer) >= batch_size:
      upserted = await _flush_upsert(buffer)
      total_upserted += upserted
      buffer.clear()
      log.info("[PRICE SERVICE] 누적 upsert=%s (진행: %s/%s)", total_upserted, idx, len(items))

  # 잔여분 업서트
  if buffer:
    upserted = await _flush_upsert(buffer)
    total_upserted += upserted
    buffer.clear()

  log.info("[PRICE SERVICE] 완료 market=%s, upserted=%s", [m.value for m in market_codes], total_upserted)
  return total_upserted


async def _flush_upsert(buffer: List[Tuple[int, DailyPriceDTO]]) -> int:
  """
  내부 헬퍼: 버퍼 내용을 트랜잭션으로 업서트 후 커밋
  """
  if not buffer:
    return 0

  async with get_session() as session:
    try:
      upserted = await upsert_daily_prices(session, buffer)
      await session.commit()
      return upserted
    except Exception:
      await session.rollback()
      log.exception("[PRICE SERVICE] upsert 트랜잭션 실패 (rollback)")
      raise