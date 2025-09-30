# src/infrastructure/price/dto/daily_price_dto.py
from dataclasses import dataclass
from datetime import date
from typing import Optional, List

from pydantic import BaseModel, Field

from utils.decimal_util import to_date8, to_float, to_int


class ResponseHeader(BaseModel):
  # content-type → 파이썬 속성명은 content_type로, 입력 alias는 'content-type' 사용
  content_type: Optional[str] = Field(default=None, alias="content-type")
  tr_id: str
  tr_cont: Optional[str] = None
  gt_uid: Optional[str] = None

  model_config = {
    "populate_by_name": True,
    "extra": "ignore",
  }


class ResponseBodyOutput2(BaseModel):
  stck_bsop_date: str
  stck_clpr: str
  stck_oprc: str
  stck_hgpr: str
  stck_lwpr: str
  acml_vol: str
  acml_tr_pbmn: str
  flng_cls_code: str
  prtt_rate: str
  mod_yn: str
  prdy_vrss_sign: str
  prdy_vrss: str
  revl_issu_reas: str

  model_config = { "extra": "ignore" }


class KISDomesticDailyResponse(BaseModel):
  """KIS 응답 최상위 래퍼"""
  rt_cd: Optional[str] = None
  msg_cd: Optional[str] = None
  msg1: Optional[str] = None
  output2: List[ResponseBodyOutput2] = Field(default_factory=list)

  model_config = { "extra": "ignore" }


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


# ------------------------- DTO 변환기 -------------------------
# 우리 시스템 내부 표준 DTO (이미 기존 코드에서 사용 중)

def to_daily_price_dtos(ticker: str, payload: dict) -> List[DailyPriceDTO]:
  """
  KIS 원시 payload(dict) → 파싱 → DailyPriceDTO 리스트로 변환
  - output2 배열(일자별)을 순회하며 DTO 작성
  """
  parsed = KISDomesticDailyResponse.model_validate(payload)

  out: List[DailyPriceDTO] = []
  for row in parsed.output2:
    d = to_date8(row.stck_bsop_date)
    out.append(
        DailyPriceDTO(
            ticker=ticker,
            trade_date=d,
            open_price=to_float(row.stck_oprc) or 0.0,
            high_price=to_float(row.stck_hgpr) or 0.0,
            low_price=to_float(row.stck_lwpr) or 0.0,
            close_price=to_float(row.stck_clpr) or 0.0,
            volume=to_int(row.acml_vol) or 0,
            trading_value=to_float(row.acml_tr_pbmn),
            # output2에는 등락률이 없고 등락금액(prdy_vrss)/부호만 있음 → 등락률은 None 처리
            adjusted_close=None,
            change_rate=None,
            # 부호 반영하여 등락금액 계산(부호: 1/2/3 ? API 문서 기준으로 맵핑 필요 시 보정)
            change_amount=to_float(row.prdy_vrss),
            market_cap=None,
            shares_outstanding=None,
        )
    )
  return out
