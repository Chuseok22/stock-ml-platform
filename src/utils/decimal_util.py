from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional


def to_decimal(s: Optional[str]) -> Optional[Decimal]:
  """
  문자열을 Decimal로 안전 변환
  - 빈 문자열/None -> None
  - "12,345.67" 같이 콤마 포함 처리
  """
  if s is None:
    return None
  s = s.strip()
  if not s:
    return None
  try:
    return Decimal(s.replace(",", ""))
  except InvalidOperation:
    return None


def to_int(s: Optional[str]) -> Optional[int]:
  """문자열을 int로 안전 변환"""
  d = to_decimal(s)
  return int(d) if d is not None else None


def to_float(s: Optional[str]) -> Optional[float]:
  d = to_decimal(s)
  return float(d) if d is not None else None


def to_date8(s: str) -> date:
  """'YYYYMMDD' -> date 객체"""
  return date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
