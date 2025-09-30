# src/core/models/index.py
"""
시장지수 관련 모델
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, BigInteger, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin
from infrastructure.db.session import Base


class MarketIndex(TimestampMixin, Base):
  """시장지수 기본 정보 테이블"""
  __tablename__ = "market_index"

  index_id = Column(Integer, primary_key=True, index=True)
  index_code = Column(String(20), unique=True, nullable=False, index=True, comment="지수코드")
  index_name = Column(String(100), nullable=False, comment="지수명")
  index_name_en = Column(String(100), nullable=True, comment="지수명(영문)")
  market_id = Column(Integer, ForeignKey("market.market_id"), nullable=False)
  base_value = Column(DECIMAL(18, 6), nullable=True, comment="기준값")
  base_date = Column(Date, nullable=True, comment="기준일")
  description = Column(Text, nullable=True, comment="지수 설명")

  # 관계 설정
  market = relationship("Market", back_populates="indices", lazy="selectin")
  daily_prices = relationship("DailyIndexPrice", back_populates="index", lazy="selectin", passive_deletes=True)

  def __repr__(self) -> str:
    return f"<MarketIndex(id={self.index_id}, code={self.index_code})>"


class DailyIndexPrice(TimestampMixin, Base):
  """
  일별 시장지수 데이터 테이블 (월별 파티셔닝)
  합성 기본키 사용: (index_id, trade_date)
  """
  __tablename__ = "daily_index_price"

  index_id = Column(Integer, ForeignKey("market_index.index_id", ondelete="CASCADE"), primary_key=True, index=True)
  trade_date = Column(Date, primary_key=True, index=True, comment="거래일")

  # OHLCV 데이터
  open_value = Column(DECIMAL(18, 6), nullable=False, comment="시가")
  high_value = Column(DECIMAL(18, 6), nullable=False, comment="고가")
  low_value = Column(DECIMAL(18, 6), nullable=False, comment="저가")
  close_value = Column(DECIMAL(18, 6), nullable=False, comment="종가")
  volume = Column(BigInteger, default=0, comment="거래량")
  change_rate = Column(DECIMAL(8, 4), nullable=True, comment="등락률(%)")
  change_amount = Column(DECIMAL(18, 6), nullable=True, comment="등락폭")

  # 파티셔닝 설정
  __table_args__ = (
    Index('idx_index_price_date_desc', 'trade_date', postgresql_using='btree'),
    Index('idx_index_price_index_date_desc', 'index_id', 'trade_date', postgresql_using='btree'),
    { "postgresql_partition_by": "RANGE (trade_date)" }
  )

  # 관계 설정
  index = relationship("MarketIndex", back_populates="daily_prices", lazy="selectin")

  def __repr__(self) -> str:
    return f"<DailyIndexPrice(index_id={self.index_id}, date={self.trade_date})>"
