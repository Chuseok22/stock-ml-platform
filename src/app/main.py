# src/app/main.py
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.settings import settings
from infrastructure.db.session import db_ping
from infrastructure.kis.service.token_service import KISTokenService
from infrastructure.redis.redis_client import RedisClient
from infrastructure.scheduler.manager import manager
from infrastructure.scheduler.registry import load_modules, schedule_registered_jobs

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
  """Postgres 연결 확인"""
  try:
    ok = await db_ping()
    if not ok:
      raise RuntimeError("Postgres DB ping 실패")
    log.info("[애플리케이션 시작] Postgres 초기화 완료")
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


@app.get("/health")
async def health():
  return { "status": "ok", "message": "시스템이 정상적으로 작동중입니다." }


@app.get("/scheduler/status")
async def scheduler_status():
  """스케줄러 상태 확인 엔드포인트"""
  scheduler = manager.get_schedule()
  jobs = []

  for job in scheduler.get_jobs():
    jobs.append({
      "id": job.id,
      "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
      "trigger": str(job.trigger)
    })
  return {
    "scheduler_running": scheduler.running,
    "timezone": str(manager.timezone),
    "jobs": jobs
  }
