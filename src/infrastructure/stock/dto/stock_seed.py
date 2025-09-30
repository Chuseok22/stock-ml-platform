# src/infrastructure/stock/dto/stock_seed.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class StockSeed:
  ticker: str
  stock_name: str
  listing_date: Optional[date]
  face_value: Optional[Decimal]
  listing_shares: Optional[int]
