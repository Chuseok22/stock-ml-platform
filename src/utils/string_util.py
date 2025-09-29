# src/utils/string_util.py
from typing import Optional


def clean_str(s: Optional[str]) -> str:
  return (s or "").strip()
