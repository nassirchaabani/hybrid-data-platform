from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Plateforme associative hybride"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    jwt_secret: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0, le=1440)
    admin_username: str = "gestionnaire"
    admin_password: SecretStr = Field(min_length=12)

    private_database_url: str = Field(repr=False)
    cloud_database_url: str = Field(repr=False)
    deployment_mode: Literal["local", "hybrid"] = "local"
    auto_create_schema: bool = False
    seed_demo_data: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
