# src/core/models/technical.py
"""
기술적 지표 모델 (파티셔닝 적용)
"""
from sqlalchemy import Column, Integer, Date, DECIMAL, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin
from infrastructure.db.session import Base


class TechnicalIndicator(TimestampMixin, Base):
  """
  기술적 지표 테이블 (월별 파티셔닝)
  합성 기본키 사용: (stock_id, trade_date)
  """
  __tablename__ = "technical_indicator"

  stock_id = Column(Integer, ForeignKey("stock.stock_id", ondelete="CASCADE"), primary_key=True, index=True)
  trade_date = Column(Date, primary_key=True, index=True, comment="거래일")

  # 이동평균 지표
  sma_5 = Column(DECIMAL(18, 6), nullable=True, comment="5일 단순이동평균")
  sma_20 = Column(DECIMAL(18, 6), nullable=True, comment="20일 단순이동평균")
  sma_60 = Column(DECIMAL(18, 6), nullable=True, comment="60일 단순이동평균")
  sma_120 = Column(DECIMAL(18, 6), nullable=True, comment="120일 단순이동평균")
  ema_12 = Column(DECIMAL(18, 6), nullable=True, comment="12일 지수이동평균")
  ema_26 = Column(DECIMAL(18, 6), nullable=True, comment="26일 지수이동평균")

  # 모멘텀 지표
  rsi_14 = Column(DECIMAL(8, 4), nullable=True, comment="14일 RSI")
  macd = Column(DECIMAL(18, 6), nullable=True, comment="MACD")
  macd_signal = Column(DECIMAL(18, 6), nullable=True, comment="MACD Signal")
  macd_histogram = Column(DECIMAL(18, 6), nullable=True, comment="MACD Histogram")

  # 변동성 지표 (볼린저 밴드)
  bollinger_upper = Column(DECIMAL(18, 6), nullable=True, comment="볼린저밴드 상단")
  bollinger_middle = Column(DECIMAL(18, 6), nullable=True, comment="볼린저밴드 중간")
  bollinger_lower = Column(DECIMAL(18, 6), nullable=True, comment="볼린저밴드 하단")

  # 거래량 지표
  volume_sma_20 = Column(BigInteger, nullable=True, comment="20일 거래량 이동평균")
  volume_ratio = Column(DECIMAL(8, 4), nullable=True, comment="거래량 비율")

  # 추가 지표들
  stochastic_k = Column(DECIMAL(8, 4), nullable=True, comment="스토캐스틱 %K")
  stochastic_d = Column(DECIMAL(8, 4), nullable=True, comment="스토캐스틱 %D")
  williams_r = Column(DECIMAL(8, 4), nullable=True, comment="윌리엄스 %R")
  cci = Column(DECIMAL(18, 6), nullable=True, comment="상품채널지수")

  # 추세 지표
  adx = Column(DECIMAL(8, 4), nullable=True, comment="평균방향지수")
  aroon_up = Column(DECIMAL(8, 4), nullable=True, comment="아룬업")
  aroon_down = Column(DECIMAL(8, 4), nullable=True, comment="아룬다운")

  # 파티셔닝 설정 및 인덱스
  __table_args__ = (
    Index('idx_technical_date_desc', 'trade_date', postgresql_using='btree'),
    Index('idx_technical_stock_date_desc', 'stock_id', 'trade_date', postgresql_using='btree'),
    { "postgresql_partition_by": "RANGE (trade_date)" }
  )

  # 관계 설정
  stock = relationship("Stock", back_populates="technical_indicators", lazy="selectin")

  def __repr__(self) -> str:
    return f"<TechnicalIndicator(stock_id={self.stock_id}, date={self.trade_date})>"
