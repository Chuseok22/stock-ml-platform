# src/config/settings.py
from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  storage_root: str
  analytics_dir: str
  log_dir: str
  model_dir: str

  # Postgres
  db_host: str
  db_port: str
  db_name: str
  db_user: str
  db_password: str

  # Redis
  redis_host: str
  redis_port: int
  redis_password: str
  redis_db: int

  # KIS
  kis_app_key: str
  kis_app_secret: str
  kis_base_url: str

@lru_cache
def get_settings() -> Settings:
  return Settings()
