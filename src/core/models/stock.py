# src/core/models/stock.py
"""
주식 기본 정보 모델
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, DECIMAL, BigInteger, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin
from infrastructure.db.session import Base


class Stock(TimestampMixin, Base):
  """주식 기본 정보 테이블"""
  __tablename__ = "stock"

  stock_id = Column(Integer, primary_key=True, index=True)
  ticker = Column(String(20), nullable=False, index=True, comment="종목코드")
  market_id = Column(Integer, ForeignKey("market.market_id"), nullable=False, index=True)
  stock_name = Column(String(200), nullable=False, comment="종목명(한글)")
  stock_name_en = Column(String(200), nullable=True, comment="종목명(영문)")
  sector_id = Column(Integer, ForeignKey("sector.sector_id"), nullable=True, index=True)

  # 상장 정보
  listing_date = Column(Date, nullable=True, comment="상장일")
  listing_shares = Column(BigInteger, nullable=True, comment="상장주식수")
  face_value = Column(DECIMAL(18, 6), nullable=True, comment="액면가")

  # 상태 정보
  is_active = Column(Boolean, default=True, nullable=False, comment="거래 가능 여부")
  delisting_date = Column(Date, nullable=True, comment="상장폐지일")

  # 추가 정보
  description = Column(Text, nullable=True, comment="기업 설명")
  website = Column(String(200), nullable=True, comment="기업 웹사이트")

  # 복합 유니크 제약조건
  __table_args__ = (
    UniqueConstraint('ticker', 'market_id', name='uq_stock_ticker_market'),
  )

  # 관계 설정 (lazy="selectin"으로 변경)
  market = relationship("Market", back_populates="stocks", lazy="selectin")
  sector = relationship("Sector", back_populates="stocks", lazy="selectin")

  # 가격 데이터
  daily_prices = relationship("DailyPrice", back_populates="stock", lazy="selectin", passive_deletes=True)
  minute_prices = relationship("MinutePrice", back_populates="stock", lazy="selectin", passive_deletes=True)

  # 재무 데이터
  financial_statements = relationship("FinancialStatement", back_populates="stock", lazy="selectin")
  investment_indicators = relationship("InvestmentIndicator", back_populates="stock", lazy="selectin")

  # 기술적 지표
  technical_indicators = relationship("TechnicalIndicator", back_populates="stock", lazy="selectin",
                                      passive_deletes=True)

  # ML 추천
  ml_recommendations = relationship("MLRecommendation", back_populates="stock", lazy="selectin")

  def __repr__(self) -> str:
    return f"<Stock(id={self.stock_id}, ticker={self.ticker})>"
