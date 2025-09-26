# src/infrastructure/db/session.py
import logging
from typing import Optional, AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config.settings import settings

log = logging.getLogger(__name__)

# 전역 싱글톤 핸들
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
  """모든 ORM 모델이 상속할 베이스 클래스"""


def _create_engine() -> AsyncEngine:
  """AsyncEngine 생성"""
  return create_async_engine(
      settings.postgres_url,
      echo=False,  # SQL 로그 활성/비활성
      pool_pre_ping=True,
      pool_size=10,
      max_overflow=30,
      pool_timeout=30,
      pool_recycle=1800,
      pool_use_lifo=True,
      future=True,
  )


def get_engine() -> AsyncEngine:
  """엔진 싱글톤 반환"""
  global _engine
  if _engine is None:
    _engine = _create_engine()
    log.debug("PostgreSQL AsyncEngine 초기화 완료")
  return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
  """AsyncSession 팩토리 싱글톤 반환(없으면 생성)"""
  global _session_factory
  if _session_factory is None:
    _session_factory = async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,  # 커밋 후에도 객체 사용 가능
        autoflush=False,
    )
  return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
  """
  비동기 데이터베이스 세션 의존성
  FastAPI 의존성 주입에서 사용
  """
  session = get_session_factory()()
  try:
    yield session
  except Exception:
    await session.rollback()
    log.exception("DB 세션 오류로 롤백 수행")
    raise
  finally:
    await session.close()


async def db_ping() -> bool:
  """연결 헬스체크"""
  try:
    async with get_engine().connect() as conn:
      await conn.execute(text("SELECT 1"))
    return True
  except Exception:
    log.exception("DB ping 실패")
    return False


async def create_tables() -> None:
  """서버 기동 시 자동으로 없는 테이블 생성"""
  try:
    # 모든 모델을 import하여 메타데이터에 등록
    from core.models import (
      Market, Sector, Stock, DailyPrice, MinutePrice,
      FinancialStatement, InvestmentIndicator, TechnicalIndicator,
      MarketIndex, DailyIndexPrice, MLRecommendation, DataCollectionLog
    )
    engine = get_engine()
    async with engine.begin() as conn:
      # 모든 테이블 생성 (이미 존재하는 테이블 무시)
      await conn.run_sync(Base.metadata.create_all)
    log.debug("데이터베에스 테이블 생성/확인 완료")
  except Exception:
    log.exception("테이터베이스 테이블 생성 실패")
    raise


async def drop_tables() -> None:
  """모든 테이블 삭제"""
  try:
    from core.models import (
      Market, Sector, Stock, DailyPrice, MinutePrice,
      FinancialStatement, InvestmentIndicator, TechnicalIndicator,
      MarketIndex, DailyIndexPrice, MLRecommendation, DataCollectionLog
    )
    engine = get_engine()
    async with engine.begin() as conn:
      await conn.run_sync(Base.metadata.drop_all)
    log.warning("모든 데이터베이스 테이블 삭제 완료")
  except Exception:
    log.exception("데이터베이스 테이블 삭제 실패")
    raise


async def get_table_info() -> dict[str, list[str]]:
  """현재 데이터베이스 테이블 정보 조회"""
  try:
    engine = get_engine()
    async with engine.connect() as conn:
      # PostgreSQL에서 테이블 목록 조회
      result = await conn.execute(text("""
                                       SELECT table_name
                                       FROM information_schema.tables
                                       WHERE table_schema = 'public'
                                       ORDER BY table_name
                                       """))

      tables = [row[0] for row in result.fetchall()]
      table_info = { }
      for table in tables:
        # 각 테이블의 컬럼 정보 조회
        column_result = await conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position
                """))

        columns = [f"{row[0]} ({row[1]})" for row in column_result.fetchall()]
        table_info[table] = columns

      return table_info

  except Exception:
    log.exception("테이블 정보 조회 실패")
    raise
