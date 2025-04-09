import typing
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ScrapperSettings(BaseSettings):
    """Configuration settings for the Scrapper API."""

    base_url: str = "http://127.0.0.1:8000"
    scrapper_default_url: str = "https://default.scrapper.url"

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="SCRAPPER_",
    )
