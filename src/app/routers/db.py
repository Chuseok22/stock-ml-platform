# src/app/routers/db.py
import logging
from typing import Any

from fastapi import APIRouter

from infrastructure.db.session import get_table_info

log = logging.getLogger(__name__)
router = APIRouter(prefix="/db", tags=["database"])


@router.get("/tables")
async def get_database_tables() -> dict[str, Any]:
  """데이터베이스 테이블 정보 조회 엔드포인트"""
  try:
    table_info = await get_table_info()
    return {
      "table_count": len(table_info),
      "tables": table_info
    }
  except Exception as e:
    log.exception("테이블 정보 조회 실패")
    return {
      "error": str(e)
    }
