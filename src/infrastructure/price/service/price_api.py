# src/infrastructure/price/service/price_api.py
from datetime import date
from typing import List

from infrastructure.kis.http.http_client import KISClient
from infrastructure.price.dto.daily_price_dto import to_daily_price_dtos, DailyPriceDTO


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
