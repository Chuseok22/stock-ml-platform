# src/core/models/recommendation.py
"""
ML 추천 결과 모델
"""
from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey, UniqueConstraint, Text, Enum as SQLEnum, \
  Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.models.base import TimestampMixin, RecommendationType
from infrastructure.db.session import Base


class MLRecommendation(TimestampMixin, Base):
  """ML 추천 결과 테이블"""
  __tablename__ = "ml_recommendation"

  recommendation_id = Column(Integer, primary_key=True, index=True)
  recommendation_date = Column(Date, nullable=False, index=True, comment="추천일")
  stock_id = Column(Integer, ForeignKey("stock.stock_id"), nullable=False, index=True)

  # 모델 정보
  model_name = Column(String(100), nullable=False, comment="ML 모델명")
  model_version = Column(String(50), nullable=False, comment="모델 버전")

  # 추천 정보
  prediction_type = Column(
      SQLEnum(RecommendationType, name="recommendation_type", native_enum=True),
      nullable=False, comment="추천 유형"
  )
  confidence_score = Column(DECIMAL(8, 4), nullable=False, comment="신뢰도 (0~1)")
  expected_return = Column(DECIMAL(8, 4), nullable=True, comment="예상수익률(%)")
  risk_score = Column(DECIMAL(8, 4), nullable=True, comment="위험점수 (0~1)")

  # 추천 근거
  recommendation_reason = Column(Text, nullable=True, comment="추천 사유")
  features_used = Column(JSONB, nullable=True, comment="사용된 특성들 JSON")
  feature_importance = Column(JSONB, nullable=True, comment="특성 중요도 JSON")

  # 백테스트 정보
  backtest_accuracy = Column(DECIMAL(8, 4), nullable=True, comment="백테스트 정확도")
  sharpe_ratio = Column(DECIMAL(8, 4), nullable=True, comment="샤프 비율")

  # 복합 유니크 제약조건
  __table_args__ = (
    UniqueConstraint('recommendation_date', 'stock_id', 'model_name', name='uq_recommendation_date_stock_model'),
    Index("idx_reco_date_model", "recommendation_date", "model_name"),
  )

  # 관계 설정
  stock = relationship("Stock", back_populates="ml_recommendations", lazy="selectin")

  def __repr__(self) -> str:
    return f"<MLRecommendation(id={self.recommendation_id}, stock_id={self.stock_id})>"
