# src/app/routers/scheduler.py
from fastapi import APIRouter

from infrastructure.scheduler.manager import manager

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
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
