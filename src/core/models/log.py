# src/core/models/log.py
"""
데이터 수집 로그 모델
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Enum as SQLEnum

from src.core.models.base import TimestampMixin, DataCollectionStatus
from src.infrastructure.db.session import Base


class DataCollectionLog(TimestampMixin, Base):
  """데이터 수집 로그 테이블"""
  __tablename__ = "data_collection_log"

  log_id = Column(Integer, primary_key=True, index=True)
  data_type = Column(String(50), nullable=False, index=True, comment="데이터 유형")
  collection_date = Column(Date, nullable=False, index=True, comment="수집 대상일")

  # 실행 정보
  start_time = Column(DateTime(timezone=True), nullable=False, comment="시작시간(UTC)")
  end_time = Column(DateTime(timezone=True), nullable=True, comment="종료시간(UTC)")
  status = Column(
      SQLEnum(DataCollectionStatus, name="data_collection_status", native_enum=True),
      nullable=False, comment="수집 상태"
  )

  # 결과 정보
  records_collected = Column(Integer, default=0, comment="수집된 레코드 수")
  records_failed = Column(Integer, default=0, comment="실패한 레코드 수")
  error_message = Column(Text, nullable=True, comment="오류 메시지")

  # 추가 정보
  source_api = Column(String(100), nullable=True, comment="데이터 소스 API")
  execution_time_seconds = Column(Integer, nullable=True, comment="실행시간(초)")

  def __repr__(self) -> str:
    return f"<DataCollectionLog(id={self.log_id}, type={self.data_type})>"
