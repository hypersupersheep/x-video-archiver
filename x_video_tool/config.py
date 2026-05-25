from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Runtime configuration read from environment variables."""

    app_token: str | None = os.getenv("X_VIDEO_APP_TOKEN") or None
    cookies_file: str | None = os.getenv("X_VIDEO_COOKIES_FILE") or None
    max_duration_seconds: int = int(os.getenv("X_VIDEO_MAX_DURATION_SECONDS", "600"))
    request_timeout_seconds: int = int(os.getenv("X_VIDEO_REQUEST_TIMEOUT_SECONDS", "45"))


settings = Settings()
