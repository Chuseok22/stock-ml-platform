# src/infrastructure/scheduler/manager.py
import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional, Coroutine
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobSpec:
  """
  Job 등록 시 내부적으로 사용하는 구조체

  Attributes:
    id: Job 고유 식별자 ex) "kis.token.refresh.midnight"
    func: 실행할 콜러블(동기/비동기 모두 가능)
    trigger: APScheduler 트리거 (CronTrigger, IntervalTrigger 등)
    kwargs: add_job 시 전달할 부가 옵션들 (ex. max_instances, misfire_grace_time)
  """
  id: str
  func: Callable[..., Any]
  trigger: Any
  kwargs: dict[str, Any]


class SchedulerManager:
  """스케줄러 수명주기/등록 메니저"""

  def __init__(self, tz: str = "Asia/Seoul") -> None:
    self._tz = ZoneInfo(tz)
    self._scheduler: Optional[AsyncIOScheduler] = None

  @property
  def timezone(self) -> ZoneInfo:
    """타임존 반환"""
    return self._tz

  def get_schedule(self) -> AsyncIOScheduler:
    """싱글톤 AsyncIOScheduler 인스턴스 획득 (없으면 생성)"""
    if self._scheduler is None:
      self._scheduler = AsyncIOScheduler(timezone=self._tz)
    return self._scheduler

  def start_schedule(self) -> None:
    """스케줄러 시작"""
    schedule = self.get_schedule()
    if not schedule.running:
      schedule.start()
      log.info("스케줄러 시작 (time-zone=%s)", self._tz)

  def shutdown_schedule(self) -> None:
    """스케줄러 종료"""
    schedule = self.get_schedule()
    if schedule.running:
      schedule.shutdown(wait=False)
      log.info("작동중인 스케줄러 정지")

  def add_cron(
      self,
      func: Callable[..., Any],
      *,
      id: str,
      second: int | str = 0,
      minute: int | str = 0,
      hour: int | str = 0,
      day: int | str | None = None,
      day_of_week: int | str | None = None,
      month: int | str | None = None,
      replace_existing: bool = True,
      max_instances: int = 1,
      misfire_grace_time: int = 600,
      **kwargs: Any,
  ) -> None:
    """
    Cron 등록 헬퍼
    :param func: 실행할 함수
    :param id: Job 고유 식별자
    :param replace_existing: 이미 동일 id가 있다면 교체 여부
    :param max_instances: 동시에 실행 가능한 인스턴스 수 (중복 실행 방지)
    :param misfire_grace_time: 누락된 트리거 발생 시 허용 지연 (초)
    :param kwargs: apscheduler.add_job 에 전달할 추가 옵션
    """
    trigger = CronTrigger(
        second=second, minute=minute, hour=hour,
        day=day, day_of_week=day_of_week, month=month,
        timezone=self._tz,
    )
    self._add_job(func, id=id, trigger=trigger,
                  replace_existing=replace_existing,
                  max_instances=max_instances,
                  misfire_grace_time=misfire_grace_time,
                  **kwargs)

  def add_interval(
      self,
      func: Callable[..., Any],
      *,
      id: str,
      seconds: int = 0,
      minutes: int = 0,
      hours: int = 0,
      replace_existing: bool = True,
      max_instances: int = 1,
      misfire_grace_time: int = 600,
      **kwargs: Any,
  ) -> None:
    """
    일정 간격으로 반복되는 Job 등록
    :param func: 실행할 함수 (동기/비동기)
    :param id: Job 고유 식별자
    :param replace_existing: 이미 동일 id가 있다면 교체 여부
    :param max_instances: 동시에 실행 가능한 인스턴스 수 (중복 실행 방지)
    :param misfire_grace_time: 누락된 트리거 발생 시 허용 지연 (초)
    :param kwargs: apscheduler.add_job 에 전달할 추가 옵션
    """
    trigger = IntervalTrigger(
        seconds=seconds, minutes=minutes, hours=hours, timezone=self._tz
    )
    self._add_job(func, id=id, trigger=trigger,
                  replace_existing=replace_existing,
                  max_instances=max_instances,
                  misfire_grace_time=misfire_grace_time,
                  **kwargs)

  def _wrap(self, func: Callable[..., Any]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    sync 함수도 event loop를 막지 않도록 thread로 돌려주는 헬퍼
    :param func: 실행할 함수 (동기/비동기)
    :return: 비동기(awaitable) 함수로 감싼 Callable
    """
    if inspect.iscoroutinefunction(func):
      # 이미 async 함수면 그대로 사용
      return func

    async def _runner(*args: Any, **kwargs: Any) -> Any:
      # 동기 함수는 별도 스레드에서 실행하여 event loop 블로킹 방지
      return await asyncio.to_thread(func, *args, **kwargs)

    return _runner

  def _add_job(self, func: Callable[..., Any], *, id: str, trigger: Any, **options: Any) -> None:
    """Job 추가 메서드"""
    schedule = self.get_schedule()
    wrapped = self._wrap(func)
    schedule.add_job(wrapped, trigger=trigger, id=id, **options)
    log.info("스케줄러 Job 등록 성공. id=%s, trigger=%s, options=%s",
             id, trigger, { k: v for k, v in options.items() if k in ("max_instances", "misfire_grace_time",) })


# 외부에서 바로 import 가능하도록 싱글톤 인스턴스 노출
manager = SchedulerManager(tz="Asia/Seoul")
