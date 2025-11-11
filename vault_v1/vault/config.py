from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///vault.db", alias="DATABASE_URL")
    vault_backend: Literal["local", "s3"] = Field(default="local", alias="VAULT_BACKEND")
    vault_local_path: Path = Field(default=Path("data"), alias="VAULT_LOCAL_PATH")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = Field(default=None, alias="AWS_DEFAULT_REGION")
    aws_bucket: Optional[str] = Field(default=None, alias="VAULT_S3_BUCKET")
    vault_signing_key: Optional[Path] = Field(default=None, alias="VAULT_SIGNING_KEY")
    default_chunk_size: int = Field(default=1024 * 1024, alias="CHUNK_SIZE")

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
