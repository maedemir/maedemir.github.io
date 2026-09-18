from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # Last source wins. Keep constructor kwargs last so tests can inject a temp DB.
        return env_settings, dotenv_settings, file_secret_settings, init_settings

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    database_url: str = "sqlite:///./data/litdb.sqlite3"
    contact_email: str = "lab@example.com"
    ingest_token: str | None = None
    data_dir: Path = Path("./data")
    host: str = "0.0.0.0"
    port: int = 8000
    start_date: str = "2025-01-01"
    user_agent: str = Field(
        default="SpatialOmicsLitDB/0.1 (Mirzazadeh Lab literature dashboard)"
    )

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def pdf_dir(self) -> Path:
        return self.data_dir / "pdfs"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "indexes"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
