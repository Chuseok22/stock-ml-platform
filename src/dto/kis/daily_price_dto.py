# src/dto/kis/daily_price_dto.py
from typing import Optional, List

from pydantic import BaseModel, Field

from infrastructure.kis.service.price_api import DailyPriceDTO
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


class ResponseBodyOutput1(BaseModel):
  # 모든 원본은 문자열로 들어오므로 str 타입 유지 (숫자필요시 변환은 변환기에서 수행)
  prdy_vrss: str
  prdy_vrss_sign: str
  prdy_ctrt: str
  stck_prdy_clpr: str
  acml_vol: str
  acml_tr_pbmn: str
  hts_kor_isnm: str
  stck_prpr: str
  stck_shrn_iscd: str
  prdy_vol: str
  stck_mxpr: str
  stck_llam: str
  stck_oprc: str
  stck_hgpr: str
  stck_lwpr: str
  stck_prdy_oprc: str
  stck_prdy_hgpr: str
  stck_prdy_lwpr: str
  askp: str
  bidp: str
  prdy_vrss_vol: str
  vol_tnrt: str
  stck_fcam: str
  lstn_stcn: str
  cpfn: str
  hts_avls: str
  per: str
  eps: str
  pbr: str
  itewhol_loan_rmnd_ratem: str

  model_config = { "extra": "ignore" }


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


class ResponseBody(BaseModel):
  rt_cd: str
  msg_cd: str
  msg1: str
  output1: ResponseBodyOutput1
  output2: List[ResponseBodyOutput2] = Field(default_factory=list)

  model_config = { "extra": "ignore" }


class KISDomesticDailyResponse(BaseModel):
  """
  KIS 응답 최상위 래퍼 (보통 header/body 구조)
  일부 API는 header가 없을 수도 있으니 optional 처리.
  """
  header: Optional[ResponseHeader] = None
  body: ResponseBody

  model_config = { "extra": "ignore" }


# ------------------------- DTO 변환기 -------------------------
# 우리 시스템 내부 표준 DTO (이미 기존 코드에서 사용 중)

def to_daily_price_dtos(ticker: str, payload: dict) -> List[DailyPriceDTO]:
  """
  KIS 원시 payload(dict) → 파싱 → DailyPriceDTO 리스트로 변환
  - output2 배열(일자별)을 순회하며 DTO 작성
  """
  parsed = KISDomesticDailyResponse.model_validate(payload)

  out: List[DailyPriceDTO] = []
  for row in parsed.body.output2:
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
