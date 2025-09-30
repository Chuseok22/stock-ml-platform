# src/infrastructure/stock/dto/stock_seed.py
import decimal
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class StockSeed:
  ticker: str
  stock_name: str
  listing_date: Optional[date]
  face_value: Optional[decimal]
  listing_shares: Optional[int]
