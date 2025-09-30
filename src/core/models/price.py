# src/core/models/price.py
"""
주가 데이터 모델 (파티셔닝 적용)
"""
from sqlalchemy import Column, Integer, Date, DateTime, DECIMAL, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin
from infrastructure.db.session import Base


class DailyPrice(TimestampMixin, Base):
  """
  일별 주가 데이터 테이블 (월별 파티셔닝)
  합성 기본키 사용: (stock_id, trade_date)
  """
  __tablename__ = "daily_price"

  stock_id = Column(Integer, ForeignKey("stock.stock_id", ondelete="CASCADE"), primary_key=True, index=True)
  trade_date = Column(Date, primary_key=True, index=True, comment="거래일")

  # OHLCV 데이터
  open_price = Column(DECIMAL(18, 6), nullable=False, comment="시가")
  high_price = Column(DECIMAL(18, 6), nullable=False, comment="고가")
  low_price = Column(DECIMAL(18, 6), nullable=False, comment="저가")
  close_price = Column(DECIMAL(18, 6), nullable=False, comment="종가")
  volume = Column(BigInteger, nullable=False, default=0, comment="거래량")

  # 추가 데이터
  trading_value = Column(DECIMAL(24, 2), nullable=True, comment="거래대금")
  adjusted_close = Column(DECIMAL(18, 6), nullable=True, comment="수정종가")
  change_rate = Column(DECIMAL(8, 4), nullable=True, comment="등락률(%)")
  change_amount = Column(DECIMAL(18, 6), nullable=True, comment="등락금액")

  # 시장 정보
  market_cap = Column(DECIMAL(24, 2), nullable=True, comment="시가총액")
  shares_outstanding = Column(BigInteger, nullable=True, comment="발행주식수")

  # 파티셔닝 설정
  __table_args__ = (
    Index('idx_daily_price_date_desc', 'trade_date', postgresql_using='btree'),
    Index('idx_daily_price_stock_date_desc', 'stock_id', 'trade_date', postgresql_using='btree'),
    { "postgresql_partition_by": "RANGE (trade_date)" }
  )

  # 관계 설정
  stock = relationship("Stock", back_populates="daily_prices", lazy="select")

  def __repr__(self) -> str:
    return f"<DailyPrice(stock_id={self.stock_id}, date={self.trade_date})>"


class MinutePrice(TimestampMixin, Base):
  """
  분봉 주가 데이터 테이블 (일별 파티셔닝)
  합성 기본키 사용: (stock_id, datetime)
  """
  __tablename__ = "minute_price"

  stock_id = Column(Integer, ForeignKey("stock.stock_id"), primary_key=True, index=True)
  datetime = Column(DateTime(timezone=True), primary_key=True, index=True, comment="거래시간(UTC)")

  # OHLCV 데이터
  open_price = Column(DECIMAL(18, 6), nullable=False, comment="시가")
  high_price = Column(DECIMAL(18, 6), nullable=False, comment="고가")
  low_price = Column(DECIMAL(18, 6), nullable=False, comment="저가")
  close_price = Column(DECIMAL(18, 6), nullable=False, comment="종가")
  volume = Column(BigInteger, nullable=False, default=0, comment="거래량")
  trading_value = Column(DECIMAL(24, 2), nullable=True, comment="거래대금")

  # 파티셔닝 설정
  __table_args__ = (
    Index('idx_minute_price_datetime_desc', 'datetime', postgresql_using='btree'),
    Index('idx_minute_price_stock_datetime_desc', 'stock_id', 'datetime', postgresql_using='btree'),
    { "postgresql_partition_by": "RANGE (datetime)" }
  )

  # 관계 설정
  stock = relationship("Stock", back_populates="minute_prices", lazy="selectin")

  def __repr__(self) -> str:
    return f"<MinutePrice(stock_id={self.stock_id}, datetime={self.datetime})>"
