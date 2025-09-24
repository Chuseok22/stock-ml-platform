# src/config/settings.py

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

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    case_sensitive = False

  @property
  def redis_url(self) -> str:
    """Redis URL"""
    if self.redis_password:
      return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
    else:
      return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
