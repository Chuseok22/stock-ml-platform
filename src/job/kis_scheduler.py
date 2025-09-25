# src/job/kis_scheduler.py
import logging

from infrastructure.kis.service.token_service import KISTokenService
from infrastructure.scheduler.registry import scheduled_cron

log = logging.getLogger(__name__)


@scheduled_cron(
    id="kis_token.refresh",
    hour=0, minute=0, second=0,  # 매일 00:00:00
    replace_existing=True,  # 동일 ID가 있으면 교체 (중복 등록 방지)
    max_instances=1,  # 중복 실행 방지
    misfire_grace_time=600  # 누락된 트리거는 10분 이내 복구 허용
)
async def refresh_kis_token_job() -> None:
  """
  매일 자정 KIS 토큰 재발급 후 Redis TTL 저장
  실패해도 스케줄러는 계속 동작, 다음 트리거에서 재시도
  """
  kis_token_service = KISTokenService()
  try:
    await kis_token_service.issue_and_save_token()
    ttl = await kis_token_service.get_ttl()
    log.info("[KIS] 토큰 재발급 스케줄러 실행 (ttl=%s)", ttl)
  except Exception as e:
    # 여기서 예외를 삼키고 로깅만 하면, 스케줄러 계속 실행 가능
    log.exception("[KIS] 토큰 재발급 실패")
