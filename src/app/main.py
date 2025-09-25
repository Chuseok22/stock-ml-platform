# src/app/main.py
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    "timezone": str(manager.get_timezone),
    "jobs": jobs
  }
