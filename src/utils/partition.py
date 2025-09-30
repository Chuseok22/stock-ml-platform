# src/utils/partition.py
from datetime import date
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _month_start(d: date) -> date:
  """해당 날짜의 월 초(1일) 반환"""
  return date(d.year, d.month, 1)


def _next_month(d: date) -> date:
  """다음 달 1일 반환"""
  if d.month == 12:
    return date(d.year + 1, 1, 1)
  return date(d.year, d.month + 1, 1)


def _month_iter(start: date, end: date) -> Iterable[tuple[date, date]]:
  """
  [start, end] 구간을 덮는 월 단위 (월초, 다음달초) 구간을 순회
  예: 2025-08-13 ~ 2025-09-30 → (2025-08-01, 2025-09-01), (2025-09-01, 2025-10-01)
  """
  cur = _month_start(start)
  limit = _next_month(_month_start(end))
  while cur < limit:
    nxt = _next_month(cur)
    yield cur, nxt
    cur = nxt


async def ensure_daily_price_partitions(
    session: AsyncSession,
    *,
    start: date,
    end: date,
) -> int:
  """
  daily_price 파티션(월별)을 [start, end] 구간에 대해 생성 (존재하면 skip)
  - 테이블명: daily_price_YYYY_MM
  - 인덱스: (stock_id, trade_date DESC), (trade_date DESC)

  Returns:
      생성(또는 이미 존재로 skip 포함)한 파티션 개수
  """
  created = 0

  for month_start, next_month_start in _month_iter(start, end):
    part_name = f"daily_price_{month_start.year}_{month_start.month:02d}"
    from_str = month_start.isoformat()
    to_str = next_month_start.isoformat()

    # ★ 파티션 테이블 생성
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {part_name}
        PARTITION OF daily_price
        FOR VALUES FROM ('{from_str}') TO ('{to_str}');
        """
    await session.execute(text(create_sql))

    # ★ 파티션 인덱스 생성
    idx1_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_{part_name}_sid_date
        ON {part_name} (stock_id, trade_date DESC);
        """
    idx2_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_{part_name}_date
        ON {part_name} (trade_date DESC);
        """
    await session.execute(text(idx1_sql))
    await session.execute(text(idx2_sql))

    created += 1

  return created