# src/app/main.py
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.settings import settings
from infrastructure.kis.service.token_service import KISTokenService
from infrastructure.redis.redis_client import RedisClient
from src.infrastructure.scheduler.manager import manager
from src.infrastructure.scheduler.registry import load_modules, schedule_registered_jobs

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  FastAPI 애플리케이션 생명주기 관리
  - 시작 시: 스케줄러 초기화 및 시작
  - 종료 시: 스케줄러 정리
  """
  # 로깅 초기화
  logging.basicConfig(
      level=settings.log_level,
      format="%(asctime)s %(levelname)s %(name)s - %(message)s",
  )
  log.info("로깅 초기화 완료")

  # Redis 연결 확인 (ping)
  try:
    redis_client = RedisClient()
    await redis_client.ping()
    log.info("Redis 연결 확인(ping) 성공")
  except Exception:
    log.exception("서버 시작 시 Redis 연결 실패")
    raise

  # KIS 토큰 워밍업
  kis_token_service = KISTokenService()
  try:
    token = await kis_token_service.get_token()
    log.info("KIS 토큰 워밍업 완료 (길이=%s)", len(token))
  except Exception:
    log.exception("KIS 토큰 워밍업 실패 (서비스는 계속 작동)")

  try:
    # 스케줄러 Job 모듈 로드
    load_modules([
      "src.job.kis_scheduler"
    ])

    # 등록된 Job들을 스케줄러에 추가
    schedule_registered_jobs()

    # 스케줄러 시작
    manager.start_schedule()
    log.info("애플리케이션 시작 완료 - 스케줄러 활성화")

    yield  # 애플리케이션 실행

  except Exception as e:
    log.error("애플리케이션 시작 중 오류 발생")
    raise
  finally:
    # 애플리케이션 종료 시 스케줄러 정리
    manager.shutdown_schedule()
    log.info("애플리케이션 종료 - 스케줄러 정리")


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
