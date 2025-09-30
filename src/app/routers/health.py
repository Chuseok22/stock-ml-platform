# src/app/routers/health.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
  return { "status": "ok", "message": "시스템이 정상적으로 작동중입니다." }
