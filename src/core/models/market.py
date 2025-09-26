# src/core/models/market.py
"""
시장 및 섹터 관련 모델
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin, MarketType, CurrencyType, CountryCode, SectorLevel
from infrastructure.db.session import Base


class Market(TimestampMixin, Base):
  """시장 정보 테이블"""
  __tablename__ = "market"

  market_id = Column(Integer, primary_key=True, index=True)
  market_code = Column(
      SQLEnum(MarketType, name="market_type", native_enum=True),
      unique=True, nullable=False, index=True
  )
  market_name = Column(String(100), nullable=False, comment="시장명")
  country_code = Column(
      SQLEnum(CountryCode, name="country_code", native_enum=True),
      nullable=False
  )
  currency = Column(
      SQLEnum(CurrencyType, name="currency_type", native_enum=True),
      nullable=False
  )
  timezone = Column(String(50), nullable=False, comment="시장 타임존")
  trading_hours = Column(JSONB, nullable=False, comment="거래시간 정보 JSON")
  description = Column(Text, nullable=True, comment="시장 설명")

  # 관계 설정
  stocks = relationship("Stock", back_populates="market", lazy="selectin")
  indices = relationship("MarketIndex", back_populates="market", lazy="selectin")

  def __repr__(self) -> str:
    return f"<Market(id={self.market_id}, code={self.market_code.value})>"


class Sector(TimestampMixin, Base):
  """섹터/산업 분류 테이블"""
  __tablename__ = "sector"

  sector_id = Column(Integer, primary_key=True, index=True)
  sector_code = Column(String(20), unique=True, nullable=False, index=True)
  sector_name = Column(String(100), nullable=False, comment="섹터명")
  sector_name_en = Column(String(100), nullable=True, comment="섹터명(영문)")
  parent_sector_id = Column(Integer, ForeignKey("sector.sector_id"), nullable=True)
  level = Column(
      SQLEnum(SectorLevel, name="sector_level", native_enum=True),
      nullable=False, default=SectorLevel.MAJOR
  )
  description = Column(Text, nullable=True, comment="섹터 설명")

  # 자기 참조 관계
  parent = relationship("Sector", remote_side="Sector.sector_id", back_populates="children")
  children = relationship("Sector", back_populates="parent", lazy="selectin")

  # 주식과의 관계
  stocks = relationship("Stock", back_populates="sector", lazy="selectin")

  def __repr__(self) -> str:
    return f"<Sector(id={self.sector_id}, code={self.sector_code})>"
