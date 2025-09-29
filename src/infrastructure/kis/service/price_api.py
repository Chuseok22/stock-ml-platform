# src/infrastructure/kis/service/price_api.py
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from dto.kis.daily_price_dto import to_daily_price_dtos
from infrastructure.kis.http.http_client import KISClient


@dataclass(frozen=True)
class DailyPriceDTO:
  """
  DB upsert에 바로 넣기 위한 표준 스키마
  """
  ticker: str
  trade_date: date
  open_price: float
  high_price: float
  low_price: float
  close_price: float
  volume: int
  trading_value: Optional[float] = None
  adjusted_close: Optional[float] = None
  change_rate: Optional[float] = None
  change_amount: Optional[float] = None
  market_cap: Optional[float] = None
  shares_outstanding: Optional[int] = None


class KISPriceAPI:
  """
  KIS API 래퍼
  """

  def __init__(self, client: KISClient) -> None:
    self._client = client

  async def fetch_domestic_daily(
      self, *, ticker: str, start: date, end: date
  ) -> List[DailyPriceDTO]:
    """국내 일봉(일자 구간)조회 -> DailyPriceDTO 리스트 변환"""
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    tr_id = "FHKST03010100"

    params = {
      "FID_COND_MRKT_DIV_CODE": "J",
      "FID_INPUT_ISCD": ticker,
      "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
      "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
      "FID_PERIOD_DIV_CODE": "D",
      "FID_ORG_ADJ_PRC": "0"
    }

    response = await self._client.get(path, tr_id=tr_id, auth=True, params=params)

    return to_daily_price_dtos(ticker, response)
