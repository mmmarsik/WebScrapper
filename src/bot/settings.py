from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Settings for the Telegram bot."""

    api_id: int
    api_hash: str
    token: str

    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=".env",
        env_prefix="BOT_",
    )
