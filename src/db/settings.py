from pydantic_settings import BaseSettings, SettingsConfigDict

from src.db.repositories.types import RepositoryAccessType


class DBSettings(BaseSettings):
    """Settings for the database."""

    db: str
    user: str
    password: str
    host: str
    access_type: RepositoryAccessType
    pagination_batch_size: int

    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=".env",
        env_prefix="POSTGRES_",
    )
