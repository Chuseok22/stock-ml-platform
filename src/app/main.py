# src/app/main.py
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI

from app.routers.db import router as db_router
from app.routers.health import router as health_router
from app.routers.scheduler import router as scheduler_router
from config.settings import settings
from core.models import MarketType
from infrastructure.db.session import db_ping, create_tables, get_table_info
from infrastructure.kis.service.token_service import KISTokenService
from infrastructure.market.service.market_service import seed_default_markets
from infrastructure.price.service.price_service import save_daily_prices
from infrastructure.redis.redis_client import RedisClient
from infrastructure.scheduler.manager import manager
from infrastructure.scheduler.registry import load_modules, schedule_registered_jobs
from infrastructure.stock.service.stock_service import seed_kospi_top30

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
  """FastAPI 애플리케이션 시작"""
  # 로깅 초기화
  _init_logger()

  # Postgres 연결 확인 (ping)
  await _init_postgres()

  # Redis 연결 확인 (ping)
  await _init_redis()

  # KIS 토큰 워밍업
  await _init_kis_token()

  # 기본 Market 정보 저장
  await _init_markets()

  # KOSPI stock 데이터 저장
  await _init_kospi_stocks()

  # KOSPI daily_price 데이터 저장
  await _init_kospi_daily_price()

  # 스케줄러 등록
  _init_schedule()
  try:
    yield  # 애플리케이션 실행
  finally:
    manager.shutdown_schedule()
    log.info("[애플리케이션 종료] - 스케줄러 정리 완료")


def _init_logger():
  """로깅 초기화"""
  try:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    log.info("[애플리케이션 시작] 로깅 초기화 완료")
  except Exception:
    log.exception("[애플리케이션 시작] 로깅 초기화 실패")
    raise


async def _init_postgres():
  """Postgres 연결 확인 및 테이블 생성"""
  try:
    # 연결 확인 (ping)
    ok = await db_ping()
    if not ok:
      raise RuntimeError("Postgres DB ping 실패")
    log.info("[애플리케이션 시작] Postgres 초기화 완료")

    # 테이블 생성 (없는 테이블만)
    await create_tables()
    log.info("[애플리케이션 시작] Postgres 테이블 생성/확인 완료")

    # 생성된 테이블 정보 로그
    table_info = await get_table_info()
    log.info(f"[애플리케이션 시작] 현재 테이블 수: {len(table_info)}개")
  except Exception:
    log.exception("[애플리케이션 시작] Postgres 초기화 실패")
    raise


async def _init_redis():
  """Redis 연결 확인"""
  try:
    redis_client = RedisClient()
    await redis_client.ping()
    log.info("[애플리케이션 시작] Redis 연결 확인(ping) 성공")
  except Exception:
    log.exception("[애플리케이션 시작] Redis 연결 실패")
    raise


async def _init_kis_token():
  """KIS 토큰 확인"""
  kis_token_service = KISTokenService()
  try:
    token = await kis_token_service.get_token()
    log.info("[애플리케이션 시작] KIS 토큰 워밍업 완료 (길이=%s)", len(token))
  except Exception:
    log.exception("[애플리케이션 시작] KIS 토큰 워밍업 실패")
    raise


async def _init_markets():
  """기본 Market 데이터 추가"""
  try:
    await seed_default_markets()
    log.info("[애플리케이션 시작] Market 기본 정보 저장 성공")
  except Exception:
    log.exception("[애플리케이션 시작] Market 시드 저장 실패")
    raise


async def _init_kospi_stocks():
  """KOSPI stock 데이터 저장"""
  try:
    upserted = await seed_kospi_top30()
    log.info("[애플리케이션 시작] KOSPI stock 데이터 저장 완료: %s 건", upserted)
  except Exception:
    log.exception("[애플리케이션 시작] KOSPI stock 데이터 저장 실패")
    raise


async def _init_kospi_daily_price():
  """KOSPI daily_price 데이터 저장 (1달 전~현재)"""
  _timezone = ZoneInfo("Asia/Seoul")
  _today = datetime.now(_timezone).date()
  _start = _today - timedelta(days=31)
  try:
    upserted = await save_daily_prices(
        market_codes=[MarketType.KOSPI],
        start=_start,
        end=_today
    )
    log.info("[애플리케이션 시작] KOSPI 일봉 초기 저장 완료: %s 건 (%s ~ %s)", upserted, _start, _today)
  except Exception:
    log.exception("[애플리케이션 시작] KOSPI 일봉 초기 저장 실패")
    raise


def _init_schedule():
  try:
    # 스케줄러 Job 모듈 로드
    load_modules([
      "job.kis_scheduler"
    ])

    # 등록된 Job들을 스케줄러에 추가
    schedule_registered_jobs()

    # 스케줄러 시작
    manager.start_schedule()
    log.info("[애플리케이션 시작] 스케줄러 활성화 완료")
  except Exception:
    log.exception("[애플리케이션 시작] 스케줄러 등록 실패")
    raise


app = FastAPI(
    title=os.getenv("APP_NAME", "stock-ml-platform"),
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(db_router)
app.include_router(scheduler_router)
