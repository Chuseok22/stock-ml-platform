import importlib
import logging
from typing import Any, Callable

from apscheduler.triggers.cron import CronTrigger

from infrastructure.scheduler.manager import JobSpec, manager

log = logging.getLogger(__name__)

_REGISTRY: list[JobSpec] = []


def scheduled_cron(
    *,
    id: str,
    second: int | str = 0,
    minute: int | str = 0,
    hour: int | str = 0,
    day: int | str | None = None,
    day_of_week: int | str | None = None,
    month: int | str | None = None,
    **add_job_options: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
  """
  Cron 스케줄 데코레이터
  사용 예:
      @scheduled_cron(id="kis.token.refresh", hour=0, minute=0, second=0,
                      max_instances=1, misfire_grace_time=600)
      async def refresh_kis_token(): ...

  Params:
      id: 잡 식별자(고유 문자열)
      second, minute, hour, day, day_of_week, month:
          Cron 필드 값(정수 또는 문자열 표현 '*', '*/5' 등)
      **add_job_opts:
          APScheduler add_job 옵션 (replace_existing, max_instances, 등)
          예) replace_existing=True, max_instances=1, misfire_grace_time=600
  Returns:
      원본 함수를 그대로 반환(장식만 함).
  """

  def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    trigger = CronTrigger(
        second=second, minute=minute, hour=hour,
        day=day, day_of_week=day_of_week, month=month,
        timezone=manager.timezone,  # 매니저의 타임존 사용
    )
    # 나중에 일괄 등록할 수 있도록 레지스트리에 스펙 추가
    _REGISTRY.append(JobSpec(id=id, func=func, trigger=trigger, kwargs=add_job_options))
    return func

  return _decorator


def load_modules(module_paths: list[str]) -> None:
  """
  잡 모듈들을 import하여, 모듈 내 데코레이터가 실행되게 한다.

  Args:
      module_paths: import할 모듈 경로 리스트 (예: ["src.jobs.kis", "src.jobs.notify"])
  """
  for m in module_paths:
    importlib.import_module(m)
    log.debug("Job 모듈 import 완료: %s", m)


def schedule_registered_jobs() -> None:
  """
  데코레이터로 등록된 모든 잡(JobSpec)을 스케줄러에 실제로 add_job 한다.
  """
  for spec in _REGISTRY:
    manager.get_schedule().add_job(manager._wrap(spec.func), trigger=spec.trigger,
                                   id=spec.id, **spec.kwargs)
    log.info("Job 스케줄링 등록 id=%s", spec.id)
