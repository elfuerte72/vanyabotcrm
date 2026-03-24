from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    bot_token: str
    channel_id: int = -1002504147240
    channel_username: str = "ivanfit_health"

    # Database
    database_url: str

    # OpenRouter
    openrouter_api_key: str
    openrouter_model: str = "google/gemini-3-flash-preview"
    openrouter_temperature_conversation: float = 0.4
    openrouter_temperature_food: float = 0.8
    openrouter_max_retries: int = 2

    # Payment
    tribute_link: str = "https://t.me/tribute/app?startapp=pnvi"
    ziina_link: str = ""  # Fallback static Ziina link (used if API unavailable)
    ziina_api_key: str = ""  # Ziina API Bearer token for Payment Intent creation
    ziina_webhook_secret: str = ""

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def load_media_config() -> dict[str, Any]:
    media_path = Path(__file__).parent / "media.yaml"
    with open(media_path) as f:
        return yaml.safe_load(f)


_settings: Settings | None = None
_media_config: dict[str, Any] | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings


def get_media_config() -> dict[str, Any]:
    global _media_config
    if _media_config is None:
        _media_config = load_media_config()
    return _media_config


# Lazy proxies for backward-compatible imports
class _SettingsProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_settings(), name)

class _MediaConfigProxy:
    def __getitem__(self, key: str) -> Any:
        return get_media_config()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return get_media_config().get(key, default)


settings = _SettingsProxy()  # type: ignore[assignment]
media_config = _MediaConfigProxy()  # type: ignore[assignment]
