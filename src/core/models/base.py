# src/core/models/base.py
"""
공통 ENUM 정의 및 Mixin 클래스
"""
import enum

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


# ===================== ENUM 정의 =====================

class MarketType(str, enum.Enum):
  """시장 구분"""
  KOSPI = "KOSPI"
  KOSDAQ = "KOSDAQ"
  KONEX = "KONEX"
  NYSE = "NYSE"
  NASDAQ = "NASDAQ"
  AMEX = "AMEX"
  LSE = "LSE"
  TSE = "TSE"


class CurrencyType(str, enum.Enum):
  """통화 구분"""
  KRW = "KRW"
  USD = "USD"
  EUR = "EUR"
  JPY = "JPY"
  GBP = "GBP"


class CountryCode(str, enum.Enum):
  """국가 코드"""
  KOR = "KOR"
  USA = "USA"
  EUR = "EUR"
  JPN = "JPN"
  GBR = "GBR"


class PeriodType(str, enum.Enum):
  """재무제표 기간 구분"""
  Q1 = "Q1"
  Q2 = "Q2"
  Q3 = "Q3"
  Q4 = "Q4"
  FY = "FY"


class RecommendationType(str, enum.Enum):
  """추천 유형"""
  BUY = "BUY"
  SELL = "SELL"
  HOLD = "HOLD"
  STRONG_BUY = "STRONG_BUY"
  STRONG_SELL = "STRONG_SELL"


class DataCollectionStatus(str, enum.Enum):
  """데이터 수집 상태"""
  SUCCESS = "SUCCESS"
  FAILED = "FAILED"
  PARTIAL = "PARTIAL"
  RUNNING = "RUNNING"


class SectorLevel(int, enum.Enum):
  """섹터 레벨"""
  MAJOR = 1
  MIDDLE = 2
  MINOR = 3


class TimestampMixin:
  """
  생성일시, 수정일시 필드를 제공하는 Mixin
  PostgreSQL TIMESTAMPTZ 사용 (UTC)
  """
  created_at = Column(
      DateTime(timezone=True),
      server_default=func.now(),
      nullable=False,
      comment="생성일시 (UTC)"
  )
  updated_at = Column(
      DateTime(timezone=True),
      server_default=func.now(),
      onupdate=func.now(),  # 업데이트시 자동 갱신
      nullable=False,
      comment="수정일시 (UTC)"
  )
