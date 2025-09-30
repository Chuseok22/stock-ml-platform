# src/core/models/financial.py
"""
재무제표 및 투자지표 모델
"""
from sqlalchemy import Column, Integer, Date, DECIMAL, ForeignKey, UniqueConstraint, Enum as SQLEnum, Text, Index
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin, PeriodType
from infrastructure.db.session import Base


class FinancialStatement(TimestampMixin, Base):
  """재무제표 데이터 테이블"""
  __tablename__ = "financial_statement"

  financial_id = Column(Integer, primary_key=True, index=True)
  stock_id = Column(Integer, ForeignKey("stock.stock_id"), nullable=False, index=True)
  report_date = Column(Date, nullable=False, index=True, comment="보고서 기준일")
  period_type = Column(
      SQLEnum(PeriodType, name="period_type", native_enum=True),
      nullable=False, comment="기간 구분"
  )
  fiscal_year = Column(Integer, nullable=False, comment="회계연도")

  # 손익계산서 (단위: 원)
  revenue = Column(DECIMAL(24, 2), nullable=True, comment="매출액")
  operating_income = Column(DECIMAL(24, 2), nullable=True, comment="영업이익")
  ebitda = Column(DECIMAL(24, 2), nullable=True, comment="EBITDA")
  net_income = Column(DECIMAL(24, 2), nullable=True, comment="순이익")
  eps = Column(DECIMAL(18, 6), nullable=True, comment="주당순이익")

  # 재무상태표 (단위: 원)
  total_assets = Column(DECIMAL(24, 2), nullable=True, comment="총자산")
  current_assets = Column(DECIMAL(24, 2), nullable=True, comment="유동자산")
  non_current_assets = Column(DECIMAL(24, 2), nullable=True, comment="비유동자산")
  total_liabilities = Column(DECIMAL(24, 2), nullable=True, comment="총부채")
  current_liabilities = Column(DECIMAL(24, 2), nullable=True, comment="유동부채")
  shareholders_equity = Column(DECIMAL(24, 2), nullable=True, comment="자본총계")

  # 현금흐름표 (단위: 원)
  operating_cash_flow = Column(DECIMAL(24, 2), nullable=True, comment="영업현금흐름")
  investing_cash_flow = Column(DECIMAL(24, 2), nullable=True, comment="투자현금흐름")
  financing_cash_flow = Column(DECIMAL(24, 2), nullable=True, comment="재무현금흐름")
  free_cash_flow = Column(DECIMAL(24, 2), nullable=True, comment="잉여현금흐름")

  # 추가 정보
  notes = Column(Text, nullable=True, comment="특이사항")

  # 복합 유니크 제약조건
  __table_args__ = (
    UniqueConstraint('stock_id', 'report_date', 'period_type', name='uq_financial_stock_date_period'),
    Index("idx_financial_stock_report_date", "stock_id", "report_date"),
  )

  # 관계 설정
  stock = relationship("Stock", back_populates="financial_statements", lazy="select")

  def __repr__(self) -> str:
    return f"<FinancialStatement(id={self.financial_id}, stock_id={self.stock_id})>"


class InvestmentIndicator(TimestampMixin, Base):
  """투자지표 테이블"""
  __tablename__ = "investment_indicator"

  investment_id = Column(Integer, primary_key=True, index=True)
  stock_id = Column(Integer, ForeignKey("stock.stock_id"), nullable=False, index=True)
  report_date = Column(Date, nullable=False, index=True, comment="기준일")

  # 밸류에이션 지표
  per = Column(DECIMAL(18, 6), nullable=True, comment="주가수익비율")
  pbr = Column(DECIMAL(18, 6), nullable=True, comment="주가순자산비율")
  pcr = Column(DECIMAL(18, 6), nullable=True, comment="주가현금흐름비율")
  psr = Column(DECIMAL(18, 6), nullable=True, comment="주가매출비율")
  ev_ebitda = Column(DECIMAL(18, 6), nullable=True, comment="EV/EBITDA")

  # 수익성 지표 (%)
  roe = Column(DECIMAL(8, 4), nullable=True, comment="자기자본이익률(%)")
  roa = Column(DECIMAL(8, 4), nullable=True, comment="총자산이익률(%)")
  roic = Column(DECIMAL(8, 4), nullable=True, comment="투하자본이익률(%)")
  gross_margin = Column(DECIMAL(8, 4), nullable=True, comment="매출총이익률(%)")
  operating_margin = Column(DECIMAL(8, 4), nullable=True, comment="영업이익률(%)")
  net_margin = Column(DECIMAL(8, 4), nullable=True, comment="순이익률(%)")

  # 안정성 지표 (%)
  debt_ratio = Column(DECIMAL(8, 4), nullable=True, comment="부채비율(%)")
  current_ratio = Column(DECIMAL(8, 4), nullable=True, comment="유동비율(%)")
  quick_ratio = Column(DECIMAL(8, 4), nullable=True, comment="당좌비율(%)")

  # 배당 지표 (%)
  dividend_yield = Column(DECIMAL(8, 4), nullable=True, comment="배당수익률(%)")
  dividend_payout_ratio = Column(DECIMAL(8, 4), nullable=True, comment="배당성향(%)")

  # 성장성 지표 (%)
  revenue_growth_rate = Column(DECIMAL(8, 4), nullable=True, comment="매출증가율(%)")
  profit_growth_rate = Column(DECIMAL(8, 4), nullable=True, comment="순이익증가율(%)")

  # 복합 유니크 제약조건
  __table_args__ = (
    UniqueConstraint('stock_id', 'report_date', name='uq_investment_stock_date'),
    Index("idx_investment_stock_report_date", "stock_id", "report_date"),
  )

  # 관계 설정
  stock = relationship("Stock", back_populates="investment_indicators", lazy="select")

  def __repr__(self) -> str:
    return f"<InvestmentIndicator(id={self.investment_id}, stock_id={self.stock_id})>"
