# src/infrastructure/stock/service/stock_service.py
import logging
from typing import List

from core.models import MarketType
from infrastructure.db.session import get_session
from infrastructure.stock.dto.stock_seed import StockSeed
from infrastructure.stock.repository.stock_repository import find_market_id_by_market_code, save_stocks

log = logging.getLogger(__name__)

_KOSPI_TOP30: list[tuple[str, str]] = [
  ("005930", "삼성전자"),
  ("000660", "SK하이닉스"),
  ("207940", "삼성바이오로직스"),
  ("373220", "LG에너지솔루션"),
  ("005380", "현대차"),
  ("035420", "NAVER"),
  ("051910", "LG화학"),
  ("006400", "삼성SDI"),
  ("035720", "카카오"),
  ("000270", "기아"),
  ("012330", "현대모비스"),
  ("096770", "SK이노베이션"),
  ("066570", "LG전자"),
  ("028260", "삼성물산"),
  ("105560", "KB금융"),
  ("055550", "신한지주"),
  ("015760", "한국전력"),
  ("017670", "SK텔레콤"),
  ("090430", "아모레퍼시픽"),
  ("018260", "삼성에스디에스"),
  ("003670", "포스코퓨처엠"),
  ("005490", "POSCO홀딩스"),
  ("068270", "셀트리온"),
  ("034730", "SK"),
  ("032830", "삼성생명"),
  ("323410", "카카오뱅크"),
  ("377300", "카카오페이"),
  ("302440", "SK바이오사이언스"),
  ("259960", "크래프톤"),
  ("086520", "에코프로")  # 필요시 교체/삭제
]


def _to_seeds(rows: list[tuple[str, str]]) -> List[StockSeed]:
  """ticker, name 리스트를 StockSeed 리스트로 변환"""
  return [
    StockSeed(
        ticker=t,
        stock_name=n,
        listing_date=None,
        face_value=None,
        listing_shares=None,
    )
    for t, n in rows[:30]
  ]


async def seed_kospi_top30() -> int:
  """KOSPI TOP 30 UPSERT"""
  seeds = _to_seeds(_KOSPI_TOP30)
  if not seeds:
    log.warning("[KOSPI SEED] KOSPI 시드 데이터가 비어있습니다.")
    return 0

  async with get_session() as session:
    try:
      market_id = await find_market_id_by_market_code(session, MarketType.KOSPI)
      upserted = await save_stocks(session, market_id=market_id, seeds=seeds)
      await session.commit()
      log.info("[KOSPI SEED] stock 데이터 UPSERT 완료: %s 건", upserted)
      return upserted
    except Exception:
      await session.rollback()
      log.exception("[KOSPI SEED] UPSERT 중 오류 발생 (rollback)")
      raise
