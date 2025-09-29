import logging
import os
import ssl
import urllib.request
import zipfile
from typing import List

from core.models import MarketType
from infrastructure.db.session import get_session
from infrastructure.kis.stock.repository.stock_repository import find_market_id_by_market_code, save_stocks
from infrastructure.kis.stock.service.stock_mst_parser import StockSeed, parse_kospi_mst

log = logging.getLogger(__name__)

KOSPI_ZIP_URL = "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
KOSPI_MST_FILE_NAME = "kospi_code.mst"


async def ingest_kospi_master_from_file(mst_path: str) -> int:
  """KOSPI 마스터(.mst) 파일을 파싱하여 stock 테이블에 저장"""
  # .mst 파일 파싱 -> StockSeed 리스트 생성
  seeds: List[StockSeed] = parse_kospi_mst(mst_path)
  if not seeds:
    log.warning("[STOCK_SERVICE] KOSPI .mst 파싱 결과가 비어 있습니다. path=%s", mst_path)
    return 0

  async with get_session() as session:
    try:
      market_id = await find_market_id_by_market_code(session, MarketType.KOSPI)
      upserted = await save_stocks(session, market_id=market_id, seeds=seeds)
      await session.commit()
      log.info("[STOCK_SERVICE] KOSPI stock upsert 완료: %s건", upserted)
      return upserted
    except Exception:
      # 실패 시 롤백
      await session.rollback()
      log.exception("[STOCK_SERVICE] KOSPI stock upsert 중 오류 발생 (rollback 수행)")
      raise


async def get_kospi_mst_file(dest_dir: str) -> str:
  """
  .mst파일이 있다면 반환 없으면 다운로드
  """
  os.makedirs(dest_dir, exist_ok=True)
  mst_path = os.path.join(dest_dir, KOSPI_MST_FILE_NAME)
  # 파일이 없거나 0바이트면 재다운로드
  if not os.path.exists(mst_path) or os.path.getsize(mst_path) == 0:
    log.info("[STOCK_SERVICE] KOSPI mst 파일이 없어 다운로드를 진행합니다. dir=%s", dest_dir)
    mst_path = _download_kospi_mst_file(dest_dir)
  else:
    log.info("[STOCK_SERVICE] 기존 KOSPI mst 파일 사용: %s", mst_path)
  return mst_path


def _download_kospi_mst_file(dest_dir: str) -> str:
  """(동기) KIS 제공 mst.zip 파일 다운로드 후 파일 경로 반환"""
  os.makedirs(dest_dir, exist_ok=True)
  zip_path = os.path.join(dest_dir, "kospi_code.mst.zip")

  ssl._create_default_https_context = ssl._create_unverified_context
  urllib.request.urlretrieve(KOSPI_ZIP_URL, zip_path)

  with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(dest_dir)

  os.remove(zip_path)

  mst_path = os.path.join(dest_dir, KOSPI_MST_FILE_NAME)
  if not os.path.exists(mst_path):
    raise FileNotFoundError(f"{KOSPI_MST_FILE_NAME} 파일을 찾을 수 없습니다: {dest_dir}")

  log.info("[STOCK_SERVICE] KOSPI 마스터 파일 다운로드 및 zip 해제 완료: %s", mst_path)
  return mst_path
