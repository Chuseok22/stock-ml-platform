# src/infrastructure/kis/service/stock_mst_parser.py
import decimal
import io
from dataclasses import dataclass
from datetime import date
from typing import Optional, List

import pandas as pd

from utils.decimal_util import to_date8, to_decimal, to_int
from utils.string_util import clean_str


@dataclass(frozen=True)
class StockSeed:
  ticker: str
  stock_name: str
  listing_date: Optional[date]
  face_value: Optional[decimal]
  listing_shares: Optional[int]


def parse_kospi_mst(filepath: str) -> List[StockSeed]:
  """
  kospi_code.mst 파일을 파싱하여 StockSeed 리스트로 변환
  - 인코딩: CP949
  """
  tmp1, tmp2 = [], []
  with open(filepath, mode="r", encoding="cp949") as file:
    for row in file:
      head = row[0:len(row) - 228]  # 앞부분: 코드/이름
      tail = row[-228:]  # 뒷부분: 고정폭 필드

      rf1_1 = head[0:9].rstrip()  # 단축코드
      rf1_2 = head[9:21].rstrip()  # 표준코드
      rf1_3 = head[21:].rstrip()  # 한글명
      tmp1.append((rf1_1, rf1_2, rf1_3))

      tmp2.append(tail)

    df1 = pd.DataFrame(tmp1, columns=["단축코드", "표준코드", "한글명"])

    # 고정폭 스펙
    field_specs = [
      2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
      1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
      1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
      9, 5, 5, 1, 1, 1, 2, 1, 1, 1,
      2, 2, 2, 3, 1, 3, 12, 12, 8, 15,
      21, 2, 7, 1, 1, 1, 1, 9, 9, 9,
      5, 9, 8, 9, 3, 1, 1, 1
    ]
  part2_columns = [
    '그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류',
    '제조업', '저유동성', '지배구조지수종목', 'KOSPI200섹터업종', 'KOSPI100',
    'KOSPI50', 'KRX', 'ETP', 'ELW발행', 'KRX100',
    'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC',
    'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설',
    'Non1', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송',
    'SRI', '기준가', '매매수량단위', '시간외수량단위', '거래정지',
    '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',
    '우회상장', '락구분', '액면변경', '증자구분', '증거금비율',
    '신용가능', '신용기간', '전일거래량', '액면가', '상장일자',
    '상장주수', '자본금', '결산월', '공모가', '우선주',
    '공매도과열', '이상급등', 'KRX300', 'KOSPI', '매출액',
    '영업이익', '경상이익', '당기순이익', 'ROE', '기준년월',
    '시가총액', '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능'
  ]

  df2 = pd.read_fwf(
      io.StringIO("".join(tmp2)),
      widths=field_specs,
      names=part2_columns,
      dtype=str,
  )

  df = pd.concat([df1, df2], axis=1)

  seeds: List[StockSeed] = []
  for _, r in df.iterrows():
    ticker = clean_str(r.get("단축코드"))
    name = clean_str(r.get("한글명"))
    if not ticker or not name:
      continue

    listing_date = to_date8(r.get("상장일자"))
    face_value = to_decimal(r.get("액면가"))
    shares_thousand = to_int(r.get("상장주수"))  # "천 주" 단위
    listing_shares = shares_thousand * 1000 if shares_thousand else None

    seeds.append(
        StockSeed(
            ticker=ticker,
            stock_name=name,
            listing_date=listing_date,
            face_value=face_value,
            listing_shares=listing_shares,
        )
    )
  return seeds
