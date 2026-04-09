import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "async-document-processing-workflow"
    debug: bool = False
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str = ""
    allowed_hosts: str = "localhost,127.0.0.1"
    enforce_https: bool = False
    gzip_minimum_size: int = 1024

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/docproc"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    redis_progress_channel: str = "job_progress"
    redis_ssl_cert_reqs: str = "required"
    celery_broker_connection_retry_on_startup: bool = True

    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def cors_origins_list(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def cors_origin_regex_value(self) -> str | None:
        value = (self.cors_origin_regex or "").strip()
        return value or None

    @property
    def allowed_hosts_list(self) -> List[str]:
        raw = (self.allowed_hosts or "").strip()
        if not raw:
            return ["localhost", "127.0.0.1"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    values = [str(item).strip() for item in parsed if str(item).strip()]
                    return values or ["localhost", "127.0.0.1"]
            except json.JSONDecodeError:
                pass
        values = [item.strip() for item in raw.split(",") if item.strip()]
        return values or ["localhost", "127.0.0.1"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
