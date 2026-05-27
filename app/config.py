import os
from dataclasses import dataclass


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("NISCORE_APP_NAME", "NISCore API")
    app_version: str = os.getenv("NISCORE_APP_VERSION", "0.4.0")
    env: str = os.getenv("NISCORE_ENV", "dev")
    database_url: str = os.getenv("NISCORE_DATABASE_URL", "sqlite:///niscore.db")
    api_token: str = os.getenv("NISCORE_API_TOKEN", "")
    cors_origins_raw: str = os.getenv("NISCORE_CORS_ORIGINS", "*")
    jwt_secret: str = os.getenv("NISCORE_JWT_SECRET", "dev-only-secret-change-me")

    @property
    def cors_origins(self) -> list[str]:
        origins = _split_csv(self.cors_origins_raw)
        return origins or ["*"]


settings = Settings()
